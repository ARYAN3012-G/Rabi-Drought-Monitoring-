# Rabi drought v2 - indicator vs independent crop outcomes (retrospective)

District-season rows (Kurnool and Anantapur on pre-2022 boundaries; APY rabi statistics). Within-district rank correlation (Spearman) pooled over both districts; 95 % interval by resampling whole seasons. Outcomes are impacts with other causes (prices, pests, irrigation, reporting), not drought labels. Development 2000-10 was inspected while building the indicators; evaluation 2011-22 was not used for any choice, but the soil product and yield series were downloaded together.

## Pooled (Kurnool + Anantapur)

| period | outcome | indicator | expected_sign | n | seasons | rho | ci_lo | ci_hi | sign_as_expected |
|---|---|---|---|---|---|---|---|---|---|
| development 2000-10 | yield_index | DD | - | 22 | 11 | -0.3 |  |  | True |
| development 2000-10 | yield_index | DDS | - | 22 | 11 | -0.263 |  |  | True |
| development 2000-10 | yield_index | RUN | - | 22 | 11 | -0.3 |  |  | True |
| development 2000-10 | yield_index | PCT | + | 22 | 11 | 0.332 |  |  | True |
| development 2000-10 | yield_index | SOW | + | 22 | 11 | 0.4 |  |  | True |
| development 2000-10 | yield_index | rain_jun_nov_ratio | + | 22 | 11 | 0.382 |  |  | True |
| development 2000-10 | yield_index | rain_nov_feb_ratio | + | 22 | 11 | 0.045 |  |  | True |
| development 2000-10 | sown_area_anom | DD | - | 22 | 11 | 0.027 |  |  | False |
| development 2000-10 | sown_area_anom | DDS | - | 22 | 11 | -0.054 |  |  | True |
| development 2000-10 | sown_area_anom | RUN | - | 22 | 11 | 0.027 |  |  | False |
| development 2000-10 | sown_area_anom | PCT | + | 22 | 11 | 0.032 |  |  | True |
| development 2000-10 | sown_area_anom | SOW | + | 22 | 11 | 0.045 |  |  | True |
| development 2000-10 | sown_area_anom | rain_jun_nov_ratio | + | 22 | 11 | 0.068 |  |  | True |
| development 2000-10 | sown_area_anom | rain_nov_feb_ratio | + | 22 | 11 | 0.5 |  |  | True |
| evaluation 2011-22 | yield_index | DD | - | 24 | 12 | -0.498 | -0.846 | -0.157 | True |
| evaluation 2011-22 | yield_index | DDS | - | 24 | 12 | -0.393 | -0.529 | -0.125 | True |
| evaluation 2011-22 | yield_index | RUN | - | 24 | 12 | -0.498 | -0.846 | -0.157 | True |
| evaluation 2011-22 | yield_index | PCT | + | 24 | 12 | 0.689 | 0.253 | 0.885 | True |
| evaluation 2011-22 | yield_index | SOW | + | 24 | 12 | 0.762 | 0.344 | 0.934 | True |
| evaluation 2011-22 | yield_index | rain_jun_nov_ratio | + | 24 | 12 | 0.594 | 0.049 | 0.842 | True |
| evaluation 2011-22 | yield_index | rain_nov_feb_ratio | + | 24 | 12 | 0.063 | -0.5 | 0.619 | True |
| evaluation 2011-22 | sown_area_anom | DD | - | 24 | 12 | -0.243 | -0.607 | 0.117 | True |
| evaluation 2011-22 | sown_area_anom | DDS | - | 24 | 12 | -0.393 | -0.587 | -0.052 | True |
| evaluation 2011-22 | sown_area_anom | RUN | - | 24 | 12 | -0.243 | -0.607 | 0.117 | True |
| evaluation 2011-22 | sown_area_anom | PCT | + | 24 | 12 | 0.476 | 0.019 | 0.782 | True |
| evaluation 2011-22 | sown_area_anom | SOW | + | 24 | 12 | 0.479 | -0.063 | 0.856 | True |
| evaluation 2011-22 | sown_area_anom | rain_jun_nov_ratio | + | 24 | 12 | 0.507 | 0.061 | 0.81 | True |
| evaluation 2011-22 | sown_area_anom | rain_nov_feb_ratio | + | 24 | 12 | 0.024 | -0.496 | 0.471 | True |
| all 2000-22 | yield_index | DD | - | 46 | 23 | -0.457 | -0.668 | -0.09 | True |
| all 2000-22 | yield_index | DDS | - | 46 | 23 | -0.275 | -0.441 | 0.019 | True |
| all 2000-22 | yield_index | RUN | - | 46 | 23 | -0.457 | -0.668 | -0.09 | True |
| all 2000-22 | yield_index | PCT | + | 46 | 23 | 0.469 | 0.126 | 0.691 | True |
| all 2000-22 | yield_index | SOW | + | 46 | 23 | 0.529 | 0.246 | 0.704 | True |
| all 2000-22 | yield_index | rain_jun_nov_ratio | + | 46 | 23 | 0.398 | 0.072 | 0.626 | True |
| all 2000-22 | yield_index | rain_nov_feb_ratio | + | 46 | 23 | 0.006 | -0.34 | 0.369 | True |
| all 2000-22 | sown_area_anom | DD | - | 46 | 23 | -0.049 | -0.35 | 0.274 | True |
| all 2000-22 | sown_area_anom | DDS | - | 46 | 23 | -0.034 | -0.278 | 0.214 | True |
| all 2000-22 | sown_area_anom | RUN | - | 46 | 23 | -0.049 | -0.35 | 0.274 | True |
| all 2000-22 | sown_area_anom | PCT | + | 46 | 23 | 0.164 | -0.165 | 0.47 | True |
| all 2000-22 | sown_area_anom | SOW | + | 46 | 23 | 0.158 | -0.206 | 0.496 | True |
| all 2000-22 | sown_area_anom | rain_jun_nov_ratio | + | 46 | 23 | 0.133 | -0.228 | 0.461 | True |
| all 2000-22 | sown_area_anom | rain_nov_feb_ratio | + | 46 | 23 | 0.231 | -0.054 | 0.476 | True |

