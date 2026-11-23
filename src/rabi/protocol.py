"""
Rabi monitoring protocol v1 - the rules (docs/PROTOCOL_v1.md). Constants here are FROZEN for rabi 2026-27.

For an issue date D, only Sentinel-2 images dated <= D - SAT_DELAY_DAYS are used (no look-ahead).

Per field, season y (1 Oct y .. 30 Apr y+1):
  monthly median NDVI for Oct .. Apr (the current month uses the images so far)
  trough T   = lowest monthly median of Oct, Nov, Dec;  its month = m_T
  green-up G = highest monthly median of the months after m_T (up to D)
  ESTABLISHED   G - T >= RISE and G > GREEN               (same shape rule as script C1 v2)
  EVALUABLE     >= 2 of Oct-Dec months observed, >= 1 month after m_T observed and
                >= min_obs(D) clear images between 1 Dec and D
Per unit = site x class (rainfed / irrigated), needs >= MIN_FIELDS evaluable fields:
  Signal 1 (establishment) share = established / evaluable; normal = mean share in the reference
          seasons at the same day of the season; FLAG if share < EST_RATIO x normal
  Signal 2 (condition)    per established field G / (its mean G in reference seasons in which it was
          established at the same day, >= 2 seasons); FLAG if the median over >= MIN_COND_FIELDS
          fields < COND_RATIO
  Reference seasons are compared with the other reference seasons only (leave-one-season-out).
Wet guard: if Sep-Nov rain at the site's weather cell > WET_GUARD x its 1979-2011 mean, an
establishment flag is reported as WET-DELAY (late/no sowing after excess rain), not as drought.
Unit FLAG = signal 1 (not wet-guarded) or signal 2 flags. Site FLAG = any valid unit flags; OK = >= 1 valid unit, none
flags; INSUFFICIENT = no valid unit. Mandal FLAG = any of its sites flags.
"""
from __future__ import annotations

from pathlib import Path

import os

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TS_FILE = ROOT / "data" / "gee_exports" / "C2_candidate_timeseries_v2.csv"
FROZEN = ROOT / "data" / "frozen" / "fields_v1.csv"
DECL = ROOT / "data" / "official" / "rabi_declarations.csv"
SITES_FILE = ROOT / "data" / "sites.csv"
WEATHER_DIR = Path(os.environ.get("WEATHER_DIR", ROOT / "data" / "processed" / "weather"))

# ---- FROZEN constants (protocol v1) -------------------------------------------------------
REF_SEASONS = [2019, 2020, 2021, 2022]          # season y = 1 Oct y .. 30 Apr y+1
ISSUE_DAYS = [(1, 15), (2, 15), (3, 15)]        # 15 Jan, 15 Feb (PRIMARY), 15 Mar
PRIMARY_ISSUE = (2, 15)
SAT_DELAY_DAYS = 2
MIN_CLEAR = 0.6                                 # clear fraction of the field (as the satellite module)
CLEAR_REF_END = "2023-04-30"                    # 100 % = clearest image up to here (frozen)
RISE, GREEN = 0.15, 0.35
MIN_FIELDS = 10                                 # evaluable fields per unit
MIN_COND_FIELDS = 5
EST_RATIO = 0.75                                # flag: establishment share < 75 % of normal
COND_RATIO = 0.85                               # flag: median greenness < 85 % of own normal
MIN_REF_SEASONS = 2
WET_GUARD = 1.5                                 # Sep-Nov rain > 150 % of 1979-2011 mean
PRIMARY_NOTE = "15 Feb = primary (scored), 15 Mar = secondary (scored), 15 Jan = informational"
SEASON_MONTHS = [10, 11, 12, 1, 2, 3, 4]
SITE_MANDAL = {"Som": "Somandepalli", "Lep": "Lepakshi", "Cho": "Lepakshi", "Sira": "Sira taluk",
               "Ped": "Adoni / Pedda Kadubur", "Din": "Kurnool Rural", "Bal": "Kurnool Urban", "Pul": "Kurnool Urban"}
# Amendment A1 (21 Nov 2026, before the season, after the mandal boundary check
# Sentinel2-Drought-Confirmation/results/qc/MANDAL_CHECK.md): 25 of Ped's 40 rabi fields lie in Pedda Kadubur,
# 15 in Adoni. Ped is scored only when both mandals have the same official status; otherwise "Ambiguous".
SITES = ["Som", "Lep", "Cho", "Sira", "Ped", "Din", "Bal", "Pul"]


