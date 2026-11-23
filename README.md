# Rabi drought monitoring (separate project, pilot)

**Complete clone-and-run handoff:** [installation, included datasets, saved models
and research commands](docs/HANDOFF.md). All required historical weather inputs
are now bundled; no parent weather repository is needed.

## Run the completed research workflow

```powershell
python -B rabi.py run --update
```

This updates live soil data, runs the saved 7/15/30-day drought-risk models,
attaches available crop observations, and creates a local report, CSV/GeoJSON
outputs and an immutable run record. It does not retrain or alter frozen research
data. For a verified historical example: `python -B rabi.py run --date 2026-03-01`.

**[Start here: run guide, outputs and field-validation workflow](docs/RUN_RABI.md).**

Software status: complete research workflow. Scientific status: regional
soil-moisture risk, with agricultural-drought accuracy still unestablished.
No forecast is issued outside Dec-Mar or with missing required inputs. Current
satellite context needs a new Earth Engine export; the ready script and import
command are included. Soil-only regional forecasts do not require that export.

## New: regional soil-moisture drought prediction (23 Nov 2026)

The water-shortage prediction experiment is now implemented separately from
satellite early drying. It predicts 7/15/30-day **regional root-zone soil-moisture
deficit**, with frozen reference data, saved models and an as-of-date command.
See [execution summary](results/drought_v1/EXECUTION_SUMMARY.md),
[results](results/drought_v1/DROUGHT_REPORT.md) and
[development protocol](docs/DROUGHT_v1.md).

**Status: experimental, not a proven best agricultural-drought model.** The
fixed ERA5-Land definition yields no recent evaluation drought cases; NASA's
soil product disagrees on some cases. In the earlier chronological diagnostic,
a simple transition baseline outperformed the selected learned model on new
onsets. These findings and all candidate scores are retained, not hidden.

```powershell
python -B -m src.drought.run predict --date 2026-03-01
python -B -m src.drought.crop_context --date 2026-03-01
python -B -m src.drought.audit
```

The example is a historical replay. New-season use requires fresh soil and
corrected AgERA5 inputs. Outputs are regional risk plus satellite crop context;
they do not assert verified drought in individual sampled fields.

## Latest: Physics-guided false alarm suppression (`detect_v5`, 23 Nov 2026)

The project includes an operational early-drying event detection lineage (`v2` → `v3` → `v4` → `v5`):
- **`detect_v2` (Baseline):** Raw optical NDVI drops suffered from a **68.7% false alarm rate** (332 warnings, 31.3% precision).
- **`detect_v3` (Phenology & Tuning):** Added decline speed (`drop_rate`) and recall-constrained thresholding (61.4% false alarms, 207 warnings).
- **`detect_v4` (Soil Moisture & Crop Priors):** Added ERA5-Land rootzone moisture and reference phenological archetypes (58.6% false alarms, 157 warnings).
- **`detect_v5` (Physics-Guided Soil Gate):** Enforces an agronomic hard constraint (`rootzone < 0.30 m³/m³`). Vetoes false alarms on wet, harvested black-cotton soils, dropping the false alarm rate to **41.0%** and elevating warning precision to **59.0%** (83 warnings, 21-day median lead).

Run detect_v5 or compare the lineage:
```powershell
python -B rabi.py detect             # Run full detect_v5 training and evaluation
python -B rabi.py detect --compare   # Print v2 -> v3 -> v4 -> v5 comparative table
```

## Baseline reference: corrected early-drying event audit (`detect_v2`, 22 Nov 2026)

The latest reproducible classifier evaluation is
[`results/detect_v2/EVENT_REPORT.md`](results/detect_v2/EVENT_REPORT.md).
It forecasts **satellite-defined early drying**, a candidate drought-risk signal,
not field-verified agricultural drought. It preserves the separate frozen
15-day NDVI forecasting experiment.

Classifier v1 is superseded for operational claims: a completed-season status
had entered its predictors, its references included validation-season data,
and its first December issues used some unpublished rainfall. Version 2 fixes
those inputs, selects models/thresholds on validation, and saves every operating
point and prediction. Its stricter training reference changes the eligible
population; the two runs are not a same-cohort comparison.

Warnings are recounted **once per sampled point-season**, with event coverage,
false warnings and first timely lead shown together. The corrected 30-day,
validation-selected random forest catches 104 of 108 monitored events, but only
104 of 332 warned point-seasons have a timely match (31.3%). An always-warn
diagnostic catches 107 events while warning on 453 point-seasons. These numbers
are historical development evidence, not prospective drought-detection accuracy.

```powershell
python -B src/detect/causal_events.py
python -B src/detect/event_sanity.py
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -B -m pytest tests/test_detect_events.py -q -p no:cacheprovider
```

Rules and disclosure: [`docs/DETECT_v2.md`](docs/DETECT_v2.md). Saved event ledger:
`results/detect_v2/events.csv`; thresholds and validation model selection:
`results/detect_v2/operating_points.json`. Input/source hashes and independent
aggregation checks are saved alongside. Neither government orders nor the
UAV module are used to construct these labels.

The earlier pilot and candidate-field workflow is retained below for provenance.

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

## Revised rabi design (21 Nov 2026, in progress - not yet frozen)
Rabi crops use water stored before the season (Oct-Dec rain, soil, tanks, borewells), so the rabi module is built
around (1) water availability, (2) vegetation establishment over the WHOLE mandal's cropland (fixed denominator,
so empty land counts), (3) crop development (early decline, a candidate terminal-stress indicator) and
(4) validation (field evidence; government orders as an administrative comparison, not a tuning target).
Step 1 = `src/gee/script_C3_mandal_cropland.js` (data preparation, rabi 2019-20 .. 2025-26 only; 2026-27 not read).
R1/R2 (satellite repo) and protocol v1 stay unchanged. New rules are registered before rabi 2026-27 outcomes are seen.
