"""
Development check of protocol v1 on rabi 2023-24, 2024-25, 2025-26 against the AP rabi orders.
RETROSPECTIVE: these seasons were known when the project was designed (their declarations motivated
it), so this describes the rule; it is NOT an independent test. The test is rabi 2026-27.

    python src/rabi/dev_check.py
Writes results/dev_check/{units,sites,mandals}_<issue>.csv and DEV_CHECK.md
"""
from __future__ import annotations

import re

import pandas as pd

import protocol as P

OUT = P.ROOT / "results" / "dev_check"
DEV_SEASONS = [2023, 2024, 2025]


def outcomes() -> pd.DataFrame:
    """Official rabi status per mandal and season (Sira = Unknown, not scored)."""
    d = pd.read_csv(P.DECL)
    rows = []
    for r in d.itertuples():
        st = r.status
        if r.site_code == "Ped":                      # pin on the Adoni side of the border
            m = re.search(r"(Severe|Moderate|Not declared) \(Adoni\)", st)
            st = m.group(1) if m else st
        rows.append(dict(season=r.year, mandal=P.SITE_MANDAL[r.site_code], official=st, order_date=r.order_date))
    return pd.DataFrame(rows).drop_duplicates(["season", "mandal"])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    obs = P.load_obs()
    seasons = P.REF_SEASONS + DEV_SEASONS
    off = outcomes()
    lines = ["# Protocol v1 - development check (retrospective, NOT a test)", "",
             "Rules: docs/PROTOCOL_v1.md (src/rabi/protocol.py), frozen before this check was run. "
             "Reference seasons 2019-22 are scored leave-one-season-out (no declarations: shown as the "
             "false-flag background). 2023-24 .. 2025-26 were known while designing the project.", ""]
    for md in P.ISSUE_DAYS:
        tag = f"{md[0]:02d}-{md[1]:02d}"
        units, sites, mand = P.run(obs, seasons, md)
        for name, t in (("units", units), ("sites", sites), ("mandals", mand)):
            t.round(3).to_csv(OUT / f"{name}_{tag}.csv", index=False)
        m = mand.merge(off, on=["season", "mandal"], how="left")
        m["issue"] = [P.issue_date(s, md).date() for s in m.season]
        dev = m[m.season.isin(DEV_SEASONS)]
        ref_units = units[units.season.isin(P.REF_SEASONS) & (units.status != "INSUFFICIENT")]
        role = {(2, 15): "PRIMARY", (3, 15): "secondary", (1, 15): "informational"}[md]
        lines += [f"## Issue {md[1]} {pd.Timestamp(2000, md[0], 1):%b} ({role})", "",
                  f"Reference seasons: {(ref_units.status == 'FLAG').sum()} of {len(ref_units)} valid "
                  f"site-class units flagged ({(ref_units.status == 'WET-DELAY').sum()} wet-delay).", ""]
        sc = []
        for lvl in ["Severe", "Moderate", "Not declared"]:
            g = dev[(dev.official == lvl)]
            v = g[g.status != "INSUFFICIENT"]
            sc.append(dict(official=lvl, mandal_seasons=len(g), insufficient=len(g) - len(v),
                           flagged=f"{(v.status == 'FLAG').sum()}/{len(v)}"))
        lines += [P.md_table(pd.DataFrame(sc)), "",
                  P.md_table(dev[["season", "mandal", "official", "order_date", "issue", "status", "sites"]]), ""]
        u = units[units.season.isin(DEV_SEASONS) & (units.status != "INSUFFICIENT")]
        lines += ["Units (site x class):", "",
                  P.md_table(u[["season", "site_code", "cls", "evaluable", "established", "share", "normal_share",
                              "est_ratio", "sep_nov_rain_ratio", "cond_fields", "cond_median", "status"]].round(2)), ""]
    (OUT / "DEV_CHECK.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
