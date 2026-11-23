"""Attach causal crop observations to regional predictions without inventing field labels."""
import argparse
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
from . import model as M

def attach(date):
    issue=pd.Timestamp(date);folder=M.OUT/'forecasts'/issue.strftime('%Y-%m-%d')
    regional=pd.read_csv(folder/'regional_drought_risk.csv')
    if 'cell' not in regional:print('No regional forecast to contextualize');return
    pts=pd.read_csv(M.ROOT/'data/gee_exports/C3_points.csv')
    spec=importlib.util.spec_from_file_location('rabi_forecast_loader',M.ROOT/'src/forecast/build_dataset.py')
    loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
    obs=loader.load_obs();cut=issue-pd.Timedelta(days=2)
    obs=obs[obs.date<=cut].sort_values(['point_id','date']).groupby('point_id',as_index=False).tail(1)
    pts=pts.merge(obs[['point_id','date','ndvi']],on='point_id',how='left')
    cells={}
    for cell in regional.cell.dropna().unique():
        w=pd.read_csv(M.ROOT/f'data/prepared/{cell}.csv',nrows=1)
        cells[cell]=(float(w.latitude.iloc[0]),float(w.longitude.iloc[0]))
    pts['cell']=[min(cells,key=lambda c:(lat-cells[c][0])**2+(lon-cells[c][1])**2) for lat,lon in zip(pts.lat,pts.lon)]
    pts['image_age_days']=(issue-pts.date).dt.days
    pts['vegetation_context']=np.select([pts.date.isna()|pts.image_age_days.gt(12),pts.ndvi.ge(.35)],
        ['unknown: no recent clear image','green vegetation observed'],default='low greenness observed')
    pts.loc[pts.image_age_days.gt(12),'ndvi']=np.nan
    out=pts.merge(regional,on='cell',how='left',validate='many_to_many')
    out['interpretation']=np.select([out.status.ne('ok'),out.irr.eq(1),out.vegetation_context.str.startswith('unknown'),
        out.warning.fillna(False)&out.vegetation_context.eq('green vegetation observed'),out.warning.fillna(False)],
        ['regional forecast unavailable','regional context only: irrigation supply unknown','crop context unavailable',
         'regional drought warning near green rainfed vegetation: inspect crop water stress',
         'regional drought warning: check crop presence and water stress'],
        default='no regional percentile warning: crop health not established')
    out['field_drought_confirmed']=False
    out.to_csv(folder/'sampled_point_context.csv',index=False)
    print(f'Saved {len(out)} point-horizon context rows. Scores shared by cell; not independent field drought predictions.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--date',required=True);attach(p.parse_args().date)
