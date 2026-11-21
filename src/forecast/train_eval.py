"""
Rabi forecast v1 - training and chronological evaluation (rules: docs/FORECAST_v1.md).

    python src/forecast/train_eval.py
Writes results/forecast_v1/{predictions.csv.gz, metrics.csv, FORECAST_RESULTS.md}
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
OUT = ROOT / "results" / "forecast_v1"

TRAIN, VAL, TEST = [2019, 2020, 2021], [2022], [2023, 2024, 2025]
XGB = dict(objective="reg:squarederror", max_depth=6, learning_rate=0.05, subsample=0.8,
           colsample_bytree=0.8, random_state=0, tree_method="hist", n_jobs=-1)
MAX_TREES, EARLY = 2000, 50
DROP = -0.10
GREEN, RISE = 0.35, 0.15
N_BOOT, BOOT_SEED = 1000, 12345
FEATURES = ["ndvi_last", "age_last", "ndvi_15", "age_15", "ndvi_30", "age_30", "chg15", "chg30",
            "season_max", "season_min", "n_obs30", "doy_issue", "irr", "lat", "lon",
            "rain30", "rain90", "rain_jun_ratio", "et0_15", "tmax_15", "wb60", "spei",
            "clim_target", "clim_last"]
SEASON_NAME = {y: f"{y}-{str(y + 1)[2:]}" for y in range(2019, 2026)}


def add_clim(d: pd.DataFrame, P: np.ndarray, pidx: dict, seasons: list, allowed: list, pool_key: pd.Series):
    """Point climatology at doy_target / doy_last from `allowed` seasons, excluding the row's own season."""
    pi = d.point_id.map(pidx).to_numpy()
    own = d.season.to_numpy()
    res = {}
    for col, doy in (("clim_target", d.doy_target.to_numpy(int)), ("clim_last", d.doy_last.to_numpy(int))):
        vals = np.full(len(d), np.nan)
        for s in sorted(set(own)):
            rows = np.where(own == s)[0]
            use = [seasons.index(a) for a in allowed if a != s]
            if not use:
                continue
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                sub = P[pi[rows][:, None], np.array(use)[None, :], doy[rows][:, None]]
                vals[rows] = np.nanmean(sub, axis=1)
        # fallback: mandal x irrigation pool of point means
        tmp = pd.DataFrame({"k": pool_key.to_numpy(), "s": own, "v": vals})
        for s in sorted(set(own)):
            m = tmp.s == s
            pool = tmp[m].groupby("k").v.transform("mean")
            vals[m.to_numpy()] = np.where(np.isnan(vals[m.to_numpy()]), pool.to_numpy(), vals[m.to_numpy()])
        res[col] = vals
    return d.assign(**res)


def baselines(d: pd.DataFrame) -> pd.DataFrame:
    persist = d.ndvi_last
    clim = d.clim_target.fillna(persist)
    anom = (d.clim_target + (d.ndvi_last - d.clim_last)).fillna(persist)
    return d.assign(pred_persistence=persist, pred_climatology=clim, pred_anomaly=anom)


def established(d: pd.DataFrame) -> pd.Series:
    return (d.season_max >= GREEN) & (d.season_max - d.season_min >= RISE)


def mae(y, p):
    return float(np.mean(np.abs(y - p)))