## By district (all 2000-22 seasons)

| outcome | indicator | Anantapur | Kurnool | Tumkur |
|---|---|---|---|---|
| sown_area_anom | DD | -0.175 | 0.077 | -0.109 |
| sown_area_anom | DDS | -0.09 | 0.022 | 0.002 |
| sown_area_anom | PCT | 0.412 | -0.085 | 0.091 |
| sown_area_anom | RUN | -0.175 | 0.077 | -0.109 |
| sown_area_anom | SOW | 0.383 | -0.067 | 0.052 |
| sown_area_anom | rain_jun_nov_ratio | 0.357 | -0.091 | -0.077 |
| sown_area_anom | rain_nov_feb_ratio | 0.24 | 0.222 | 0.173 |
| yield_index | DD | -0.539 | -0.376 | -0.257 |
| yield_index | DDS | -0.359 | -0.19 | -0.361 |
| yield_index | PCT | 0.608 | 0.331 | 0.384 |
| yield_index | RUN | -0.539 | -0.376 | -0.257 |
| yield_index | SOW | 0.696 | 0.362 | 0.498 |
| yield_index | rain_jun_nov_ratio | 0.582 | 0.214 | 0.326 |
| yield_index | rain_nov_feb_ratio | 0.249 | -0.236 | 0.043 |

## By crop (DD vs each crop's yield and area anomaly, 2000-22)

| district | crop | weight | n | rho_DD_yield | rho_DD_area |
|---|---|---|---|---|---|
| Anantapur | Gram | 0.401 | 23 | -0.561 | -0.021 |
| Anantapur | Groundnut | 0.149 | 23 | -0.224 | -0.322 |
| Anantapur | Jowar | 0.124 | 23 | -0.532 | 0.117 |
| Anantapur | Rice | 0.142 | 23 | 0.181 | -0.296 |
| Anantapur | Sunflower | 0.184 | 12 | 0.229 | -0.156 |
| Kurnool | Gram | 0.39 | 23 | -0.326 | 0.325 |
| Kurnool | Groundnut | 0.077 | 23 | -0.372 | -0.437 |
| Kurnool | Jowar | 0.239 | 23 | -0.134 | 0.485 |
| Kurnool | Rice | 0.054 | 23 | -0.472 | -0.547 |
| Kurnool | Sunflower | 0.24 | 12 | -0.521 | -0.043 |

## Seasons in the top third of deficit duration vs the rest (primary districts)

| dd_high | yield_index | sown_area_anom |
|---|---|---|
| True | 0.13 | 0.017 |
