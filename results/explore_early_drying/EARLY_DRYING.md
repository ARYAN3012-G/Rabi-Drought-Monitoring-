# Exploratory: early drying of rabi crops (terminal drought)

Added after the 2023-26 development check; not part of protocol v1; whole-season (retrospective) dates. Delta = field's drying date minus its own 2019-22 normal (leave-one-season-out), median per site x class (>= 5 fields). EARLY = median <= -14 days.

## Median shift of the drying date (days; negative = dries earlier than normal)

| site_code | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Som |  |  |  |  |  | irrigated: -1 d | irrigated: -4 d |
| Lep |  | irrigated: -27 d | irrigated: +28 d | irrigated: +21 d | irrigated: -15 d | irrigated: +4 d | irrigated: +5 d |
| Cho | irrigated: -15 d |  |  | irrigated: +10 d | irrigated: +27 d | irrigated: +11 d | irrigated: +34 d |
| Sira | irrigated: -9 d | irrigated: +5 d | irrigated: +1 d | irrigated: -3 d | irrigated: -29 d | irrigated: -8 d | irrigated: -30 d |
| Ped | irrigated: -19 d, rainfed: -26 d | irrigated: -12 d, rainfed: +5 d | irrigated: +32 d, rainfed: -0 d | irrigated: +10 d, rainfed: +10 d | irrigated: -46 d, rainfed: -23 d | irrigated: -12 d, rainfed: -11 d | irrigated: +0 d, rainfed: +12 d |
| Din | irrigated: -8 d | irrigated: +7 d | irrigated: +1 d | irrigated: +3 d | irrigated: -8 d | irrigated: -9 d | irrigated: -1 d |
| Bal | irrigated: -4 d, rainfed: -12 d | irrigated: +5 d, rainfed: +14 d | irrigated: -1 d, rainfed: -24 d | irrigated: +3 d, rainfed: +8 d | irrigated: -8 d, rainfed: -6 d | irrigated: -23 d, rainfed: -12 d | irrigated: +6 d, rainfed: +13 d |
| Pul | irrigated: +8 d, rainfed: -4 d | irrigated: +10 d, rainfed: +11 d | irrigated: +5 d, rainfed: -10 d | irrigated: -0 d, rainfed: +3 d | irrigated: -18 d, rainfed: +1 d | irrigated: -18 d, rainfed: -14 d | irrigated: +9 d, rainfed: +26 d |

## Sites with early drying

| season | sites EARLY |
|---|---|
| 2019 | Cho, Ped |
| 2020 | Lep |
| 2021 | Bal |
| 2022 | - |
| 2023 | Lep, Ped, Pul, Sira |
| 2024 | Bal, Pul |
| 2025 | Sira |

## Units

