"""Direct (interactive) version of script_D2_modis_rabi.js: same units, mask, collection and columns.

Why: Export tasks wait in the Earth Engine batch queue; interactive requests run immediately.
Fetches one rabi season (Sep..Apr) at a time and writes data/modis/drought2_D2_modis_rabi.csv.
Resumable: seasons already in data/modis/parts/ are skipped.

Run: python -B src/gee/fetch_d2_direct.py   (after: earthengine authenticate)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import ee
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/modis'
PARTS = OUT / 'parts'
PROJECT = 'drought-sat-2026'
SITES = [('Som', 13.9988, 77.6247), ('Lep', 13.7998, 77.6194), ('Cho', 13.8118, 77.5687),
         ('Sira', 13.7975, 76.9750), ('Ped', 15.7826, 77.2528), ('Din', 15.7715, 78.0471),
         ('Bal', 15.7834, 78.0561), ('Pul', 15.7982, 78.0806)]


def units():
    site = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([lon, lat]).buffer(3000),
                                            {'unit': u, 'unit_type': 'site'}) for u, lat, lon in SITES])
    dist = (ee.FeatureCollection('FAO/GAUL/2015/level2')
            .filter(ee.Filter.inList('ADM2_NAME', ['Kurnool', 'Anantapur', 'Tumkur']))
            .map(lambda f: ee.Feature(f.geometry(), {'unit': f.get('ADM2_NAME'), 'unit_type': 'district'})))
    return dist.merge(site)


def main():
    ee.Initialize(project=PROJECT)
    PARTS.mkdir(parents=True, exist_ok=True)
    U = units()
    crop = ee.ImageCollection('ESA/WorldCover/v100').first().eq(40)
    cp = crop.selfMask().rename('crop').reduceRegions(collection=U, reducer=ee.Reducer.count(), scale=250,
                                                      tileScale=4).getInfo()
    crop_pixels = {f['properties']['unit']: f['properties']['count'] for f in cp['features']}
    print('cropland pixels', crop_pixels, flush=True)

    def prep(im):
        ok = im.select('SummaryQA').lte(1)
        return (im.select(['NDVI', 'EVI']).multiply(0.0001).updateMask(ok).updateMask(crop)
                .copyProperties(im, ['system:time_start']))

    def rows(im):
        date = ee.Date(im.get('system:time_start')).format('YYYY-MM-dd')
        return im.reduceRegions(collection=U, reducer=ee.Reducer.mean().combine(ee.Reducer.count(), '', True),
                                scale=250, tileScale=4).map(
            lambda f: ee.Feature(None, {'unit': f.get('unit'), 'unit_type': f.get('unit_type'), 'date': date,
                                        'ndvi_mean': f.get('NDVI_mean'), 'evi_mean': f.get('EVI_mean'),
                                        'ndvi_count': f.get('NDVI_count')}))

    for s in range(1999, 2026):          # season s = Sep s .. Apr s+1 (first images start Feb 2000)
        part = PARTS / f'season_{s}.csv'
        if part.exists():
            continue
        start = max(f'{s}-09-01', '2000-02-18')      # MODIS record starts 18 Feb 2000
        col = (ee.ImageCollection('MODIS/061/MOD13Q1').filterDate(start, f'{s + 1}-05-01')
               .filter(ee.Filter.calendarRange(9, 4, 'month')).map(prep))
        for attempt in range(4):
            try:
                t = time.time()
                fc = ee.FeatureCollection(col.map(rows)).flatten()
                data = ee.data.computeFeatures({'expression': fc, 'fileFormat': 'PANDAS_DATAFRAME'})
                data['crop_pixels'] = data.unit.map(crop_pixels)
                data[['unit', 'unit_type', 'date', 'ndvi_mean', 'evi_mean', 'ndvi_count', 'crop_pixels']].to_csv(
                    part, index=False)
                print(f'season {s}: {len(data)} rows in {time.time() - t:.0f}s', flush=True)
                break
            except Exception as e:  # transient timeouts: retry
                print(f'season {s} attempt {attempt + 1} failed: {str(e)[:200]}', flush=True)
                time.sleep(10)
        else:
            sys.exit(f'season {s} failed 4 times; rerun to resume')
    df = pd.concat([pd.read_csv(p) for p in sorted(PARTS.glob('season_*.csv'))]).drop_duplicates(['unit', 'date'])
    df.sort_values(['unit', 'date']).to_csv(OUT / 'drought2_D2_modis_rabi.csv', index=False)
    print('wrote', OUT / 'drought2_D2_modis_rabi.csv', len(df), 'rows')


if __name__ == '__main__':
    main()
