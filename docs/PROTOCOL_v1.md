# Rabi monitoring protocol v1 (frozen)

**Fixed:** 21 November 2026, before rabi 2026-27 and before the development check on 2023-24 – 2025-26 was run. The git commit that adds this file dates it. The rules are implemented in `src/rabi/protocol.py`; none of the constants will be changed before rabi 2026-27 is scored. Any later change becomes protocol v2, with its reason, and is scored separately.

## 1. Question
Can satellite images of fields that **historically grow a rabi crop** show a rabi drought (fewer fields sown and/or poorer crops) **before** the Andhra Pradesh rabi drought order (usually 16–31 March)?

## 2. Monitored fields (frozen)
- `data/frozen/fields_v1.csv`: **233 fields**, SHA-256 `b86919d36372b7179539114fae4d56b7bbff1799e2be30a0834873647b9521e0`.
- These are the fields of the Earth Engine asset `rabi_candidates_v2`, written by script C1 v2:
  - farmland of the satellite module;
  - winter-active in at least 2 of 4 reference seasons (2019-20 – 2022-23);
  - a "dip then rise" curve (the January–March monthly peak is at least 0.15 above the October–December monthly low);
  - field-sized segments;
  - a random sample per site and class with seed 42.
- Rainfed / irrigated: the frozen summer-greenness rule of the satellite module.

| Site | Som | Lep | Cho | Sira | Ped | Din | Bal | Pul |
|---|---|---|---|---|---|---|---|---|
| irrigated | 20 | 20 | 20 | 20 | 20 | 20 | 20 | 20 |
| rainfed | 3 | 3 | 0 | 4 | 20 | 6 | 17 | 20 |

- Every frozen field is followed in every season, including when it stays empty: an empty field in a dry year is the signal.
- "Candidate" means a field with historic winter vegetation activity. Crop type and sowing date are not verified.
- The GeoJSON `sampled` flag differs from the asset at Ped and Pul (the export tasks ordered the segments differently before the seeded draw). The asset, which script C2 follows, is authoritative.

