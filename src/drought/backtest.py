"""Post hoc chronological stress diagnostic; never replaces main selection."""
import json
import joblib
import numpy as np
import pandas as pd
from . import model as M
from .run import md,sha

def main():
    out=M.OUT/'backtest';out.mkdir(parents=True,exist_ok=True)
    data=pd.read_csv(M.DATA/'instances.csv.gz',parse_dates=['issue_date','target_date'])
    results=[];validation=[];configs=[];predictions=[]
    for h in M.HORIZONS:
        d=data[data.horizon==h];tr=d[d.season.between(2001,2013)];va=d[d.season.between(2014,2016)];te=d[d.season.between(2017,2019)]
        fitted=[];scores=[]
        for c in M.candidates():
            print(f'Backtest {h}d: {c.name}',flush=True);c.fit(tr);fitted.append(c)
        fitted.append(M.Ensemble([c for c in fitted if getattr(c,'kind','')=='learned']))
        for c in fitted:
            p=c.predict_proba(va);t=M.operating_threshold(c,va.target>0,p[:,1:].sum(axis=1))
            scores.append(dict(horizon=h,model=c.name,threshold=t,**M.metrics(va.target,p,t)))
        chosen=M.select(scores);configs.append(chosen);validation.extend(scores)
        (out/'selection_locked.json').write_text(json.dumps(configs,indent=2),encoding='utf-8')
        for c in fitted:
            p=c.predict_proba(te);thr=next(s['threshold'] for s in scores if s['model']==c.name)
            for scope,mask in [('all',np.ones(len(te),dtype=bool)),('new_onset',te.issue_percentile.to_numpy()>20)]:
                if mask.any():results.append(dict(horizon=h,model=c.name,selected=c.name==chosen['model'],scope=scope,
                    threshold=thr,**M.metrics(te.target.to_numpy()[mask],p[mask],thr)))
            if c.name==chosen['model']:
                joblib.dump(c,out/f'diagnostic_model_{h}d.joblib',compress=3)
                q=te[['cell','season','issue_date','target_date','horizon','target','issue_percentile']].copy()
                q['score']=p[:,1:].sum(axis=1);q['warn']=q.score>=thr;q['model']=c.name
                predictions.append(q)
    r=pd.DataFrame(results);r.to_csv(out/'metrics.csv',index=False)
    pd.DataFrame(validation).to_csv(out/'validation_metrics.csv',index=False)
    pd.concat(predictions).to_csv(out/'predictions.csv',index=False)
    cols=['horizon','model','scope','n','drought_cases','drought_ap','drought_auc','precision','recall','warnings']
    text=['# Earlier chronological drought stress check',
        '**Post hoc diagnostic:** chosen after viewing the seasonal prevalence table. This is historical development evidence, not a fresh test. Main production-candidate models are unchanged.',
        'Train 2001-2013; validate 2014-2016; evaluate 2017-2019. Same fixed 1981-2000 reference. Five regional cells. Only 2018 contains drought targets in this evaluation, so apparent sample size overstates independent drought events.',
        '## Selected models',md(r[r.selected][cols]),
        '## Baselines',md(r[r.model.isin(['Percentile persistence','Conditional transition','Soil analog k25'])][cols]),
        '## All candidates',md(r[cols]),
        'No ground-truth agricultural drought, irrigation, yield loss or farmer observations are available. These are forecasts of a modelled soil-moisture indicator. New-onset rows exclude actual drought at issue only for scoring; inference never uses that unknown issue-day value.']
    (out/'BACKTEST_REPORT.md').write_text('\n\n'.join(text)+'\n',encoding='utf-8')
    (out/'provenance.json').write_text(json.dumps({'protocol_sha256':sha(M.ROOT/'docs/DROUGHT_v1.md'),
        'script_sha256':sha(__file__),'main_selection_sha256':sha(M.OUT/'selection_locked.json')},indent=2))
    print('Backtest complete',flush=True)

if __name__=='__main__':main()
