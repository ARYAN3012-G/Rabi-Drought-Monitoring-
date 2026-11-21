# Candidate audit, part 1: what script C1 selected

Run 2026-11-21. Segments with selection reasons: 5139; duplicate field_id: 0.

## Area (hectares, from C1_stats)

| site_code | farmland_ha | candidate_ha | candidate_rainfed_ha | candidate_irrigated_ha | candidate_% | rainfed_%_of_cand |
|---|---|---|---|---|---|---|
| Som | 883.3 | 280.1 | 92.5 | 187.5 | 31.7 | 33.0 |
| Lep | 1628.0 | 672.6 | 149.1 | 523.5 | 41.3 | 22.2 |
| Cho | 1736.8 | 702.9 | 213.3 | 489.6 | 40.5 | 30.3 |
| Sira | 1612.9 | 431.0 | 133.5 | 297.5 | 26.7 | 31.0 |
| Ped | 1829.0 | 913.3 | 475.1 | 438.2 | 49.9 | 52.0 |
| Din | 302.6 | 91.9 | 24.9 | 67.0 | 30.4 | 27.1 |
| Bal | 247.7 | 85.1 | 37.6 | 47.5 | 34.4 | 44.2 |
| Pul | 1060.4 | 792.5 | 235.4 | 557.1 | 74.7 | 29.7 |

## Segments and sampled fields

| site_code | irrigated_segments | rainfed_segments | irrigated_sampled | rainfed_sampled |
|---|---|---|---|---|
| Som | 260 | 62 | 20 | 20 |
| Lep | 755 | 88 | 20 | 20 |
| Cho | 705 | 170 | 20 | 20 |
| Sira | 401 | 63 | 20 | 20 |
| Ped | 616 | 657 | 20 | 20 |
| Din | 91 | 21 | 20 | 20 |
| Bal | 67 | 43 | 20 | 20 |
| Pul | 832 | 308 | 20 | 20 |

## Sampled fields: selection reasons

active_<y>_% = share of sampled fields winter-active in season y (Oct y - Apr y+1).

| site_code | class | fields | area_ha_med | active_2019_% | active_2020_% | active_2021_% | active_2022_% | jm_ndvi_2022_med | min_obs_JanMar |
|---|---|---|---|---|---|---|---|---|---|
| Som | irrigated | 20 | 0.7 | 70 | 90 | 85 | 75 | 0.47 | 16.0 |
| Som | rainfed | 20 | 0.5 | 25 | 95 | 90 | 95 | 0.4 | 16.0 |
| Lep | irrigated | 20 | 0.6 | 60 | 90 | 100 | 90 | 0.48 | 16.0 |
| Lep | rainfed | 20 | 0.61 | 50 | 85 | 65 | 85 | 0.43 | 15.04 |
| Cho | irrigated | 20 | 0.68 | 60 | 90 | 95 | 85 | 0.46 | 15.1 |
| Cho | rainfed | 20 | 0.57 | 45 | 80 | 75 | 90 | 0.45 | 15.96 |
| Sira | irrigated | 20 | 0.58 | 40 | 70 | 100 | 100 | 0.51 | 12.39 |
| Sira | rainfed | 20 | 0.48 | 40 | 65 | 90 | 85 | 0.42 | 13.5 |
| Ped | irrigated | 20 | 0.64 | 60 | 75 | 85 | 95 | 0.65 | 13.0 |
| Ped | rainfed | 20 | 0.64 | 55 | 70 | 65 | 95 | 0.49 | 14.0 |
| Din | irrigated | 20 | 0.6 | 100 | 95 | 85 | 90 | 0.6 | 13.77 |
| Din | rainfed | 20 | 0.6 | 70 | 70 | 50 | 80 | 0.46 | 13.4 |
| Bal | irrigated | 20 | 0.65 | 100 | 80 | 85 | 85 | 0.56 | 14.0 |
| Bal | rainfed | 20 | 0.64 | 70 | 90 | 35 | 65 | 0.39 | 13.0 |
| Pul | irrigated | 20 | 0.7 | 70 | 95 | 95 | 100 | 0.56 | 13.96 |
| Pul | rainfed | 20 | 0.64 | 55 | 90 | 65 | 75 | 0.5 | 13.77 |

Number of active seasons (of 4):

| site_code | class | 2 | 3 | 4 |
|---|---|---|---|---|
| Som | irrigated | 3 | 13 | 4 |
| Som | rainfed | 2 | 17 | 1 |
| Lep | irrigated | 2 | 14 | 4 |
| Lep | rainfed | 7 | 13 | 0 |
| Cho | irrigated | 2 | 15 | 3 |
| Cho | rainfed | 3 | 17 | 0 |
| Sira | irrigated | 3 | 17 | 0 |
| Sira | rainfed | 6 | 14 | 0 |
| Ped | irrigated | 2 | 12 | 6 |
| Ped | rainfed | 7 | 11 | 2 |
| Din | irrigated | 1 | 6 | 13 |
| Din | rainfed | 9 | 8 | 3 |
| Bal | irrigated | 0 | 12 | 8 |
| Bal | rainfed | 11 | 9 | 0 |
| Pul | irrigated | 0 | 15 | 5 |
| Pul | rainfed | 7 | 9 | 4 |
