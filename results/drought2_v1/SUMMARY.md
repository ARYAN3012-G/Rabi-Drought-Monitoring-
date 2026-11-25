# Rabi drought v2: final summary (23 November 2026, branch `rabi-drought-v2`, not committed)

**Scope:**
- the 8 kharif study sites;
- district checks for Kurnool, Anantapur and Tumkur on pre-2022 boundaries;
- all rabi crops.

**Protocol and disclosed amendments:** `docs/DROUGHT2_v1.md`. Earlier rabi results (NDVI forecast, detect_v1/v2, drought_v1) are unchanged in their own directories.

## 1. Published method: extraction and adaptation
- **Padhee et al. 2017**, soil-moisture deficit duration in rabi. The full text was **not accessible** (HTTP 403).
- Our deficit and duration definitions are **adaptations, not a verified reproduction**. The table is in `docs/DROUGHT2_v1.md` §1.

## 2. Data audit and new datasets
| Dataset | Unit | Period | Note |
|---|---|---|---|
| ERA5-Land root-zone soil moisture, district grid (new) | 45 points at 0.3° in the district polygons | Sep–Apr 1990-91..2022-23 | Modelled reanalysis. No cropland mask. Free-API budget limited the months. Hashes in `data/drought2/sources.json` |
| ERA5-Land site cells (existing, drought_v1) | 5 cells | 1981–2026 | Labelled site-cell analysis |
| District crop statistics APY (new) | district × season × crop | 1997-98..2022-23 | Ministry of Agriculture via India Data Portal. Districts split in 2022 were re-aggregated. Hash in `data/drought2/apy_source.txt` |
| geoBoundaries IND ADM2 (new) | old district polygons | – | – |
| AgERA5 rain / ET0 (existing) | site cells averaged per district | 1979– | – |

**Major rabi crops (≥ 5 % of area, 1997–2009):**
- Kurnool and Anantapur: chickpea (gram), jowar, sunflower, groundnut, rice.
- Tumkur: horse-gram, groundnut, ragi, jowar, chickpea. Its rabi area is tiny and erratic, so it is reported separately and is not in the primary test.

## 3. Monitoring indicators (retrospective, completed season)
- **DD:** deficit duration, the share of days 1 Nov – 28 Feb at or below the 20th percentile.
- **DDS:** the same for severe deficit.
- **RUN:** the longest run of deficit days.
- **PCT:** the season's mean soil-moisture percentile.
- **SOW:** the mean soil-moisture percentile at sowing time.
- **Coverage** is reported for each.
- **File:** `data/drought2/season_indicators.csv`.

## 4. Independent-impact association (district rabi yield and sown area)
Within-district Spearman rank correlation, pooled over Kurnool + Anantapur, evaluation seasons 2011-12..2022-23 (24 district-seasons, 12 seasons). 95 % interval from resampling whole seasons.

| Indicator | vs multi-crop yield index | vs sown-area anomaly |
|---|---|---|
| **DD** (deficit duration) | **−0.62** [−0.89, −0.19] | **−0.59** [−0.80, −0.20] |
| DDS (severe) | −0.56 [−0.82, −0.08] | −0.56 [−0.79, −0.18] |
| SOW (moisture at sowing) | +0.73 [0.28, 0.93] | +0.57 [0.07, 0.88] |
| Rain Jun–Nov (baseline) | +0.59 [0.05, 0.84] | +0.51 [0.06, 0.81] |
| Rain Nov–Feb (baseline) | +0.06 | +0.02 |

- **Every soil indicator has the expected sign in every period.**
- Soil-moisture deficit duration relates to rabi crop outcomes **at least as strongly as** the best rain baseline.
- In-season rain alone is unrelated to the outcomes.
- **Site-cell analysis:** DD vs yield −0.50, SOW +0.76. The same direction, so it is robust to the soil sampling.
- Per-crop and per-district tables: `VALIDATION.md`.

**Limits:**
- Only 2 districts × 12 seasons; districts sharing a season are not independent.
- Yields have other causes and are reported statistics.
- Development seasons 2000–10 were inspected while building.
- **This is district association, not field validation.**

## 5. 15-day forecasting extension (district deficit in the next 15 days)
**Setup:**
- Evaluation seasons 2014-15..2022-23.
- Only **2 deficit seasons** (2016-17, 2018-19): 71 positive issue-date rows, 16 new onsets, 4 deficit district-seasons.
- Validation 2007–2013 had **no** positives, so thresholds come from leave-one-season-out within training (amendment A1).

| New onset (16 positives) | Recall | Precision | PR-AUC |
|---|---|---|---|
| Logistic regression, soil + weather (selected by the rules) | 0.63 | **0.91** | **0.90** |
| XGBoost, soil | **1.00** | 0.76 | 0.74 |
| Conditional transition (baseline) | 0.81 | 0.76 | 0.78 |
| Persistence | 0.00 | – | – |
| Climatology | 1.00 (warns always) | 0.03 | 0.03 |

- **District-season events:** the selected model, XGBoost (soil) and the transition baseline all catch 4 of 4. The selected model has no false district-seasons; the transition baseline has 1.
- **Models do not clearly beat the conditional-transition baseline.** The selected model trades recall for precision.
- **Weather-only inputs** are weaker than soil inputs.
- The **oracle** with future rain is labelled and excluded from selection.
- **Site-cell analysis:** 5 deficit district-seasons. Soil models recall 0.75–0.96 on new onsets, against 0.50 for the transition baseline.
- **No model improvement over the baseline is claimed** for the district grid.

## 6. Runnable module and tests
```
python -B -m src.drought2.run --date 2017-01-15            # historical replay
python -B -m src.drought2.run --date 2026-12-15 --update   # live: fetches ERA5-Land for the season so far
```
- **Outputs:** district status (monitoring and forecast kept separate), GeoJSON, report, manifest with hashes.
- Missing inputs give "unavailable"; it never outputs "healthy".
- **Rebuild:**
  ```
  python -B -m src.drought2.fetch_district
  python -B -m src.drought2.yields
  python -B -m src.drought2.indicators
  python -B -m src.drought2.validate
  python -B -m src.drought2.forecast
  ```
  For the site cells, set `DROUGHT2_DATA=data/drought2_sitecells`, `DROUGHT2_RESULTS=results/drought2_v1_sitecells` and `DROUGHT2_MODELS=models/drought2_v1_sitecells`.
- **Tests:** `tests/test_drought2.py` (leakage, target timing, season boundaries, missing data, causal yield baseline). The full suite: 39 pass.

## 7. What works, what fails, what is unverified
**Works:**
- A reproducible district soil-moisture deficit-duration indicator, for all rabi crops.
- Its season values relate to independent district rabi yield and sown-area losses in held-out seasons. This is the first evidence in this project that a rabi indicator relates to agricultural impact.

**Fails / weak:**
- The 15-day forecast does not clearly beat a simple conditional-transition baseline.
- The evaluation has only 2 deficit seasons.
- The validation period has none.

**Unverified:**
- Field-level drought.
- Attribution, i.e. that a deficit caused a given loss.
- Irrigated-crop water stress.
- The paper's exact method.
- Historical vegetation condition: the Earth Engine script `src/gee/script_D1_district_vci.js` has not been run.
- Real-time product availability beyond the 8-day assumption.

**Next:**
- Run script D1 to add vegetation condition.
- Obtain the Padhee 2017 PDF to check the adaptation.
- Collect field records with `data/field_validation/FIELD_TEMPLATE_v2.csv` in rabi 2026-27.
