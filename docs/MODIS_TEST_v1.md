# MODIS long-record test v1: does "soil drier than normal + greenness drop" identify rabi drought over 2000–2025?

**Registered:** 24 November 2026, **before** the MODIS data was exported. Script `src/gee/script_D2_modis_rabi.js` has not been run yet.

**Why:**
- The combined module (`docs/COMBINED_v1.md`) found that early-drying warnings under below-normal soil were 0.70 precise, against 0.31 under wet soil.
- That result came from only three Sentinel-2 test seasons, with one dry season (2023), and the rule was written after seeing related results.
- This test checks the same idea over 23 independent district-seasons per district, against crop statistics. The rules below are fixed now. Any change goes under Amendments, with its date.

## 1. Data
- **MODIS:** MOD13Q1 v061 NDVI, 250 m, 16-day composites, SummaryQA ≤ 1.
  - Only ESA WorldCover 2020 cropland is used.
  - Sep–Apr, seasons 2000-01 to 2025-26.
  - Units: Kurnool, Anantapur and Tumkur (FAO GAUL 2015 level 2), plus the 8 site areas (3 km radius).
- **A composite is used** only if its valid pixel count is at least 30 % of the unit's cropland pixels. Otherwise it is missing, never "normal".
- **Soil:** drought v2 district series `data/drought2/daily_district.csv.gz`.
  - `pct_median` = median grid-point percentile of 7-day root-zone moisture.
  - The soil reference is 1990–2004.
- **Outcome:** drought v2 district rabi yield index (`data/drought2/yields_district.csv`), 2000-01 to 2022-23.
  - **Loss season** = yield index ≤ −0.15.
  - The sown-area anomaly is a secondary outcome.

## 2. Indicators (all fixed)
- **NDVI percentile:** each composite is compared with reference seasons 2000-01 to 2009-10, same unit, composites within ±16 calendar days.
  - It uses the same empirical-percentile formula as drought v2.
  - At least 8 reference values are required.
- **Per unit-season, window 1 Dec – 28 Feb** (composite start date):
  - **VD** = share of valid composites with NDVI percentile ≤ 0.20 (low-greenness duration);
  - **VPCT** = mean NDVI percentile;
  - **CD (combined)** = share of valid composites where NDVI percentile ≤ 0.20 **and** the district soil `pct_median` on the composite start date is < 0.50;
  - **DD** (soil only) = the existing drought v2 deficit duration.
- **Early-warning versions at 15 January:**
  - composites are used only if start date + 20 days ≤ 15 Jan (publication delay);
  - soil is used up to 7 Jan (8-day delay);
  - the window is 1 Dec to the cutoff.

## 3. Tests
**Units and periods:**
- Districts Kurnool + Anantapur, pooled within district.
- **Evaluation seasons 2010-11 to 2022-23** (26 district-seasons). These are outside the NDVI reference.
- 2000-01 to 2009-10 is reported separately and marked "inside NDVI reference".
- Tumkur is reported separately, as in drought v2.

| Test | Measure | Comparison |
|---|---|---|
| T1 association | Within-district Spearman of DD, VD, VPCT, CD vs yield index (and vs sown area) | Each other; rain Jun–Nov and SPEI from drought v2 |
| T2 loss detection, season end | ROC-AUC for loss seasons; precision and recall of the fixed rule "CD ≥ 0.25" vs "VD ≥ 0.25" vs "DD ≥ 0.25" | Same |
| T3 early warning, 15 Jan | ROC-AUC of the 15 Jan versions | Soil deficit-so-far (the drought v2 15 Dec/15 Jan rows) |
| T4 greenness attribution | Among unit-composites with NDVI percentile ≤ 0.20: share falling in loss seasons when soil < 0.50, vs when soil ≥ 0.50 | This repeats the COMBINED_v1 soil-tag result on independent seasons |

**Uncertainty:** 95 % intervals by resampling whole seasons, 2000 draws.

**Primary hypotheses** (results reported as they come, whichever way):
- **H1:** in T4, the share of loss seasons is higher for low-greenness composites under soil < 0.50 than under soil ≥ 0.50.
- **H2:** in T2, the AUC of CD is at least the AUC of VD.

**Sites** (8 site areas, 2000–2025):
- Soil comes from each site's ERA5-Land cell percentile, using the same rule and the 1990–2004 reference.
- Bal and Pul use the Din cell.
- Code: `src/combined/modis.py`, written and tested on dummy data before the export.
- descriptive only: per site-season VD/CD table, and the inherited district loss-season flag;
- 2023-24 to 2025-26 are compared descriptively with the detect_v5 soil-tag results.
- **No accuracy claim is made at site scale.**

## 4. Not claimed
- Field-level drought.
- Crop identity.
- Causation of yield loss.
- Irrigated-crop stress.

The MODIS 250 m pixels mix fields; the cropland mask is from 2020 only.

## Amendments
**A1 (24 Nov 2026, data source only, before any result was seen)**
- The batch export stayed queued for more than 1 hour.
- The same computation was therefore fetched interactively with `src/gee/fetch_d2_direct.py`: same units, mask, collection, QA rule and columns.
- Cropland pixel counts are identical to the Code Editor printout.

## Results (run 24 Nov 2026; `results/modis_v1/MODIS_RESULTS.md`)
**Evaluation seasons 2010-11 to 2022-23**, Kurnool + Anantapur: 26 district-seasons, 9 loss seasons.

| Indicator | ρ vs yield index [95 % CI] | Loss-season AUC [95 % CI] |
|---|---|---|
| DD (soil deficit duration) | −0.58 [−0.84, −0.18] | 0.82 [0.64, 0.97] |
| VPCT (mean Dec–Feb NDVI percentile) | +0.70 [0.25, 0.92] | 0.83 [0.57, 1.00] |
| VPCT at 15 Jan (early warning) | – | 0.81 [0.53, 1.00] |
| VD = CD (low-greenness duration) | −0.39 [−0.52, −0.12] | 0.61 [0.50, 0.75] |
| Rain Jun–Nov | +0.54 [0.07, 0.79] | 0.80 [0.51, 0.98] |
| SPEI so far | +0.38 [−0.21, 0.78] | 0.65 [0.38, 0.89] |

**Hypotheses:**
- **H1 (T4): not testable.** Only 3 district composites in 2010–22 had NDVI percentile ≤ 0.20. All 3 had soil below normal and fell in loss seasons, so the "soil normal/wet" comparison group is empty.
- **H2:** holds only as a tie. CD and VD are identical (AUC 0.61), because every low-greenness composite also had soil below normal.

**Design flaw, found after the results:**
- District Dec–Feb NDVI rose from 0.32–0.38 (2000–09) to 0.40–0.46 (2017–25).
- Against the fixed 2000–09 reference, the mean percentile in 2017–25 is about 0.9.
- So the fixed "≤ 20th percentile" rule almost never fires after 2010, and VD/CD/T4 are weak by construction, not because greenness is uninformative.
- The registered continuous indicator VPCT, ranked within district, carries a strong signal: ρ +0.70, AUC 0.83.
- A trend-robust reference (for example, the previous 10 seasons) would be a **new, post-hoc analysis** and must be labelled exploratory.

**Seasons missed by every indicator:**
- Anantapur 2015 and 2021 are yield-loss seasons with no soil deficit and high greenness.
- These are consistent with losses not caused by drought, for example excess rain. This is not verified.
