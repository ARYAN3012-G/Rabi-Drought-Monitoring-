# Run the rabi module

The software workflow is complete as a **research monitoring module**. It
forecasts regional root-zone soil-moisture drought risk at 7/15/30 days and
attaches available Sentinel-2 crop observations. It does not certify field
agricultural drought. The existing evaluation limitations remain in the report.

## One command

From the `rabi_module` directory:

```powershell
python -B rabi.py run --update
```

The issue date defaults to today's date in India. The command:

1. Appends available ERA5-Land soil observations through issue minus eight days.
2. Loads the saved, validation-selected models and frozen historical reference.
3. Issues 7/15/30-day regional risk forecasts if the date and inputs are valid.
4. Adds recent crop observations where available; missing imagery remains unknown.
5. Saves a report, CSV outputs, a GeoJSON map and a reproducibility manifest.

No retraining, Git commit, push, email, deployment or automatic drought
declaration occurs. Each run creates a new directory. The selected models and
the frozen research datasets are not changed by updates.

Open the path printed after `Report:`. `results/operations/latest.json` points
to the most recently completed run, which may be a historical replay.

## Reproduce the working example

```powershell
python -B rabi.py run --date 2026-03-01
```

This is a historical replay, not a live forecast. The verified example produces
15 regional forecasts and context for 1,350 sampled points at three horizons.
1,349 points have an image within the freshness requirement on this date.
Multiple points share a soil grid score; they are not 1,350 independent
drought predictions. A missing image is not an empty or healthy field.

## Output files

Under `results/operations/<issue-date>/<UTC-run-id>/`:

| File | Meaning |
|---|---|
| `report.html` | Local report: forecasts, soil trends, crop coverage, source dates and limitations |
| `regional_drought_risk.csv` | Five cells x three horizons, score, threshold, class, target window and availability |
| `sampled_point_context.csv` | Regional risk linked to sampled points and available crop imagery |
| `sampled_points.geojson` | 15-day regional context at the sampled point coordinates; usable in QGIS |
| `inspection_candidates.csv` | Rainfed sampled points under a regional warning, for checking rather than diagnosis |
| `features_used.csv` | Exact issue-time predictor values; contains no future outcomes |
| `source_status.csv` | Input cutoffs, coverage and whether weather is required |
| `manifest.json` | Model/input/output hashes and software/data provenance |

The binary warning and the argmax soil class answer different questions. A
warning uses the validation-chosen threshold on total deficit risk; the class
is the most likely of no percentile deficit, moderate deficit and severe-or-worse
deficit. Scores have not been validated as calibrated probabilities.

## Data freshness and calendar

- Monitoring: **1 December through 31 March**. End-of-window targets may reach April.
- Soil and any required weather: date <=issue-8 days, with complete lookback.
- Satellite: acquisition <=issue-2 days and no older than 12 days.
- The model was selected using outcomes through April 2023; earlier issues
  cannot be recreated with this final model and are rejected.
- Future issue dates are not issued in advance. Missing/stale model inputs
  produce an unavailable forecast, never a zero-risk substitute.
- All currently selected models use soil history. Weather availability is
  reported but is not required for those models. This is determined from the
  saved estimator's actual feature list, not from a manually chosen bypass.

On **23 November 2026**, the soil cache has been updated through **15 November**.
The day is outside the configured season, so the current report correctly has
no issued forecasts. On or after 1 December, the same command updates inputs
and issues predictions when the required dates are present.

## Refresh crop observations

The satellite export supplied to this project ends in April 2026, so current
crop context is unavailable. Regional soil predictions do not depend on it.

A ready-to-run Earth Engine script is at `src/gee/script_D_live_points.js`.
It embeds the **same 1,350 point IDs and coordinates** and copies C3's cloud mask,
15 m buffers, 10 m reduction and projection. It does not resample fields using
the season being evaluated. Set `START` and `END_EXCLUSIVE`, run it in the
authenticated Earth Engine Code Editor, and start its single CSV export.
The script was syntax-checked locally; the remote Earth Engine export has not
been executed in this session because no authenticated Earth Engine Python
session is configured.

Import the downloaded file:

```powershell
python -B rabi.py import-satellite C:\path\Rabi_live_points.csv
python -B rabi.py run --update
```

Imports check IDs, date validity, NDVI and clear-pixel counts. They keep the
best overlapping image, preserve the frozen observations, and refuse conflicting
revisions of previously imported observations. Historical research files remain
byte-identical. The live soil updater similarly checks overlap and continuity
before appending; a source revision stops the update for review.

## Verify a saved run

```powershell
python -B rabi.py verify "results/operations/2026-03-01/<run-id>"
```

This verifies saved output/model hashes and reproduces predictions from the
saved input features. It does not need the original mutable live input cache.

## Validate against independent crop observations

An empty template is provided at `observations/field_observations.csv`. Record
point ID, visit date, crop, sowing/harvest timing, irrigation, soil measurements,
an assessment (`yes`, `no`, `unknown`), its method and evidence. Mark
`independent_of_model=yes` only when the assessment was made independently of
the model score. Do not copy a satellite/model warning into the observed label.
This flag is an assessor declaration, not an automatic verification of evidence.

```powershell
python -B rabi.py validate --run-dir "results/operations/<date>/<run-id>" --observations observations/field_observations.csv
```

Only observations in the future seven-day target window are matched. The latest
assessment in the window is selected deterministically. Unknown/missing visits
are not negatives; no assessable visits means unknown accuracy. Rainfed and
irrigated-context results are separate. A new validation subdirectory is
written without altering the archived monitoring run. Regional soil forecasts
and field crop assessments have different endpoints and spatial support.

## Installation and checks

The saved models were produced with the versions in `requirements-drought.txt`.
Run with the existing Python environment, or install those versions into an
isolated environment. Optional weather context uses the parent weather repo's
`data/prepared` files; soil-only forecasts continue if those optional files are
absent. Soil reference files, saved models, configuration and point catalogue
must be retained with the repository.

For the optional tests in a fresh environment, install
`requirements-drought-dev.txt`; the runtime itself does not need pytest.

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -B -m pytest tests -q -p no:cacheprovider
python -B -m src.drought.audit
```

Research results: `results/drought_v1/DROUGHT_REPORT.md` and `MODEL_CARD.json`.
The earlier early-drying work is preserved under `results/detect_v2/` and is
not relabelled as verified agricultural drought.
