"""
Rabi drought v2 - one command for an issue date, using saved artifacts only (no training).

    python -B -m src.drought2.run --date 2019-01-15            # historical replay (data in repository)
    python -B -m src.drought2.run --date 2026-12-15 --update   # fetch ERA5-Land soil for the season so far

Outputs results/drought2_operations/<date>/:
  district_status.csv   monitoring (season-so-far, input cutoff t-8) and 15-day forecast risk per district
  grid_points.geojson   latest percentile / deficit flag per grid point (0.3 deg, regional scale)
  report.md             readable summary with evidence dates and flags
  manifest.json         input / model hashes
Monitoring status and forecast risk are separate. Missing inputs give "unavailable", never "no deficit".
Scores are not calibrated probabilities. Regional soil-moisture deficit is not verified crop drought.
"""
from __future__ import annotations

import argparse
import os
import hashlib
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import requests
import sys

ROOT = Path(__file__).resolve().parents[2]
D2 = Path(os.environ.get("DROUGHT2_DATA", ROOT / "data" / "drought2"))
MD = Path(os.environ.get("DROUGHT2_MODELS", ROOT / "models" / "drought2_v1"))
LIVE = D2 / "live"
sys.path.insert(0, str(ROOT / "src" / "rabi"))
from protocol import md_table  # noqa: E402
URL = "https://archive-api.open-meteo.com/v1/archive"
LAG, HALF, DEF = 8, 15, 0.20


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ""


def season_of(t):
    return t.year if t.month >= 9 else t.year - 1


def fetch_live(start, end, pts):
    LIVE.mkdir(parents=True, exist_ok=True)
    frames = []
    for b in range(0, len(pts), 20):
        p = pts.iloc[b:b + 20]
        params = dict(latitude=",".join(map(str, p.lat)), longitude=",".join(map(str, p.lon)),
                      start_date=str(start.date()), end_date=str(end.date()),
                      daily="soil_moisture_0_to_7cm_mean,soil_moisture_7_to_28cm_mean,soil_moisture_28_to_100cm_mean",
                      models="era5_land", timezone="GMT")
        r = requests.get(URL, params=params, timeout=300, headers={"User-Agent": "research-client"})
        r.raise_for_status()
        f = LIVE / f"live_{start.date()}_{end.date()}_{b:03d}.json"
        f.write_bytes(r.content)
        data = r.json()
        for gid, d in zip(p.gid, data if isinstance(data, list) else [data]):
            df = pd.DataFrame(d["daily"]).rename(columns={"time": "date"})
            df["gid"] = gid
            frames.append(df)
        time.sleep(3)
    g = pd.concat(frames)
    g["rootzone"] = (0.07 * g.soil_moisture_0_to_7cm_mean + 0.21 * g.soil_moisture_7_to_28cm_mean
                     + 0.72 * g.soil_moisture_28_to_100cm_mean)
    return g.merge(pts[["gid", "district", "lat", "lon"]], on="gid")


