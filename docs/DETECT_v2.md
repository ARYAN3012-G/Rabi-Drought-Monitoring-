# Detect v2: causal early-drying forecasts and event-based evaluation

Written 22 November 2026, after inspection of detect_v1 and its historical scores.
This is a documented development correction, not prospective preregistration.
The objective is prediction of satellite-defined early drying, not a verified
diagnosis of agricultural drought. No government orders are training labels.

## Why v1 is superseded

`src/detect/build_dataset.py` supplied `status_t` from the completed-season
`early` label and retrospective drying date as a model input. That status can
depend on later images and the future season peak. It is not an operational
observation. The shared reference included the 2022 validation season when
building training normals. June-November rainfall also included observations
not yet published at the first December issue dates. v1 saved mean probabilities
but not validation probabilities or decision thresholds, so an exact independent
event recount at its original operating points cannot be reconstructed without
refitting. v1 results are retained as superseded exploratory evidence.

## Fixed development settings, before the v2 rerun

- Train: 2019-20, 2020-21, 2021-22. Validation: 2022-23. Historical evaluation:
  2023-24, 2024-25, 2025-26. All these seasons have already been consulted.
- Reference normals and population selection use 2019-21 only; a training
  season excludes itself. Require at least two established reference seasons
  with observed drying dates. This reduces the population compared with v1;
  report the counts rather than comparing the two runs as identical cohorts.
- Keep v1's retrospective target definition: centered three-observation median,
  October-December trough, subsequent peak, establishment >=0.35 and amplitude
  >=0.15, first of two post-peak observations below half-amplitude, and drying
  >=21 days earlier than the reference median. A missing drying date means no
  *observed* crossing, not proof of a healthy crop. At least 8 season observations
  and 2 October-December observations are required to score a season.
- Issue dates every 5 days from 1 December through 31 March; horizons 7/15/30 days.
  Satellite observations must be <= issue-2 days and at most 12 days old. Weather
  is from corrected `data/prepared`, <= issue-8 days. June-November rain is cut
  off at the latest available date and compared with the same historical span.
- Inputs are rebuilt from the issue-time observation prefix. A causal observed
  drying flag uses only the peak and two consecutive below-half observations
  known at issue time; it is distinct from the retrospective label. No completed
  season status, peak, drying date, or end-of-season quality enters the features.
- Forecasts are produced independently of end-of-season observation quality;
  rows without an evaluable outcome are excluded from scoring, with counts.
- Target: a retrospective early-drying event in **(issue, issue+horizon]**.
  This is onset risk, not the cumulative "already happened" target in v1.
  Training and primary point-date evaluation use examples before retrospective
  onset and without an issue-time observed drying flag. Predictions for other
  issue-time-eligible rows are retained for the operational warning audit.
- Same small models as v1: standardized/imputed logistic regression; random
  forest (500 trees, minimum leaf 5); XGBoost (400 trees, depth 4, learning rate
  0.05, row/column sampling 0.8). Five seeds for RF/XGBoost, one for deterministic
  LR. Equal and validation-AP-weighted probability ensembles.
- Thresholds maximize validation balanced accuracy on new-onset examples.
  Ensemble weights and primary model choice (highest validation average
  precision) use validation only. Save every threshold, weight and validation
  probability. No threshold/model is chosen by historical test results.
- Evaluate seed-averaged deployment probabilities; show per-seed point-date
  metrics separately. Baselines: below-normal NDVI, drop share, the issue-time
  drying rule, and zero new-event risk. Imputation and score direction are fixed
  on training/validation, never evaluation data. No new baseline tuning after
  seeing evaluation scores.

## Unique-event and warning definitions

One event = one sampled point-season with the retrospective early-drying label.
These are sampled points, not independently delineated fields.

For horizon h, evaluate events after the first issue date and up to the last
issue date+h (bounded by 30 April). An event has forecast opportunity if at least
one eligible, not-already-observed-dry issue falls in [event-h, event). A hit is
at least one warning in that interval. Repeated warnings do not increase hits.
Report total events, events with opportunity, hits, recall among opportunity
events, and recall among all monitored events (including coverage failures).

Warning precision is also aggregated: one warned point-season counts once. It
is successful only if at least one of its warnings precedes the event by >0 and
<=h days. A late warning or one too far ahead earns no credit. A point-season
with earlier false alerts and a later timely alert counts once as successful;
report point-date precision too so this aggregation does not hide false alerts.
Lead time is event date minus the **first timely warning**, once per caught
event, not the median over repeated forecast rows. Also report recall with at
least 7 and at least 14 days of lead. Date is an image-based crossing date;
cloud gaps and retrospective smoothing limit exact physical-onset precision.

Bootstrap point-seasons grouped by point and by weather cell, 1000 draws, seed
12345. Five weather cells and three evaluation seasons limit inference. Rainfall
association is descriptive consistency evidence at cell-season scale, not
independent field-level confirmation or proof of causation.

## Required checks and outputs

- Mutating future satellite/validation data must not change training features.
- Moving an unknown retrospective event date must not change issue-time inputs.
- Early-December rain must exclude unpublished late-November observations.
- Repeated alerts count once; late/out-of-horizon alerts are not hits; events
  without opportunities remain in the end-to-end denominator.
- Save label coverage, issue exclusions, inputs, all prediction probabilities,
  thresholds, model-choice metadata, per-event records, point-date and event
  tables, a report, and input/source SHA-256 hashes under detect_v2 paths.

## Post-run diagnostic disclosure

After viewing the v2 event counts, an always-warn policy was added as an explicit
alert-burden sanity check (`src/detect/event_sanity.py`). It warns at every usable
issue and shows why high event recall and long first-timely lead alone do not
demonstrate useful discrimination. It does not change models, thresholds or
the validation-based model choice. The fixed C3 sampling/irrigation strata
were defined with WorldCover 2020/21 and summers 2019-23; this is a pre-evaluation
cohort, not a recreation of land-cover knowledge available in 2019. The strata
and historical development status must be retained in interpretation.
