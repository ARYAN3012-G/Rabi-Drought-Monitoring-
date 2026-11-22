"""
Rabi forecast v1 + amendment A1 - training and chronological evaluation (rules: docs/FORECAST_v1.md).

    python src/forecast/train_eval.py
Writes results/forecast_v1_A1/{predictions.csv.gz, metrics.csv, metrics_dec_mar.csv, FORECAST_RESULTS.md}
(The superseded first run c976795 is in results/forecast_v1.)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rabi"))
from protocol import md_table  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "forecast"
OUT = ROOT / "results" / "forecast_v1_A1"

TRAIN, VAL, TEST = [2019, 2020, 2021], [2022], [2023, 2024, 2025]
XGB = dict(objective="reg:squarederror", max_depth=6, learning_rate=0.05, subsample=0.8,
           colsample_bytree=0.8, random_state=0, tree_method="hist", n_jobs=-1)
MAX_TREES, EARLY = 2000, 50
DROP = -0.10
GREEN, RISE = 0.35, 0.15
N_BOOT, BOOT_SEED = 1000, 12345
SAT = ["ndvi_last", "age_last", "ndvi_15", "age_15", "ndvi_30", "age_30", "chg15", "chg30",
       "season_max", "season_min", "n_obs30", "doy_issue", "irr", "lat", "lon", "clim_target", "clim_last"]
WX = ["rain30", "rain90", "rain_jun_ratio", "et0_15", "tmax_15", "wb60", "spei"]
MAIN = "XGBoost"                                      # weather available 8 days late
VARIANTS = {MAIN: SAT + WX,
            "XGBoost satellite-only": SAT,
            "XGBoost weather 1-day (sensitivity)": SAT + [w + "_d1" for w in WX]}
BASES = ["Persistence", "Climatology", "Anomaly persistence"]
SEASON_NAME = {y: f"{y}-{str(y + 1)[2:]}" for y in range(2019, 2026)}


def add_clim(d, P, pidx, seasons, allowed, pool_key):
    """Point climatology at issue+15 days (doy_fc) and at the latest observation (doy_last), from `allowed`
    seasons, always excluding the row's own season; fallback = mandal x irrigation pool."""
    pi = d.point_id.map(pidx).to_numpy()
    own = d.season.to_numpy()
    res = {}
    for col, doy in (("clim_target", d.doy_fc.to_numpy(int)), ("clim_last", d.doy_last.to_numpy(int))):
        vals = np.full(len(d), np.nan)
        for s in sorted(set(own)):
            rows = np.where(own == s)[0]
            use = [seasons.index(a) for a in allowed if a != s]
            if not use:
                continue
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                vals[rows] = np.nanmean(P[pi[rows][:, None], np.array(use)[None, :], doy[rows][:, None]], axis=1)
        tmp = pd.DataFrame({"k": pool_key.to_numpy(), "s": own, "v": vals})
        for s in sorted(set(own)):
            m = (tmp.s == s).to_numpy()
            pool = tmp[m].groupby("k").v.transform("mean").to_numpy()
            vals[m] = np.where(np.isnan(vals[m]), pool, vals[m])
        res[col] = vals
    return d.assign(**res)


def baselines(d):
    persist = d.ndvi_last
    return d.assign(pred_persistence=persist,
                    pred_climatology=d.clim_target.fillna(persist),
                    pred_anomaly=(d.clim_target + (d.ndvi_last - d.clim_last)).fillna(persist))


def established(d):
    return (d.season_max >= GREEN) & (d.season_max - d.season_min >= RISE)


def mae(y, p):
    return float(np.mean(np.abs(y - p)))


def cluster_boot(d, a, b, unit="point_id"):
    """95 % CI of MAE(a) - MAE(b), resampling whole clusters (points or weather cells)."""
    e = d.assign(ea=(d.target - d[a]).abs(), eb=(d.target - d[b]).abs())
    g = e.groupby(unit).agg(sa=("ea", "sum"), sb=("eb", "sum"), n=("ea", "size"))
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(g), size=(N_BOOT, len(g)))
    diff = (g.sa.to_numpy()[idx].sum(1) - g.sb.to_numpy()[idx].sum(1)) / g.n.to_numpy()[idx].sum(1)
    return float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5))


