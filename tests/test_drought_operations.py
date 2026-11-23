"""Operational failure cases, frozen data protection and field scoring."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import pytest
from src.drought import model as M
from src.drought.live_data import append_checked,LAYERS
from src.drought.satellite_io import context_at,clean_observations
from src.drought.field_validation import score_observations
from src.drought.operations import normalize_date

def soil_fixture():
    d=pd.DataFrame({'date':pd.date_range('2026-01-01',periods=4),'cell':'c'})
    for c in LAYERS:d[c]=.3
    return d

def test_update_checks_overlap_and_rejects_revisions():
    d=soil_fixture();assert len(append_checked(d.iloc[:2],d.iloc[1:]))==2
    altered=d.iloc[1:].copy();altered.loc[1,LAYERS[0]]=.4
    with pytest.raises(ValueError,match='revised'):append_checked(d.iloc[:2],altered)

def test_update_rejects_gaps_missing_layers_and_duplicate_dates():
    d=soil_fixture()
    with pytest.raises(ValueError,match='contiguous'):append_checked(d.iloc[:2],d.iloc[[1,3]])
    bad=d.iloc[1:].copy();bad.loc[2,LAYERS[1]]=np.nan
    with pytest.raises(ValueError,match='Missing'):append_checked(d.iloc[:2],bad)
    with pytest.raises(ValueError,match='Duplicate'):append_checked(d.iloc[:2],pd.concat([d,d.iloc[:1]]))

def test_soil_only_model_does_not_require_unused_weather():
    dates=pd.date_range('2025-01-01','2026-02-01')
    raw=pd.DataFrame({'date':dates,'cell':'c','rootzone':.3,LAYERS[0]:.3,LAYERS[2]:.3})
    refs={'c':[np.linspace(.1,.5,500) for _ in range(365)]};soil=M.prepare_soil(raw,refs)['c']
    a,reason=M.features_at(soil,None,'2026-01-15',15,0,require_weather=False)
    assert reason=='ok' and np.isfinite(a['soil_pct']) and np.isnan(a['rain30'])
    assert M.features_at(soil,None,'2026-01-15',15,0,require_weather=True)[1]=='missing/stale weather'

def fixtures():
    points=pd.DataFrame({'point_id':['a','b'],'mandal':'M','irr':[0,1],'lat':14.,'lon':77.})
    cells=pd.DataFrame({'cell':['c'],'latitude':[14.],'longitude':[77.]})
    regional=pd.DataFrame({'cell':['c'],'horizon':[15],'status':['missing/stale soil'],'warning':[pd.NA],
        'issue_date':['2026-01-15'],'target_start':['2026-01-24'],'target_date':['2026-01-30']})
    obs=pd.DataFrame({'point_id':['a','a'],'date':pd.to_datetime(['2025-12-01','2026-01-20']),'ndvi':[.2,.8]})
    return points,cells,regional,obs

def test_future_images_and_stale_soil_never_turn_into_a_healthy_verdict():
    pts,cells,r,obs=fixtures();a=context_at(r,'2026-01-15',pts,obs,cells)
    assert len(a)==2 and a.ndvi.isna().all()
    assert a.vegetation_context.str.startswith('unknown').all()
    assert a.interpretation.eq('regional forecast unavailable').all()
    assert a.field_drought_assessment.eq('not independently assessed').all()
    obs.loc[obs.date>'2026-01-13','ndvi']=-.2
    pd.testing.assert_frame_equal(a,context_at(r,'2026-01-15',pts,obs,cells))

def test_satellite_cleaning_uses_quality_and_best_duplicate():
    raw=pd.DataFrame({'point_id':['a']*4,'date':['2026-01-10']*4,'mean':[.4,.5,.6,2.], 'count':[11,12,16,16]})
    out=clean_observations(raw);assert len(out)==1 and out.iloc[0].ndvi==.6

def test_field_truth_must_be_independent_and_in_the_future_target_window():
    pts,cells,r,obs=fixtures();r['status']='ok';r['warning']=True
    p=context_at(r,'2026-01-15',pts,obs,cells)
    visits=pd.DataFrame({'observation_id':['old','hit','unknown'],'point_id':['a','a','b'],
        'observation_date':['2026-01-15','2026-01-25','2026-01-25'],
        'drought_assessment':['no','yes','unknown'],'independent_of_model':['yes','yes','unknown'],'assessment_method':['visit','visit',''],
        'evidence_notes':['before target window','crop water stress assessed','']})
    score,matched=score_observations(p,visits)
    assert len(matched)==1 and matched.iloc[0].observation_id=='hit'
    assert score.iloc[0].tp==1 and score.iloc[0].matched_assessments==1
    visits.loc[1,'evidence_notes']=''
    with pytest.raises(ValueError,match='evidence'):score_observations(p,visits)

def test_no_field_visits_means_unknown_accuracy():
    pts,cells,r,obs=fixtures();r['status']='ok';r['warning']=True
    p=context_at(r,'2026-01-15',pts,obs,cells)
    empty=pd.DataFrame(columns=['observation_id','point_id','observation_date','drought_assessment','independent_of_model','assessment_method','evidence_notes'])
    score,matched=score_observations(p,empty)
    assert len(matched)==0 and score.iloc[0].matched_assessments==0
    assert np.isnan(score.iloc[0].recall) and np.isnan(score.iloc[0].precision)

def test_model_derived_assessments_cannot_be_counted_as_independent_truth():
    pts,cells,r,obs=fixtures();r['status']='ok';r['warning']=True
    p=context_at(r,'2026-01-15',pts,obs,cells)
    visit=pd.DataFrame({'observation_id':['v'],'point_id':['a'],'observation_date':['2026-01-25'],
        'drought_assessment':['yes'],'independent_of_model':['no'],'assessment_method':['model result'],'evidence_notes':['score high']})
    scores,matched=score_observations(p,visit)
    assert len(matched)==0 and scores.matched_assessments.sum()==0

def test_dates_do_not_silently_accept_timezone_or_time():
    assert normalize_date('2026-01-15')==pd.Timestamp('2026-01-15')
    with pytest.raises(ValueError):normalize_date('2026-01-15T12:00:00')
    with pytest.raises(ValueError):normalize_date('2026-01-15T00:00:00+05:30')

def test_report_handles_unavailable_warnings_and_no_update(tmp_path):
    from src.drought.report import write_report
    issue=pd.Timestamp('2026-11-23')
    r=pd.DataFrame({'cell':['c'],'horizon':[15],'status':['outside Dec-Mar monitoring season'],
        'warning':[pd.NA],'drought_risk_score':[np.nan],'forecast_class':['unavailable'],
        'forecast_mode':['dated research monitoring']})
    readiness=pd.DataFrame({'cell':['c'],'required_cutoff':[issue-pd.Timedelta(days=8)],
        'soil_available_through':[issue-pd.Timedelta(days=8)],'soil_available_by_cutoff':[issue-pd.Timedelta(days=8)],
        'weather_available_through':[pd.NaT],'weather_required_by_selected_model':[False]})
    write_report(tmp_path,issue,r,pd.DataFrame(),readiness,{},
        {'point_population':0,'points_with_recent_satellite_image':0,'update':None})
    html=(tmp_path/'report.html').read_text(encoding='utf-8')
    assert 'Not assessed' in html and '&lt;NA&gt;' not in html
