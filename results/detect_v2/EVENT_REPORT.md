# Rabi early-drying risk: corrected historical evaluation and unique-event audit

Development correction v2, 22 November 2026. Supersedes detect_v1 for operational claims. Satellite-defined early drying is a proxy event; agricultural drought causation is not independently verified.

## Corrections and scope

- Removed retrospective completed-season status from inputs; all satellite features use only issue-time observations.
- Reference population, drying normals and NDVI curves use training seasons 2019-21 only (own season excluded).
- Weather uses an 8-day publication lag, including the early-December antecedent-rain feature.
- Forecasts target a new event within the horizon. Known/past events cannot earn advance-warning credit.
- Weights, thresholds and primary model are chosen on 2022-23 validation, not the historical evaluation seasons.
- v1 did not save thresholds/validation predictions, preventing an exact recount at its original operating point. Both are saved in v2. The cohort changed with the corrected reference; v1/v2 scores are not a same-cohort ablation.

## Coverage

| season | points | reference_ok | season_quality_ok | scorable | early_events | forecast_points | new_onset_training_or_evaluation_rows |
|---|---|---|---|---|---|---|---|
| 2019 | 1350 | 127 | 1350 | 127 | 27 | 92 | 1107 |
| 2020 | 1350 | 141 | 1350 | 141 | 9 | 96 | 1559 |
| 2021 | 1350 | 132 | 1350 | 132 | 16 | 103 | 1416 |
| 2022 | 1350 | 232 | 1345 | 232 | 18 | 149 | 2440 |
| 2023 | 1350 | 232 | 1350 | 232 | 59 | 148 | 1984 |
| 2024 | 1350 | 232 | 1350 | 232 | 33 | 161 | 2377 |
| 2025 | 1350 | 232 | 1350 | 232 | 17 | 145 | 2472 |

## New-onset point-date metrics (validation-selected model)

| horizon | model | n | positives | prevalence | roc_auc | average_precision | precision | recall |
|---|---|---|---|---|---|---|---|---|
| 7 | Random forest | 6833 | 144 | 0.021 | 0.925 | 0.175 | 0.075 | 0.958 |
| 15 | Random forest | 6833 | 292 | 0.043 | 0.914 | 0.312 | 0.162 | 0.897 |
| 30 | Random forest | 6833 | 527 | 0.077 | 0.905 | 0.372 | 0.242 | 0.920 |

## Unique point-season events (validation-selected model)

| horizon | model | monitored_events | events_with_opportunity | caught_events | recall_all_events | recall_opportunity | warned_point_seasons | warning_precision | median_lead |
|---|---|---|---|---|---|---|---|---|---|
| 7 | Random forest | 108 | 104 | 102 | 0.944 | 0.981 | 331 | 0.308 | 5.000 |
| 15 | Random forest | 108 | 106 | 101 | 0.935 | 0.953 | 305 | 0.331 | 12.000 |
| 30 | Random forest | 108 | 107 | 104 | 0.963 | 0.972 | 332 | 0.313 | 27.000 |

Each point-season contributes at most one event and one warned unit. Warning precision here is the fraction of warned point-seasons with at least one timely alert. It is not per-alert precision. Earlier false alerts are not erased from the saved point-date predictions. Lead time uses the first timely warning per caught event.

## Lead-time requirements

| horizon | model | recall_at_least_7_days | recall_at_least_14_days | lead_q25 | median_lead | lead_q75 |
|---|---|---|---|---|---|---|
| 7 | Random forest | 0.213 | 0.000 | 3.000 | 5.000 | 6.000 |
| 15 | Random forest | 0.843 | 0.120 | 11.000 | 12.000 | 13.000 |
| 30 | Random forest | 0.917 | 0.833 | 20.000 | 27.000 | 28.000 |

## Event uncertainty

