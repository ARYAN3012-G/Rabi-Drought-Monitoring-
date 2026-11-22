"""
Rabi early-drying labels (docs/DETECT_v1.md).

    python src/detect/build_labels.py
Writes data/detect/labels.csv (one row per point-season, every exclusion kept with its reason).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "forecast"))
from build_dataset import load_obs  # noqa: E402

OUT = ROOT / "data" / "detect"
REF = [2019, 2020, 2021, 2022]
GREEN, RISE, EARLY_DAYS = 0.35, 0.15, 21
MIN_OBS, MIN_EARLY_OBS = 8, 2


def phenology(doy: np.ndarray, ndvi: np.ndarray) -> dict:
    if len(ndvi) < MIN_OBS or (doy <= 91).sum() < MIN_EARLY_OBS:
        return dict(quality_ok=False)
    v = pd.Series(ndvi).rolling(3, center=True, min_periods=1).median().to_numpy()
    early = doy <= 91
    ti = int(np.argmin(np.where(early, v, np.inf)))
    after = np.arange(len(v)) > ti
    if not after.any():
        return dict(quality_ok=True, est=False)
    pi = int(np.argmax(np.where(after, v, -np.inf)))
    t, p = v[ti], v[pi]
    est = bool(p >= GREEN and p - t >= RISE)
    out = dict(quality_ok=True, est=est, trough=t, peak=p, peak_doy=int(doy[pi]), dry_doy=np.nan)
    if est:
        half = t + 0.5 * (p - t)
        for i in range(pi + 1, len(v) - 1):
            if v[i] < half and v[i + 1] < half:
                out["dry_doy"] = int(doy[i])
                break
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    obs = load_obs()
    pts = pd.read_csv(ROOT / "data" / "gee_exports" / "C3_points.csv")[["point_id", "mandal", "irr"]]
    rows = []
    for (pid, s), g in obs.groupby(["point_id", "season"]):
        g = g.sort_values("doy")
        rows.append(dict(point_id=pid, season=s, **phenology(g.doy.to_numpy(), g.ndvi.to_numpy())))
    ph = pd.DataFrame(rows)
    # complete grid so that point-seasons without observations are counted, not silently lost
    grid = pd.MultiIndex.from_product([pts.point_id, range(2019, 2026)], names=["point_id", "season"]).to_frame(False)
    ph = grid.merge(ph, how="left").merge(pts, on="point_id")
    ph["quality_ok"] = ph.quality_ok.fillna(False).astype(bool)
    ph["est"] = ph.est.fillna(False).astype(bool)

    n_ref, normal = [], []
    for r in ph.itertuples():
        q = ph[(ph.point_id == r.point_id) & ph.season.isin(REF) & (ph.season != r.season) & ph.est]
        n_ref.append(len(q))
        normal.append(q.dry_doy.median() if q.dry_doy.notna().any() else np.nan)
    ph["n_ref_est"] = n_ref
    ph["normal_dry"] = normal
    ph["rabi_point"] = (ph.n_ref_est >= 2) & ph.normal_dry.notna()
    ph["early"] = ph.est & ph.dry_doy.notna() & (ph.dry_doy <= ph.normal_dry - EARLY_DAYS)
    ph["reason"] = np.select([~ph.quality_ok, ~ph.rabi_point, ~ph.est], ["season quality", "not a rabi point",
                                                                        "not established"], "ok")
    ph.to_csv(OUT / "labels.csv", index=False)
    t = ph.groupby(["season", "reason"]).size().unstack(fill_value=0)
    t["early_share_of_ok"] = ph[ph.reason == "ok"].groupby("season").early.mean().round(3)
    print(t.to_string())


if __name__ == "__main__":
    main()
