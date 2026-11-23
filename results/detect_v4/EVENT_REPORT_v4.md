# Rabi early-drying risk: detect_v4 (Soil Moisture & Crop-Type Priors)

**Key Additions in detect_v4:**
- ERA5-Land Root-Zone and Surface Soil Moisture (8-day publication lag)
- 15-day rootzone moisture depletion trend
- Crop-Type Phenological Priors (derived from 2019-2021 reference training years)
- In-season phenological stage ratio and harvest risk interaction term

## Point-date metrics (new onsets, validation-selected model)

| horizon | model | n | positives | prevalence | roc_auc | average_precision | f05 | precision | recall |
|---|---|---|---|---|---|---|---|---|---|
| 7 | Ensemble weighted | 6833 | 144 | 0.021 | 0.897 | 0.130 | 0.174 | 0.150 | 0.486 |
| 15 | Ensemble weighted | 6833 | 292 | 0.043 | 0.903 | 0.220 | 0.209 | 0.176 | 0.801 |
| 30 | XGBoost | 6833 | 527 | 0.077 | 0.877 | 0.298 | 0.327 | 0.324 | 0.340 |

## Unique point-season events (validation-selected model)

| horizon | model | monitored_events | caught_events | recall_all_events | warned_point_seasons | warning_precision | median_lead |
|---|---|---|---|---|---|---|---|
| 7 | Ensemble weighted | 108 | 46 | 0.426 | 147 | 0.313 | 5.000 |
| 15 | Ensemble weighted | 108 | 71 | 0.657 | 217 | 0.327 | 12.000 |
| 30 | XGBoost | 108 | 67 | 0.620 | 179 | 0.374 | 21.000 |

## Interpretation

By integrating physical rootzone soil moisture and phenological crop-type priors,
the model distinguishes between true drought-induced moisture stress and normal
post-maturity crop harvest in moist, irrigated fields.

## Reproduction

`python -B src/detect/causal_events_v4.py`

Compare across versions: `python -B src/detect/causal_events_v4.py --compare`
