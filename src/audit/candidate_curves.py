"""
Candidate audit, part 2: October - April NDVI curves of the 320 sampled candidates (script C2).

What do the "historically winter-active" candidates look like inside the winter?
  rabi-like     a dip (Oct - Dec) followed by a rise of >= RISE into a Dec - Mar peak (sown in the season)
  kharif tail   highest in Oct - Nov, falls by >= RISE by Feb - Mar, no such rise (kharif crop drying)
  flat green    green through the winter (monthly min > FLAT_MIN) with no rise or fall of >= RISE
  other         anything else / too few months
Shapes are judged per field and season on monthly medians, REFERENCE seasons 2019-20 .. 2022-23 only
(the seasons C1 selected on). Later seasons are summarised separately, for information.

    python src/audit/candidate_curves.py [v1|v2]
Reads  data/gee_exports/C2_candidate_timeseries.csv
Writes results/audit/<version>/{monthly_ndvi.csv, shapes_field_season.csv, shapes_field.csv,
                      CANDIDATE_CURVES.md, curves_by_site.png, curves_by_shape.png}
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
import sys
VER = sys.argv[1] if len(sys.argv) > 1 else "v1"          # v1: first C1 run, v2: rise rule
TS = ROOT / "data" / "gee_exports" / ("C2_candidate_timeseries.csv" if VER == "v1" else f"C2_candidate_timeseries_{VER}.csv")
OUT = ROOT / "results" / "audit" / VER
SITES = ["Som", "Lep", "Cho", "Sira", "Ped", "Din", "Bal", "Pul"]
REF = [2019, 2020, 2021, 2022]
MONTHS = [10, 11, 12, 1, 2, 3, 4]                 # season order Oct .. Apr
MLAB = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr"]
MIN_CLEAR = 0.6                                   # as the satellite module (clear fraction of the field)
RISE, FLAT_MIN, MIN_MONTHS = 0.15, 0.30, 5
COL = {"rainfed": "#eb6834", "irrigated": "#2a78d6"}  # categorical slots 2 / 1
INK, MUTED, GRID = "#2b2b29", "#6b6a64", "#e4e3de"


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Clear-fraction filter (vs each field's clearest image up to the end of the reference period),
    NDVI range, one value per field and day (the clearest)."""
    d = raw.rename(columns=lambda c: c[:-5] if c.endswith("_mean") else c).copy()
    full = d[d.date < "2023-05-01"].groupby("field_id").NDVI_count.max()
    d["clear_frac"] = (d.NDVI_count / d.field_id.map(full)).clip(upper=1)
    d = d[(d.clear_frac >= MIN_CLEAR) & d.NDVI.between(-0.2, 1.0)]
    return d.sort_values("clear_frac").drop_duplicates(["field_id", "date"], keep="last")


def monthly(d: pd.DataFrame) -> pd.DataFrame:
    d = d[d.date.dt.month.isin(MONTHS)].copy()
    d["season"] = d.date.dt.year - (d.date.dt.month <= 4).astype(int)
    d["month"] = d.date.dt.month
    m = d.groupby(["field_id", "season", "month"]).NDVI.median().unstack("month")
    return m.reindex(columns=MONTHS)


def shape(r: pd.Series) -> str:
    v = r[MONTHS].to_numpy(float)
    if np.isfinite(v).sum() < MIN_MONTHS:
        return "other"
    early, win = v[:3], v[2:6]                    # Oct-Dec ; Dec-Mar
    if np.isfinite(early).any() and np.isfinite(win).any():
        t = int(np.nanargmin(early))
        after = v[t + 1:6]
        if np.isfinite(after).any() and np.nanmax(after) - early[t] >= RISE:
            return "rabi-like"
    start, late = np.nanmax(v[:2]) if np.isfinite(v[:2]).any() else np.nan, v[4:6]
    if np.isfinite(start) and np.isfinite(late).any() and start - np.nanmin(late) >= RISE:
        return "kharif tail"
    if np.nanmin(v) > FLAT_MIN and np.nanmax(v) - np.nanmin(v) < RISE:
        return "flat green"
    return "other"


