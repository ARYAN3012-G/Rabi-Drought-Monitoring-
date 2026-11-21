# Protocol v1 - development check (retrospective, NOT a test)

## Summary (written after the check; detection rules were NOT changed afterwards)
- Scoring follows amendment A1 (Ped counts only when Adoni and Pedda Kadubur have the same status), so
  2023-24 Ped (Adoni Severe, Pedda Kadubur not declared) is 'Ambiguous' and not counted.
  Before A1 the 15 Feb result was severe 1/5 (that one hit was Adoni 2023-24).
- **15 Feb (primary):** severe mandal-seasons flagged **0/4**; not-declared flagged **5/10** (4 of them in 2025-26).
  15 Mar: 0/4 and 6/10. The rule does **not** reproduce the AP rabi declarations.
- **Kurnool 2023-24 and 2024-25 (declared Severe):** sowing and greenness of the rabi-crop fields were at or
  above normal (e.g. Bal rainfed 82-88 % established vs normal 78 %). As in the kharif project's audit, the
  2024-25 Kurnool declaration is not supported by rain or images.
- **2025-26 (declared only in Markapuram):** fewer fields sown at several sites (e.g. Ped irrigated 35 % vs 74 %
  normal, Som irrigated 25 % vs 47 %), consistent with almost no Dec-Feb rain in Kurnool (4-11 % of normal).
- Reading: on these seasons field-level rabi crop activity and the administrative rabi declarations disagree.
  Possible reasons: declarations use other criteria (Oct-Dec rainfall deficit, kharif carry-over, mandal-wide
  sown-area reports), our 3 km sites are small parts of a mandal, irrigated rabi fields are buffered by
  wells/tanks. Rabi 2026-27 is scored with the unchanged rules.


Rules: docs/PROTOCOL_v1.md (src/rabi/protocol.py), frozen before this check was run. Reference seasons 2019-22 are scored leave-one-season-out (no declarations: shown as the false-flag background). 2023-24 .. 2025-26 were known while designing the project.

## Issue 15 Jan (informational)

Reference seasons: 10 of 43 valid site-class units flagged (7 wet-delay).

| official | mandal_seasons | insufficient | flagged |
|---|---|---|---|
| Severe | 4 | 0 | 1/4 |
| Moderate | 0 | 0 | 0/0 |
| Not declared | 10 | 0 | 5/10 |

| season | mandal | official | order_date | issue | status | sites |
|---|---|---|---|---|---|---|
| 2023 | Adoni / Pedda Kadubur | Ambiguous | 2024-03-16 | 2024-01-15 | OK | Ped:OK |
| 2023 | Kurnool Rural | Severe | 2024-03-16 | 2024-01-15 | OK | Din:OK |
| 2023 | Kurnool Urban | Severe | 2024-03-16 | 2024-01-15 | FLAG | Bal:FLAG, Pul:FLAG |
| 2023 | Lepakshi | Not declared | 2024-03-16 | 2024-01-15 | OK | Cho:OK, Lep:OK |
| 2023 | Sira taluk | Unknown | 2024-03-16 | 2024-01-15 | OK | Sira:OK |
| 2023 | Somandepalli | Not declared | 2024-03-16 | 2024-01-15 | FLAG | Som:FLAG |
| 2024 | Adoni / Pedda Kadubur | Not declared | 2025-03-31 | 2025-01-15 | OK | Ped:OK |
| 2024 | Kurnool Rural | Severe | 2025-03-31 | 2025-01-15 | OK | Din:OK |
| 2024 | Kurnool Urban | Severe | 2025-03-31 | 2025-01-15 | OK | Bal:OK, Pul:OK |
| 2024 | Lepakshi | Not declared | 2025-03-31 | 2025-01-15 | OK | Cho:OK, Lep:OK |
| 2024 | Sira taluk | Unknown | 2025-03-31 | 2025-01-15 | FLAG | Sira:FLAG |
| 2024 | Somandepalli | Not declared | 2025-03-31 | 2025-01-15 | OK | Som:OK |
| 2025 | Adoni / Pedda Kadubur | Not declared | 2026-03-31 | 2026-01-15 | OK | Ped:OK |
| 2025 | Kurnool Rural | Not declared | 2026-03-31 | 2026-01-15 | FLAG | Din:FLAG |
| 2025 | Kurnool Urban | Not declared | 2026-03-31 | 2026-01-15 | FLAG | Bal:FLAG, Pul:FLAG |
| 2025 | Lepakshi | Not declared | 2026-03-31 | 2026-01-15 | FLAG | Cho:FLAG, Lep:OK |
| 2025 | Sira taluk | Unknown | 2026-03-31 | 2026-01-15 | OK | Sira:OK |
| 2025 | Somandepalli | Not declared | 2026-03-31 | 2026-01-15 | FLAG | Som:FLAG |

