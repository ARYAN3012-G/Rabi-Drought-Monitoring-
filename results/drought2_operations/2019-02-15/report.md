# Rabi drought v2 - status for 2019-02-15

Inputs up to 2019-02-07 (8-day publication lag). Regional ERA5-Land root-zone soil moisture, 45 grid points in Kurnool / Anantapur / Tumkur. **Monitoring status and the 15-day forecast are separate. Soil-moisture deficit is not verified crop drought; scores are not calibrated probabilities. Field validation is pending.**

| district | issue_date | input_cutoff | latest_soil_date | grid_points | scale | deficit_area_now | deficit_area_15d | median_percentile_now | deficit_duration_season_so_far | monitoring_status | forecast_status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Kurnool | 2019-02-15 | 2019-02-07 | 2019-02-07 | 17 | regional (0.3 deg grid, no cropland mask) | 0.059 | 0.196 | 0.35 | 0.582 | no widespread soil-moisture deficit (regional; not a crop-health statement) | unavailable (needs ['rain30', 'rain60', 'rain_since_oct', 'rain_jun_nov_ratio', 'et0_30']; weather inputs not wired for live use) |
| Anantapur | 2019-02-15 | 2019-02-07 | 2019-02-07 | 18 | regional (0.3 deg grid, no cropland mask) | 0.556 | 0.552 | 0.187 | 0.702 | soil-moisture deficit (regional) | unavailable (needs ['rain30', 'rain60', 'rain_since_oct', 'rain_jun_nov_ratio', 'et0_30']; weather inputs not wired for live use) |
| Tumkur | 2019-02-15 | 2019-02-07 | 2019-02-07 | 10 | regional (0.3 deg grid, no cropland mask) | 0.0 | 0.053 | 0.366 | 0.159 | no widespread soil-moisture deficit (regional; not a crop-health statement) | unavailable (needs ['rain30', 'rain60', 'rain_since_oct', 'rain_jun_nov_ratio', 'et0_30']; weather inputs not wired for live use) |
