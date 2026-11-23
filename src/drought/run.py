"""Train/evaluate or issue regional root-zone drought predictions.

python -m src.drought.run train
python -m src.drought.run predict --date 2026-03-01
"""
from __future__ import annotations
import argparse
import hashlib
import json
import platform
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from . import model as M

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def md(d):
    def fmt(x):return '-' if pd.isna(x) else f'{x:.3f}' if isinstance(x,(float,np.floating)) else str(x)
    return '\n'.join(['| '+' | '.join(d.columns)+' |','|'+'|'.join(['---']*len(d.columns))+'|']+
        ['| '+' | '.join(map(fmt,r))+' |' for r in d.itertuples(index=False,name=None)])

def bootstrap(p):
    seasons=sorted(p.season.unique());by={s:p[p.season==s] for s in seasons};rng=np.random.default_rng(42);vals=[]
    for _ in range(1000):
        q=pd.concat([by[s] for s in rng.choice(seasons,size=len(seasons),replace=True)])
        a=(q.selected_warn&(q.target>0)).sum();b=q.selected_warn.sum();c=(q.target>0).sum()
        vals.append([a/b if b else np.nan,a/c if c else np.nan,
            ((q.selected_score-(q.target>0))**2).mean()-((q.persistence_score-(q.target>0))**2).mean()])
    vals=np.array(vals);out={}
    for i,k in enumerate(['precision','recall','brier_difference_vs_persistence']):
        v=vals[:,i];v=v[np.isfinite(v)]
        lo,hi=np.quantile(v,[.025,.975]) if len(v) else (None,None)
        out[k]=dict(low=lo,high=hi,valid_draws=len(v))
    return out

