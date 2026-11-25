# Combined rabi module v1: audit of detect_v3–v5 and combination with drought v2

**Date:** 24 November 2026.

**Folder:** `rabi_module_v2`, a clone of github.com/MULLANGIROVAN/Rabi-crop at 7f37cfb, plus copied drought v2 files. Nothing is committed.

**Code:** `src/combined/fuse.py`. Run it with `python -B -m src.combined.fuse`.

**Outputs:** `results/combined_v1/`.

## 1. Audit of the friend's detect_v3, v4 and v5

**What was checked:**
- The code was read in full: `src/detect/causal_events_v3/v4/v5.py`.
- The v5 Random forest was re-run unmodified.
- The results were re-scored independently.

| Item | Finding | Verdict |
|---|---|---|
| Reproducibility | v5 30-day results reproduce exactly: 48 events caught, 69 warnings, precision 0.696. | Correct |
| Future data in the features | Weather and soil are joined at issue − 8 days. Crop priors use training seasons 2019–21 only. Splits are by whole season. | Correct |
| Model choice | `selected = 'Random forest'` is hard-coded. Validation PR-AUC would also pick Random forest at 7 and 30 days, but at 15 days it would pick the weighted ensemble (0.340 vs 0.323). | Minor |
| Soil veto `rootzone < 0.30 m³/m³` | 0.30 is about the median root-zone value of the two Kurnool black-soil cells (0.30–0.31). It is above almost every value in the other three cells (medians 0.19–0.21). So it acts as a Kurnool filter, not a physical "wet soil" limit. | Not valid as stated |
| Veto on validation 2022 | The veto **lowered** F0.5 at every horizon: at 30 days, 0.347 → 0.270, with recall 0.78 → 0.22. Selection on validation would have rejected it. Its benefit appears only on the test seasons. | Selection effectively on the test seasons |
| Irrigated recall target 0.35 → 0.50 (24 Nov) | Changed after the earlier v5 results had been seen, "to catch more true events". | Post-hoc |
| v3 threshold rule | `DETECT_v3.md` registers F0.5 thresholds; the code and report use recall-constrained thresholds. | Deviation, not disclosed |
| Headline "false alarms 68.7 % → 30.4 %" | True for precision, but recall fell from 0.96 (v2) to 0.44 (v5), so 60 of 108 events are missed. 39 of the 48 catches come from one season, 2023. | Incomplete framing |
| Report consistency | `DETECT_v5.md` gives dual confirmation as 59.7 % / 62 warnings; the report gives 63.6 % / 11 warnings with recall 0.065. The report text says "~40 % false alarms / ~60 % precision". | Inconsistent |
| "Inferred crop type" | It is based on the point's own earlier peak date, not observed crop identity. The code comments contradict each other on which crop is "early". | Wording only |

**Value of the new features at equal recall** (test 2023–25; precision when a raised threshold alone gives the same number of caught events):

| Horizon | v5 Random forest | detect_v2 |
|---|---|---|
| 30 days, 62 events caught | 0.488 | 0.443 |
| 15 days, 64 events caught | 0.374 | 0.388 |
| 7 days, 48 events caught | 0.282 | 0.356 |

The v3–v5 features give **no clear gain** over v2 once recall is matched.

## 2. What soil moisture adds (drought v2 percentile, not an absolute value)

**Soil context for each warning:**
- the cell's 7-day root-zone percentile at the input cutoff (issue − 8 days);
- reference seasons 1990–2004, ±15 calendar days, using the same function as drought v2 (`src/drought2/indicators.percentiles`);
- **soil-dry** = below the cell's own median for that date; **soil-wet** otherwise.

**Disclosure:**
- This rule was written after seeing that the absolute veto acts as a Kurnool filter, but before seeing its own results.
- A stricter variant (warn only in soil deficit, percentile ≤ 0.20) gave **zero** warnings in 2022–2025. Soil deficit days were rare in those seasons: at most 7 % of Nov–Feb days, in 2023.

**Soil-moisture percentile by season** (Nov–Feb median, all 5 cells):
- **2022, 2024 and 2025:** 0.81–1.00, wetter than normal.
- **2023:** 0.36–0.42, drier than normal but not in deficit.

