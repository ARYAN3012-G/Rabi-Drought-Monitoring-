"""Regional rabi soil-moisture drought forecasts with as-of-date features.

Run `python -m src.drought.run train` from the repository root. See DROUGHT_v1.md.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (average_precision_score, roc_auc_score, f1_score,
                             precision_score, recall_score, brier_score_loss)

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/drought_v1'
OUT=ROOT/'results/drought_v1'
MODELS=ROOT/'models/drought_v1'
TRAIN=list(range(2001,2017)); VAL=list(range(2017,2023)); TEST=[2023,2024,2025]
HORIZONS=[7,15,30]; DELAY=8
SOIL_FEATURES=['soil_pct','soil_pct_change7','soil_pct_change30','rootzone','root7',
    'root_change7','root_change30','surface','deep','target_sin','target_cos','cell_index']
WX_FEATURES=[f'{v}{n}' for n in [7,30,90,180] for v in ['rain','et0','wb']]+['tmax30','dry_run']
FEATURES=SOIL_FEATURES+WX_FEATURES
CLASS_NAMES=['No percentile-defined deficit','Moderate soil-moisture deficit','Severe-or-worse soil-moisture deficit']

def calendar_bin(dates):
    d=pd.DatetimeIndex(dates)
    return np.array([(pd.Timestamp(2001,x.month,min(x.day,28) if x.month==2 else x.day)
                      -pd.Timestamp(2001,1,1)).days for x in d],dtype=int)

def fit_reference(soil):
    refs={}
    for cell,g in soil.groupby('cell'):
        g=g.sort_values('date').set_index('date').asfreq('D')
        z=g.rootzone.rolling(7,min_periods=7).mean()
        z=z[(z.index.year>=1981)&(z.index.year<=2000)].dropna()
        bins=calendar_bin(z.index)
        refs[cell]=[np.sort(z.to_numpy()[np.minimum(abs(bins-k),365-abs(bins-k))<=15])
                    for k in range(365)]
        if min(map(len,refs[cell]))<400:raise ValueError(f'Insufficient reference: {cell}')
    return refs

def percentile(values,dates,ref):
    out=[]
    for v,k in zip(values,calendar_bin(dates)):
        a=ref[k]
        out.append(np.nan if not np.isfinite(v) else
                   50*(np.searchsorted(a,v,'left')+np.searchsorted(a,v,'right'))/len(a))
    return np.array(out)

def drought_class(pct):
    p=np.asarray(pct)
    return np.where(p<=10,2,np.where(p<=20,1,0)).astype(int)

def prepare_soil(soil,refs):
    groups={}
    for cell,g in soil.groupby('cell'):
        g=g.sort_values('date').set_index('date').asfreq('D')
        g['root7']=g.rootzone.rolling(7,min_periods=7).mean()
        g['soil_pct']=percentile(g.root7,g.index,refs[cell])
        groups[cell]=g
    return groups

def load_weather(cells):
    return {c:pd.read_csv(ROOT/f'data/prepared/{c}.csv',parse_dates=['valid_time'])
              .set_index('valid_time').asfreq('D') for c in cells}

def features_at(soil,weather,issue,horizon,cell_index,require_weather=True):
    """Explicit exact cutoffs: no future observations, filling or backfilling."""
    issue=pd.Timestamp(issue);cut=issue-pd.Timedelta(days=DELAY)
    days=pd.date_range(cut-pd.Timedelta(days=179),cut)
    s=soil.reindex(pd.date_range(cut-pd.Timedelta(days=30),cut))
    need=['Precipitation_Flux','ReferenceET_PenmanMonteith_FAO56','Temperature_Air_2m_Max_24h']
    w=weather.reindex(index=days,columns=need) if weather is not None else pd.DataFrame(index=days,columns=need,dtype=float)
    if s[['rootzone','root7','soil_pct','soil_moisture_0_to_7cm_mean',
          'soil_moisture_28_to_100cm_mean']].isna().any().any():return None,'missing/stale soil'
    weather_ok=not w[need].isna().any().any()
    if require_weather and not weather_ok:return None,'missing/stale weather'
    last=s.iloc[-1];p7=s.iloc[-8];p30=s.iloc[0]
    target=issue+pd.Timedelta(days=horizon);k=calendar_bin([target])[0]
    f=dict(soil_pct=last.soil_pct,soil_pct_change7=last.soil_pct-p7.soil_pct,
        soil_pct_change30=last.soil_pct-p30.soil_pct,rootzone=last.rootzone,root7=last.root7,
        root_change7=last.root7-p7.root7,root_change30=last.root7-p30.root7,
        surface=last.soil_moisture_0_to_7cm_mean,deep=last.soil_moisture_28_to_100cm_mean,
        target_sin=np.sin(2*np.pi*k/365),target_cos=np.cos(2*np.pi*k/365),cell_index=cell_index)
    if not weather_ok:
        f.update({k:np.nan for k in WX_FEATURES})
        return f,'ok'
    for n in [7,30,90,180]:
        f[f'rain{n}']=float(w.Precipitation_Flux.iloc[-n:].sum())
        f[f'et0{n}']=float(w.ReferenceET_PenmanMonteith_FAO56.iloc[-n:].sum())
        f[f'wb{n}']=f[f'rain{n}']-f[f'et0{n}']
    f['tmax30']=float(w.Temperature_Air_2m_Max_24h.iloc[-30:].mean()-273.15)
    dry=(w.Precipitation_Flux.to_numpy()[::-1]<1.)
    f['dry_run']=int(np.argmax(~dry)) if (~dry).any() else len(dry)
    return f,'ok'

def required_features(model):
    """Inspect the saved estimator, not the broad experiment feature catalogue."""
    if isinstance(model,Ensemble):
        return sorted({f for member in model.members for f in required_features(member)})
    if getattr(model,'kind',None)=='learned':return list(model.features)
    return ['soil_pct','soil_pct_change7']

def make_dataset(soil,refs,weather):
    groups=prepare_soil(soil,refs);cells=sorted(groups);rows=[];excluded=[]
    for cell in cells:
        s=groups[cell];w=weather[cell]
        for season in TRAIN+VAL+TEST:
            split='train' if season in TRAIN else 'validation' if season in VAL else 'evaluation'
            for issue in pd.date_range(f'{season}-12-01',f'{season+1}-03-31',freq='5D'):
                for h in HORIZONS:
                    f,reason=features_at(s,w,issue,h,cells.index(cell))
                    target=issue+pd.Timedelta(days=h)
                    y=s.soil_pct.get(target,np.nan);now=s.soil_pct.get(issue,np.nan)
                    if f is None or not np.isfinite(y) or not np.isfinite(now):
                        excluded.append(dict(cell=cell,season=season,issue_date=issue,horizon=h,reason=reason if f is None else 'target missing'))
                        continue
                    rows.append(dict(cell=cell,season=season,split=split,issue_date=issue,horizon=h,
                        target_date=target,target_start=target-pd.Timedelta(days=6),
                        soil_date=issue-pd.Timedelta(days=DELAY),weather_date=issue-pd.Timedelta(days=DELAY),
                        target_percentile=y,target=int(drought_class(y)),issue_percentile=now,**f))
    return pd.DataFrame(rows),pd.DataFrame(excluded)

class Candidate:
    """Pickleable learned model or an explicitly defined training-only baseline."""
    def __init__(self,name,features=None,estimator=None,kind='learned'):
        self.name,self.features,self.estimator,self.kind=name,features,estimator,kind

    def fit(self,d):
        if self.kind=='learned':self.estimator.fit(d[self.features],d.target)
        else:
            self.prior=np.bincount(d.target,minlength=3)/len(d)
            q=d.copy();q['bucket']=(q.soil_pct//10).clip(0,9).astype(int)
            q['month']=pd.to_datetime(q.target_date).dt.month
            self.month={};self.transition={}
            for month,g in q.groupby('month'):
                self.month[int(month)]=(np.bincount(g.target,minlength=3)+3*self.prior)/(len(g)+3)
            for (b,m),g in q.groupby(['bucket','month']):
                self.transition[int(b),int(m)]=(np.bincount(g.target,minlength=3)+10*self.month[int(m)])/(len(g)+10)
        return self

    def predict_proba(self,d):
        if self.kind=='learned':
            raw=self.estimator.predict_proba(d[self.features]);p=np.zeros((len(d),3))
            p[:,self.estimator.classes_.astype(int)]=raw;return p
        month=pd.to_datetime(d.target_date).dt.month
        if self.kind=='climatology':return np.array([self.month.get(int(m),self.prior) for m in month])
        if self.kind=='transition':return np.array([self.transition.get((int(min(p//10,9)),int(m)),self.month.get(int(m),self.prior)) for p,m in zip(d.soil_pct,month)])
        p=d.soil_pct.to_numpy().copy()
        if self.kind=='trend':p=np.clip(p+.5*d.soil_pct_change7.to_numpy()/7*(d.horizon.to_numpy()+DELAY),0,100)
        return np.eye(3)[drought_class(p)]

class Ensemble:
    def __init__(self,members):self.name='Equal learned ensemble';self.members=members
    def predict_proba(self,d):return np.mean([m.predict_proba(d) for m in self.members],axis=0)

def candidates():
    out=[Candidate('Percentile persistence',kind='persistence'),Candidate('Seasonal climatology',kind='climatology'),
         Candidate('Conditional transition',kind='transition'),Candidate('Damped trend',kind='trend')]
    for features,suffix in [(SOIL_FEATURES,'soil'),(FEATURES,'soil+weather')]:
        out.append(Candidate(f'Logistic {suffix}',features,make_pipeline(StandardScaler(),LogisticRegression(max_iter=2000,C=1.))))
        for leaf in [5,15]:
            out.append(Candidate(f'RF leaf{leaf} {suffix}',features,RandomForestClassifier(n_estimators=300,
                max_depth=12,min_samples_leaf=leaf,max_features=.8,random_state=42,n_jobs=4)))
        for leaves in [7,15]:
            out.append(Candidate(f'HGB leaves{leaves} {suffix}',features,HistGradientBoostingClassifier(
                max_iter=150,max_leaf_nodes=leaves,min_samples_leaf=20,l2_regularization=5,
                learning_rate=.05,early_stopping=False,random_state=42)))
    out.append(Candidate('Soil analog k25',['soil_pct','soil_pct_change7','soil_pct_change30','target_sin','target_cos'],
        make_pipeline(StandardScaler(),KNeighborsClassifier(n_neighbors=25,weights='distance'))))
    return out

def choose_threshold(y,p):
    y=np.asarray(y,dtype=bool);p=np.asarray(p)
    if not y.any():raise ValueError('No validation drought cases')
    options=np.unique(np.r_[0.,np.quantile(p,np.linspace(0,1,201)),np.nextafter(1.,2.)])
    records=[]
    for t in options:
        pred=p>=t;tp=int((pred&y).sum());n=int(pred.sum());rec=tp/y.sum();prec=tp/n if n else 0.
        f=.0 if not(tp) else 1.25*prec*rec/(.25*prec+rec)
        if rec>=.5:records.append((f,prec,rec,float(t)))
    return max(records)[-1]

def operating_threshold(candidate,y,p):
    # A binary persistence/trend rule must remain that rule, not become always-warn.
    if getattr(candidate,'kind',None) in ['persistence','trend']:return .5
    return choose_threshold(y,p)

def issue_allowed(issue):
    issue=pd.Timestamp(issue)
    if issue.month not in [12,1,2,3]:return False,'outside Dec-Mar monitoring season'
    if issue<pd.Timestamp(min(TEST),12,1):return False,'model selection used later validation seasons'
    return True,'ok'

def metrics(y,p,threshold):
    y=np.asarray(y,dtype=int);b=y>0;score=p[:,1:].sum(axis=1);warn=score>=threshold
    both=len(np.unique(b))==2
    return dict(n=len(y),drought_cases=int(b.sum()),prevalence=float(b.mean()),
        macro_f1=f1_score(y,p.argmax(axis=1),labels=[0,1,2],average='macro',zero_division=0),
        drought_ap=average_precision_score(b,score) if b.any() else np.nan,
        drought_auc=roc_auc_score(b,score) if both else np.nan,
        brier=brier_score_loss(b,score),precision=precision_score(b,warn,zero_division=0) if warn.any() else np.nan,
        recall=recall_score(b,warn,zero_division=0) if b.any() else np.nan,
        f1=f1_score(b,warn,zero_division=0) if b.any() else np.nan,warnings=int(warn.sum()))

def select(validation_rows):
    # Pure function of validation evidence: never receives an evaluation dataframe.
    return max(validation_rows,key=lambda r:(r['drought_ap'],-r['brier']))

def load_inputs():
    soil=pd.read_csv(DATA/'soil_daily.csv.gz',parse_dates=['date'])
    return soil,load_weather(sorted(soil.cell.unique()))
