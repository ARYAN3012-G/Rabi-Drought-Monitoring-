"""
EXPLORATORY (added 21 Nov 2026 AFTER seeing the 2023-26 development check; not part of protocol v1):
signal 3 "early drying" (terminal drought) - does the rabi crop dry earlier than its own normal?

Per field and season (Oct y .. Apr y+1), retrospective (whole season):
  NDVI series = 3-image rolling median of the clean observations
  trough T = min of Oct-Dec, peak P = max after T (Dec - Mar), field "established" if P - T >= 0.15, P > 0.35
  half = T + 0.5 (P - T)
  green-up date  = first date after T's date with NDVI >= half
  drying date    = first date after the peak with NDVI < half   (search until 30 Apr)
  green length   = drying date - green-up date
Field normal = mean drying date (day of season) over the reference seasons 2019-22 in which it was established
(leave-one-season-out for reference seasons, >= 2 seasons). Delta = drying date - normal (negative = earlier).
Site x class: median delta over >= 5 fields; "EARLY" if median <= -14 days.

    python src/rabi/explore_early_drying.py
Writes results/explore_early_drying/{fields.csv, units.csv, EARLY_DRYING.md}
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import protocol as P

OUT = P.ROOT / "results" / "explore_early_drying"
SEASONS = list(range(2019, 2026))
EARLY_DAYS, MIN_FIELDS = -14, 5


def field_season(g: pd.DataFrame, season: int) -> dict:
    s0 = pd.Timestamp(season, 10, 1)
    w = g[(g.date >= s0) & (g.date <= pd.Timestamp(season + 1, 4, 30))].sort_values("date")
    if len(w) < 10:
        return {}
    v = w.NDVI.rolling(3, center=True, min_periods=2).median().to_numpy()
    d = w.date.to_numpy()
    early = w.date < pd.Timestamp(season, 12, 31)
    if early.sum() < 3:
        return {}
    ti = int(np.nanargmin(np.where(early, v, np.nan)))
    after = np.arange(len(v)) > ti
    win = after & (w.date <= pd.Timestamp(season + 1, 3, 31)).to_numpy()
    if not win.any():
        return {}
    pi = int(np.nanargmax(np.where(win, v, np.nan)))
    t, p = v[ti], v[pi]
    est = (p - t >= P.RISE) and (p > P.GREEN)
    out = dict(season=season, trough=t, peak=p, established=est, peak_date=pd.Timestamp(d[pi]))
    if not est:
        return out
    half = t + 0.5 * (p - t)
    up = [i for i in range(ti + 1, pi + 1) if v[i] >= half]
    dn = [i for i in range(pi + 1, len(v)) if v[i] < half]
    if up:
        out["greenup_date"] = pd.Timestamp(d[up[0]])
    if dn:
        out["drying_date"] = pd.Timestamp(d[dn[0]])
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    obs = P.load_obs()
    fr = pd.read_csv(P.FROZEN)[["field_id", "site_code", "class"]].rename(columns={"class": "cls"})
    rows = []
    for fid, g in obs.groupby("field_id"):
        for s in SEASONS:
            r = field_season(g, s)
            if r:
                rows.append(dict(field_id=fid, **r))
    f = pd.DataFrame(rows).merge(fr, on="field_id")
    for c in ("greenup_date", "drying_date", "peak_date"):
        f[c + "_doy"] = (f[c] - pd.to_datetime(f.season.astype(str) + "-10-01")).dt.days   # day of season
    f["green_days"] = f.drying_date_doy - f.greenup_date_doy
    ok = f[f.established & f.drying_date_doy.notna()]
    # leave-one-season-out field normal of the drying day
    deltas = []
    for r in ok.itertuples():
        ref = ok[(ok.field_id == r.field_id) & ok.season.isin(P.REF_SEASONS) & (ok.season != r.season)]
        deltas.append(r.drying_date_doy - ref.drying_date_doy.mean() if len(ref) >= 2 else np.nan)
    ok = ok.assign(delta_days=deltas)
    f = f.merge(ok[["field_id", "season", "delta_days"]], on=["field_id", "season"], how="left")
    f.to_csv(OUT / "fields.csv", index=False)

    u = (ok.dropna(subset=["delta_days"]).groupby(["season", "site_code", "cls"])
         .agg(fields=("delta_days", "size"), median_delta_days=("delta_days", "median"),
              median_green_days=("green_days", "median"),
              median_drying=("drying_date", lambda x: x.median().strftime("%d %b"))).reset_index())
    u = u[u.fields >= MIN_FIELDS]
    u["early"] = u.median_delta_days <= EARLY_DAYS
    u.to_csv(OUT / "units.csv", index=False)

    site = u.groupby(["season", "site_code"]).agg(
        early=("early", "any"), detail=("cls", lambda s: ", ".join(
            f"{c}: {d:+.0f} d" for c, d in zip(s, u.loc[s.index, "median_delta_days"])))).reset_index()
    site["mandal"] = site.site_code.map(P.SITE_MANDAL)
    wide = site.pivot_table(index="site_code", columns="season", values="detail", aggfunc="first").reindex(P.SITES)
    flags = site[site.early].groupby("season").site_code.apply(", ".join)

    lines = ["# Exploratory: early drying of rabi crops (terminal drought)", "",
             "Added after the 2023-26 development check; not part of protocol v1; whole-season (retrospective) "
             "dates. Delta = field's drying date minus its own 2019-22 normal (leave-one-season-out), median per "
             f"site x class (>= {MIN_FIELDS} fields). EARLY = median <= {EARLY_DAYS} days.", "",
             "## Median shift of the drying date (days; negative = dries earlier than normal)", "",
             P.md_table(wide.reset_index().fillna("")), "",
             "## Sites with early drying", "",
             P.md_table(flags.reindex(SEASONS).fillna("-").rename("sites EARLY").reset_index()), "",
             "## Units", "", P.md_table(u.round(1)), ""]
    (OUT / "EARLY_DRYING.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
