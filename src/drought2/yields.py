"""
District rabi crop outcomes (impact measures, not drought labels) from the Ministry of Agriculture
area-production-yield (APY) statistics, 1997-98 .. 2022-23.

- Districts on pre-2022 boundaries: Kurnool (+ Nandyal 2022-23), Anantapur (+ Sri Sathya Sai 2022-23), Tumkur.
- Season "Rabi" only. Crops: those with >= 5 % of the district's mean rabi area in the reference
  period 1997-98 .. 2009-10 (fixed list, fixed area weights).
- Per crop: yield = production / area; anomaly = yield / median of the 5 previous seasons - 1
  (causal, no future data, no fitted trend). Secondary: linear trend fitted on 1997-2009 only.
- Aggregate yield index = fixed reference-area-weighted mean of available crop anomalies
  (weights renormalised over crops reported that season; coverage reported).
- Sown-area anomaly (separate outcome): total rabi area of the fixed crops / previous-5-season median - 1.

    python -B -m src.drought2.yields
Writes data/drought2/yields_crop.csv, data/drought2/yields_district.csv
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
APY = ROOT / "data" / "external" / "apy" / "apy.csv"
OUT = ROOT / "data" / "drought2"
MAP = {("Andhra Pradesh", "Kurnool"): "Kurnool", ("Andhra Pradesh", "Nandyal"): "Kurnool",
       ("Andhra Pradesh", "Ananthapuramu"): "Anantapur", ("Andhra Pradesh", "Sri Sathya Sai"): "Anantapur",
       ("Karnataka", "Tumakuru"): "Tumkur"}
REF = range(1997, 2010)          # reference / development seasons for crop list, weights and trend
MIN_SHARE = 0.05


def load():
    d = pd.read_csv(APY)
    d["district"] = [MAP.get((s, n)) for s, n in zip(d.state_name, d.district_name)]
    d = d[d.district.notna() & (d.season.str.strip().str.lower() == "rabi")].copy()
    d["season"] = d.year.str[:4].astype(int)
    g = d.groupby(["district", "season", "crop_name"])[["area", "production"]].sum(min_count=1).reset_index()
    g = g[g.area > 0]
    g["yield"] = g.production / g.area
    return g


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = load()
    ref = g[g.season.isin(REF)]
    share = ref.groupby(["district", "crop_name"]).area.mean() / ref.groupby("district").area.sum().div(
        ref.groupby("district").season.nunique())
    crops = share[share >= MIN_SHARE].rename("weight").reset_index()
    crops["weight"] = crops.weight / crops.groupby("district").weight.transform("sum")
    g = g.merge(crops, on=["district", "crop_name"])
    rows = []
    for (dist, crop), q in g.groupby(["district", "crop_name"]):
        q = q.set_index("season").sort_index()
        yr = q["yield"]
        base = yr.rolling(5, min_periods=3).median().shift(1)
        refq = q.loc[q.index.isin(REF)]
        coef = np.polyfit(refq.index, refq["yield"], 1) if len(refq) >= 8 else (np.nan, np.nan)
        trend = np.polyval(coef, q.index)
        abase = q.area.rolling(5, min_periods=3).median().shift(1)
        for s in q.index:
            rows.append(dict(district=dist, crop=crop, season=s, weight=q.weight.iloc[0], area=q.area[s],
                             production=q.production[s], yield_t_ha=yr[s],
                             yield_anom=yr[s] / base[s] - 1 if base[s] > 0 else np.nan,
                             yield_anom_trend=yr[s] / trend[list(q.index).index(s)] - 1,
                             area_anom=q.area[s] / abase[s] - 1 if abase[s] > 0 else np.nan))
    c = pd.DataFrame(rows)
    c.to_csv(OUT / "yields_crop.csv", index=False)

    def agg(q):
        ok = q[q.yield_anom.notna()]
        w = ok.weight / ok.weight.sum() if len(ok) else ok.weight
        okt = q[q.yield_anom_trend.notna()]
        wt = okt.weight / okt.weight.sum() if len(okt) else okt.weight
        return pd.Series(dict(yield_index=(w * ok.yield_anom).sum() if len(ok) else np.nan,
                              yield_index_trend=(wt * okt.yield_anom_trend).sum() if len(okt) else np.nan,
                              weight_coverage=ok.weight.sum(), crops=len(ok), rabi_area=q.area.sum()))
    dd = c.groupby(["district", "season"]).apply(agg).reset_index()
    for dist, q in dd.groupby("district"):
        base = q.set_index("season").rabi_area.rolling(5, min_periods=3).median().shift(1)
        dd.loc[q.index, "sown_area_anom"] = (q.set_index("season").rabi_area / base - 1).to_numpy()
    dd.to_csv(OUT / "yields_district.csv", index=False)
    (OUT / "apy_source.txt").write_text(
        "Ministry of Agriculture & Farmers Welfare, Crop Statistics (district x season x crop APY), via India Data "
        "Portal CKAN resource f980409d-49a2-42ae-9eb0-182365005c04, accessed 2026-11-23.\nsha256 "
        + hashlib.sha256(APY.read_bytes()).hexdigest() + "\n", encoding="utf-8")
    print(crops.to_string(index=False))
    print(dd.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