Units (site x class):

| season | site_code | cls | evaluable | established | share | normal_share | est_ratio | sep_nov_rain_ratio | cond_fields | cond_median | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2023 | Bal | irrigated | 20 | 10 | 0.5 | 0.48 | 1.05 | 0.83 | 8 | 0.82 | FLAG |
| 2023 | Bal | rainfed | 15 | 12 | 0.8 | 0.56 | 1.44 | 0.83 | 9 | 0.84 | FLAG |
| 2023 | Cho | irrigated | 14 | 4 | 0.29 | 0.15 | 1.9 | 0.59 | 2 |  | OK |
| 2023 | Din | irrigated | 19 | 6 | 0.32 | 0.34 | 0.94 | 0.64 | 3 |  | OK |
| 2023 | Lep | irrigated | 18 | 6 | 0.33 | 0.14 | 2.35 | 0.59 | 1 |  | OK |
| 2023 | Ped | irrigated | 20 | 10 | 0.5 | 0.28 | 1.8 | 0.68 | 6 | 1.13 | OK |
| 2023 | Ped | rainfed | 20 | 15 | 0.75 | 0.5 | 1.49 | 0.68 | 12 | 1.0 | OK |
| 2023 | Pul | irrigated | 19 | 9 | 0.47 | 0.45 | 1.05 | 0.83 | 6 | 0.86 | OK |
| 2023 | Pul | rainfed | 18 | 11 | 0.61 | 0.62 | 0.98 | 0.83 | 9 | 0.69 | FLAG |
| 2023 | Sira | irrigated | 20 | 4 | 0.2 | 0.16 | 1.23 | 0.68 | 0 |  | OK |
| 2023 | Som | irrigated | 18 | 1 | 0.06 | 0.09 | 0.61 | 0.52 | 0 |  | FLAG |
| 2024 | Bal | irrigated | 20 | 14 | 0.7 | 0.48 | 1.47 | 1.03 | 12 | 1.12 | OK |
| 2024 | Bal | rainfed | 17 | 15 | 0.88 | 0.56 | 1.59 | 1.03 | 11 | 1.11 | OK |
| 2024 | Cho | irrigated | 20 | 4 | 0.2 | 0.15 | 1.33 | 1.08 | 2 |  | OK |
| 2024 | Din | irrigated | 19 | 10 | 0.53 | 0.34 | 1.56 | 1.11 | 3 |  | OK |
| 2024 | Lep | irrigated | 20 | 3 | 0.15 | 0.14 | 1.06 | 1.08 | 1 |  | OK |
| 2024 | Ped | irrigated | 19 | 6 | 0.32 | 0.28 | 1.14 | 1.17 | 3 |  | OK |
| 2024 | Ped | rainfed | 20 | 11 | 0.55 | 0.5 | 1.09 | 1.17 | 8 | 1.05 | OK |
| 2024 | Pul | irrigated | 20 | 10 | 0.5 | 0.45 | 1.11 | 1.03 | 6 | 0.98 | OK |
| 2024 | Pul | rainfed | 20 | 12 | 0.6 | 0.62 | 0.96 | 1.03 | 11 | 1.03 | OK |
| 2024 | Sira | irrigated | 20 | 2 | 0.1 | 0.16 | 0.62 | 1.17 | 1 |  | FLAG |
| 2024 | Som | irrigated | 20 | 2 | 0.1 | 0.09 | 1.1 | 1.16 | 0 |  | OK |
| 2025 | Bal | irrigated | 20 | 5 | 0.25 | 0.48 | 0.53 | 1.4 | 5 | 0.82 | FLAG |
| 2025 | Bal | rainfed | 17 | 7 | 0.41 | 0.56 | 0.74 | 1.4 | 4 |  | FLAG |
| 2025 | Cho | irrigated | 20 | 2 | 0.1 | 0.15 | 0.67 | 0.68 | 0 |  | FLAG |
| 2025 | Din | irrigated | 20 | 2 | 0.1 | 0.34 | 0.3 | 1.29 | 1 |  | FLAG |
| 2025 | Lep | irrigated | 20 | 3 | 0.15 | 0.14 | 1.06 | 0.68 | 0 |  | OK |
| 2025 | Ped | irrigated | 17 | 6 | 0.35 | 0.28 | 1.27 | 1.02 | 3 |  | OK |
| 2025 | Ped | rainfed | 20 | 11 | 0.55 | 0.5 | 1.09 | 1.02 | 7 | 1.02 | OK |
| 2025 | Pul | irrigated | 20 | 4 | 0.2 | 0.45 | 0.44 | 1.4 | 3 |  | FLAG |
| 2025 | Pul | rainfed | 20 | 8 | 0.4 | 0.62 | 0.64 | 1.4 | 6 | 1.02 | FLAG |
| 2025 | Sira | irrigated | 20 | 4 | 0.2 | 0.16 | 1.23 | 0.75 | 0 |  | OK |
| 2025 | Som | irrigated | 20 | 0 | 0.0 | 0.09 | 0.0 | 0.73 | 0 |  | FLAG |

