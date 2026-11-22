# Rabi forecast v1 + amendment A1 - results (15-day NDVI forecast)

Rules: `docs/FORECAST_v1.md` incl. amendment A1 (climatology at issue+15 days; frozen-calibration weather from data/prepared; weather available 8 days late). Supersedes the first run (c976795). Chronological test: trained 2019-20 .. 2022-23 (early stopping on 2022-23), tested 2023-24, 2024-25, 2025-26. Historical development evidence (seasons known during design), not a real-time test.

Trees chosen on validation: XGBoost 57, XGBoost satellite-only 136, XGBoost weather 1-day (sensitivity) 41

## Eligibility

Potential forecasts 342900; usable 233020 (68.0%). Excluded: latest observation > 12 days old 54260; no observation within t+15 +- 3 days 55620. Excluded = missing data, not 'no crop'.

## Accuracy (MAE of NDVI, lower is better) - all eligible points

| season | cls | n | MAE XGBoost | MAE XGBoost satellite-only | MAE XGBoost weather 1-day (sensitivity) | MAE Persistence | MAE Climatology | MAE Anomaly persistence | best baseline | skill vs best |
|---|---|---|---|---|---|---|---|---|---|---|
| pooled | all | 105594 | 0.0511 | 0.0509 | 0.051 | 0.0641 | 0.0909 | 0.0623 | Anomaly persistence | 0.18 |
| pooled | rainfed | 70419 | 0.0415 | 0.0411 | 0.0415 | 0.0554 | 0.0747 | 0.0512 | Anomaly persistence | 0.189 |
| pooled | irrigated | 35175 | 0.0704 | 0.0705 | 0.0702 | 0.0814 | 0.1233 | 0.0845 | Persistence | 0.135 |
| 2023-24 | all | 35508 | 0.046 | 0.0466 | 0.045 | 0.0535 | 0.0983 | 0.0582 | Persistence | 0.14 |
| 2023-24 | rainfed | 23722 | 0.0371 | 0.0374 | 0.0362 | 0.0452 | 0.0816 | 0.0468 | Persistence | 0.179 |
| 2023-24 | irrigated | 11786 | 0.0639 | 0.065 | 0.0627 | 0.0702 | 0.1317 | 0.0813 | Persistence | 0.09 |
| 2024-25 | all | 32880 | 0.0512 | 0.0509 | 0.0519 | 0.068 | 0.0823 | 0.0608 | Anomaly persistence | 0.158 |
| 2024-25 | rainfed | 21872 | 0.0407 | 0.0404 | 0.0413 | 0.0589 | 0.0666 | 0.0498 | Anomaly persistence | 0.183 |
| 2024-25 | irrigated | 11008 | 0.0722 | 0.0716 | 0.0728 | 0.0861 | 0.1135 | 0.0828 | Anomaly persistence | 0.128 |
| 2025-26 | all | 37206 | 0.0559 | 0.0551 | 0.0561 | 0.0707 | 0.0914 | 0.0675 | Anomaly persistence | 0.172 |
| 2025-26 | rainfed | 24825 | 0.0464 | 0.0454 | 0.0467 | 0.0622 | 0.0751 | 0.0568 | Anomaly persistence | 0.183 |
| 2025-26 | irrigated | 12381 | 0.075 | 0.0747 | 0.0749 | 0.0878 | 0.1241 | 0.0889 | Persistence | 0.146 |

## Accuracy - established at issue

| season | cls | n | MAE XGBoost | MAE XGBoost satellite-only | MAE XGBoost weather 1-day (sensitivity) | MAE Persistence | MAE Climatology | MAE Anomaly persistence | best baseline | skill vs best |
|---|---|---|---|---|---|---|---|---|---|---|
| pooled | all | 86456 | 0.049 | 0.0487 | 0.0489 | 0.0618 | 0.0898 | 0.0597 | Anomaly persistence | 0.179 |
| pooled | rainfed | 56371 | 0.0382 | 0.0377 | 0.0383 | 0.0521 | 0.071 | 0.0473 | Anomaly persistence | 0.192 |
| pooled | irrigated | 30085 | 0.0691 | 0.0693 | 0.0688 | 0.0801 | 0.1251 | 0.083 | Persistence | 0.137 |
| 2023-24 | all | 27484 | 0.0439 | 0.0442 | 0.0431 | 0.0523 | 0.0965 | 0.0563 | Persistence | 0.161 |
| 2023-24 | rainfed | 17544 | 0.0331 | 0.033 | 0.0326 | 0.0424 | 0.0754 | 0.0429 | Persistence | 0.219 |
| 2023-24 | irrigated | 9940 | 0.0629 | 0.0641 | 0.0616 | 0.0697 | 0.1337 | 0.0801 | Persistence | 0.098 |
| 2024-25 | all | 27749 | 0.0494 | 0.0489 | 0.05 | 0.0654 | 0.0818 | 0.0585 | Anomaly persistence | 0.156 |
| 2024-25 | rainfed | 18303 | 0.038 | 0.0377 | 0.0386 | 0.0549 | 0.0648 | 0.0463 | Anomaly persistence | 0.179 |
| 2024-25 | irrigated | 9446 | 0.0714 | 0.0706 | 0.0721 | 0.0858 | 0.1146 | 0.0822 | Anomaly persistence | 0.131 |
| 2025-26 | all | 31223 | 0.0531 | 0.0524 | 0.0531 | 0.0671 | 0.091 | 0.0637 | Anomaly persistence | 0.166 |
| 2025-26 | rainfed | 20524 | 0.0427 | 0.0417 | 0.043 | 0.0579 | 0.0727 | 0.052 | Anomaly persistence | 0.179 |
| 2025-26 | irrigated | 10699 | 0.0729 | 0.0729 | 0.0726 | 0.0846 | 0.1263 | 0.0863 | Persistence | 0.138 |

