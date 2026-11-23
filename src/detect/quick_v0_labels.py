import sys
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "src" / "forecast"))
import build_dataset as B  # noqa: E402

obs = B.load_obs()
pts = pd.read_csv(R / "data" / "gee_exports" / "C3_points.csv")[["point_id", "mandal", "irr"]]
rows = []
for (pid, s), g in obs.groupby(["point_id", "season"]):
    g = g.sort_values("doy")
    v = g.ndvi.rolling(3, center=True, min_periods=1).median().to_numpy()
    d = g.doy.to_numpy()
    early = d <= 91                      # Oct-Dec
    if early.sum() < 2 or len(v) < 8:
        rows.append(dict(point_id=pid, season=s, ok=False)); continue
    ti = int(np.argmin(np.where(early, v, np.inf)))
    after = np.arange(len(v)) > ti
    if not after.any():
        rows.append(dict(point_id=pid, season=s, ok=False)); continue
    pi = int(np.argmax(np.where(after, v, -np.inf)))
    t, p = v[ti], v[pi]
    est = (p >= 0.35) and (p - t >= 0.15)
    dry = np.nan
    if est:
        half = t + 0.5 * (p - t)
        for i in range(pi + 1, len(v) - 1):
            if v[i] < half and v[i + 1] < half:   # sustained
                dry = d[i]; break
    rows.append(dict(point_id=pid, season=s, ok=True, est=est, peak_doy=d[pi], dry_doy=dry))
f = pd.DataFrame(rows).merge(pts, on="point_id")
f = f[f.ok]
ref = [2019, 2020, 2021, 2022]
out = []
for pid, g in f.groupby("point_id"):
    for r in g.itertuples():
        rr = g[g.season.isin(ref) & (g.season != r.season)]
        n_est = int(rr.est.astype(int).sum())
        normal_dry = rr[rr.est.astype(bool)].dry_doy.median()
        out.append(dict(point_id=pid, season=r.season, irr=r.irr, mandal=r.mandal, est=r.est,
                        dry=r.dry_doy, n_ref=len(rr), ref_est=n_est, normal_dry=normal_dry))
o = pd.DataFrame(out)
o["rabi_point"] = (o.ref_est >= 2)                      # normally grows a rabi crop
o["failed"] = o.rabi_point & ~o.est.astype(bool)
o["early"] = o.rabi_point & o.est.astype(bool) & (o.normal_dry - o.dry >= 21)
o["drought"] = o.failed | o.early
q = o[o.rabi_point]
print("rabi points per season:\n", q.groupby("season").size().to_string())
print(q.groupby("season")[["failed", "early", "drought"]].mean().round(3).to_string())
print(q.groupby(["season", "irr"]).drought.mean().unstack().round(3).to_string())
print("normal drying day-of-season (median):", q.normal_dry.median(), " (0 = 1 Oct)")
o.to_csv(Path(__file__).resolve().parents[2] / "results" / "detect_quick_v0" / "labels_v0.csv", index=False)
