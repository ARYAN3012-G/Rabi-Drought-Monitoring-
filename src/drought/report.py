"""Self-contained local HTML report; no external services or tracking."""
from html import escape
from pathlib import Path
import numpy as np
import pandas as pd

def table(frame):
    return frame.to_html(index=False,border=0,na_rep='Unavailable',float_format=lambda v:f'{v:.3f}',escape=True)

def trend_svg(series,title):
    s=series.dropna().tail(90);w,h=500,175;left,top,right,bottom=40,28,16,30
    x=lambda i:left+i/max(len(s)-1,1)*(w-left-right)
    y=lambda v:top+(100-v)/100*(h-top-bottom)
    parts=[f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)} soil moisture percentile"><title>{escape(title)}</title>',
        f'<text x="{left}" y="16" font-size="12" font-weight="600">{escape(title)}</text>']
    for pct,color in [(100,'#ccd5df'),(50,'#ccd5df'),(20,'#d88425'),(10,'#b83030'),(0,'#ccd5df')]:
        parts.append(f'<line x1="{left}" x2="{w-right}" y1="{y(pct)}" y2="{y(pct)}" stroke="{color}" stroke-dasharray="3 3"/><text x="8" y="{y(pct)+4}" font-size="10">{pct}</text>')
    if len(s):
        line=' '.join(f'{x(i):.1f},{y(v):.1f}' for i,v in enumerate(s))
        parts.append(f'<polyline fill="none" stroke="#176e88" stroke-width="2" points="{line}"/>')
        parts.append(f'<text x="{left}" y="{h-7}" font-size="10">{s.index[0]:%d %b %Y}</text><text x="{w-right}" y="{h-7}" text-anchor="end" font-size="10">{s.index[-1]:%d %b %Y}</text>')
    return ''.join(parts)+'</svg>'

def write_report(folder,issue,regional,points,readiness,groups,manifest):
    valid=regional.status.eq('ok');warning=regional.warning.eq(True)
    mode='Historical replay' if regional.forecast_mode.eq('historical replay').all() else 'Dated research monitoring'
    main=regional[regional.horizon==15]
    show=main[['cell','status','drought_risk_score','warning','forecast_class']].copy()
    show.columns=['Area / soil cell','Availability','Risk score','Warning','Forecast soil class']
    show['Warning']=show['Warning'].map(lambda v:'Unavailable' if pd.isna(v) else 'Yes' if v else 'No')
    if not valid.any():
        summary='No forecast was issued. '+str(regional.status.iloc[0])+'.'
    else:summary=f'{int(valid.sum())} regional forecasts issued across 7, 15 and 30 days; {int(warning.sum())} warning flags.'
    if (manifest.get('update') or {}).get('status')=='update failed':
        summary+=' The data update failed; availability below reflects the existing cache.'
    n=manifest['point_population'];recent=manifest['points_with_recent_satellite_image']
    charts=''.join(f'<div class="chart">{trend_svg(g.soil_pct,cell)}</div>' for cell,g in groups.items())
    crop='No sampled-point catalogue is available.'
    if len(points):
        q=points[points.horizon==15]
        agg=q.groupby(['mandal','irr','vegetation_context']).size().rename('Sampled points').reset_index()
        agg['irr']=agg.irr.map({0:'Rainfed stratum',1:'Irrigated stratum'});agg.columns=['Mandal','Sampling stratum','Image context','Sampled points']
        crop=table(agg)
    data=readiness.copy()
    for c in ['required_cutoff','soil_available_through','soil_available_by_cutoff','weather_available_through']:
        data[c]=pd.to_datetime(data[c]).dt.strftime('%Y-%m-%d')
    data['weather_required_by_selected_model']=data.weather_required_by_selected_model.map({True:'Yes',False:'No'})
    data.columns=['Area','Required through','Soil cache through','Soil available at cutoff','Weather cache through','Weather required']
    warning_count=str(int(warning.sum())) if valid.any() else 'Not assessed'
    cards=f'<div class="card"><strong>{int(valid.sum())}/15</strong><span>Regional forecasts available</span></div><div class="card"><strong>{warning_count}</strong><span>Regional warning flags</span></div><div class="card"><strong>{recent}/{n}</strong><span>Points with recent imagery</span></div>'
    links=['regional_drought_risk.csv','features_used.csv','source_status.csv','manifest.json']
    if len(points):links+=['sampled_point_context.csv','sampled_points.geojson','inspection_candidates.csv']
    html=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rabi drought risk - {issue:%Y-%m-%d}</title><style>
