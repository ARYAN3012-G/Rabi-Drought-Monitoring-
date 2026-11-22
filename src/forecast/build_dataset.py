"""
Rabi forecast v1 - dataset (rules: docs/FORECAST_v1.md, fixed before training).

    python src/forecast/build_dataset.py
Writes data/forecast/{instances.csv.gz, point_curves.npz, DATASET.md}
"""
from __future__ import annotations

import os
from pathlib import Path

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rabi"))
from protocol import md_table  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
GEE = ROOT / "data" / "gee_exports"
OUT = ROOT / "data" / "forecast"
WEATHER_DIR = Path(os.environ.get("PREPARED_WEATHER_DIR", ROOT.parent / "data" / "prepared"))  # v3/v4, frozen SPEI
SEASONS = list(range(2019, 2026))

MIN_COUNT, NDVI_MIN, NDVI_MAX = 12, -0.2, 1.0
SAT_DELAY = 2
WX_DELAYS = {"": 8, "_d1": 1}   # main: AgERA5 ~8-day publication delay; _d1 = sensitivity only
MAX_INPUT_AGE = 12
LEAD, TOL = 15, 3
CLIM_HALF = 7
N_DOY = 213          # 1 Oct .. 30 Apr (+ leap day)


def season_start(y: int) -> pd.Timestamp:
    return pd.Timestamp(y, 10, 1)


def load_obs() -> pd.DataFrame:
    t = pd.read_csv(GEE / "C3_points_timeseries.csv", parse_dates=["date"])
    t = t[(t["count"] >= MIN_COUNT) & t["mean"].between(NDVI_MIN, NDVI_MAX)]
    t = t.sort_values("count").groupby(["point_id", "date"], as_index=False).tail(1)
    t["season"] = t.date.dt.year - (t.date.dt.month <= 4).astype(int)
    t["doy"] = (t.date - pd.to_datetime(t.season.astype(str) + "-10-01")).dt.days
    return t.rename(columns={"mean": "ndvi"})[["point_id", "date", "season", "doy", "ndvi"]]


# ---- weather -------------------------------------------------------------------------------
def weather_cells() -> dict:
    files = pd.read_csv(ROOT / "data" / "sites.csv").weather_file.unique()
    cells = {}
    for wf in files:
        d = pd.read_csv(WEATHER_DIR / f"{wf}.csv", parse_dates=["valid_time"]).set_index("valid_time")
        cells[wf] = d
    return cells


def nearest_cell(cells: dict, lat: float, lon: float) -> str:
    return min(cells, key=lambda k: (cells[k].latitude.iloc[0] - lat) ** 2 + (cells[k].longitude.iloc[0] - lon) ** 2)


def weather_features(d: pd.DataFrame, dates: pd.DatetimeIndex, delay: int, sfx: str) -> pd.DataFrame:
    d = d.asfreq("D")
    rain = d.Precipitation_Flux.fillna(0)
    et0 = d.ReferenceET_PenmanMonteith_FAO56
    tmax = d.Temperature_Air_2m_Max_24h - 273.15
    cr = rain.cumsum()
    wb = (rain - et0).fillna(0).cumsum()
    # rain since 1 June, normal = 1979-2011 mean for the same calendar span
    clim_years = range(1979, 2012)
    rows = []
    for t in dates:
        e = t - pd.Timedelta(days=delay)
        jun = pd.Timestamp(e.year if e.month >= 6 else e.year - 1, 6, 1)
        since = rain[jun:e].sum()
        span = e - jun   # same number of days after 1 June in each normal year (leap-day safe)
        norm = np.mean([rain[pd.Timestamp(y, 6, 1):pd.Timestamp(y, 6, 1) + span].sum() for y in clim_years])
        f = dict(rain30=cr[e] - cr[e - pd.Timedelta(days=30)],
                 rain90=cr[e] - cr[e - pd.Timedelta(days=90)],
                 rain_jun_ratio=since / norm if norm > 0 else np.nan,
                 et0_15=et0[e - pd.Timedelta(days=14):e].mean(),
                 tmax_15=tmax[e - pd.Timedelta(days=14):e].mean(),
                 wb60=wb[e] - wb[e - pd.Timedelta(days=60)],
                 spei=d.SPEI.get(e, np.nan))
        rows.append({"issue_date": t, **{k + sfx: v for k, v in f.items()}})
    return pd.DataFrame(rows)


# ---- instances -----------------------------------------------------------------------------
def issue_dates(y: int) -> list:
    out, t = [], pd.Timestamp(y, 10, 15)
    while t + pd.Timedelta(days=LEAD + TOL) <= pd.Timestamp(y + 1, 4, 30):
        out.append(t)
        t += pd.Timedelta(days=5)
    return out


def last_before(dates: np.ndarray, vals: np.ndarray, cutoff: np.datetime64):
    i = np.searchsorted(dates, cutoff, side="right") - 1
    return (vals[i], dates[i]) if i >= 0 else (np.nan, None)


