# Rabi vegetation forecast, experiment v1: rules fixed before training

**Fixed:** 21 November 2026, before any model was trained or evaluated on these data. The git commit that adds this file dates it. Code: `src/forecast/build_dataset.py` and `src/forecast/train_eval.py`.

## Question
Can a model forecast the vegetation condition (NDVI) of rabi cropland **15 days ahead** better than simple baselines, using only past satellite and weather data?
- The target comes from future satellite observations. Government drought orders are **not** used.
- Detecting drought is a separate, later question.

## Data
- **Points:** 1,350 stratified random cropland points (`C3_points.csv`): 100 rainfed + 50 irrigated in each of 9 mandals.
  - Cropland = WorldCover 2020 and 2021 class 40.
  - Irrigated = Mar–May NDVI p75 > 0.4 in at least 2 of the summers 2019–2023.
  - Both rules use data from **before** the test seasons (from 1 Oct 2023), so they leak nothing into the test.
- **Satellite:** `C3_points_timeseries.csv`, Sentinel-2 SR with Cloud Score+ 0.60 and SCL masking. Each value is the mean NDVI in a 15 m buffer (about 16 pixels), every image from Oct to Apr, 2019-20 to 2025-26.
- **Weather:** AgERA5 daily data. Each mandal uses the weather cell nearest to the mean of its points, among the six independent cells of the weather module.
- **Previous inspection, disclosed:**
  - The mandal-level C3 summaries were looked at before these rules were fixed. They showed lower irrigated establishment at Adoni and Pedda Kadubur in 2023-24.
  - All seven seasons were known while the rabi project was designed. Results on them are **historical development evidence**, not a real-time test.

## Observation cleaning
- A point observation is kept if the count ≥ 12 (≥ 75 % of the buffer is clear) and NDVI is between −0.2 and 1.
- Each point has one observation per date: the one with the highest count, because the image strips overlap.

## Forecast instances
- **Season y:** 1 Oct y to 30 Apr y+1.
- **Issue dates t:** 15 Oct y, then every 5 days, as long as t + 18 ≤ 30 Apr y+1.
- **Availability:** inputs use satellite observations dated ≤ t − 2 days and weather dated ≤ t − 1 day.
- **Recent-input rule:** the latest usable observation must be at most **12 days old** at t.
  - Otherwise the instance is **excluded as "no recent observation"**.
  - It is counted and reported, and never treated as "no crop".
- **Target rule:** the observed NDVI nearest to t + 15 within **±3 days** (t + 12 to t + 18).
  - No interpolation.
  - If there is none, the instance is **excluded as "no target"**, and counted and reported.

## Inputs (past only)
- **Satellite:**
  - NDVI and age of the latest observation;
  - the latest observation dated ≤ t − 15 and ≤ t − 30, with ages;
  - the 15- and 30-day changes;
  - the season-so-far minimum and maximum;
  - the number of observations in the last 30 days.
- **Timing and location:** days since 1 Oct, irrigated flag, latitude, longitude.
- **Weather:**
  - rain over the last 30 and 90 days;
  - rain since 1 June as a ratio to its 1979–2011 mean for the same dates;
  - mean ET0 and mean Tmax over the last 15 days;
  - 60-day water balance (rain − ET0);
  - the weather module's SPEI (frozen 1979–2011 calibration) at t − 1.
- **Point climatology:** the point's mean NDVI within ±7 days of the target day-of-season and of the latest-observation day.
  - Computed **only from the allowed training seasons**, always excluding the row's own season.
  - Fallback: the mandal × irrigation pool, then missing.

## Baselines
1. **Persistence:** forecast = latest NDVI.
2. **Climatology:** forecast = point climatology at the target day (persistence if missing).
3. **Anomaly persistence:** forecast = climatology at the target day + (latest NDVI − climatology at the latest day).

The existing satellite-module models forecast an SPEI drought class, not NDVI. They are not a like-for-like baseline and are not scored here.

## Splits (chronological; main test)
- **Train:** 2019-20, 2020-21, 2021-22.
- **Validation:** 2022-23, used only for early stopping.
- **Final model:** refit on 2019-20 to 2022-23 with the number of trees chosen on validation.
- **Test:** 2023-24, 2024-25, 2025-26. Never used for any choice.
- **Secondary:** leave-one-season-out, labelled retrospective; it may be added later.

## Model
- XGBoost regression (`reg:squarederror`) with fixed settings, no tuning:
  - max_depth 6, learning_rate 0.05, subsample 0.8, colsample_bytree 0.8;
  - up to 2,000 trees, early stopping after 50; seed 0.
- The model predicts the 15-day **change** (target − latest NDVI). The forecast is latest NDVI + change.

## Metrics and populations
- **Metrics:** MAE and RMSE of the forecast NDVI. Skill = 1 − MAE_model ÷ MAE_baseline.
- **Breakdowns:** by test season, rainfed vs irrigated.
- **Populations:**
  - (a) all eligible instances, empty fields included;
  - (b) **established at issue**: season-so-far maximum ≥ 0.35 and ≥ 0.15 above the season-so-far minimum.
- **Deterioration:** in population (b), an event is an observed 15-day change ≤ −0.10. Reported:
  - AUC of the predicted change;
  - precision and recall of "predicted change ≤ −0.10".
- **Uncertainty:** cluster bootstrap over points, 1,000 resamples, seed 12345. Rows from the same point are correlated and are resampled together.

## Acceptance rule
The forecast is called **useful** only if, **in each of the three test seasons**, its MAE is lower than every baseline, **and** the 95 % bootstrap interval of (MAE_model − MAE_best baseline), pooled over the test seasons, is entirely below 0. Otherwise the result is reported as it is.

A useful forecast is **vegetation-condition evidence**. It becomes agricultural-drought evidence only after independent validation.

## Amendment A1 (22 November 2026, after the first run c976795; from an independent review)
The first run (c976795) had three input errors. It is kept in git and reported as **superseded**. The corrected run replaces it, and the acceptance rule is unchanged.
1. **Future image date in a feature.** `clim_target` was evaluated on the day of the actual future image used as target. That date depends on future clouds, so it is unknown at issue time. It is now evaluated at **issue date + 15 days** for the model and the baselines. The actual future image is used only for scoring.
2. **Weather source.** The first run read the legacy weather files (`data/processed/weather`), whose SPEI is the old full-record calibration and is missing in about 27 % of the test rows. The corrected run reads `data/prepared/<cell>.csv`: the weather module's v3/v4 files, SPEI recalibrated on 1979–2011 only with frozen parameters (`src/dataprep/prepare_data.py`, `results/v4/spei_calibration.json`). Missingness is reported.
3. **Weather availability.** AgERA5 is published with a delay of about 8 days, so the main run uses weather dated ≤ t − **8** days. A run with a 1-day delay is reported as a sensitivity check only.

**Added reports, decided before the corrected run:**
- **Satellite-only XGBoost:** same settings, without the weather inputs. It shows whether weather improves accuracy, which feature importance cannot show.
- **December–March subset** by season.
- **Weather-cell cluster bootstrap** in addition to the point bootstrap.
- **Span of the "decline":** from the latest observation to the target. It is reported as "decline from the latest observation to the forecast target". It does not distinguish drought from harvest.
