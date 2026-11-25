# Rabi drought v2: soil-moisture deficit duration, crop-impact association and 15-day forecast

**Branch:** `rabi-drought-v2`.

**Written:** 23 November 2026, before the indicator, validation or forecast results were computed. It is not committed, so no git date proves the order. The rules below were not changed after seeing results; any later change is listed under Amendments.

**Places:** the 8 study sites of the kharif module only.
- Their mandals are monitored by the existing rabi products.
- District-scale checks use the three districts containing the sites, on pre-2022 boundaries: **Kurnool** (incl. Nandyal), **Anantapur** (incl. Sri Sathya Sai), **Tumkur**.
- **Crops:** all rabi crops. No single crop is assumed.

## 1. Published approach: extraction and adaptation

**Primary reference:** Padhee, Nikam, Dutta & Aggarwal (2017), *Using satellite-based soil moisture to detect and monitor spatiotemporal traces of agricultural drought over Bundelkhand region of India*, GIScience & Remote Sensing, doi:10.1080/15481603.2017.1286725.

**Access:** the full text could not be retrieved (HTTP 403 from the publisher and the mirrors, 23 Nov 2026). The abstract-level description is:
- a time-based function of satellite soil moisture as an agricultural-drought indicator;
- mapping of *frequent soil-moisture deficit areas during the rabi season*;
- spatio-temporal severity;
- the reference list includes the Soil Moisture Deficit Index (Narasimhan & Srinivasan 2005).

**No equation, threshold or reference period below is attributed to the paper.** All of them are ours.

| Element | Paper (as accessible) | This study | Type |
|---|---|---|---|
| Soil moisture | Satellite soil moisture (product not verified) | ERA5-Land root zone (0–100 cm, layer-weighted), via the Open-Meteo archive. **Modelled reanalysis, not a satellite measurement.** | B: adaptation (product availability, root zone) |
| Area | Bundelkhand agricultural area | 0.3° grid points inside the district polygons. **No cropland mask** (Earth Engine needed); 45 points. | B |
| Deficit | Soil-moisture deficit relative to normal (definition not verified) | Empirical percentile of the 7-day mean vs reference seasons 1990-91..2004-05, same point, ±15 calendar days. Deficit ≤ 20th percentile, severe ≤ 10th. | B |
| Duration / frequency | Time-based function, frequency of deficit in rabi | **DD** = share of days 1 Nov–28 Feb in deficit (mean over points); **DDS** = severe; **RUN** = longest run | A/B: concept follows the paper, formula is ours |
| Vegetation condition | Computed alongside (index not verified) | Historical district VCI needs a MODIS export: `src/gee/script_D1_district_vci.js` (pending, user Earth Engine). Sentinel-2 crop context exists only from 2019. | **Pending** |
| Impact check | Crop-specific seasonal yield | District rabi yield of every major rabi crop, a fixed-weight multi-crop index, and sown-area anomalies (APY 1997–2022) | A/B |
| Forecast | Not part of the paper | 15-day district deficit forecast (section 5) | C: our extension |

**Supporting references, used only as context:**
- Padhee et al. 2014: rainfall → soil moisture → NDVI lag. Its use of future rainfall is **not** copied; future rain appears only in a labelled oracle.
- ICRISAT chickpea mapping, Nandyal/Kadapa 2025-26: crop identity context, not drought evidence.
- Sharma et al. 2025: moisture-sensitive Sentinel-2 indices. Not used here; it needs a new export and has random-row splits.
- The 2026 Scientific Data soil-moisture product (doi:10.1038/s41597-026-06940-x) was **not evaluated within the one-day scope**: training period, latency and independence unchecked.

## 2. Data
- **ERA5-Land soil moisture** (`data/drought2/district_grid.csv.gz`):
  - 45 points: Kurnool 17, Anantapur 18, Tumkur 10;
  - Sep–Apr of seasons 1990-91 to 2022-23;
  - three layers combined into the root zone;
  - source requests and hashes in `data/drought2/sources.json`.
  - Sep–Apr only, to stay within the free API budget.
- **Rain and ET0:** existing corrected AgERA5 site cells (`data/prepared`), averaged per district. These are site cells, not district averages.
- **Crop outcomes:** Ministry of Agriculture district × season × crop area, production and yield (APY), 1997-98 to 2022-23, from the India Data Portal (`data/external/apy`, hash recorded).
  - Season "Rabi"; districts re-aggregated to pre-2022 boundaries.
  - These are reported statistics with revisions and reporting changes. **They are impacts, not drought labels.**
- **Boundaries:** geoBoundaries IND ADM2 (old district polygons).

