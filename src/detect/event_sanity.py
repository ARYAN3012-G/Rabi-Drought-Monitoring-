"""Independent saved-result checks and an explicit always-warn burden comparison.

Run after causal_events.py. This diagnostic was added after viewing v2 results;
it does not fit models, change thresholds, or select a model on evaluation data.
"""
from pathlib import Path
import hashlib
import json

import pandas as pd

from causal_events import (ROOT, DATA, OUT, HORIZONS, TEST, event_records,
                           event_summary, md_table)


def main():
    p=pd.read_csv(OUT/'predictions.csv.gz',parse_dates=['issue_date','event_date'])
    l=pd.read_csv(DATA/'labels.csv',parse_dates=['event_date'])
    l=l[l.season.isin(TEST)]
    metrics=pd.read_csv(OUT/'event_metrics.csv')
    assert not p.duplicated(['point_id','season','issue_date','horizon','model']).any()
    rows=[]
    for h in HORIZONS:
        q=p[(p.horizon==h)&p.selected].copy()
        target=q.early&(q.issue_date<q.event_date)&(q.event_date<=q.issue_date+pd.Timedelta(days=h))
        assert (target.to_numpy()==q.target.to_numpy()).all()
        matched=q[q.warn&target]
        hit=matched.groupby(['point_id','season']).agg(first=('issue_date','min'),event=('event_date','first'))
        saved=metrics[(metrics.horizon==h)&(metrics.season=='pooled')&metrics.selected].iloc[0]
        assert len(hit)==saved.caught_events
        assert (hit.event-hit['first']).dt.days.median()==saved.median_lead
        assert len(q[q.warn][['point_id','season']].drop_duplicates())==saved.warned_point_seasons
        q['warn']=q.observed_dry==0
        always=event_summary(event_records(l,q,h,'Always warn diagnostic'))
        rows.append(dict(horizon=h,selected_model=saved.model,
            model_caught=int(saved.caught_events),always_caught=always['caught_events'],
            total_events=int(saved.monitored_events),model_warned_units=int(saved.warned_point_seasons),
            always_warned_units=always['warned_point_seasons'],
            model_unit_precision=saved.warning_precision,always_unit_precision=always['warning_precision'],
            model_first_timely_lead=saved.median_lead,always_first_timely_lead=always['median_lead']))
    table=pd.DataFrame(rows);table.to_csv(OUT/'always_warn_comparison.csv',index=False)
    path=OUT/'EVENT_REPORT.md';text=path.read_text(encoding='utf-8')
    heading='## Always-warn sanity check (added after the primary v2 run)'
    if heading in text:text=text[:text.index(heading)]
    text+='\n'+heading+'\n\n'+md_table(table)+'\n\n'
    text+=('Always warning at every usable issue can also catch almost every event. Therefore high unique-event '
        'recall and the first-timely lead alone are not evidence of strong discrimination. The selected model reduces '
        'the number of warned point-seasons, but still produces many false warnings. This fixed diagnostic did not '
        'alter the selected models, fitted parameters or thresholds.\n')
    path.write_text(text,encoding='utf-8')
    files=[ROOT/'src/detect/causal_events.py',Path(__file__),ROOT/'docs/DETECT_v2.md',
           ROOT/'tests/test_detect_events.py',DATA/'labels.csv',DATA/'instances.csv.gz',
           OUT/'operating_points.json',OUT/'predictions.csv.gz',OUT/'validation_predictions.csv.gz',OUT/'events.csv']
    hashes={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    for cell in p.cell.unique():
        f=ROOT/f'data/prepared/{cell}.csv'
        hashes[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
    (OUT/'audit_checks.json').write_text(json.dumps({'duplicate_prediction_keys':0,
        'independent_event_aggregation':'passed at all three horizons',
        'target_window_consistency':'passed', 'sha256':hashes},indent=2),encoding='utf-8')
    print(table.to_string(index=False))


if __name__=='__main__':main()
