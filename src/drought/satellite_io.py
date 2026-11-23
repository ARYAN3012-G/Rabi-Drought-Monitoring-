"""Frozen point population, append-only satellite imports and causal crop context."""
from __future__ import annotations
from datetime import datetime,timezone
import json
from pathlib import Path
import numpy as np
import pandas as pd
from . import model as M
from .live_data import LIVE,cell_config,sha

FROZEN=M.ROOT/'data/gee_exports/C3_points_timeseries.csv'
POINTS=M.ROOT/'data/gee_exports/C3_points.csv'

def clean_observations(raw):
    required={'point_id','date','mean','count'}
    if not required.issubset(raw):raise ValueError(f'Satellite CSV needs {sorted(required)}')
    d=raw.copy();d['date']=pd.to_datetime(d.date,errors='raise')
    for c in ['mean','count']:d[c]=pd.to_numeric(d[c],errors='coerce')
    d=d[(d['count']>=12)&d['mean'].between(-.2,1)].copy()
    d=d.sort_values(['point_id','date','count'],kind='stable').drop_duplicates(['point_id','date'],keep='last')
    return d.rename(columns={'mean':'ndvi'})[['point_id','date','ndvi','count']]

def load_observations(live_dir=LIVE):
    paths=[FROZEN];parts=[pd.read_csv(FROZEN)]
    ext=Path(live_dir)/'satellite_extension.csv.gz'
    if ext.exists():parts.append(pd.read_csv(ext));paths.append(ext)
    return clean_observations(pd.concat(parts,ignore_index=True)),paths

