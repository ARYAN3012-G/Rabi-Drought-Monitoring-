"""
Rabi drought v2 - analyses for the 8-site case-study paper (district scale: Kurnool, Anantapur; Tumkur as
sensitivity). Uses the district ERA5-Land grid indicators, AgERA5 rain/SPEI and APY rabi crop statistics.

1. Monitoring association over all seasons with outcomes (2000-01..2022-23), soil vs rain/SPEI baselines.
2. Early warning: at issue dates 15 Dec / 15 Jan / 15 Feb (inputs <= t-8 d), does the season-so-far indicator
   separate seasons that end with a rabi yield loss (multi-crop index <= -0.15, fixed before analysis)?
   Single indicators need no fitting (AUC of the raw indicator); a 2-variable logistic model is scored by
   leave-one-season-out. 95 % intervals resample whole seasons.
3. Case-study figures: daily district deficit area in dry vs normal seasons; indicator vs yield scatter.

    python -B -m src.drought2.paper
Writes results/drought2_paper/{*.csv, *.png, PAPER_RESULTS.md}
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

warnings.simplefilter("ignore")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "rabi"))
from protocol import md_table  # noqa: E402

D2 = ROOT / "data" / "drought2"
PREP = ROOT / "data" / "prepared"
OUT = ROOT / "results" / "drought2_paper"
PRIMARY = ["Kurnool", "Anantapur"]
CELLS = {"Kurnool": ["Peddakadubur", "kurnool_dinedevarapadu"], "Anantapur": ["Somandepalle", "cholasamudram"],
         "Tumkur": ["sira"]}
LOSS = -0.15
ISSUES = [(12, 15), (1, 15), (2, 15)]
LAG = 8
NB, SEED = 2000, 7
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


def weather():
    out = {}
    for dist, cells in CELLS.items():
        fr = [pd.read_csv(PREP / f"{c}.csv", usecols=["valid_time", "Precipitation_Flux", "SPEI"],
                          parse_dates=["valid_time"]).set_index("valid_time") for c in cells]
        out[dist] = sum(fr) / len(fr)
    return out


def seasonal_weather(wx):
    rows = []
    for dist, w in wx.items():
        r = w.Precipitation_Flux
        n_jn = np.mean([r[f"{y}-06-01":f"{y}-11-30"].sum() for y in range(1979, 2005)])
        n_nf = np.mean([r[f"{y}-11-01":f"{y + 1}-02-28"].sum() for y in range(1979, 2005)])
        for s in range(1990, 2023):
            rows.append(dict(district=dist, season=s, rain_jun_nov=r[f"{s}-06-01":f"{s}-11-30"].sum() / n_jn,
                             rain_nov_feb=r[f"{s}-11-01":f"{s + 1}-02-28"].sum() / n_nf,
                             spei_sow=w.SPEI[f"{s}-10-01":f"{s}-11-30"].mean(),
                             spei_season=w.SPEI[f"{s}-11-01":f"{s + 1}-02-28"].mean()))
    return pd.DataFrame(rows)


def boot_rho(df, a, b):
    seasons = df.season.unique()
    rng = np.random.default_rng(SEED)
    v = []
    for _ in range(NB):
        pick = rng.choice(seasons, len(seasons))
        q = pd.concat([df[df.season == s].assign(season=i) for i, s in enumerate(pick)])
        ra = q.groupby("district")[a].rank(pct=True)
        rb = q.groupby("district")[b].rank(pct=True)
        r = spearmanr(ra, rb).correlation
        if not np.isnan(r):
            v.append(r)
    return np.percentile(v, [2.5, 97.5])


def pooled(df, a, b):
    q = df.dropna(subset=[a, b])
    return spearmanr(q.groupby("district")[a].rank(pct=True), q.groupby("district")[b].rank(pct=True)).correlation, len(q)


def boot_auc(y, s, seasons):
    rng = np.random.default_rng(SEED)
    us = np.unique(seasons)
    v = []
    for _ in range(NB):
        idx = np.concatenate([np.where(seasons == u)[0] for u in rng.choice(us, len(us))])
        if y[idx].min() != y[idx].max():
            v.append(roc_auc_score(y[idx], s[idx]))
    return np.percentile(v, [2.5, 97.5])


def so_far(gp, wx, dist, s, t):
    c = t - pd.Timedelta(days=LAG)
    q = gp[(gp.district == dist) & (gp.date >= pd.Timestamp(s, 11, 1)) & (gp.date <= c)]
    sow = gp[(gp.district == dist) & (gp.date >= pd.Timestamp(s, 10, 1)) & (gp.date < pd.Timestamp(s, 12, 1))]
    w = wx[dist]
    r = w.Precipitation_Flux
    n = np.mean([r[pd.Timestamp(y, 6, 1):pd.Timestamp(y, 6, 1) + (c - pd.Timestamp(s, 6, 1))].sum()
                 for y in range(1979, 2005)])
    return dict(DD_so_far=q.groupby("gid").deficit.mean().mean(), PCT_so_far=q.pct.mean(), SOW=sow.pct.mean(),
                rain_since_jun=r[f"{s}-06-01":c].sum() / n, spei_so_far=w.SPEI[f"{s}-11-01":c].mean())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    si = pd.read_csv(D2 / "season_indicators.csv")
    y = pd.read_csv(D2 / "yields_district.csv")
    wx = weather()
    sw = seasonal_weather(wx)
    df = si.drop(columns=[c for c in si.columns if c.startswith("rain_")]).merge(sw, on=["district", "season"]) \
        .merge(y, on=["district", "season"])
    df = df[df.season.between(2000, 2022)]
    df.to_csv(OUT / "district_seasons.csv", index=False)

    # 1. monitoring association, all seasons
    inds = {"DD": "deficit duration Nov-Feb", "DDS": "severe deficit duration", "SOW": "soil moisture at sowing",
            "PCT": "mean soil percentile Nov-Feb", "rain_jun_nov": "rain Jun-Nov", "rain_nov_feb": "rain Nov-Feb",
            "spei_sow": "SPEI-30 Oct-Nov", "spei_season": "SPEI-30 Nov-Feb"}
    rows = []
    for scope, dists in (("Kurnool + Anantapur", PRIMARY), ("+ Tumkur (sensitivity)", PRIMARY + ["Tumkur"])):
        p = df[df.district.isin(dists)]
        for out in ("yield_index", "sown_area_anom"):
            for k, nm in inds.items():
                r, n = pooled(p, k, out)
                lo, hi = boot_rho(p.dropna(subset=[k, out]), k, out)
                rows.append(dict(scope=scope, outcome=out, indicator=nm, n=n, rho=round(r, 2),
                                 ci=f"[{lo:+.2f}, {hi:+.2f}]"))
    assoc = pd.DataFrame(rows)
    assoc.to_csv(OUT / "association_all_seasons.csv", index=False)

    # 2. early warning of yield-loss seasons
    gp = pd.read_csv(D2 / "grid_percentiles.csv.gz", parse_dates=["date"])
    ew = []
    for r in df[df.district.isin(PRIMARY)].itertuples():
        for (m, d) in ISSUES:
            t = pd.Timestamp(r.season + (1 if m < 9 else 0), m, d)
            f = so_far(gp, wx, r.district, r.season, t)
            ew.append(dict(district=r.district, season=r.season, issue=f"{d} {['Dec', 'Jan', 'Feb'][ISSUES.index((m, d))]}",
                           loss=int(r.yield_index <= LOSS), yield_index=r.yield_index, **f))
    ew = pd.DataFrame(ew)
    ew.to_csv(OUT / "early_warning_rows.csv", index=False)
    erows = []
    for iss, q in ew.groupby("issue", sort=False):
        q = q.dropna(subset=["DD_so_far", "SOW", "rain_since_jun", "spei_so_far"])
        yv, se = q.loss.to_numpy(), q.season.to_numpy()
        for nm, score in (("Soil deficit so far (DD)", q.DD_so_far), ("Soil moisture at sowing (low = risk)", -q.SOW),
                          ("Soil percentile so far (low = risk)", -q.PCT_so_far),
                          ("Rain since June (low = risk)", -q.rain_since_jun), ("SPEI so far (low = risk)", -q.spei_so_far)):
            s = score.to_numpy()
            lo, hi = boot_auc(yv, s, se)
            erows.append(dict(issue=iss, method=nm, n=len(q), loss_seasons=int(yv.sum()), auc=round(roc_auc_score(yv, s), 2),
                              ci=f"[{lo:.2f}, {hi:.2f}]"))
        # LOSO logistic on soil (DD so far + SOW) and on rain baseline
        for nm, feats in (("LOSO logistic: soil (DD so far + SOW)", ["DD_so_far", "SOW"]),
                          ("LOSO logistic: rain + SPEI", ["rain_since_jun", "spei_so_far"])):
            p = np.full(len(q), np.nan)
            for s in np.unique(se):
                tr, te = se != s, se == s
                if yv[tr].min() == yv[tr].max():
                    continue
                m = LogisticRegression(class_weight="balanced").fit(q[feats].to_numpy()[tr], yv[tr])
                p[te] = m.predict_proba(q[feats].to_numpy()[te])[:, 1]
            ok = ~np.isnan(p)
            lo, hi = boot_auc(yv[ok], p[ok], se[ok])
            pred = p[ok] >= 0.5
            tp = int((pred & (yv[ok] == 1)).sum())
            erows.append(dict(issue=iss, method=nm, n=int(ok.sum()), loss_seasons=int(yv[ok].sum()),
                              auc=round(roc_auc_score(yv[ok], p[ok]), 2), ci=f"[{lo:.2f}, {hi:.2f}]",
                              warned=int(pred.sum()), caught=tp))
    early = pd.DataFrame(erows)
    early.to_csv(OUT / "early_warning.csv", index=False)

    # 3. figures
    dd = pd.read_csv(D2 / "daily_district.csv.gz", parse_dates=["date"])
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.4), sharey=True)
    for ax, dist in zip(axs, PRIMARY):
        q = df[df.district == dist].set_index("season")
        dry = q.yield_index.nsmallest(3).index.tolist()
        for s in range(2000, 2023):
            x = dd[(dd.district == dist) & (dd.season == s)]
            x = x[(x.date >= f"{s}-10-01") & (x.date <= f"{s + 1}-03-31")]
            days = (x.date - pd.Timestamp(s, 10, 1)).dt.days
            sm = x.deficit_area.rolling(7, min_periods=1).mean()
            if s in dry:
                ax.plot(days, sm, lw=1.8, label=f"{s}-{str(s + 1)[2:]} (yield {q.yield_index[s]:+.0%})")
            else:
                ax.plot(days, sm, color="#BBBBBB", lw=0.6)
        ax.set_title(f"{dist}: share of district in soil-moisture deficit", fontsize=9)
        ax.set_xticks([0, 31, 61, 92, 123, 151, 182], ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr"])
        ax.legend(fontsize=7, frameon=False, title="3 worst rabi yields", title_fontsize=7)
    axs[0].set_ylabel("Deficit area (7-day mean)")
    fig.tight_layout()
    fig.savefig(OUT / "fig_deficit_seasons.png", dpi=250)
    plt.close(fig)

    fig, axs = plt.subplots(1, 2, figsize=(9, 3.4))
    for ax, (x, out, lab) in zip(axs, (("DD", "yield_index", "Rabi yield index"),
                                       ("DD", "sown_area_anom", "Rabi sown-area anomaly"))):
        for dist, mk in zip(PRIMARY, ("o", "s")):
            q = df[df.district == dist]
            ax.scatter(q[x], q[out], marker=mk, s=22, label=dist, alpha=0.8)
            for r in q[q[out] <= q[out].nsmallest(2).max()].itertuples():
                ax.annotate(f"{r.season}-{str(r.season + 1)[2:]}", (getattr(r, x), getattr(r, out)), fontsize=6)
        ax.axhline(0, color="#999999", lw=0.6)
        ax.set_xlabel("Soil-moisture deficit duration (share of Nov-Feb days)")
        ax.set_ylabel(lab)
    axs[0].legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "fig_dd_vs_outcomes.png", dpi=250)
    plt.close(fig)

    lines = ["# Rabi drought v2 - results for the 8-site case-study paper", "",
             "Districts of the 8 study sites (pre-2022 boundaries); Kurnool + Anantapur primary, Tumkur sensitivity. "
             "Outcomes: APY rabi multi-crop yield index (fixed weights, causal 5-season baseline) and sown-area anomaly. "
             "Seasons 2000-01..2022-23. Within-district Spearman rank correlation; 95 % intervals resample whole seasons. "
             "District statistics are impacts with other causes, not drought labels; this is district association, "
             "not field validation.", "",
             "## 1. Monitoring: completed-season indicators vs crop outcomes (all seasons)", "", md_table(assoc), "",
             f"## 2. Early warning of rabi yield-loss seasons (yield index <= {LOSS:+.0%}, fixed before analysis)", "",
             "Indicators use inputs up to 8 days before the issue date. Single indicators: AUC of the raw value (no "
             "fitting). Logistic models: leave-one-season-out. Rows are district-seasons; districts share seasons.", "",
             md_table(early.fillna("")), "",
             "## 3. Figures", "", "- fig_deficit_seasons.png - daily district deficit area; 3 worst yield seasons highlighted",
             "- fig_dd_vs_outcomes.png - deficit duration vs yield index and sown-area anomaly", ""]
    (OUT / "PAPER_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
