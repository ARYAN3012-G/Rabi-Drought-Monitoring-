"""Leakage, timing, season-boundary and missing-data tests for rabi drought v2 (docs/DROUGHT2_v1.md)."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
import os
D2 = Path(os.environ.get("DROUGHT2_DATA", ROOT / "data" / "drought2"))
need = pytest.mark.skipif(not (D2 / "forecast_instances.csv.gz").exists(), reason="drought2 data not built")


@pytest.fixture(scope="module")
def inst():
    return pd.read_csv(D2 / "forecast_instances.csv.gz", parse_dates=["issue_date", "input_cutoff"])


@pytest.fixture(scope="module")
def daily():
    return pd.read_csv(D2 / "daily_district.csv.gz", parse_dates=["date"])


@need
def test_inputs_end_eight_days_before_issue(inst):
    ok = inst[inst.status == "ok"]
    assert ((ok.issue_date - ok.input_cutoff).dt.days == 8).all()


@need
def test_features_use_only_past_and_target_only_future(inst, daily):
    ok = inst[inst.status == "ok"].sample(40, random_state=1)
    for r in ok.itertuples():
        q = daily[daily.district == r.district].set_index("date").deficit_area
        past = q[:r.input_cutoff]
        assert np.isclose(past.tail(15).mean(), r.area_15)
        fut = q[r.issue_date + pd.Timedelta(days=1):r.issue_date + pd.Timedelta(days=15)]
        assert len(fut) == 15 and fut.index.min() > r.issue_date
        assert np.isclose(fut.mean(), r.target_mean)


@need
def test_missing_inputs_are_not_turned_into_no_deficit(inst):
    bad = inst[inst.status != "ok"]
    if len(bad):
        assert bad.target.isna().all()


@need
def test_splits_are_disjoint_whole_seasons():
    from src.drought2.forecast import EVAL, TRAIN, VAL
    assert not set(TRAIN) & set(VAL) and not set(VAL) & set(EVAL) and not set(TRAIN) & set(EVAL)
    assert max(TRAIN) < min(VAL) < min(EVAL)


@need
def test_issue_dates_within_rabi_window(inst):
    m = inst.issue_date.dt.month
    assert m.isin([12, 1, 2, 3]).all()
    assert ((inst.issue_date.dt.year - (m <= 8).astype(int)) == inst.season).all()


def test_percentile_reference_is_reference_seasons_only():
    from src.drought2.indicators import REF, percentiles
    rng = np.random.default_rng(0)
    rows = []
    for s in range(1990, 2023):
        for d in pd.date_range(f"{s}-09-01", f"{s + 1}-04-30"):
            rows.append(dict(gid="X", date=d, season=s, rz7=rng.random() + (5 if s not in REF else 0)))
    g = pd.DataFrame(rows)
    g["cday"] = g.date.dt.dayofyear
    g = percentiles(g)
    # non-reference seasons are all far wetter than the reference -> percentile near 1, never computed from themselves
    assert g[~g.season.isin(REF)].pct.min() > 0.99
    assert g[g.season.isin(REF)].pct.between(0, 1).all()


def test_missing_soil_gives_missing_percentile():
    from src.drought2.indicators import percentiles
    d = pd.date_range("1995-09-01", "1996-04-30")
    g = pd.DataFrame(dict(gid="X", date=d, season=1995, rz7=np.nan))
    g["cday"] = g.date.dt.dayofyear
    g = percentiles(g)
    assert g.pct.isna().all() and g.deficit.isna().all()


@pytest.mark.skipif(not (D2 / "yields_crop.csv").exists(), reason="yields not built")
def test_yield_anomaly_uses_previous_seasons_only():
    c = pd.read_csv(D2 / "yields_crop.csv")
    q = c[(c.district == "Kurnool") & (c.crop == "Gram")].set_index("season").sort_index()
    for s in q.index[5:10]:
        prev = q.loc[[x for x in q.index if s - 5 <= x < s], "yield_t_ha"]
        assert np.isclose(q.loc[s, "yield_t_ha"] / prev.median() - 1, q.loc[s, "yield_anom"])
