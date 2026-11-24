# DETECT_v5 Protocol — Physics-Guided Guardrails for False Alarm Suppression

**Registered:** 23 November 2026  
**Status:** Validated Research Increment  
**Lineage:** Builds upon `detect_v2` (baseline), `detect_v3` (phenology & thresholding), and `detect_v4` (soil moisture & crop priors).

---

## 1. Problem Statement
Diagnostic audits of `detect_v2`, `v3`, and `v4` demonstrated that over **80% of all false alarms** originated in irrigated cropland (`irr = 1`), specifically in the **Kurnool / Peddakadubur** black-cotton soil cluster. In these fields:
1. Farmers cultivate rabi crops (e.g., chickpea, sunflower) supported by deep residual moisture and localized irrigation.
2. At crop maturity (January–February), farmers harvest the crop.
3. Satellite optical greenness (NDVI) collapses abruptly post-harvest.
4. Purely optical or unconstrained models misclassify this harvest as an acute drought event.

---

## 2. Core Methodological Contributions

### A. The Physics-Guided Soil Moisture Gate (The "Soil Veto")
* **Physical Constraint:** Agronomic crop water stress requires genuine root-zone moisture deficit. When volumetric root-zone moisture is normal-to-wet ($\text{rootzone} \ge 0.30\text{ m}^3/\text{m}^3$), severe physiological moisture starvation is physically excluded.
* **Mechanism:** If the machine learning model triggers an alert, but root-zone moisture at issue time (accounting for the 8-day publication lag) is $\ge 0.30\text{ m}^3/\text{m}^3$, the alert is **vetoed**.
* **Impact:** Suppresses spurious alerts on harvested fields that retain high subsurface water.

### B. Multi-Temporal Persistence Confirmation (2-Consecutive Issue Filter)
* **Operational Principle:** Single-date optical anomalies frequently arise from cloud shadow fringe artifacts, momentary irrigation interruptions, or localized spot clearance.
* **Mechanism:** An operational alert requires two consecutive triggers ($T$ and $T+5\text{ d}$):
  * **Issue 1:** Drought Advisory / Watch
  * **Issue 2 (Consecutive):** Confirmed Drought Warning

### C. Five Feature Engineering Improvements (24 Nov 2026)
To address limitations identified in model review, five additional features were added to `engineer_features()`:

| # | Feature | Purpose |
|---|---|---|
| 1 | `spei_drought_flag` | SPEI < 0 co-confirmation (reduces satellite-only proxy dependence) |
| 2 | `soil_depth_divergence` | Surface (0–7 cm) minus root-zone moisture (within-cell variability proxy) |
| 3 | `inferred_crop_early` | 1 if prior_peak_doy < 80 (early-maturing crop proxy: groundnut/sorghum) |
| 4 | `inferred_crop_mid` | 1 if 80 ≤ prior_peak_doy ≤ 110 (mid-season crop: chickpea) |
| 5 | `inferred_crop_late` | 1 if prior_peak_doy > 110 (late-season crop: sunflower) |

Additionally, **irrigated field recall** was raised from 0.35 → 0.50 to recover previously missed genuine drought events, accepting a small increase in false alarm rate as the deliberate trade-off.

---

## 3. Results Overview (30-Day Lead Horizon)

| Lineage Version | Innovation | Warning Precision | False Alarm Rate | Total Warnings | Events Caught | Lead |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`detect_v2`** | Raw Optical NDVI Baseline | `31.3%` | `68.7%` | `332` | — | — |
| **`detect_v3`** | Decline Speed & F0.5 Thresholding | `38.6%` | `61.4%` | `207` | — | — |
| **`detect_v4`** | Soil Reanalysis + Crop Priors | `41.4%` | `58.6%` | `157` | — | — |
| **`detect_v5 [Soil Veto]`** (pre-24 Nov) | Physics-Guided Soil Gate | `72.2%` | `27.8%` | `54` | `39` | `18.0 d` |
| **`detect_v5 [Soil Veto]`** 🏆 (24 Nov) | **+ Crop proxies, SPEI flag, improved recall** | **`69.6%`** | **`30.4%`** | **`69`** | **`48`** | **`23.0 d`** |
| **`detect_v5 [Dual Confirm]`** | Soil Gate + 2-Issue Confirmation | `59.7%` | `40.3%` | `62` | — | — |

**Key trade-off (24 Nov update):** Raising irrigated recall (0.35→0.50) recovers +9 real drought events at 30 d horizon but costs +2.6% extra false alarms. The 23-day median lead (+5 days) is a practical gain for farmers needing time to arrange credit or irrigation.

### Kurnool-Specific Results (30-Day Horizon, Random Forest [v5_soil_veto])

| Cell | Warned | Hits | FA | Precision | FAR |
|------|--------|------|----|-----------|-----|
| Peddakadubur | 14 | 10 | 4 | 71.4% | 28.6% |
| kurnool_dinedevarapadu | 28 | 19 | 9 | 67.9% | 32.1% |
| **Kurnool total** | **42** | **29** | **13** | **69.0%** | **31.0%** |

---

## 4. Reproduction

```powershell
python -B src/detect/causal_events_v5.py
python -B src/detect/causal_events_v5.py --compare
```
