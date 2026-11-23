"""Independent reanalysis-product consistency check, never used for selection."""
import hashlib
import json
import pandas as pd
import requests
from . import model as M
from .run import md

def main():
    out=M.OUT/'cross_product';out.mkdir(parents=True,exist_ok=True)
    raw=M.DATA/'nasa_raw';raw.mkdir(exist_ok=True)
    soil=pd.read_csv(M.DATA/'soil_daily.csv.gz',parse_dates=['date']);rows=[];sources=[]
    for cell in sorted(soil.cell.unique()):
        file=raw/f'{cell}.json'
        w=pd.read_csv(M.ROOT/f'data/prepared/{cell}.csv',nrows=1)
        params=dict(parameters='GWETROOT',community='AG',latitude=float(w.latitude.iloc[0]),
            longitude=float(w.longitude.iloc[0]),start='19810101',end='20260430',format='JSON',**{'time-standard':'UTC'})
        if not file.exists():
            r=requests.get('https://power.larc.nasa.gov/api/temporal/daily/point',params=params,timeout=90)
            r.raise_for_status();file.write_text(r.text,encoding='utf-8')
        j=json.loads(file.read_text(encoding='utf-8'));series=pd.Series(j['properties']['parameter']['GWETROOT'],name='rootzone')
        series.index=pd.to_datetime(series.index,format='%Y%m%d');series=series.replace(j['header']['fill_value'],float('nan'))
        frame=series.rename_axis('date').reset_index();frame['cell']=cell;rows.append(frame)
        sources.append(dict(cell=cell,request=params,header=j['header'],units=j['parameters'],
            sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
        print(f'NASA cross-check {cell}: {series.notna().sum()} days',flush=True)
    nasa=pd.concat(rows);refs=M.fit_reference(nasa);groups=M.prepare_soil(nasa,refs)
    d=pd.read_csv(M.DATA/'instances.csv.gz',parse_dates=['target_date'])
    q=d[d.horizon==15].copy()
    q['nasa_percentile']=[groups[r.cell].soil_pct.get(r.target_date,float('nan')) for r in q.itertuples()]
    q['era5_dry']=q.target>0;q['nasa_dry']=q.nasa_percentile<=20
    q.to_csv(out/'comparison.csv',index=False)
    table=q[q.nasa_percentile.notna()].groupby('season').agg(cell_dates=('target','size'),
        era5_drought=('era5_dry','sum'),nasa_drought=('nasa_dry','sum'),nasa_median=('nasa_percentile','median'),era5_median=('target_percentile','median'))
    table.to_csv(out/'by_season.csv')
    (out/'sources.json').write_text(json.dumps(sources,indent=2),encoding='utf-8')
    text=['# Soil-product consistency check',
        'Post hoc diagnostic, not training or label selection. NASA POWER MERRA-2 GWETROOT is a different modelled root-zone estimate at coarser resolution; values are rounded and neighbouring requests can share grid cells. It is not field truth or an independent set of 1,350 crop labels. Same frozen 1981-2000 reference and +/-15-day calendar windows. Seven-day mean assessed at the primary 15-day target dates.',
        md(table.reset_index()),
        '[NASA root-zone data definitions](https://power.larc.nasa.gov/docs/methodology/data/sources_hydrology/) and [MERRA-2 soil-layer definitions](https://gmao.gsfc.nasa.gov/gmao-products/merra-2/faq_merra-2/). No primary labels or fitted models were changed using this comparison.']
    (out/'CROSS_PRODUCT_REPORT.md').write_text('\n\n'.join(text)+'\n',encoding='utf-8')
    print('Cross-product check complete',flush=True)

if __name__=='__main__':main()
