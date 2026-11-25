"""
Rabi drought v2 - association of completed-season district indicators with independent crop outcomes
(district rabi yield index and sown-area anomalies, APY statistics). Retrospective monitoring check,
not a forecast and not field-level validation.

Pre-specified (docs/DROUGHT2_v1.md): expected sign negative for DD/DDS/RUN (more deficit -> lower yield
and sown area) and positive for PCT/SOW/rain ratios. Development seasons 2000-01..2010-11, evaluation
2011-12..2022-23. District-season rows; 3 districts share each season, so uncertainty resamples whole
seasons. Tumkur (very small, erratic rabi area) is reported separately and excluded from the primary pool.

    python -B -m src.drought2.validate
Writes results/drought2_v1/validation_*.csv and VALIDATION.md
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "rabi"))
from protocol import md_table  # noqa: E402

D2 = Path(os.environ.get("DROUGHT2_DATA", ROOT / "data" / "drought2"))   # override for sensitivity runs
OUT = Path(os.environ.get("DROUGHT2_RESULTS", ROOT / "results" / "drought2_v1"))
DEV, EVAL = range(2000, 2011), range(2011, 2023)
PRIMARY = ["Kurnool", "Anantapur"]
INDICATORS = {"DD": -1, "DDS": -1, "RUN": -1, "PCT": 1, "SOW": 1, "rain_jun_nov_ratio": 1, "rain_nov_feb_ratio": 1}
OUTCOMES = ["yield_index", "sown_area_anom"]
NB, SEED = 2000, 2026


def within_rank(df, col):
    return df.groupby("district")[col].rank(pct=True)


def pooled_rho(df, ind, out):
    q = df.dropna(subset=[ind, out])
    if len(q) < 6:
        return np.nan, len(q)
    return spearmanr(within_rank(q, ind), within_rank(q, out)).correlation, len(q)


def boot_ci(df, ind, out):
    seasons = df.season.unique()
    rng = np.random.default_rng(SEED)
    vals = []
    for _ in range(NB):
        pick = rng.choice(seasons, len(seasons))
        b = pd.concat([df[df.season == s].assign(season=f"{s}_{i}") for i, s in enumerate(pick)])
        r, _ = pooled_rho(b, ind, out)
        if not np.isnan(r):
            vals.append(r)
    return (np.percentile(vals, 2.5), np.percentile(vals, 97.5)) if vals else (np.nan, np.nan)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    si = pd.read_csv(D2 / "season_indicators.csv")
    y = pd.read_csv(D2 / "yields_district.csv")
    df = si.merge(y, on=["district", "season"], how="inner")
    df = df[df.season.isin(list(DEV) + list(EVAL))]
    rows = []
    for period, seasons in (("development 2000-10", DEV), ("evaluation 2011-22", EVAL), ("all 2000-22", range(2000, 2023))):
        p = df[df.season.isin(seasons) & df.district.isin(PRIMARY)]
        for out in OUTCOMES:
            for ind, sign in INDICATORS.items():
                r, n = pooled_rho(p, ind, out)
                lo, hi = boot_ci(p, ind, out) if period != "development 2000-10" else (np.nan, np.nan)
                rows.append(dict(period=period, outcome=out, indicator=ind, expected_sign="-" if sign < 0 else "+",
                                 n=n, seasons=p.season.nunique(), rho=r, ci_lo=lo, ci_hi=hi,
                                 sign_as_expected=bool(np.sign(r) == sign) if not np.isnan(r) else None))
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "validation_pooled.csv", index=False)

    per = []
    for dist, q in df.groupby("district"):
        for out in OUTCOMES:
            for ind in INDICATORS:
                qq = q.dropna(subset=[ind, out])
                per.append(dict(district=dist, outcome=out, indicator=ind, n=len(qq),
                                rho=spearmanr(qq[ind], qq[out]).correlation if len(qq) >= 6 else np.nan))
    per = pd.DataFrame(per)
    per.to_csv(OUT / "validation_by_district.csv", index=False)

    crop = pd.read_csv(D2 / "yields_crop.csv").merge(si, on=["district", "season"])
    crop = crop[crop.season.isin(range(2000, 2023)) & crop.district.isin(PRIMARY)]
    cr = []
    for (dist, c), q in crop.groupby(["district", "crop"]):
        qq = q.dropna(subset=["DD", "yield_anom"])
        cr.append(dict(district=dist, crop=c, weight=q.weight.iloc[0], n=len(qq),
                       rho_DD_yield=spearmanr(qq.DD, qq.yield_anom).correlation if len(qq) >= 6 else np.nan,
                       rho_DD_area=spearmanr(qq.DD, qq.area_anom).correlation if qq.area_anom.notna().sum() >= 6 else np.nan))
    cr = pd.DataFrame(cr)
    cr.to_csv(OUT / "validation_by_crop.csv", index=False)

    # high-deficit seasons vs others (DD top tercile within district, all years)
    p = df[df.district.isin(PRIMARY)].copy()
    p["dd_high"] = p.groupby("district").DD.transform(lambda s: s >= s.quantile(2 / 3))
    contrast = p.groupby("dd_high")[["yield_index", "sown_area_anom"]].mean().round(3)

    def t(frame):
        return md_table(frame.round(3))
    lines = ["# Rabi drought v2 - indicator vs independent crop outcomes (retrospective)", "",
             "District-season rows (Kurnool and Anantapur on pre-2022 boundaries; APY rabi statistics). "
             "Within-district rank correlation (Spearman) pooled over both districts; 95 % interval by resampling "
             "whole seasons. Outcomes are impacts with other causes (prices, pests, irrigation, reporting), not "
             "drought labels. Development 2000-10 was inspected while building the indicators; evaluation 2011-22 "
             "was not used for any choice, but the soil product and yield series were downloaded together.", "",
             "## Pooled (Kurnool + Anantapur)", "", t(res), "",
             "## By district (all 2000-22 seasons)", "", t(per.pivot_table(index=["outcome", "indicator"],
                                                                         columns="district", values="rho").reset_index()), "",
             "## By crop (DD vs each crop's yield and area anomaly, 2000-22)", "", t(cr), "",
             "## Seasons in the top third of deficit duration vs the rest (primary districts)", "",
             t(contrast.reset_index()), ""]
    (OUT / "VALIDATION.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
