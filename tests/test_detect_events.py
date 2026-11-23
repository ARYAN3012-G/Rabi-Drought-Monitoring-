"""Causality and distinct-event tests for the corrected rabi warning evaluation."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location('events_v2', Path(__file__).resolve().parents[1]/'src/detect/causal_events.py')
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)


def test_future_images_cannot_change_inputs():
    dates=pd.date_range('2023-10-01',periods=35,freq='5D')
    obs=pd.DataFrame({'date':dates,'ndvi':np.r_[np.linspace(.2,.7,18),np.linspace(.7,.2,17)]})
    issue=pd.Timestamp('2024-01-15'); normal=np.full(213,.45)
    a,reason=E.past_features(obs,2023,issue,180,normal)
    assert reason=='eligible'
    changed=obs.copy();changed.loc[changed.date>issue-pd.Timedelta(days=2),'ndvi']=9
    b,_=E.past_features(changed,2023,issue,180,normal)
    pd.testing.assert_series_equal(pd.Series(a),pd.Series(b))
    c,_=E.past_features(obs[obs.date<=issue-pd.Timedelta(days=2)],2023,issue,180,normal)
    pd.testing.assert_series_equal(pd.Series(a),pd.Series(c))


def test_validation_and_own_season_do_not_enter_reference():
    lab=pd.DataFrame({'point_id':['a']*7,'season':range(2019,2026),'quality_ok':True,
                      'est':True,'dry_doy':[150,160,170,100,110,120,130]})
    assert E.reference_stats(lab,'a',2019)==(2,165)
    lab.loc[lab.season>=2022,'dry_doy']=999
    lab.loc[lab.season==2019,'dry_doy']=888
    assert E.reference_stats(lab,'a',2019)==(2,165)


def test_unpublished_november_rain_is_not_used():
    rain=pd.Series(1.,index=pd.date_range('1979-01-01','2026-12-31'))
    before=E.rainfall_ratio(rain,2023,pd.Timestamp('2023-12-01'))
    rain.loc['2023-11-24':'2023-11-30']=100
    assert E.rainfall_ratio(rain,2023,pd.Timestamp('2023-12-01'))==before
    assert E.rainfall_ratio(rain,2023,pd.Timestamp('2023-12-11'))>before


def fixture():
    labels=pd.DataFrame({'point_id':['hit','late','no_opportunity','negative'], 'season':2023,
        'cell':'c','irr':0,'scorable':True,'early':[True,True,True,False],
        'event_date':pd.to_datetime(['2024-02-01','2024-02-01','2024-02-01',None])})
    pred=pd.DataFrame({'point_id':['hit','hit','hit','late','negative'],'season':2023,
        'issue_date':pd.to_datetime(['2024-01-02','2024-01-20','2024-02-01','2024-02-03','2024-01-10']),
        'observed_dry':0,'warn':True})
    return labels,pred


def test_repeated_warnings_are_one_event_and_one_warned_unit():
    lab,pred=fixture();e=E.event_records(lab,pred,30,'m');s=E.event_summary(e)
    assert s['monitored_events']==3
    assert s['caught_events']==1
    assert s['warned_point_seasons']==3
    assert s['events_with_opportunity']==1
    assert s['recall_all_events']==1/3
    assert s['recall_opportunity']==1
    assert s['warning_precision']==1/3
    assert s['median_lead']==30
    assert e.set_index('point_id').loc['hit','n_timely_warnings']==2


def test_horizon_and_onset_boundaries():
    lab,pred=fixture();e=E.event_records(lab,pred,7,'m')
    assert not e.hit.any()  # January 20 is >7 days ahead; same-day and late are not advance warnings
    assert e.warned.sum()==3


def test_observed_dry_suppresses_operational_warning():
    lab,pred=fixture();pred['observed_dry']=1
    e=E.event_records(lab,pred,30,'m')
    assert not e.warned.any()
    assert e.event.sum()==3
    assert not e.opportunity.any()


def test_outcome_columns_are_not_features():
    assert not set(E.FEATURES)&{'status_t','early','early_season','dry_doy','event_date','scorable','at_risk'}


def test_no_recent_image_abstains():
    obs=pd.DataFrame({'date':pd.to_datetime(['2023-10-01','2023-10-10']), 'ndvi':[.2,.7]})
    f,reason=E.past_features(obs,2023,pd.Timestamp('2024-01-15'),180,np.ones(213)*.4)
    assert f is None and reason=='no recent observation'
