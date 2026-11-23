"""Download explicit ERA5-Land soil layers, retaining raw responses and provenance."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'data/drought_v1'
LAYERS = ['soil_moisture_0_to_7cm_mean', 'soil_moisture_7_to_28cm_mean',
          'soil_moisture_28_to_100cm_mean']
URL = 'https://archive-api.open-meteo.com/v1/archive'

def download(end='2026-04-30'):
    raw=OUT/'raw'; raw.mkdir(parents=True,exist_ok=True)
    mapping=pd.read_csv(ROOT/'data/detect_v2/labels.csv',usecols=['cell']).drop_duplicates()
    manifest=[]; rows=[]
    for cell in sorted(mapping.cell):
        w=pd.read_csv(ROOT/f'data/prepared/{cell}.csv',nrows=1)
        lat,lon=float(w.latitude.iloc[0]),float(w.longitude.iloc[0])
        for start in range(1981,2027,10):
            finish=min(f'{start+9}-12-31',end)
            if f'{start}-01-01'>end: continue
            file=raw/f'{cell}_{start}_{finish}.json'
            params=dict(latitude=lat,longitude=lon,start_date=f'{start}-01-01',
                end_date=finish,daily=','.join(LAYERS),models='era5_land',timezone='GMT',
                cell_selection='nearest',elevation='nan')
            if not file.exists():
                for attempt in range(5):
                    r=requests.get(URL,params=params,timeout=90)
                    if r.status_code==200:break
                    if r.status_code not in [429,500,502,503,504]:r.raise_for_status()
                    print(f'Retry {cell} {start}: HTTP {r.status_code}: {r.text[:180]}',flush=True)
                    time.sleep(min(60,10*(attempt+1)))
                r.raise_for_status(); j=r.json()
                if 'daily' not in j:raise ValueError(j)
                file.write_text(json.dumps(j),encoding='utf-8')
            else:j=json.loads(file.read_text(encoding='utf-8'))
            d=pd.DataFrame(j['daily']).rename(columns={'time':'date'})
            if d[LAYERS].isna().any().any():raise ValueError(f'Missing soil observations: {file}')
            if not d[LAYERS].apply(lambda x:x.between(0,1).all()).all():raise ValueError('Invalid soil units')
            d['cell']=cell
            d['rootzone']=.07*d[LAYERS[0]]+.21*d[LAYERS[1]]+.72*d[LAYERS[2]]
            rows.append(d)
            manifest.append(dict(cell=cell,request=params,source=URL,file=str(file.relative_to(ROOT)),
                returned_lat=j['latitude'],returned_lon=j['longitude'],units=j['daily_units'],
                sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
            print(f'{cell} {start}: {len(d)} days',flush=True)
            (OUT/'sources.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    result=pd.concat(rows,ignore_index=True).sort_values(['cell','date'])
    if result.duplicated(['cell','date']).any():raise ValueError('Duplicate cell/dates')
    result.to_csv(OUT/'soil_daily.csv.gz',index=False)
    print(f'Saved {len(result)} cell-days',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--end',default='2026-04-30')
    download(p.parse_args().end)
