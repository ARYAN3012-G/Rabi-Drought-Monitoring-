# Rabi drought v2 - status for 2017-01-15

Inputs up to 2017-01-07 (8-day publication lag). Regional ERA5-Land root-zone soil moisture, 45 grid points in Kurnool / Anantapur / Tumkur. **Monitoring status and the 15-day forecast are separate. Soil-moisture deficit is not verified crop drought; scores are not calibrated probabilities. Field validation is pending.**

| district | issue_date | input_cutoff | latest_soil_date | grid_points | scale | deficit_area_now | deficit_area_15d | median_percentile_now | deficit_duration_season_so_far | monitoring_status | forecast_model | risk_score | threshold | forecast_window | forecast_status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Kurnool | 2017-01-15 | 2017-01-07 | 2017-01-07 | 2 | regional (0.3 deg grid, no cropland mask) | 0.0 | 0.0 | 0.491 | 0.0 | no widespread soil-moisture deficit (regional; not a crop-health statement) | Logistic regression (soil) | 0.019 | 0.618 | 2017-01-16 .. 2017-01-30 | no warning (score below threshold; not 'healthy') |
| Anantapur | 2017-01-15 | 2017-01-07 | 2017-01-07 | 2 | regional (0.3 deg grid, no cropland mask) | 0.0 | 0.0 | 0.245 | 0.64 | no widespread soil-moisture deficit (regional; not a crop-health statement) | Logistic regression (soil) | 0.785 | 0.618 | 2017-01-16 .. 2017-01-30 | WARNING: district-wide soil deficit likely in next 15 days |
| Tumkur | 2017-01-15 | 2017-01-07 | 2017-01-07 | 1 | regional (0.3 deg grid, no cropland mask) | 1.0 | 0.667 | 0.165 | 0.838 | soil-moisture deficit (regional) | Logistic regression (soil) | 0.984 | 0.618 | 2017-01-16 .. 2017-01-30 | WARNING: district-wide soil deficit likely in next 15 days |
