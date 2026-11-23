"""Audit saved drought artifacts and reproduce selected-model inference."""
import json
import hashlib
import joblib
import numpy as np
import pandas as pd
from . import model as M
from .run import sha

def main():
    d=pd.read_csv(M.DATA/'instances.csv.gz',float_precision='round_trip',parse_dates=['issue_date','target_date','target_start','soil_date','weather_date'])
    assert not d.duplicated(['cell','issue_date','horizon']).any()
    assert (d.target_start>d.issue_date).all()
    assert ((d.target_date-d.issue_date).dt.days==d.horizon).all()
    assert ((d.issue_date-d.soil_date).dt.days==8).all()
    assert (d.soil_date==d.weather_date).all()
    assert not set(d[d.split=='train'].season)&set(d[d.split=='evaluation'].season)
    validation=pd.read_csv(M.OUT/'validation_metrics.csv')
    configs=json.loads((M.OUT/'selection_locked.json').read_text())
    p=pd.read_csv(M.OUT/'predictions.csv.gz',float_precision='round_trip',parse_dates=['issue_date'])
    for cfg in configs:
        h=cfg['horizon'];vr=validation[validation.horizon==h].to_dict('records')
        assert M.select(vr)['model']==cfg['model']
        saved=joblib.load(M.MODELS/f'forecast_{h}d.joblib')
        test=d[(d.split=='evaluation')&(d.horizon==h)]
        probs=saved['model'].predict_proba(test)
        table=p[(p.horizon==h)&p.selected]
        assert list(zip(test.cell,test.issue_date))==list(zip(table.cell,table.issue_date))
        np.testing.assert_allclose(probs,table[['p_no_deficit','p_moderate','p_severe']].to_numpy(),rtol=0,atol=1e-12)
        # Label and outcome mutations cannot influence a loaded prediction.
        altered=test.copy();altered[['target','target_percentile','issue_percentile']]=999
        np.testing.assert_allclose(saved['model'].predict_proba(altered),probs,rtol=0,atol=1e-12)
    card=dict(status='experimental research candidate; not validated for field drought decisions',
        target='future seven-day mean modelled root-zone soil-moisture percentile',
        scale='ERA5-Land approximately 11 km, five requested cells',
        horizons=M.HORIZONS,selected_models={str(c['horizon']):c['model'] for c in configs},
        reference_years=[1981,2000],train_seasons=M.TRAIN,validation_seasons=M.VAL,evaluation_seasons=M.TEST,
        evaluation_drought_cases_per_horizon={str(h):int(((d.horizon==h)&(d.split=='evaluation')&(d.target>0)).sum()) for h in M.HORIZONS},
        operationally_validated=False,independent_agricultural_impact_labels_available=False,
        new_onset_advantage_over_strong_baseline_demonstrated=False,
        limitations=['No drought targets in the primary recent evaluation under the frozen ERA5 definition',
            'NASA MERRA-2 disagrees with some recent labels; both are model products, not field measurements',
            'Earlier chronological stress check is post hoc and concentrated in one drought season',
            'Final reanalysis is used, not an original-vintage operational archive',
            'Irrigation supply and crop-specific water requirements are not represented'])
    (M.OUT/'MODEL_CARD.json').write_text(json.dumps(card,indent=2),encoding='utf-8')
    files=list((M.ROOT/'src/drought').glob('*.py'))+[M.ROOT/'docs/DROUGHT_v1.md',M.ROOT/'tests/test_drought_prediction.py',
        M.OUT/'selection_locked.json',M.OUT/'predictions.csv.gz',M.DATA/'soil_daily.csv.gz']+list(M.MODELS.glob('*.joblib'))
    audit=dict(duplicate_forecast_keys=0,future_target_windows='passed',input_cutoffs='passed',
        validation_model_selection='passed',saved_model_reproduction='passed',outcome_mutation_invariance='passed',
        sha256={str(f.relative_to(M.ROOT)):sha(f) for f in files})
    (M.OUT/'audit_checks.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print('Saved-model reproduction, cutoff, target-window and selection audits passed.')

if __name__=='__main__':main()