def train():
    for folder in [M.DATA,M.OUT,M.MODELS]:folder.mkdir(parents=True,exist_ok=True)
    soil,weather=M.load_inputs();refs=M.fit_reference(soil)
    joblib.dump(refs,M.MODELS/'reference.joblib',compress=3)
    print('Build historical issue-time dataset',flush=True)
    data,excluded=M.make_dataset(soil,refs,weather)
    data.to_csv(M.DATA/'instances.csv.gz',index=False);excluded.to_csv(M.DATA/'exclusions.csv',index=False)
    data.groupby(['split','season','horizon']).agg(rows=('target','size'),drought=('target',lambda x:(x>0).sum()),
        severe=('target',lambda x:(x==2).sum())).to_csv(M.OUT/'coverage.csv')
    configs=[];validation=[];models={}
    for h in M.HORIZONS:
        d=data[data.horizon==h];tr=d[d.split=='train'];va=d[d.split=='validation']
        fitted=[];scored=[]
        for candidate in M.candidates():
            print(f'{h} days: {candidate.name}',flush=True)
            candidate.fit(tr);fitted.append(candidate)
        fitted.append(M.Ensemble([c for c in fitted if getattr(c,'kind','')=='learned']))
        for c in fitted:
            p=c.predict_proba(va);thr=M.operating_threshold(c,va.target>0,p[:,1:].sum(axis=1))
            row=dict(horizon=h,model=c.name,threshold=thr,**M.metrics(va.target,p,thr))
            scored.append(row);validation.append(row)
        chosen=M.select(scored);models[h]={c.name:c for c in fitted}
        config=dict(horizon=h,model=chosen['model'],threshold=chosen['threshold'],
            validation_metrics=chosen,feature_schema=M.FEATURES,cells=sorted(refs),
            input_delay=M.DELAY,scope='regional_modelled_rootzone_soil_moisture_drought',
            class_names=M.CLASS_NAMES)
        bundle=dict(config=config,model=models[h][chosen['model']],reference=refs)
        joblib.dump(bundle,M.MODELS/f'forecast_{h}d.joblib',compress=3)
        configs.append(config)
    # Selection is persisted before any evaluation candidate is scored.
    (M.OUT/'selection_locked.json').write_text(json.dumps(configs,indent=2),encoding='utf-8')
    pd.DataFrame(validation).to_csv(M.OUT/'validation_metrics.csv',index=False)
    provenance=dict(protocol_sha256=sha(M.ROOT/'docs/DROUGHT_v1.md'),
        soil_sha256=sha(M.DATA/'soil_daily.csv.gz'),python=platform.python_version(),sklearn=sklearn.__version__,
        source_sha256={str(p.relative_to(M.ROOT)):sha(p) for p in [M.ROOT/'src/drought/model.py',M.ROOT/'src/drought/run.py']},
        weather_sha256={c:sha(M.ROOT/f'data/prepared/{c}.csv') for c in refs})
    (M.OUT/'provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    print('Selection locked. Evaluate fixed candidates on historical 2023-2025 seasons.',flush=True)
    results=[];predictions=[];cis=[]
    for config in configs:
        h=config['horizon'];te=data[(data.horizon==h)&(data.split=='evaluation')].copy()
        valrows={r['model']:r for r in validation if r['horizon']==h}
        selected_prob=None;persistence_prob=None
        for name,c in models[h].items():
            p=c.predict_proba(te);thr=valrows[name]['threshold']
            if name==config['model']:selected_prob=p
            if name=='Percentile persistence':persistence_prob=p
            base=dict(horizon=h,model=name,selected=name==config['model'],threshold=thr)
            for scope,mask in [('all',np.ones(len(te),dtype=bool)),('new_onset',te.issue_percentile.to_numpy()>20)]:
                if mask.any():results.append(dict(**base,group='pooled',scope=scope,**M.metrics(te.target.to_numpy()[mask],p[mask],thr)))
            for kind,key in [('season','season'),('cell','cell')]:
                for v in sorted(te[key].unique()):
                    mask=(te[key]==v).to_numpy()
                    results.append(dict(**base,group=f'{kind}:{v}',scope='all',**M.metrics(te.target.to_numpy()[mask],p[mask],thr)))
            q=te[['cell','season','issue_date','target_date','target_start','soil_date','weather_date','horizon','target','target_percentile','issue_percentile','soil_pct']].copy()
            q['model']=name;q['selected']=name==config['model'];q['threshold']=thr
            q[['p_no_deficit','p_moderate','p_severe']]=p;q['drought_score']=p[:,1:].sum(axis=1)
            q['warn']=q.drought_score>=thr;q['forecast_class']=p.argmax(axis=1)
            predictions.append(q)
        audit=te[['season','target']].copy();audit['selected_score']=selected_prob[:,1:].sum(axis=1)
        audit['selected_warn']=audit.selected_score>=config['threshold']
        audit['persistence_score']=persistence_prob[:,1:].sum(axis=1)
        cis.append(dict(horizon=h,seasons=len(M.TEST),intervals=bootstrap(audit)))
        loaded=joblib.load(M.MODELS/f'forecast_{h}d.joblib')
        if not np.allclose(loaded['model'].predict_proba(te),selected_prob,rtol=0,atol=1e-12):raise AssertionError('Saved model differs')
    scores=pd.DataFrame(results);scores.to_csv(M.OUT/'evaluation_metrics.csv',index=False)
    pd.concat(predictions).to_csv(M.OUT/'predictions.csv.gz',index=False)
    (M.OUT/'uncertainty.json').write_text(json.dumps(cis,indent=2),encoding='utf-8')
    report(scores,pd.DataFrame(validation),configs,cis,data)
    print('Completed, saved models and reports',flush=True)

def report(scores,val,configs,cis,data):
    cols=['horizon','model','n','drought_cases','macro_f1','drought_ap','drought_auc','brier','precision','recall','warnings']
    main=scores[(scores.group=='pooled')&(scores.scope=='all')&scores.selected]
    baselines=scores[(scores.group=='pooled')&(scores.scope=='all')&scores.model.isin(['Percentile persistence','Conditional transition','Soil analog k25'])]
    onset=scores[(scores.group=='pooled')&(scores.scope=='new_onset')&(scores.selected|scores.model.eq('Percentile persistence'))]
    warning=('**Evaluation limitation:** the 2023-2025 evaluation has no <=20th-percentile drought targets. '
        'Detection recall, drought AP and ROC-AUC are not estimable. These seasons only assess false alerts '
        'and scores under non-drought conditions. Neither no alerts nor high accuracy would prove drought-prediction skill. '
        'The threshold/reference are retained unchanged; no labels were altered to manufacture dry cases.'
        if main.drought_cases.sum()==0 else '')
    parts=['# Rabi regional soil-moisture drought prediction',
        'Development experiment, 23 November 2026. This predicts a future root-zone water-deficit indicator; it does not relabel satellite early drying as drought. It is a regional, modelled-soil target, not verified field crop loss or an official drought declaration.',
        warning,
        '## What is predicted',
        'For issues every five days during Dec-Mar, predict the class of seven-day mean root-zone water ending 7/15/30 days ahead. The entire target window is future. <=20th historical percentile is soil-moisture drought; <=10th is severe-or-worse deficit. Reference: 1981-2000 only, calendar-day +/-15 days. Above 20 is not a crop-health guarantee.',
        'Train: rabi 2001-02 through 2016-17. Validate: 2017-18 through 2022-23. Historical evaluation: 2023-24 through 2025-26. Both soil and weather inputs end eight days before issue. Model and threshold selection are validation-only and saved before evaluation. Final reanalysis may differ from original release vintages.',
        '## Selected results',md(main[cols]),
        'Precision/recall refer to repeated cell-issue forecasts, not independent drought episodes. Learned-score thresholds maximize validation F0.5 while retaining >=50% validation recall. Deterministic persistence/trend rules retain threshold 0.5. This favors fewer false warnings; evaluation recall is not constrained. Risk scores are not asserted calibrated.',
        '## Strong baselines on identical rows',md(baselines[cols]),
        '## New-onset subset',
        'Rows where the true issue-day soil indicator is not already dry. This issue-day truth is retrospective evaluation information only; the model still uses data dated issue-8 days. Many forecast positives in the full table are drought continuation, not new onset.',md(onset[cols]),
        '## Per-season selected results',md(scores[scores.selected&scores.group.str.startswith('season:')][['group']+cols]),
        '## Validation comparison (model selection)',md(val[['horizon','model','drought_ap','brier','precision','recall','threshold']]),
        '## All fixed candidates, historical evaluation',md(scores[(scores.group=='pooled')&(scores.scope=='all')][cols]),
        '## Coverage and limits',
        f'{data.cell.nunique()} soil/weather cells, not 1,350 independent soil locations. No field-level irrigation estimate; apply regional risk primarily to rainfed contexts. ERA5-Land and AgERA5 share atmospheric forcing, so the target is not independent field evidence. Thresholds describe relative rarity rather than crop-specific wilting or yield loss. Crop variety, rooting depth, sowing and irrigation can change impacts. No claims of perfectly detecting agricultural drought or universal best model.',
        'Evaluation seasons had been consulted in the broader project. New soil labels and this model comparison were specified before fitting, but this remains historical development evidence. Bootstrap intervals resample only three whole seasons, preserving cells jointly; their precision is limited.',
        '## Reproduction and inference',
        '`python -B src/drought/fetch_soil.py`\n\n`python -B -m src.drought.run train`\n\n`python -B -m src.drought.run predict --date 2026-03-01`',
        'Inference uses only the saved models/reference and issue-time inputs. Missing data abstain. Dates outside Dec-Mar abstain. Historical predictions are explicitly marked as replay. Current satellite observations can contextualize crop exposure but do not establish the cause of stress.',
        '## Additional historical stress check',
        'After discovering the lack of evaluation drought cases, a separate chronological backtest was specified: '
        'train 2001-2013, validate 2014-2016, evaluate 2017-2019. See `backtest/`. '
        'This is an explicitly post hoc development diagnostic, not a fresh untouched test. It does not change '
        'the main frozen reference, models, thresholds or labels.',
        '## Sources',
        '- [ERA5-Land data and latency via Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api)\n- [NOAA CPC percentile convention](https://www.cpc.ncep.noaa.gov/products/Drought/Monitoring/smp_body.shtml)\n- [NIDIS soil moisture and drought](https://www.drought.gov/what-is-drought/soil-moisture-and-drought)']
    (M.OUT/'DROUGHT_REPORT.md').write_text('\n\n'.join(x for x in parts if x)+'\n',encoding='utf-8')

def refresh_report():
    scores=pd.read_csv(M.OUT/'evaluation_metrics.csv')
    scores.loc[scores.drought_cases==0,['recall','f1']]=np.nan
    scores.loc[scores.warnings==0,'precision']=np.nan
    scores.to_csv(M.OUT/'evaluation_metrics.csv',index=False)
    val=pd.read_csv(M.OUT/'validation_metrics.csv')
    data=pd.read_csv(M.DATA/'instances.csv.gz')
    configs=json.loads((M.OUT/'selection_locked.json').read_text())
    predictions=pd.read_csv(M.OUT/'predictions.csv.gz');cis=[]
    for config in configs:
        h=config['horizon'];q=predictions[(predictions.horizon==h)&predictions.selected].copy()
        base=predictions[(predictions.horizon==h)&predictions.model.eq('Percentile persistence')]
        keys=['cell','issue_date','horizon']
        q=q.merge(base[keys+['drought_score']].rename(columns={'drought_score':'persistence_score'}),on=keys,validate='one_to_one')
        q=q.rename(columns={'drought_score':'selected_score','warn':'selected_warn'})
        cis.append(dict(horizon=h,seasons=3,intervals=bootstrap(q)))
    (M.OUT/'uncertainty.json').write_text(json.dumps(cis,indent=2),encoding='utf-8')
    report(scores,val,configs,cis,data)
    print('Regenerated reports; no models or thresholds changed')

def predict(date):
    issue=pd.Timestamp(date);out=M.OUT/'forecasts'/issue.strftime('%Y-%m-%d');out.mkdir(parents=True,exist_ok=True)
    allowed,reason=M.issue_allowed(issue)
    if not allowed:
        pd.DataFrame([dict(issue_date=issue,status=reason)]).to_csv(out/'regional_drought_risk.csv',index=False)
        print(f'Abstained: {reason}');return
    soil,weather=M.load_inputs();rows=[]
    for h in M.HORIZONS:
        b=joblib.load(M.MODELS/f'forecast_{h}d.joblib');cfg=b['config'];groups=M.prepare_soil(soil,b['reference'])
        for idx,cell in enumerate(cfg['cells']):
            needs_weather=bool(set(M.required_features(b['model']))&set(M.WX_FEATURES))
            f,reason=M.features_at(groups[cell],weather[cell],issue,h,idx,require_weather=needs_weather)
            row=dict(cell=cell,issue_date=issue,horizon=h,target_date=issue+pd.Timedelta(days=h),
                target_start=issue+pd.Timedelta(days=h-6),model=cfg['model'],status=reason,
                scope='regional modelled root-zone drought risk',input_cutoff=issue-pd.Timedelta(days=M.DELAY),
                validation_status='experimental; agricultural impact unvalidated',forecast_mode='as-of simulation using final reanalysis')
            if f is not None:
                d=pd.DataFrame([dict(**f,target_date=row['target_date'],horizon=h)])
                p=b['model'].predict_proba(d)[0];score=float(p[1:].sum())
                row.update(drought_risk_score=score,warning=score>=cfg['threshold'],threshold=cfg['threshold'],
                    forecast_class=M.CLASS_NAMES[int(np.argmax(p))],latest_soil_percentile=f['soil_pct'],
                    p_no_deficit=p[0],p_moderate=p[1],p_severe=p[2])
            rows.append(row)
    pd.DataFrame(rows).to_csv(out/'regional_drought_risk.csv',index=False)
    print(f'Saved {len(rows)} forecasts to {out}',flush=True)

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('train');sub.add_parser('reports-only');q=sub.add_parser('predict');q.add_argument('--date',required=True)
    args=p.parse_args()
    if args.command=='train':train()
    elif args.command=='reports-only':refresh_report()
    else:predict(args.date)

if __name__=='__main__':main()
