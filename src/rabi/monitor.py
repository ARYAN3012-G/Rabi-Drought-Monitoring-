"""
Live rabi monitoring (protocol v1): status of every site on an issue date.

    python src/rabi/monitor.py --date 2027-02-15
Uses only Sentinel-2 images dated <= date - 2 days (C2_candidate_timeseries_v2.csv: rerun script C2 in
Earth Engine and download it first) and the weather module's AgERA5 files for the wet guard
(run tools/update_agera5.py + prepare_data in the weather module so Sep-Nov is complete).
Writes results/monitor/<date>/{STATUS.md, units.csv, sites.csv, mandals.csv}. Commit each report on
the day it is made: the commit date proves the status was issued live.
"""
from __future__ import annotations

import argparse

import pandas as pd

import protocol as P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    a = ap.parse_args()
    d = pd.Timestamp(a.date)
    season = d.year if d.month >= 10 else d.year - 1
    md = (d.month, d.day)
    obs = P.load_obs()
    last = obs.date.max()
    used = obs[obs.date <= d - pd.Timedelta(days=P.SAT_DELAY_DAYS)].date.max()
    units, sites, mand = P.run(obs, [season], md)
    out = P.ROOT / "results" / "monitor" / str(d.date())
    out.mkdir(parents=True, exist_ok=True)
    for name, t in (("units", units), ("sites", sites), ("mandals", mand)):
        t.round(3).to_csv(out / f"{name}.csv", index=False)
    role = {(2, 15): "PRIMARY issue date (scored)", (3, 15): "secondary issue date (scored)"}.get(md, "interim / informational")
    warn = []
    if (d - used).days > 12:
        warn.append(f"WARNING: newest usable image is {used.date()} ({(d - used).days} days old) - rerun script C2.")
    if d < pd.Timestamp(season + 1, 1, 1):
        warn.append("Early season: rabi green-up is normally from late December; statuses are preliminary.")
    rain_missing = units.sep_nov_rain_ratio.isna().any()
    if rain_missing:
        warn.append("Sep-Nov rain incomplete for some sites (update AgERA5): wet guard not applied there.")
    show = units[["site_code", "cls", "evaluable", "established", "share", "normal_share", "est_ratio",
                  "sep_nov_rain_ratio", "cond_fields", "cond_median", "status"]].round(2)
    lines = [f"# Rabi {season}-{str(season + 1)[2:]} status on {d.date()} ({role})", "",
             f"Protocol v1. Images used: up to {used.date()} (file ends {last.date()}).", ""] + \
            [f"- {w}" for w in warn] + ["", "## Mandals", "", P.md_table(mand), "",
                                        "## Sites", "", P.md_table(sites), "",
                                        "## Units (site x class)", "", P.md_table(show), ""]
    (out / "STATUS.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
