# Rabi early-drying (drought-risk) detection, experiment v1: rules fixed before the run

**Fixed:** 22 November 2026, before this experiment was run. The git commit that adds this file dates it.

**Code:**
- `src/detect/build_labels.py`
- `src/detect/build_dataset.py`
- `src/detect/train_eval.py`

## What has already been seen (disclosure)
- The seasons 2019-20 to 2025-26, including the evaluation seasons 2023-24 to 2025-26, were examined during development:
  - the rabi forecast;
  - the mandal summaries;
  - a quick XGBoost test of this task (`src/detect/quick_v0_*`, `results/detect_quick_v0/`).
- The evaluation seasons stay excluded from fitting and from every choice made in this experiment. They are **historical evaluation seasons already consulted during development, not unseen data.**

## What is predicted
- The target is **early drying of an established rabi crop**, defined from the Sentinel-2 series of the point. It is a satellite-defined **drought-risk event**, not field-verified agricultural drought.
- Its link with water shortage is checked separately (see "Drought check" below) and is reported as supporting evidence only.

## Points and phenology (1,350 C3 points; cleaned observations as in FORECAST_v1)
For each point and season (1 Oct to 30 Apr):
- **Smoothing:** NDVI series = 3-observation rolling median.
- **Trough T:** the lowest value from October to December (day of season ≤ 91).
- **Peak P:** the highest value after T.
- **Established:** P ≥ 0.35 and P − T ≥ 0.15.
- **Drying date D:** the first observation after the peak at which NDVI < T + 0.5 (P − T) for two consecutive observations.
  - If there is none, the crop did not dry before 30 April.
- **Rabi point** for a season: the point was established in at least 2 of the reference seasons 2019-20 to 2022-23, excluding the season itself.
- **Normal drying day N:** the median D over those established reference seasons.
- **Early-drying season:** established, and D ≤ N − 21 days.
- **Season quality:** at least 8 observations, and at least 2 of them in October–December. Otherwise the point-season is excluded and counted.

## Status and targets
- **Status on day d:**
  - 1 if the season is an early-drying season and D ≤ d (the crop has already dried early);
  - 0 otherwise.
- **Issue dates t:** every 5 days from 1 December to 31 March.
- **Horizons:** h = 7, 15, 30 days; t + h ≤ 30 April.
- **Target:** status on day t + h.
- **Eligible instance** (decided with information up to t only):
  - a rabi point;
  - established by t, from observations ≤ t − 2 days;
  - the latest observation ≤ 12 days old.
  - Excluded instances are counted.
- **New-onset subset:** status at t is 0, so drying has not started yet. Here recall and lead time (D − t) are reported separately.

## Inputs (information available at t)
- **Satellite** (observations ≤ t − 2 days):
  - latest NDVI and its age;
  - peak so far, days since the peak, drop from the peak, drop as a share of the amplitude;
  - 15- and 30-day changes;
  - anomaly versus the point's normal curve on that day;
  - status at t.
- **Point history:**
  - normal drying day N, and days from t to N;
  - the point's normal curve: mean of the reference seasons excluding its own;
  - day of season, irrigated flag.
- **Weather** (AgERA5 dated ≤ t − 8 days, from `data/prepared`, frozen SPEI):
  - June–November rain as a ratio to its 1979–2011 mean;
  - rain since 1 October and over the last 60 days;
  - mean ET0 and Tmax over 30 days;
  - SPEI.

## Splits
- **Train:** 2019-20 to 2021-22.
- **Validation:** 2022-23. Used for ensemble weights and decision thresholds.
- **Evaluation:** 2023-24, 2024-25, 2025-26. Never used for any choice.

## Models
Fixed settings, no tuning, 5 seeds for the stochastic models:
1. Logistic regression (standardised inputs, balanced class weights).
2. Random forest: 500 trees, min_samples_leaf 5, balanced subsample.
3. XGBoost: 400 trees, depth 4, learning rate 0.05, subsample 0.8, colsample 0.8, scale_pos_weight = negatives / positives.
4. **Ensemble, equal weights:** mean probability of models 1–3.
5. **Ensemble, validation-weighted:** weights proportional to validation PR-AUC.

**Decision threshold:** chosen on validation (maximum balanced accuracy) for each model and horizon.

## Baselines
1. Persistence: status at t.
2. Below-normal now: −anomaly.
3. Drop from the observed peak, as a share of the amplitude.
4. Early-drying rule: the drop share is ≥ 0.5 and t + h ≤ N − 21.

Baselines 2–4 are scored by AUC. Baseline 1 and the rule are also scored as yes/no.

## Metrics
- Per horizon, on all eligible instances and on the new-onset subset:
  - accuracy, balanced accuracy, precision, recall, F1, ROC-AUC, PR-AUC;
  - counts and seasonal breakdowns.
- **Seeds:** mean ± s.d. over seeds. Seeds are not independent seasonal tests.
- **Uncertainty:** 95 % cluster-bootstrap interval over points of the AUC difference (ensemble − best baseline).

## Drought check (separate from accuracy)
- At cell-season level: the share of established rabi crops with early drying, against June–November rain relative to normal (Spearman correlation).
- The early-drying rate when rain < 80 % of normal, against otherwise.

## Wording
- The result is an **early-drying risk model**.
- Its accuracy is accuracy against the satellite-defined early-drying label.
- Whether its alerts represent agricultural drought is supported by the rain association, and needs independent field or UAV confirmation.
