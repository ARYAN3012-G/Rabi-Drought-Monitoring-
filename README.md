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
