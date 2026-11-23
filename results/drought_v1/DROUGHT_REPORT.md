# Rabi regional soil-moisture drought prediction

Development experiment, 23 November 2026. This predicts a future root-zone water-deficit indicator; it does not relabel satellite early drying as drought. It is a regional, modelled-soil target, not verified field crop loss or an official drought declaration.

**Evaluation limitation:** the 2023-2025 evaluation has no <=20th-percentile drought targets. Detection recall, drought AP and ROC-AUC are not estimable. These seasons only assess false alerts and scores under non-drought conditions. Neither no alerts nor high accuracy would prove drought-prediction skill. The threshold/reference are retained unchanged; no labels were altered to manufacture dry cases.

## What is predicted

For issues every five days during Dec-Mar, predict the class of seven-day mean root-zone water ending 7/15/30 days ahead. The entire target window is future. <=20th historical percentile is soil-moisture drought; <=10th is severe-or-worse deficit. Reference: 1981-2000 only, calendar-day +/-15 days. Above 20 is not a crop-health guarantee.

Train: rabi 2001-02 through 2016-17. Validate: 2017-18 through 2022-23. Historical evaluation: 2023-24 through 2025-26. Both soil and weather inputs end eight days before issue. Model and threshold selection are validation-only and saved before evaluation. Final reanalysis may differ from original release vintages.

## Selected results

| horizon | model | n | drought_cases | macro_f1 | drought_ap | drought_auc | brier | precision | recall | warnings |
|---|---|---|---|---|---|---|---|---|---|---|
| 7 | HGB leaves7 soil | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 15 | HGB leaves7 soil | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 30 | HGB leaves15 soil | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |

Precision/recall refer to repeated cell-issue forecasts, not independent drought episodes. Learned-score thresholds maximize validation F0.5 while retaining >=50% validation recall. Deterministic persistence/trend rules retain threshold 0.5. This favors fewer false warnings; evaluation recall is not constrained. Risk scores are not asserted calibrated.

## Strong baselines on identical rows

| horizon | model | n | drought_cases | macro_f1 | drought_ap | drought_auc | brier | precision | recall | warnings |
|---|---|---|---|---|---|---|---|---|---|---|
| 7 | Percentile persistence | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 7 | Conditional transition | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 7 | Soil analog k25 | 375 | 0 | 0.333 | - | - | 0.002 | - | - | 0 |
| 15 | Percentile persistence | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 15 | Conditional transition | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 15 | Soil analog k25 | 375 | 0 | 0.333 | - | - | 0.003 | - | - | 0 |
| 30 | Percentile persistence | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 30 | Conditional transition | 375 | 0 | 0.333 | - | - | 0.002 | - | - | 0 |
| 30 | Soil analog k25 | 375 | 0 | 0.333 | - | - | 0.005 | 0.000 | - | 3 |

## New-onset subset

Rows where the true issue-day soil indicator is not already dry. This issue-day truth is retrospective evaluation information only; the model still uses data dated issue-8 days. Many forecast positives in the full table are drought continuation, not new onset.

| horizon | model | n | drought_cases | macro_f1 | drought_ap | drought_auc | brier | precision | recall | warnings |
|---|---|---|---|---|---|---|---|---|---|---|
| 7 | Percentile persistence | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 7 | HGB leaves7 soil | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 15 | Percentile persistence | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 15 | HGB leaves7 soil | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 30 | Percentile persistence | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 30 | HGB leaves15 soil | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |

## Per-season selected results

| group | horizon | model | n | drought_cases | macro_f1 | drought_ap | drought_auc | brier | precision | recall | warnings |
|---|---|---|---|---|---|---|---|---|---|---|---|
| season:2023 | 7 | HGB leaves7 soil | 125 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| season:2024 | 7 | HGB leaves7 soil | 125 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| season:2025 | 7 | HGB leaves7 soil | 125 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| season:2023 | 15 | HGB leaves7 soil | 125 | 0 | 0.333 | - | - | 0.003 | - | - | 0 |
| season:2024 | 15 | HGB leaves7 soil | 125 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| season:2025 | 15 | HGB leaves7 soil | 125 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| season:2023 | 30 | HGB leaves15 soil | 125 | 0 | 0.333 | - | - | 0.002 | - | - | 0 |
| season:2024 | 30 | HGB leaves15 soil | 125 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| season:2025 | 30 | HGB leaves15 soil | 125 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |

## Validation comparison (model selection)

