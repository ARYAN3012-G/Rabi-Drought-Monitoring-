"""
Rabi drought v2 - 15-day forecasting extension (district scale). Separate from monitoring.

Target (future interval water deficit): mean district deficit_area over the 15 days (t, t+15] >= 0.5,
i.e. at least half the district's grid points in soil-moisture deficit on an average day of the next
15 days. Issue dates t every 5 days, 1 Dec - 31 Mar. Inputs dated <= t-8 (ERA5-Land / AgERA5
publication lag), so the target begins 9 days after the last input.
New-onset subset: mean deficit_area over the 15 input days ending t-8 < 0.5.

Splits (whole seasons): train 1990-91..2006-07, validation 2007-08..2013-14, evaluation 2014-15..2022-23.
Models: persistence, crop-calendar climatology, conditional transition, logistic regression, XGBoost;
feature sets soil-only, weather-only, combined on identical rows. Threshold per model = max F1 on validation.

    python -B -m src.drought2.forecast
Writes data/drought2/forecast_instances.csv.gz, results/drought2_v1/forecast_*.csv, FORECAST.md
"""
from __future__ import annotations

import sys
import warnings
import os
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss, f1_score, precision_score, recall_score,
                             roc_auc_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.simplefilter("ignore")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "rabi"))
from protocol import md_table  # noqa: E402

D2 = Path(os.environ.get("DROUGHT2_DATA", ROOT / "data" / "drought2"))   # override for sensitivity runs
OUT = Path(os.environ.get("DROUGHT2_RESULTS", ROOT / "results" / "drought2_v1"))
PREP = ROOT / "data" / "prepared"
LAG, H, THR = 8, 15, 0.5
TRAIN, VAL, EVAL = range(1990, 2007), range(2007, 2014), range(2014, 2023)
CELLS = {"Kurnool": ["Peddakadubur", "kurnool_dinedevarapadu"], "Anantapur": ["Somandepalle", "cholasamudram"],
         "Tumkur": ["sira"]}
SOIL = ["area_last", "area_15", "area_30", "pct_last", "pct_chg15", "pct_chg30", "dd_so_far", "doy"]
WEATHER = ["rain30", "rain60", "rain_since_oct", "rain_jun_nov_ratio", "et0_30", "doy"]
DIST = ["d_Kurnool", "d_Anantapur", "d_Tumkur"]


def weather_daily():
    out = {}
    for dist, cells in CELLS.items():
        frames = [pd.read_csv(PREP / f"{c}.csv", usecols=["valid_time", "Precipitation_Flux",
                                                          "ReferenceET_PenmanMonteith_FAO56"],
                              parse_dates=["valid_time"]).set_index("valid_time") for c in cells]
        out[dist] = sum(frames) / len(frames)
    return out


