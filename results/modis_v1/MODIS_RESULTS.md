# MODIS long-record test v1: results

Rules: `docs/MODIS_TEST_v1.md` (registered before export). Evaluation seasons 2010-11..2022-23, Kurnool + Anantapur; 95 % season-block bootstrap.

## T1 association with district rabi outcomes

| period | indicator | outcome | n | rho | lo | hi | expected_sign |
|---|---|---|---|---|---|---|---|
| evaluation 2010-22 | DD | yield_index | 26 | -0.58 | -0.84 | -0.18 | -1 |
| evaluation 2010-22 | DD | sown_area_anom | 26 | -0.61 | -0.80 | -0.25 | -1 |
| evaluation 2010-22 | VD | yield_index | 26 | -0.39 | -0.52 | -0.12 | -1 |
| evaluation 2010-22 | VD | sown_area_anom | 26 | -0.39 | -0.57 | -0.07 | -1 |
| evaluation 2010-22 | CD | yield_index | 26 | -0.39 | -0.52 | -0.12 | -1 |
| evaluation 2010-22 | CD | sown_area_anom | 26 | -0.39 | -0.57 | -0.07 | -1 |
| evaluation 2010-22 | VPCT | yield_index | 26 | 0.70 | 0.25 | 0.92 | 1 |
| evaluation 2010-22 | VPCT | sown_area_anom | 26 | 0.38 | -0.14 | 0.77 | 1 |
| evaluation 2010-22 | rain_jun_nov_ratio | yield_index | 26 | 0.54 | 0.07 | 0.79 | 1 |
| evaluation 2010-22 | rain_jun_nov_ratio | sown_area_anom | 26 | 0.53 | 0.12 | 0.81 | 1 |
| evaluation 2010-22 | spei_so_far | yield_index | 26 | 0.38 | -0.21 | 0.78 | 1 |
| evaluation 2010-22 | spei_so_far | sown_area_anom | 26 | 0.31 | -0.16 | 0.68 | 1 |
| inside NDVI reference 2000-09 | DD | yield_index | 20 | -0.73 | - | - | -1 |
| inside NDVI reference 2000-09 | DD | sown_area_anom | 20 | -0.13 | - | - | -1 |
| inside NDVI reference 2000-09 | VD | yield_index | 20 | -0.32 | - | - | -1 |
| inside NDVI reference 2000-09 | VD | sown_area_anom | 20 | -0.05 | - | - | -1 |
| inside NDVI reference 2000-09 | CD | yield_index | 20 | -0.32 | - | - | -1 |
| inside NDVI reference 2000-09 | CD | sown_area_anom | 20 | -0.05 | - | - | -1 |
| inside NDVI reference 2000-09 | VPCT | yield_index | 20 | 0.63 | - | - | 1 |
| inside NDVI reference 2000-09 | VPCT | sown_area_anom | 20 | 0.20 | - | - | 1 |
| inside NDVI reference 2000-09 | rain_jun_nov_ratio | yield_index | 20 | 0.57 | - | - | 1 |
| inside NDVI reference 2000-09 | rain_jun_nov_ratio | sown_area_anom | 20 | 0.12 | - | - | 1 |
| inside NDVI reference 2000-09 | spei_so_far | yield_index | 20 | 0.48 | - | - | 1 |
| inside NDVI reference 2000-09 | spei_so_far | sown_area_anom | 20 | 0.18 | - | - | 1 |

## T2/T3 loss-season detection (9 loss seasons of 26)

| indicator | n | losses | auc | lo | hi | rule | warned | caught | precision | recall |
|---|---|---|---|---|---|---|---|---|---|---|
| DD | 26 | 9 | 0.82 | 0.64 | 0.97 | DD >= 0.25 | 3.00 | 3.00 | 1.00 | 0.33 |
| VD | 26 | 9 | 0.61 | 0.50 | 0.75 | VD >= 0.25 | 1.00 | 1.00 | 1.00 | 0.11 |
| CD | 26 | 9 | 0.61 | 0.50 | 0.75 | CD >= 0.25 | 1.00 | 1.00 | 1.00 | 0.11 |
| VPCT | 26 | 9 | 0.83 | 0.57 | 1.00 | - | - | - | - | - |
| rain_jun_nov_ratio | 26 | 9 | 0.80 | 0.51 | 0.98 | - | - | - | - | - |
| VD_15jan | 26 | 9 | 0.61 | 0.50 | 0.75 | - | - | - | - | - |
| CD_15jan | 26 | 9 | 0.61 | 0.50 | 0.75 | - | - | - | - | - |
| VPCT_15jan | 26 | 9 | 0.81 | 0.53 | 1.00 | - | - | - | - | - |
| DD_so_far | 26 | 9 | 0.82 | 0.64 | 0.97 | - | - | - | - | - |
| spei_so_far | 26 | 9 | 0.65 | 0.38 | 0.89 | - | - | - | - | - |

## T4 low-greenness composites: share in yield-loss seasons by soil state

| soil | low_greenness_composites | in_loss_season | share_in_loss_season |
|---|---|---|---|
| soil below normal | 3 | 3 | 1.00 |

Difference (soil below normal - normal/wet): 95 % CI [nan, nan]

## Data coverage

| unit | composites | valid | with_pct |
|---|---|---|---|
| Anantapur | 395 | 391 | 391 |
| Bal | 395 | 388 | 388 |
| Cho | 395 | 387 | 387 |
| Din | 395 | 388 | 388 |
| Kurnool | 395 | 391 | 391 |
| Lep | 395 | 383 | 383 |
| Ped | 395 | 391 | 391 |
| Pul | 395 | 388 | 388 |
| Sira | 395 | 386 | 386 |
| Som | 395 | 382 | 382 |
| Tumkur | 395 | 388 | 388 |