# Rabi drought monitoring (separate project, pilot)

A separate study for the rabi season (crops growing December - March) in the same 8 study areas as
the kharif weather -> satellite system. It does **not** reuse the kharif system's fields, rules or
models; it reuses only data tools (Sentinel-2 download and cleaning, AgERA5 weather, SPEI).

Why separate: the kharif system confirmed 0 of 4 severe rabi declarations on in-season images
(Sentinel2-Drought-Confirmation, results/replay). An audit of its fields showed few that are green in
January - March (results/rabi/RABI_AUDIT.md there). This project starts from fields that were
historically green in winter.

## Steps
1. **Script C1** (Earth Engine): historically winter-active *candidate* fields, chosen on the reference
   seasons 2019-20 .. 2022-23 only; rainfed and irrigated kept separate; selection reasons exported.
   **v1 audit (2026-11-21, results/audit/v1):** in v1, 58 % of rainfed candidate field-seasons were late
   kharif crops drying through the winter. **Script C1 v2** (`script_C1v2_rabi_candidates.js`) adds a RISE
   rule (Jan-Mar monthly peak minus Oct-Dec monthly trough >= 0.15), still on the reference seasons only.
2. **Script C2** (Earth Engine): Sentinel-2 series of the sampled candidates, Oct 2019 onwards.
3. **Candidate audit** (Python): October - April curves and images of a sample of candidates; lock the
   field list (frozen IDs).
4. **Protocol v1** (dated, in docs/): the two signals, thresholds, normals, missing-data handling,
   evaluation unit - fixed before rabi 2026-27 outcomes are known.
5. **Monitoring** December 2026 - March 2027; scoring against the AP rabi 2026-27 order.

Two signals (each with its own denominator):
- **Establishment / activity**: share of ALL candidate fields green by a given date vs normal
  (fields left empty in a drought year count - that is the signal).
- **Condition**: among fields with established vegetation, greenness vs each field's own normal.

Comparisons with the 2023-24 and 2024-25 declarations are retrospective development checks, not
independent tests. The registered R1/R2 test of the kharif project runs unchanged alongside.

"Candidate" = winter vegetation activity; crop type and sowing date are not verified.

## Status (21 Nov 2026)
- Fields frozen: `data/frozen/fields_v1.csv` (233 fields; asset `rabi_candidates_v2`). Audit: `results/audit/v1`, `v2`
  (the v2 part-1 "sampled" counts use the GeoJSON flag, which differs from the asset at Ped/Pul - see protocol).
- **Protocol v1** frozen: `docs/PROTOCOL_v1.md` (commit b266217), code `src/rabi/protocol.py`, tests `tests/`.
- Development check (retrospective): `results/dev_check/DEV_CHECK.md` - severe 0/4, not-declared 5/10 flagged
  at 15 Feb (scoring amendment A1 for Ped); the rule does not reproduce the 2023-26 declarations. Detection rules unchanged.

## Season calendar 2026-27 (all laptop work, no lab runs)
| When | Who | What |
|---|---|---|
| ~8 Dec 2026 | laptop | weather module: `python tools/update_agera5.py` then prepare_data (Sep-Nov rain for the wet guard) |
| 1 Jan, 15 Jan, 1 Feb, **15 Feb**, 1 Mar, **15 Mar** 2027 | Earth Engine (you) | rerun script C2 (VERSION 'v2'), download `C2_candidate_timeseries_v2.csv` |
| same days | laptop | `python src/rabi/monitor.py --date <day>` then commit `results/monitor/<day>/` the same day |
| after the AP rabi 2026-27 order (~end Mar 2027) | laptop | score 15 Feb (primary) and 15 Mar against the order; also score R1/R2 in the satellite repo |

    python src/rabi/freeze_fields.py      # (already done) frozen list
    python src/rabi/dev_check.py          # development check 2023-26
    python src/rabi/monitor.py --date 2027-02-15
    python -m pytest tests                # set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 on the laptop
