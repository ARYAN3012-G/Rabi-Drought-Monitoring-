# Rabi research module: implementation completion

Completed locally on 23 November 2026. No commit or push was made.

## Implemented and executed

- One entry point: `python rabi.py run --update`.
- Saved regional soil-moisture drought-risk models at 7, 15 and 30 days.
- Append-only live soil updates with overlap checks, continuity checks and a
  separate cache. Added 995 cell-days through 15 November 2026; the frozen
  research dataset hash is unchanged.
- Input requirements derived from the saved model. Soil-only predictions do
  not fail merely because unused AgERA5 data are stale or absent.
- Two-day satellite cutoff, 12-day image freshness, all sampled points retained
  in the context denominator, missing data explicitly unknown.
- Earth Engine script for the same 1,350 frozen point IDs, plus validated CSV
  import. The script passed JavaScript syntax checks; a remote authenticated
  export was not executed in this session.
- Self-contained HTML report, regional prediction CSV, sampled-point context,
  GeoJSON, inspection candidates and exact feature snapshots.
- Immutable per-run folders, model/data/output hashes, exact replay verification,
  current/retrospective/future/out-of-season distinctions and stale-input abstention.
- Independent field-observation template and scoring path, separate rainfed and
  irrigated context, no invented labels or automatic retraining.

## Verification

- All 31 repository tests pass.
- The 1 March 2026 replay issues 15 forecasts with 1,349/1,350 points having
  recent images; all 15 risk scores exactly equal the existing research outputs.
- The 23 November 2026 run correctly issues no out-of-season forecast and
  reports current imagery as unavailable.
- Saved-run verification reproduces predictions from the feature snapshot and
  verifies output/model hashes.
- The empty observation template yields no assessable cases and unknown
  accuracy, not false negatives or perfect scores.
- Model weights, thresholds, references and experimental labels were not changed.
- The portable ZIP was extracted to a separate directory with no parent weather
  data. It ran successfully and reproduced all 15 example scores exactly.

## Meaning of complete

The software workflow is complete and executable. Agricultural-drought accuracy
is still unestablished; the weak new-onset results and soil-product disagreement
remain documented. Future field observations and prospective monitoring provide
new evidence, not a software task that can be replaced with another training run.
Current satellite context requires the supplied Earth Engine export/import step.
