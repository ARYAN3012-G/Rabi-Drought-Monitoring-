"""Detect v3: precision-improved early-drying model.

Three improvements over detect_v2 to reduce the 68.7% false alarm rate:
  1. Four new harvest-vs-stress discriminator features (drop_rate, season_progress,
     anom_at_peak, rain_30_pre_peak).
  2. F0.5-score threshold tuning (weights precision twice over recall) instead
     of balanced_accuracy_score.
  3. Irrigation-stratified threshold (irrigated fields get a higher threshold
     because borewells buffer them against drought stress).

Outputs go to results/detect_v3/. detect_v2 artifacts are never overwritten.

Run:
    python -B src/detect/causal_events_v3.py

Compare v2 vs v3 with:
    python -B src/detect/causal_events_v3.py --compare
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, average_precision_score, balanced_accuracy_score,
    f1_score, fbeta_score, precision_score, recall_score, roc_auc_score
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[2]
DATA_V2 = ROOT / 'data/detect_v2'   # read-only: reuse v2 labels & raw data
DATA_V3 = ROOT / 'data/detect_v3'   # new: v3 augmented dataset
OUT = ROOT / 'results/detect_v3'
OUT_V2 = ROOT / 'results/detect_v2'  # read-only for comparison

TRAIN, VAL, TEST = [2019, 2020, 2021], [2022], [2023, 2024, 2025]
HORIZONS, SEEDS = [7, 15, 30], list(range(5))
BASE_MODELS = ['Logistic regression', 'Random forest', 'XGBoost']

# ── v2 features (unchanged) ──────────────────────────────────────────────────
FEATURES_V2 = [
    'irr', 'doy', 'ndvi', 'age', 'peak', 'trough', 'days_since_peak', 'drop',
    'drop_share', 'chg15', 'chg30', 'anom', 'normal_dry', 'days_to_normal_dry',
    'observed_dry', 'rain_jun_available_ratio', 'rain_since_oct', 'rain60',
    'et0_30', 'tmax_30', 'spei'
]

# ── NEW v3 features ───────────────────────────────────────────────────────────
NEW_FEATURES = [
    'drop_rate',         # (peak - ndvi) / max(days_since_peak, 1)  — fast drop = harvest
    'season_progress',   # doy / normal_dry                          — late = harvest
    'anom_at_peak',      # peak - normal_curve at peak_doy           — stressed crop peaks below normal
    'rain_30_pre_peak',  # mm of rain in 30 days before peak date    — low = pre-season stress
    'irr_x_drop_rate',   # irrigation × drop_rate interaction
]

FEATURES_V3 = FEATURES_V2 + NEW_FEATURES


# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def average(a, axis=None):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        return np.nanmean(a, axis=axis)


# ─────────────────────────────────────────────────────────────────────────────
# Threshold tuning  —  KEY CHANGE vs v2
# ─────────────────────────────────────────────────────────────────────────────

def threshold_balanced(y, p):
    """v2 method: balanced accuracy (equal weight on recall & specificity)."""
    grid = np.unique(np.quantile(p, np.linspace(.01, .99, 197)))
    return float(max(grid, key=lambda x: balanced_accuracy_score(y, p >= x)))


def threshold_recall_constrained(y, p, min_recall=0.70):
    """v3 method: highest-precision threshold that keeps recall >= min_recall.

    This avoids the degenerate F0.5 failure mode on rare-event datasets where
    the optimizer finds extreme thresholds that fire on 1-2 samples (100%
    precision, 0% recall). Instead we find the best precision operating point
    that is still practically useful (≥70% event recall).

    Falls back to balanced_accuracy if no threshold satisfies the constraint.
    """
    grid = np.unique(np.quantile(p, np.linspace(.01, .99, 197)))
    best_thr, best_prec = None, -1.0
    for thr in grid:
        pred = p >= thr
        rec = recall_score(y, pred, zero_division=0)
        if rec >= min_recall:
            prec = precision_score(y, pred, zero_division=0)
            if prec > best_prec:
                best_prec = prec
                best_thr = thr
    if best_thr is None:
        # Fallback: no threshold achieves min_recall; use balanced accuracy
        best_thr = float(max(grid, key=lambda x: balanced_accuracy_score(y, p >= x)))
    return float(best_thr)


def threshold_stratified(y, p, irr_mask, min_recall=0.70):
    """Irrigation-stratified thresholds using recall-constrained precision.

    Irrigated fields use a stricter min_recall (0.60) since drought events
    there are rarer — precision matters more for irrigated warnings.
    Returns a dict: {'all': thr, 'irr': thr_irr, 'rai': thr_rai}
    """
    thr_all = threshold_recall_constrained(y, p, min_recall)
    # Irrigated: stricter threshold (fewer but more reliable warnings)
    if irr_mask.sum() > 10:
        thr_irr = threshold_recall_constrained(y[irr_mask], p[irr_mask], min_recall=0.60)
    else:
        thr_irr = thr_all
    # Rainfed: standard threshold (drought more common, recall matters more)
    if (~irr_mask).sum() > 10:
        thr_rai = threshold_recall_constrained(y[~irr_mask], p[~irr_mask], min_recall=0.75)
    else:
        thr_rai = thr_all
    return {'all': thr_all, 'irr': thr_irr, 'rai': thr_rai}


# ─────────────────────────────────────────────────────────────────────────────
# Reference helpers (identical to v2)
# ─────────────────────────────────────────────────────────────────────────────

def reference_stats(phenology, point, own_season):
    q = phenology[
        (phenology.point_id == point) &
        phenology.season.isin(TRAIN) &
        (phenology.season != own_season) &
        phenology.quality_ok &
        phenology.est &
        phenology.dry_doy.notna()
    ]
    return len(q), float(q.dry_doy.median()) if len(q) else np.nan


def issue_dates(season):
    return pd.date_range(f'{season}-12-01', f'{season + 1}-03-31', freq='5D')


# ─────────────────────────────────────────────────────────────────────────────
# Feature engineering  —  extends v2 past_features() with 4 new signals
# ─────────────────────────────────────────────────────────────────────────────

def past_features_v3(obs, season, issue, normal_dry, normal_curve, rain_series):
    """Causal feature vector at issue_date with 4 new harvest-discriminator features.

    Parameters
    ----------
    obs          : DataFrame with [date, ndvi] for one point-season
    season       : int, start year of Rabi season
    issue        : date-like, the forecast issue date
    normal_dry   : float, median normal drying DOY from training reference
    normal_curve : np.ndarray shape (366,) of daily NDVI normals
    rain_series  : pd.Series indexed by date, daily precipitation (mm)
    """
    issue = pd.Timestamp(issue)
    cut = issue - pd.Timedelta(days=2)
    g = obs[(obs.date <= cut) & (obs.date >= pd.Timestamp(season, 10, 1))].sort_values('date')

    if g.empty or (issue - g.date.iloc[-1]).days > 12:
        return None, 'no recent observation'

    v = g.ndvi.rolling(3, min_periods=1).median().to_numpy()
    d = (g.date - pd.Timestamp(season, 10, 1)).dt.days.to_numpy()
    dt = (issue - pd.Timestamp(season, 10, 1)).days
    ld = int(d[-1])

    if not (d <= 91).any():
        return None, 'not established by issue'

    ti = int(np.argmin(np.where(d <= 91, v, np.inf)))
    if ti >= len(v) - 1:
        return None, 'not established by issue'

    pi = ti + 1 + int(np.argmax(v[ti + 1:]))
    trough, peak, last = float(v[ti]), float(v[pi]), float(v[-1])
    amp = peak - trough
    if peak < .35 or amp < .15:
        return None, 'not established by issue'

    # ── same observed_dry flag as v2 ────────────────────────────────────────
    observed_dry = 0
    for j in range(pi + 1, len(v) - 1):
        if v[j] < trough + .5 * amp and v[j + 1] < trough + .5 * amp:
            observed_dry = int(d[j] <= normal_dry - 21)
            break

    def lag(days):
        m = d <= ld - days
        return float(v[m][-1]) if m.any() else np.nan

    # ── v2 features ─────────────────────────────────────────────────────────
    days_since_peak = ld - int(d[pi])
    drop = peak - last
    feats = dict(
        doy=dt, ndvi=last, age=dt - ld, peak=peak, trough=trough,
        days_since_peak=days_since_peak,
        drop=drop,
        drop_share=drop / amp,
        chg15=last - lag(15), chg30=last - lag(30),
        anom=last - normal_curve[ld],
        normal_dry=normal_dry,
        days_to_normal_dry=normal_dry - dt,
        observed_dry=observed_dry,
    )

    # ── NEW v3 features ──────────────────────────────────────────────────────

    # 1. drop_rate: how fast (per day) is NDVI falling?
    #    Fast drop (harvest) ≠ slow drop (drought stress)
    feats['drop_rate'] = drop / max(days_since_peak, 1)

    # 2. season_progress: how far through the typical season are we?
    #    Values near 1.0 or above = normal harvest time → low drought risk
    feats['season_progress'] = dt / max(normal_dry, 1)

    # 3. anom_at_peak: was the peak NDVI above or below the season-normal curve?
    #    A drought-stressed crop peaks BELOW normal (anom_at_peak < 0)
    peak_doy = int(d[pi])
    feats['anom_at_peak'] = peak - float(normal_curve[min(peak_doy, len(normal_curve) - 1)])

    # 4. rain_30_pre_peak: total rainfall in 30 days BEFORE the NDVI peak
    #    Low pre-peak rain → crop was already stressed during establishment
    if rain_series is not None:
        peak_date = pd.Timestamp(season, 10, 1) + pd.Timedelta(days=peak_doy)
        rain_window_start = peak_date - pd.Timedelta(days=30)
        rain_window_end = peak_date - pd.Timedelta(days=1)
        try:
            feats['rain_30_pre_peak'] = float(
                rain_series.loc[rain_window_start:rain_window_end].sum()
            )
        except Exception:
            feats['rain_30_pre_peak'] = np.nan
    else:
        feats['rain_30_pre_peak'] = np.nan

    # 5. irr_x_drop_rate will be added after the irr field is merged in make_dataset_v3

    return feats, 'eligible'


# ─────────────────────────────────────────────────────────────────────────────
# Weather helpers  (same as v2, extended with rain_series per cell)
# ─────────────────────────────────────────────────────────────────────────────

def rainfall_ratio(rain, season, issue):
    end = min(pd.Timestamp(issue) - pd.Timedelta(days=8), pd.Timestamp(season, 11, 30))
    start = pd.Timestamp(season, 6, 1)
    span = end - start
    normal = np.mean([
        rain.loc[pd.Timestamp(y, 6, 1):pd.Timestamp(y, 6, 1) + span].sum()
        for y in range(1979, 2012)
    ])
    return float(rain.loc[start:end].sum() / normal) if normal > 0 else np.nan


def load_rain_series(cell):
    w = pd.read_csv(ROOT / f'data/prepared/{cell}.csv', parse_dates=['valid_time'])
    return w.set_index('valid_time').Precipitation_Flux


def make_weather(cells, dates):
    rows = []
    for cell in cells:
        w = pd.read_csv(ROOT / f'data/prepared/{cell}.csv', parse_dates=['valid_time'])
        w = w.set_index('valid_time').asfreq('D')
        if w.Precipitation_Flux.isna().any():
            raise ValueError(f'Missing rainfall in {cell}')
        rain = w.Precipitation_Flux
        for issue in dates:
            e = issue - pd.Timedelta(days=8)
            s = issue.year if issue.month >= 6 else issue.year - 1
            rows.append(dict(
                cell=cell, issue_date=issue, weather_date=e,
                rain_jun_available_ratio=rainfall_ratio(rain, s, issue),
                rain_since_oct=rain.loc[pd.Timestamp(s, 10, 1):e].sum(),
                rain60=rain.loc[e - pd.Timedelta(days=59):e].sum(),
                et0_30=w.ReferenceET_PenmanMonteith_FAO56.loc[e - pd.Timedelta(days=29):e].mean(),
                tmax_30=(w.Temperature_Air_2m_Max_24h.loc[e - pd.Timedelta(days=29):e].mean() - 273.15),
                spei=w.SPEI.loc[e]
            ))
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Dataset builder
# ─────────────────────────────────────────────────────────────────────────────

def make_dataset_v3():
    """Build the v3 instance dataset with new features. Reuses v2 raw labels."""
    DATA_V3.mkdir(parents=True, exist_ok=True)

    # Reuse v2 label file (same phenology definitions)
    old = pd.read_csv(ROOT / 'data/detect/labels.csv')
    lab = old[['point_id', 'season', 'quality_ok', 'est', 'dry_doy', 'mandal', 'irr']].copy()
    refs = [reference_stats(lab, r.point_id, r.season) for r in lab.itertuples()]
    lab['n_ref_dry'], lab['normal_dry'] = zip(*refs)
    lab['reference_ok'] = lab.n_ref_dry >= 2
    lab['early'] = lab.est & lab.dry_doy.notna() & (lab.dry_doy <= lab.normal_dry - 21)
    lab['scorable'] = lab.quality_ok & lab.reference_ok
    lab['event_date'] = (
        pd.to_datetime(lab.season.astype(str) + '-10-01') +
        pd.to_timedelta(lab.dry_doy, unit='D')
    )
    mapping = pd.read_csv(
        ROOT / 'data/forecast/instances.csv.gz',
        usecols=['mandal', 'cell']
    ).drop_duplicates()
    lab = lab.merge(mapping, on='mandal', validate='many_to_one')

    loader = load_module('forecast_loader_v3', ROOT / 'src/forecast/build_dataset.py')
    obs = loader.load_obs()
    groups = {k: g for k, g in obs.groupby(['point_id', 'season'])}
    z = np.load(ROOT / 'data/forecast/point_curves.npz', allow_pickle=True)
    ids, seasons, curves = list(z['point_ids']), list(z['seasons']), z['P']
    pidx = {p: i for i, p in enumerate(ids)}

    # Pre-load rain series per cell for rain_30_pre_peak feature
    cell_rain = {}
    for cell in lab.cell.unique():
        try:
            cell_rain[cell] = load_rain_series(cell)
        except Exception:
            cell_rain[cell] = None

    rows, excluded = [], []
    for r in lab.itertuples():
        if not r.reference_ok:
            excluded.append(dict(
                point_id=r.point_id, season=r.season,
                issue_date=pd.NaT, reason='insufficient training reference'
            ))
            continue
        use = [seasons.index(s) for s in TRAIN if s != r.season]
        normal = average(curves[pidx[r.point_id], use, :], axis=0)
        g = groups.get((r.point_id, r.season), obs.iloc[:0])
        rain_s = cell_rain.get(r.cell)

        for issue in issue_dates(r.season):
            f, reason = past_features_v3(g, r.season, issue, r.normal_dry, normal, rain_s)
            if f is None:
                excluded.append(dict(
                    point_id=r.point_id, season=r.season,
                    issue_date=issue, reason=reason
                ))
                continue
            row = dict(
                point_id=r.point_id, season=r.season, issue_date=issue,
                mandal=r.mandal, irr=r.irr, cell=r.cell,
                scorable=r.scorable, early=r.early,
                event_date=r.event_date, **f
            )
            # Add irr × drop_rate interaction
            row['irr_x_drop_rate'] = r.irr * row['drop_rate']

            row['at_risk'] = not (r.early and r.event_date <= issue)
            for h in HORIZONS:
                row[f'y{h}'] = int(r.early and issue < r.event_date <= issue + pd.Timedelta(days=h))
            rows.append(row)

    d = pd.DataFrame(rows)
    wx = make_weather(d.cell.unique(), sorted(d.issue_date.unique()))
    d = d.merge(wx, on=['cell', 'issue_date'], validate='many_to_one')
    if d[['spei', 'rain60', 'et0_30', 'tmax_30']].isna().any().any():
        raise ValueError('Missing corrected weather')
    d.to_csv(DATA_V3 / 'instances.csv.gz', index=False)
    pd.DataFrame(excluded).to_csv(DATA_V3 / 'exclusions.csv', index=False)
    print(f'V3 dataset: {len(d)} rows, {d.point_id.nunique()} points', flush=True)
    return d, lab


# ─────────────────────────────────────────────────────────────────────────────
# Models (same architectures as v2)
# ─────────────────────────────────────────────────────────────────────────────

def fit_models(seed, weight):
    return {
        'Logistic regression': make_pipeline(
            SimpleImputer(strategy='median'), StandardScaler(),
            LogisticRegression(max_iter=3000, class_weight='balanced')
        ),
        'Random forest': make_pipeline(
            SimpleImputer(strategy='median'),
            RandomForestClassifier(
                n_estimators=500, min_samples_leaf=5,
                class_weight='balanced_subsample',
                random_state=seed, n_jobs=4
            )
        ),
        'XGBoost': XGBClassifier(
            n_estimators=400, max_depth=4, learning_rate=.05, subsample=.8,
            colsample_bytree=.8, scale_pos_weight=weight,
            random_state=seed, eval_metric='logloss', n_jobs=4
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Metric helpers
# ─────────────────────────────────────────────────────────────────────────────

def metric(y, p, thr):
    y, p = np.asarray(y), np.asarray(p)
    f = p >= thr
    both = len(np.unique(y)) == 2
    return dict(
        n=len(y), positives=int(y.sum()), prevalence=float(y.mean()),
        accuracy=accuracy_score(y, f),
        balanced_accuracy=balanced_accuracy_score(y, f),
        f1=f1_score(y, f, zero_division=0),
        f05=fbeta_score(y, f, beta=0.5, zero_division=0),
        precision=precision_score(y, f, zero_division=0),
        recall=recall_score(y, f, zero_division=0),
        roc_auc=roc_auc_score(y, p) if both else np.nan,
        average_precision=average_precision_score(y, p) if both else np.nan,
    )


def event_records(labels, pred, h, model):
    rows = []
    grouped = {k: g.sort_values('issue_date') for k, g in pred.groupby(['point_id', 'season'])}
    for r in labels[labels.scorable].itertuples():
        g = grouped.get((r.point_id, r.season), pd.DataFrame(columns=pred.columns))
        first, last = issue_dates(r.season)[[0, -1]]
        event = bool(r.early and first < r.event_date <= last + pd.Timedelta(days=h))
        oper = g[g.observed_dry == 0]
        alerts = oper[oper.warn.astype(bool)]
        window = oper.iloc[:0]
        if event:
            window = oper[
                (oper.issue_date < r.event_date) &
                (oper.issue_date >= r.event_date - pd.Timedelta(days=h))
            ]
        hits = window[window.warn.astype(bool)]
        lead = (r.event_date - hits.issue_date.iloc[0]).days if len(hits) else np.nan
        rows.append(dict(
            point_id=r.point_id, season=r.season, cell=r.cell, irr=r.irr,
            horizon=h, model=model, event=event,
            opportunity=bool(len(window)), hit=bool(len(hits)),
            warned=bool(len(alerts)),
            first_warning=alerts.issue_date.iloc[0] if len(alerts) else pd.NaT,
            first_timely_warning=hits.issue_date.iloc[0] if len(hits) else pd.NaT,
            event_date=r.event_date if r.early else pd.NaT,
            lead_days=lead, n_warnings=len(alerts),
            n_timely_warnings=len(hits), n_forecasts=len(oper)
        ))
    return pd.DataFrame(rows)


def event_summary(e):
    n = int(e.event.sum())
    opp = int((e.event & e.opportunity).sum())
    hit = int(e.hit.sum())
    warn = int(e.warned.sum())

    def ratio(a, b):
        return float(a / b) if b else np.nan

    leads = e.loc[e.hit, 'lead_days']
    return dict(
        point_seasons=len(e), monitored_events=n,
        events_with_opportunity=opp, caught_events=hit,
        recall_all_events=ratio(hit, n), recall_opportunity=ratio(hit, opp),
        warned_point_seasons=warn, warning_precision=ratio(hit, warn),
        median_lead=float(leads.median()) if len(leads) else np.nan,
        lead_q25=float(leads.quantile(.25)) if len(leads) else np.nan,
        lead_q75=float(leads.quantile(.75)) if len(leads) else np.nan,
        recall_at_least_7_days=ratio(int((e.hit & (e.lead_days >= 7)).sum()), n),
        recall_at_least_14_days=ratio(int((e.hit & (e.lead_days >= 14)).sum()), n),
    )


def md_table(frame):
    def fmt(x):
        if pd.isna(x):
            return '-'
        if isinstance(x, (float, np.floating)):
            return f'{x:.3f}'
        return str(x)
    return '\n'.join([
        '| ' + ' | '.join(map(str, frame.columns)) + ' |',
        '|' + '|'.join(['---'] * len(frame.columns)) + '|'
    ] + [
        '| ' + ' | '.join(map(fmt, row)) + ' |'
        for row in frame.itertuples(index=False, name=None)
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Main training & evaluation loop
# ─────────────────────────────────────────────────────────────────────────────

def run(d, lab):
    summaries, seed_scores, events, point_preds, validation_preds, configs = [], [], [], [], [], []

    for h in HORIZONS:
        print(f'Train horizon {h}', flush=True)
        active = d.scorable & d.at_risk & (d.observed_dry == 0)
        tr = d[active & d.season.isin(TRAIN)]
        va = d[active & d.season.isin(VAL)]
        te = d[d.scorable & d.season.isin(TEST)].copy()
        vm = d[d.scorable & d.season.isin(VAL)].copy()
        y = f'y{h}'

        if tr[y].nunique() < 2 or va[y].nunique() < 2:
            raise ValueError('Insufficient validation/train events')

        weight = (1 - tr[y].mean()) / tr[y].mean()
        pv, pt, pvm = {}, {}, {}
        for seed in SEEDS:
            for name, model in fit_models(seed, weight).items():
                if name == 'Logistic regression' and seed > 0:
                    continue
                model.fit(tr[FEATURES_V3], tr[y])
                pv.setdefault(name, []).append(model.predict_proba(va[FEATURES_V3])[:, 1])
                pt.setdefault(name, []).append(model.predict_proba(te[FEATURES_V3])[:, 1])
                pvm.setdefault(name, []).append(model.predict_proba(vm[FEATURES_V3])[:, 1])
                print(f'  {name} seed {seed}', flush=True)

        ap = {n: average_precision_score(va[y], np.mean(pv[n], axis=0)) for n in BASE_MODELS}
        weights_arr = np.array([ap[n] for n in BASE_MODELS])
        weights_arr = weights_arr / weights_arr.sum()

        for name, w in [('Ensemble equal', np.ones(3) / 3), ('Ensemble weighted', weights_arr)]:
            for dest in (pv, pt, pvm):
                dest[name] = [
                    np.average(
                        [dest[n][min(seed, len(dest[n]) - 1)] for n in BASE_MODELS],
                        axis=0, weights=w
                    )
                    for seed in SEEDS
                ]

        # Baselines (fixed from training distribution)
        for bname, col, sign in [('Below-normal baseline', 'anom', -1),
                                  ('Drop baseline', 'drop_share', 1),
                                  ('Drop-rate baseline', 'drop_rate', 1)]:  # NEW: drop_rate baseline
            fill = float(tr[col].median())
            for dest, part in [(pv, va), (pt, te), (pvm, vm)]:
                dest[bname] = [(sign * part[col].fillna(fill)).to_numpy()]
        for dest, part in [(pv, va), (pt, te), (pvm, vm)]:
            dest['Early-drying rule'] = [
                ((part.drop_share >= .5) & (part.doy + h <= part.normal_dry - 21)).to_numpy(float)
            ]
            dest['Zero-onset baseline'] = [np.zeros(len(part))]

        candidate = [*BASE_MODELS, 'Ensemble equal', 'Ensemble weighted']
        vap = {n: float(average_precision_score(va[y], np.mean(pv[n], axis=0))) for n in candidate}
        selected = max(candidate, key=lambda n: vap[n])

        # ── F0.5 threshold (KEY CHANGE vs v2) ────────────────────────────────
        va_irr = va.irr.to_numpy().astype(bool)
        config = {
            'horizon': h, 'selected_model': selected,
            'selection': 'highest validation average precision',
            'threshold_method': 'Recall-constrained precision maximisation (min_recall=0.70)',
            'weights': dict(zip(BASE_MODELS, weights_arr.tolist())),
            'validation_ap': vap,
            'n_train': len(tr), 'n_val': len(va),
            'thresholds': {}
        }

        new = (te.at_risk & (te.observed_dry == 0)).to_numpy()
        meta = ['point_id', 'season', 'cell', 'irr', 'issue_date', 'event_date', 'early', 'at_risk', 'observed_dry']

        for name in pv:
            a = np.mean(pv[name], axis=0)
            b = np.mean(pt[name], axis=0)
            c = np.mean(pvm[name], axis=0)

            # F0.5 threshold (or 0.5 for rule-based)
            if name in ['Early-drying rule', 'Zero-onset baseline']:
                thr = 0.5
            else:
                thr = threshold_recall_constrained(va[y].to_numpy(), a)  # ← v3 change

            config['thresholds'][name] = thr

            for s in ['pooled', *TEST]:
                mask = new if s == 'pooled' else new & (te.season == s).to_numpy()
                if mask.any():
                    summaries.append(dict(
                        horizon=h, model=name, season=s, selected=(name == selected),
                        **metric(te[y].to_numpy()[mask], b[mask], thr)
                    ))

            for seed, (v_seed, t_seed) in enumerate(zip(pv[name], pt[name])):
                st = 0.5 if name in ['Early-drying rule', 'Zero-onset baseline'] \
                    else threshold_recall_constrained(va[y].to_numpy(), v_seed)
                seed_scores.append(dict(
                    horizon=h, model=name, seed=seed, threshold=st,
                    **metric(te[y].to_numpy()[new], t_seed[new], st)
                ))

            pred = te[meta].copy()
            pred['horizon'] = h
            pred['model'] = name
            pred['probability_or_score'] = b
            pred['threshold'] = thr
            # Stratified warn: irrigated fields use a stricter threshold
            irr_te = te.irr.to_numpy().astype(bool)
            if name not in ['Early-drying rule', 'Zero-onset baseline']:
                thr_dict = threshold_stratified(va[y].to_numpy(), a, va_irr)
                warn_arr = np.where(
                    irr_te,
                    b >= thr_dict['irr'],
                    b >= thr_dict['rai']
                ) & (te.observed_dry.to_numpy() == 0)
                config['thresholds'][name + '_stratified'] = thr_dict
            else:
                warn_arr = (b >= thr) & (te.observed_dry.to_numpy() == 0)

            pred['warn'] = warn_arr
            pred['target'] = te[y].to_numpy()
            pred['selected'] = (name == selected)
            point_preds.append(pred)

            vp = vm[meta].copy()
            vp['horizon'] = h
            vp['model'] = name
            vp['probability_or_score'] = c
            vp['threshold'] = thr
            vp_irr = vm.irr.to_numpy().astype(bool)
            if name not in ['Early-drying rule', 'Zero-onset baseline']:
                thr_dict_v = threshold_stratified(va[y].to_numpy(), a, va_irr)
                vp['warn'] = np.where(vp_irr, c >= thr_dict_v['irr'], c >= thr_dict_v['rai']) \
                             & (vm.observed_dry.to_numpy() == 0)
            else:
                vp['warn'] = (c >= thr) & (vm.observed_dry.to_numpy() == 0)
            vp['target'] = vm[y].to_numpy()
            validation_preds.append(vp)

            ev = event_records(lab[lab.season.isin(TEST)], pred, h, name)
            ev['selected'] = (name == selected)
            events.append(ev)

        configs.append(config)
        (OUT / 'operating_points.json').write_text(json.dumps(configs, indent=2), encoding='utf-8')
        pd.concat(point_preds).to_csv(OUT / 'predictions.csv.gz', index=False)
        pd.concat(validation_preds).to_csv(OUT / 'validation_predictions.csv.gz', index=False)
        pd.concat(events).to_csv(OUT / 'events.csv', index=False)

    met = pd.DataFrame(summaries)
    met.to_csv(OUT / 'point_date_metrics.csv', index=False)
    pd.DataFrame(seed_scores).to_csv(OUT / 'seed_metrics.csv', index=False)

    ev = pd.concat(events)
    rows, cis = [], []
    for (h, name), g in ev.groupby(['horizon', 'model'], sort=False):
        for s in ['pooled', *TEST]:
            sub = g if s == 'pooled' else g[g.season == s]
            rows.append(dict(
                horizon=h, model=name, season=s,
                selected=bool(g.selected.iloc[0]),
                **event_summary(sub)
            ))
    es = pd.DataFrame(rows)
    es.to_csv(OUT / 'event_metrics.csv', index=False)

    write_report(met, es, lab)


# ─────────────────────────────────────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────────────────────────────────────

def write_report(met, es, lab):
    pm = met[(met.season == 'pooled') & met.selected]
    em = es[(es.season == 'pooled') & es.selected]
    lines = [
        '# Rabi early-drying risk: detect_v3 (precision-improved)',
        '',
        '**Improvements over detect_v2:**',
        '- 4 new harvest-discrimination features: `drop_rate`, `season_progress`, `anom_at_peak`, `rain_30_pre_peak`.',
        '- Recall-constrained precision threshold: highest threshold that keeps validation recall ≥ 70%.',
        '- Irrigation-stratified thresholds (irrigated fields → stricter warning criteria).',
        '',
        '## Point-date metrics (new onsets, validation-selected model)',
        '',
        md_table(pm[['horizon', 'model', 'n', 'positives', 'prevalence',
                      'roc_auc', 'average_precision', 'f05', 'precision', 'recall']]),
        '',
        '## Unique point-season events (validation-selected model)',
        '',
        md_table(em[['horizon', 'model', 'monitored_events', 'caught_events',
                      'recall_all_events', 'warned_point_seasons', 'warning_precision', 'median_lead']]),
        '',
        '## Interpretation',
        '',
        'Recall-constrained precision threshold selects the highest-precision operating point',
        'that maintains ≥70% validation recall (irrigated fields: ≥60%; rainfed: ≥75%).',
        'The harvest-discrimination features (especially `drop_rate` and `season_progress`)',
        'help the model distinguish drought stress (slow decline early in season) from',
        'natural maturity and harvest (fast decline late in season).',
        '',
        '## Reproduction',
        '',
        '`python -B src/detect/causal_events_v3.py`',
        '',
        'Compare v2 vs v3: `python -B src/detect/causal_events_v3.py --compare`',
        '',
    ]
    (OUT / 'EVENT_REPORT_v3.md').write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(lines))


# ─────────────────────────────────────────────────────────────────────────────
# Comparison report: v2 vs v3
# ─────────────────────────────────────────────────────────────────────────────

def compare_v2_v3():
    """Print a side-by-side comparison table of v2 and v3 event metrics."""
    if not (OUT_V2 / 'event_metrics.csv').exists():
        print('detect_v2 event_metrics.csv not found — run causal_events.py first.')
        return
    if not (OUT / 'event_metrics.csv').exists():
        print('detect_v3 event_metrics.csv not found — run causal_events_v3.py first.')
        return

    v2 = pd.read_csv(OUT_V2 / 'event_metrics.csv')
    v3 = pd.read_csv(OUT / 'event_metrics.csv')

    sel_v2 = v2[(v2.selected) & (v2.season == 'pooled')][
        ['horizon', 'model', 'caught_events', 'monitored_events',
         'recall_all_events', 'warned_point_seasons', 'warning_precision', 'median_lead']
    ].copy()
    sel_v3 = v3[(v3.selected) & (v3.season == 'pooled')][
        ['horizon', 'model', 'caught_events', 'warned_point_seasons', 'warning_precision', 'median_lead']
    ].copy()

    sel_v2 = sel_v2.rename(columns={
        'model': 'model_v2', 'caught_events': 'caught_v2',
        'warned_point_seasons': 'warned_v2', 'warning_precision': 'precision_v2',
        'median_lead': 'lead_v2'
    })
    sel_v3 = sel_v3.rename(columns={
        'model': 'model_v3', 'caught_events': 'caught_v3',
        'warned_point_seasons': 'warned_v3', 'warning_precision': 'precision_v3',
        'median_lead': 'lead_v3'
    })
    cmp = sel_v2.merge(sel_v3, on='horizon')
    cmp['precision_gain'] = (cmp.precision_v3 - cmp.precision_v2).round(3)
    cmp['recall_loss'] = ((cmp.caught_v2 - cmp.caught_v3) / cmp.monitored_events).round(3)

    print('\n=== V2 vs V3 Comparison (selected model, pooled evaluation seasons) ===')
    print(cmp[['horizon', 'caught_v2', 'warned_v2', 'precision_v2',
               'caught_v3', 'warned_v3', 'precision_v3',
               'precision_gain', 'recall_loss', 'lead_v3']].to_string(index=False))

    out_path = OUT / 'v2_vs_v3_comparison.csv'
    cmp.to_csv(out_path, index=False)
    print(f'\nSaved: {out_path}')


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compare', action='store_true',
                        help='Print v2 vs v3 comparison table (both must have been run already)')
    parser.add_argument('--reports-only', action='store_true',
                        help='Rebuild report from saved scores without refitting')
    args = parser.parse_args()

    if args.compare:
        compare_v2_v3()
        return

    if args.reports_only:
        write_report(
            pd.read_csv(OUT / 'point_date_metrics.csv'),
            pd.read_csv(OUT / 'event_metrics.csv'),
            pd.read_csv(ROOT / 'data/detect/labels.csv')
        )
        print('Report refreshed; no training.')
        return

    # Record provenance
    paths = [
        Path(__file__),
        ROOT / 'docs/DETECT_v2.md',
        ROOT / 'data/detect/labels.csv',
        ROOT / 'data/gee_exports/C3_points_timeseries.csv',
        ROOT / 'data/forecast/point_curves.npz'
    ]
    hashes = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in paths if p.exists()
    }
    (OUT / 'provenance.json').write_text(json.dumps({
        'version': 'detect_v3',
        'improvements': [
            'drop_rate feature (harvest-speed discriminator)',
            'season_progress feature (late-season harvest filter)',
            'anom_at_peak feature (pre-stress peak suppression)',
            'rain_30_pre_peak feature (pre-season water deficit)',
            'F0.5 threshold tuning (precision-weighted)',
            'irrigation-stratified thresholds'
        ],
        'train': TRAIN, 'validation': VAL, 'evaluation': TEST,
        'seeds': SEEDS, 'features': FEATURES_V3,
        'threshold_metric': 'recall_constrained_precision(min_recall=0.70)',
        'sha256': hashes
    }, indent=2), encoding='utf-8')

    print('Building v3 dataset with new features...', flush=True)
    d, lab = make_dataset_v3()
    print(f'Eligible forecasts: {len(d)}; points: {d.point_id.nunique()}', flush=True)
    run(d, lab)
    print('Complete: results/detect_v3/EVENT_REPORT_v3.md', flush=True)
    print('Run with --compare to see v2 vs v3 side by side.', flush=True)


if __name__ == '__main__':
    main()
