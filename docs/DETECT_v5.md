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

---

## 3. Results Overview (30-Day Lead Horizon)

| Lineage Version | Innovation | Warning Precision | False Alarm Rate | Total Warnings |
| :--- | :--- | :---: | :---: | :---: |
| **`detect_v2`** | Raw Optical NDVI Baseline | `31.3%` | `68.7%` | `332` |
| **`detect_v3`** | Decline Speed & F0.5 Thresholding | `38.6%` | `61.4%` | `207` |
| **`detect_v4`** | Soil Reanalysis + Crop Priors | `41.4%` | `58.6%` | `157` |
| **`detect_v5 [Soil Veto]`** 🏆 | **Physics-Guided Soil Gate** | **`59.0%`** | **`41.0%`** | **`83`** |
| **`detect_v5 [Dual Confirm]`** | **Soil Gate + 2-Issue Confirmation** | **`59.7%`** | **`40.3%`** | **`62`** |

---

## 4. Reproduction

```powershell
python -B src/detect/causal_events_v5.py
python -B src/detect/causal_events_v5.py --compare
```
