"""
Candidate audit, part 1: what script C1 selected (from its exports only, no new data).

    python src/audit/candidates_summary.py [v1|v2]
Reads  data/gee_exports/C1_stats.csv, C1_candidates_<site>.geojson
Writes results/audit/{candidates_all.csv, CANDIDATES_SUMMARY.md}
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "data" / "gee_exports"
import sys
VER = sys.argv[1] if len(sys.argv) > 1 else "v1"
PFX = "C1" if VER == "v1" else f"C1{VER}"
OUT = ROOT / "results" / "audit" / VER
SITES = ["Som", "Lep", "Cho", "Sira", "Ped", "Din", "Bal", "Pul"]
SEASONS = [2019, 2020, 2021, 2022]


def load() -> pd.DataFrame:
    rows = []
    for s in SITES:
        g = json.loads((EXP / f"{PFX}_candidates_{s}.geojson").read_text(encoding="utf-8"))
        rows += [f["properties"] for f in g["features"]]
    d = pd.DataFrame(rows)
    d["class"] = d.irrigated.map({0: "rainfed", 1: "irrigated"})
    return d


def md(t: pd.DataFrame) -> str:
    t = t.reset_index()
    head = "| " + " | ".join(map(str, t.columns)) + " |"
    sep = "|" + "---|" * len(t.columns)
    body = ["| " + " | ".join(str(v) for v in r) + " |" for r in t.itertuples(index=False)]
    return "\n".join([head, sep] + body)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = load()
    d.drop(columns=["label"], errors="ignore").to_csv(OUT / "candidates_all.csv", index=False)
    st = pd.read_csv(EXP / f"{PFX}_stats.csv").set_index("site_code")

    dup = d.field_id.duplicated().sum()
    area = st[["farmland_ha", "candidate_ha", "candidate_rainfed_ha", "candidate_irrigated_ha"]].copy()
    area["candidate_%"] = 100 * area.candidate_ha / area.farmland_ha
    area["rainfed_%_of_cand"] = 100 * area.candidate_rainfed_ha / area.candidate_ha

    cnt = d.pivot_table(index="site_code", columns="class", values="field_id", aggfunc="count", fill_value=0)
    smp = d[d.sampled == 1].pivot_table(index="site_code", columns="class", values="field_id",
                                        aggfunc="count", fill_value=0)
    seg = cnt.add_suffix("_segments").join(smp.add_suffix("_sampled")).reindex(SITES).fillna(0).astype(int)

    s = d[d.sampled == 1].copy()
    s["n_active"] = s.n_active_seasons.round().astype(int)
    for y in SEASONS:
        s[f"act_{y}"] = (s[f"active_{y}"] >= 0.5).astype(int)
    q = s.groupby(["site_code", "class"]).agg(
        fields=("field_id", "count"), area_ha_med=("area_ha", "median"),
        **{f"active_{y}_%": (f"act_{y}", lambda x: round(100 * x.mean())) for y in SEASONS},
        jm_ndvi_2022_med=("jm_ndvi_2022", "median"), min_obs_JanMar=("obs_2019", "min"))
    q = q.reindex(SITES, level=0)
    nact = pd.crosstab([s.site_code, s["class"]], s.n_active).reindex(SITES, level=0)

    lines = ["# Candidate audit, part 1: what script C1 selected", "",
             f"Run 2026-11-21. Segments with selection reasons: {len(d)}; duplicate field_id: {dup}.", "",
             "## Area (hectares, from C1_stats)", "", md(area.round(1)), "",
             "## Segments and sampled fields", "", md(seg), "",
             "## Sampled fields: selection reasons", "",
             "active_<y>_% = share of sampled fields winter-active in season y (Oct y - Apr y+1).", "",
             md(q.round(2)), "", "Number of active seasons (of 4):", "", md(nact), ""]
    (OUT / "CANDIDATES_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
