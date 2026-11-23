# Execution handover - 23 November 2026

Source baseline: detect_v1 at commit `062b3b8`. The original predictions are
retained. This work is local; no commit or push was made.

## What changed

1. Removed retrospective completed-season status from model inputs. Causal
   observed drying uses only the satellite prefix available at issue time.
2. Training reference is 2019-21 only, with the row's own season excluded and
   at least two observed reference drying dates. The stricter rule changes
   the eligible population; v1 and v2 are not same-cohort comparisons.
3. Every weather input respects eight-day publication latency, including
   antecedent June-November rainfall at the first December issue dates.
4. Target is a new early-drying event in (issue, issue+horizon], rather than
   cumulative post-event status. Full-season information is retained only
   for outcome evaluation and explicit retrospective risk-set assessment.
5. Thresholds, ensemble weights and primary model selection use validation.
   Saved validation predictions and operating points make decisions auditable.
6. Recounted unique point-season events, warning opportunity, first timely
   lead and warned-point-season precision. Added an always-warn diagnostic
   after the primary run without changing fitted models or thresholds.
7. Added eight causality/event-accounting tests and independently reproduced
   event counts directly from saved predictions. No duplicate forecast keys.
8. Updated the final report's rabi section, architecture and generated tables.

## Result scope

The validation-selected model is Random Forest at all three horizons. At 30
days it catches 104 of 108 monitored events and warns on 332 point-seasons:
31.3% of warned units contain a timely event. Median first timely lead is
27 days. An always-warn policy catches 107 events and warns on 453 units.
This comparison shows reduced warning burden, not reliable drought diagnosis.

The corrected reference admits 232 points in each validation/evaluation season;
only a subset has an eligible forecast. The three evaluation seasons contain
108 events within the monitoring window. These are sampled points and
satellite-defined drying events, not verified field-level drought cases.

The rainfall correlation is descriptive (rho -0.423 across 21 qualifying
cell-seasons). None of those groups has rain below 80% of normal, so the old
"twice as common" dry-versus-other comparison cannot be retained for this cohort.
The one lower-rain cell-season has only nine established eligible points and
fails the fixed minimum of ten. No cutoff was changed to recover that claim.

## Reproduction

From the rabi repository:

```powershell
python -B src/detect/causal_events.py
python -B src/detect/event_sanity.py
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -B -m pytest tests/test_detect_events.py -q -p no:cacheprovider
```

To regenerate narrative tables without training:

```powershell
python -B src/detect/causal_events.py --reports-only
python -B src/detect/event_sanity.py
```

From the parent weather workspace:

```powershell
python -B final_report_materials/update_rabi_events.py
```

Compile `final_report_materials/latex/main.tex` with Tectonic or upload the
updated Overleaf bundle. The original report source and facts sheet were
backed up with `.pre_detect_v2` in their filenames.

`provenance.json` preserves hashes recorded before model fitting;
`audit_checks.json` records final sources, saved predictions and corrected
weather inputs. Subsequent code edits only added report regeneration and
explicit handling of the unestimable rainfall contrast; fitted models and
prediction probabilities were not changed by those edits.
