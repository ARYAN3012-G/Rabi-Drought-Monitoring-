# DETECT_v6: corrected detect_v5

**Written:** 24 November 2026, before detect_v6 was run.

**Code:** `src/detect/causal_events_v6.py`. It reuses the detect_v5 features, labels, splits and event scoring unmodified.

**Detect_v3–v5 files:** left unchanged. The corrections are listed in section 3.

## 1. Why
The audit in `docs/COMBINED_v1.md` found that three v5 choices had been made after the evaluation-season results were seen:
1. **The model:** Random forest was hard-coded.
2. **The thresholds:** the recall targets went 0.60/0.75 → 0.35/0.70 → 0.50/0.70. Commit messages say "to reduce false alarm rate to 27.8 %" and "to catch more true events".
3. **The soil veto:** rootzone < 0.30 m³/m³. It lowered F0.5 on validation at every horizon.

## 2. Rules (all decided on validation 2022 or earlier documents)
| Item | detect_v6 | Source of the rule |
|---|---|---|
| Features, labels, splits, event scoring | As detect_v5 | Unchanged |
| Model | Highest validation PR-AUC among LR, RF, XGBoost and the two ensembles | As detect_v2 to v4 |
| Thresholds | Maximise F0.5 on validation, separately for irrigated and rainfed points | The rule registered in `docs/DETECT_v3.md` (§2–3) |
| Soil veto | None | Validation evidence (COMBINED_v1 §1) |
| Soil context | Each warning gets the cell's 7-day root-zone percentile at issue − 8 days (drought v2 method, 1990–2004 reference): **soil-dry** < 0.50, **soil-wet** ≥ 0.50 | drought v2 |

**Disclosure:**
- The evaluation seasons 2023–25 have already been looked at many times, by v2–v5 and by COMBINED_v1. detect_v6 is therefore a **re-analysis with corrected rules**, not a fresh test.
- The soil-tag contrast is descriptive on these seasons. Its independent test is `docs/MODIS_TEST_v1.md`, 2010–2022.

## 3. Errata for detect_v5 (`docs/DETECT_v5.md`, `results/detect_v5/EVENT_REPORT_v5.md`, README)
| Statement in v5 | Correction |
|---|---|
| "Physics-guided soil gate: rootzone ≥ 0.30 means normal-to-wet" | 0.30 m³/m³ is about the **median** root-zone value of the two Kurnool black-soil cells. It is above almost all values in the other three cells (medians 0.19–0.21), so it is not a uniform "wet" limit. On validation 2022 the veto lowered F0.5 at 7/15/30 days (0.397→0.227, 0.335→0.222, 0.347→0.270). |
| "False alarm rate 68.7 % → 30.4 %" | Correct as warning precision, but event recall fell from 0.963 (v2) to 0.444. 39 of the 48 caught events are from 2023-24. By season, recall is 2023: 0.66, 2024: 0.18, 2025: 0.19. |
| Dual confirmation "59.7 %, 62 warnings" | The report and code give precision 0.636 with 11 warnings and 7 events caught (recall 0.065). |
| Report text "~40 % false alarms, ~60 % precision" | Stale. It does not match the table. |
| Irrigated recall 0.35 → 0.50 "to catch more true events" | Chosen after the evaluation results were seen. It is not a validated choice. |
| `selected = 'Random forest'` "achieves peak precision" | Chosen on evaluation results. Validation PR-AUC also picks RF at 7 and 30 days, but at 15 days it picks the weighted ensemble. |
| DETECT_v3 registered F0.5 thresholds | The v3 code used recall-constrained thresholds instead. The deviation was not disclosed. |
| "Inferred crop type" (early/mid/late) | This is the point's own earlier peak date, not observed crop identity. The code comments disagree on which crop is "early". |
| "Follows US Drought Monitor / Copernicus EMS" (2-issue confirmation) | No source is cited. Remove, or cite. |

## 4. Results (run 24 Nov 2026; `results/detect_v6/EVENT_REPORT_v6.md`)

**Registered operating point** (test 2023–25, 108 events):

| Horizon | Model (chosen on validation) | Caught | Warned | Precision [95 % CI] | Recall [95 % CI] | Lead |
|---|---|---|---|---|---|---|
| 7 days | Random forest | 20 | 81 | 0.25 [0.14, 0.36] | 0.19 [0.11, 0.27] | 5 days |
| 15 days | Ensemble weighted | 9 | 29 | 0.31 [0.15, 0.48] | 0.08 [0.03, 0.14] | 11 days |
| 30 days | Random forest | 30 | 56 | 0.54 [0.42, 0.66] | 0.28 [0.20, 0.36] | 16 days |

The registered F0.5 rule warns rarely.

**Threshold-free comparison** (`results/detect_v6/curve_vs_v2.csv`): precision when the threshold is set to catch the same number of events.

| Horizon | Caught | detect_v6 | detect_v2 | detect_v6, soil-dry warnings only |
|---|---|---|---|---|
| 30 days | 20 | 0.50 | 0.54 | 0.71 |
| 30 days | 40 | 0.56 | 0.51 | 0.69 |
| 30 days | 50 | 0.50 | 0.48 | 0.59 |
| 15 days | 40 | 0.36 | 0.41 | 0.61 |
| 7 days | 40 | 0.27 | 0.35 | 0.50 |

**Conclusions:**
- The v3–v5 features do **not** clearly improve on detect_v2: they are slightly better at 30 days, similar at 15 days and worse at 7 days.
- Soil context raises precision at every horizon, by 0.13 to 0.25, while catching the same number of events (up to the 59 events that occur under soil-dry conditions).
- This soil result is descriptive: these seasons had been seen before. It is tested independently in `docs/MODIS_TEST_v1.md`.
