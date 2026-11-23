"""Append-only live soil cache. Frozen training/evaluation files are never modified."""
from __future__ import annotations
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
import requests
from . import model as M
from .fetch_soil import LAYERS,URL

LIVE=M.ROOT/'data/drought_live'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def cell_config():
    return pd.read_csv(M.ROOT/'config/drought_cells.csv')

def load_soil(live_dir=LIVE):
    frozen=M.DATA/'soil_daily.csv.gz'
    # Match the parser used to fit the saved models; derived feature snapshots
    # are separately read with float_precision='round_trip' for exact replay.
    base=pd.read_csv(frozen,parse_dates=['date'])
    extra=Path(live_dir)/'soil_extension.csv.gz'
    if extra.exists():
        add=pd.read_csv(extra,parse_dates=['date'])
        base=pd.concat([base,add],ignore_index=True)
    if base.duplicated(['cell','date']).any():raise ValueError('Duplicate cell/date in frozen and live soil data')
    return base.sort_values(['cell','date']),[p for p in [frozen,extra] if p.exists()]

def append_checked(existing,new):
    """Refuse historical revisions, duplicates, gaps, missing/invalid water data."""
    for d in [existing,new]:
        if d.date.duplicated().any():raise ValueError('Duplicate soil dates')
    if new[LAYERS].isna().any().any() or not new[LAYERS].apply(lambda x:x.between(0,1).all()).all():
        raise ValueError('Missing or out-of-range soil layer')
    old=existing.set_index('date');incoming=new.set_index('date');overlap=old.index.intersection(incoming.index)
    if not len(overlap):raise ValueError('Soil update needs overlap to verify source continuity')
    if not np.allclose(old.loc[overlap,LAYERS],incoming.loc[overlap,LAYERS],rtol=0,atol=1e-9):
        raise ValueError('Soil source revised overlapping observations; frozen values retained, update stopped')
    add=new[new.date>existing.date.max()].copy().sort_values('date')
    if len(add):
        expected=pd.date_range(existing.date.max()+pd.Timedelta(days=1),add.date.max())
        if list(add.date)!=list(expected):raise ValueError('Non-contiguous soil update')
    return add

def update_soil(end,live_dir=LIVE,request_get=requests.get):
    end=pd.Timestamp(end).normalize();live_dir=Path(live_dir);live_dir.mkdir(parents=True,exist_ok=True)
    raw=live_dir/'raw';raw.mkdir(exist_ok=True)
    current,_=load_soil(live_dir); additions=[];requests_log=[]
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    for r in cell_config().itertuples():
        old=current[current.cell==r.cell]
        if old.empty:raise ValueError(f'No frozen source for {r.cell}')
        if old.date.max()>=end:continue
        start=old.date.max()-pd.Timedelta(days=6)
        params=dict(latitude=r.latitude,longitude=r.longitude,start_date=start.strftime('%Y-%m-%d'),
            end_date=end.strftime('%Y-%m-%d'),daily=','.join(LAYERS),models='era5_land',
            timezone='GMT',elevation='nan',cell_selection='nearest')
        for attempt in range(4):
            response=request_get(URL,params=params,timeout=60)
            if response.status_code==200:break
            if response.status_code not in [429,500,502,503,504]:response.raise_for_status()
            print(f'Soil update retry for {r.cell}: HTTP {response.status_code}',flush=True)
            if attempt<3:time.sleep(min(30,10*(attempt+1)))
        response.raise_for_status();j=response.json()
        file=raw/f'{stamp}_{r.cell}.json';file.write_text(json.dumps(j),encoding='utf-8')
        if not np.isclose(j['latitude'],r.latitude,atol=.051) or not np.isclose(j['longitude'],r.longitude,atol=.051):
            raise ValueError(f'Unexpected soil grid for {r.cell}')
        new=pd.DataFrame(j['daily']).rename(columns={'time':'date'});new['date']=pd.to_datetime(new.date)
        if new.date.min()!=start or new.date.max()!=end:raise ValueError('Incomplete soil request period')
        new['cell']=r.cell;new['rootzone']=.07*new[LAYERS[0]]+.21*new[LAYERS[1]]+.72*new[LAYERS[2]]
        add=append_checked(old,new);additions.append(add)
        requests_log.append(dict(cell=r.cell,request=params,source=URL,raw_file=str(file.relative_to(M.ROOT)),
            sha256=sha(file),rows_added=len(add),downloaded_at_utc=stamp))
        print(f'{r.cell}: verified overlap, {len(add)} new soil days through {end.date()}',flush=True)
    target=live_dir/'soil_extension.csv.gz'
    if additions:
        previous=pd.read_csv(target,parse_dates=['date'],float_precision='round_trip') if target.exists() else current.iloc[:0]
        merged=pd.concat([previous,*additions],ignore_index=True).sort_values(['cell','date'])
        if merged.duplicated(['cell','date']).any():raise ValueError('Duplicate appended records')
        temporary=live_dir/'soil_extension.pending.csv.gz';merged.to_csv(temporary,index=False)
        temporary.replace(target)
    manifest=live_dir/f'update_{stamp}.json'
    manifest.write_text(json.dumps(dict(end=str(end.date()),requests=requests_log,
        frozen_file_sha256=sha(M.DATA/'soil_daily.csv.gz'),status='updated' if additions else 'already current'),indent=2),encoding='utf-8')
    return dict(status='updated' if additions else 'already current',added_rows=sum(len(a) for a in additions),manifest=str(manifest))