def import_satellite(path,live_dir=LIVE):
    path=Path(path);raw=pd.read_csv(path);points=pd.read_csv(POINTS)
    d=clean_observations(raw)
    from .operations import local_today
    if (pd.to_datetime(raw.date)>pd.Timestamp(local_today())).any():
        raise ValueError('Satellite export contains future acquisition dates')
    unknown=set(raw.point_id)-set(points.point_id)
    if unknown:raise ValueError(f'Unknown point IDs: {sorted(unknown)[:4]}')
    # Preserve every frozen outcome and training observation.
    historical=pd.read_csv(FROZEN,usecols=['date']);cut=pd.to_datetime(historical.date).max()
    d=d[d.date>cut].rename(columns={'ndvi':'mean'})
    live_dir=Path(live_dir);live_dir.mkdir(parents=True,exist_ok=True)
    target=live_dir/'satellite_extension.csv.gz'
    if target.exists():
        old=pd.read_csv(target,parse_dates=['date'])
        joined=old.merge(d,on=['point_id','date'],suffixes=('_old','_new'))
        if len(joined) and ((joined['mean_old']-joined['mean_new']).abs()>1e-12).any():
            raise ValueError('Imported satellite values revise a recorded observation; review source before replacing')
        d=pd.concat([old,d],ignore_index=True).sort_values('count',kind='stable').drop_duplicates(['point_id','date'],keep='last')
    temporary=live_dir/'satellite_extension.pending.csv.gz';d.to_csv(temporary,index=False);temporary.replace(target)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    meta=dict(source=str(path.resolve()),sha256=sha(path),raw_rows=len(raw),retained_live_rows=len(d),
        frozen_unchanged=True,download_import_time_utc=stamp,minimum_clear_count=12)
    (live_dir/f'satellite_import_{stamp}.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return meta

def context_at(regional,issue,points,obs,cells):
    issue=pd.Timestamp(issue);cut=issue-pd.Timedelta(days=2)
    if points.point_id.duplicated().any():raise ValueError('Duplicate point IDs')
    past=obs[obs.date<=cut].sort_values(['point_id','date']).groupby('point_id',as_index=False).tail(1)
    pts=points.merge(past[['point_id','date','ndvi']],on='point_id',how='left')
    coordinates={r.cell:(r.latitude,r.longitude) for r in cells.itertuples()}
    pts['cell']=[min(coordinates,key=lambda c:(lat-coordinates[c][0])**2+(lon-coordinates[c][1])**2)
                 for lat,lon in zip(pts.lat,pts.lon)]
    pts['image_age_days']=(issue-pts.date).dt.days
    recent=pts.date.notna()&pts.image_age_days.le(12)
    pts['vegetation_context']=np.select([~recent,pts.ndvi.ge(.35)],
        ['unknown: no recent clear image','green vegetation observed'],default='low greenness observed')
    pts.loc[~recent,'ndvi']=np.nan
    out=pts.merge(regional,on='cell',how='left',validate='many_to_many')
    flag=out['warning'].eq(True).fillna(False)
    out['interpretation']=np.select([out.status.ne('ok'),out.irr.eq(1),out.vegetation_context.str.startswith('unknown'),
        flag&out.vegetation_context.eq('green vegetation observed'),flag],
        ['regional forecast unavailable','regional context only: irrigation supply unknown','crop context unavailable',
         'regional drought warning near green rainfed vegetation: inspect crop water stress',
         'regional drought warning: check crop presence and water stress'],
        default='no regional percentile warning: crop health not established')
    out['field_drought_assessment']='not independently assessed'
    return out

def make_gee_script(path):
    pts=pd.read_csv(POINTS);records=pts[['point_id','mandal','irr','lon','lat']].values.tolist()
    # Coordinates/IDs are frozen; do not resample using current-season greenness.
    header='''// Rabi live point observations; generated from frozen C3_points.csv.
// Paste into https://code.earthengine.google.com and run the one Tasks export.
// Set START and END_EXCLUSIVE for the new monitoring period. No resampling.
var START = '2026-10-01';
var END_EXCLUSIVE = '2026-11-24';
var records = '''
    body=''';
var pts = ee.FeatureCollection(records.map(function(r) {
  return ee.Feature(ee.Geometry.Point([r[3], r[4]]),
    {point_id:r[0], mandal:r[1], irr:r[2], lon:r[3], lat:r[4]});
}));
var aoi = pts.geometry().bounds();
var cs = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');
var images = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(aoi).filterDate(START, END_EXCLUSIVE)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE',90)).linkCollection(cs,['cs_cdf'])
  .map(function(img) {
    var scl=img.select('SCL');
    var clear=img.select('cs_cdf').gte(0.60).and(scl.neq(1)).and(scl.neq(3))
      .and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10)).and(scl.neq(11));
    return img.normalizedDifference(['B8','B4']).rename('NDVI').updateMask(clear)
      .copyProperties(img,['system:time_start']);
  });
var buffers=pts.map(function(p) {return p.buffer(15);});
// Same 15 m buffer, 10 m reduction, cloud mask and projection as C3.
var rows=images.map(function(img) {
  var date=ee.Date(img.get('system:time_start')).format('YYYY-MM-dd');
  return img.reduceRegions({collection:buffers.filterBounds(img.geometry()),
    reducer:ee.Reducer.mean().combine({reducer2:ee.Reducer.count(),sharedInputs:true}),
    crs:'EPSG:32643',scale:10,tileScale:2}).map(function(f){return f.set('date',date);});
}).flatten().filter(ee.Filter.gt('count',0));
Export.table.toDrive({collection:rows,description:'Rabi_live_points',folder:'drought_rabi',
  fileNamePrefix:'Rabi_live_points',fileFormat:'CSV',
  selectors:['point_id','mandal','irr','date','mean','count']});
print('Frozen points',pts.size());
print('Export created. Import downloaded CSV with: python rabi.py import-satellite FILE.csv');
Map.centerObject(pts,8);Map.addLayer(pts,{color:'ff9900'},'Frozen sampled points');
'''
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(header+json.dumps(records,separators=(',',':'))+body,encoding='utf-8')
    return str(path)