## Issue 15 Feb (PRIMARY)

Reference seasons: 2 of 44 valid site-class units flagged (4 wet-delay).

| official | mandal_seasons | insufficient | flagged |
|---|---|---|---|
| Severe | 4 | 0 | 0/4 |
| Moderate | 0 | 0 | 0/0 |
| Not declared | 10 | 0 | 5/10 |

| season | mandal | official | order_date | issue | status | sites |
|---|---|---|---|---|---|---|
| 2023 | Adoni / Pedda Kadubur | Ambiguous | 2024-03-16 | 2024-02-15 | FLAG | Ped:FLAG |
| 2023 | Kurnool Rural | Severe | 2024-03-16 | 2024-02-15 | OK | Din:OK |
| 2023 | Kurnool Urban | Severe | 2024-03-16 | 2024-02-15 | OK | Bal:OK, Pul:OK |
| 2023 | Lepakshi | Not declared | 2024-03-16 | 2024-02-15 | OK | Cho:OK, Lep:OK |
| 2023 | Sira taluk | Unknown | 2024-03-16 | 2024-02-15 | OK | Sira:OK |
| 2023 | Somandepalli | Not declared | 2024-03-16 | 2024-02-15 | FLAG | Som:FLAG |
| 2024 | Adoni / Pedda Kadubur | Not declared | 2025-03-31 | 2025-02-15 | OK | Ped:OK |
| 2024 | Kurnool Rural | Severe | 2025-03-31 | 2025-02-15 | OK | Din:OK |
| 2024 | Kurnool Urban | Severe | 2025-03-31 | 2025-02-15 | OK | Bal:OK, Pul:OK |
| 2024 | Lepakshi | Not declared | 2025-03-31 | 2025-02-15 | OK | Cho:OK, Lep:OK |
| 2024 | Sira taluk | Unknown | 2025-03-31 | 2025-02-15 | FLAG | Sira:FLAG |
| 2024 | Somandepalli | Not declared | 2025-03-31 | 2025-02-15 | OK | Som:OK |
| 2025 | Adoni / Pedda Kadubur | Not declared | 2026-03-31 | 2026-02-15 | FLAG | Ped:FLAG |
| 2025 | Kurnool Rural | Not declared | 2026-03-31 | 2026-02-15 | OK | Din:OK |
| 2025 | Kurnool Urban | Not declared | 2026-03-31 | 2026-02-15 | FLAG | Bal:FLAG, Pul:OK |
| 2025 | Lepakshi | Not declared | 2026-03-31 | 2026-02-15 | FLAG | Cho:FLAG, Lep:OK |
| 2025 | Sira taluk | Unknown | 2026-03-31 | 2026-02-15 | OK | Sira:OK |
| 2025 | Somandepalli | Not declared | 2026-03-31 | 2026-02-15 | FLAG | Som:FLAG |

Units (site x class):

