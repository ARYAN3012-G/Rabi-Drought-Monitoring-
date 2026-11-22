# Rabi forecast v1 + amendment A1 - results (15-day NDVI forecast)

Rules: `docs/FORECAST_v1.md` incl. amendment A1 (climatology at issue+15 days; frozen-calibration weather from data/prepared; weather available 8 days late). Supersedes the first run (c976795). Chronological test: trained 2019-20 .. 2022-23 (early stopping on 2022-23), tested 2023-24, 2024-25, 2025-26. Historical development evidence (seasons known during design), not a real-time test.

Trees chosen on validation: XGBoost 123, XGBoost satellite-only 112, XGBoost weather 1-day (sensitivity) 39

## Eligibility

Potential forecasts 342900; usable 233020 (68.0%). Excluded: latest observation > 12 days old 54260; no observation within t+15 +- 3 days 55620. Excluded = missing data, not 'no crop'.

## Accuracy (MAE of NDVI, lower is better) - all eligible points

| season | cls | n | MAE XGBoost | MAE XGBoost satellite-only | MAE XGBoost weather 1-day (sensitivity) | MAE Persistence | MAE Climatology | MAE Anomaly persistence | best baseline | skill vs best |
|---|---|---|---|---|---|---|---|---|---|---|
| pooled | all | 105594 | 0.0524 | 0.0509 | 0.0511 | 0.0641 | 0.0909 | 0.0624 | Anomaly persistence | 0.16 |
| pooled | rainfed | 70419 | 0.0429 | 0.0411 | 0.0416 | 0.0554 | 0.0747 | 0.0514 | Anomaly persistence | 0.165 |
| pooled | irrigated | 35175 | 0.0712 | 0.0704 | 0.0703 | 0.0814 | 0.1233 | 0.0845 | Persistence | 0.125 |
| 2023-24 | all | 35508 | 0.0496 | 0.0465 | 0.0451 | 0.0535 | 0.0983 | 0.0584 | Persistence | 0.073 |
| 2023-24 | rainfed | 23722 | 0.0414 | 0.0373 | 0.0364 | 0.0452 | 0.0816 | 0.047 | Persistence | 0.084 |
| 2023-24 | irrigated | 11786 | 0.0663 | 0.065 | 0.0627 | 0.0702 | 0.1317 | 0.0814 | Persistence | 0.056 |
| 2024-25 | all | 32880 | 0.051 | 0.0508 | 0.052 | 0.068 | 0.0823 | 0.0609 | Anomaly persistence | 0.163 |
| 2024-25 | rainfed | 21872 | 0.0403 | 0.0404 | 0.0413 | 0.0589 | 0.0667 | 0.0498 | Anomaly persistence | 0.191 |
| 2024-25 | irrigated | 11008 | 0.0723 | 0.0716 | 0.0731 | 0.0861 | 0.1135 | 0.0829 | Anomaly persistence | 0.128 |
| 2025-26 | all | 37206 | 0.0562 | 0.0551 | 0.0561 | 0.0707 | 0.0914 | 0.0676 | Anomaly persistence | 0.169 |
| 2025-26 | rainfed | 24825 | 0.0468 | 0.0454 | 0.0467 | 0.0622 | 0.0751 | 0.0569 | Anomaly persistence | 0.178 |
| 2025-26 | irrigated | 12381 | 0.075 | 0.0745 | 0.075 | 0.0878 | 0.1241 | 0.0889 | Persistence | 0.146 |

## Accuracy - established at issue

| season | cls | n | MAE XGBoost | MAE XGBoost satellite-only | MAE XGBoost weather 1-day (sensitivity) | MAE Persistence | MAE Climatology | MAE Anomaly persistence | best baseline | skill vs best |
|---|---|---|---|---|---|---|---|---|---|---|
| pooled | all | 86456 | 0.0498 | 0.0486 | 0.049 | 0.0618 | 0.0898 | 0.0597 | Anomaly persistence | 0.166 |
| pooled | rainfed | 56371 | 0.0391 | 0.0376 | 0.0384 | 0.0521 | 0.071 | 0.0473 | Anomaly persistence | 0.173 |
| pooled | irrigated | 30085 | 0.0698 | 0.0692 | 0.0689 | 0.0801 | 0.1251 | 0.083 | Persistence | 0.129 |
| 2023-24 | all | 27484 | 0.0464 | 0.0441 | 0.0431 | 0.0523 | 0.0965 | 0.0563 | Persistence | 0.113 |
| 2023-24 | rainfed | 17544 | 0.0359 | 0.0328 | 0.0327 | 0.0424 | 0.0754 | 0.0429 | Persistence | 0.153 |
| 2023-24 | irrigated | 9940 | 0.0649 | 0.064 | 0.0614 | 0.0697 | 0.1337 | 0.0801 | Persistence | 0.069 |
| 2024-25 | all | 27749 | 0.0492 | 0.0489 | 0.0501 | 0.0654 | 0.0818 | 0.0585 | Anomaly persistence | 0.159 |
| 2024-25 | rainfed | 18303 | 0.0377 | 0.0377 | 0.0386 | 0.0549 | 0.0648 | 0.0463 | Anomaly persistence | 0.186 |
| 2024-25 | irrigated | 9446 | 0.0714 | 0.0707 | 0.0724 | 0.0858 | 0.1146 | 0.0822 | Anomaly persistence | 0.131 |
| 2025-26 | all | 31223 | 0.0533 | 0.0523 | 0.0532 | 0.0671 | 0.091 | 0.0637 | Anomaly persistence | 0.163 |
| 2025-26 | rainfed | 20524 | 0.043 | 0.0417 | 0.043 | 0.0579 | 0.0727 | 0.052 | Anomaly persistence | 0.173 |
| 2025-26 | irrigated | 10699 | 0.0729 | 0.0727 | 0.0727 | 0.0846 | 0.1263 | 0.0863 | Persistence | 0.138 |

