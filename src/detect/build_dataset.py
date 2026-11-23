"""
Rabi early-drying detection dataset: issue dates every 5 days (1 Dec - 31 Mar), horizons 7 / 15 / 30 days
(docs/DETECT_v1.md). Inputs use satellite observations <= t-2 and weather <= t-8 only.

    python src/detect/build_dataset.py
Writes data/detect/instances.csv.gz and data/detect/eligibility.csv
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "forecast"))
from build_dataset import load_obs  # noqa: E402

OUT = ROOT / "data" / "detect"
WX = ROOT / "data" / "prepared"
REF = [2019, 2020, 2021, 2022]
HORIZONS = [7, 15, 30]
SAT_DELAY, WX_DELAY, MAX_AGE = 2, 8, 12
GREEN, RISE = 0.35, 0.15


def issue_dates(y):
    t, out = pd.Timestamp(y, 12, 1), []
    while t <= pd.Timestamp(y + 1, 3, 31):
        out.append(t)
        t += pd.Timedelta(days=5)
    return out


def weather_table(cells, dates):
    rows = []
    for c in cells:
        d = pd.read_csv(WX / f"{c}.csv", parse_dates=["valid_time"]).set_index("valid_time").asfreq("D")
        rain = d.Precipitation_Flux.fillna(0)
        cr = rain.cumsum()
        norm_cache = {}
        for t in dates:
            e = t - pd.Timedelta(days=WX_DELAY)
            y = t.year if t.month >= 6 else t.year - 1
            if y not in norm_cache:
                tot = rain[f"{y}-06-01":f"{y}-11-30"].sum()
                norm = np.mean([rain[f"{k}-06-01":f"{k}-11-30"].sum() for k in range(1979, 2012)])
                norm_cache[y] = tot / norm
            rows.append(dict(cell=c, issue_date=t, rain_jun_nov_ratio=norm_cache[y],
                             rain_since_oct=cr[e] - cr[pd.Timestamp(y, 10, 1) - pd.Timedelta(days=1)],
                             rain60=cr[e] - cr[e - pd.Timedelta(days=60)],
                             et0_30=d.ReferenceET_PenmanMonteith_FAO56[e - pd.Timedelta(days=29):e].mean(),
                             tmax_30=(d.Temperature_Air_2m_Max_24h[e - pd.Timedelta(days=29):e] - 273.15).mean(),
                             spei=d.SPEI.get(e, np.nan)))
    return pd.DataFrame(rows)


def main():
    lab = pd.read_csv(ROOT / "data" / "detect" / "labels.csv")
    obs = load_obs()
    z = np.load(ROOT / "data" / "forecast" / "point_curves.npz", allow_pickle=True)
    P, pids, seasons = z["P"], list(z["point_ids"]), list(z["seasons"])
    pidx = {p: i for i, p in enumerate(pids)}
    groups = {k: g.sort_values("date") for k, g in obs.groupby(["point_id", "season"])}

    rows, elig = [], []
    cand = lab[lab.quality_ok & lab.rabi_point]
    for r in cand.itertuples():
        g = groups.get((r.point_id, r.season))
        dates = g.date.to_numpy()
        doy = g.doy.to_numpy()
        vals = pd.Series(g.ndvi.to_numpy()).rolling(3, min_periods=1).median().to_numpy()   # causal smoothing
        use = [seasons.index(s) for s in REF if s != r.season]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            ncurve = np.nanmean(P[pidx[r.point_id]][use], axis=0)
        s0 = pd.Timestamp(r.season, 10, 1)
        for t in issue_dates(r.season):
            dt = (t - s0).days
            cut = np.datetime64(t - pd.Timedelta(days=SAT_DELAY))
            k = np.searchsorted(dates, cut, side="right")
            base = dict(point_id=r.point_id, season=r.season, issue_date=t)
            if k == 0 or (np.datetime64(t) - dates[k - 1]) / np.timedelta64(1, "D") > MAX_AGE:
                elig.append(dict(base, reason="no recent observation"))
                continue
            v, d = vals[:k], doy[:k]
            early = d <= 91
            if early.sum() == 0:
                elig.append(dict(base, reason="not established by t"))
                continue
            ti = int(np.argmin(np.where(early, v, np.inf)))
            if ti >= k - 1:
                elig.append(dict(base, reason="not established by t"))
                continue
            pi = ti + 1 + int(np.argmax(v[ti + 1:]))
            trough, peak = v[ti], v[pi]
            if not (peak >= GREEN and peak - trough >= RISE):
                elig.append(dict(base, reason="not established by t"))
                continue
            elig.append(dict(base, reason="eligible"))
            last = v[-1]
            ld = int(d[-1])

            def lag(days):
                m = d <= ld - days
                return v[m][-1] if m.any() else np.nan
            amp = peak - trough
            status_t = int(bool(r.early) and r.dry_doy <= dt)
            f = dict(point_id=r.point_id, season=r.season, issue_date=t, mandal=r.mandal, irr=r.irr,
                     doy=dt, ndvi=last, age=dt - ld, peak=peak, trough=trough, days_since_peak=ld - int(d[pi]),
                     drop=peak - last, drop_share=(peak - last) / amp if amp > 0 else np.nan,
                     chg15=last - lag(15), chg30=last - lag(30), anom=last - ncurve[min(ld, ncurve.size - 1)],
                     normal_dry=r.normal_dry, days_to_normal_dry=r.normal_dry - dt, status_t=status_t,
                     early_season=int(bool(r.early)), dry_doy=r.dry_doy)
            for h in HORIZONS:
                if t + pd.Timedelta(days=h) > pd.Timestamp(r.season + 1, 4, 30):
                    f[f"y{h}"] = np.nan
                else:
                    f[f"y{h}"] = int(bool(r.early) and r.dry_doy <= dt + h)
            rows.append(f)
    inst = pd.DataFrame(rows)
    cells = pd.read_csv(ROOT / "data" / "forecast" / "instances.csv.gz", usecols=["mandal", "cell"]).drop_duplicates()
    inst = inst.merge(cells, on="mandal")
    wx = weather_table(inst.cell.unique(), sorted(inst.issue_date.unique()))
    inst = inst.merge(wx, on=["cell", "issue_date"], how="left")
    inst.to_csv(OUT / "instances.csv.gz", index=False)
    e = pd.DataFrame(elig)
    tab = e.groupby(["season", "reason"]).size().unstack(fill_value=0)
    tab.to_csv(OUT / "eligibility.csv")
    print(tab.to_string())
    print("instances:", len(inst), "positives at t+15:", int(inst.y15.sum()))


if __name__ == "__main__":
    main()