def cluster_boot(d: pd.DataFrame, a: str, b: str) -> tuple:
    """95 % CI of MAE(a) - MAE(b), resampling points."""
    e = d.assign(ea=(d.target - d[a]).abs(), eb=(d.target - d[b]).abs())
    g = e.groupby("point_id").agg(sa=("ea", "sum"), sb=("eb", "sum"), n=("ea", "size"))
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(g), size=(N_BOOT, len(g)))
    sa, sb, n = g.sa.to_numpy()[idx].sum(1), g.sb.to_numpy()[idx].sum(1), g.n.to_numpy()[idx].sum(1)
    diff = (sa - sb) / n
    return float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5))


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

    # stage 1: train 2019-21, early stopping on 2022 (climatology from 2019-21 only)
    s1 = add_clim(d[d.season.isin(TRAIN + VAL)], P, pidx, seasons, TRAIN, key[d.season.isin(TRAIN + VAL)])
    tr, va = s1[s1.season.isin(TRAIN)], s1[s1.season.isin(VAL)]
    m1 = xgb.XGBRegressor(n_estimators=MAX_TREES, early_stopping_rounds=EARLY, **XGB)
    m1.fit(tr[FEATURES], tr.target - tr.ndvi_last, eval_set=[(va[FEATURES], va.target - va.ndvi_last)], verbose=False)
    n_trees = m1.best_iteration + 1

    # stage 2: refit on 2019-22 with n_trees; climatology from 2019-22 only; predict 2023-25
    s2 = add_clim(d, P, pidx, seasons, TRAIN + VAL, key)
    tr2, te = s2[s2.season.isin(TRAIN + VAL)], s2[s2.season.isin(TEST)].copy()
    m2 = xgb.XGBRegressor(n_estimators=n_trees, **XGB)
    m2.fit(tr2[FEATURES], tr2.target - tr2.ndvi_last, verbose=False)
    te["pred_change"] = m2.predict(te[FEATURES])
    te["pred_model"] = te.ndvi_last + te.pred_change
    te = baselines(te)
    te["established"] = established(te)
    te.to_csv(OUT / "predictions.csv.gz", index=False)

    methods = {"XGBoost": "pred_model", "Persistence": "pred_persistence", "Climatology": "pred_climatology",
               "Anomaly persistence": "pred_anomaly"}
    rows = []
    for pop, sub in (("all", te), ("established", te[te.established])):
        for scope, g in [("pooled", sub)] + [(SEASON_NAME[s], sub[sub.season == s]) for s in TEST]:
            for cls, h in (("all", g), ("rainfed", g[g.irr == 0]), ("irrigated", g[g.irr == 1])):
                r = dict(population=pop, season=scope, cls=cls, n=len(h))
                for nm, c in methods.items():
                    r[f"MAE {nm}"] = round(mae(h.target, h[c]), 4)
                rows.append(r)
    met = pd.DataFrame(rows)
    bases = ["Persistence", "Climatology", "Anomaly persistence"]
    met["best baseline"] = met[[f"MAE {b}" for b in bases]].idxmin(axis=1).str.replace("MAE ", "")
    met["skill vs best"] = (1 - met["MAE XGBoost"] / met[[f"MAE {b}" for b in bases]].min(axis=1)).round(3)
    met.to_csv(OUT / "metrics.csv", index=False)

    # acceptance (population all, class all)
    per = met[(met.population == "all") & (met.cls == "all") & (met.season != "pooled")]
    beats_each = bool((per["MAE XGBoost"] < per[[f"MAE {b}" for b in bases]].min(axis=1)).all())
    pooled = met[(met.population == "all") & (met.cls == "all") & (met.season == "pooled")].iloc[0]
    best_col = methods[pooled["best baseline"]]
    lo, hi = cluster_boot(te, "pred_model", best_col)
    accepted = beats_each and hi < 0

    # deterioration (established)
    ev = te[te.established].copy()
    ev["event"] = (ev.target - ev.ndvi_last) <= DROP
    det = []
    for nm, c in methods.items():
        chg = ev[c] - ev.ndvi_last
        auc = roc_auc_score(ev.event, -chg) if chg.std() > 0 else 0.5
        flag = chg <= DROP
        tp = int((flag & ev.event).sum())
        det.append(dict(method=nm, AUC=round(auc, 3),
                        precision=round(tp / flag.sum(), 3) if flag.sum() else np.nan,
                        recall=round(tp / ev.event.sum(), 3), flagged=int(flag.sum())))
    det = pd.DataFrame(det)

    imp = pd.Series(m2.get_booster().get_score(importance_type="gain")).sort_values(ascending=False)
    imp = (imp / imp.sum()).round(3).head(12).rename("gain share").reset_index().rename(columns={"index": "feature"})

    show = ["season", "cls", "n"] + [f"MAE {m}" for m in methods] + ["best baseline", "skill vs best"]
    lines = [
        "# Rabi forecast v1 - results (15-day NDVI forecast)", "",
        "Rules fixed before training in `docs/FORECAST_v1.md`. Chronological test: trained on 2019-20 .. 2022-23 "
        f"(early stopping on 2022-23, {n_trees} trees), tested on 2023-24, 2024-25, 2025-26. The seasons were known "
        "while the rabi project was designed: historical development evidence, not a real-time test.", "",
        "## Eligibility", "",
        f"Potential forecasts {n_all}; usable {int(status.ok.sum())} ({status.ok.sum() / n_all:.1%}). "
        "Excluded: no recent observation (latest > 12 days old) "
        f"{int(status.no_recent_obs.sum())}, no target within t+15 +- 3 days {int(status.no_target.sum())}. "
        "Excluded forecasts are missing data, not 'no crop'.", "",
        md_table(status.reset_index()), "",
        "## Accuracy (MAE of NDVI, lower is better) - all eligible points", "",
        md_table(met[met.population == "all"][show]), "",
        "## Accuracy - points established at issue", "",
        md_table(met[met.population == "established"][show]), "",
        f"## Acceptance rule", "",
        f"- XGBoost beats every baseline in each test season: **{'yes' if beats_each else 'no'}**",
        f"- Pooled MAE(XGBoost) - MAE({pooled['best baseline']}), 95 % cluster-bootstrap CI over points: "
        f"[{lo:.4f}, {hi:.4f}]",
        f"- **Verdict: {'USEFUL (passes the pre-registered rule)' if accepted else 'NOT accepted under the pre-registered rule'}**",
        "", f"## Deterioration (established points, event = 15-day drop <= {DROP}; "
            f"{int(ev.event.sum())} events in {len(ev)} forecasts)", "",
        md_table(det), "",
        "## Feature importance (gain share, final model)", "", md_table(imp), ""]
    (OUT / "FORECAST_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
