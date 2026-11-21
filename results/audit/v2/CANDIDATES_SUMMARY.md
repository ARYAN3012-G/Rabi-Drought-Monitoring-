# Candidate audit, part 1: what script C1 selected

Run 2026-11-21. Segments with selection reasons: 2202; duplicate field_id: 0.

## Area (hectares, from C1_stats)

| site_code | farmland_ha | candidate_ha | candidate_rainfed_ha | candidate_irrigated_ha | candidate_% | rainfed_%_of_cand |
|---|---|---|---|---|---|---|
| Som | 883.3 | 103.6 | 5.2 | 98.4 | 11.7 | 5.0 |
| Lep | 1628.0 | 203.6 | 5.2 | 198.3 | 12.5 | 2.6 |
| Cho | 1736.8 | 124.7 | 4.0 | 120.6 | 7.2 | 3.2 |
| Sira | 1612.9 | 61.5 | 6.6 | 54.9 | 3.8 | 10.8 |
| Ped | 1829.0 | 584.9 | 277.6 | 307.3 | 32.0 | 47.5 |
| Din | 302.6 | 48.9 | 6.6 | 42.3 | 16.2 | 13.5 |
| Bal | 247.7 | 42.2 | 11.7 | 30.5 | 17.0 | 27.8 |
| Pul | 1060.4 | 547.8 | 163.9 | 383.9 | 51.7 | 29.9 |

## Segments and sampled fields

| site_code | irrigated_segments | rainfed_segments | irrigated_sampled | rainfed_sampled |
|---|---|---|---|---|
| Som | 129 | 3 | 20 | 3 |
| Lep | 236 | 3 | 20 | 3 |
| Cho | 127 | 0 | 20 | 0 |
| Sira | 47 | 4 | 20 | 4 |
| Ped | 417 | 373 | 20 | 20 |
| Din | 56 | 6 | 20 | 6 |
| Bal | 44 | 17 | 20 | 17 |
| Pul | 539 | 201 | 20 | 20 |

## Sampled fields: selection reasons

active_<y>_% = share of sampled fields winter-active in season y (Oct y - Apr y+1).

| site_code | class | fields | area_ha_med | active_2019_% | active_2020_% | active_2021_% | active_2022_% | jm_ndvi_2022_med | min_obs_JanMar |
|---|---|---|---|---|---|---|---|---|---|
| Som | irrigated | 20 | 0.65 | 60 | 85 | 60 | 65 | 0.51 | 16.0 |
| Som | rainfed | 3 | 0.45 | 67 | 0 | 33 | 100 | 0.56 | 16.0 |
| Lep | irrigated | 20 | 0.57 | 60 | 85 | 50 | 90 | 0.58 | 15.0 |
| Lep | rainfed | 3 | 0.52 | 0 | 67 | 67 | 100 | 0.62 | 15.0 |
| Cho | irrigated | 20 | 0.5 | 65 | 75 | 80 | 85 | 0.57 | 15.21 |
| Sira | irrigated | 20 | 0.48 | 35 | 60 | 80 | 70 | 0.52 | 15.33 |
| Sira | rainfed | 4 | 0.4 | 0 | 0 | 100 | 100 | 0.55 | 14.62 |
| Ped | irrigated | 20 | 0.61 | 70 | 80 | 55 | 90 | 0.6 | 13.61 |
| Ped | rainfed | 20 | 0.62 | 30 | 75 | 70 | 95 | 0.64 | 14.0 |
| Din | irrigated | 20 | 0.61 | 85 | 90 | 65 | 85 | 0.65 | 13.0 |
| Din | rainfed | 6 | 0.88 | 83 | 83 | 83 | 67 | 0.55 | 13.37 |
| Bal | irrigated | 20 | 0.64 | 85 | 75 | 80 | 85 | 0.62 | 14.0 |
| Bal | rainfed | 17 | 0.45 | 65 | 76 | 41 | 76 | 0.47 | 13.0 |
| Pul | irrigated | 20 | 0.63 | 80 | 75 | 90 | 95 | 0.66 | 14.03 |
| Pul | rainfed | 20 | 0.6 | 85 | 90 | 65 | 65 | 0.51 | 14.0 |

Number of active seasons (of 4):

| site_code | class | 2 | 3 | 4 |
|---|---|---|---|---|
| Som | irrigated | 9 | 10 | 1 |
| Som | rainfed | 2 | 1 | 0 |
| Lep | irrigated | 11 | 8 | 1 |
| Lep | rainfed | 2 | 1 | 0 |
| Cho | irrigated | 9 | 10 | 1 |
| Sira | irrigated | 14 | 5 | 1 |
| Sira | rainfed | 4 | 0 | 0 |
| Ped | irrigated | 5 | 12 | 3 |
| Ped | rainfed | 11 | 7 | 2 |
| Din | irrigated | 4 | 9 | 7 |
| Din | rainfed | 3 | 0 | 3 |
| Bal | irrigated | 4 | 11 | 5 |
| Bal | rainfed | 9 | 7 | 1 |
| Pul | irrigated | 1 | 15 | 4 |
| Pul | rainfed | 7 | 5 | 8 |
