# Rabi drought v2 - results for the 8-site case-study paper

Districts of the 8 study sites (pre-2022 boundaries); Kurnool + Anantapur primary, Tumkur sensitivity. Outcomes: APY rabi multi-crop yield index (fixed weights, causal 5-season baseline) and sown-area anomaly. Seasons 2000-01..2022-23. Within-district Spearman rank correlation; 95 % intervals resample whole seasons. District statistics are impacts with other causes, not drought labels; this is district association, not field validation.

## 1. Monitoring: completed-season indicators vs crop outcomes (all seasons)

| scope | outcome | indicator | n | rho | ci |
|---|---|---|---|---|---|
| Kurnool + Anantapur | yield_index | deficit duration Nov-Feb | 46 | -0.58 | [-0.74, -0.36] |
| Kurnool + Anantapur | yield_index | severe deficit duration | 46 | -0.52 | [-0.68, -0.23] |
| Kurnool + Anantapur | yield_index | soil moisture at sowing | 46 | 0.55 | [+0.27, +0.73] |
| Kurnool + Anantapur | yield_index | mean soil percentile Nov-Feb | 46 | 0.43 | [+0.09, +0.68] |
| Kurnool + Anantapur | yield_index | rain Jun-Nov | 46 | 0.4 | [+0.07, +0.63] |
| Kurnool + Anantapur | yield_index | rain Nov-Feb | 46 | 0.01 | [-0.35, +0.39] |
| Kurnool + Anantapur | yield_index | SPEI-30 Oct-Nov | 46 | 0.44 | [+0.10, +0.68] |
| Kurnool + Anantapur | yield_index | SPEI-30 Nov-Feb | 46 | 0.39 | [+0.04, +0.64] |
| Kurnool + Anantapur | sown_area_anom | deficit duration Nov-Feb | 46 | -0.26 | [-0.54, +0.08] |
| Kurnool + Anantapur | sown_area_anom | severe deficit duration | 46 | -0.16 | [-0.47, +0.16] |
| Kurnool + Anantapur | sown_area_anom | soil moisture at sowing | 46 | 0.21 | [-0.16, +0.54] |
| Kurnool + Anantapur | sown_area_anom | mean soil percentile Nov-Feb | 46 | 0.23 | [-0.09, +0.54] |
| Kurnool + Anantapur | sown_area_anom | rain Jun-Nov | 46 | 0.13 | [-0.23, +0.48] |
| Kurnool + Anantapur | sown_area_anom | rain Nov-Feb | 46 | 0.23 | [-0.06, +0.47] |
| Kurnool + Anantapur | sown_area_anom | SPEI-30 Oct-Nov | 46 | 0.38 | [+0.04, +0.64] |
| Kurnool + Anantapur | sown_area_anom | SPEI-30 Nov-Feb | 46 | 0.24 | [-0.11, +0.53] |
| + Tumkur (sensitivity) | yield_index | deficit duration Nov-Feb | 69 | -0.54 | [-0.66, -0.34] |
| + Tumkur (sensitivity) | yield_index | severe deficit duration | 69 | -0.44 | [-0.61, -0.23] |
| + Tumkur (sensitivity) | yield_index | soil moisture at sowing | 69 | 0.54 | [+0.31, +0.68] |
| + Tumkur (sensitivity) | yield_index | mean soil percentile Nov-Feb | 69 | 0.43 | [+0.15, +0.64] |
| + Tumkur (sensitivity) | yield_index | rain Jun-Nov | 69 | 0.37 | [+0.12, +0.57] |
| + Tumkur (sensitivity) | yield_index | rain Nov-Feb | 69 | 0.02 | [-0.29, +0.33] |
| + Tumkur (sensitivity) | yield_index | SPEI-30 Oct-Nov | 69 | 0.37 | [+0.07, +0.60] |
| + Tumkur (sensitivity) | yield_index | SPEI-30 Nov-Feb | 69 | 0.32 | [+0.03, +0.54] |
| + Tumkur (sensitivity) | sown_area_anom | deficit duration Nov-Feb | 69 | -0.18 | [-0.46, +0.11] |
| + Tumkur (sensitivity) | sown_area_anom | severe deficit duration | 69 | -0.11 | [-0.41, +0.18] |
| + Tumkur (sensitivity) | sown_area_anom | soil moisture at sowing | 69 | 0.17 | [-0.12, +0.46] |
| + Tumkur (sensitivity) | sown_area_anom | mean soil percentile Nov-Feb | 69 | 0.2 | [-0.07, +0.47] |
| + Tumkur (sensitivity) | sown_area_anom | rain Jun-Nov | 69 | 0.06 | [-0.23, +0.35] |
| + Tumkur (sensitivity) | sown_area_anom | rain Nov-Feb | 69 | 0.21 | [-0.05, +0.44] |
| + Tumkur (sensitivity) | sown_area_anom | SPEI-30 Oct-Nov | 69 | 0.26 | [-0.05, +0.53] |
| + Tumkur (sensitivity) | sown_area_anom | SPEI-30 Nov-Feb | 69 | 0.17 | [-0.13, +0.44] |