| season | site_code | cls | evaluable | established | share | normal_share | est_ratio | sep_nov_rain_ratio | cond_fields | cond_median | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2023 | Bal | irrigated | 20 | 17 | 0.85 | 0.75 | 1.13 | 0.83 | 17 | 0.91 | OK |
| 2023 | Bal | rainfed | 17 | 14 | 0.82 | 0.78 | 1.06 | 0.83 | 14 | 0.97 | OK |
| 2023 | Cho | irrigated | 20 | 9 | 0.45 | 0.42 | 1.07 | 0.59 | 3 |  | OK |
| 2023 | Din | irrigated | 20 | 15 | 0.75 | 0.69 | 1.09 | 0.64 | 15 | 1.02 | OK |
| 2023 | Lep | irrigated | 20 | 11 | 0.55 | 0.34 | 1.6 | 0.59 | 5 | 0.94 | OK |
| 2023 | Ped | irrigated | 20 | 11 | 0.55 | 0.74 | 0.75 | 0.68 | 10 | 0.98 | FLAG |
| 2023 | Ped | rainfed | 20 | 15 | 0.75 | 0.71 | 1.05 | 0.68 | 15 | 0.93 | OK |
| 2023 | Pul | irrigated | 20 | 15 | 0.75 | 0.7 | 1.07 | 0.83 | 14 | 0.94 | OK |
| 2023 | Pul | rainfed | 20 | 17 | 0.85 | 0.89 | 0.96 | 0.83 | 17 | 1.06 | OK |
| 2023 | Sira | irrigated | 20 | 10 | 0.5 | 0.45 | 1.11 | 0.68 | 5 | 1.06 | OK |
| 2023 | Som | irrigated | 20 | 7 | 0.35 | 0.47 | 0.75 | 0.52 | 7 | 0.81 | FLAG |
| 2024 | Bal | irrigated | 20 | 18 | 0.9 | 0.75 | 1.2 | 1.03 | 18 | 1.05 | OK |
| 2024 | Bal | rainfed | 17 | 15 | 0.88 | 0.78 | 1.13 | 1.03 | 15 | 1.11 | OK |
| 2024 | Cho | irrigated | 20 | 10 | 0.5 | 0.42 | 1.19 | 1.08 | 5 | 1.1 | OK |
| 2024 | Din | irrigated | 20 | 15 | 0.75 | 0.69 | 1.09 | 1.11 | 13 | 1.01 | OK |
| 2024 | Lep | irrigated | 20 | 7 | 0.35 | 0.34 | 1.02 | 1.08 | 5 | 0.91 | OK |
| 2024 | Ped | irrigated | 20 | 14 | 0.7 | 0.74 | 0.95 | 1.17 | 13 | 1.1 | OK |
| 2024 | Ped | rainfed | 20 | 11 | 0.55 | 0.71 | 0.77 | 1.17 | 11 | 0.98 | OK |
| 2024 | Pul | irrigated | 20 | 12 | 0.6 | 0.7 | 0.86 | 1.03 | 11 | 1.01 | OK |
| 2024 | Pul | rainfed | 20 | 18 | 0.9 | 0.89 | 1.01 | 1.03 | 18 | 0.99 | OK |
| 2024 | Sira | irrigated | 20 | 4 | 0.2 | 0.45 | 0.44 | 1.17 | 3 |  | FLAG |
| 2024 | Som | irrigated | 20 | 14 | 0.7 | 0.47 | 1.5 | 1.16 | 11 | 1.05 | OK |
| 2025 | Bal | irrigated | 20 | 15 | 0.75 | 0.75 | 1.0 | 1.4 | 15 | 1.01 | OK |
| 2025 | Bal | rainfed | 17 | 9 | 0.53 | 0.78 | 0.68 | 1.4 | 9 | 1.01 | FLAG |
| 2025 | Cho | irrigated | 20 | 6 | 0.3 | 0.42 | 0.71 | 0.68 | 0 |  | FLAG |
| 2025 | Din | irrigated | 20 | 11 | 0.55 | 0.69 | 0.8 | 1.29 | 11 | 1.03 | OK |
| 2025 | Lep | irrigated | 20 | 9 | 0.45 | 0.34 | 1.31 | 0.68 | 6 | 1.03 | OK |
| 2025 | Ped | irrigated | 20 | 7 | 0.35 | 0.74 | 0.47 | 1.02 | 7 | 1.03 | FLAG |
| 2025 | Ped | rainfed | 20 | 14 | 0.7 | 0.71 | 0.98 | 1.02 | 13 | 0.98 | OK |
| 2025 | Pul | irrigated | 20 | 12 | 0.6 | 0.7 | 0.86 | 1.4 | 12 | 0.99 | OK |
| 2025 | Pul | rainfed | 20 | 15 | 0.75 | 0.89 | 0.85 | 1.4 | 15 | 1.1 | OK |
| 2025 | Sira | irrigated | 20 | 7 | 0.35 | 0.45 | 0.78 | 0.75 | 4 |  | OK |
| 2025 | Som | irrigated | 20 | 5 | 0.25 | 0.47 | 0.53 | 0.73 | 5 | 0.9 | FLAG |