def percentile_today(ref, gid, cday, v):
    r = ref.get(gid)
    if r is None or np.isnan(v):
        return np.nan
    dist = np.abs(r[:, 0] - cday)
    dist = np.minimum(dist, 366 - dist)
    s = r[dist <= HALF, 1]
    return (np.sum(s < v) + 0.5 * np.sum(s == v) + 1) / (len(s) + 1) if len(s) >= 30 else np.nan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--update", action="store_true")
    a = ap.parse_args()
    t = pd.Timestamp(a.date)
    s = season_of(t)
    cutoff = t - pd.Timedelta(days=LAG)
    out = Path(os.environ.get("DROUGHT2_OPS", ROOT / "results" / "drought2_operations")) / str(t.date())
    out.mkdir(parents=True, exist_ok=True)
    pts = pd.read_csv(D2 / "grid_points.csv")
    in_season = pd.Timestamp(s, 12, 1) <= t <= pd.Timestamp(s + 1, 3, 31)

    hist = pd.read_csv(D2 / "district_grid.csv.gz", parse_dates=["date"])
    g = hist[(hist.date >= pd.Timestamp(s, 9, 1)) & (hist.date <= cutoff)]
    if a.update and (g.empty or g.date.max() < cutoff):
        g = fetch_live(pd.Timestamp(s, 9, 1), cutoff, pts)
        g["date"] = pd.to_datetime(g.date)
    g = g.sort_values(["gid", "date"])
    g["rz7"] = g.groupby("gid").rootzone.transform(lambda x: x.rolling(7, min_periods=7).mean())
    ref = {k: v[["cday", "rz7"]].to_numpy() for k, v in pd.read_csv(D2 / "reference_rz7.csv.gz").groupby("gid")}
    g["pct"] = [percentile_today(ref, gid, d.dayofyear, v) for gid, d, v in zip(g.gid, g.date, g.rz7)]
    g["deficit"] = np.where(g.pct.notna(), (g.pct <= DEF).astype(float), np.nan)

    bundle = joblib.load(MD / "forecast_15d.joblib")
    rows = []
    for dist in ["Kurnool", "Anantapur", "Tumkur"]:
        q = g[g.district == dist]
        daily = q.groupby("date").agg(area=("deficit", "mean"), pct=("pct", "median"), n=("pct", "count"))
        complete = (not daily.empty and daily.index.max() >= cutoff and len(daily) >= 31
                    and daily.area.tail(31).notna().all())
        r = dict(district=dist, issue_date=str(t.date()), input_cutoff=str(cutoff.date()),
                 latest_soil_date=str(daily.index.max().date()) if not daily.empty else "",
                 grid_points=int(pts.district.eq(dist).sum()), scale="regional (0.3 deg grid, no cropland mask)")
        if not complete:
            r.update(monitoring_status="unavailable (incomplete soil inputs)", forecast_status="unavailable")
            rows.append(r)
            continue
        a_ = daily.area
        dd = a_[f"{s}-11-01":].mean() if cutoff >= pd.Timestamp(s, 11, 1) else np.nan
        r.update(deficit_area_now=round(a_.iloc[-1], 3), deficit_area_15d=round(a_.tail(15).mean(), 3),
                 median_percentile_now=round(daily.pct.iloc[-1], 3), deficit_duration_season_so_far=round(dd, 3)
                 if not np.isnan(dd) else None,
                 monitoring_status="soil-moisture deficit (regional)" if a_.tail(15).mean() >= 0.5
                 else "no widespread soil-moisture deficit (regional; not a crop-health statement)")
        if not in_season:
            r.update(forecast_status="not issued (outside 1 Dec - 31 Mar)")
        elif bundle["kind"] != "model":
            r.update(forecast_status=f"selected method is a baseline ({bundle['name']}); see results")
        else:
            feats = dict(area_last=a_.iloc[-1], area_15=a_.tail(15).mean(), area_30=a_.tail(30).mean(),
                         pct_last=daily.pct.iloc[-1], pct_chg15=daily.pct.iloc[-1] - daily.pct.iloc[-16],
                         pct_chg30=daily.pct.iloc[-1] - daily.pct.iloc[-31], dd_so_far=dd,
                         doy=(t - pd.Timestamp(s, 10, 1)).days, d_Kurnool=int(dist == "Kurnool"),
                         d_Anantapur=int(dist == "Anantapur"), d_Tumkur=int(dist == "Tumkur"))
            missing = [f for f in bundle["features"] if f not in feats]
            if missing:
                r.update(forecast_status=f"unavailable (needs {missing}; weather inputs not wired for live use)")
            else:
                X = pd.DataFrame([{f: feats[f] for f in bundle["features"]}])
                score = float(np.mean([m.predict_proba(X)[:, 1] for m in bundle["models"]]))
                r.update(forecast_model=bundle["name"], risk_score=round(score, 3), threshold=round(bundle["threshold"], 3),
                         forecast_window=f"{(t + pd.Timedelta(days=1)).date()} .. {(t + pd.Timedelta(days=15)).date()}",
                         forecast_status="WARNING: district-wide soil deficit likely in next 15 days"
                         if score >= bundle["threshold"] else "no warning (score below threshold; not 'healthy')")
        rows.append(r)
    st = pd.DataFrame(rows)
    st.to_csv(out / "district_status.csv", index=False)
    last = g[g.date == g.date.max()] if not g.empty else g
    if "lat" not in last.columns:
        last = last.merge(pts[["gid", "lat", "lon"]], on="gid", how="left")
    feats = [dict(type="Feature", geometry=dict(type="Point", coordinates=[float(r.lon), float(r.lat)]),
                  properties=dict(gid=r.gid, district=r.district, date=str(pd.Timestamp(r.date).date()),
                                  percentile=None if np.isnan(r.pct) else round(float(r.pct), 3),
                                  deficit=None if np.isnan(r.deficit) else bool(r.deficit)))
             for r in last.itertuples()]
    (out / "grid_points.geojson").write_text(json.dumps(dict(type="FeatureCollection", features=feats)), encoding="utf-8")
    md = ["# Rabi drought v2 - status for " + str(t.date()), "",
          f"Inputs up to {cutoff.date()} (8-day publication lag). Regional ERA5-Land root-zone soil moisture, "
          f"{len(pts)} grid points in Kurnool / Anantapur / Tumkur. **Monitoring status and the 15-day forecast are separate. "
          "Soil-moisture deficit is not verified crop drought; scores are not calibrated probabilities. Field "
          "validation is pending.**", "", md_table(st.fillna("")), ""]
    try:
        (out / "report.md").write_text("\n".join(md), encoding="utf-8")
    except Exception:
        (out / "report.md").write_text(st.to_string(), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps(dict(
        issue_date=str(t.date()), input_cutoff=str(cutoff.date()), updated=a.update,
        model=json.loads((MD / "forecast_15d.json").read_text()) if (MD / "forecast_15d.json").exists() else None,
        inputs={p.name: sha(p) for p in [D2 / "district_grid.csv.gz", D2 / "reference_rz7.csv.gz",
                                         MD / "forecast_15d.joblib"]}), indent=1), encoding="utf-8")
    print(st.to_string(index=False))
    print("Report:", out / "report.md")


if __name__ == "__main__":
    main()