def fit_predict(d, P, pidx, seasons, key, feats):
    trva = d.season.isin(TRAIN + VAL)
    s1 = add_clim(d[trva], P, pidx, seasons, TRAIN, key[trva])           # climatology from 2019-21 only
    tr, va = s1[s1.season.isin(TRAIN)], s1[s1.season.isin(VAL)]
    m1 = xgb.XGBRegressor(n_estimators=MAX_TREES, early_stopping_rounds=EARLY, **XGB)
    m1.fit(tr[feats], tr.target - tr.ndvi_last, eval_set=[(va[feats], va.target - va.ndvi_last)], verbose=False)
    n_trees = m1.best_iteration + 1
    s2 = add_clim(d, P, pidx, seasons, TRAIN + VAL, key)                 # climatology from 2019-22 only
    tr2, te = s2[s2.season.isin(TRAIN + VAL)], s2[s2.season.isin(TEST)].copy()
    m2 = xgb.XGBRegressor(n_estimators=n_trees, **XGB)
    m2.fit(tr2[feats], tr2.target - tr2.ndvi_last, verbose=False)
    return te, m2.predict(te[feats]), n_trees, m2


def mae_table(te, methods, months=None):
    rows = []
    for pop, sub in (("all", te), ("established", te[te.established])):
        if months:
            sub = sub[sub.issue_date.dt.month.isin(months)]
        for scope, g in [("pooled", sub)] + [(SEASON_NAME[s], sub[sub.season == s]) for s in TEST]:
            for cls, h in (("all", g), ("rainfed", g[g.irr == 0]), ("irrigated", g[g.irr == 1])):
                r = dict(population=pop, season=scope, cls=cls, n=len(h))
                for nm, c in methods.items():
                    r[f"MAE {nm}"] = round(mae(h.target, h[c]), 4)
                rows.append(r)
    met = pd.DataFrame(rows)
    met["best baseline"] = met[[f"MAE {b}" for b in BASES]].idxmin(axis=1).str.replace("MAE ", "")
    met["skill vs best"] = (1 - met[f"MAE {MAIN}"] / met[[f"MAE {b}" for b in BASES]].min(axis=1)).round(3)
    return met


