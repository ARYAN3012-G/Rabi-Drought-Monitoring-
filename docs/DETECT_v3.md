# DETECT_v3 Protocol — Precision-Improved Early-Drying Model

**Registered:** 23 November 2026  
**Status:** Experiment (registered before evaluation results are examined)  
**Supersedes:** detect_v2 false-alarm analysis only. detect_v2 event ledger, models and results are preserved unchanged.

---

## Motivation

detect_v2 achieved high event recall (96%) but only 31.3% warning precision at the
30-day horizon — meaning 68.7% of issued warnings were false alarms. The primary cause
identified in the event sanity audit is the inability of NDVI-drop features alone to
distinguish:
1. **Drought stress** — slow NDVI decline beginning early in the season, below-normal peak.
2. **Normal harvest** — fast NDVI decline late in the season after a normal-height peak.

This protocol registers three changes to address this before examining evaluation results.

---

## Changes from detect_v2

### 1. Four New Harvest-Discrimination Features

All features are computed causally from observations dated before the issue date.
They are added to the existing 21 detect_v2 features, giving 26 total.

| Feature | Formula | Rationale |
|---------|---------|-----------|
| `drop_rate` | `(peak − ndvi) / max(days_since_peak, 1)` | Harvest → fast drop (days⁻¹); drought → slow drop |
| `season_progress` | `doy / normal_dry` | >1.0 at issue → field past its normal drying date → harvest |
| `anom_at_peak` | `peak − normal_curve[peak_doy]` | Stressed crop peaks below normal (negative); healthy crop peaks above |
| `rain_30_pre_peak` | Sum of daily rainfall 30 d before peak date | Low pre-peak rain → crop established under water stress |
| `irr_x_drop_rate` | `irr × drop_rate` | Irrigated fast-drying fields are almost always harvested, not drought-hit |

No feature uses information available only after the issue date. Weather inputs still
respect the 8-day publication lag.

### 2. F0.5 Threshold Tuning

detect_v2 selected thresholds by maximising `balanced_accuracy_score` (equal weight on
recall and specificity). detect_v3 selects thresholds by maximising `fbeta_score(beta=0.5)`,
which weights precision twice as heavily as recall. This reduces false-alarm volume at
the cost of some event recall.

The same grid (197 quantile points between the 1st and 99th percentiles of validation
probabilities) is used. Threshold selection uses validation data only.

### 3. Irrigation-Stratified Thresholds

Irrigated fields show very few confirmed drought events (they are buffered by borewells
and canal water). After computing the global F0.5 threshold, separate thresholds are
computed for the irrigated and rainfed validation subsets. Irrigated fields are warned
only when the model probability exceeds the stricter irrigated threshold.

---

## What is Not Changed

- Label definition (early = observed drying ≥ 21 days before normal_dry).
- Training seasons: 2019–2021.
- Validation season (threshold/model selection): 2022.
- Evaluation seasons: 2023–2025.
- Model architectures: Logistic Regression, Random Forest (n=500), XGBoost.
- Ensemble construction (equal and PR-AUC-weighted).
- Event aggregation logic (one event and one warned unit per point-season).
- detect_v2 output files (never overwritten).

---

## Outputs

| File | Description |
|------|-------------|
| `results/detect_v3/EVENT_REPORT_v3.md` | Main report with metrics table |
| `results/detect_v3/point_date_metrics.csv` | Per-horizon per-model point-date scores |
| `results/detect_v3/event_metrics.csv` | Per-horizon unique-event summary |
| `results/detect_v3/predictions.csv.gz` | Full evaluation predictions |
| `results/detect_v3/operating_points.json` | Selected models and F0.5 thresholds |
| `results/detect_v3/v2_vs_v3_comparison.csv` | Side-by-side precision/recall comparison |
| `data/detect_v3/instances.csv.gz` | Augmented dataset with new features |

---

## Expected Scientific Contribution

The v2 → v3 comparison is the core contribution to the Gap 3 paper section:

> *"We show that incorporating canopy-decline rate and phenological-stage features,
> combined with precision-weighted threshold calibration, reduces the false-alarm rate
> from 68.7% to approximately 35–45% at the 30-day horizon while retaining 80–88%
> event recall — a substantially more actionable operating point for field extension
> services."*

The result (whether the target is met, exceeded, or not reached) is reported as-is.
No post-hoc label changes or threshold reselection on evaluation data are permitted.

---

## Reproduction

```powershell
python -B src/detect/causal_events_v3.py
python -B src/detect/causal_events_v3.py --compare
```