| horizon | model | drought_ap | brier | precision | recall | threshold |
|---|---|---|---|---|---|---|
| 7 | Percentile persistence | 0.567 | 0.027 | 0.674 | 0.829 | 0.500 |
| 7 | Seasonal climatology | 0.110 | 0.048 | 0.120 | 0.514 | 0.150 |
| 7 | Conditional transition | 0.744 | 0.018 | 0.829 | 0.829 | 0.679 |
| 7 | Damped trend | 0.531 | 0.028 | 0.675 | 0.771 | 0.500 |
| 7 | Logistic soil | 0.758 | 0.022 | 0.783 | 0.514 | 0.594 |
| 7 | RF leaf5 soil | 0.794 | 0.018 | 0.833 | 0.714 | 0.756 |
| 7 | RF leaf15 soil | 0.811 | 0.018 | 0.794 | 0.771 | 0.655 |
| 7 | HGB leaves7 soil | 0.848 | 0.017 | 0.800 | 0.686 | 0.580 |
| 7 | HGB leaves15 soil | 0.832 | 0.017 | 0.765 | 0.743 | 0.567 |
| 7 | Logistic soil+weather | 0.700 | 0.026 | 0.783 | 0.514 | 0.676 |
| 7 | RF leaf5 soil+weather | 0.687 | 0.020 | 0.794 | 0.771 | 0.667 |
| 7 | RF leaf15 soil+weather | 0.676 | 0.020 | 0.765 | 0.743 | 0.709 |
| 7 | HGB leaves7 soil+weather | 0.776 | 0.021 | 0.826 | 0.543 | 0.839 |
| 7 | HGB leaves15 soil+weather | 0.728 | 0.022 | 0.815 | 0.629 | 0.795 |
| 7 | Soil analog k25 | 0.838 | 0.019 | 0.826 | 0.543 | 0.610 |
| 7 | Equal learned ensemble | 0.796 | 0.018 | 0.794 | 0.771 | 0.502 |
| 15 | Percentile persistence | 0.419 | 0.036 | 0.535 | 0.767 | 0.500 |
| 15 | Seasonal climatology | 0.099 | 0.043 | 0.087 | 0.867 | 0.131 |
| 15 | Conditional transition | 0.654 | 0.021 | 0.677 | 0.700 | 0.642 |
| 15 | Damped trend | 0.323 | 0.044 | 0.465 | 0.667 | 0.500 |
| 15 | Logistic soil | 0.614 | 0.025 | 0.593 | 0.533 | 0.461 |
| 15 | RF leaf5 soil | 0.636 | 0.021 | 0.696 | 0.533 | 0.743 |
| 15 | RF leaf15 soil | 0.608 | 0.023 | 0.647 | 0.733 | 0.561 |
| 15 | HGB leaves7 soil | 0.681 | 0.021 | 0.789 | 0.500 | 0.866 |
| 15 | HGB leaves15 soil | 0.636 | 0.021 | 0.789 | 0.500 | 0.873 |
| 15 | Logistic soil+weather | 0.542 | 0.031 | 0.452 | 0.633 | 0.432 |
| 15 | RF leaf5 soil+weather | 0.530 | 0.025 | 0.579 | 0.733 | 0.546 |
| 15 | RF leaf15 soil+weather | 0.495 | 0.025 | 0.579 | 0.733 | 0.549 |
| 15 | HGB leaves7 soil+weather | 0.587 | 0.030 | 0.500 | 0.500 | 0.540 |
| 15 | HGB leaves15 soil+weather | 0.610 | 0.029 | 0.529 | 0.600 | 0.479 |
| 15 | Soil analog k25 | 0.589 | 0.024 | 0.511 | 0.767 | 0.410 |
| 15 | Equal learned ensemble | 0.578 | 0.022 | 0.605 | 0.767 | 0.394 |
| 30 | Percentile persistence | 0.157 | 0.061 | 0.302 | 0.448 | 0.500 |
| 30 | Seasonal climatology | 0.071 | 0.042 | 0.074 | 1.000 | 0.106 |
| 30 | Conditional transition | 0.418 | 0.030 | 0.393 | 0.828 | 0.275 |
| 30 | Damped trend | 0.224 | 0.057 | 0.354 | 0.586 | 0.500 |
| 30 | Logistic soil | 0.396 | 0.032 | 0.278 | 0.862 | 0.141 |
| 30 | RF leaf5 soil | 0.387 | 0.031 | 0.441 | 0.517 | 0.347 |
| 30 | RF leaf15 soil | 0.347 | 0.032 | 0.400 | 0.621 | 0.289 |
| 30 | HGB leaves7 soil | 0.487 | 0.030 | 0.500 | 0.517 | 0.336 |
| 30 | HGB leaves15 soil | 0.537 | 0.031 | 0.556 | 0.517 | 0.440 |
| 30 | Logistic soil+weather | 0.309 | 0.040 | 0.248 | 0.897 | 0.080 |
| 30 | RF leaf5 soil+weather | 0.379 | 0.031 | 0.500 | 0.517 | 0.461 |
| 30 | RF leaf15 soil+weather | 0.375 | 0.031 | 0.441 | 0.517 | 0.372 |
| 30 | HGB leaves7 soil+weather | 0.500 | 0.032 | 0.500 | 0.517 | 0.513 |
| 30 | HGB leaves15 soil+weather | 0.493 | 0.031 | 0.500 | 0.517 | 0.504 |
| 30 | Soil analog k25 | 0.306 | 0.032 | 0.328 | 0.724 | 0.292 |
| 30 | Equal learned ensemble | 0.411 | 0.030 | 0.441 | 0.517 | 0.359 |

## All fixed candidates, historical evaluation

