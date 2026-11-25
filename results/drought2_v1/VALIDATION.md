# Rabi drought v2 - indicator vs independent crop outcomes (retrospective)

District-season rows (Kurnool and Anantapur on pre-2022 boundaries; APY rabi statistics). Within-district rank correlation (Spearman) pooled over both districts; 95 % interval by resampling whole seasons. Outcomes are impacts with other causes (prices, pests, irrigation, reporting), not drought labels. Development 2000-10 was inspected while building the indicators; evaluation 2011-22 was not used for any choice, but the soil product and yield series were downloaded together.

## Pooled (Kurnool + Anantapur)

| period | outcome | indicator | expected_sign | n | seasons | rho | ci_lo | ci_hi | sign_as_expected |
|---|---|---|---|---|---|---|---|---|---|
| development 2000-10 | yield_index | DD | - | 22 | 11 | -0.595 |  |  | True |
| development 2000-10 | yield_index | DDS | - | 22 | 11 | -0.595 |  |  | True |
| development 2000-10 | yield_index | RUN | - | 22 | 11 | -0.558 |  |  | True |
| development 2000-10 | yield_index | PCT | + | 22 | 11 | 0.355 |  |  | True |
| development 2000-10 | yield_index | SOW | + | 22 | 11 | 0.432 |  |  | True |
| development 2000-10 | yield_index | rain_jun_nov_ratio | + | 22 | 11 | 0.382 |  |  | True |
| development 2000-10 | yield_index | rain_nov_feb_ratio | + | 22 | 11 | 0.045 |  |  | True |
| development 2000-10 | sown_area_anom | DD | - | 22 | 11 | -0.079 |  |  | True |
| development 2000-10 | sown_area_anom | DDS | - | 22 | 11 | -0.079 |  |  | True |
| development 2000-10 | sown_area_anom | RUN | - | 22 | 11 | -0.17 |  |  | True |
| development 2000-10 | sown_area_anom | PCT | + | 22 | 11 | 0.086 |  |  | True |
| development 2000-10 | sown_area_anom | SOW | + | 22 | 11 | 0.068 |  |  | True |
| development 2000-10 | sown_area_anom | rain_jun_nov_ratio | + | 22 | 11 | 0.068 |  |  | True |
| development 2000-10 | sown_area_anom | rain_nov_feb_ratio | + | 22 | 11 | 0.5 |  |  | True |
| evaluation 2011-22 | yield_index | DD | - | 24 | 12 | -0.62 | -0.887 | -0.191 | True |
| evaluation 2011-22 | yield_index | DDS | - | 24 | 12 | -0.56 | -0.815 | -0.077 | True |
| evaluation 2011-22 | yield_index | RUN | - | 24 | 12 | -0.591 | -0.808 | -0.126 | True |
| evaluation 2011-22 | yield_index | PCT | + | 24 | 12 | 0.573 | 0.049 | 0.872 | True |
| evaluation 2011-22 | yield_index | SOW | + | 24 | 12 | 0.731 | 0.284 | 0.933 | True |
| evaluation 2011-22 | yield_index | rain_jun_nov_ratio | + | 24 | 12 | 0.594 | 0.049 | 0.842 | True |
| evaluation 2011-22 | yield_index | rain_nov_feb_ratio | + | 24 | 12 | 0.063 | -0.5 | 0.619 | True |
| evaluation 2011-22 | sown_area_anom | DD | - | 24 | 12 | -0.593 | -0.801 | -0.199 | True |
| evaluation 2011-22 | sown_area_anom | DDS | - | 24 | 12 | -0.564 | -0.793 | -0.178 | True |
| evaluation 2011-22 | sown_area_anom | RUN | - | 24 | 12 | -0.288 | -0.555 | 0.07 | True |
| evaluation 2011-22 | sown_area_anom | PCT | + | 24 | 12 | 0.619 | 0.169 | 0.869 | True |
| evaluation 2011-22 | sown_area_anom | SOW | + | 24 | 12 | 0.57 | 0.065 | 0.883 | True |
| evaluation 2011-22 | sown_area_anom | rain_jun_nov_ratio | + | 24 | 12 | 0.507 | 0.061 | 0.81 | True |
| evaluation 2011-22 | sown_area_anom | rain_nov_feb_ratio | + | 24 | 12 | 0.024 | -0.496 | 0.471 | True |
| all 2000-22 | yield_index | DD | - | 46 | 23 | -0.577 | -0.737 | -0.346 | True |
| all 2000-22 | yield_index | DDS | - | 46 | 23 | -0.516 | -0.678 | -0.212 | True |
| all 2000-22 | yield_index | RUN | - | 46 | 23 | -0.443 | -0.662 | -0.199 | True |
| all 2000-22 | yield_index | PCT | + | 46 | 23 | 0.431 | 0.092 | 0.669 | True |
| all 2000-22 | yield_index | SOW | + | 46 | 23 | 0.547 | 0.271 | 0.728 | True |
| all 2000-22 | yield_index | rain_jun_nov_ratio | + | 46 | 23 | 0.398 | 0.072 | 0.626 | True |
| all 2000-22 | yield_index | rain_nov_feb_ratio | + | 46 | 23 | 0.006 | -0.34 | 0.369 | True |
| all 2000-22 | sown_area_anom | DD | - | 46 | 23 | -0.256 | -0.539 | 0.064 | True |
| all 2000-22 | sown_area_anom | DDS | - | 46 | 23 | -0.157 | -0.469 | 0.161 | True |
| all 2000-22 | sown_area_anom | RUN | - | 46 | 23 | -0.083 | -0.337 | 0.215 | True |
| all 2000-22 | sown_area_anom | PCT | + | 46 | 23 | 0.233 | -0.075 | 0.526 | True |
| all 2000-22 | sown_area_anom | SOW | + | 46 | 23 | 0.211 | -0.141 | 0.544 | True |
| all 2000-22 | sown_area_anom | rain_jun_nov_ratio | + | 46 | 23 | 0.133 | -0.228 | 0.461 | True |
| all 2000-22 | sown_area_anom | rain_nov_feb_ratio | + | 46 | 23 | 0.231 | -0.054 | 0.476 | True |

