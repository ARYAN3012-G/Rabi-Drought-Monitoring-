# Rabi early-drying risk: detect_v3 (precision-improved)

**Improvements over detect_v2:**
- 4 new harvest-discrimination features: `drop_rate`, `season_progress`, `anom_at_peak`, `rain_30_pre_peak`.
- Recall-constrained precision threshold: highest threshold that keeps validation recall ≥ 70%.
- Irrigation-stratified thresholds (irrigated fields → stricter warning criteria).

## Point-date metrics (new onsets, validation-selected model)

| horizon | model | n | positives | prevalence | roc_auc | average_precision | f05 | precision | recall |
|---|---|---|---|---|---|---|---|---|---|
| 7 | Random forest | 6833 | 144 | 0.021 | 0.918 | 0.177 | 0.177 | 0.150 | 0.625 |
| 15 | Ensemble weighted | 6833 | 292 | 0.043 | 0.915 | 0.291 | 0.264 | 0.229 | 0.675 |
| 30 | Random forest | 6833 | 527 | 0.077 | 0.906 | 0.381 | 0.386 | 0.357 | 0.571 |

## Unique point-season events (validation-selected model)

| horizon | model | monitored_events | caught_events | recall_all_events | warned_point_seasons | warning_precision | median_lead |
|---|---|---|---|---|---|---|---|
| 7 | Random forest | 108 | 66 | 0.611 | 204 | 0.324 | 5.000 |
| 15 | Ensemble weighted | 108 | 78 | 0.722 | 196 | 0.398 | 12.000 |
| 30 | Random forest | 108 | 80 | 0.741 | 207 | 0.386 | 22.000 |

## Interpretation

Recall-constrained precision threshold selects the highest-precision operating point
that maintains ≥70% validation recall (irrigated fields: ≥60%; rainfed: ≥75%).
The harvest-discrimination features (especially `drop_rate` and `season_progress`)
help the model distinguish drought stress (slow decline early in season) from
natural maturity and harvest (fast decline late in season).

## Reproduction

`python -B src/detect/causal_events_v3.py`

Compare v2 vs v3: `python -B src/detect/causal_events_v3.py --compare`