## 2. Early warning of rabi yield-loss seasons (yield index <= -15%, fixed before analysis)

Indicators use inputs up to 8 days before the issue date. Single indicators: AUC of the raw value (no fitting). Logistic models: leave-one-season-out. Rows are district-seasons; districts share seasons.

| issue | method | n | loss_seasons | auc | ci | warned | caught |
|---|---|---|---|---|---|---|---|
| 15 Dec | Soil deficit so far (DD) | 46 | 11 | 0.8 | [0.62, 0.95] |  |  |
| 15 Dec | Soil moisture at sowing (low = risk) | 46 | 11 | 0.77 | [0.58, 0.93] |  |  |
| 15 Dec | Soil percentile so far (low = risk) | 46 | 11 | 0.76 | [0.54, 0.93] |  |  |
| 15 Dec | Rain since June (low = risk) | 46 | 11 | 0.72 | [0.51, 0.89] |  |  |
| 15 Dec | SPEI so far (low = risk) | 46 | 11 | 0.6 | [0.36, 0.80] |  |  |
| 15 Dec | LOSO logistic: soil (DD so far + SOW) | 46 | 11 | 0.77 | [0.55, 0.94] | 15.0 | 6.0 |
| 15 Dec | LOSO logistic: rain + SPEI | 46 | 11 | 0.64 | [0.44, 0.84] | 23.0 | 8.0 |
| 15 Jan | Soil deficit so far (DD) | 46 | 11 | 0.79 | [0.63, 0.95] |  |  |
| 15 Jan | Soil moisture at sowing (low = risk) | 46 | 11 | 0.77 | [0.58, 0.93] |  |  |
| 15 Jan | Soil percentile so far (low = risk) | 46 | 11 | 0.74 | [0.53, 0.93] |  |  |
| 15 Jan | Rain since June (low = risk) | 46 | 11 | 0.71 | [0.51, 0.88] |  |  |
| 15 Jan | SPEI so far (low = risk) | 46 | 11 | 0.64 | [0.41, 0.86] |  |  |
| 15 Jan | LOSO logistic: soil (DD so far + SOW) | 46 | 11 | 0.76 | [0.55, 0.93] | 15.0 | 6.0 |
| 15 Jan | LOSO logistic: rain + SPEI | 46 | 11 | 0.65 | [0.45, 0.84] | 24.0 | 8.0 |
| 15 Feb | Soil deficit so far (DD) | 46 | 11 | 0.79 | [0.62, 0.95] |  |  |
| 15 Feb | Soil moisture at sowing (low = risk) | 46 | 11 | 0.77 | [0.58, 0.93] |  |  |
| 15 Feb | Soil percentile so far (low = risk) | 46 | 11 | 0.73 | [0.51, 0.92] |  |  |
| 15 Feb | Rain since June (low = risk) | 46 | 11 | 0.71 | [0.52, 0.88] |  |  |
| 15 Feb | SPEI so far (low = risk) | 46 | 11 | 0.65 | [0.44, 0.85] |  |  |
| 15 Feb | LOSO logistic: soil (DD so far + SOW) | 46 | 11 | 0.76 | [0.55, 0.93] | 15.0 | 6.0 |
| 15 Feb | LOSO logistic: rain + SPEI | 46 | 11 | 0.64 | [0.44, 0.83] | 23.0 | 8.0 |

## 3. Figures

- fig_deficit_seasons.png - daily district deficit area; 3 worst yield seasons highlighted
- fig_dd_vs_outcomes.png - deficit duration vs yield index and sown-area anomaly
