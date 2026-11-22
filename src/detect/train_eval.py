"""
Rabi early-drying risk model: Logistic Regression, Random Forest, XGBoost and two ensembles vs baselines,
horizons 7 / 15 / 30 days (docs/DETECT_v1.md).

    python src/detect/train_eval.py
Writes results/detect_v1/{metrics.csv, metrics_by_season.csv, predictions.csv.gz, DETECT_RESULTS.md}
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, balanced_accuracy_score, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.simplefilter("ignore")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "rabi"))
from protocol import md_table  # noqa: E402

DATA = ROOT / "data" / "detect"
OUT = ROOT / "results" / "detect_v1"
TRAIN, VAL, TEST = [2019, 2020, 2021], [2022], [2023, 2024, 2025]
HORIZONS = [7, 15, 30]
SEEDS = [0, 1, 2, 3, 4]
N_BOOT, BOOT_SEED = 1000, 12345
FEATS = ["irr", "doy", "ndvi", "age", "peak", "trough", "days_since_peak", "drop", "drop_share", "chg15", "chg30",
         "anom", "normal_dry", "days_to_normal_dry", "status_t", "rain_jun_nov_ratio", "rain_since_oct", "rain60",
         "et0_30", "tmax_30", "spei"]
SEASON = {y: f"{y}-{str(y + 1)[2:]}" for y in range(2019, 2026)}


def models(seed, pos_w):
    return {
        "Logistic regression": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                             LogisticRegression(max_iter=3000, class_weight="balanced")),
        "Random forest": make_pipeline(SimpleImputer(strategy="median"),
                                       RandomForestClassifier(n_estimators=500, min_samples_leaf=5, n_jobs=-1,
                                                              class_weight="balanced_subsample", random_state=seed)),
        "XGBoost": xgb.XGBClassifier(n_estimators=400, max_depth=4, learning_rate=0.05, subsample=0.8,
                                     colsample_bytree=0.8, scale_pos_weight=pos_w, random_state=seed,
                                     eval_metric="logloss", n_jobs=-1),
    }


def best_threshold(y, p):
    grid = np.unique(np.quantile(p, np.linspace(0.01, 0.99, 197)))
    scores = [balanced_accuracy_score(y, p >= g) for g in grid]
    return float(grid[int(np.argmax(scores))])


def scores(y, p, thr):
    pred = p >= thr
    return dict(n=len(y), positives=int(y.sum()), accuracy=accuracy_score(y, pred),
                balanced_accuracy=balanced_accuracy_score(y, pred), precision=precision_score(y, pred, zero_division=0),
                recall=recall_score(y, pred), f1=f1_score(y, pred), roc_auc=roc_auc_score(y, p),
                pr_auc=average_precision_score(y, p))


def boot_auc_diff(df, a, b, y):
    pts = df.point_id.unique()
    rng = np.random.default_rng(BOOT_SEED)
    idx = {p: np.where(df.point_id.to_numpy() == p)[0] for p in pts}
    diffs = []
    for _ in range(N_BOOT):
        sel = np.concatenate([idx[p] for p in rng.choice(pts, len(pts))])
        yy = df[y].to_numpy()[sel]
        if yy.min() == yy.max():
            continue
        diffs.append(roc_auc_score(yy, df[a].to_numpy()[sel]) - roc_auc_score(yy, df[b].to_numpy()[sel]))
    return float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(DATA / "instances.csv.gz", parse_dates=["issue_date"])
    all_rows, season_rows, preds, notes = [], [], [], []
    for h in HORIZONS:
        y = f"y{h}"
        dh = d[d[y].notna()].copy()
        dh[y] = dh[y].astype(int)
        tr, va, te = (dh[dh.season.isin(s)].copy() for s in (TRAIN, VAL, TEST))
        pos_w = (1 - tr[y].mean()) / tr[y].mean()
        probs_va, probs_te = {}, {}
        for seed in SEEDS:
            for nm, m in models(seed, pos_w).items():
                if nm == "Logistic regression" and seed > 0:
                    continue
                m.fit(tr[FEATS], tr[y])
                probs_va.setdefault(nm, []).append(m.predict_proba(va[FEATS])[:, 1])
                probs_te.setdefault(nm, []).append(m.predict_proba(te[FEATS])[:, 1])
        base = ["Logistic regression", "Random forest", "XGBoost"]
        # per-seed ensembles (LR is deterministic and reused)
        prauc = {nm: average_precision_score(va[y], np.mean(probs_va[nm], axis=0)) for nm in base}
        w = np.array([prauc[nm] for nm in base])
        w = w / w.sum()
        for s in range(len(SEEDS)):
            pv = [probs_va[nm][min(s, len(probs_va[nm]) - 1)] for nm in base]
            pt = [probs_te[nm][min(s, len(probs_te[nm]) - 1)] for nm in base]
            probs_va.setdefault("Ensemble (equal)", []).append(np.mean(pv, axis=0))
            probs_te.setdefault("Ensemble (equal)", []).append(np.mean(pt, axis=0))
            probs_va.setdefault("Ensemble (validation-weighted)", []).append(np.average(pv, axis=0, weights=w))
            probs_te.setdefault("Ensemble (validation-weighted)", []).append(np.average(pt, axis=0, weights=w))
        notes.append(f"{h} d: validation PR-AUC LR {prauc[base[0]]:.3f}, RF {prauc[base[1]]:.3f}, "
                     f"XGB {prauc[base[2]]:.3f} -> weights {', '.join(f'{x:.2f}' for x in w)}")

        new = te.status_t.to_numpy() == 0
        for nm in probs_te:
            res = {"all": [], "new": []}
            for pv, pt in zip(probs_va[nm], probs_te[nm]):
                thr = best_threshold(va[y].to_numpy(), pv)
                res["all"].append(scores(te[y].to_numpy(), pt, thr))
                res["new"].append(scores(te[y].to_numpy()[new], pt[new], thr))
            for subset, lst in res.items():
                df = pd.DataFrame(lst)
                row = dict(horizon=h, subset=subset, model=nm, seeds=len(lst))
                for c in df.columns:
                    row[c] = df[c].mean()
                    row[c + "_sd"] = df[c].std(ddof=0)
                all_rows.append(row)
            pm = np.mean(probs_te[nm], axis=0)
            te[f"p_{nm}"] = pm
            thr = best_threshold(va[y].to_numpy(), np.mean(probs_va[nm], axis=0))
            for s in TEST:
                q = (te.season == s).to_numpy()
                season_rows.append(dict(horizon=h, model=nm, season=SEASON[s], **scores(te[y].to_numpy()[q], pm[q], thr)))

        # baselines
        te["b_persistence"] = te.status_t
        te["b_below_normal"] = -te.anom
        te["b_drop"] = te.drop_share
        te["b_rule"] = ((te.drop_share >= 0.5) & (te.doy + h <= te.normal_dry - 21)).astype(int)
        va_rule = ((va.drop_share >= 0.5) & (va.doy + h <= va.normal_dry - 21)).astype(int)
        for nm, col, vcol in (("Baseline: persistence (dried early already)", "b_persistence", va.status_t),
                              ("Baseline: greenness below normal", "b_below_normal", -va.anom),
                              ("Baseline: drop from peak", "b_drop", va.drop_share),
                              ("Baseline: early-drying rule", "b_rule", va_rule)):
            p = te[col].fillna(te[col].median()).to_numpy().astype(float)
            pv = vcol.fillna(vcol.median()).to_numpy().astype(float)
            thr = best_threshold(va[y].to_numpy(), pv) if len(np.unique(pv)) > 2 else 0.5
            for subset, m in (("all", np.ones(len(te), bool)), ("new", new)):
                yy = te[y].to_numpy()[m]
                pp = p[m]
                row = dict(horizon=h, subset=subset, model=nm, seeds=1)
                if yy.min() != yy.max() and len(np.unique(pp)) > 1:
                    row.update(scores(yy, pp, thr))
                else:
                    row.update(n=len(yy), positives=int(yy.sum()), roc_auc=0.5)
                all_rows.append(row)
        best_b = max(("b_below_normal", "b_drop"), key=lambda c: roc_auc_score(te[y], te[c].fillna(te[c].median())))
        te[best_b] = te[best_b].fillna(te[best_b].median())
        lo, hi = boot_auc_diff(te[te.status_t == 0], "p_Ensemble (validation-weighted)", best_b, y)
        notes.append(f"{h} d, new onsets: AUC(weighted ensemble) - AUC({best_b}) 95% CI over points [{lo:+.3f}, {hi:+.3f}]")
        # lead time for correctly warned new onsets
        thr = best_threshold(va[y].to_numpy(), np.mean(probs_va["Ensemble (validation-weighted)"], axis=0))
        hit = (te.status_t == 0) & (te[y] == 1) & (te["p_Ensemble (validation-weighted)"] >= thr)
        lead = (te.dry_doy - te.doy)[hit]
        notes.append(f"{h} d: correctly warned new onsets {int(hit.sum())} of {int(((te.status_t == 0) & (te[y] == 1)).sum())}; "
                     f"lead time before drying median {lead.median():.0f} d (IQR {lead.quantile(.25):.0f}-{lead.quantile(.75):.0f})")
        te["horizon"] = h
        preds.append(te[["point_id", "season", "issue_date", "horizon", "status_t", y, "dry_doy", "doy"] +
                        [c for c in te.columns if c.startswith(("p_", "b_"))]].rename(columns={y: "target"}))

    met = pd.DataFrame(all_rows)
    met.to_csv(OUT / "metrics.csv", index=False)
    pd.DataFrame(season_rows).to_csv(OUT / "metrics_by_season.csv", index=False)
    pd.concat(preds).to_csv(OUT / "predictions.csv.gz", index=False)

    # drought check: early-drying rate vs Jun-Nov rain (cell-season)
    lab = pd.read_csv(DATA / "labels.csv")
    ok = lab[lab.reason == "ok"].merge(d[["point_id", "season", "cell", "rain_jun_nov_ratio"]].drop_duplicates(
        ["point_id", "season"]), on=["point_id", "season"])
    cs = ok.groupby(["cell", "season"]).agg(early=("early", "mean"), rain=("rain_jun_nov_ratio", "first"),
                                            n=("early", "size"))
    cs = cs[cs.n >= 10]
    rho = cs.early.corr(cs.rain, method="spearman")
    dry = cs.rain < 0.8

    def tbl(subset):
        q = met[met.subset == subset].copy()
        q["model"] = q.model.str.replace("Baseline: ", "B: ")
        cols = ["horizon", "model", "n", "positives", "accuracy", "balanced_accuracy", "precision", "recall", "f1",
                "roc_auc", "pr_auc"]
        return md_table(q[cols].round(3))

    lines = ["# Rabi early-drying risk model v1 - results", "",
             "Rules: `docs/DETECT_v1.md` (fixed before the run). Train 2019-20..2021-22, validation 2022-23 "
             "(thresholds, ensemble weights), evaluation 2023-24..2025-26 - historical seasons already consulted "
             "during development, never used for fitting or choices here. Target = satellite-defined early drying "
             "(>= 21 days before the point's normal drying date), not field-verified drought.", "",
             "## All eligible forecasts (mean over 5 seeds)", "", tbl("all"), "",
             "## New onsets only (crop not yet dried at the issue date)", "", tbl("new"), "",
             "## Notes", ""] + [f"- {n}" for n in notes] + [
             "", "## Drought check", "",
             f"Cell-season early-drying rate vs June-November rain ratio: Spearman {rho:.2f} (n = {len(cs)}); "
             f"rate when rain < 80 % of normal {cs[dry].early.mean():.2f} vs {cs[~dry].early.mean():.2f} otherwise.", ""]
    (OUT / "DETECT_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