| horizon | model | bootstrap_unit | clusters | recall_all_events_lo | recall_all_events_hi | recall_opportunity_lo | recall_opportunity_hi | warning_precision_lo | warning_precision_hi |
|---|---|---|---|---|---|---|---|---|---|
| 7 | Random forest | point_id | 232 | 0.897 | 0.981 | 0.951 | 1.000 | 0.253 | 0.361 |
| 7 | Random forest | cell | 5 | 0.846 | 0.974 | 0.944 | 1.000 | 0.252 | 0.365 |
| 15 | Random forest | point_id | 232 | 0.885 | 0.976 | 0.908 | 0.990 | 0.275 | 0.387 |
| 15 | Random forest | cell | 5 | 0.900 | 0.947 | 0.932 | 0.983 | 0.277 | 0.392 |
| 30 | Random forest | point_id | 232 | 0.922 | 0.992 | 0.938 | 1.000 | 0.259 | 0.370 |
| 30 | Random forest | cell | 5 | 0.944 | 0.984 | 0.944 | 1.000 | 0.267 | 0.372 |

Point resampling retains each point across seasons; weather-cell resampling is indicative with very few cells. Neither creates additional independent drought seasons.

## All models and baselines: new-onset point-dates

| horizon | model | selected | roc_auc | average_precision | precision | recall |
|---|---|---|---|---|---|---|
| 7 | Logistic regression | False | 0.838 | 0.076 | 0.045 | 0.951 |
| 7 | Random forest | True | 0.925 | 0.175 | 0.075 | 0.958 |
| 7 | XGBoost | False | 0.897 | 0.164 | 0.102 | 0.826 |
| 7 | Ensemble equal | False | 0.906 | 0.170 | 0.075 | 0.910 |
| 7 | Ensemble weighted | False | 0.923 | 0.177 | 0.094 | 0.931 |
| 7 | Below-normal baseline | False | 0.488 | 0.019 | 0.022 | 0.743 |
| 7 | Drop baseline | False | 0.490 | 0.019 | 0.028 | 0.792 |
| 7 | Early-drying rule | False | 0.497 | 0.021 | 0.000 | 0.000 |
| 7 | Zero-onset baseline | False | 0.500 | 0.021 | 0.000 | 0.000 |
| 15 | Logistic regression | False | 0.854 | 0.149 | 0.108 | 0.935 |
| 15 | Random forest | True | 0.914 | 0.312 | 0.162 | 0.897 |
| 15 | XGBoost | False | 0.885 | 0.227 | 0.153 | 0.842 |
| 15 | Ensemble equal | False | 0.902 | 0.273 | 0.147 | 0.877 |
| 15 | Ensemble weighted | False | 0.909 | 0.277 | 0.133 | 0.955 |
| 15 | Below-normal baseline | False | 0.465 | 0.037 | 0.040 | 0.599 |
| 15 | Drop baseline | False | 0.430 | 0.034 | 0.047 | 0.654 |
| 15 | Early-drying rule | False | 0.497 | 0.043 | 0.000 | 0.000 |
| 15 | Zero-onset baseline | False | 0.500 | 0.043 | 0.000 | 0.000 |
| 30 | Logistic regression | False | 0.881 | 0.289 | 0.195 | 0.956 |
| 30 | Random forest | True | 0.905 | 0.372 | 0.242 | 0.920 |
| 30 | XGBoost | False | 0.894 | 0.353 | 0.258 | 0.844 |
| 30 | Ensemble equal | False | 0.907 | 0.378 | 0.223 | 0.941 |
| 30 | Ensemble weighted | False | 0.907 | 0.373 | 0.244 | 0.934 |
| 30 | Below-normal baseline | False | 0.410 | 0.061 | 0.035 | 0.051 |
| 30 | Drop baseline | False | 0.349 | 0.057 | 0.077 | 1.000 |
| 30 | Early-drying rule | False | 0.498 | 0.077 | 0.000 | 0.000 |
| 30 | Zero-onset baseline | False | 0.500 | 0.077 | 0.000 | 0.000 |

## All models: unique events