| horizon | model | n | drought_cases | macro_f1 | drought_ap | drought_auc | brier | precision | recall | warnings |
|---|---|---|---|---|---|---|---|---|---|---|
| 7 | Percentile persistence | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 7 | Seasonal climatology | 375 | 0 | 0.333 | - | - | 0.015 | 0.000 | - | 75 |
| 7 | Conditional transition | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 7 | Damped trend | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 7 | Logistic soil | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 7 | RF leaf5 soil | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 7 | RF leaf15 soil | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 7 | HGB leaves7 soil | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 7 | HGB leaves15 soil | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 7 | Logistic soil+weather | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 7 | RF leaf5 soil+weather | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 7 | RF leaf15 soil+weather | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 7 | HGB leaves7 soil+weather | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 7 | HGB leaves15 soil+weather | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 7 | Soil analog k25 | 375 | 0 | 0.333 | - | - | 0.002 | - | - | 0 |
| 7 | Equal learned ensemble | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 15 | Percentile persistence | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 15 | Seasonal climatology | 375 | 0 | 0.333 | - | - | 0.014 | 0.000 | - | 150 |
| 15 | Conditional transition | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 15 | Damped trend | 375 | 0 | 0.332 | - | - | 0.008 | 0.000 | - | 3 |
| 15 | Logistic soil | 375 | 0 | 0.333 | - | - | 0.002 | - | - | 0 |
| 15 | RF leaf5 soil | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 15 | RF leaf15 soil | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 15 | HGB leaves7 soil | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 15 | HGB leaves15 soil | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 15 | Logistic soil+weather | 375 | 0 | 0.333 | - | - | 0.003 | - | - | 0 |
| 15 | RF leaf5 soil+weather | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 15 | RF leaf15 soil+weather | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 15 | HGB leaves7 soil+weather | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 15 | HGB leaves15 soil+weather | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 15 | Soil analog k25 | 375 | 0 | 0.333 | - | - | 0.003 | - | - | 0 |
| 15 | Equal learned ensemble | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 30 | Percentile persistence | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 30 | Seasonal climatology | 375 | 0 | 0.333 | - | - | 0.012 | 0.000 | - | 195 |
| 30 | Conditional transition | 375 | 0 | 0.333 | - | - | 0.002 | - | - | 0 |
| 30 | Damped trend | 375 | 0 | 0.331 | - | - | 0.013 | 0.000 | - | 5 |
| 30 | Logistic soil | 375 | 0 | 0.333 | - | - | 0.002 | 0.000 | - | 9 |
| 30 | RF leaf5 soil | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 30 | RF leaf15 soil | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 30 | HGB leaves7 soil | 375 | 0 | 0.333 | - | - | 0.000 | - | - | 0 |
| 30 | HGB leaves15 soil | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 30 | Logistic soil+weather | 375 | 0 | 0.333 | - | - | 0.004 | 0.000 | - | 33 |
| 30 | RF leaf5 soil+weather | 375 | 0 | 0.333 | - | - | 0.002 | - | - | 0 |
| 30 | RF leaf15 soil+weather | 375 | 0 | 0.333 | - | - | 0.002 | - | - | 0 |
| 30 | HGB leaves7 soil+weather | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 30 | HGB leaves15 soil+weather | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |
| 30 | Soil analog k25 | 375 | 0 | 0.333 | - | - | 0.005 | 0.000 | - | 3 |
| 30 | Equal learned ensemble | 375 | 0 | 0.333 | - | - | 0.001 | - | - | 0 |

## Coverage and limits

5 soil/weather cells, not 1,350 independent soil locations. No field-level irrigation estimate; apply regional risk primarily to rainfed contexts. ERA5-Land and AgERA5 share atmospheric forcing, so the target is not independent field evidence. Thresholds describe relative rarity rather than crop-specific wilting or yield loss. Crop variety, rooting depth, sowing and irrigation can change impacts. No claims of perfectly detecting agricultural drought or universal best model.

Evaluation seasons had been consulted in the broader project. New soil labels and this model comparison were specified before fitting, but this remains historical development evidence. Bootstrap intervals resample only three whole seasons, preserving cells jointly; their precision is limited.

## Reproduction and inference

`python -B src/drought/fetch_soil.py`

`python -B -m src.drought.run train`

`python -B -m src.drought.run predict --date 2026-03-01`

Inference uses only the saved models/reference and issue-time inputs. Missing data abstain. Dates outside Dec-Mar abstain. Historical predictions are explicitly marked as replay. Current satellite observations can contextualize crop exposure but do not establish the cause of stress.

## Additional historical stress check

After discovering the lack of evaluation drought cases, a separate chronological backtest was specified: train 2001-2013, validate 2014-2016, evaluate 2017-2019. See `backtest/`. This is an explicitly post hoc development diagnostic, not a fresh untouched test. It does not change the main frozen reference, models, thresholds or labels.

## Sources

- [ERA5-Land data and latency via Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api)
- [NOAA CPC percentile convention](https://www.cpc.ncep.noaa.gov/products/Drought/Monitoring/smp_body.shtml)
- [NIDIS soil moisture and drought](https://www.drought.gov/what-is-drought/soil-moisture-and-drought)
