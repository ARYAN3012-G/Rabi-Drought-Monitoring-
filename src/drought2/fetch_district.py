"""
District-wide ERA5-Land grid (via Open-Meteo archive) for the rabi drought v2 study.

Grid: 0.2 deg points inside the (pre-2022) district polygons of geoBoundaries IND ADM2
(Kurnool, Anantapur, Tumkur) = the districts of our 8 study sites. Variables (daily):
root-zone soil-moisture layers (Sep-Apr of each rabi season; free-API budget).

    python -B -m src.drought2.fetch_district
Writes data/drought2/district_grid.csv, data/drought2/raw/*.json, data/drought2/sources.json
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "drought2"
RAW = OUT / "raw"
BND = ROOT / "data" / "external" / "boundaries" / "ind_adm2.geojson"
URL = "https://archive-api.open-meteo.com/v1/archive"
DISTRICTS = {"Kurnool": "Kurnool", "Anantapur": "Anantapur", "Tumkur": "Tumkur"}
DAILY = ["soil_moisture_0_to_7cm_mean", "soil_moisture_7_to_28cm_mean", "soil_moisture_28_to_100cm_mean"]
STEP = 0.3
CHUNKS = [(f"{y}-09-01", f"{y + 1}-04-30") for y in range(1990, 2023)]   # Sep-Apr of rabi seasons 1990-91..2022-23


def _inside(x, y, ring):
    n, c = len(ring), False
    for i in range(n):
        x1, y1 = ring[i][:2]
        x2, y2 = ring[(i + 1) % n][:2]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def grid_points():
    gj = json.loads(BND.read_text(encoding="utf-8"))
    rows = []
    for f in gj["features"]:
        nm = f["properties"]["shapeName"]
        if nm not in DISTRICTS:
            continue
        g = f["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        xs = [p[0] for poly in polys for p in poly[0]]
        ys = [p[1] for poly in polys for p in poly[0]]
        for lat in np.arange(np.floor(min(ys) * 5) / 5 + 0.1, max(ys), STEP):
            for lon in np.arange(np.floor(min(xs) * 5) / 5 + 0.1, max(xs), STEP):
                if any(_inside(lon, lat, poly[0]) for poly in polys):
                    rows.append(dict(district=DISTRICTS[nm], lat=round(lat, 2), lon=round(lon, 2)))
    return pd.DataFrame(rows)


def download():
    RAW.mkdir(parents=True, exist_ok=True)
    pts = grid_points()
    pts["gid"] = [f"{d[:3]}_{i:03d}" for i, d in enumerate(pts.district)]
    pts.to_csv(OUT / "grid_points.csv", index=False)
    print(pts.groupby("district").size().to_string())
    sources, frames = [], []
    batch = 20
    for c0, c1 in CHUNKS:
        for b in range(0, len(pts), batch):
            p = pts.iloc[b:b + batch]
            f = RAW / f"grid_{b:03d}_{c0[:4]}.json"
            params = dict(latitude=",".join(map(str, p.lat)), longitude=",".join(map(str, p.lon)), start_date=c0,
                          end_date=c1, daily=",".join(DAILY), models="era5_land", timezone="GMT")
            if not f.exists():
                for attempt in range(8):
                    r = requests.get(URL, params=params, timeout=300, headers={"User-Agent": "research-client"})
                    if r.status_code == 200:
                        f.write_bytes(r.content)
                        break
                    wait = 620 if (r.status_code == 429 and "Hourly" in r.text) else 20 * (attempt + 1)
                    print(f"{r.status_code}: waiting {wait}s", flush=True)
                    time.sleep(wait)
                else:
                    raise RuntimeError(f"download failed {r.status_code}: {r.text[:200]}")
                time.sleep(8)
            data = json.loads(f.read_text())
            data = data if isinstance(data, list) else [data]
            for gid, d in zip(p.gid, data):
                df = pd.DataFrame(d["daily"])
                df["gid"] = gid
                frames.append(df)
            sources.append(dict(file=str(f.relative_to(ROOT)), source=URL, params=params,
                                sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
    g = pd.concat(frames).rename(columns={"time": "date"})
    g["rootzone"] = (0.07 * g.soil_moisture_0_to_7cm_mean + 0.21 * g.soil_moisture_7_to_28cm_mean
                     + 0.72 * g.soil_moisture_28_to_100cm_mean)
    g = g.merge(pts[["gid", "district", "lat", "lon"]], on="gid")
    g.to_csv(OUT / "district_grid.csv.gz", index=False)
    (OUT / "sources.json").write_text(json.dumps(dict(accessed_utc=datetime.now(timezone.utc).isoformat(),
                                                      boundaries=str(BND.relative_to(ROOT)), step_deg=STEP,
                                                      requests=sources), indent=1), encoding="utf-8")
    print("rows", len(g), "points", g.gid.nunique(), g.date.min(), g.date.max())


if __name__ == "__main__":
    download()
