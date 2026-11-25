"""
Rabi drought v2 - monitoring indicators (adaptation of the soil-moisture-deficit duration idea of
Padhee et al. 2017; exact equations not accessible - see docs/DROUGHT2_v1.md).

Per grid point (district-wide ERA5-Land, 0.3 deg):
  rz7      = 7-day trailing mean of root-zone moisture (0.07/0.21/0.72 layer weights, as drought_v1)
  pct      = empirical percentile of rz7 among reference seasons 1990-91..2004-05, same grid point,
             calendar days within +-15 days (Weibull plotting position)
  deficit  = pct <= 0.20 ; severe = pct <= 0.10
Per district and day: deficit_area = share of grid points in deficit (missing points excluded, count kept).
Completed-season indicators (retrospective monitoring, window 1 Nov - 28/29 Feb):
  DD   = mean over grid points of the fraction of window days in deficit   (deficit duration)
  DDS  = same for severe deficit
  PCT  = mean percentile ; SOW = mean percentile 1 Oct - 30 Nov (water at sowing)
  RUN  = median over grid points of the longest run of consecutive deficit days
Rain baselines (AgERA5 site cells of the district, data/prepared): Jun-Nov and Nov-Feb rain vs 1979-2004 mean.

    python -B -m src.drought2.indicators
Writes data/drought2/daily_district.csv.gz, data/drought2/season_indicators.csv
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
D2 = Path(os.environ.get("DROUGHT2_DATA", ROOT / "data" / "drought2"))   # override for sensitivity runs
PREP = ROOT / "data" / "prepared"
REF = list(range(1990, 2005))
HALF = 15
DEF, SEV = 0.20, 0.10
CELLS = {"Kurnool": ["Peddakadubur", "kurnool_dinedevarapadu"], "Anantapur": ["Somandepalle", "cholasamudram"],
         "Tumkur": ["sira"]}


def season_of(dates: pd.Series) -> pd.Series:
    return dates.dt.year - (dates.dt.month <= 8).astype(int)


def load_grid() -> pd.DataFrame:
    g = pd.read_csv(D2 / "district_grid.csv.gz", parse_dates=["date"])
    g = g.sort_values(["gid", "date"])
    g["season"] = season_of(g.date)
    # 7-day trailing mean within a season block (blocks are Sep-Apr; no cross-season carry)
    g["rz7"] = g.groupby(["gid", "season"]).rootzone.transform(lambda s: s.rolling(7, min_periods=7).mean())
    g["cday"] = g.date.dt.dayofyear
    return g


def percentiles(g: pd.DataFrame) -> pd.DataFrame:
    out = []
    for gid, q in g.groupby("gid"):
        ref = q[q.season.isin(REF) & q.rz7.notna()]
        rd, rv = ref.cday.to_numpy(), ref.rz7.to_numpy()
        pct = np.full(len(q), np.nan)
        cd, v = q.cday.to_numpy(), q.rz7.to_numpy()
        for i in range(len(q)):
            if np.isnan(v[i]):
                continue
            dist = np.abs(rd - cd[i])
            dist = np.minimum(dist, 366 - dist)
            sample = rv[dist <= HALF]
            if len(sample) >= 30:
                pct[i] = (np.sum(sample < v[i]) + 0.5 * np.sum(sample == v[i]) + 1) / (len(sample) + 1)
        out.append(pd.Series(pct, index=q.index))
    g["pct"] = pd.concat(out)
    g["deficit"] = np.where(g.pct.notna(), (g.pct <= DEF).astype(float), np.nan)
    g["severe"] = np.where(g.pct.notna(), (g.pct <= SEV).astype(float), np.nan)
    return g


def longest_run(x: np.ndarray) -> int:
    best = cur = 0
    for v in x:
        cur = cur + 1 if v == 1 else 0
        best = max(best, cur)
    return best


def rain_baselines() -> pd.DataFrame:
    rows = []
    for dist, cells in CELLS.items():
        rr = []
        for c in cells:
            d = pd.read_csv(PREP / f"{c}.csv", usecols=["valid_time", "Precipitation_Flux"],
                            parse_dates=["valid_time"]).set_index("valid_time").Precipitation_Flux
            rr.append(d)
        rain = pd.concat(rr, axis=1).mean(axis=1)
        jn = {y: rain[f"{y}-06-01":f"{y}-11-30"].sum() for y in range(1979, 2023)}
        nf = {y: rain[f"{y}-11-01":f"{y + 1}-02-28"].sum() for y in range(1979, 2023)}
        jn0 = np.mean([jn[y] for y in range(1979, 2005)])
        nf0 = np.mean([nf[y] for y in range(1979, 2005)])
        for y in range(1990, 2023):
            rows.append(dict(district=dist, season=y, rain_jun_nov_ratio=jn[y] / jn0, rain_nov_feb_ratio=nf[y] / nf0))
    return pd.DataFrame(rows)


def main():
    g = load_grid()
    g[g.season.isin(REF) & g.rz7.notna()][["gid", "cday", "rz7"]].to_csv(D2 / "reference_rz7.csv.gz", index=False)
    g = percentiles(g)
    daily = g.groupby(["district", "date", "season"]).agg(
        deficit_area=("deficit", "mean"), severe_area=("severe", "mean"), pct_median=("pct", "median"),
        points=("pct", "count"), points_total=("gid", "size")).reset_index()
    daily.to_csv(D2 / "daily_district.csv.gz", index=False)
    g.to_csv(D2 / "grid_percentiles.csv.gz", index=False, columns=["gid", "district", "date", "season", "rz7",
                                                                    "pct", "deficit", "severe"])
    rows = []
    for (dist, s), q in g.groupby(["district", "season"]):
        win = q[(q.date >= f"{s}-11-01") & (q.date < f"{s + 1}-03-01")]
        sow = q[(q.date >= f"{s}-10-01") & (q.date < f"{s}-12-01")]
        per_pt = win.groupby("gid").agg(dd=("deficit", "mean"), dds=("severe", "mean"), cov=("pct", "count"),
                                        n=("date", "size"))
        runs = win.dropna(subset=["deficit"]).groupby("gid").deficit.apply(lambda x: longest_run(x.to_numpy()))
        rows.append(dict(district=dist, season=s, DD=per_pt.dd.mean(), DDS=per_pt.dds.mean(), PCT=win.pct.mean(),
                         SOW=sow.pct.mean(), RUN=runs.median() if len(runs) else np.nan,
                         coverage=per_pt["cov"].sum() / per_pt.n.sum() if per_pt.n.sum() else 0.0,
                         grid_points=q.gid.nunique(), reference_season=s in REF))
    si = pd.DataFrame(rows).merge(rain_baselines(), on=["district", "season"], how="left")
    si.to_csv(D2 / "season_indicators.csv", index=False)
    print(si.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