## 3. Monitoring indicators (retrospective, completed season)
**Daily, per point:**
- percentile of the 7-day trailing root-zone mean;
- deficit / severe flags;
- missing values stay missing.

**Daily, per district:**
- deficit area = share of points in deficit;
- number of points available.

**Season, per district** (window 1 Nov – 28 Feb):
- DD, DDS, RUN;
- PCT (mean percentile);
- SOW (mean percentile 1 Oct – 30 Nov);
- coverage.

**Season-so-far versions** are used only in the forecast, with the input cutoff. A completed-season indicator is never presented as a warning.

## 4. Impact association (agricultural relevance)
**Outcomes**, per district-season:
- **yield index:** each crop's yield as a ratio to the median of its 5 previous seasons, minus 1 (causal);
- crops are those with ≥ 5 % of rabi area in 1997–2009, with fixed 1997–2009 area weights;
- **sown-area anomaly** (separate outcome), same causal baseline.

**Primary test:**
- within-district Spearman rank correlation, pooled over **Kurnool + Anantapur**;
- Tumkur is reported separately, because its rabi area is tiny and erratic;
- expected signs: DD/DDS/RUN negative; PCT/SOW/rain positive.

**Periods:**
- development 2000-01 to 2010-11, looked at while building;
- evaluation 2011-12 to 2022-23.

**Uncertainty:** 95 % interval by resampling whole seasons (both districts together).

**Comparison:** June–November and November–February rain ratios (rain-only baselines).

**Not claimed:**
- field-level validation;
- drought attribution for any site;
- independence between districts in the same season.

## 5. 15-day forecasting extension
- **Target:** mean district deficit area over (t, t+15] ≥ 0.5. This is a future-interval water deficit.
- **Issue dates:** every 5 days, 1 Dec – 31 Mar.
- **Inputs:** dated ≤ t − 8 days.
- **New-onset subset:** mean deficit area over the 15 input days < 0.5.
- **Splits** (whole seasons): train 1990–2006, validation 2007–2013, evaluation 2014–2022.
  - The percentile reference (1990–2004) lies inside training.
- **Baselines:** persistence, climatology (district × 15-day calendar bin), conditional transition (district × current-area bin).
- **Models:** logistic regression and XGBoost (5 seeds), each with soil-only, weather-only and combined inputs on identical rows.
- **Oracle:** an XGBoost with future rain, labelled not operational.
- **Thresholds:** maximum F1 on validation.
- **Selection:** best validation F1 among operational models.
- **Metrics:** precision, recall, F1, PR-AUC, ROC-AUC, Brier; new-onset subset; district-season events (caught, warned, warned with a correct warning).

## 6. Status words
- "Soil-moisture deficit" = reanalysis water shortage.
- "Crop stress" and "agricultural drought" are **not** asserted for points or sites without independent evidence.
- **Field validation is pending:** see `data/field_validation/FIELD_TEMPLATE_v2.csv`.

## Amendments
**A1 (23 Nov 2026, after the first site-cell forecast run had been displayed)**
- **Problem:** the validation seasons 2007-08 to 2013-14 contain **no** positive targets in the site-cell data, so thresholds and selection "on validation" were degenerate: every model warned on every row.
- **Change:** thresholds (max F1) and model selection (F1) now use **leave-one-season-out predictions within the training seasons 1990–2006**. Validation is still reported with its positive count.
- **Disclosure:** the degenerate run's evaluation table was seen before this change. The threshold-free evaluation scores (PR-AUC, ROC-AUC) are unaffected by it.

**A2 (23 Nov 2026)**
- **Problem:** the free Open-Meteo API limits (10,000 weighted calls per day, 5,000 per hour) delayed the 45-point district grid.
- **Added:** the same pipeline was run on the 5 existing ERA5-Land **site cells** (`data/drought_v1`), as a labelled site-cell analysis (`results/drought2_v1_sitecells`).
- **Primary analysis:** the district grid (`results/drought2_v1`), when complete.

**A3 (23 Nov 2026): paper analyses** (`src/drought2/paper.py`, `results/drought2_paper/`)
- **Added after the v2 results above had been seen.**
- **What was added:**
  - the association over all seasons 2000–22;
  - SPEI baselines;
  - an early-warning test of yield-loss seasons at 15 Dec / 15 Jan / 15 Feb.
- **Fixed before running:**
  - loss = multi-crop yield index ≤ −15 %;
  - inputs ≤ t − 8 days;
  - single indicators unfitted;
  - the 2-variable logistic model scored by leave-one-season-out.
- **Not chosen after seeing results:** no threshold or indicator.
- **Status:** exploratory case-study evidence on 2 districts.
