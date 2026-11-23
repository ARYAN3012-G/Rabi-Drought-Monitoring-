from pathlib import Path

import numpy as np
import pandas as pd

SP = Path(__file__).resolve().parents[2] / "results" / "detect_quick_v0"
R = Path(__file__).resolve().parents[2]
W = R / "data" / "prepared"
o = pd.read_csv(SP / "labels_v0.csv")
cell = pd.read_csv(R / "data" / "forecast" / "instances.csv.gz", usecols=["mandal", "cell"]).drop_duplicates()
o = o.merge(cell, on="mandal")

# water: Jun-Nov rain of the season vs 1979-2011 mean (cell), i.e. stored water before rabi
rain = {}
for c in o.cell.unique():
    d = pd.read_csv(W / f"{c}.csv", usecols=["valid_time", "Precipitation_Flux"], parse_dates=["valid_time"])
    d = d.set_index("valid_time").Precipitation_Flux
    tot = lambda y: d[f"{y}-06-01":f"{y}-11-30"].sum()
    norm = np.mean([tot(y) for y in range(1979, 2012)])
    for y in range(2019, 2026):
        rain[(c, y)] = tot(y) / norm
o["rain_ratio"] = [rain[(c, y)] for c, y in zip(o.cell, o.season)]

for name, pt in (("loose: green in >=2 other ref seasons", o.ref_est >= 2),
                 ("strict: green in ALL other ref seasons (>=3)", (o.ref_est >= 3) & (o.ref_est == o.n_ref))):
    q = o[pt].copy()
    for thr in (21, 30):
        q["early"] = q.est.astype(bool) & ((q.normal_dry - q.dry) >= thr)
        q["failed"] = ~q.est.astype(bool)
        g = q.groupby(["season"]).agg(n=("early", "size"), failed=("failed", "mean"), early=("early", "mean"),
                                       rain=("rain_ratio", "mean"))
        print(f"\n== {name}; early = {thr}+ days before normal")
        print(g.round(3).to_string())
        # relation with water at cell-season level
        cs = q.groupby(["cell", "season"]).agg(failed=("failed", "mean"), early=("early", "mean"),
                                               rain=("rain_ratio", "first"), n=("early", "size"))
        cs = cs[cs.n >= 10]
        print("Spearman with Jun-Nov rain ratio (cell-season, n=%d): failed %.2f, early %.2f" % (
            len(cs), cs.failed.corr(cs.rain, method="spearman"), cs.early.corr(cs.rain, method="spearman")))
        dry = cs.rain < 0.8
        print("mean rate when rain<80%% of normal: failed %.2f early %.2f | otherwise: failed %.2f early %.2f" % (
            cs[dry].failed.mean(), cs[dry].early.mean(), cs[~dry].failed.mean(), cs[~dry].early.mean()))