def build():
    dd = pd.read_csv(D2 / "daily_district.csv.gz", parse_dates=["date"]).set_index("date")
    wx = weather_daily()
    rows = []
    for (dist, s), q in dd.groupby(["district", "season"]):
        q = q.sort_index()
        w = wx[dist]
        jn = w.Precipitation_Flux[f"{s}-06-01":f"{s}-11-30"].sum()
        jn0 = np.mean([w.Precipitation_Flux[f"{y}-06-01":f"{y}-11-30"].sum() for y in range(1979, 2005)])
        t = pd.Timestamp(s, 12, 1)
        while t <= pd.Timestamp(s + 1, 3, 31):
            e = t - pd.Timedelta(days=LAG)
            past = q[:e]
            fut = q[t + pd.Timedelta(days=1):t + pd.Timedelta(days=H)]
            r = dict(district=dist, season=s, issue_date=t, doy=(t - pd.Timestamp(s, 10, 1)).days)
            if len(fut) < H or fut.deficit_area.isna().mean() > 0.2 or past.deficit_area.tail(30).isna().any():
                r["status"] = "insufficient data"
                rows.append(r)
                t += pd.Timedelta(days=5)
                continue
            a = past.deficit_area
            pm = past.pct_median
            rr = w.Precipitation_Flux
            r.update(status="ok", target=int(fut.deficit_area.mean() >= THR), target_mean=fut.deficit_area.mean(),
                     area_last=a.iloc[-1], area_15=a.tail(15).mean(), area_30=a.tail(30).mean(),
                     pct_last=pm.iloc[-1], pct_chg15=pm.iloc[-1] - pm.iloc[-16], pct_chg30=pm.iloc[-1] - pm.iloc[-31],
                     dd_so_far=a[f"{s}-11-01":].mean() if e >= pd.Timestamp(s, 11, 1) else np.nan,
                     rain30=rr[e - pd.Timedelta(days=29):e].sum(), rain60=rr[e - pd.Timedelta(days=59):e].sum(),
                     rain_since_oct=rr[f"{s}-10-01":e].sum(), rain_jun_nov_ratio=jn / jn0,
                     et0_30=w.ReferenceET_PenmanMonteith_FAO56[e - pd.Timedelta(days=29):e].mean(),
                     input_cutoff=e, oracle_rain_future=rr[t + pd.Timedelta(days=1):t + pd.Timedelta(days=H)].sum())
            rows.append(r)
            t += pd.Timedelta(days=5)
    d = pd.DataFrame(rows)
    for k in ["Kurnool", "Anantapur", "Tumkur"]:
        d[f"d_{k}"] = (d.district == k).astype(int)
    d.to_csv(D2 / "forecast_instances.csv.gz", index=False)
    return d


def best_thr(y, p):
    grid = np.unique(np.quantile(p, np.linspace(0.02, 0.98, 97)))
    f = [f1_score(y, p >= g, zero_division=0) for g in grid]
    return float(grid[int(np.argmax(f))])