def beats_each(m):
    per = m[(m.population == "all") & (m.cls == "all") & (m.season != "pooled")]
    return bool((per[f"MAE {MAIN}"] < per[[f"MAE {b}" for b in BASES]].min(axis=1)).all())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(DATA / "instances.csv.gz", parse_dates=["issue_date"])
    n_all = len(d)
    status = d.groupby(["season", "status"]).size().unstack(fill_value=0)
    d = d[d.status == "ok"].copy()
    z = np.load(DATA / "point_curves.npz", allow_pickle=True)
    P, pids, seasons = z["P"], list(z["point_ids"]), list(z["seasons"])
    pidx = {p: i for i, p in enumerate(pids)}
    key = d.mandal + "_" + d.irr.astype(str)

    te, trees, model = None, {}, None
    for nm, feats in VARIANTS.items():
        t, pred, n, m = fit_predict(d, P, pidx, seasons, key, feats)
        te = t if te is None else te
        te["pred_" + nm] = te.ndvi_last.to_numpy() + pred
        trees[nm] = n
        model = m if nm == MAIN else model
    te = baselines(te)
    te["established"] = established(te)
    te.to_csv(OUT / "predictions.csv.gz", index=False)

    methods = {nm: "pred_" + nm for nm in VARIANTS}
    methods.update({"Persistence": "pred_persistence", "Climatology": "pred_climatology",
                    "Anomaly persistence": "pred_anomaly"})
    met = mae_table(te, methods)
    met.to_csv(OUT / "metrics.csv", index=False)
    dm = mae_table(te, methods, months=[12, 1, 2, 3])
    dm.to_csv(OUT / "metrics_dec_mar.csv", index=False)

    ok_each = beats_each(met)
    pooled = met[(met.population == "all") & (met.cls == "all") & (met.season == "pooled")].iloc[0]
    best_col = methods[pooled["best baseline"]]
    lo, hi = cluster_boot(te, methods[MAIN], best_col)
    clo, chi = cluster_boot(te, methods[MAIN], best_col, unit="cell")
    slo, shi = cluster_boot(te, methods[MAIN], methods["XGBoost satellite-only"])
    accepted = ok_each and hi < 0

    ev = te[te.established].copy()
    ev["event"] = (ev.target - ev.ndvi_last) <= DROP
    det = []
    for nm, c in methods.items():
        chg = ev[c] - ev.ndvi_last
        flag = chg <= DROP
        tp = int((flag & ev.event).sum())
        det.append(dict(method=nm, AUC=round(roc_auc_score(ev.event, -chg), 3) if chg.std() > 0 else 0.5,
                        precision=round(tp / flag.sum(), 3) if flag.sum() else np.nan,
                        recall=round(tp / ev.event.sum(), 3), flagged=int(flag.sum())))
    det = pd.DataFrame(det)
    span = ev.span_days.describe()

    imp = pd.Series(model.get_booster().get_score(importance_type="gain")).sort_values(ascending=False)
    imp = (imp / imp.sum()).round(3).head(12).rename("gain share").reset_index().rename(columns={"index": "feature"})

    cols = ["season", "cls", "n"] + [f"MAE {m}" for m in methods] + ["best baseline", "skill vs best"]
    short = ["population", "season", "n"] + [f"MAE {m}" for m in methods] + ["best baseline", "skill vs best"]
    lines = [
        "# Rabi forecast v1 + amendment A1 - results (15-day NDVI forecast)", "",
        "Rules: `docs/FORECAST_v1.md` incl. amendment A1 (climatology at issue+15 days; frozen-calibration weather "
        "from data/prepared; weather available 8 days late). Supersedes the first run (c976795). Chronological test: "
        "trained 2019-20 .. 2022-23 (early stopping on 2022-23), tested 2023-24, 2024-25, 2025-26. Historical "
        "development evidence (seasons known during design), not a real-time test.", "",
        "Trees chosen on validation: " + ", ".join(f"{k} {v}" for k, v in trees.items()), "",
        "## Eligibility", "",
        f"Potential forecasts {n_all}; usable {int(status.ok.sum())} ({status.ok.sum() / n_all:.1%}). Excluded: "
        f"latest observation > 12 days old {int(status.no_recent_obs.sum())}; no observation within t+15 +- 3 days "
        f"{int(status.no_target.sum())}. Excluded = missing data, not 'no crop'.", "",
        "## Accuracy (MAE of NDVI, lower is better) - all eligible points", "",
        md_table(met[met.population == "all"][cols]), "",
        "## Accuracy - established at issue", "", md_table(met[met.population == "established"][cols]), "",
        "## December - March issue dates only (class all)", "", md_table(dm[dm.cls == "all"][short]), "",
        "## Acceptance rule (main model = XGBoost with 8-day-delayed weather)", "",
        f"- Beats every baseline in each test season: **{'yes' if ok_each else 'no'}** "
        f"(December - March only: {'yes' if beats_each(dm) else 'no'})",
        f"- Pooled MAE({MAIN}) - MAE({pooled['best baseline']}), 95 % CI: bootstrap over points [{lo:.4f}, {hi:.4f}]; "
        f"over weather cells (only {te.cell.nunique()} cells, indicative) [{clo:.4f}, {chi:.4f}]",
        f"- **Verdict: {'passes the pre-registered rule' if accepted else 'does NOT pass the pre-registered rule'}**", "",
        "## Does weather help?", "",
        f"Pooled MAE(with weather) - MAE(satellite-only), 95 % CI over points: [{slo:.4f}, {shi:.4f}] "
        "(negative = weather helps).", "",
        f"## Decline from the latest observation to the forecast target (established points; event = change <= {DROP}; "
        f"{int(ev.event.sum())} events in {len(ev)} forecasts)", "",
        f"Span from the latest observation to the target: median {span['50%']:.0f} days "
        f"(range {span['min']:.0f}-{span['max']:.0f}). The event does not distinguish drought from harvest.", "",
        md_table(det), "",
        "## Feature importance (gain share, main model)", "", md_table(imp), ""]
    (OUT / "FORECAST_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
