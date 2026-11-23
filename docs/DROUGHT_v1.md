# Rabi root-zone drought prediction: development protocol

Written 23 November 2026 before fitting this experiment. The user requested
drought prediction. This extends the earlier crop-drying study; it does not
rename its satellite labels as drought. Regional history was already examined
during development. This is not a prospective preregistration.

## Prediction target and scale

Predict the seven-day mean root-zone soil-moisture percentile ending 7, 15 or
30 days after issue. All seven target days are in the future. Below or equal
to the 20th percentile is soil-moisture drought; <=10th is severe-or-worse
soil-moisture deficit. Above 20 is "no percentile-defined deficit", not a
guarantee of healthy crops. The 10/20 percentile convention is motivated by
NOAA CPC's soil-moisture drought categories, not fitted to local declarations.
Local agricultural validity still needs assessment.

Data: ERA5-Land daily soil-water means at 0-7, 7-28 and 28-100 cm through
Open-Meteo's archive API, explicitly models=era5_land, nearest grid cell, UTC,
elevation=nan. Root-zone volumetric water is 0.07*layer1+0.21*layer2+0.72*layer3.
These are ~11 km model grid estimates, not field measurements. AgERA5 and
ERA5-Land share ERA5 forcing: agreement is not independent field validation.
The source does not resolve actual farm irrigation; the application is regional
rainfed drought risk. No field-level severity labels are inferred by replication.

Reference distribution: 1981-2000 only, seven-day trailing root-zone means,
calendar-day +/-15 days pooled across reference years. Feb 29 uses Feb 28's
calendar bin. Percentile uses a midrank empirical CDF to handle rounded data.
No validation/evaluation period contributes to this reference.

Whole rabi seasons (start-year notation): train 2001-2016 (through Mar 2017),
validate 2017-2022, evaluate 2023-2025. Issue Dec 1-Mar 31 every five days.
The last target can be Apr 30. Adjacent splits have months of separation.
Five distinct weather cells are the units; sampled satellite pixels do not
multiply the soil-model sample size. Save exact source coordinates and hashes.

## Available information and models

Both soil and AgERA5 inputs are dated <=issue-8 days. ERA5-Land's advertised
five-day delay is buffered to eight days, but final reanalysis is not an archive
of original release vintages. Results are a latency-aware hindcast, not proof
of historical real-time availability. Missing/stale data cause abstention.
No observed future rain, soil water, target date selected by clouds, final
season crop status or official declaration enters predictors.

Inputs: recent soil level/percentile/trends, causal rain and reference ET sums,
temperature, seasonal date and cell identity. Crop histories remain separate
context: they are not drought ground truth. Fit soil-only and soil+weather
candidates to quantify weather's added value.

Small fixed comparison: logistic regression, random forests (minimum leaves
5/15), histogram gradient boosting (7/15 leaves), and a probability average of
the learned candidates. Baselines: class/percentile persistence, training
climatology, training-only conditional transition and a damped percentile trend.
Random seed 42; no large architecture or hyperparameter search. Pick model by
validation drought average precision, with Brier score as tie break; baselines
are eligible to win. Pick binary alert threshold on validation maximizing F0.5
subject to recall >=0.50. Report the recall/precision trade-off explicitly.
Probability-like scores are not claimed calibrated. Forecast class is argmax
for learned probabilities, deterministic class for persistence/trend.

Save and lock selection plus model files before computing 2023-2025 scores.
Report every fixed candidate; do not retune after viewing evaluation results.
Primary horizon 15 days; 7 and 30 are reported separately. No claim of "best"
beyond the fixed candidates and validation criterion.

## Checks and deliverables

Scores: macro-F1 for three classes; drought AP, ROC-AUC, Brier, precision and
recall at the validation threshold; separate new-onset subset (true issue-day
soil percentile >20) from ongoing drought. Unknown issue-day truth is used only
to evaluate that subset, never to issue alerts. Include season/cell tables,
coverage and block-bootstrap uncertainty resampling whole seasons across cells.
Only three evaluation seasons limit inference. Show persistence on identical rows.

Deliver saved inference bundles, daily input/ref cache, source metadata, an
as-of-date prediction command and a report. Predictions expose source dates,
horizon, model, regional drought risk score, severity category and coverage.
Unsupported dates/locations abstain. Existing early-drying and NDVI results are
preserved. No commit or push is included in this work.

Required tests: future weather/soil mutations cannot alter issue features;
post-reference mutations cannot alter normals; seven target days are future;
whole seasons remain together; stale/missing inputs abstain; serialized inference
reproduces evaluation; changing evaluation labels cannot alter selection.

## Primary sources

- https://open-meteo.com/en/docs/historical-weather-api
- https://www.cpc.ncep.noaa.gov/products/Drought/Monitoring/smp_body.shtml
- https://www.drought.gov/what-is-drought/soil-moisture-and-drought

## Post-run diagnostic amendment, 23 November 2026

The fixed definition yielded zero evaluation drought targets in 2023-2025.
Do not change its baseline or thresholds to force those seasons to be drought.
Recall/AP/AUC are unestimable there, rather than zero or perfect. Retain the
chosen main models; package them as research candidates, not a proven best model.

Before fitting the additional check, specify one earlier chronological backtest:
train 2001-2013, validation 2014-2016, evaluation 2017-2019. Same reference,
features, fixed candidates and selection rule. The season prevalence table has
already been viewed, so this is a post hoc stress diagnostic. It does not change
the primary selection or provide an untouched test. Include onset-only scores.
Also compare ERA5-Land soil-percentile labels with NASA POWER MERRA-2 GWETROOT,
using the same 1981-2000 reference and calendar rule. This independent-product
comparison is not ground truth, and will not tune/replace the primary labels.

Reporting correction: the first threshold routine also applied the recall floor
to deterministic persistence/trend rules, sometimes turning them into an
always-warn rule. Those binary baselines now keep threshold 0.5; their probabilities,
AP, Brier scores and the AP-based model selection do not change. Recompute their
warning counts from saved data without refitting learned models. No learned
threshold is changed. Inference also refuses dates before Dec 2023 because the
main model selection used validation outcomes through Apr 2023.
