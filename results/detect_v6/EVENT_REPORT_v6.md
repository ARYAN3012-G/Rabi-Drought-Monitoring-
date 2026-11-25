# Rabi early-drying risk: detect_v6 (corrected detect_v5)

Validation-selected model, DETECT_v3 registered F0.5 thresholds (irrigated / rainfed), no soil veto; every warning tagged with the drought v2 soil percentile. Evaluation 2023-24..2025-26, unique point-season events, 95 % point-cluster bootstrap. Protocol: `docs/DETECT_v6.md`.

## Selected model, pooled

| horizon | model | monitored_events | caught_events | recall_all_events | recall_lo | recall_hi | warned_point_seasons | warning_precision | precision_lo | precision_hi | median_lead |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 7 | Random forest | 108 | 20 | 0.185 | 0.106 | 0.273 | 81 | 0.247 | 0.140 | 0.360 | 5.000 |
| 15 | Ensemble weighted | 108 | 9 | 0.083 | 0.031 | 0.142 | 29 | 0.310 | 0.148 | 0.480 | 11.000 |
| 30 | Random forest | 108 | 30 | 0.278 | 0.200 | 0.360 | 56 | 0.536 | 0.422 | 0.656 | 16.000 |

## Selected model, by season

| horizon | season | monitored_events | caught_events | warned_point_seasons | warning_precision | recall_all_events |
|---|---|---|---|---|---|---|
| 7 | 2023 | 59 | 13 | 36 | 0.361 | 0.220 |
| 7 | 2024 | 33 | 2 | 23 | 0.087 | 0.061 |
| 7 | 2025 | 16 | 5 | 22 | 0.227 | 0.312 |
| 15 | 2023 | 59 | 6 | 11 | 0.545 | 0.102 |
| 15 | 2024 | 33 | 2 | 12 | 0.167 | 0.061 |
| 15 | 2025 | 16 | 1 | 6 | 0.167 | 0.062 |
| 30 | 2023 | 59 | 20 | 30 | 0.667 | 0.339 |
| 30 | 2024 | 33 | 4 | 11 | 0.364 | 0.121 |
| 30 | 2025 | 16 | 6 | 15 | 0.400 | 0.375 |

## Warnings by soil context (selected model; tag from the first warning of the point-season)

| horizon | soil_tag | warned | correct | precision |
|---|---|---|---|---|
| 7 | soil-dry | 36 | 13 | 0.361 |
| 7 | soil-wet | 45 | 7 | 0.156 |
| 15 | soil-dry | 11 | 6 | 0.545 |
| 15 | soil-wet | 18 | 3 | 0.167 |
| 30 | soil-dry | 30 | 20 | 0.667 |
| 30 | soil-wet | 26 | 10 | 0.385 |

Soil-dry = cell root-zone percentile below its own 1990-2004 normal at issue - 8 days. The tag is context, not a filter; it was examined on these test seasons before (COMBINED_v1), so its contrast here is descriptive. Its independent test is docs/MODIS_TEST_v1.md.