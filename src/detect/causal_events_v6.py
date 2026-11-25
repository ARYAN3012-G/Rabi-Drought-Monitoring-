"""Detect v6: corrected detect_v5 (validation-only choices + drought v2 soil-percentile context).

Changes from detect_v5 (docs/DETECT_v6.md; nothing chosen on the evaluation seasons):
  1. Model selected by validation PR-AUC (v5 hard-coded Random forest).
  2. Thresholds = the rule registered in docs/DETECT_v3.md: maximise F0.5 on validation 2022, separately
     for irrigated and rainfed points (v5 used recall targets 0.50/0.70 changed after test results were seen).
  3. No absolute soil veto (rootzone < 0.30 lowered validation F0.5 at every horizon; docs/COMBINED_v1.md).
     Instead every warning carries the drought v2 soil percentile at the input cutoff (issue - 8 d):
       soil-dry = below the cell's own normal (< 0.50), soil-wet = otherwise. Reported, not used as a filter.
  Features, labels, splits and event scoring are exactly detect_v5's (imported, unmodified).

Run: python -B -m src.detect.causal_events_v6
"""
from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, fbeta_score

from src.detect import causal_events_v5 as v5
from src.combined.fuse import soil_context, boot

warnings.filterwarnings('ignore')
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/detect_v6'
MODELS = ROOT / 'models/detect_v6'
SOIL_TAG = 0.50
CANDIDATES = [*v5.BASE_MODELS, 'Ensemble equal', 'Ensemble weighted']


def threshold_f05(y, p):
    """DETECT_v3 registered rule: F0.5-maximising threshold on a 197-point quantile grid of validation scores."""
    if len(y) < 10 or y.sum() == 0:
        return None
    grid = np.unique(np.quantile(p, np.linspace(.01, .99, 197)))
    return float(max(grid, key=lambda t: fbeta_score(y, p >= t, beta=0.5, zero_division=0)))


def thresholds(y, p, irr):
    t_all = threshold_f05(y, p)
    t_irr = threshold_f05(y[irr], p[irr]) or t_all
    t_rai = threshold_f05(y[~irr], p[~irr]) or t_all
    return {'all': t_all, 'irr': t_irr, 'rai': t_rai}


