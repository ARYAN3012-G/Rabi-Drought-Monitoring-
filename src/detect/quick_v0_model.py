"""Quick feasibility: predict early drying (drought label) at fixed issue dates."""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (balanced_accuracy_score, f1_score, precision_score, recall_score,
                             roc_auc_score, accuracy_score)

warnings.simplefilter("ignore")
SP = Path(__file__).resolve().parents[2] / "results" / "detect_quick_v0"
R = Path(__file__).resolve().parents[2]
W = R / "data" / "prepared"
sys.path.insert(0, str(R / "src" / "forecast"))
import build_dataset as B  # noqa: E402

lab = pd.read_csv(SP / "labels_v0.csv")
lab = lab[(lab.ref_est >= 2) & lab.est.astype(bool) & lab.normal_dry.notna()].copy()   # established rabi crops
lab["drought"] = ((lab.normal_dry - lab.dry) >= 21).astype(int)
cell = pd.read_csv(R / "data" / "forecast" / "instances.csv.gz", usecols=["mandal", "cell"]).drop_duplicates()
lab = lab.merge(cell, on="mandal")
obs = B.load_obs()
z = np.load(R / "data" / "forecast" / "point_curves.npz", allow_pickle=True)
P, pids = z["P"], list(z["point_ids"])
pidx = {p: i for i, p in enumerate(pids)}

wx = {}
for c in lab.cell.unique():
    d = pd.read_csv(W / f"{c}.csv", parse_dates=["valid_time"]).set_index("valid_time")
    wx[c] = d


def weather(c, y, t):
    d = wx[c]
    e = t - pd.Timedelta(days=8)
    rain = d.Precipitation_Flux
    jn = rain[f"{y}-06-01":f"{y}-11-30"].sum()
    norm = np.mean([rain[f"{k}-06-01":f"{k}-11-30"].sum() for k in range(1979, 2012)])
    return dict(rain_jun_nov_ratio=jn / norm, rain_since_oct=rain[f"{y}-10-01":e].sum(),
                rain60=rain[e - pd.Timedelta(days=60):e].sum(),
                et0_30=d.ReferenceET_PenmanMonteith_FAO56[e - pd.Timedelta(days=30):e].mean(),
                tmax_30=(d.Temperature_Air_2m_Max_24h[e - pd.Timedelta(days=30):e] - 273.15).mean(),
                spei=d.SPEI.get(e, np.nan))


TRAIN = [2019, 2020, 2021, 2022]
TEST = [2023, 2024, 2025]
for md, label in (((1, 15), "15 Jan"), ((2, 15), "15 Feb")):
    rows = []
    for r in lab.itertuples():
        t = pd.Timestamp(r.season + 1, *md)
        g = obs[(obs.point_id == r.point_id) & (obs.season == r.season) & (obs.date <= t - pd.Timedelta(days=2))]
        if len(g) < 4:
            continue
        g = g.sort_values("date")
        v = g.ndvi.rolling(3, min_periods=1).median().to_numpy()
        doy_t = (t - pd.Timestamp(r.season, 10, 1)).days
        last, ld = v[-1], g.doy.iloc[-1]
        pk = v.max()
        pk_doy = g.doy.iloc[int(v.argmax())]
        def at(days):
            m = g.doy <= ld - days
            return v[m.to_numpy()][-1] if m.any() else np.nan
        use = [TRAIN.index(s) for s in TRAIN if s != r.season]
        with np.errstate(all="ignore"):
            norm_now = np.nanmean(P[pidx[r.point_id], use, min(ld, 212)])
            norm_peak = np.nanmax(np.nanmean(P[pidx[r.point_id], use, :], axis=0))
        f = dict(point_id=r.point_id, season=r.season, irr=r.irr, y=r.drought, ndvi=last, age=doy_t - ld,
                 peak=pk, days_since_peak=ld - pk_doy, drop_from_peak=pk - last, chg15=last - at(15), chg30=last - at(30),
                 anom=last - norm_now, peak_vs_normal=pk - norm_peak, normal_dry=r.normal_dry, doy=doy_t,
                 days_to_normal_dry=r.normal_dry - doy_t)
        f.update(weather(r.cell, r.season, t))
        rows.append(f)
    d = pd.DataFrame(rows)
    feats = [c for c in d.columns if c not in ("point_id", "season", "y")]
    tr, te = d[d.season.isin(TRAIN)], d[d.season.isin(TEST)]
    m = xgb.XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                          random_state=0, eval_metric="logloss",
                          scale_pos_weight=(1 - tr.y.mean()) / tr.y.mean())
    m.fit(tr[feats], tr.y)
    p = m.predict_proba(te[feats])[:, 1]
    pred = (p >= 0.5).astype(int)
    base = -te.anom  # simple baseline: below-normal greenness now
    print(f"\n=== issue {label}: train n={len(tr)} (drought {tr.y.mean():.0%}), test n={len(te)} (drought {te.y.mean():.0%})")
    print(f"XGBoost   AUC {roc_auc_score(te.y, p):.3f}  acc {accuracy_score(te.y, pred):.3f}  bal.acc {balanced_accuracy_score(te.y, pred):.3f}"
          f"  precision {precision_score(te.y, pred):.3f}  recall {recall_score(te.y, pred):.3f}  F1 {f1_score(te.y, pred):.3f}")
    print(f"Baseline (greenness below normal) AUC {roc_auc_score(te.y, base):.3f}")
    for s in TEST:
        q = te.season == s
        print(f"  {s}-{str(s+1)[2:]}: n {q.sum()}, drought {te.y[q].mean():.0%}, AUC {roc_auc_score(te.y[q], p[q]):.3f}, "
              f"recall {recall_score(te.y[q], pred[q]):.2f}, precision {precision_score(te.y[q], pred[q]):.2f}")
    imp = pd.Series(m.feature_importances_, feats).sort_values(ascending=False).head(8)
    print("top features:", ", ".join(f"{k} {v:.2f}" for k, v in imp.items()))
