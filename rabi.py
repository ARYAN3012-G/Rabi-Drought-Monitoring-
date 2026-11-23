"""Rabi regional drought-risk research workflow. Run `python rabi.py --help`."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description='Rabi regional soil-moisture drought risk, crop context and independent field checks.')
    sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('run',help='Create a dated report, predictions, map and immutable audit record')
    q.add_argument('--date',help='YYYY-MM-DD; defaults to today in India')
    q.add_argument('--update',action='store_true',help='Append available soil observations through issue minus eight days')
    q=sub.add_parser('update-soil',help='Append live soil data without altering frozen research data');q.add_argument('--through',required=True)
    q=sub.add_parser('import-satellite',help='Validate/import an Earth Engine observation export');q.add_argument('csv')
    q=sub.add_parser('make-satellite-script',help='Generate Earth Engine script for the frozen point catalogue')
    q.add_argument('--output',default='src/gee/script_D_live_points.js')
    q=sub.add_parser('verify',help='Verify saved artifacts and exactly reproduce predictions');q.add_argument('run_dir')
    q=sub.add_parser('observation-template',help='Create an empty field-observation template')
    q.add_argument('--output',default='observations/field_observations.csv')
    q=sub.add_parser('validate',help='Compare a run with independently collected field observations')
    q.add_argument('--run-dir',required=True);q.add_argument('--observations',required=True)
    q=sub.add_parser('detect',help='Run rabi early-drying risk model (detect_v5: soil moisture gate & crop priors)')
    q.add_argument('--compare',action='store_true',help='Compare lineage across v2, v3, v4, and v5')
    args=p.parse_args()
    try:
        if args.command=='run':
            from src.drought.operations import run
            run(args.date,args.update)
        elif args.command=='detect':
            from src.detect import causal_events_v5
            if args.compare:
                causal_events_v5.compare_all_versions()
            else:
                causal_events_v5.main()
        elif args.command=='update-soil':
            from src.drought.operations import normalize_date,local_today
            from src.drought.live_data import update_soil
            import pandas as pd
            through=normalize_date(args.through)
            if through>pd.Timestamp(local_today())-pd.Timedelta(days=8):raise ValueError('Use a cutoff at least eight days before today')
            print(json.dumps(update_soil(through),indent=2))
        elif args.command=='import-satellite':
            from src.drought.satellite_io import import_satellite
            print(json.dumps(import_satellite(args.csv),indent=2))
        elif args.command=='make-satellite-script':
            from src.drought.satellite_io import make_gee_script
            print(make_gee_script(args.output))
        elif args.command=='verify':
            from src.drought.operations import verify_run
            print(json.dumps(verify_run(args.run_dir),indent=2))
        elif args.command=='observation-template':
            from src.drought.field_validation import write_template
            print(write_template(args.output))
        elif args.command=='validate':
            from src.drought.field_validation import validate
            print(validate(args.run_dir,args.observations))
    except (ValueError,OSError,KeyError) as e:
        p.exit(1,f'Rabi workflow could not complete: {e}\n')

if __name__=='__main__':main()