## By district (all 2000-22 seasons)

| outcome | indicator | Anantapur | Kurnool | Tumkur |
|---|---|---|---|---|
| sown_area_anom | DD | -0.456 | 0.046 | 0.02 |
| sown_area_anom | DDS | -0.357 | 0.043 | 0.121 |
| sown_area_anom | PCT | 0.505 | -0.039 | 0.14 |
| sown_area_anom | RUN | -0.184 | 0.062 | 0.125 |
| sown_area_anom | SOW | 0.435 | -0.013 | 0.099 |
| sown_area_anom | rain_jun_nov_ratio | 0.357 | -0.091 | -0.077 |
| sown_area_anom | rain_nov_feb_ratio | 0.24 | 0.222 | 0.173 |
| yield_index | DD | -0.786 | -0.337 | -0.481 |
| yield_index | DDS | -0.703 | -0.329 | -0.423 |
| yield_index | PCT | 0.621 | 0.241 | 0.44 |
| yield_index | RUN | -0.629 | -0.387 | -0.353 |
| yield_index | SOW | 0.705 | 0.389 | 0.52 |
| yield_index | rain_jun_nov_ratio | 0.582 | 0.214 | 0.326 |
| yield_index | rain_nov_feb_ratio | 0.249 | -0.236 | 0.043 |

## By crop (DD vs each crop's yield and area anomaly, 2000-22)

| district | crop | weight | n | rho_DD_yield | rho_DD_area |
|---|---|---|---|---|---|
| Anantapur | Gram | 0.401 | 23 | -0.756 | -0.088 |
| Anantapur | Groundnut | 0.149 | 23 | -0.084 | -0.613 |
| Anantapur | Jowar | 0.124 | 23 | -0.471 | -0.192 |
| Anantapur | Rice | 0.142 | 23 | -0.252 | -0.697 |
| Anantapur | Sunflower | 0.184 | 12 | 0.039 | -0.382 |
| Kurnool | Gram | 0.39 | 23 | -0.315 | 0.153 |
| Kurnool | Groundnut | 0.077 | 23 | -0.273 | -0.559 |
| Kurnool | Jowar | 0.239 | 23 | -0.201 | 0.308 |
| Kurnool | Rice | 0.054 | 23 | -0.272 | -0.523 |
| Kurnool | Sunflower | 0.24 | 12 | -0.37 | -0.379 |

## Seasons in the top third of deficit duration vs the rest (primary districts)

| dd_high | yield_index | sown_area_anom |
|---|---|---|
| False | 0.255 | 0.054 |
| True | -0.103 | -0.053 |
