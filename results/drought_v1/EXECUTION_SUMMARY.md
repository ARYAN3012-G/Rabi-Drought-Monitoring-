# What was built for drought prediction

23 November 2026. Local changes only; no commit or push.

## Deliverable

A separate regional rabi **root-zone soil-moisture drought predictor**, with
saved models at 7, 15 and 30 days. The target is water shortage relative to a
fixed historical reference, not satellite early drying. Existing NDVI and
early-drying experiments remain intact. This is an experimental predictor,
not a proven best model or field-verified agricultural drought diagnosis.

- Downloaded 82,780 daily cell records, Jan 1981-Apr 2026, across five ERA5-Land
  cells. Weighted the 0-7, 7-28 and 28-100 cm layers into a root-zone mean.
- Built a fixed 1981-2000 seasonal reference. Forecast a wholly future seven-day
  mean: <=20th percentile is deficit; <=10th is severe-or-worse deficit.
- Trained 2001-2016 rabi seasons; selected models and thresholds on 2017-2022;
  evaluated 2023-2025. Soil/weather inputs stop eight days before issue.
- Compared logistic regression, random forest, histogram gradient boosting,
  an ensemble, soil analogues and persistence/transition/climatology baselines.
  Included soil-only and soil+weather versions.
- Saved selected model bundles, reference, probabilities, thresholds, source
  responses, source hashes, coverage and reproducible inference commands.
- Added a crop-context output using only recent available Sentinel-2 images.
  Regional scores are shared by grid cell, not independent field predictions.
  Irrigated points explicitly lack irrigation-supply information.

The main validation selection is histogram gradient boosting with soil-history
inputs at all horizons (7 leaves for 7/15 days, 15 leaves for 30 days). Weather
candidates were compared, but are not the selected main models. This does not
establish that weather is unimportant to agricultural drought.

## What the evidence permits

**Recent evaluation:** no ERA5-defined drought targets at these sampled issue
dates in 2023-2025, and no warnings from the selected models. Recall and AUC are
unestimable, not 100%. A no-warning baseline also succeeds on those negatives.

**Additional earlier chronological check:** train 2001-2013, validate 2014-2016,
evaluate 2017-2019. This was specified after seeing the prevalence table, so it
is a post hoc historical diagnostic. At 15 days, the selected soil+weather
boosting model caught 25/30 drought-labelled cell-dates (83% recall) with 25/49
warnings correct (51% precision). On the new-onset subset, it caught 3/8 with
3/14 warnings correct (21% precision). A simple conditional-transition baseline
caught 6/8 with 6/17 warnings correct. These are correlated cell-dates, not
counts of independent drought episodes. The learned model did not demonstrate
superior new-onset prediction in this check.

**Independent-product check:** at the primary 15-day target dates, NASA MERRA-2
has 15 dry cell-dates in 2023-24 and two in 2024-25; ERA5-Land has none. Different
soil models, spatial support and rounded NASA values limit comparison. Neither
is field truth. No target definition or selected main model was changed to
improve agreement with NASA or government declarations.

## How to run

From the rabi repository:

```powershell
python -B -m src.drought.run predict --date 2026-03-01
python -B -m src.drought.crop_context --date 2026-03-01
```

This produces a historical replay in `results/drought_v1/forecasts/2026-03-01/`:
`regional_drought_risk.csv` (15 regional forecasts) and
`sampled_point_context.csv` (1,350 points x three horizons, context only).

Inference rejects dates before model selection could have been completed and
dates outside Dec-Mar. Missing/stale inputs abstain. The frozen soil download
currently ends Apr 2026 and local AgERA5 ends 2 Nov 2026: update both before
issuing future-season predictions. Do not present the historical demo as live.

```powershell
python -B src/drought/fetch_soil.py --end YYYY-MM-DD
# Update corrected AgERA5 through the existing weather-module workflow.
python -B -m src.drought.run predict --date YYYY-MM-DD
```

Tests: `tests/test_drought_prediction.py`; saved-artifact checks:
`python -B -m src.drought.audit`. Full reproduction and the frozen development
choices are in `docs/DROUGHT_v1.md`; main tables in `DROUGHT_REPORT.md`, earlier
diagnostic in `backtest/BACKTEST_REPORT.md`, product check in
`cross_product/CROSS_PRODUCT_REPORT.md`.

The next scientific requirement is validation of the regional soil target and
crop water stress, including management/harvest information. More architectures
or tuning on the known 2023-2025 seasons cannot provide that evidence.