def main():
    OUT.mkdir(parents=True, exist_ok=True); MODELS.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ROOT / 'data/detect_v4/instances.csv.gz', parse_dates=['issue_date'])
    d = v5.engineer_features(d).merge(soil_context(), on=['cell', 'weather_date'], how='left')
    lab = pd.read_csv(ROOT / 'data/detect_v2/labels.csv', parse_dates=['event_date'])
    meta = ['point_id', 'season', 'cell', 'irr', 'issue_date', 'event_date', 'early', 'at_risk', 'observed_dry',
            'rootzone', 'soil_pct']
    configs, events, preds = [], [], []
    for h in v5.HORIZONS:
        print(f'horizon {h}', flush=True)
        active = d.scorable & d.at_risk & (d.observed_dry == 0)
        tr, va = d[active & d.season.isin(v5.TRAIN)], d[active & d.season.isin(v5.VAL)]
        te = d[d.scorable & d.season.isin(v5.TEST)].copy()
        y = f'y{h}'
        w = (1 - tr[y].mean()) / tr[y].mean()
        pv, pt, fitted = {}, {}, {}
        for seed in v5.SEEDS:
            for name, m in v5.fit_models(seed, w).items():
                if name == 'Logistic regression' and seed > 0:
                    continue
                m.fit(tr[v5.FEATURES], tr[y])
                pv.setdefault(name, []).append(m.predict_proba(va[v5.FEATURES])[:, 1])
                pt.setdefault(name, []).append(m.predict_proba(te[v5.FEATURES])[:, 1])
                fitted.setdefault(name, []).append(m)
        ap = {n: average_precision_score(va[y], np.mean(pv[n], 0)) for n in v5.BASE_MODELS}
        wts = np.array([ap[n] for n in v5.BASE_MODELS]); wts = wts / wts.sum()
        for name, wv in [('Ensemble equal', np.ones(3) / 3), ('Ensemble weighted', wts)]:
            for dest in (pv, pt):
                dest[name] = [np.average([dest[n][min(s, len(dest[n]) - 1)] for n in v5.BASE_MODELS], axis=0,
                                         weights=wv) for s in v5.SEEDS]
        vap = {n: float(average_precision_score(va[y], np.mean(pv[n], 0))) for n in CANDIDATES}
        selected = max(CANDIDATES, key=vap.get)
        irr_va, irr_te = va.irr.to_numpy().astype(bool), te.irr.to_numpy().astype(bool)
        for name in CANDIDATES:
            a, b = np.mean(pv[name], 0), np.mean(pt[name], 0)
            thr = thresholds(va[y].to_numpy(), a, irr_va)
            warn = np.where(irr_te, b >= thr['irr'], b >= thr['rai']) & (te.observed_dry.to_numpy() == 0)
            pred = te[meta].copy()
            pred['horizon'], pred['model'], pred['score'], pred['warn'] = h, name, b, warn
            pred['target'] = te[y].to_numpy()
            pred['soil_tag'] = np.where(pred.soil_pct >= SOIL_TAG, 'soil-wet',
                                        np.where(pred.soil_pct.notna(), 'soil-dry', 'unavailable'))
            pred['selected'] = name == selected
            ev = v5.event_records(lab[lab.season.isin(v5.TEST)], pred, h, name)
            first = pred[pred.warn].sort_values('issue_date').groupby(['point_id', 'season']).head(1)
            ev = ev.merge(first[['point_id', 'season', 'soil_tag']], on=['point_id', 'season'], how='left')
            ev['selected'] = name == selected
            events.append(ev)
            if name == selected:
                preds.append(pred)
                configs.append(dict(horizon=h, selected_model=selected, validation_ap=vap, thresholds=thr,
                                    threshold_rule='F0.5 on validation 2022, irrigated / rainfed (DETECT_v3)'))
        comps = v5.BASE_MODELS if selected.startswith('Ensemble') else [selected]
        joblib.dump(dict(models={n: fitted[n] for n in comps}, selected=selected, features=v5.FEATURES,
                         ensemble_weights=dict(zip(v5.BASE_MODELS, wts.tolist())), config=configs[-1]),
                    MODELS / f'detect_v6_h{h}.joblib')
    ev = pd.concat(events); ev.to_csv(OUT / 'events.csv', index=False)
    pd.concat(preds).to_csv(OUT / 'predictions.csv.gz', index=False)
    (OUT / 'operating_points.json').write_text(json.dumps(configs, indent=2), encoding='utf-8')
    report(ev)
    paths = [Path(__file__), ROOT / 'data/detect_v4/instances.csv.gz', ROOT / 'data/detect_v2/labels.csv']
    (OUT / 'provenance.json').write_text(json.dumps({
        'version': 'detect_v6', 'features': v5.FEATURES, 'soil_tag_threshold': SOIL_TAG,
        'sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}},
        indent=2), encoding='utf-8')


def report(ev):
    rows = []
    for (h, m), g in ev.groupby(['horizon', 'model'], sort=False):
        for s in ['pooled', *v5.TEST]:
            sub = g if s == 'pooled' else g[g.season == s]
            sm = v5.event_summary(sub)
            ci = boot(sub) if s == 'pooled' else ([np.nan] * 2, [np.nan] * 2)
            rows.append(dict(horizon=h, model=m, season=s, selected=bool(g.selected.iloc[0]), **sm,
                             precision_lo=ci[0][0], precision_hi=ci[0][1], recall_lo=ci[1][0], recall_hi=ci[1][1]))
    es = pd.DataFrame(rows); es.to_csv(OUT / 'event_metrics.csv', index=False)
    sel = ev[ev.selected]
    tag = sel[sel.warned].groupby(['horizon', 'soil_tag']).agg(warned=('warned', 'sum'), correct=('hit', 'sum'))
    tag['precision'] = tag.correct / tag.warned
    tag.to_csv(OUT / 'soil_tag_summary.csv')

    def md(df):
        f = lambda x: '-' if pd.isna(x) else (f'{x:.3f}' if isinstance(x, (float, np.floating)) else str(x))
        return '\n'.join(['| ' + ' | '.join(map(str, df.columns)) + ' |', '|' + '---|' * len(df.columns)] +
                         ['| ' + ' | '.join(f(v) for v in r) + ' |' for r in df.itertuples(index=False)])
    p = es[es.selected & (es.season == 'pooled')][['horizon', 'model', 'monitored_events', 'caught_events',
        'recall_all_events', 'recall_lo', 'recall_hi', 'warned_point_seasons', 'warning_precision', 'precision_lo',
        'precision_hi', 'median_lead']]
    s = es[es.selected & (es.season != 'pooled')][['horizon', 'season', 'monitored_events', 'caught_events',
        'warned_point_seasons', 'warning_precision', 'recall_all_events']]
    lines = ['# Rabi early-drying risk: detect_v6 (corrected detect_v5)', '',
             'Validation-selected model, DETECT_v3 registered F0.5 thresholds (irrigated / rainfed), no soil veto; '
             'every warning tagged with the drought v2 soil percentile. Evaluation 2023-24..2025-26, '
             'unique point-season events, 95 % point-cluster bootstrap. Protocol: `docs/DETECT_v6.md`.', '',
             '## Selected model, pooled', '', md(p), '', '## Selected model, by season', '', md(s), '',
             '## Warnings by soil context (selected model; tag from the first warning of the point-season)', '',
             md(tag.reset_index()), '',
             'Soil-dry = cell root-zone percentile below its own 1990-2004 normal at issue - 8 days. The tag is '
             'context, not a filter; it was examined on these test seasons before (COMBINED_v1), so its contrast '
             'here is descriptive. Its independent test is docs/MODIS_TEST_v1.md.']
    (OUT / 'EVENT_REPORT_v6.md').write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
