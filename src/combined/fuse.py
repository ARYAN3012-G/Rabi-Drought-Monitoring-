"""Combined rabi module v1: detect_v5 early-drying model + drought2 soil-moisture percentile context.

What it does (rules fixed in docs/COMBINED_v1.md before the combined test was run):
  1. Re-runs the detect_v5 Random forest exactly as written (src/detect/causal_events_v5.py functions, unmodified).
  2. Primary operating point = the validation-selected one: v5 stratified thresholds, NO soil veto
     (on validation 2022 the absolute 0.30 veto lowered F0.5 at every horizon).
  3. Every warning is tagged with drought2 soil context: the cell's 7-day root-zone percentile at the input
     cutoff (issue - 8 d), reference seasons 1990-2004, +-15 days (src/drought2/indicators.percentiles).
       soil-dry   : percentile < 0.50  (drier than the cell's own normal for the date)
       soil-wet   : percentile >= 0.50 (likely harvest / management, not water shortage)
     The tag is context. It is not used as a filter for the headline numbers.
  4. Reports, labelled as post-hoc: friend's absolute veto (rootzone < 0.30 m3/m3) and the tag used as a filter.
  5. Matched-recall check: precision of detect_v2 and of the v5 RF when the threshold alone is raised to
     the same number of caught events.

Run:  python -B -m src.combined.fuse
Out:  results/combined_v1/
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from src.detect import causal_events_v5 as v5
from src.drought2.indicators import percentiles

warnings.filterwarnings('ignore')
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results' / 'combined_v1'
SOIL_TAG = 0.50
META = ['point_id', 'season', 'cell', 'irr', 'issue_date', 'event_date', 'early', 'at_risk', 'observed_dry',
        'rootzone', 'soil_pct']


def soil_context() -> pd.DataFrame:
    s = pd.read_csv(ROOT / 'data/drought_v1/soil_daily.csv.gz', parse_dates=['date']).sort_values(['cell', 'date'])
    s['rz7'] = s.groupby('cell').rootzone.transform(lambda x: x.rolling(7, min_periods=7).mean())
    s['season'] = s.date.dt.year - (s.date.dt.month <= 8).astype(int)
    s['cday'] = s.date.dt.dayofyear
    s = percentiles(s.rename(columns={'cell': 'gid'})).rename(columns={'gid': 'cell', 'pct': 'soil_pct'})
    s['weather_date'] = s.date.dt.strftime('%Y-%m-%d')
    return s[['cell', 'weather_date', 'soil_pct']]


def f05(p, r):
    return 1.25 * p * r / (0.25 * p + r) if p and r and not np.isnan(p) else 0.0


def boot(e: pd.DataFrame, n=2000, seed=0):
    """Point-cluster bootstrap (whole points resampled) of warning precision and event recall."""
    g = e.groupby('point_id').agg(ev=('event', 'sum'), hit=('hit', 'sum'), w=('warned', 'sum')).to_numpy(float)
    rng = np.random.default_rng(seed)
    s = np.array([g[rng.integers(0, len(g), len(g))].sum(0) for _ in range(n)])
    with np.errstate(invalid='ignore', divide='ignore'):
        P, R = s[:, 1] / s[:, 2], s[:, 1] / s[:, 0]
    return [round(float(x), 3) for x in np.nanpercentile(P, [2.5, 97.5])], \
           [round(float(x), 3) for x in np.nanpercentile(R, [2.5, 97.5])]


def ps_scores(pred: pd.DataFrame, lab: pd.DataFrame, h: int) -> pd.DataFrame:
    """Per point-season: event flag, max score over operational rows, max score inside the timely window."""
    pred = pred[pred.observed_dry == 0]
    mx_all = pred.groupby(['point_id', 'season']).score.max()
    out = []
    for r in lab[lab.scorable].itertuples():
        first, last = v5.issue_dates(r.season)[[0, -1]]
        ev = bool(r.early and first < r.event_date <= last + pd.Timedelta(days=h))
        mw = np.nan
        if ev:
            q = pred[(pred.point_id == r.point_id) & (pred.season == r.season) & (pred.issue_date < r.event_date) &
                     (pred.issue_date >= r.event_date - pd.Timedelta(days=h))]
            mw = q.score.max() if len(q) else np.nan
        out.append(dict(event=ev, mx_all=mx_all.get((r.point_id, r.season), np.nan), mx_win=mw))
    return pd.DataFrame(out)


def matched(ps: pd.DataFrame, targets):
    """Raise a single threshold until caught events <= target; return (caught, warned, precision)."""
    res = {}
    for t in targets:
        for thr in np.unique(ps.mx_all.dropna()):  # ascending: first threshold with caught <= target
            c = int((ps.event & (ps.mx_win >= thr)).sum())
            if c <= t:
                w = int((ps.mx_all >= thr).sum())
                res[t] = (c, w, round(c / w, 3) if w else np.nan)
                break
    return res


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ROOT / 'data/detect_v4/instances.csv.gz', parse_dates=['issue_date'])
    d = v5.engineer_features(d).merge(soil_context(), on=['cell', 'weather_date'], how='left')
    lab = pd.read_csv(ROOT / 'data/detect_v2/labels.csv', parse_dates=['event_date'])
    v2 = pd.read_csv(ROOT / 'results/detect_v2/predictions.csv.gz', parse_dates=['issue_date', 'event_date'])
    rows, tagged, checks, pss = [], [], [], {}
    for h in v5.HORIZONS:
        active = d.scorable & d.at_risk & (d.observed_dry == 0)
        tr, va = d[active & d.season.isin(v5.TRAIN)], d[active & d.season.isin(v5.VAL)]
        y = f'y{h}'
        w = (1 - tr[y].mean()) / tr[y].mean()
        sets = {'validation 2022': d[d.scorable & d.season.isin(v5.VAL)].copy(),
                'test 2023-25': d[d.scorable & d.season.isin(v5.TEST)].copy()}
        pv, pp = [], {k: [] for k in sets}
        for seed in v5.SEEDS:
            m = v5.fit_models(seed, w)['Random forest']
            m.fit(tr[v5.FEATURES], tr[y])
            pv.append(m.predict_proba(va[v5.FEATURES])[:, 1])
            for k, s in sets.items():
                pp[k].append(m.predict_proba(s[v5.FEATURES])[:, 1])
        thr = v5.threshold_stratified(va[y].to_numpy(), np.mean(pv, 0), va.irr.to_numpy().astype(bool))
        for split, s in sets.items():
            p = np.mean(pp[split], 0)
            irr = s.irr.to_numpy().astype(bool)
            base = np.where(irr, p >= thr['irr'], p >= thr['rai']) & (s.observed_dry.to_numpy() == 0)
            dry = ~(s.soil_pct.to_numpy() >= SOIL_TAG)
            modes = {
                'A. v5 Random forest, validation-selected (primary)': base,
                'B. + absolute veto rootzone<0.30 (friend v5, post-hoc)': base & (s.rootzone.to_numpy() < 0.30),
                'C. + soil-dry tag as filter (post-hoc)': base & dry,
            }
            lb = lab[lab.season.isin(v5.VAL if split.startswith('val') else v5.TEST)]
            for mode, wm in modes.items():
                pred = s[META].copy(); pred['warn'] = wm; pred['score'] = p
                e = v5.event_records(lb, pred, h, mode)
                sm = v5.event_summary(e)
                ci = boot(e) if split.startswith('test') else ([np.nan] * 2, [np.nan] * 2)
                rows.append(dict(split=split, horizon=h, mode=mode, season='all', events=sm['monitored_events'],
                                 caught=sm['caught_events'], warned=sm['warned_point_seasons'],
                                 precision=sm['warning_precision'], recall=sm['recall_all_events'],
                                 f05=f05(sm['warning_precision'], sm['recall_all_events']),
                                 median_lead=sm['median_lead'], precision_ci=ci[0], recall_ci=ci[1]))
                if split.startswith('test'):
                    for season in v5.TEST:
                        es = v5.event_summary(e[e.season == season])
                        rows.append(dict(split=split, horizon=h, mode=mode, season=season,
                                         events=es['monitored_events'], caught=es['caught_events'],
                                         warned=es['warned_point_seasons'], precision=es['warning_precision'],
                                         recall=es['recall_all_events']))
                if mode.startswith('A') and split.startswith('test'):
                    # soil tag on each warned point-season, from its first warning
                    first = pred[pred.warn].sort_values('issue_date').groupby(['point_id', 'season']).head(1)
                    t = e[e.warned].merge(first[['point_id', 'season', 'issue_date', 'soil_pct', 'rootzone', 'score']],
                                          on=['point_id', 'season'])
                    t['soil_tag'] = np.where(t.soil_pct >= SOIL_TAG, 'soil-wet', 'soil-dry')
                    tagged.append(t.assign(horizon=h))
                    # matched-recall check vs detect_v2 and vs threshold-only
                    ps5 = ps_scores(pred, lb, h)
                    q2 = v2[v2.selected & (v2.horizon == h) & v2.season.isin(v5.TEST)].rename(
                        columns={'probability_or_score': 'score'})
                    ps2 = ps_scores(q2, lb, h)
                    pss[h] = (ps5, ps2)
        print(f'horizon {h} done', flush=True)
    # Matched-recall check: at the catch counts of A, B and C, what precision does a raised threshold alone give?
    res = pd.DataFrame(rows)
    for h in v5.HORIZONS:
        ps5, ps2 = pss[h]
        for _, r in res[(res.split == 'test 2023-25') & (res.horizon == h) & (res.season == 'all')].iterrows():
            t = int(r.caught)
            checks.append(dict(horizon=h, operating_point=r['mode'], caught=t, warned=int(r.warned),
                               precision=round(r.precision, 3) if r.warned else None,
                               v5_rf_threshold_only=matched(ps5, [t]).get(t),
                               detect_v2_threshold_only=matched(ps2, [t]).get(t)))
    res.to_csv(OUT / 'metrics.csv', index=False)
    tg = pd.concat(tagged)
    tg.to_csv(OUT / 'warnings_soil_tagged.csv', index=False)
    tag_sum = tg.groupby(['horizon', 'soil_tag']).agg(warned=('warned', 'sum'), correct=('hit', 'sum'))
    tag_sum['precision'] = (tag_sum.correct / tag_sum.warned).round(3)
    tag_sum.to_csv(OUT / 'soil_tag_summary.csv')
    (OUT / 'matched_checks.json').write_text(json.dumps(checks, indent=2, default=str), encoding='utf-8')
    pd.set_option('display.width', 250); pd.set_option('display.max_columns', 20); pd.set_option('display.max_colwidth', 60)
    print(res.round(3).to_string(index=False)); print(tag_sum); print(json.dumps(checks, indent=1, default=str))


if __name__ == '__main__':
    main()