| horizon | model | selected | caught_events | monitored_events | recall_all_events | warning_precision | median_lead |
|---|---|---|---|---|---|---|---|
| 7 | Logistic regression | False | 100 | 108 | 0.926 | 0.263 | 5.000 |
| 7 | Random forest | True | 102 | 108 | 0.944 | 0.308 | 5.000 |
| 7 | XGBoost | False | 89 | 108 | 0.824 | 0.317 | 5.000 |
| 7 | Ensemble equal | False | 96 | 108 | 0.889 | 0.342 | 5.000 |
| 7 | Ensemble weighted | False | 100 | 108 | 0.926 | 0.353 | 5.000 |
| 7 | Below-normal baseline | False | 79 | 108 | 0.731 | 0.183 | 5.000 |
| 7 | Drop baseline | False | 84 | 108 | 0.778 | 0.193 | 5.000 |
| 7 | Early-drying rule | False | 0 | 108 | 0.000 | 0.000 | - |
| 7 | Zero-onset baseline | False | 0 | 108 | 0.000 | - | - |
| 15 | Logistic regression | False | 103 | 108 | 0.954 | 0.302 | 12.000 |
| 15 | Random forest | True | 101 | 108 | 0.935 | 0.331 | 12.000 |
| 15 | XGBoost | False | 95 | 108 | 0.880 | 0.315 | 12.000 |
| 15 | Ensemble equal | False | 100 | 108 | 0.926 | 0.355 | 12.000 |
| 15 | Ensemble weighted | False | 104 | 108 | 0.963 | 0.323 | 12.000 |
| 15 | Below-normal baseline | False | 73 | 108 | 0.676 | 0.173 | 12.000 |
| 15 | Drop baseline | False | 88 | 108 | 0.815 | 0.202 | 11.000 |
| 15 | Early-drying rule | False | 0 | 108 | 0.000 | 0.000 | - |
| 15 | Zero-onset baseline | False | 0 | 108 | 0.000 | - | - |
| 30 | Logistic regression | False | 107 | 108 | 0.991 | 0.305 | 27.000 |
| 30 | Random forest | True | 104 | 108 | 0.963 | 0.313 | 27.000 |
| 30 | XGBoost | False | 101 | 108 | 0.935 | 0.327 | 26.000 |
| 30 | Ensemble equal | False | 107 | 108 | 0.991 | 0.338 | 27.000 |
| 30 | Ensemble weighted | False | 106 | 108 | 0.981 | 0.337 | 27.000 |
| 30 | Below-normal baseline | False | 12 | 108 | 0.111 | 0.052 | 17.500 |
| 30 | Drop baseline | False | 107 | 108 | 0.991 | 0.236 | 27.000 |
| 30 | Early-drying rule | False | 0 | 108 | 0.000 | 0.000 | - |
| 30 | Zero-onset baseline | False | 0 | 108 | 0.000 | - | - |

## Rainfall consistency check

Across 21 cell-seasons with at least 10 established reference-eligible points, Spearman rho = -0.423. The <80%-of-normal versus other-years contrast is not estimable: 0 qualifying dry cell-seasons and 21 other cell-seasons. Do not carry forward the v1 twofold-rate claim. This descriptive analysis uses all available development seasons. It is not an independent drought test.

## Limits on interpretation

The seven seasons were examined during development. The three evaluation seasons are excluded from fitting but are not a fresh prospective test. Sampled pixels are not verified fields. Crop identity, planting and harvest dates are unverified; normal crop timing changes can resemble drought. Retrospective phenology uses centered smoothing and two-image confirmation, so the nominal onset is an image-based date, not measured physiological stress onset. Long gaps can hide or delay crossings. The normal has only two or three training seasons. No observed crossing is not evidence of absence of water stress. Independent field/crop-water evidence is required before calling these alerts confirmed agricultural drought.

## Reproduction

`python -B src/detect/causal_events.py`
Operating points: `operating_points.json`; event ledger: `events.csv`; validation probabilities: `validation_predictions.csv.gz`; inputs and exclusions: `data/detect_v2/`.


## Always-warn sanity check (added after the primary v2 run)

| horizon | selected_model | model_caught | always_caught | total_events | model_warned_units | always_warned_units | model_unit_precision | always_unit_precision | model_first_timely_lead | always_first_timely_lead |
|---|---|---|---|---|---|---|---|---|---|---|
| 7 | Random forest | 102 | 104 | 108 | 331 | 453 | 0.308 | 0.230 | 5.000 | 5.000 |
| 15 | Random forest | 101 | 106 | 108 | 305 | 453 | 0.331 | 0.234 | 12.000 | 12.500 |
| 30 | Random forest | 104 | 107 | 108 | 332 | 453 | 0.313 | 0.236 | 27.000 | 27.000 |

Always warning at every usable issue can also catch almost every event. Therefore high unique-event recall and the first-timely lead alone are not evidence of strong discrimination. The selected model reduces the number of warned point-seasons, but still produces many false warnings. This fixed diagnostic did not alter the selected models, fitted parameters or thresholds.