## December - March issue dates only (class all)

| population | season | n | MAE XGBoost | MAE XGBoost satellite-only | MAE XGBoost weather 1-day (sensitivity) | MAE Persistence | MAE Climatology | MAE Anomaly persistence | best baseline | skill vs best |
|---|---|---|---|---|---|---|---|---|---|---|
| all | pooled | 81833 | 0.0483 | 0.047 | 0.0471 | 0.0614 | 0.0886 | 0.0571 | Anomaly persistence | 0.154 |
| all | 2023-24 | 26790 | 0.0438 | 0.0419 | 0.0404 | 0.052 | 0.094 | 0.0521 | Persistence | 0.158 |
| all | 2024-25 | 25687 | 0.0481 | 0.0477 | 0.0486 | 0.0649 | 0.0816 | 0.0569 | Anomaly persistence | 0.155 |
| all | 2025-26 | 29356 | 0.0525 | 0.051 | 0.052 | 0.0669 | 0.0897 | 0.0617 | Anomaly persistence | 0.149 |
| established | pooled | 73132 | 0.0488 | 0.0477 | 0.0479 | 0.0617 | 0.0901 | 0.0581 | Anomaly persistence | 0.16 |
| established | 2023-24 | 22715 | 0.045 | 0.0434 | 0.0419 | 0.0535 | 0.0973 | 0.0547 | Persistence | 0.159 |
| established | 2024-25 | 23424 | 0.0484 | 0.048 | 0.0489 | 0.0644 | 0.0823 | 0.0572 | Anomaly persistence | 0.154 |
| established | 2025-26 | 26993 | 0.0524 | 0.0512 | 0.052 | 0.0661 | 0.0909 | 0.0617 | Anomaly persistence | 0.151 |

## Acceptance rule (main model = XGBoost with 8-day-delayed weather)

- Beats every baseline in each test season: **yes** (December - March only: yes)
- Pooled MAE(XGBoost) - MAE(Anomaly persistence), 95 % CI: bootstrap over points [-0.0109, -0.0093]; over weather cells (only 5 cells, indicative) [-0.0146, -0.0063]
- **Verdict: passes the pre-registered rule**

## Does weather help?

Pooled MAE(with weather) - MAE(satellite-only), 95 % CI over points: [0.0014, 0.0016] (negative = weather helps).

## Decline from the latest observation to the forecast target (established points; event = change <= -0.1; 11802 events in 86456 forecasts)

Span from the latest observation to the target: median 20 days (range 15-30). The event does not distinguish drought from harvest.

| method | AUC | precision | recall | flagged |
|---|---|---|---|---|
| XGBoost | 0.825 | 0.596 | 0.303 | 5989 |
| XGBoost satellite-only | 0.831 | 0.603 | 0.306 | 5993 |
| XGBoost weather 1-day (sensitivity) | 0.833 | 0.63 | 0.203 | 3802 |
| Persistence | 0.5 |  | 0.0 | 0 |
| Climatology | 0.777 | 0.394 | 0.558 | 16720 |
| Anomaly persistence | 0.649 | 0.356 | 0.211 | 6990 |

## Feature importance (gain share, main model)

| feature | gain share |
|---|---|
| ndvi_15 | 0.143 |
| irr | 0.112 |
| clim_target | 0.083 |
| ndvi_30 | 0.079 |
| season_min | 0.066 |
| ndvi_last | 0.059 |
| tmax_15 | 0.039 |
| doy_issue | 0.039 |
| rain90 | 0.038 |
| wb60 | 0.03 |
| chg30 | 0.029 |
| chg15 | 0.028 |