## December - March issue dates only (class all)

| population | season | n | MAE XGBoost | MAE XGBoost satellite-only | MAE XGBoost weather 1-day (sensitivity) | MAE Persistence | MAE Climatology | MAE Anomaly persistence | best baseline | skill vs best |
|---|---|---|---|---|---|---|---|---|---|---|
| all | pooled | 81833 | 0.0473 | 0.0471 | 0.0471 | 0.0614 | 0.0886 | 0.057 | Anomaly persistence | 0.17 |
| all | 2023-24 | 26790 | 0.0412 | 0.0421 | 0.0404 | 0.052 | 0.094 | 0.0521 | Persistence | 0.208 |
| all | 2024-25 | 25687 | 0.0481 | 0.0478 | 0.0484 | 0.0649 | 0.0816 | 0.0569 | Anomaly persistence | 0.155 |
| all | 2025-26 | 29356 | 0.0521 | 0.051 | 0.052 | 0.0669 | 0.0897 | 0.0617 | Anomaly persistence | 0.156 |
| established | pooled | 73132 | 0.048 | 0.0478 | 0.0478 | 0.0617 | 0.0901 | 0.0581 | Anomaly persistence | 0.174 |
| established | 2023-24 | 22715 | 0.0427 | 0.0436 | 0.0418 | 0.0535 | 0.0973 | 0.0547 | Persistence | 0.202 |
| established | 2024-25 | 23424 | 0.0484 | 0.048 | 0.0488 | 0.0644 | 0.0823 | 0.0572 | Anomaly persistence | 0.154 |
| established | 2025-26 | 26993 | 0.0521 | 0.0512 | 0.052 | 0.0661 | 0.0909 | 0.0617 | Anomaly persistence | 0.156 |

## Acceptance rule (main model = XGBoost with 8-day-delayed weather)

- Beats every baseline in each test season: **yes** (December - March only: yes)
- Pooled MAE(XGBoost) - MAE(Anomaly persistence), 95 % CI: bootstrap over points [-0.0120, -0.0104]; over weather cells (only 5 cells, indicative) [-0.0150, -0.0076]
- **Verdict: passes the pre-registered rule**

## Does weather help?

Pooled MAE(with weather) - MAE(satellite-only), 95 % CI over points: [0.0001, 0.0003] (negative = weather helps).

## Decline from the latest observation to the forecast target (established points; event = change <= -0.1; 11802 events in 86456 forecasts)

Span from the latest observation to the target: median 20 days (range 15-30). The event does not distinguish drought from harvest.

| method | AUC | precision | recall | flagged |
|---|---|---|---|---|
| XGBoost | 0.829 | 0.621 | 0.244 | 4629 |
| XGBoost satellite-only | 0.83 | 0.604 | 0.321 | 6265 |
| XGBoost weather 1-day (sensitivity) | 0.833 | 0.64 | 0.204 | 3768 |
| Persistence | 0.5 |  | 0.0 | 0 |
| Climatology | 0.777 | 0.394 | 0.558 | 16718 |
| Anomaly persistence | 0.649 | 0.356 | 0.211 | 6988 |

## Feature importance (gain share, main model)

| feature | gain share |
|---|---|
| ndvi_15 | 0.205 |
| irr | 0.087 |
| ndvi_30 | 0.082 |
| clim_target | 0.075 |
| ndvi_last | 0.064 |
| season_min | 0.059 |
| doy_issue | 0.038 |
| rain90 | 0.033 |
| tmax_15 | 0.033 |
| chg30 | 0.032 |
| chg15 | 0.031 |
| et0_15 | 0.029 |
