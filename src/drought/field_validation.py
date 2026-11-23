"""Record independent field assessments; never synthesize missing drought truth."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

COLUMNS=['observation_id','point_id','observation_date','crop','sowing_date','harvest_date',
    'irrigation_source','last_irrigation_date','soil_moisture_value','soil_moisture_unit',
    'measurement_depth_cm','drought_assessment','independent_of_model','assessment_method','evidence_notes']

def write_template(path):
    path=Path(path)
    if path.exists():raise FileExistsError(f'Observation file already exists: {path}')
    path.parent.mkdir(parents=True,exist_ok=True);pd.DataFrame(columns=COLUMNS).to_csv(path,index=False)
    return str(path)

def score_observations(points,observations):
    required={'observation_id','point_id','observation_date','drought_assessment','independent_of_model','assessment_method','evidence_notes'}
    if not required.issubset(observations):raise ValueError(f'Observations need {sorted(required)}')
    obs=observations.copy()
    if obs.observation_id.isna().any() or obs.observation_id.duplicated().any():raise ValueError('Unique observation IDs required')
    obs['observation_date']=pd.to_datetime(obs.observation_date,errors='raise')
    obs['drought_assessment']=obs.drought_assessment.fillna('unknown').astype(str).str.strip().str.lower()
    if not obs.drought_assessment.isin(['yes','no','unknown']).all():raise ValueError('Assessment must be yes, no or unknown')
    obs['independent_of_model']=obs.independent_of_model.fillna('unknown').astype(str).str.strip().str.lower()
    if not obs.independent_of_model.isin(['yes','no','unknown']).all():raise ValueError('Independent-of-model flag must be yes, no or unknown')
    assessed=obs.drought_assessment.isin(['yes','no'])
    for c in ['assessment_method','evidence_notes']:
        if obs.loc[assessed,c].fillna('').astype(str).str.strip().eq('').any():raise ValueError('Assessments need a method and supporting evidence notes')
    unknown=set(obs.point_id)-set(points.point_id)
    if unknown:raise ValueError(f'Unknown sampled point IDs: {sorted(unknown)[:4]}')
    candidates=points[points.status=='ok'].copy()
    for c in ['target_start','target_date','issue_date']:candidates[c]=pd.to_datetime(candidates[c])
    if candidates.duplicated(['point_id','horizon']).any():raise ValueError('Score one run at a time, with one point/horizon prediction')
    joined=candidates.merge(obs,on='point_id',how='inner')
    matches=joined[(joined.observation_date>=joined.target_start)&(joined.observation_date<=joined.target_date)]
    # Deterministic latest assessment, independent of agreement with the forecast.
    matches=matches.sort_values(['observation_date','observation_id'],kind='stable').drop_duplicates(['point_id','horizon'],keep='last')
    eligible=matches[matches.drought_assessment.isin(['yes','no'])&matches.independent_of_model.eq('yes')].copy()
    rows=[]
    for h in sorted(points.horizon.unique()):
        for irr,group in [(0,'rainfed_primary'),(1,'irrigated_context_only')]:
            q=eligible[(eligible.horizon==h)&eligible.irr.eq(irr)];positive=q.drought_assessment.eq('yes');warning=q.warning.eq(True)
            tp=int((positive&warning).sum());fp=int((~positive&warning).sum());fn=int((positive&~warning).sum());tn=int((~positive&~warning).sum())
            rows.append(dict(horizon=int(h),group=group,matched_assessments=len(q),positive_assessments=int(positive.sum()),
                tp=tp,fp=fp,fn=fn,tn=tn,precision=tp/(tp+fp) if tp+fp else np.nan,
                recall=tp/(tp+fn) if tp+fn else np.nan))
    return pd.DataFrame(rows),eligible

def validate(run_dir,observation_path):
    run_dir=Path(run_dir);points=pd.read_csv(run_dir/'sampled_point_context.csv')
    observations=pd.read_csv(observation_path)
    scores,matches=score_observations(points,observations)
    # New validation directory; never rewrite the original monitoring manifest.
    from datetime import datetime,timezone
    out=run_dir/'field_validation'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True,exist_ok=False)
    scores.to_csv(out/'scores.csv',index=False);matches.to_csv(out/'matched_observations.csv',index=False)
    text=('No assessable field observations matched the future target windows. Drought detection accuracy remains unknown.'
        if not len(matches) else f'{len(matches)} independent assessment records matched point/horizon windows. These observations may share soil cells and are not spatially independent trials.')
    (out/'VALIDATION.md').write_text('# Field observation comparison\n\n'+text+'\n\nOnly explicitly assessed yes/no outcomes with methods and evidence notes are scored. Unknowns and missing visits are never negatives. Regional soil forecasts and field crop assessments have different spatial support and endpoints; mismatches require investigation. No automatic model retraining is performed.\n',encoding='utf-8')
    from .live_data import sha
    (out/'provenance.json').write_text(json.dumps(dict(observations=str(Path(observation_path).resolve()),
        observations_sha256=sha(observation_path),run_manifest_sha256=sha(run_dir/'manifest.json')),indent=2),encoding='utf-8')
    return str(out)
