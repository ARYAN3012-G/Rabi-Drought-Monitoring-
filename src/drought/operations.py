"""One-command research monitoring, with immutable run artifacts and explicit abstention."""
from __future__ import annotations
from datetime import datetime,timezone,timedelta
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from . import model as M
from .live_data import cell_config,load_soil,sha,update_soil
from .satellite_io import POINTS,load_observations,context_at

OPS=M.ROOT/'results/operations'

def local_today():return datetime.now(timezone(timedelta(hours=5,minutes=30))).date()

def normalize_date(value):
    t=pd.Timestamp(value)
    if pd.isna(t) or t.tzinfo is not None or t!=t.normalize():raise ValueError('Use an unambiguous YYYY-MM-DD date without time or timezone')
    return t

def load_bundles():
    bundles={h:joblib.load(M.MODELS/f'forecast_{h}d.joblib') for h in M.HORIZONS}
    if len({joblib.hash(b['reference']) for b in bundles.values()})!=1:raise ValueError('Forecast horizons have different references')
    if any(b['config']['cells']!=list(cell_config().cell) for b in bundles.values()):
        raise ValueError('Model cells do not match runtime configuration')
    return bundles

def optional_weather(cells):
    weather={};paths=[]
    for cell in cells:
        path=M.ROOT/f'data/prepared/{cell}.csv'
        if path.exists():
            weather[cell]=pd.read_csv(path,parse_dates=['valid_time']).set_index('valid_time').asfreq('D');paths.append(path)
        else:weather[cell]=None
    return weather,paths

def source_status(soil,weather,obs,issue,bundles):
    cutoff=issue-pd.Timedelta(days=M.DELAY);rows=[]
    for cell in bundles[M.HORIZONS[0]]['config']['cells']:
        sg=soil[soil.cell==cell];past=sg[sg.date<=cutoff]
        w=weather.get(cell);need_weather=any(bool(set(M.required_features(b['model']))&set(M.WX_FEATURES)) for b in bundles.values())
        rows.append(dict(cell=cell,required_cutoff=cutoff,soil_available_through=sg.date.max(),
            soil_available_by_cutoff=past.date.max() if len(past) else pd.NaT,
            weather_available_through=w.index.max() if w is not None else pd.NaT,
            weather_required_by_selected_model=need_weather))
    return pd.DataFrame(rows)

def make_forecasts(issue,soil,weather,bundles,today=None):
    issue=normalize_date(issue);today=pd.Timestamp(today if today is not None else local_today())
    allowed,reason=M.issue_allowed(issue)
    if issue>today:allowed,reason=False,'future issue date: no forecast issued'
    cutoff=issue-pd.Timedelta(days=M.DELAY)
    reference=bundles[M.HORIZONS[0]]['reference']
    # Keep the original prefix for numerically identical rolling means; never expose later soil data.
    groups=M.prepare_soil(soil[soil.date<=cutoff],reference)
    rows=[];feature_rows=[]
    for h,b in bundles.items():
        cfg=b['config'];required=M.required_features(b['model']);needs_weather=bool(set(required)&set(M.WX_FEATURES))
        for idx,cell in enumerate(cfg['cells']):
            row=dict(cell=cell,issue_date=issue,horizon=h,target_start=issue+pd.Timedelta(days=h-6),
                target_date=issue+pd.Timedelta(days=h),model=cfg['model'],status=reason,input_cutoff=cutoff,
                weather_used=needs_weather,scope='regional root-zone soil-moisture drought risk',
                drought_risk_score=np.nan,warning=pd.NA,threshold=cfg['threshold'],
                forecast_class='unavailable',latest_soil_percentile=np.nan,p_no_deficit=np.nan,p_moderate=np.nan,p_severe=np.nan,
                forecast_mode='historical replay' if issue<today else 'dated research monitoring',
                validation_status='experimental; field agricultural impacts not validated')
            if allowed:
                group=groups.get(cell)
                if group is None:f,why=None,'missing soil cell'
                else:f,why=M.features_at(group,weather.get(cell),issue,h,idx,require_weather=needs_weather)
                row['status']=why
                if f is not None:
                    x=pd.DataFrame([dict(**f,horizon=h,target_date=row['target_date'])])
                    p=b['model'].predict_proba(x)[0]
                    if not np.isfinite(p).all() or not np.isclose(p.sum(),1):raise ValueError('Invalid model probabilities')
                    risk=float(p[1:].sum());row.update(drought_risk_score=risk,warning=bool(risk>=cfg['threshold']),
                        forecast_class=M.CLASS_NAMES[int(np.argmax(p))],latest_soil_percentile=f['soil_pct'],
                        p_no_deficit=p[0],p_moderate=p[1],p_severe=p[2])
                    feature_rows.append(dict(cell=cell,issue_date=issue,horizon=h,target_date=row['target_date'],**f))
            rows.append(row)
    return pd.DataFrame(rows),pd.DataFrame(feature_rows,columns=['cell','issue_date','horizon','target_date']+M.FEATURES),groups

