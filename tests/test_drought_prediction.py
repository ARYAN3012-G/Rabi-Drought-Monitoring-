"""Causal cutoffs and independently defined targets for soil-moisture forecasts."""
import importlib.util
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

spec=importlib.util.spec_from_file_location('drought_model',Path(__file__).resolve().parents[1]/'src/drought/model.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)

def fixture():
    dates=pd.date_range('2001-01-01','2003-04-30')
    soil=pd.DataFrame({'date':dates,'cell':'c','rootzone':.3+.03*np.sin(np.arange(len(dates))/40),
        'soil_moisture_0_to_7cm_mean':.25,'soil_moisture_28_to_100cm_mean':.35})
    refs={'c':[np.linspace(.1,.5,500) for _ in range(365)]}
    weather=pd.DataFrame({'Precipitation_Flux':2.,'ReferenceET_PenmanMonteith_FAO56':3.,
        'Temperature_Air_2m_Max_24h':300.},index=dates)
    return soil,refs,weather

def test_future_weather_and_soil_do_not_change_forecast_features():
    s,r,w=fixture();issue=pd.Timestamp('2002-01-15');cut=issue-pd.Timedelta(days=8)
    a,reason=M.features_at(M.prepare_soil(s,r)['c'],w,issue,15,0);assert reason=='ok'
    s.loc[s.date>cut,'rootzone']=.99;w.loc[w.index>cut,:]=999
    b,reason=M.features_at(M.prepare_soil(s,r)['c'],w,issue,15,0)
    assert a==b

def test_reference_excludes_all_post_2000_data():
    dates=pd.date_range('1981-01-01','2002-12-31')
    s=pd.DataFrame({'date':dates,'cell':'c','rootzone':np.linspace(.1,.5,len(dates))})
    a=M.fit_reference(s)
    s.loc[s.date>='2001-01-01','rootzone']=999
    b=M.fit_reference(s)
    for x,y in zip(a['c'],b['c']):np.testing.assert_array_equal(x,y)

def test_percentile_midrank_and_leap_day():
    ref=[np.array([1.,2.,2.,3.]) for _ in range(365)]
    np.testing.assert_allclose(M.percentile([2.,0.,4.],['2020-02-29','2020-03-01','2020-03-01'],ref),[50.,0.,100.])
    assert M.calendar_bin(['2020-02-28'])[0]==M.calendar_bin(['2020-02-29'])[0]
    assert M.calendar_bin(['2020-03-01'])[0]==M.calendar_bin(['2021-03-01'])[0]

def test_missing_or_unpublished_input_abstains():
    s,r,w=fixture();issue=pd.Timestamp('2002-01-15');cut=issue-pd.Timedelta(days=8)
    gs=M.prepare_soil(s,r)['c'];assert M.features_at(gs,w,issue,15,0)[0] is not None
    assert M.features_at(gs[gs.index<cut],w,issue,15,0)[1]=='missing/stale soil'
    w.loc[cut,'Precipitation_Flux']=np.nan
    assert M.features_at(gs,w,issue,15,0)[1]=='missing/stale weather'

def test_entire_target_window_is_future_and_seasons_do_not_overlap():
    for season in M.TRAIN+M.VAL+M.TEST:
        for issue in pd.date_range(f'{season}-12-01',f'{season+1}-03-31',freq='5D'):
            for h in M.HORIZONS:
                assert issue+pd.Timedelta(days=h-6)>issue
    assert max(M.TRAIN)<min(M.VAL) and max(M.VAL)<min(M.TEST)
    assert pd.Timestamp(max(M.TRAIN)+1,4,30)<pd.Timestamp(min(M.VAL),12,1)

def test_alert_threshold_obeys_validation_recall_constraint():
    y=np.array([0,0,0,0,1,1,1,1]);p=np.array([.1,.2,.3,.4,.3,.6,.8,.9])
    t=M.choose_threshold(y,p)
    assert ((p>=t)&(y==1)).sum()/y.sum()>=.5
    assert t>.3  # low-score positives are traded for fewer false warnings

def test_target_and_future_columns_not_in_feature_schema():
    assert not set(M.FEATURES)&{'target','target_percentile','issue_percentile','target_start','split'}
    np.testing.assert_array_equal(M.drought_class([0,10,10.1,20,20.1,100]),[2,2,1,1,0,0])

def test_persistence_cannot_become_always_warn_to_meet_recall_floor():
    c=M.Candidate('persistence',kind='persistence')
    assert M.operating_threshold(c,[0,1,1,1],[0,0,0,1])==.5

def test_no_drought_events_are_unestimable_not_perfect_detection():
    r=M.metrics([0,0],np.array([[1.,0,0],[1.,0,0]]),.5)
    assert np.isnan(r['recall']) and np.isnan(r['precision'])
    assert np.isnan(r['drought_auc']) and np.isnan(r['drought_ap'])

def test_inference_cannot_use_model_selected_after_its_issue_date():
    assert not M.issue_allowed('2020-01-15')[0]
    assert not M.issue_allowed('2026-11-23')[0]
    assert M.issue_allowed('2026-12-01')[0]