So most "early-drying" events in the 2024 and 2025 test seasons happened while the soil was wetter than normal. They are probably harvest or management, not water shortage.

**Precision of the validation-selected v5 warnings, split by soil tag** (test 2023–25, point-seasons):

| Horizon | Soil-dry warnings | Correct | Precision | Soil-wet warnings | Correct | Precision |
|---|---|---|---|---|---|---|
| 7 days | 63 | 30 | 0.48 | 107 | 18 | 0.17 |
| 15 days | 72 | 41 | 0.57 | 99 | 23 | 0.23 |
| 30 days | 57 | 40 | **0.70** | 70 | 22 | 0.31 |

## 3. Combined rabi module: design

| Layer | Source | Question it answers | Unit | Evidence |
|---|---|---|---|---|
| 1. Season drought indicator | drought v2 (ours) | Is this rabi season a soil-moisture drought in the district? | District / grid | Deficit duration vs multi-crop rabi yield: ρ −0.58 [−0.74, −0.36] (2000–22). 15 Dec warning of yield-loss seasons: AUC 0.80 [0.62, 0.95], better than rain (0.72) and SPEI (0.60). |
| 2. Early-drying warning | detect_v5 Random forest (friend), validation-selected thresholds | Which fields will dry early, 7–30 days ahead? | Field point | Test 2023–25, 30 days: precision 0.49 [0.40, 0.57], recall 0.57 [0.48, 0.67], median lead 21.5 days |
| 3. Soil attribution tag | drought v2 percentile applied to layer 2 | Is the drying water-driven (soil below normal) or likely harvest (soil wet)? | Each warning | Soil-dry warnings 0.70 precise vs soil-wet 0.31 (30 days, test seasons) |

## 4. Results to report (test 2023–25, 108 early-drying events, 95 % point-cluster bootstrap)

| Operating point | Horizon | Caught | Warned | Precision | Recall | Lead | Status |
|---|---|---|---|---|---|---|---|
| **A. v5 Random forest, validation-selected** | 30 days | 62 | 127 | **0.49** [0.40, 0.57] | **0.57** [0.48, 0.67] | 21.5 days | **Primary** |
| A | 15 days | 64 | 171 | 0.37 [0.30, 0.45] | 0.59 [0.50, 0.69] | 11 days | Primary |
| A | 7 days | 48 | 170 | 0.28 [0.21, 0.36] | 0.44 [0.35, 0.54] | 4 days | Primary |
| B. A + absolute veto 0.30 (friend) | 30 days | 48 | 69 | 0.70 [0.59, 0.81] | 0.44 [0.36, 0.54] | 23 days | Post-hoc; worse on validation |
| C. A + soil-dry filter (drought v2) | 30 days | 40 | 57 | 0.70 [0.58, 0.82] | 0.37 [0.29, 0.45] | 21 days | Post-hoc; zero warnings on validation |

**Threshold-only comparison:** at the same catch counts, raising the threshold alone gives precision 0.52 (48 caught) and 0.56 (40 caught). So **soil information does add precision on the test seasons**, but:
- the gain comes from one dry season, 2023;
- on validation 2022 it removed correct warnings;
- it is not a held-out result.

## 5. Allowed claims

**Allowed:**
- A field-scale model warns of early rabi canopy drying up to 30 days ahead (satellite proxy, historical evaluation).
- A district soil-moisture deficit-duration indicator relates to independent rabi crop losses.
- Warnings issued under below-normal soil are about twice as often correct as warnings under wet soil.

**Not allowed:**
- "70 % precision drought detection" as a held-out result;
- "physics-guided veto";
- field-verified drought;
- crop identity.

**Data limits:**
- **Only one test season (2023) had below-normal soil**, and no test season had a soil deficit.
- Point-level drought cannot be validated until field observations exist (`data/field_validation/FIELD_TEMPLATE_v2.csv`).
- Comparison only: Kurnool rabi was declared drought in 2023-24 and 2024-25. ERA5-Land soil was wet in 2024-25, so the two disagree that season.
