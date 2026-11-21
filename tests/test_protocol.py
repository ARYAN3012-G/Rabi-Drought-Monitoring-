"""Protocol v1 checks: no look-ahead, missing fields stay in, thresholds behave."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "rabi"))
import protocol as P  # noqa: E402


def test_no_look_ahead():
    obs = P.load_obs()
    s, issue = 2021, pd.Timestamp(2022, 2, 15)
    a = P.field_states(obs, s, issue)
    fake = obs[obs.date > issue - pd.Timedelta(days=P.SAT_DELAY_DAYS)].copy()
    fake["NDVI"] = 0.9 - fake["NDVI"]                      # change every later image
    b = P.field_states(pd.concat([obs[obs.date <= issue - pd.Timedelta(days=P.SAT_DELAY_DAYS)], fake]), s, issue)
    pd.testing.assert_frame_equal(a, b)


def test_all_frozen_fields_reported_even_without_images():
    obs = P.load_obs()
    st = P.field_states(obs[obs.field_id != obs.field_id.iloc[0]], 2021, pd.Timestamp(2022, 2, 15))
    assert len(st) == len(pd.read_csv(P.FROZEN))
    assert not st.set_index("field_id").loc[obs.field_id.iloc[0], "evaluable"]


def test_issue_dates_and_min_obs():
    assert P.issue_date(2026, (2, 15)) == pd.Timestamp(2027, 2, 15)
    assert P.min_obs(pd.Timestamp(2027, 1, 15), 2026) == 3
    assert P.min_obs(pd.Timestamp(2027, 2, 15), 2026) == 5
    assert P.min_obs(pd.Timestamp(2027, 3, 15), 2026) == 7
