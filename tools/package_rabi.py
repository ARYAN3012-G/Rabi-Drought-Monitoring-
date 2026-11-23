"""Build a portable research runtime; do not package credentials or parent weather data."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]

def latest_complete(day):
    for folder in sorted((ROOT/'results/operations'/day).iterdir(),reverse=True):
        m=folder/'manifest.json'
        if m.exists() and json.loads(m.read_text())['run_status']=='complete':return folder
    raise ValueError(f'No completed run for {day}')

def main():
    out=ROOT/'dist';out.mkdir(exist_ok=True)
    target=out/'rabi_research_module_2026-11-23.zip'
    files=set()
    def add(path):
        p=ROOT/path
        if p.is_dir():files.update(f for f in p.rglob('*') if f.is_file() and '__pycache__' not in f.parts)
        else:files.add(p)
    for p in ['rabi.py','requirements-drought.txt','requirements-drought-dev.txt','src/drought','config','models/drought_v1',
        'docs/RUN_RABI.md','docs/DROUGHT_v1.md','docs/COMPLETION_2026-11-23.md','src/gee/script_D_live_points.js',
        'tests/test_drought_prediction.py','tests/test_drought_operations.py',
        'data/gee_exports/C3_points.csv','data/gee_exports/C3_points_timeseries.csv',
        'data/drought_v1/soil_daily.csv.gz','data/drought_v1/instances.csv.gz','data/drought_v1/sources.json',
        'data/drought_live','observations/field_observations.csv','results/drought_v1',
        'tools/package_rabi.py']:
        add(p)
    runs=[latest_complete(d) for d in ['2026-03-01','2026-11-23']]
    for run in runs:add(run.relative_to(ROOT))
    readme='''# Rabi drought-risk research module

Extract this directory, open a terminal here, and use the project's Python
environment (or install requirements-drought.txt in an isolated environment).

    python -B rabi.py run --date 2026-03-01
    python -B rabi.py run --update

Open the report.html path printed by the command. The first command is a
historical example; the second uses today's India date. Dec-Mar monitoring,
eight-day soil delay and two-day image delay are enforced. Missing information
is unavailable, never a healthy label. The current release is a research risk
predictor, not field-validated agricultural drought diagnosis.

This runtime includes saved models, frozen soil/reference data, existing crop
observations, live soil updates, reports, tests and the manual Earth Engine
export/import path. It works without the parent weather repo because the
selected models use soil history only. Retraining every research experiment
still requires the full project, including the AgERA5 training files.

Read docs/RUN_RABI.md for outputs, independent field validation and limitations.
The latest soil data in this package end 15 November 2026; satellite observations
end April 2026. Run updates and import new satellite observations before live use.
The supplied field-observation template has no labels filled in.

No credentials are included. No commit, push, publication or automatic
notification was performed. Model weights and historical research results are
preserved; the new code completes the monitoring and verification workflow.
'''
    records={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    release=dict(created_utc=datetime.now(timezone.utc).isoformat(),scope='portable research monitoring runtime',
        code_tests_passed=31,field_accuracy_established=False,files=records)
    with ZipFile(target,'w',ZIP_DEFLATED) as z:
        for p in sorted(files):z.write(p,Path('rabi_module')/p.relative_to(ROOT))
        z.writestr('rabi_module/README.md',readme)
        z.writestr('rabi_module/RELEASE_MANIFEST.json',json.dumps(release,indent=2))
    with ZipFile(target) as z:
        if z.testzip() is not None:raise ValueError('Corrupt archive')
    print(f'{target}\n{target.stat().st_size:,} bytes; {len(files)} source/data/result files')

if __name__=='__main__':main()