def build_point_season(g: pd.DataFrame, y: int) -> list:
    dates = g.date.to_numpy()
    vals = g.ndvi.to_numpy()
    rows = []
    for t in issue_dates(y):
        tn = np.datetime64(t)
        cut = tn - np.timedelta64(SAT_DELAY, "D")
        v0, d0 = last_before(dates, vals, cut)
        r = dict(issue_date=t, season=y, doy_issue=(t - season_start(y)).days)
        if d0 is None or (tn - d0) / np.timedelta64(1, "D") > MAX_INPUT_AGE:
            r["status"] = "no_recent_obs"
            rows.append(r)
            continue
        age0 = (tn - d0) / np.timedelta64(1, "D")
        # target: nearest obs to t+15 within +-3 d
        lo, hi = tn + np.timedelta64(LEAD - TOL, "D"), tn + np.timedelta64(LEAD + TOL, "D")
        m = (dates >= lo) & (dates <= hi)
        if not m.any():
            r["status"] = "no_target"
            rows.append(r)
            continue
        cand = np.where(m)[0]
        k = cand[np.argmin(np.abs((dates[cand] - (tn + np.timedelta64(LEAD, "D"))) / np.timedelta64(1, "D")))]
        past = dates <= cut
        v15, d15 = last_before(dates, vals, tn - np.timedelta64(15, "D"))
        v30, d30 = last_before(dates, vals, tn - np.timedelta64(30, "D"))
        sm = past & (dates >= np.datetime64(season_start(y)))
        r.update(status="ok", ndvi_last=v0, age_last=age0,
                 doy_last=int((d0 - np.datetime64(season_start(y))) / np.timedelta64(1, "D")),
                 ndvi_15=v15, age_15=(tn - d15) / np.timedelta64(1, "D") if d15 is not None else np.nan,
                 ndvi_30=v30, age_30=(tn - d30) / np.timedelta64(1, "D") if d30 is not None else np.nan,
                 season_max=vals[sm].max() if sm.any() else np.nan,
                 season_min=vals[sm].min() if sm.any() else np.nan,
                 n_obs30=int((past & (dates > tn - np.timedelta64(30, "D"))).sum()),
                 target=vals[k],
                 doy_target=int((dates[k] - np.datetime64(season_start(y))) / np.timedelta64(1, "D")),
                 target_offset=int((dates[k] - tn) / np.timedelta64(1, "D")))
        r["chg15"] = r["ndvi_last"] - r["ndvi_15"]
        r["chg30"] = r["ndvi_last"] - r["ndvi_30"]
        rows.append(r)
    return rows


def point_curves(obs: pd.DataFrame, pids: list) -> np.ndarray:
    """P[point, season, doy] = mean NDVI of that point-season within +-CLIM_HALF days (NaN if none)."""
    P = np.full((len(pids), len(SEASONS), N_DOY), np.nan)
    idx = {p: i for i, p in enumerate(pids)}
    for (pid, s), g in obs.groupby(["point_id", "season"]):
        if s not in SEASONS:
            continue
        acc = np.zeros(N_DOY)
        n = np.zeros(N_DOY)
        for dd, v in zip(g.doy.to_numpy(), g.ndvi.to_numpy()):
            a, b = max(0, dd - CLIM_HALF), min(N_DOY, dd + CLIM_HALF + 1)
            acc[a:b] += v
            n[a:b] += 1
        with np.errstate(invalid="ignore"):
            P[idx[pid], SEASONS.index(s)] = acc / n
    return P


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pts = pd.read_csv(GEE / "C3_points.csv")
    obs = load_obs()
    rows = []
    for pid, g in obs.groupby("point_id"):
        g = g.sort_values("date")
        for y in SEASONS:
            for r in build_point_season(g, y):
                r["point_id"] = pid
                rows.append(r)
    inst = pd.DataFrame(rows).merge(pts, on="point_id")

    cells = weather_cells()
    centre = pts.groupby("mandal")[["lat", "lon"]].mean()
    m2c = {m: nearest_cell(cells, r.lat, r.lon) for m, r in centre.iterrows()}
    wx = []
    days = pd.DatetimeIndex(sorted(inst.issue_date.unique()))
    for c in set(m2c.values()):
        w = None
        for sfx, delay in WX_DELAYS.items():
            x = weather_features(cells[c], days, delay, sfx)
            w = x if w is None else w.merge(x, on="issue_date")
        w["cell"] = c
        wx.append(w)
    inst["cell"] = inst.mandal.map(m2c)
    inst = inst.merge(pd.concat(wx), on=["cell", "issue_date"], how="left")
    inst["doy_fc"] = inst.doy_issue + LEAD          # climatology day, known at issue (amendment A1)
    inst["span_days"] = inst.doy_target - inst.doy_last

    pids = sorted(pts.point_id)
    P = point_curves(obs, pids)
    np.savez_compressed(OUT / "point_curves.npz", P=P, point_ids=np.array(pids), seasons=np.array(SEASONS))
    inst.to_csv(OUT / "instances.csv.gz", index=False)

    st = inst.groupby(["season", "status"]).size().unstack(fill_value=0)
    st["share_ok"] = (st.ok / st.sum(axis=1)).round(3)
    ok = inst[inst.status == "ok"]
    lines = ["# Rabi forecast v1 - dataset", "",
             f"Points: {pts.point_id.nunique()}; clean observations: {len(obs)}; "
             f"potential forecasts: {len(inst)}; usable: {len(ok)} ({len(ok) / len(inst):.1%}).", "",
             "Mandal -> AgERA5 cell: " + ", ".join(f"{m}: {c}" for m, c in m2c.items()), "",
             "## Potential forecasts by season and status", "",
             "no_recent_obs = latest observation older than 12 days (NOT 'no crop'); "
             "no_target = no observation within t+15 +- 3 days (no interpolation).", "",
             md_table(st.reset_index()), "",
             "## Usable forecasts by season and class", "",
             md_table(ok.groupby(["season", "irr"]).size().unstack().rename(columns={0: "rainfed", 1: "irrigated"}).reset_index()),
             "", f"Distinct point-seasons with >= 1 usable forecast: {ok.groupby(['point_id', 'season']).ngroups}",
             "", "Weather: data/prepared (frozen 1979-2011 SPEI). Missing share among usable rows: "
             + ", ".join(f"{c} {ok[c].isna().mean():.1%}" for c in ok.columns
                         if c.startswith(("rain", "et0", "tmax", "wb60", "spei"))), ""]
    (OUT / "DATASET.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
