# Complete research handoff — 23 November 2026

Clone this repository normally. No sibling weather repository, Git LFS download,
private credentials or Earth Engine export is required for the included historical
example. Python 3.11 is recommended. Create a virtual environment, activate it,
then run from this repository's root:

```sh
python -m pip install -r requirements.txt
python -B -m pytest tests -q -p no:cacheprovider
python -B rabi.py run --date 2026-03-01
```

Open the printed `report.html`. The example uses saved models and included data;
it does not train models or download new observations. Current-season monitoring
is described in [RUN_RABI.md](RUN_RABI.md); fresh soil downloads require internet
and new satellite exports require your own Earth Engine access.

## What is included

- Earth Engine export scripts, downloaded C1/C2/C3 satellite data and metadata.
- Frozen populations, official comparison documents and derived research datasets.
- `data/prepared/`: exact corrected AgERA5 inputs used by the current research
  experiments, with SPEI calibrated on the historical training reference.
- `data/processed/weather/`: older weather inputs for reproducing the original
  protocol only. Do not substitute these for corrected inputs in new experiments.
- `data/WEATHER_INPUT_MANIFEST.json`: hashes and provenance for those 14 files.
- ERA5-Land historical soil data, separate live extension and cross-product inputs.
- Saved drought_v1 models and detect_v2 models, reference data, validation selections,
  predictions, metrics, negative results, superseded experiment reports and tests.
- Existing operation reports and an empty independent field-observation template.

The weather paths now resolve inside this repository, rather than the original
author's parent directory. Input bytes and saved model weights were preserved.
Existing historical provenance manifests are retained and may contain the original
absolute paths; new runs record paths for the clone where they execute.

## Research entry points

| Experiment | Build / run | Evidence |
|---|---|---|
| NDVI forecast | `python src/forecast/build_dataset.py`, then `python src/forecast/train_eval.py` | `results/forecast_v1_A1/` |
| Corrected early drying | `python src/detect/causal_events.py` | `results/detect_v2/` |
| Early-drying audit | `python src/detect/event_sanity.py` | Unique-event and always-warn comparisons |
| Regional soil drought | `python -m src.drought.run --help` | `results/drought_v1/` |
| Operational saved-model run | `python rabi.py run --date 2026-03-01` | A new immutable directory under `results/operations/` |

Training commands can overwrite derived research outputs. Work on a new branch
and preserve the supplied results before changing features, labels or splits.
The old `quick_v0_*` and detect_v1 code are retained as historical experiments,
not endorsed as leakage-free methods.

## Scientific status your improvements must preserve

1. NDVI forecasting is not validated agricultural-drought prediction.
2. Early drying is a satellite proxy, not independently confirmed drought.
3. The recent ERA5-Land soil evaluation has zero positive drought targets.
4. The earlier post hoc new-onset check favors the conditional-transition baseline.
5. No independent field-observation labels have been filled in.

The existing 2023–2026 seasons were examined during development; keep that
disclosure. Do not select a new model or label threshold on these seasons and
describe the same seasons as an untouched test.

Data provenance and original source attribution remain in the included source
manifests and reports. Dataset inclusion does not change the upstream providers'
terms. Local Python caches, virtual environments and duplicate distribution ZIPs
are intentionally excluded from Git.