def score(y, p, thr, binary=False):
    pred = p >= thr
    two = y.min() != y.max()
    return dict(n=len(y), positives=int(y.sum()), warnings=int(pred.sum()),
                precision=precision_score(y, pred, zero_division=0) if pred.sum() else np.nan,
                recall=recall_score(y, pred, zero_division=0) if y.sum() else np.nan,
                f1=f1_score(y, pred, zero_division=0) if y.sum() else np.nan,
                pr_auc=average_precision_score(y, p) if two and not binary else np.nan,
                roc_auc=roc_auc_score(y, p) if two and not binary else np.nan,
                brier=brier_score_loss(y, np.clip(p, 0, 1)) if not binary else np.nan)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = build()
    ok = d[d.status == "ok"].copy()
    tr, va, ev = (ok[ok.season.isin(s)].copy() for s in (TRAIN, VAL, EVAL))
    preds_va, preds_ev, binary = {}, {}, set()
    # baselines
    preds_va["Persistence (area last 15 d >= 0.5)"] = (va.area_15 >= THR).astype(float).to_numpy()
    preds_ev["Persistence (area last 15 d >= 0.5)"] = (ev.area_15 >= THR).astype(float).to_numpy()
    binary.add("Persistence (area last 15 d >= 0.5)")
    clim = tr.assign(b=(tr.doy // 15)).groupby(["district", "b"]).target.mean()
    for nm, frame, store in (("va", va, preds_va), ("ev", ev, preds_ev)):
        store["Climatology (district x calendar)"] = frame.assign(b=frame.doy // 15).set_index(
            ["district", "b"]).index.map(clim).to_numpy(dtype=float)
    bins = [-0.01, 0.1, 0.3, 0.5, 0.7, 1.01]
    trans = tr.assign(s=pd.cut(tr.area_15, bins)).groupby(["district", "s"], observed=False).target.mean()
    for frame, store in ((va, preds_va), (ev, preds_ev)):
        store["Conditional transition"] = frame.assign(s=pd.cut(frame.area_15, bins)).set_index(
            ["district", "s"]).index.map(trans).to_numpy(dtype=float)
    # models
    fitted = {}
    for fs_name, feats in (("soil", SOIL + DIST), ("weather", WEATHER + DIST), ("combined", SOIL + WEATHER[:-1] + DIST)):
        lr = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                           LogisticRegression(max_iter=3000, class_weight="balanced"))
        lr.fit(tr[feats], tr.target)
        fitted[f"Logistic regression ({fs_name})"] = ([lr], feats)
        preds_va[f"Logistic regression ({fs_name})"] = lr.predict_proba(va[feats])[:, 1]
        preds_ev[f"Logistic regression ({fs_name})"] = lr.predict_proba(ev[feats])[:, 1]
        pv, pe, ms = [], [], []
        for seed in range(5):
            m = xgb.XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8,
                                  colsample_bytree=0.8, random_state=seed, eval_metric="logloss",
                                  scale_pos_weight=(1 - tr.target.mean()) / tr.target.mean())
            m.fit(tr[feats], tr.target)
            ms.append(m)
            pv.append(m.predict_proba(va[feats])[:, 1])
            pe.append(m.predict_proba(ev[feats])[:, 1])
        fitted[f"XGBoost ({fs_name})"] = (ms, feats)
        preds_va[f"XGBoost ({fs_name})"] = np.mean(pv, axis=0)
        preds_ev[f"XGBoost ({fs_name})"] = np.mean(pe, axis=0)
    # oracle (future rain), clearly not operational
    of = SOIL + ["oracle_rain_future"] + DIST
    m = xgb.XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, random_state=0, eval_metric="logloss")
    m.fit(tr[of], tr.target)
    preds_va["ORACLE: XGBoost soil + future rain (not operational)"] = m.predict_proba(va[of])[:, 1]
    preds_ev["ORACLE: XGBoost soil + future rain (not operational)"] = m.predict_proba(ev[of])[:, 1]

    # Amendment A1 (docs/DROUGHT2_v1.md): the validation seasons can contain no positive targets, so
    # thresholds and model selection use leave-one-season-out (LOSO) predictions within TRAINING seasons.
    oof = {nm: np.full(len(tr), np.nan) for nm in preds_ev}
    yt = tr.target.to_numpy()
    for s in sorted(tr.season.unique()):
        f_in, f_out = (tr.season != s).to_numpy(), (tr.season == s).to_numpy()
        a, b = tr[f_in], tr[f_out]
        oof["Persistence (area last 15 d >= 0.5)"][f_out] = (b.area_15 >= THR).astype(float)
        c_ = a.assign(bb=a.doy // 15).groupby(["district", "bb"]).target.mean()
        oof["Climatology (district x calendar)"][f_out] = b.assign(bb=b.doy // 15).set_index(
            ["district", "bb"]).index.map(c_).to_numpy(dtype=float)
        t_ = a.assign(ss=pd.cut(a.area_15, bins)).groupby(["district", "ss"], observed=False).target.mean()
        oof["Conditional transition"][f_out] = b.assign(ss=pd.cut(b.area_15, bins)).set_index(
            ["district", "ss"]).index.map(t_).to_numpy(dtype=float)
        if a.target.sum() == 0:
            continue
        for nm, (ms, feats) in fitted.items():
            if nm.startswith("Logistic"):
                m = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                  LogisticRegression(max_iter=3000, class_weight="balanced")).fit(a[feats], a.target)
            else:
                m = xgb.XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8,
                                      colsample_bytree=0.8, random_state=0, eval_metric="logloss",
                                      scale_pos_weight=(1 - a.target.mean()) / a.target.mean()).fit(a[feats], a.target)
            oof[nm][f_out] = m.predict_proba(b[feats])[:, 1]
        m = xgb.XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, random_state=0,
                              eval_metric="logloss").fit(a[of], a.target)
        oof["ORACLE: XGBoost soil + future rain (not operational)"][f_out] = m.predict_proba(b[of])[:, 1]

    new_ev = (ev.area_15 < THR).to_numpy()
    rows = []
    for nm in preds_ev:
        po = np.nan_to_num(oof[nm], nan=float(np.nanmean(oof[nm])))
        pe = np.nan_to_num(preds_ev[nm], nan=float(np.nanmean(oof[nm])))
        thr = 0.5 if nm in binary else best_thr(yt, po)
        loso_f1 = f1_score(yt, po >= thr, zero_division=0)
        loso_prauc = average_precision_score(yt, po) if nm not in binary else np.nan
        val_pos = int(va.target.sum())
        for subset, m_ in (("all", np.ones(len(ev), bool)), ("new onset", new_ev)):
            rows.append(dict(model=nm, subset=subset, threshold=thr, loso_train_f1=loso_f1,
                             loso_train_pr_auc=loso_prauc, validation_positives=val_pos,
                             **score(ev.target.to_numpy()[m_], pe[m_], thr, nm in binary)))
        ev[f"p::{nm}"] = pe
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "forecast_metrics.csv", index=False)
    ev.to_csv(OUT / "forecast_predictions.csv.gz", index=False)

    # event level: district-seasons with >= 1 positive target; caught if warned on a positive row
    sel = res[(res.subset == "all") & ~res.model.str.startswith("ORACLE")].sort_values("loso_train_f1", ascending=False)
    ev_rows = []
    for nm in res.model.unique():
        thr = res[(res.model == nm)].threshold.iloc[0]
        e = ev.assign(w=ev[f"p::{nm}"] >= thr)
        g = e.groupby(["district", "season"]).agg(pos=("target", "max"), hit=("w", lambda x: 0))
        hits = e[e.w & (e.target == 1)].groupby(["district", "season"]).size()
        warned = e[e.w].groupby(["district", "season"]).size()
        g["caught"] = g.index.isin(hits.index)
        g["warned"] = g.index.isin(warned.index)
        ev_rows.append(dict(model=nm, deficit_district_seasons=int(g.pos.sum()),
                            caught=int((g.caught & (g.pos == 1)).sum()), warned_district_seasons=int(g.warned.sum()),
                            warned_with_correct=int((g.warned & g.caught).sum()), district_seasons=len(g)))
    evt = pd.DataFrame(ev_rows)
    evt.to_csv(OUT / "forecast_events.csv", index=False)

    # save the validation-selected operational model (trained on training seasons only)
    import joblib, json, hashlib
    MD = Path(os.environ.get("DROUGHT2_MODELS", ROOT / "models" / "drought2_v1"))
    MD.mkdir(parents=True, exist_ok=True)
    chosen = sel.iloc[0].model
    bundle = dict(name=chosen, threshold=float(sel.iloc[0].threshold), lag_days=LAG, horizon=H, target_threshold=THR,
                  models=None, features=None, kind="baseline")
    if chosen in fitted:
        bundle.update(models=fitted[chosen][0], features=fitted[chosen][1], kind="model")
    joblib.dump(bundle, MD / "forecast_15d.joblib")
    (MD / "forecast_15d.json").write_text(json.dumps(dict(name=chosen, threshold=bundle["threshold"],
        features=bundle["features"], kind=bundle["kind"], train=[TRAIN.start, TRAIN.stop - 1],
        validation=[VAL.start, VAL.stop - 1], sha256=hashlib.sha256((MD / "forecast_15d.joblib").read_bytes()).hexdigest()),
        indent=1), encoding="utf-8")
    if chosen not in fitted:
        joblib.dump(dict(clim=clim, trans=trans, bins=bins), MD / "baseline_tables.joblib")

    cov = d.groupby(["season", "status"]).size().unstack(fill_value=0)
    lines = ["# Rabi drought v2 - 15-day district soil-deficit forecast", "",
             f"Target: mean district deficit area over (t, t+15] >= {THR}. Inputs <= t-{LAG} d. Train 1990-2006, "
             "validation 2007-13 (reported; thresholds and selection by leave-one-season-out within training, amendment A1), evaluation 2014-22 (whole seasons). Rows are correlated issue "
             "dates of 3 districts. Model selection by LOSO training F1 among operational models: "
             f"**{sel.iloc[0].model}**.", "",
             "## Evaluation rows", "", md_table(res.round(3)), "",
             "## District-season events (evaluation)", "", md_table(evt), "",
             "## Coverage", "", md_table(cov.reset_index()), ""]
    (OUT / "FORECAST.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
