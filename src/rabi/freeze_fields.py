"""
Freeze the monitored field list (protocol v1): the sampled candidates of script C1 v2, i.e. the
fields of the Earth Engine asset rabi_candidates_v2 that script C2 follows (their IDs = the field_ids in
C2_candidate_timeseries_v2.csv). Selection reasons come from the C1 v2 GeoJSON exports.
Note: the GeoJSON 'sampled' flag differs from the asset at Ped and Pul (the seeded random draw ran on a
differently ordered collection in the separate export tasks); the asset is authoritative.

    python src/rabi/freeze_fields.py
Writes data/frozen/fields_v1.csv (+ prints its SHA-256, recorded in docs/PROTOCOL_v1.md).
Every frozen field is followed in every season, also when it stays empty (that is the signal).
"""
from __future__ import annotations

import hashlib
import json

import pandas as pd

from protocol import FROZEN, ROOT, SITES

KEEP = ["field_id", "site", "site_code", "class", "irrigated", "area_ha", "pixels", "n_active_seasons",
        "n_observed_seasons", "geojson_sampled"] + [f"{k}_{y}" for k in ("active", "obs", "jm_ndvi", "rise") for y in range(2019, 2023)]


def main():
    rows = []
    for s in SITES:
        g = json.loads((ROOT / "data" / "gee_exports" / f"C1v2_candidates_{s}.geojson").read_text(encoding="utf-8"))
        rows += [f["properties"] for f in g["features"]]
    asset_ids = set(pd.read_csv(ROOT / "data" / "gee_exports" / "C2_candidate_timeseries_v2.csv",
                                usecols=["field_id"]).field_id)
    d = pd.DataFrame(rows)
    d["geojson_sampled"] = d.pop("sampled")
    d = d[d.field_id.isin(asset_ids)]
    assert len(d) == len(asset_ids), "asset field missing from the GeoJSON candidates"
    d["class"] = d.irrigated.map({0: "rainfed", 1: "irrigated"})
    d = d[KEEP].sort_values(["site_code", "class", "field_id"])
    for c in d.select_dtypes("float").columns:
        d[c] = d[c].round(4)
    FROZEN.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(FROZEN, index=False, lineterminator="\n")
    print(d.groupby(["site_code", "class"]).size().unstack(fill_value=0).reindex(SITES).fillna(0).astype(int))
    print(len(d), "fields; sha256", hashlib.sha256(FROZEN.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
