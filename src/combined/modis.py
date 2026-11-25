"""MODIS long-record test v1 (rules: docs/MODIS_TEST_v1.md, registered before the export was run).

Input : data/modis/drought2_D2_modis_rabi.csv  (Earth Engine script src/gee/script_D2_modis_rabi.js)
Output: results/modis_v1/  MODIS_RESULTS.md, season_indicators.csv, composites.csv, t1..t4 csv
Run   : python -B -m src.combined.modis
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from src.drought2.paper import boot_auc, boot_rho, pooled

ROOT = Path(__file__).resolve().parents[2]
SRC = Path(os.environ.get('MODIS_FILE', ROOT / 'data/modis/drought2_D2_modis_rabi.csv'))
OUT = Path(os.environ.get('MODIS_RESULTS', ROOT / 'results/modis_v1'))
D2 = ROOT / 'data/drought2'
REF = list(range(2000, 2010))          # NDVI reference seasons 2000-01..2009-10
EVAL = list(range(2010, 2023))         # evaluation seasons 2010-11..2022-23
PRIMARY = ['Kurnool', 'Anantapur']
HALF, MIN_REF, MIN_VALID = 16, 8, 0.30
LOW, SOIL_DRY, RULE, LOSS = 0.20, 0.50, 0.25, -0.15
SITE_DISTRICT = {'Som': 'Anantapur', 'Lep': 'Anantapur', 'Cho': 'Anantapur', 'Sira': 'Tumkur',
                 'Ped': 'Kurnool', 'Din': 'Kurnool', 'Bal': 'Kurnool', 'Pul': 'Kurnool'}
SITE_CELL = {'Som': 'Somandepalle', 'Lep': 'cholasamudram', 'Cho': 'cholasamudram', 'Sira': 'sira',
             'Ped': 'Peddakadubur', 'Din': 'kurnool_dinedevarapadu', 'Bal': 'kurnool_dinedevarapadu',
             'Pul': 'kurnool_dinedevarapadu'}


def season_of(d: pd.Series) -> pd.Series:
    return d.dt.year - (d.dt.month <= 8).astype(int)


def load() -> pd.DataFrame:
    m = pd.read_csv(SRC, parse_dates=['date'])
    m['unit'] = m.unit.replace({'Anantapur': 'Anantapur', 'Tumkur': 'Tumkur', 'Kurnool': 'Kurnool'})
    m['season'] = season_of(m.date)
    m['cday'] = m.date.dt.dayofyear
    m['valid'] = (m.ndvi_count >= MIN_VALID * m.crop_pixels) & m.ndvi_mean.notna()
    m.loc[~m.valid, 'ndvi_mean'] = np.nan
    return m.sort_values(['unit', 'date']).reset_index(drop=True)


def ndvi_percentile(m: pd.DataFrame) -> pd.DataFrame:
    pct = pd.Series(np.nan, index=m.index)
    for u, q in m.groupby('unit'):
        ref = q[q.season.isin(REF) & q.ndvi_mean.notna()]
        rd, rv = ref.cday.to_numpy(), ref.ndvi_mean.to_numpy()
        for i, cd, v in zip(q.index, q.cday, q.ndvi_mean):
            if np.isnan(v):
                continue
            dist = np.abs(rd - cd); dist = np.minimum(dist, 366 - dist)
            s = rv[dist <= HALF]
            if len(s) >= MIN_REF:
                pct[i] = (np.sum(s < v) + 0.5 * np.sum(s == v) + 1) / (len(s) + 1)
    m['ndvi_pct'] = pct
    return m


def attach_soil(m: pd.DataFrame) -> pd.DataFrame:
    """District units: drought v2 district grid pct_median. Site units: their ERA5-Land site cell percentile."""
    dd = pd.read_csv(D2 / 'daily_district.csv.gz', parse_dates=['date'])[['district', 'date', 'pct_median']]
    m = m.merge(dd.rename(columns={'district': 'unit', 'pct_median': 'soil_pct'}), on=['unit', 'date'], how='left')
    from src.combined.fuse import soil_context
    sc = soil_context().rename(columns={'weather_date': 'date'})
    sc['date'] = pd.to_datetime(sc.date)
    site = m.unit_type == 'site'
    sm = m.loc[site, ['unit', 'date']].assign(cell=lambda x: x.unit.map(SITE_CELL)).merge(
        sc, on=['cell', 'date'], how='left')
    m.loc[site, 'soil_pct'] = sm.soil_pct.to_numpy()
    return m


def season_table(m: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (u, s), q in m.groupby(['unit', 'season']):
        start = pd.Timestamp(f'{s}-12-01')
        end = pd.Timestamp(f'{s + 1}-02-28')
        cut = pd.Timestamp(f'{s + 1}-01-15') - pd.Timedelta(days=20)   # composite start + 20 d <= 15 Jan
        for tag, hi in [('', end), ('_15jan', cut)]:
            w = q[(q.date >= start) & (q.date <= hi) & q.ndvi_pct.notna()]
            low = w.ndvi_pct <= LOW
            both = low & (w.soil_pct < SOIL_DRY)
            r = rows[-1] if tag else dict(unit=u, unit_type=q.unit_type.iloc[0], season=s)
            r.update({f'n_valid{tag}': len(w),
                      f'VD{tag}': low.mean() if len(w) else np.nan,
                      f'VPCT{tag}': w.ndvi_pct.mean() if len(w) else np.nan,
                      f'CD{tag}': both.mean() if len(w) and w.soil_pct.notna().all() else np.nan})
            if not tag:
                rows.append(r)
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    m = attach_soil(ndvi_percentile(load()))
    m.to_csv(OUT / 'composites.csv', index=False)
    st = season_table(m)
    st.to_csv(OUT / 'season_indicators.csv', index=False)

    y = pd.read_csv(D2 / 'yields_district.csv')
    si = pd.read_csv(D2 / 'season_indicators.csv')[['district', 'season', 'DD', 'rain_jun_nov_ratio']]
    ew = pd.read_csv(ROOT / 'results/drought2_paper/early_warning_rows.csv')
    ew = ew[ew.issue == '15 Jan'][['district', 'season', 'DD_so_far', 'spei_so_far']]
    d = (st[st.unit_type == 'district'].rename(columns={'unit': 'district'})
         .merge(y[['district', 'season', 'yield_index', 'sown_area_anom']], on=['district', 'season'])
         .merge(si, on=['district', 'season'], how='left').merge(ew, on=['district', 'season'], how='left'))
    d['loss'] = (d.yield_index <= LOSS).astype(int)
    d.to_csv(OUT / 'district_seasons.csv', index=False)
    lines = ['# MODIS long-record test v1: results', '',
             'Rules: `docs/MODIS_TEST_v1.md` (registered before export). Evaluation seasons 2010-11..2022-23, '
             'Kurnool + Anantapur; 95 % season-block bootstrap.', '']

    # T1 association
    t1 = []
    signs = {'DD': -1, 'VD': -1, 'CD': -1, 'VPCT': 1, 'rain_jun_nov_ratio': 1, 'spei_so_far': 1}
    for period, seasons in [('evaluation 2010-22', EVAL), ('inside NDVI reference 2000-09', REF)]:
        q = d[d.district.isin(PRIMARY) & d.season.isin(seasons)]
        for ind in signs:
            for out in ['yield_index', 'sown_area_anom']:
                qq = q.dropna(subset=[ind, out])
                if len(qq) < 6 or qq[ind].nunique() < 2:
                    continue
                r, n = pooled(qq, ind, out)
                lo, hi = boot_rho(qq, ind, out) if period.startswith('eval') else (np.nan, np.nan)
                t1.append(dict(period=period, indicator=ind, outcome=out, n=n, rho=r, lo=lo, hi=hi,
                               expected_sign=signs[ind]))
    t1 = pd.DataFrame(t1); t1.to_csv(OUT / 't1_association.csv', index=False)

    # T2 / T3 loss detection
    q = d[d.district.isin(PRIMARY) & d.season.isin(EVAL)].copy()
    t2 = []
    for ind, sign in [('DD', 1), ('VD', 1), ('CD', 1), ('VPCT', -1), ('rain_jun_nov_ratio', -1),
                      ('VD_15jan', 1), ('CD_15jan', 1), ('VPCT_15jan', -1), ('DD_so_far', 1), ('spei_so_far', -1)]:
        qq = q.dropna(subset=[ind])
        yv, sv = qq.loss.to_numpy(), sign * qq[ind].to_numpy()
        if yv.min() == yv.max():
            continue
        auc = roc_auc_score(yv, sv)
        lo, hi = boot_auc(yv, sv, qq.season.to_numpy())
        row = dict(indicator=ind, n=len(qq), losses=int(yv.sum()), auc=auc, lo=lo, hi=hi)
        if ind in ('DD', 'VD', 'CD'):
            warn = qq[ind] >= RULE
            tp = int((warn & (qq.loss == 1)).sum())
            row.update(rule=f'{ind} >= {RULE}', warned=int(warn.sum()), caught=tp,
                       precision=tp / warn.sum() if warn.sum() else np.nan, recall=tp / yv.sum())
        t2.append(row)
    t2 = pd.DataFrame(t2); t2.to_csv(OUT / 't2_t3_loss_detection.csv', index=False)

    # T4 greenness attribution (district composites, evaluation seasons)
    c = m[(m.unit_type == 'district') & m.unit.isin(PRIMARY) & m.season.isin(EVAL) & (m.ndvi_pct <= LOW)
          & m.soil_pct.notna() & m.date.dt.month.isin([12, 1, 2])]
    c = c.merge(d[['district', 'season', 'loss']].rename(columns={'district': 'unit'}), on=['unit', 'season'])
    c['soil'] = np.where(c.soil_pct < SOIL_DRY, 'soil below normal', 'soil normal/wet')
    t4 = c.groupby('soil').agg(low_greenness_composites=('loss', 'size'), in_loss_season=('loss', 'sum'))
    t4['share_in_loss_season'] = t4.in_loss_season / t4.low_greenness_composites
    rng = np.random.default_rng(0); us = c.season.unique(); diffs = []
    for _ in range(2000):
        b = pd.concat([c[c.season == s] for s in rng.choice(us, len(us))])
        g = b.groupby('soil').loss.mean()
        if len(g) == 2:
            diffs.append(g['soil below normal'] - g['soil normal/wet'])
    t4_ci = np.percentile(diffs, [2.5, 97.5]) if diffs else [np.nan, np.nan]
    t4.to_csv(OUT / 't4_attribution.csv')

    sites = st[st.unit_type == 'site'].copy()
    sites['district'] = sites.unit.map(SITE_DISTRICT)
    sites = sites.merge(d[['district', 'season', 'loss']], on=['district', 'season'], how='left')
    sites.to_csv(OUT / 'site_seasons.csv', index=False)

    f = lambda x: '-' if pd.isna(x) else (f'{x:.2f}' if isinstance(x, float) else str(x))
    def md(df):
        return '\n'.join(['| ' + ' | '.join(df.columns) + ' |', '|' + '---|' * len(df.columns)] +
                         ['| ' + ' | '.join(f(v) for v in r) + ' |' for r in df.itertuples(index=False)])
    lines += ['## T1 association with district rabi outcomes', '', md(t1), '',
              f'## T2/T3 loss-season detection ({int(q.loss.sum())} loss seasons of {len(q)})', '', md(t2), '',
              '## T4 low-greenness composites: share in yield-loss seasons by soil state', '', md(t4.reset_index()),
              '', f'Difference (soil below normal - normal/wet): 95 % CI [{t4_ci[0]:.2f}, {t4_ci[1]:.2f}]', '',
              '## Data coverage', '',
              md(m.groupby('unit').agg(composites=('date', 'size'), valid=('valid', 'sum'),
                                        with_pct=('ndvi_pct', lambda s: int(s.notna().sum()))).reset_index())]
    (OUT / 'MODIS_RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