def write_geojson(points,folder):
    features=[]
    for row in points[points.horizon==15].to_dict('records'):
        props={k:row.get(k) for k in ['point_id','mandal','irr','cell','status','drought_risk_score','warning',
            'vegetation_context','image_age_days','interpretation','field_drought_assessment']}
        props={k:(None if pd.isna(v) else v) for k,v in props.items()}
        features.append(dict(type='Feature',geometry=dict(type='Point',coordinates=[row['lon'],row['lat']]),properties=props))
    (folder/'sampled_points.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=features),allow_nan=False),encoding='utf-8')

def run(issue=None,update=False,today=None):
    today=pd.Timestamp(today if today is not None else local_today());issue=normalize_date(issue if issue is not None else today)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder=OPS/issue.strftime('%Y-%m-%d')/stamp;folder.mkdir(parents=True,exist_ok=False)
    manifest=dict(issue_date=issue.strftime('%Y-%m-%d'),created_utc=stamp,software_status='research monitoring workflow',
        research_status='agricultural drought accuracy not established',run_status='started',files={})
    updates=None
    if update:
        end=min(issue,today)-pd.Timedelta(days=M.DELAY)
        try:updates=update_soil(end)
        except (OSError,ValueError,RuntimeError) as e:
            updates=dict(status='update failed',reason=str(e));print(f'Update failed; assessing cached data: {e}',flush=True)
        # Network failures must not stop a readiness report or silently imply fresh data.
        except Exception as e:
            updates=dict(status='update failed',reason=f'{type(e).__name__}: {e}');print('Update failed; checking cache',flush=True)
    try:
        bundles=load_bundles();soil,soil_paths=load_soil();weather,weather_paths=optional_weather(cell_config().cell)
        regional,features,groups=make_forecasts(issue,soil,weather,bundles,today=today)
        if POINTS.exists():
            pts=pd.read_csv(POINTS)
            try:obs,satellite_paths=load_observations()
            except FileNotFoundError:
                obs=pd.DataFrame({'point_id':pd.Series(dtype=str),'date':pd.Series(dtype='datetime64[ns]'),'ndvi':pd.Series(dtype=float)})
                satellite_paths=[]
            points=context_at(regional,issue,pts,obs,cell_config())
        else:points=pd.DataFrame();obs=pd.DataFrame();satellite_paths=[]
        readiness=source_status(soil,weather,obs,issue,bundles)
        regional.to_csv(folder/'regional_drought_risk.csv',index=False)
        features.to_csv(folder/'features_used.csv',index=False)
        readiness.to_csv(folder/'source_status.csv',index=False)
        if len(points):
            points.to_csv(folder/'sampled_point_context.csv',index=False);write_geojson(points,folder)
            priorities=points[(points.status=='ok')&points.warning.eq(True)&points.irr.eq(0)]
            priorities.to_csv(folder/'inspection_candidates.csv',index=False)
        valid=int(regional.status.eq('ok').sum());warnings=int(regional.warning.eq(True).sum())
        coverage=int(points[points.horizon==15].vegetation_context.ne('unknown: no recent clear image').sum()) if len(points) else 0
        manifest.update(run_status='complete',forecast_status='issued' if valid==len(regional) else 'partial' if valid else 'abstained',
            forecasts_issued=valid,regional_warnings=warnings,points_with_recent_satellite_image=coverage,
            point_population=int(len(points)/len(M.HORIZONS)),update=updates,
            issue_date_is_future=bool(issue>today),models={},inputs={},outputs={})
        for h in M.HORIZONS:
            p=M.MODELS/f'forecast_{h}d.joblib';manifest['models'][str(h)]=dict(path=str(p.relative_to(M.ROOT)),sha256=sha(p))
        inputs=soil_paths+weather_paths+satellite_paths+[M.ROOT/'config/drought_cells.csv']+([POINTS] if POINTS.exists() else [])
        for path in inputs:manifest['inputs'][str(path)]=dict(sha256=sha(path))
        from .report import write_report
        write_report(folder,issue,regional,points,readiness,groups,manifest)
        for path in sorted(folder.iterdir()):
            if path.is_file():manifest['outputs'][path.name]=sha(path)
        manifest['source_hashes']={str(p.relative_to(M.ROOT)):sha(p) for p in (M.ROOT/'src/drought').glob('*.py')}
        (folder/'manifest.json').write_text(json.dumps(manifest,indent=2,default=str),encoding='utf-8')
        (OPS/'latest.json').write_text(json.dumps(dict(path=str(folder),issue_date=str(issue.date())),indent=2),encoding='utf-8')
        print(f'Completed: {valid}/{len(regional)} forecasts; {warnings} regional warnings; {coverage} points with recent images.\nReport: {folder / "report.html"}',flush=True)
        return folder
    except Exception as e:
        manifest.update(run_status='failed',error=f'{type(e).__name__}: {e}')
        (folder/'manifest.json').write_text(json.dumps(manifest,indent=2,default=str),encoding='utf-8')
        raise

def verify_run(folder):
    folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text())
    if manifest['run_status']!='complete':raise ValueError('Run did not complete')
    for name,digest in manifest['outputs'].items():
        if sha(folder/name)!=digest:raise ValueError(f'Output changed: {name}')
    for h,meta in manifest['models'].items():
        if sha(M.ROOT/meta['path'])!=meta['sha256']:raise ValueError(f'Model changed: {h}')
    if manifest['forecasts_issued']:
        features=pd.read_csv(folder/'features_used.csv',float_precision='round_trip')
        regional=pd.read_csv(folder/'regional_drought_risk.csv',float_precision='round_trip')
        for h,meta in manifest['models'].items():
            b=joblib.load(M.ROOT/meta['path']);x=features[features.horizon==int(h)]
            if not len(x):continue
            p=b['model'].predict_proba(x)
            recorded=regional[(regional.horizon==int(h))&regional.status.eq('ok')]
            if list(x.cell)!=list(recorded.cell):raise ValueError('Feature/prediction order mismatch')
            np.testing.assert_allclose(p,recorded[['p_no_deficit','p_moderate','p_severe']].to_numpy(),rtol=0,atol=1e-12)
    return dict(status='passed',outputs_verified=len(manifest['outputs']),predictions_reproduced=manifest['forecasts_issued'])