| season | site_code | cls | fields | median_delta_days | median_green_days | median_drying | early |
|---|---|---|---|---|---|---|---|
| 2019 | Bal | irrigated | 15 | -4.0 | 70.0 | 19 Mar | False |
| 2019 | Bal | rainfed | 10 | -11.5 | 70.0 | 23 Feb | False |
| 2019 | Cho | irrigated | 6 | -15.2 | 32.5 | 23 Feb | True |
| 2019 | Din | irrigated | 12 | -7.8 | 65.0 | 26 Mar | False |
| 2019 | Ped | irrigated | 9 | -19.0 | 40.0 | 02 Mar | True |
| 2019 | Ped | rainfed | 7 | -25.7 | 45.0 | 06 Feb | True |
| 2019 | Pul | irrigated | 13 | 8.5 | 55.0 | 24 Mar | False |
| 2019 | Pul | rainfed | 17 | -4.0 | 60.0 | 28 Feb | False |
| 2019 | Sira | irrigated | 8 | -8.7 | 65.0 | 30 Mar | False |
| 2020 | Bal | irrigated | 13 | 4.7 | 70.0 | 29 Mar | False |
| 2020 | Bal | rainfed | 11 | 14.5 | 70.0 | 09 Mar | False |
| 2020 | Din | irrigated | 11 | 7.0 | 70.0 | 03 Apr | False |
| 2020 | Lep | irrigated | 5 | -27.0 | 35.0 | 12 Feb | True |
| 2020 | Ped | irrigated | 14 | -11.5 | 75.0 | 12 Mar | False |
| 2020 | Ped | rainfed | 14 | 5.0 | 55.0 | 25 Feb | False |
| 2020 | Pul | irrigated | 11 | 9.7 | 75.0 | 29 Mar | False |
| 2020 | Pul | rainfed | 15 | 11.3 | 75.0 | 14 Mar | False |
| 2020 | Sira | irrigated | 7 | 5.0 | 73.0 | 01 Apr | False |
| 2021 | Bal | irrigated | 14 | -0.8 | 70.0 | 31 Mar | False |
| 2021 | Bal | rainfed | 12 | -23.7 | 45.0 | 12 Feb | True |
| 2021 | Din | irrigated | 9 | 1.3 | 65.0 | 29 Mar | False |
| 2021 | Lep | irrigated | 5 | 27.5 | 35.0 | 29 Mar | False |
| 2021 | Ped | irrigated | 11 | 32.5 | 70.0 | 06 Apr | False |
| 2021 | Ped | rainfed | 16 | -0.2 | 75.0 | 04 Mar | False |
| 2021 | Pul | irrigated | 11 | 4.7 | 70.0 | 14 Mar | False |
| 2021 | Pul | rainfed | 17 | -10.3 | 55.0 | 04 Mar | False |
| 2021 | Sira | irrigated | 7 | 1.0 | 62.0 | 16 Apr | False |
| 2022 | Bal | irrigated | 14 | 3.3 | 77.5 | 29 Mar | False |
| 2022 | Bal | rainfed | 11 | 7.5 | 65.0 | 27 Feb | False |
| 2022 | Cho | irrigated | 5 | 9.5 | 70.0 | 09 Mar | False |
| 2022 | Din | irrigated | 11 | 3.0 | 85.0 | 03 Apr | False |
| 2022 | Lep | irrigated | 6 | 20.8 | 47.5 | 16 Mar | False |
| 2022 | Ped | irrigated | 15 | 10.0 | 70.0 | 06 Apr | False |
| 2022 | Ped | rainfed | 15 | 9.7 | 70.0 | 25 Feb | False |
| 2022 | Pul | irrigated | 13 | -0.5 | 80.0 | 14 Mar | False |
| 2022 | Pul | rainfed | 18 | 3.0 | 77.5 | 09 Mar | False |
| 2022 | Sira | irrigated | 5 | -3.0 | 55.0 | 08 Apr | False |
| 2023 | Bal | irrigated | 16 | -7.6 | 65.0 | 18 Mar | False |
| 2023 | Bal | rainfed | 14 | -5.8 | 55.0 | 12 Feb | False |
| 2023 | Cho | irrigated | 10 | 26.9 | 60.0 | 28 Mar | False |
| 2023 | Din | irrigated | 13 | -7.5 | 65.0 | 18 Mar | False |
| 2023 | Lep | irrigated | 7 | -15.2 | 55.0 | 17 Feb | True |
| 2023 | Ped | irrigated | 11 | -45.5 | 70.0 | 31 Jan | True |
| 2023 | Ped | rainfed | 17 | -23.3 | 50.0 | 31 Jan | True |
| 2023 | Pul | irrigated | 15 | -17.5 | 55.0 | 03 Mar | True |
| 2023 | Pul | rainfed | 17 | 1.0 | 50.0 | 08 Mar | False |
| 2023 | Sira | irrigated | 9 | -29.0 | 62.0 | 03 Mar | True |
| 2024 | Bal | irrigated | 18 | -22.5 | 72.5 | 03 Mar | True |
| 2024 | Bal | rainfed | 15 | -12.5 | 60.0 | 16 Feb | False |
| 2024 | Cho | irrigated | 5 | 11.0 | 75.0 | 17 Apr | False |
| 2024 | Din | irrigated | 13 | -8.8 | 75.0 | 23 Mar | False |
| 2024 | Lep | irrigated | 5 | 3.7 | 65.0 | 28 Mar | False |
| 2024 | Ped | irrigated | 15 | -12.5 | 70.0 | 19 Feb | False |
| 2024 | Ped | rainfed | 15 | -11.0 | 65.0 | 14 Feb | False |
| 2024 | Pul | irrigated | 14 | -18.1 | 50.0 | 21 Feb | True |
| 2024 | Pul | rainfed | 17 | -14.3 | 50.0 | 11 Feb | True |
| 2024 | Sira | irrigated | 6 | -7.6 | 61.0 | 03 Apr | False |
| 2024 | Som | irrigated | 9 | -1.0 | 75.0 | 17 Apr | False |
| 2025 | Bal | irrigated | 16 | 5.5 | 80.0 | 04 Apr | False |
| 2025 | Bal | rainfed | 10 | 13.2 | 75.0 | 28 Mar | False |
| 2025 | Cho | irrigated | 7 | 33.5 | 55.0 | 02 Apr | False |
| 2025 | Din | irrigated | 14 | -1.4 | 73.5 | 02 Apr | False |
| 2025 | Lep | irrigated | 8 | 5.0 | 65.0 | 02 Apr | False |
| 2025 | Ped | irrigated | 11 | 0.3 | 60.0 | 16 Mar | False |
| 2025 | Ped | rainfed | 14 | 12.3 | 72.5 | 03 Mar | False |
| 2025 | Pul | irrigated | 13 | 8.7 | 60.0 | 13 Mar | False |
| 2025 | Pul | rainfed | 16 | 25.8 | 85.0 | 28 Mar | False |
| 2025 | Sira | irrigated | 9 | -29.7 | 63.0 | 16 Feb | True |
| 2025 | Som | irrigated | 5 | -3.5 | 70.0 | 09 Apr | False |
