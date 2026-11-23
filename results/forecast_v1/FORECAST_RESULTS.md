# Rabi forecast v1 - results (15-day NDVI forecast)

Rules fixed before training in `docs/FORECAST_v1.md`. Chronological test: trained on 2019-20 .. 2022-23 (early stopping on 2022-23, 41 trees), tested on 2023-24, 2024-25, 2025-26. The seasons were known while the rabi project was designed: historical development evidence, not a real-time test.

## Eligibility

Potential forecasts 342900; usable 233020 (68.0%). Excluded: no recent observation (latest > 12 days old) 54260, no target within t+15 +- 3 days 55620. Excluded forecasts are missing data, not 'no crop'.

| season | no_recent_obs | no_target | ok |
|---|---|---|---|
| 2019 | 9947 | 9947 | 30056 |
| 2020 | 8438 | 8862 | 31300 |
| 2021 | 8836 | 9282 | 30482 |
| 2022 | 5538 | 7474 | 35588 |
| 2023 | 5652 | 8790 | 35508 |
| 2024 | 9306 | 6414 | 32880 |
| 2025 | 6543 | 4851 | 37206 |

## Accuracy (MAE of NDVI, lower is better) - all eligible points

| season | cls | n | MAE XGBoost | MAE Persistence | MAE Climatology | MAE Anomaly persistence | best baseline | skill vs best |
|---|---|---|---|---|---|---|---|---|
| pooled | all | 105594 | 0.051 | 0.0641 | 0.0902 | 0.0627 | Anomaly persistence | 0.187 |
| pooled | rainfed | 70419 | 0.0414 | 0.0554 | 0.074 | 0.0516 | Anomaly persistence | 0.198 |
| pooled | irrigated | 35175 | 0.0703 | 0.0814 | 0.1227 | 0.085 | Persistence | 0.136 |
| 2023-24 | all | 35508 | 0.0451 | 0.0535 | 0.0979 | 0.0587 | Persistence | 0.157 |
| 2023-24 | rainfed | 23722 | 0.0362 | 0.0452 | 0.0812 | 0.0472 | Persistence | 0.199 |
| 2023-24 | irrigated | 11786 | 0.0629 | 0.0702 | 0.1315 | 0.0819 | Persistence | 0.104 |
| 2024-25 | all | 32880 | 0.0517 | 0.068 | 0.0818 | 0.0608 | Anomaly persistence | 0.15 |
| 2024-25 | rainfed | 21872 | 0.0411 | 0.0589 | 0.0659 | 0.0498 | Anomaly persistence | 0.175 |
| 2024-25 | irrigated | 11008 | 0.0728 | 0.0861 | 0.1132 | 0.0828 | Anomaly persistence | 0.121 |
| 2025-26 | all | 37206 | 0.056 | 0.0707 | 0.0903 | 0.0681 | Anomaly persistence | 0.178 |
| 2025-26 | rainfed | 24825 | 0.0466 | 0.0622 | 0.0741 | 0.0573 | Anomaly persistence | 0.187 |
| 2025-26 | irrigated | 12381 | 0.075 | 0.0878 | 0.1228 | 0.0898 | Persistence | 0.146 |

## Accuracy - points established at issue

| season | cls | n | MAE XGBoost | MAE Persistence | MAE Climatology | MAE Anomaly persistence | best baseline | skill vs best |
|---|---|---|---|---|---|---|---|---|
| pooled | all | 86456 | 0.0489 | 0.0618 | 0.0892 | 0.0601 | Anomaly persistence | 0.186 |
| pooled | rainfed | 56371 | 0.0383 | 0.0521 | 0.0703 | 0.0476 | Anomaly persistence | 0.195 |
| pooled | irrigated | 30085 | 0.0689 | 0.0801 | 0.1246 | 0.0836 | Persistence | 0.14 |
| 2023-24 | all | 27484 | 0.0433 | 0.0523 | 0.0962 | 0.0566 | Persistence | 0.172 |
| 2023-24 | rainfed | 17544 | 0.0327 | 0.0424 | 0.0751 | 0.0431 | Persistence | 0.229 |
| 2023-24 | irrigated | 9940 | 0.0618 | 0.0697 | 0.1335 | 0.0806 | Persistence | 0.113 |
| 2024-25 | all | 27749 | 0.0498 | 0.0654 | 0.0812 | 0.0585 | Anomaly persistence | 0.149 |
| 2024-25 | rainfed | 18303 | 0.0383 | 0.0549 | 0.0641 | 0.0463 | Anomaly persistence | 0.173 |
| 2024-25 | irrigated | 9446 | 0.0721 | 0.0858 | 0.1143 | 0.0822 | Anomaly persistence | 0.123 |
| 2025-26 | all | 31223 | 0.0531 | 0.0671 | 0.0901 | 0.0646 | Anomaly persistence | 0.178 |
| 2025-26 | rainfed | 20524 | 0.0429 | 0.0579 | 0.0717 | 0.0526 | Anomaly persistence | 0.184 |
| 2025-26 | irrigated | 10699 | 0.0728 | 0.0846 | 0.1253 | 0.0876 | Persistence | 0.139 |

## Acceptance rule

- XGBoost beats every baseline in each test season: **yes**
- Pooled MAE(XGBoost) - MAE(Anomaly persistence), 95 % cluster-bootstrap CI over points: [-0.0125, -0.0109]
- **Verdict: USEFUL (passes the pre-registered rule)**

## Deterioration (established points, event = 15-day drop <= -0.1; 11802 events in 86456 forecasts)

| method | AUC | precision | recall | flagged |
|---|---|---|---|---|
| XGBoost | 0.833 | 0.63 | 0.21 | 3925 |
| Persistence | 0.5 |  | 0.0 | 0 |
| Climatology | 0.782 | 0.396 | 0.574 | 17091 |
| Anomaly persistence | 0.658 | 0.354 | 0.239 | 7989 |

## Feature importance (gain share, final model)

| feature | gain share |
|---|---|
| ndvi_15 | 0.249 |
| ndvi_30 | 0.079 |
| clim_target | 0.074 |
| irr | 0.069 |
| ndvi_last | 0.066 |
| season_min | 0.063 |
| chg15 | 0.035 |
| rain90 | 0.032 |
| tmax_15 | 0.031 |
| chg30 | 0.027 |
| doy_issue | 0.026 |
| rain30 | 0.026 |