## Issue 15 Mar (secondary)

Reference seasons: 2 of 44 valid site-class units flagged (1 wet-delay).

| official | mandal_seasons | insufficient | flagged |
|---|---|---|---|
| Severe | 4 | 0 | 0/4 |
| Moderate | 0 | 0 | 0/0 |
| Not declared | 10 | 0 | 6/10 |

| season | mandal | official | order_date | issue | status | sites |
|---|---|---|---|---|---|---|
| 2023 | Adoni / Pedda Kadubur | Ambiguous | 2024-03-16 | 2024-03-15 | FLAG | Ped:FLAG |
| 2023 | Kurnool Rural | Severe | 2024-03-16 | 2024-03-15 | OK | Din:OK |
| 2023 | Kurnool Urban | Severe | 2024-03-16 | 2024-03-15 | OK | Bal:OK, Pul:OK |
| 2023 | Lepakshi | Not declared | 2024-03-16 | 2024-03-15 | OK | Cho:OK, Lep:OK |
| 2023 | Sira taluk | Unknown | 2024-03-16 | 2024-03-15 | OK | Sira:OK |
| 2023 | Somandepalli | Not declared | 2024-03-16 | 2024-03-15 | FLAG | Som:FLAG |
| 2024 | Adoni / Pedda Kadubur | Not declared | 2025-03-31 | 2025-03-15 | OK | Ped:OK |
| 2024 | Kurnool Rural | Severe | 2025-03-31 | 2025-03-15 | OK | Din:OK |
| 2024 | Kurnool Urban | Severe | 2025-03-31 | 2025-03-15 | OK | Bal:OK, Pul:OK |
| 2024 | Lepakshi | Not declared | 2025-03-31 | 2025-03-15 | FLAG | Cho:OK, Lep:FLAG |
| 2024 | Sira taluk | Unknown | 2025-03-31 | 2025-03-15 | FLAG | Sira:FLAG |
| 2024 | Somandepalli | Not declared | 2025-03-31 | 2025-03-15 | OK | Som:OK |
| 2025 | Adoni / Pedda Kadubur | Not declared | 2026-03-31 | 2026-03-15 | FLAG | Ped:FLAG |
| 2025 | Kurnool Rural | Not declared | 2026-03-31 | 2026-03-15 | OK | Din:OK |
| 2025 | Kurnool Urban | Not declared | 2026-03-31 | 2026-03-15 | FLAG | Bal:FLAG, Pul:FLAG |
| 2025 | Lepakshi | Not declared | 2026-03-31 | 2026-03-15 | FLAG | Cho:FLAG, Lep:OK |
| 2025 | Sira taluk | Unknown | 2026-03-31 | 2026-03-15 | FLAG | Sira:FLAG |
| 2025 | Somandepalli | Not declared | 2026-03-31 | 2026-03-15 | FLAG | Som:FLAG |

Units (site x class):