## 3. Data
- Sentinel-2 (script C2), cleaned in the same way as the satellite module:
  - an image is kept for a field if at least 60 % of the field is clear (100 % = the field's clearest image up to 30 Apr 2023);
  - NDVI must be in the range −0.2 to 1;
  - one image per field per day (the clearest).
- **No look-ahead:** on issue date D, only images dated on or before D − 2 days are used.
- The weather module's AgERA5 files are used for the wet guard only.

## 4. Rules
Season y runs from 1 October y to 30 April y+1.

**Per field, at issue date D**
- Monthly median NDVI for October to April. The current month uses the images available so far.
- Trough T = the lowest monthly median of October, November and December.
- Green-up G = the highest monthly median of the months after T's month.
- **Evaluable:** at least 2 of the October–December months are observed, at least 1 month after T is observed, and there are at least `max(3, days from 1 Dec to D ÷ 14)` clear images since 1 December (15 Jan: 3; 15 Feb: 5; 15 Mar: 7).
- **Established:** G − T ≥ 0.15 and G > 0.35.

**Per unit (site × class)**
- A unit needs at least **10 evaluable fields**. Otherwise it is INSUFFICIENT.
- **Signal 1, establishment:**
  - share = established ÷ evaluable;
  - normal = the mean share in the reference seasons 2019–2022 on the same day of the season (reference seasons are compared with the other three only; at least 2 seasons with 10 or more evaluable fields);
  - **flag if share < 0.75 × normal.**
- **Wet guard:** if September–November rain at the site's AgERA5 cell is more than **150 %** of its 1979–2011 mean, an establishment flag is reported as **WET-DELAY** (late or no sowing after excess rain) and does not count as drought.
  - This was added after the reference seasons showed it: in 2021-22, September–November rain was 181–192 % of normal at the south sites, and sowing there was delayed.
- **Signal 2, condition:**
  - for each established field, ratio = G ÷ the field's mean G in the reference seasons in which it was established on the same day (at least 2 such seasons);
  - **flag if the median ratio over at least 5 fields is below 0.85.**
- **Unit FLAG** = signal 1 (not wet-guarded) or signal 2 flags.

**Per site and mandal**
- **Site:**
  - FLAG if any valid unit flags;
  - OK if at least one unit is valid and none flags;
  - INSUFFICIENT otherwise.
- **Mandal:** FLAG if any of its sites flags.

| Site | Mandal |
|---|---|
| Som | Somandepalli |
| Lep, Cho | Lepakshi |
| Sira | Sira taluk |
| Ped | Adoni / Pedda Kadubur (amendment A1) |
| Din | Kurnool Rural |
| Bal, Pul | Kurnool Urban |

Ped's pin lies on the Adoni side of the Adoni / Pedda Kadubur border, but most of its fields lie in Pedda Kadubur (amendment A1).

## 5. Issue dates and scoring

| Issue date | Role |
|---|---|
| **15 February** | **PRIMARY** (scored) |
| 15 March | secondary (scored) |
| 15 January | informational only. The reference seasons showed it is too early: 10 of 43 units were flagged without a drought. |

- **Outcome:** the official AP rabi 2026-27 drought order (Severe / Moderate / Not declared) for each mandal.
  - Sira (Karnataka) is scored only if a Karnataka rabi declaration naming Sira is found.
- **Reported:**
  - severe flagged x/n, moderate flagged x/n, not-declared flagged x/n;
  - INSUFFICIENT mandals listed and not counted;
  - whether the flag came before the order date.
- Live reports are produced with `python src/rabi/monitor.py --date <date>` and committed on the day.

## 6. What the result can and cannot show
- **Coverage:** rainfed monitoring is possible only at Ped, Bal and Pul, since the other sites have fewer than 10 rainfed rabi fields. That is a finding: there is little rainfed rabi cropping around Somandepalle, Lepakshi and Sira. Irrigated units cover all 8 sites.
- **Small sample:** one season and about 5 scorable mandals give case evidence, not a statistical test.
- **Declarations** are administrative decisions, not field truth. The site-to-mandal assignment uses the site centre.
- **The development check** on 2023-24 – 2025-26 (`results/dev_check/DEV_CHECK.md`) describes the rule. Those seasons were known while the project was designed, so it is **not** evidence that the rule works.
- **Reference false-flag background** (2019–2022, leave-one-season-out, with the wet guard): 2 of 44 units flagged at 15 Feb, 2 of 44 at 15 Mar.
- **Independence:** the registered R1/R2 test of the kharif project (`Sentinel2-Drought-Confirmation/docs/PREREGISTRATION_rabi_2026-27.md`) runs unchanged and is scored separately.

## Amendment A1 (21 November 2026, before rabi 2026-27; scoring only)
A boundary check against official sub-district polygons (geoBoundaries IND ADM3, lgdirectory.gov.in 2018;
`Sentinel2-Drought-Confirmation/results/qc/MANDAL_CHECK.md`) found that Ped's centre lies in Adoni but 25 of its
40 rabi fields lie in **Pedda Kadubur** (15 in Adoni). Ped is therefore scored only when Adoni and Pedda Kadubur
have the **same** official status; otherwise it is reported as "Ambiguous" and not counted (as in the kharif
replay). Detection rules, fields and thresholds are unchanged. The amendment lowers the development-check result
(severe 1/5 → 0/4), so it is not chosen to improve it.
Other findings of the check (no change): Lep 16 of 23 rabi fields in Lepakshi, 7 in Chilamathur; Sira 15 of 24
in Sira, 9 in Agali (Andhra Pradesh); Som, Cho all inside their mandal; Din, Bal, Pul all inside the pre-2022
Kurnool mandal (the 2018 polygons cannot separate Kurnool Urban from Kurnool Rural).
