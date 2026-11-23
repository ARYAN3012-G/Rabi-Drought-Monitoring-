"""Detect v2: causal features, saved operating points and unique-event evaluation.

Run: python -B src/detect/causal_events.py
No v1 artifacts are overwritten. See docs/DETECT_v2.md for the development protocol.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, balanced_accuracy_score,
                             f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[2]
DATA, OUT = ROOT / 'data/detect_v2', ROOT / 'results/detect_v2'
TRAIN, VAL, TEST = [2019, 2020, 2021], [2022], [2023, 2024, 2025]
HORIZONS, SEEDS = [7, 15, 30], list(range(5))
FEATURES = ['irr', 'doy', 'ndvi', 'age', 'peak', 'trough', 'days_since_peak', 'drop',
            'drop_share', 'chg15', 'chg30', 'anom', 'normal_dry', 'days_to_normal_dry',
            'observed_dry', 'rain_jun_available_ratio', 'rain_since_oct', 'rain60',
            'et0_30', 'tmax_30', 'spei']
BASE_MODELS = ['Logistic regression', 'Random forest', 'XGBoost']


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def average(a, axis=None):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        return np.nanmean(a, axis=axis)


def reference_stats(phenology, point, own_season):
    q = phenology[(phenology.point_id == point) & phenology.season.isin(TRAIN)
                  & (phenology.season != own_season) & phenology.quality_ok
                  & phenology.est & phenology.dry_doy.notna()]
    return len(q), float(q.dry_doy.median()) if len(q) else np.nan


def issue_dates(season):
    return pd.date_range(f'{season}-12-01', f'{season + 1}-03-31', freq='5D')


def past_features(obs, season, issue, normal_dry, normal_curve):
    """Accept observations only; never accept retrospective outcome/status columns."""
    issue = pd.Timestamp(issue)
    cut = issue - pd.Timedelta(days=2)
    g = obs[(obs.date <= cut) & (obs.date >= pd.Timestamp(season, 10, 1))].sort_values('date')
    if g.empty or (issue - g.date.iloc[-1]).days > 12:
        return None, 'no recent observation'
    v = g.ndvi.rolling(3, min_periods=1).median().to_numpy()
    d = (g.date - pd.Timestamp(season, 10, 1)).dt.days.to_numpy()
    dt, ld = (issue - pd.Timestamp(season, 10, 1)).days, int(d[-1])
    if not (d <= 91).any():
        return None, 'not established by issue'
    ti = int(np.argmin(np.where(d <= 91, v, np.inf)))
    if ti >= len(v) - 1:
        return None, 'not established by issue'
    pi = ti + 1 + int(np.argmax(v[ti + 1:]))
    trough, peak, last = float(v[ti]), float(v[pi]), float(v[-1])
    amp = peak - trough
    if peak < .35 or amp < .15:
        return None, 'not established by issue'
    observed_dry = 0
    for j in range(pi + 1, len(v) - 1):
        if v[j] < trough + .5 * amp and v[j + 1] < trough + .5 * amp:
            observed_dry = int(d[j] <= normal_dry - 21)
            break

    def lag(days):
        m = d <= ld - days
        return float(v[m][-1]) if m.any() else np.nan

    return dict(doy=dt, ndvi=last, age=dt-ld, peak=peak, trough=trough,
                days_since_peak=ld-int(d[pi]), drop=peak-last, drop_share=(peak-last)/amp,
                chg15=last-lag(15), chg30=last-lag(30), anom=last-normal_curve[ld],
                normal_dry=normal_dry, days_to_normal_dry=normal_dry-dt,
                observed_dry=observed_dry), 'eligible'


def rainfall_ratio(rain, season, issue):
    end = min(pd.Timestamp(issue) - pd.Timedelta(days=8), pd.Timestamp(season, 11, 30))
    start = pd.Timestamp(season, 6, 1)
    span = end - start
    normal = np.mean([rain.loc[pd.Timestamp(y, 6, 1):pd.Timestamp(y, 6, 1)+span].sum()
                      for y in range(1979, 2012)])
    return float(rain.loc[start:end].sum()/normal) if normal > 0 else np.nan


def make_weather(cells, dates):
    rows = []
    for cell in cells:
        w = pd.read_csv(ROOT / f'data/prepared/{cell}.csv', parse_dates=['valid_time'])
        w = w.set_index('valid_time').asfreq('D')
        if w.Precipitation_Flux.isna().any():
            raise ValueError(f'Missing rainfall in {cell}; do not silently replace with zero')
        rain = w.Precipitation_Flux
        for issue in dates:
            e = issue-pd.Timedelta(days=8)
            s = issue.year if issue.month >= 6 else issue.year-1
            rows.append(dict(cell=cell, issue_date=issue, weather_date=e,
                             rain_jun_available_ratio=rainfall_ratio(rain, s, issue),
                             rain_since_oct=rain.loc[pd.Timestamp(s, 10, 1):e].sum(),
                             rain60=rain.loc[e-pd.Timedelta(days=59):e].sum(),
                             et0_30=w.ReferenceET_PenmanMonteith_FAO56.loc[e-pd.Timedelta(days=29):e].mean(),
                             tmax_30=w.Temperature_Air_2m_Max_24h.loc[e-pd.Timedelta(days=29):e].mean()-273.15,
                             spei=w.SPEI.loc[e]))
    return pd.DataFrame(rows)


def make_dataset():
    # v1 stores the raw per-season phenology as well as its old reference. Reuse
    # only the raw measurements; rebuild every reference and label below.
    old = pd.read_csv(ROOT / 'data/detect/labels.csv')
    lab = old[['point_id','season','quality_ok','est','dry_doy','mandal','irr']].copy()
    refs = [reference_stats(lab, r.point_id, r.season) for r in lab.itertuples()]
    lab['n_ref_dry'], lab['normal_dry'] = zip(*refs)
    lab['reference_ok'] = lab.n_ref_dry >= 2
    lab['early'] = lab.est & lab.dry_doy.notna() & (lab.dry_doy <= lab.normal_dry-21)
    lab['scorable'] = lab.quality_ok & lab.reference_ok
    lab['event_date'] = pd.to_datetime(lab.season.astype(str)+'-10-01') + pd.to_timedelta(lab.dry_doy, unit='D')
    mapping = pd.read_csv(ROOT/'data/forecast/instances.csv.gz', usecols=['mandal','cell']).drop_duplicates()
    lab = lab.merge(mapping, on='mandal', validate='many_to_one')
    loader = load_module('forecast_loader_v2', ROOT/'src/forecast/build_dataset.py')
    obs = loader.load_obs()
    groups = {k:g for k,g in obs.groupby(['point_id','season'])}
    z = np.load(ROOT/'data/forecast/point_curves.npz', allow_pickle=True)
    ids, seasons, curves = list(z['point_ids']), list(z['seasons']), z['P']
    pidx = {p:i for i,p in enumerate(ids)}
    rows, excluded = [], []
    for r in lab.itertuples():
        if not r.reference_ok:
            excluded.append(dict(point_id=r.point_id, season=r.season, issue_date=pd.NaT,
                                 reason='insufficient training reference'))
            continue
        use = [seasons.index(s) for s in TRAIN if s != r.season]
        normal = average(curves[pidx[r.point_id],use,:], axis=0)
        g = groups.get((r.point_id,r.season), obs.iloc[:0])
        for issue in issue_dates(r.season):
            f, reason = past_features(g, r.season, issue, r.normal_dry, normal)
            if f is None:
                excluded.append(dict(point_id=r.point_id,season=r.season,issue_date=issue,reason=reason))
                continue
            row = dict(point_id=r.point_id,season=r.season,issue_date=issue,mandal=r.mandal,
                       irr=r.irr,cell=r.cell,scorable=r.scorable,early=r.early,event_date=r.event_date,**f)
            row['at_risk'] = not (r.early and r.event_date <= issue)
            for h in HORIZONS:
                row[f'y{h}'] = int(r.early and issue < r.event_date <= issue+pd.Timedelta(days=h))
            rows.append(row)
    d = pd.DataFrame(rows)
    wx = make_weather(d.cell.unique(), sorted(d.issue_date.unique()))
    d = d.merge(wx,on=['cell','issue_date'],validate='many_to_one')
    if d[['spei','rain60','et0_30','tmax_30']].isna().any().any():
        raise ValueError('Missing corrected weather')
    d.to_csv(DATA/'instances.csv.gz',index=False)
    lab.to_csv(DATA/'labels.csv',index=False)
    pd.DataFrame(excluded).to_csv(DATA/'exclusions.csv',index=False)
    counts = lab.groupby('season').agg(points=('point_id','size'),reference_ok=('reference_ok','sum'),
                                      season_quality_ok=('quality_ok','sum'),scorable=('scorable','sum'))
    counts['early_events'] = lab[lab.scorable].groupby('season').early.sum()
    counts['forecast_points'] = d.groupby('season').point_id.nunique()
    counts['new_onset_training_or_evaluation_rows'] = d[d.scorable & d.at_risk & (d.observed_dry==0)].groupby('season').size()
    counts.to_csv(DATA/'coverage.csv')
    return d,lab


def fit_models(seed, weight):
    return {
        'Logistic regression':make_pipeline(SimpleImputer(strategy='median'), StandardScaler(),
            LogisticRegression(max_iter=3000,class_weight='balanced')),
        'Random forest':make_pipeline(SimpleImputer(strategy='median'),
            RandomForestClassifier(n_estimators=500,min_samples_leaf=5,class_weight='balanced_subsample',
                                   random_state=seed,n_jobs=4)),
        'XGBoost':XGBClassifier(n_estimators=400,max_depth=4,learning_rate=.05,subsample=.8,
            colsample_bytree=.8,scale_pos_weight=weight,random_state=seed,eval_metric='logloss',n_jobs=4)}


def threshold(y,p):
    grid = np.unique(np.quantile(p,np.linspace(.01,.99,197)))
    return float(max(grid,key=lambda x:balanced_accuracy_score(y,p>=x)))


def metric(y,p,thr):
    y,p = np.asarray(y),np.asarray(p)
    f = p>=thr
    both = len(np.unique(y))==2
    return dict(n=len(y),positives=int(y.sum()),prevalence=float(y.mean()),
                accuracy=accuracy_score(y,f),balanced_accuracy=balanced_accuracy_score(y,f),
                precision=precision_score(y,f,zero_division=0),recall=recall_score(y,f,zero_division=0),
                f1=f1_score(y,f,zero_division=0),roc_auc=roc_auc_score(y,p) if both else np.nan,
                average_precision=average_precision_score(y,p) if both else np.nan)


def event_records(labels,pred,h,model):
    """Aggregate deployable warning decisions, never repeated rows, into point-seasons."""
    rows=[]
    grouped={k:g.sort_values('issue_date') for k,g in pred.groupby(['point_id','season'])}
    for r in labels[labels.scorable].itertuples():
        g=grouped.get((r.point_id,r.season),pd.DataFrame(columns=pred.columns))
        first,last=issue_dates(r.season)[[0,-1]]
        event=bool(r.early and first < r.event_date <= last+pd.Timedelta(days=h))
        oper=g[g.observed_dry==0]
        alerts=oper[oper.warn.astype(bool)]
        window=oper.iloc[:0]
        if event:
            window=oper[(oper.issue_date < r.event_date)&(oper.issue_date>=r.event_date-pd.Timedelta(days=h))]
        hits=window[window.warn.astype(bool)]
        lead=(r.event_date-hits.issue_date.iloc[0]).days if len(hits) else np.nan
        rows.append(dict(point_id=r.point_id,season=r.season,cell=r.cell,irr=r.irr,horizon=h,model=model,
            event=event,opportunity=bool(len(window)),hit=bool(len(hits)),warned=bool(len(alerts)),
            first_warning=alerts.issue_date.iloc[0] if len(alerts) else pd.NaT,
            first_timely_warning=hits.issue_date.iloc[0] if len(hits) else pd.NaT,
            event_date=r.event_date if r.early else pd.NaT,lead_days=lead,
            n_warnings=len(alerts),n_timely_warnings=len(hits),n_forecasts=len(oper)))
    return pd.DataFrame(rows)


def event_summary(e):
    n,opp,hit,warn=int(e.event.sum()),int((e.event&e.opportunity).sum()),int(e.hit.sum()),int(e.warned.sum())
    ratio=lambda a,b:float(a/b) if b else np.nan
    leads=e.loc[e.hit,'lead_days']
    return dict(point_seasons=len(e),monitored_events=n,events_with_opportunity=opp,
        events_without_opportunity=n-opp,caught_events=hit,recall_opportunity=ratio(hit,opp),
        recall_all_events=ratio(hit,n),warned_point_seasons=warn,
        successful_warned_point_seasons=hit,warning_precision=ratio(hit,warn),
        median_lead=float(leads.median()),lead_q25=float(leads.quantile(.25)),lead_q75=float(leads.quantile(.75)),
        recall_at_least_7_days=ratio(int((e.hit&(e.lead_days>=7)).sum()),n),
        recall_at_least_14_days=ratio(int((e.hit&(e.lead_days>=14)).sum()),n))


def event_ci(e,unit):
    g=e.assign(opp=e.event&e.opportunity).groupby(unit)[['event','opp','hit','warned']].sum()
    ix=np.random.default_rng(12345).integers(0,len(g),size=(1000,len(g)))
    a=g.to_numpy(float)[ix].sum(axis=1)
    out={'bootstrap_unit':unit,'clusters':len(g)}
    for name,num,den in [('recall_all_events',2,0),('recall_opportunity',2,1),('warning_precision',2,3)]:
        v=np.divide(a[:,num],a[:,den],out=np.full(len(a),np.nan),where=a[:,den]>0)
        out[name+'_lo'],out[name+'_hi']=np.nanquantile(v,[.025,.975]).tolist()
    return out


def md_table(frame):
    def fmt(x):
        if pd.isna(x): return '-'
        if isinstance(x,(float,np.floating)): return f'{x:.3f}'
        return str(x)
    return '\n'.join(['| '+' | '.join(map(str,frame.columns))+' |',
                      '|'+'|'.join(['---']*len(frame.columns))+'|']+
                     ['| '+' | '.join(map(fmt,row))+' |' for row in frame.itertuples(index=False,name=None)])


def run(d,lab):
    summaries,seed_scores,events,point_preds,validation_preds,configs=[],[],[],[],[],[]
    for h in HORIZONS:
        print(f'Train horizon {h}',flush=True)
        active=d.scorable&d.at_risk&(d.observed_dry==0)
        tr=d[active&d.season.isin(TRAIN)]
        va=d[active&d.season.isin(VAL)]
        te=d[d.scorable&d.season.isin(TEST)].copy()  # keep operational rows after retrospective onset too
        vm=d[d.scorable&d.season.isin(VAL)].copy()
        y=f'y{h}'
        if tr[y].nunique()<2 or va[y].nunique()<2: raise ValueError('Insufficient validation/train events')
        weight=(1-tr[y].mean())/tr[y].mean()
        pv,pt,pvm={},{},{}
        for seed in SEEDS:
            for name,model in fit_models(seed,weight).items():
                if name=='Logistic regression' and seed>0:continue
                model.fit(tr[FEATURES],tr[y])
                pv.setdefault(name,[]).append(model.predict_proba(va[FEATURES])[:,1])
                pt.setdefault(name,[]).append(model.predict_proba(te[FEATURES])[:,1])
                pvm.setdefault(name,[]).append(model.predict_proba(vm[FEATURES])[:,1])
                print(f'  {name} seed {seed}',flush=True)
        ap={n:average_precision_score(va[y],np.mean(pv[n],axis=0)) for n in BASE_MODELS}
        weights=np.array([ap[n] for n in BASE_MODELS]);weights=weights/weights.sum()
        for name,w in [('Ensemble equal',np.ones(3)/3),('Ensemble weighted',weights)]:
            for dest in (pv,pt,pvm):
                dest[name]=[np.average([dest[n][min(seed,len(dest[n])-1)] for n in BASE_MODELS],axis=0,weights=w)
                            for seed in SEEDS]
        # Baseline scores and medians are fixed from training, not test distribution.
        for name,col,sign in [('Below-normal baseline','anom',-1),('Drop baseline','drop_share',1)]:
            fill=float(tr[col].median())
            for dest,part in [(pv,va),(pt,te),(pvm,vm)]:
                dest[name]=[(sign*part[col].fillna(fill)).to_numpy()]
        for dest,part in [(pv,va),(pt,te),(pvm,vm)]:
            dest['Early-drying rule']=[((part.drop_share>=.5)&(part.doy+h<=part.normal_dry-21)).to_numpy(float)]
            dest['Zero-onset baseline']=[np.zeros(len(part))]
        candidate=[*BASE_MODELS,'Ensemble equal','Ensemble weighted']
        vap={n:float(average_precision_score(va[y],np.mean(pv[n],axis=0))) for n in candidate}
        selected=max(candidate,key=lambda n:vap[n])
        config={'horizon':h,'selected_model':selected,'selection':'highest validation average precision',
                'weights':dict(zip(BASE_MODELS,weights.tolist())),'validation_ap':vap,
                'n_train':len(tr),'n_val':len(va),'thresholds':{}}
        new=(te.at_risk&(te.observed_dry==0)).to_numpy()
        meta=['point_id','season','cell','irr','issue_date','event_date','early','at_risk','observed_dry']
        for name in pv:
            a,b,c=np.mean(pv[name],axis=0),np.mean(pt[name],axis=0),np.mean(pvm[name],axis=0)
            thr=.5 if name in ['Early-drying rule','Zero-onset baseline'] else threshold(va[y].to_numpy(),a)
            config['thresholds'][name]=thr
            for s in ['pooled',*TEST]:
                mask=new if s=='pooled' else new&(te.season==s).to_numpy()
                if mask.any(): summaries.append(dict(horizon=h,model=name,season=s,selected=name==selected,
                                                    **metric(te[y].to_numpy()[mask],b[mask],thr)))
            for seed,(v,t) in enumerate(zip(pv[name],pt[name])):
                st=.5 if name in ['Early-drying rule','Zero-onset baseline'] else threshold(va[y].to_numpy(),v)
                seed_scores.append(dict(horizon=h,model=name,seed=seed,threshold=st,
                                        **metric(te[y].to_numpy()[new],t[new],st)))
            pred=te[meta].copy();pred['horizon']=h;pred['model']=name;pred['probability_or_score']=b
            pred['threshold']=thr;pred['warn']=(b>=thr)&(te.observed_dry.to_numpy()==0);pred['target']=te[y].to_numpy()
            pred['selected']=name==selected;point_preds.append(pred)
            vp=vm[meta].copy();vp['horizon']=h;vp['model']=name;vp['probability_or_score']=c;vp['threshold']=thr
            vp['warn']=(c>=thr)&(vm.observed_dry.to_numpy()==0);vp['target']=vm[y].to_numpy();validation_preds.append(vp)
            ev=event_records(lab[lab.season.isin(TEST)],pred,h,name);ev['selected']=name==selected;events.append(ev)
        configs.append(config)
        # Save progress after each horizon, preserving a reviewable partial run if interrupted.
        (OUT/'operating_points.json').write_text(json.dumps(configs,indent=2),encoding='utf-8')
        pd.concat(point_preds).to_csv(OUT/'predictions.csv.gz',index=False)
        pd.concat(validation_preds).to_csv(OUT/'validation_predictions.csv.gz',index=False)
        pd.concat(events).to_csv(OUT/'events.csv',index=False)
    met=pd.DataFrame(summaries);met.to_csv(OUT/'point_date_metrics.csv',index=False)
    pd.DataFrame(seed_scores).to_csv(OUT/'seed_metrics.csv',index=False)
    ev=pd.concat(events);rows=[];cis=[]
    for (h,name),g in ev.groupby(['horizon','model'],sort=False):
        for s in ['pooled',*TEST]:
            sub=g if s=='pooled' else g[g.season==s]
            rows.append(dict(horizon=h,model=name,season=s,selected=bool(g.selected.iloc[0]),**event_summary(sub)))
        if g.selected.iloc[0]:
            for unit in ['point_id','cell']:cis.append(dict(horizon=h,model=name,**event_ci(g,unit)))
    es=pd.DataFrame(rows);es.to_csv(OUT/'event_metrics.csv',index=False)
    pd.DataFrame(cis).to_csv(OUT/'event_intervals.csv',index=False)
    write_report(met,es,pd.DataFrame(cis),lab)


def write_report(met,es,cis,lab):
    cover=pd.read_csv(DATA/'coverage.csv')
    pm=met[(met.season=='pooled')&met.selected]
    em=es[(es.season=='pooled')&es.selected]
    weather=[]
    for cell,g in lab[lab.scorable&lab.est].groupby('cell'):
        w=pd.read_csv(ROOT/f'data/prepared/{cell}.csv',parse_dates=['valid_time']).set_index('valid_time')
        norm=np.mean([w.Precipitation_Flux.loc[f'{y}-06-01':f'{y}-11-30'].sum() for y in range(1979,2012)])
        for s,q in g.groupby('season'):
            weather.append(dict(cell=cell,season=s,n=len(q),early_rate=q.early.mean(),
                                rain_ratio=w.Precipitation_Flux.loc[f'{s}-06-01':f'{s}-11-30'].sum()/norm))
    cs=pd.DataFrame(weather);cs.to_csv(OUT/'rain_association.csv',index=False)
    q=cs[cs.n>=10];rho=q.early_rate.corr(q.rain_ratio,method='spearman')
    dry=q[q.rain_ratio<.8];other=q[q.rain_ratio>=.8]
    rain_summary={'cell_seasons':len(q),'spearman':float(rho),'dry_cell_seasons':len(dry),
                  'other_cell_seasons':len(other),
                  'contrast_estimable':bool(len(dry) and len(other)),
                  'dry_rate':float(dry.early_rate.mean()) if len(dry) else None,
                  'other_rate':float(other.early_rate.mean()) if len(other) else None}
    (OUT/'rain_association_summary.json').write_text(json.dumps(rain_summary,indent=2),encoding='utf-8')
    contrast=(f'Mean cell-season early-drying share below 80% of normal rain = {dry.early_rate.mean():.3f}; '
              f'otherwise {other.early_rate.mean():.3f}.' if len(dry) and len(other) else
              f'The <80%-of-normal versus other-years contrast is not estimable: {len(dry)} qualifying dry '
              f'cell-seasons and {len(other)} other cell-seasons. Do not carry forward the v1 twofold-rate claim.')
    lines=['# Rabi early-drying risk: corrected historical evaluation and unique-event audit','',
        'Development correction v2, 22 November 2026. Supersedes detect_v1 for operational claims. '
        'Satellite-defined early drying is a proxy event; agricultural drought causation is not independently verified.','',
        '## Corrections and scope','',
        '- Removed retrospective completed-season status from inputs; all satellite features use only issue-time observations.',
        '- Reference population, drying normals and NDVI curves use training seasons 2019-21 only (own season excluded).',
        '- Weather uses an 8-day publication lag, including the early-December antecedent-rain feature.',
        '- Forecasts target a new event within the horizon. Known/past events cannot earn advance-warning credit.',
        '- Weights, thresholds and primary model are chosen on 2022-23 validation, not the historical evaluation seasons.',
        '- v1 did not save thresholds/validation predictions, preventing an exact recount at its original operating point. '
        'Both are saved in v2. The cohort changed with the corrected reference; v1/v2 scores are not a same-cohort ablation.','',
        '## Coverage','',md_table(cover),'',
        '## New-onset point-date metrics (validation-selected model)','',
        md_table(pm[['horizon','model','n','positives','prevalence','roc_auc','average_precision','precision','recall']]),'',
        '## Unique point-season events (validation-selected model)','',
        md_table(em[['horizon','model','monitored_events','events_with_opportunity','caught_events',
                     'recall_all_events','recall_opportunity','warned_point_seasons','warning_precision','median_lead']]),'',
        'Each point-season contributes at most one event and one warned unit. Warning precision here is the fraction '
        'of warned point-seasons with at least one timely alert. It is not per-alert precision. Earlier false alerts '
        'are not erased from the saved point-date predictions. Lead time uses the first timely warning per caught event.','',
        '## Lead-time requirements','',
        md_table(em[['horizon','model','recall_at_least_7_days','recall_at_least_14_days','lead_q25','median_lead','lead_q75']]),'',
        '## Event uncertainty','',md_table(cis),'',
        'Point resampling retains each point across seasons; weather-cell resampling is indicative with very few cells. '
        'Neither creates additional independent drought seasons.','',
        '## All models and baselines: new-onset point-dates','',
        md_table(met[met.season=='pooled'][['horizon','model','selected','roc_auc','average_precision','precision','recall']]),'',
        '## All models: unique events','',
        md_table(es[es.season=='pooled'][['horizon','model','selected','caught_events','monitored_events',
                                        'recall_all_events','warning_precision','median_lead']]),'',
        '## Rainfall consistency check','',
        f'Across {len(q)} cell-seasons with at least 10 established reference-eligible points, Spearman rho = {rho:.3f}. '+
        contrast+' '+
        'This descriptive analysis uses all available development seasons. It is not an independent drought test.','',
        '## Limits on interpretation','',
        'The seven seasons were examined during development. The three evaluation seasons are excluded from fitting '
        'but are not a fresh prospective test. Sampled pixels are not verified fields. Crop identity, planting and '
        'harvest dates are unverified; normal crop timing changes can resemble drought. Retrospective phenology uses '
        'centered smoothing and two-image confirmation, so the nominal onset is an image-based date, not measured '
        'physiological stress onset. Long gaps can hide or delay crossings. The normal has only two or three training '
        'seasons. No observed crossing is not evidence of absence of water stress. Independent field/crop-water '
        'evidence is required before calling these alerts confirmed agricultural drought.','',
        '## Reproduction','',
        '`python -B src/detect/causal_events.py`',
        'Operating points: `operating_points.json`; event ledger: `events.csv`; validation probabilities: '
        '`validation_predictions.csv.gz`; inputs and exclusions: `data/detect_v2/`.','']
    (OUT/'EVENT_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')


def main():
    DATA.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reports-only',action='store_true',help='Rebuild report from saved scores without fitting')
    if parser.parse_args().reports_only:
        write_report(pd.read_csv(OUT/'point_date_metrics.csv'),pd.read_csv(OUT/'event_metrics.csv'),
                     pd.read_csv(OUT/'event_intervals.csv'),pd.read_csv(DATA/'labels.csv'))
        print('Report refreshed from saved results; no training',flush=True)
        return
    print('Build causal dataset and training-only references',flush=True)
    d,lab=make_dataset()
    print(f'Eligible forecasts: {len(d)}; points: {d.point_id.nunique()}',flush=True)
    paths=[Path(__file__),ROOT/'docs/DETECT_v2.md',ROOT/'data/detect/labels.csv',
           ROOT/'data/gee_exports/C3_points_timeseries.csv',ROOT/'data/forecast/point_curves.npz']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (OUT/'provenance.json').write_text(json.dumps({'train':TRAIN,'validation':VAL,'evaluation':TEST,
        'seeds':SEEDS,'features':FEATURES,'sha256':hashes},indent=2),encoding='utf-8')
    run(d,lab)
    print('Complete: results/detect_v2/EVENT_REPORT.md',flush=True)


if __name__=='__main__':
    main()