| season | site_code | cls | evaluable | established | share | normal_share | est_ratio | sep_nov_rain_ratio | cond_fields | cond_median | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2023 | Bal | irrigated | 20 | 17 | 0.85 | 0.81 | 1.05 | 0.83 | 17 | 0.91 | OK |
| 2023 | Bal | rainfed | 17 | 14 | 0.82 | 0.79 | 1.04 | 0.83 | 14 | 0.92 | OK |
| 2023 | Cho | irrigated | 20 | 13 | 0.65 | 0.6 | 1.08 | 0.59 | 12 | 1.02 | OK |
| 2023 | Din | irrigated | 20 | 16 | 0.8 | 0.76 | 1.05 | 0.64 | 15 | 1.06 | OK |
| 2023 | Lep | irrigated | 20 | 13 | 0.65 | 0.54 | 1.2 | 0.59 | 10 | 0.96 | OK |
| 2023 | Ped | irrigated | 20 | 11 | 0.55 | 0.75 | 0.73 | 0.68 | 11 | 0.98 | FLAG |
| 2023 | Ped | rainfed | 20 | 15 | 0.75 | 0.71 | 1.05 | 0.68 | 15 | 0.97 | OK |
| 2023 | Pul | irrigated | 20 | 17 | 0.85 | 0.75 | 1.13 | 0.83 | 16 | 0.94 | OK |
| 2023 | Pul | rainfed | 20 | 17 | 0.85 | 0.86 | 0.99 | 0.83 | 17 | 0.99 | OK |
| 2023 | Sira | irrigated | 20 | 9 | 0.45 | 0.6 | 0.75 | 0.68 | 9 | 1.01 | OK |
| 2023 | Som | irrigated | 20 | 8 | 0.4 | 0.67 | 0.6 | 0.52 | 8 | 0.91 | FLAG |
| 2024 | Bal | irrigated | 20 | 19 | 0.95 | 0.81 | 1.17 | 1.03 | 19 | 1.03 | OK |
| 2024 | Bal | rainfed | 17 | 15 | 0.88 | 0.79 | 1.11 | 1.03 | 15 | 1.06 | OK |
| 2024 | Cho | irrigated | 20 | 12 | 0.6 | 0.6 | 0.99 | 1.08 | 11 | 1.03 | OK |
| 2024 | Din | irrigated | 20 | 16 | 0.8 | 0.76 | 1.05 | 1.11 | 15 | 1.02 | OK |
| 2024 | Lep | irrigated | 20 | 8 | 0.4 | 0.54 | 0.74 | 1.08 | 7 | 1.08 | FLAG |
| 2024 | Ped | irrigated | 20 | 15 | 0.75 | 0.75 | 1.0 | 1.17 | 15 | 1.06 | OK |
| 2024 | Ped | rainfed | 20 | 11 | 0.55 | 0.71 | 0.77 | 1.17 | 11 | 1.06 | OK |
| 2024 | Pul | irrigated | 20 | 12 | 0.6 | 0.75 | 0.8 | 1.03 | 11 | 0.94 | OK |
| 2024 | Pul | rainfed | 20 | 18 | 0.9 | 0.86 | 1.04 | 1.03 | 18 | 0.97 | OK |
| 2024 | Sira | irrigated | 20 | 7 | 0.35 | 0.6 | 0.58 | 1.17 | 7 | 0.95 | FLAG |
| 2024 | Som | irrigated | 20 | 14 | 0.7 | 0.67 | 1.04 | 1.16 | 14 | 1.05 | OK |
| 2025 | Bal | irrigated | 20 | 14 | 0.7 | 0.81 | 0.86 | 1.4 | 14 | 1.01 | OK |
| 2025 | Bal | rainfed | 17 | 10 | 0.59 | 0.79 | 0.74 | 1.4 | 10 | 1.04 | FLAG |
| 2025 | Cho | irrigated | 20 | 7 | 0.35 | 0.6 | 0.58 | 0.68 | 6 | 1.03 | FLAG |
| 2025 | Din | irrigated | 20 | 13 | 0.65 | 0.76 | 0.85 | 1.29 | 13 | 0.96 | OK |
| 2025 | Lep | irrigated | 20 | 12 | 0.6 | 0.54 | 1.11 | 0.68 | 9 | 0.92 | OK |
| 2025 | Ped | irrigated | 20 | 8 | 0.4 | 0.75 | 0.53 | 1.02 | 8 | 0.97 | FLAG |
| 2025 | Ped | rainfed | 20 | 14 | 0.7 | 0.71 | 0.98 | 1.02 | 13 | 1.01 | OK |
| 2025 | Pul | irrigated | 20 | 11 | 0.55 | 0.75 | 0.73 | 1.4 | 11 | 1.07 | FLAG |
| 2025 | Pul | rainfed | 20 | 15 | 0.75 | 0.86 | 0.87 | 1.4 | 14 | 1.06 | OK |
| 2025 | Sira | irrigated | 20 | 7 | 0.35 | 0.6 | 0.58 | 0.75 | 7 | 1.0 | FLAG |
| 2025 | Som | irrigated | 20 | 8 | 0.4 | 0.67 | 0.6 | 0.73 | 8 | 0.98 | FLAG |