def min_obs(issue: pd.Timestamp, season: int) -> int:
    days = (issue - pd.Timestamp(season, 12, 1)).days
    return max(3, days // 14)


def issue_date(season: int, md: tuple[int, int]) -> pd.Timestamp:
    m, d = md
    return pd.Timestamp(season + (1 if m <= 9 else 0), m, d)


def load_obs(path: Path = TS_FILE) -> pd.DataFrame:
    """Clean observations of the FROZEN fields: clear fraction, NDVI range, one image per field and day."""
    raw = pd.read_csv(path, parse_dates=["date"])
    raw = raw.rename(columns=lambda c: c[:-5] if c.endswith("_mean") else c)
    frozen = pd.read_csv(FROZEN)
    raw = raw[raw.field_id.isin(frozen.field_id)]
    full = raw[raw.date <= CLEAR_REF_END].groupby("field_id").NDVI_count.max()
    raw["clear_frac"] = (raw.NDVI_count / raw.field_id.map(full)).clip(upper=1)
    d = raw[(raw.clear_frac >= MIN_CLEAR) & raw.NDVI.between(-0.2, 1.0)]
    d = d.sort_values("clear_frac").drop_duplicates(["field_id", "date"], keep="last")
    return d[["field_id", "date", "NDVI"]].sort_values(["field_id", "date"]).reset_index(drop=True)


def field_states(obs: pd.DataFrame, season: int, issue: pd.Timestamp) -> pd.DataFrame:
    """One row per frozen field: evaluable, established, G - using images dated <= issue - delay."""
    cut = issue - pd.Timedelta(days=SAT_DELAY_DAYS)
    o = obs[(obs.date >= pd.Timestamp(season, 10, 1)) & (obs.date <= cut)].copy()
    o["k"] = o.date.dt.month.map({m: i for i, m in enumerate(SEASON_MONTHS)})
    o = o.dropna(subset=["k"])
    mon = o.groupby(["field_id", "k"]).NDVI.median().unstack("k").reindex(columns=range(7))
    n_win = o[o.date >= pd.Timestamp(season, 12, 1)].groupby("field_id").size()
    need = min_obs(issue, season)
    frozen = pd.read_csv(FROZEN)[["field_id", "site_code", "class"]].rename(columns={"class": "cls"})
    rows = []
    for f in frozen.itertuples(index=False):
        ev = est = False
        g = np.nan
        if f.field_id in mon.index:
            v = mon.loc[f.field_id].to_numpy(float)
            early = v[:3]
            if np.isfinite(early).sum() >= 2:
                t = int(np.nanargmin(early))
                after = v[t + 1:]
                if np.isfinite(after).any() and n_win.get(f.field_id, 0) >= need:
                    ev = True
                    g = float(np.nanmax(after))
                    est = (g - early[t] >= RISE) and (g > GREEN)
        rows.append(dict(field_id=f.field_id, site_code=f.site_code, cls=f.cls,
                         evaluable=ev, established=bool(est), G=g if est else np.nan))
    out = pd.DataFrame(rows)
    out["season"], out["issue"] = season, issue
    return out


def all_states(obs: pd.DataFrame, seasons: list[int], md: tuple[int, int]) -> pd.DataFrame:
    return pd.concat([field_states(obs, s, issue_date(s, md)) for s in seasons], ignore_index=True)


_rain_cache: dict = {}


def sep_nov_rain_ratio(site: str, season: int) -> float:
    """Sep-Nov rain of `season` / mean Sep-Nov rain 1979-2011 (AgERA5 cell of the site); NaN if missing."""
    wf = pd.read_csv(SITES_FILE).set_index("site_code").weather_file[site]
    if wf not in _rain_cache:
        f = WEATHER_DIR / f"{wf}_with_spei.csv"
        if not f.exists():
            return np.nan
        _rain_cache[wf] = pd.read_csv(f, usecols=["valid_time", "Precipitation_Flux"],
                                      parse_dates=["valid_time"]).set_index("valid_time").Precipitation_Flux
    p = _rain_cache[wf]
    tot = lambda y: p[f"{y}-09-01":f"{y}-11-30"]
    cur = tot(season)
    if cur.index.max() < pd.Timestamp(season, 11, 30):
        return np.nan
    return float(cur.sum() / np.mean([tot(y).sum() for y in range(1979, 2012)]))


def unit_status(states: pd.DataFrame, ref: pd.DataFrame, season: int) -> pd.DataFrame:
    """states: field states of `season`; ref: field states of the reference seasons (same issue day)."""
    ref = ref[ref.season.isin(REF_SEASONS) & (ref.season != season)]
    rows = []
    for (site, cls), g in states.groupby(["site_code", "cls"]):
        r = ref[(ref.site_code == site) & (ref.cls == cls)]
        n_ev, n_est = int(g.evaluable.sum()), int(g.established.sum())
        share = n_est / n_ev if n_ev else np.nan
        rs = r.groupby("season").agg(n_ev=("evaluable", "sum"), n_est=("established", "sum"))
        rs = rs[rs.n_ev >= MIN_FIELDS]
        normal = (rs.n_est / rs.n_ev).mean() if len(rs) >= MIN_REF_SEASONS else np.nan
        est_valid = n_ev >= MIN_FIELDS and np.isfinite(normal) and normal > 0
        est_ratio = share / normal if est_valid else np.nan
        fn = r[r.established].groupby("field_id").G.agg(["mean", "size"])
        fn = fn[fn["size"] >= MIN_REF_SEASONS]["mean"]
        cur = g[g.established].set_index("field_id").G
        ratios = (cur / fn.reindex(cur.index)).dropna()
        cond_valid = n_ev >= MIN_FIELDS and len(ratios) >= MIN_COND_FIELDS
        cond = float(ratios.median()) if cond_valid else np.nan
        rain = sep_nov_rain_ratio(site, season)
        est_low = bool(est_valid and est_ratio < EST_RATIO)
        wet = bool(est_low and np.isfinite(rain) and rain > WET_GUARD)
        est_flag = est_low and not wet
        cond_flag = bool(cond_valid and cond < COND_RATIO)
        if not (est_valid or cond_valid):
            status = "INSUFFICIENT"
        elif est_flag or cond_flag:
            status = "FLAG"
        else:
            status = "WET-DELAY" if wet else "OK"
        rows.append(dict(season=season, site_code=site, cls=cls, fields=len(g), evaluable=n_ev,
                         established=n_est, share=share, normal_share=normal, est_ratio=est_ratio,
                         est_flag=est_flag, sep_nov_rain_ratio=rain, wet_delay=wet, cond_fields=len(ratios),
                         cond_median=cond, cond_flag=cond_flag, status=status))
    return pd.DataFrame(rows)


def site_status(units: pd.DataFrame) -> pd.DataFrame:
    """FLAG if any valid unit flags; OK otherwise (WET-DELAY units count as not flagged, noted)."""
    rows = []
    for (season, site), g in units.groupby(["season", "site_code"]):
        valid = g[g.status != "INSUFFICIENT"]
        st = "INSUFFICIENT" if valid.empty else ("FLAG" if (valid.status == "FLAG").any() else "OK")
        why = "; ".join(f"{r.cls}: " + " + ".join(k for k, on in (("establishment", r.est_flag),
                                                                  ("condition", r.cond_flag)) if on)
                        for r in valid.itertuples() if r.status == "FLAG")
        wet = ", ".join(valid[valid.status == "WET-DELAY"].cls)
        rows.append(dict(season=season, site_code=site, status=st, valid_units=", ".join(valid.cls),
                         flagged_by=why, wet_delay=wet))
    s = pd.DataFrame(rows)
    s["mandal"] = s.site_code.map(SITE_MANDAL)
    return s


def mandal_status(sites: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (season, mandal), g in sites.groupby(["season", "mandal"]):
        v = g[g.status != "INSUFFICIENT"]
        st = "INSUFFICIENT" if v.empty else ("FLAG" if (v.status == "FLAG").any() else "OK")
        rows.append(dict(season=season, mandal=mandal, status=st, sites=", ".join(g.site_code + ":" + g.status)))
    return pd.DataFrame(rows)


def run(obs: pd.DataFrame, seasons: list[int], md: tuple[int, int]):
    """Unit, site and mandal status for each season at issue day md."""
    ref = all_states(obs, REF_SEASONS, md)
    units = []
    for s in seasons:
        st = ref[ref.season == s] if s in REF_SEASONS else field_states(obs, s, issue_date(s, md))
        units.append(unit_status(st, ref, s))
    units = pd.concat(units, ignore_index=True)
    sites = site_status(units)
    return units, sites, mandal_status(sites)


def md_table(t: pd.DataFrame) -> str:
    """Markdown table without extra dependencies."""
    rows = ["| " + " | ".join(map(str, t.columns)) + " |", "|" + "---|" * len(t.columns)]
    return "\n".join(rows + ["| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |"
                              for r in t.itertuples(index=False)])