def md(t: pd.DataFrame) -> str:
    t = t.reset_index()
    rows = ["| " + " | ".join(map(str, t.columns)) + " |", "|" + "---|" * len(t.columns)]
    return "\n".join(rows + ["| " + " | ".join(str(v) for v in r) + " |" for r in t.itertuples(index=False)])


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8, length=0)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def plot_sites(m: pd.DataFrame, path: Path):
    fig, axes = plt.subplots(2, 4, figsize=(13, 6), sharex=True, sharey=True)
    x = np.arange(len(MONTHS))
    for ax, s in zip(axes.flat, SITES):
        for cl, c in COL.items():
            g = m[(m.site_code == s) & (m["class"] == cl) & m.season.isin(REF)][MONTHS]
            q = g.quantile([0.25, 0.5, 0.75])
            ax.fill_between(x, q.loc[0.25], q.loc[0.75], color=c, alpha=0.15, lw=0)
            ax.plot(x, q.loc[0.5], color=c, lw=2, marker="o", ms=4, label=cl)
        ax.set_title(s, fontsize=10, color=INK, loc="left")
        ax.axhline(0.35, color=MUTED, lw=0.8, ls=":")
        style(ax)
    for ax in axes[1]:
        ax.set_xticks(x, MLAB)
    for ax in axes[:, 0]:
        ax.set_ylabel("NDVI (monthly median)", fontsize=8, color=MUTED)
    axes[0, 0].legend(frameon=False, fontsize=8, loc="upper right")
    fig.suptitle("Sampled winter-active candidates, Oct - Apr, reference seasons 2019-20 .. 2022-23 "
                 "(line = median field, band = middle half; dotted = C1 green threshold 0.35)",
                 fontsize=10, color=INK, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_shapes(m: pd.DataFrame, path: Path):
    shapes = ["rabi-like", "kharif tail", "flat green", "other"]
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.4), sharey=True)
    x = np.arange(len(MONTHS))
    r = m[m.season.isin(REF)]
    for ax, sh in zip(axes, shapes):
        g = r[r.curve == sh]
        for _, row in g.sample(min(len(g), 60), random_state=0).iterrows():
            ax.plot(x, row[MONTHS].to_numpy(float), color=COL[row["class"]], lw=0.6, alpha=0.35)
        ax.plot(x, g[MONTHS].median(), color=INK, lw=2.2)
        ax.set_title(f"{sh}  ({len(g)} field-seasons)", fontsize=10, color=INK, loc="left")
        ax.set_xticks(x, MLAB)
        style(ax)
    axes[0].set_ylabel("NDVI (monthly median)", fontsize=8, color=MUTED)
    fig.suptitle("Curve shapes (thin: up to 60 field-seasons each, orange rainfed / blue irrigated; "
                 "thick: median)", fontsize=10, color=INK, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(TS, parse_dates=["date"])
    static = raw.groupby("field_id")[["site_code", "irrigated", "area_ha"]].first()
    static["class"] = static.irrigated.map({0: "rainfed", 1: "irrigated"})
    d = clean(raw)
    m = monthly(d).reset_index()
    m["curve"] = m.apply(shape, axis=1)
    m = m.join(static, on="field_id")
    m.to_csv(OUT / "shapes_field_season.csv", index=False)

    ref = m[m.season.isin(REF)]
    share = (pd.crosstab([ref.site_code, ref["class"]], ref.curve, normalize="index") * 100).round(0)
    share = share.reindex(SITES, level=0).astype(int)
    allc = (pd.crosstab(ref["class"], ref.curve, normalize="index") * 100).round(0).astype(int)

    f = ref.assign(rabi=ref.curve.eq("rabi-like"), tail=ref.curve.eq("kharif tail"),
                   flat=ref.curve.eq("flat green")).groupby("field_id")[["rabi", "tail", "flat"]].sum()
    f = f.join(static)
    f["field_type"] = np.select([f["rabi"] >= 2, f["flat"] >= 2, f["tail"] >= 2],
                                ["rabi-like (>=2 seasons)", "flat green (>=2)", "kharif tail (>=2)"], "mixed")
    f.to_csv(OUT / "shapes_field.csv")
    ft = pd.crosstab([f.site_code, f["class"]], f.field_type).reindex(SITES, level=0)
    ft_all = pd.crosstab(f["class"], f.field_type)

    later = m[~m.season.isin(REF) & (m.season <= 2025)]
    lat = (pd.crosstab([later["class"], later.season], later.curve, normalize="index") * 100).round(0).astype(int)
    obs = d.assign(season=d.date.dt.year - (d.date.dt.month <= 4).astype(int))
    obs = obs[obs.date.dt.month.isin(MONTHS) & obs.season.isin(REF)].groupby(["field_id", "season"]).size()

    plot_sites(m, OUT / "curves_by_site.png")
    plot_shapes(m, OUT / "curves_by_shape.png")

    lines = ["# Candidate audit, part 2: October - April curves of the sampled candidates", "",
             f"C2 export: {raw.field_id.nunique()} fields, {len(raw)} rows, images "
             f"{raw.date.min():%Y-%m-%d} .. {raw.date.max():%Y-%m-%d}. After cleaning (>= {MIN_CLEAR:.0%} clear, one "
             f"image per day): {len(d)} rows. Clear images per field and reference season (Oct - Apr): median "
             f"{obs.median():.0f}, min {obs.min()}.", "",
             "Shapes (monthly medians, per field and season): **rabi-like** = dip in Oct - Dec then a rise of "
             f">= {RISE} by Mar; **kharif tail** = highest in Oct - Nov, falls >= {RISE} by Feb - Mar; **flat green** "
             f"= above {FLAT_MIN} all winter, no rise/fall of {RISE}; **other** = the rest or < {MIN_MONTHS} months.", "",
             "## Share of field-seasons by shape, reference seasons 2019-20 .. 2022-23 (%)", "", md(allc), "",
             md(share), "", "## Fields by majority shape (number of the 40 sampled per site)", "", md(ft_all), "",
             md(ft), "", "## Later seasons (not used for selection), share of field-seasons (%)", "", md(lat), "",
             "Figures: curves_by_site.png, curves_by_shape.png.", ""]
    (OUT / "CANDIDATE_CURVES.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