body{{font:15px/1.55 system-ui,Segoe UI,sans-serif;color:#203144;background:#f3f6f9;margin:0}}main{{max-width:1120px;margin:auto;padding:32px 24px 60px}}
h1{{font-size:32px;line-height:1.2;margin:10px 0}}h2{{font-size:21px;margin:28px 0 12px}}p{{max-width:1000px}}.tag{{font-size:12px;font-weight:700;letter-spacing:1px;color:#277487;text-transform:uppercase}}
.notice{{border-left:4px solid #d38c25;background:#fff7e8;padding:15px 18px;margin:20px 0}}.cards{{display:flex;gap:16px;flex-wrap:wrap}}.card{{background:white;border:1px solid #d9e2e9;border-radius:8px;padding:20px;flex:1;min-width:190px}}.card strong{{display:block;font-size:28px;color:#146d84}}.card span{{font-size:13px}}
.scroll{{overflow:auto;background:white;border:1px solid #dce4eb;border-radius:8px}}table{{border-collapse:collapse;width:100%;font-size:12px}}th,td{{padding:10px 12px;border-bottom:1px solid #e5ebef;text-align:left;vertical-align:top}}th{{background:#eaf0f5;white-space:nowrap}}.charts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:16px}}.chart{{background:white;border:1px solid #dce4eb;border-radius:8px;padding:10px}}svg{{display:block;width:100%;height:auto}}a{{color:#076985}}li{{margin:6px 0}}.muted{{color:#52677c;font-size:13px}}code{{background:#e5ebf1;padding:2px 5px}}@media print{{body{{background:white}}main{{padding:0}}.scroll{{overflow:visible}}table{{font-size:9px}}}}
</style></head><body><main><div class="tag">Rabi research monitoring | {escape(mode)}</div>
<h1>Drought risk, {issue:%d %B %Y}</h1><p>{escape(summary)}</p><div class="cards">{cards}</div>
<div class="notice"><strong>What this means:</strong> regional risk of unusually low root-zone soil water, not a confirmed drought diagnosis for individual fields. Model scores are not calibrated guarantees. Agricultural drought accuracy remains unestablished.</div>
<h2>15-day regional forecast</h2><p>The target is the seven-day mean soil-water condition ending 15 days after issue. All target days are in the future relative to this issue. Classes describe soil-moisture percentiles: moderate 10-20, severe-or-worse at or below 10. Above 20 does not guarantee a healthy crop.</p><div class="scroll">{table(show)}</div>
<h2>Soil water known at issue</h2><p class="muted">Trailing seven-day soil-moisture percentile, fixed 1981-2000 reference. Curves stop at the issue date minus eight days. Lines at 20 and 10 show the deficit thresholds. The spatial support is roughly 11 km.</p><div class="charts">{charts}</div>
<h2>Crop observation coverage</h2><p>Satellite images must be at least two days old and no more than 12 days old. Missing images remain unknown. Green vegetation is not proof of crop health; low greenness is not proof of drought. Irrigation supply is unknown.</p><div class="scroll">{crop}</div>
<h2>Inputs and readiness</h2><div class="scroll">{table(data)}</div><p class="muted">Weather is required only if a selected model uses weather features. All currently selected models use soil history; stale optional weather does not prevent a soil-only forecast. Satellite coverage controls crop context, not the regional soil forecast.</p>
<h2>Evidence and limits</h2><p>The 2023-2025 evaluation contains no drought targets under the frozen ERA5 definition, so drought recall cannot be estimated there. NASA's soil product disagrees on some cases. In the earlier historical check, a simple transition baseline outperformed the selected model on new onsets. This workflow preserves those findings and does not claim a validated best model.</p>
<h2>Download this run</h2><ul>{''.join(f'<li><a href="{name}">{name}</a></li>' for name in links)}</ul>
<p class="muted">Each run has a new directory. Saved feature values and model hashes allow exact prediction replay. Field observations are collected separately and never treated as training labels automatically.</p>
</main></body></html>'''
    (folder/'report.html').write_text(html,encoding='utf-8')
    md=f'# Rabi monitoring - {issue:%Y-%m-%d}\n\n{mode}. {summary}\n\nRecent satellite coverage: {recent}/{n} points.\n\nScope: regional root-zone soil-moisture drought risk. Field agricultural-drought accuracy is not established.\n\nOpen `report.html` for forecasts, soil trends, crop coverage and source dates. `manifest.json` records input/model/output hashes.\n'
    (folder/'RUN_SUMMARY.md').write_text(md,encoding='utf-8')
