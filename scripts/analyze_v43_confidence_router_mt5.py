#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
import pandas as pd

BOOK='usd40_r1p0_cent_continuous'
CONTROL='adaptive_ewma_hl8_thr0'
HISTORICAL=['adaptive_ewma_hl8_thr0p05','adaptive_ewma_hl10_thr0p05','adaptive_ewma_hl12_thr0p05','adaptive_cp_fast5_slow20_thr0p30']
CHALLENGERS=[
    'v43_hl8_thr0p05_conf0p05',
    'v43_hl10_thr0p05_conf0p05',
    'v43_hl8_thr0p05_conf0p10',
    'v43_hl10_thr0p05_conf0p10',
]
PARENT={
    'v43_hl8_thr0p05_conf0p05':'adaptive_ewma_hl8_thr0p05',
    'v43_hl10_thr0p05_conf0p05':'adaptive_ewma_hl10_thr0p05',
    'v43_hl8_thr0p05_conf0p10':'adaptive_ewma_hl8_thr0p05',
    'v43_hl10_thr0p05_conf0p10':'adaptive_ewma_hl10_thr0p05',
}
EXPECTED_CONTROL_FINAL=107.432645
EXPECTED_CONTROL_TRADES=563
EXPECTED_MONTHS=12
EXPECTED_MONTHLY_TRADES=[30,72,76,37,43,65,41,37,20,32,62,48]
EXPECTED_MONTHLY_FINAL=[38.951141,43.518604,46.317250,47.137010,51.403129,63.068101,63.241472,64.790962,64.922339,73.052422,88.574123,107.432645]
TARGET_GEO_MONTH_PCT=15.0
TARGET_END_USD=40.0*(1.15**12)

def parse_time(s): return pd.to_datetime(s,format='%Y.%m.%d %H:%M:%S',errors='raise')

def aggregate(monthly,trades,candidate):
    m=monthly[(monthly.candidate==candidate)&(monthly.book==BOOK)].copy().sort_values('month').reset_index(drop=True)
    t=trades[(trades.candidate==candidate)&(trades.book==BOOK)].copy()
    if len(m)!=EXPECTED_MONTHS: raise RuntimeError(f'{candidate}: expected 12 monthly rows got {len(m)}')
    if len(t):
        t['entry_dt']=parse_time(t.entry_time);t['exit_dt']=parse_time(t.exit_time);t['hold_minutes']=(t.exit_dt-t.entry_dt).dt.total_seconds()/60.0
    end=float(m.final_balance.iloc[-1]);geo=100*((end/40.0)**(1/12)-1) if end>0 else -100.0
    total_return=100*(end/40.0-1);dd=float(m.max_mtm_dd_pct.astype(float).max())
    pnl=t.total_pnl.astype(float) if len(t) else pd.Series(dtype=float);gp=float(pnl[pnl>0].sum()) if len(pnl) else 0;gl=float(-pnl[pnl<0].sum()) if len(pnl) else 0
    pf=gp/gl if gl>0 else (math.inf if gp>0 else 0)
    return {'candidate':candidate,'ending_usd':end,'total_return_pct':total_return,'geo_month_pct':geo,'max_mtm_dd_pct':dd,'return_to_dd':total_return/dd if dd>0 else None,'trades':int(len(t)),'positive_months':int((m.return_pct.astype(float)>0).sum()),'months_ge_15pct':int((m.return_pct.astype(float)>=15).sum()),'worst_month_pct':float(m.return_pct.astype(float).min()),'best_month_pct':float(m.return_pct.astype(float).max()),'avg_r':float(t.r_multiple.astype(float).mean()) if len(t) else None,'sum_r':float(t.r_multiple.astype(float).sum()) if len(t) else 0,'profit_factor':pf,'turnover_x_start40':float(m.gross_notional_turnover.astype(float).sum()/40.0),'median_hold_minutes':float(t.hold_minutes.median()) if len(t) else None,'monthly_return_pct':[float(x) for x in m.return_pct.astype(float)],'monthly_final_balance':[float(x) for x in m.final_balance.astype(float)]}

def verify_control(monthly,trades):
    m=monthly[(monthly.candidate==CONTROL)&(monthly.book==BOOK)].copy().sort_values('month').reset_index(drop=True);t=trades[(trades.candidate==CONTROL)&(trades.book==BOOK)];errors=[]
    if len(m)!=EXPECTED_MONTHS: errors.append(f'months={len(m)} expected={EXPECTED_MONTHS}')
    if len(t)!=EXPECTED_CONTROL_TRADES: errors.append(f'trades={len(t)} expected={EXPECTED_CONTROL_TRADES}')
    if len(m)==EXPECTED_MONTHS:
        if list(m.trades.astype(int))!=EXPECTED_MONTHLY_TRADES: errors.append('monthly trade counts differ from accepted V38 control')
        diff=float(np.max(np.abs(m.final_balance.astype(float).to_numpy()-np.asarray(EXPECTED_MONTHLY_FINAL))))
        if diff>1e-5: errors.append(f'monthly final balance max diff={diff:.9g}')
        if abs(float(m.final_balance.iloc[-1])-EXPECTED_CONTROL_FINAL)>1e-5: errors.append('final control balance mismatch')
    return {'pass':not errors,'errors':errors}

def attach_vs(row,ref,key):
    deltas=[a-b for a,b in zip(row['monthly_return_pct'],ref['monthly_return_pct'])]
    row[key]={'ending_usd_delta':row['ending_usd']-ref['ending_usd'],'ending_usd_ratio':row['ending_usd']/ref['ending_usd'],'geo_month_pp':row['geo_month_pct']-ref['geo_month_pct'],'dd_delta_pp':row['max_mtm_dd_pct']-ref['max_mtm_dd_pct'],'trade_change_pct':100*(row['trades']-ref['trades'])/ref['trades'],'turnover_change_pct':100*(row['turnover_x_start40']-ref['turnover_x_start40'])/ref['turnover_x_start40'],'months_beat_ref':int(sum(x>0 for x in deltas)),'mean_monthly_return_uplift_pp':float(np.mean(deltas)),'monthly_return_delta_pp':deltas}

def control_gate(row,control):
    v=row['vs_control'];checks={
        'ending_usd_at_least_5pct_above_control':row['ending_usd']>=1.05*control['ending_usd'],
        'geo_uplift_at_least_0p50pp':v['geo_month_pp']>=0.50,
        'max_dd_no_more_than_control_plus_1pp':row['max_mtm_dd_pct']<=control['max_mtm_dd_pct']+1.0,
        'return_to_dd_improved':(row['return_to_dd'] or -1e99)>(control['return_to_dd'] or -1e99),
        'positive_months_at_least_10':row['positive_months']>=10,
        'beats_control_in_at_least_7_months':v['months_beat_ref']>=7,
        'worst_month_not_below_minus5pct':row['worst_month_pct']>=-5.0,
        'turnover_not_more_than_10pct_above_control':row['turnover_x_start40']<=1.10*control['turnover_x_start40'],
        'trade_breadth_at_least_75pct_control':row['trades']>=math.ceil(0.75*control['trades']),
    }
    return {'pass':all(checks.values()),'checks':checks}

def parent_gate(row,parent):
    v=row['vs_parent'];checks={
        'ending_usd_above_frozen_parent':row['ending_usd']>parent['ending_usd'],
        'geo_month_above_frozen_parent':row['geo_month_pct']>parent['geo_month_pct'],
        'return_to_dd_not_worse_than_parent':(row['return_to_dd'] or -1e99)>=(parent['return_to_dd'] or -1e99),
        'dd_no_more_than_parent_plus_0p50pp':row['max_mtm_dd_pct']<=parent['max_mtm_dd_pct']+0.50,
        'beats_parent_in_at_least_7_months':v['months_beat_ref']>=7,
        'turnover_not_more_than_5pct_above_parent':row['turnover_x_start40']<=1.05*parent['turnover_x_start40'],
        'trade_breadth_at_least_90pct_parent':row['trades']>=math.ceil(0.90*parent['trades']),
    }
    return {'pass':all(checks.values()),'checks':checks}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('--run-folder',required=True);ap.add_argument('--output',required=True);ap.add_argument('--csv',required=True);a=ap.parse_args()
    run=Path(a.run_folder);monthly=pd.read_csv(run/'monthly_summary.csv');trades=pd.read_csv(run/'trades.csv');manifest=(run/'manifest.txt').read_text(encoding='utf-8-sig',errors='replace')
    for tok in ('v43_confidence_aware_router=1','tester_only=1','native_broker_orders=0','external_broker_orders=0','v43_risk_changed=0','v43_entry_exit_geometry_changed=0','v43_global_time_hysteresis=0'):
        if tok not in manifest: raise RuntimeError('manifest contract missing '+tok)
    cc=verify_control(monthly,trades)
    if not cc['pass']: raise RuntimeError('V43 control reproduction failed: '+'; '.join(cc['errors']))
    rows=[aggregate(monthly,trades,n) for n in [CONTROL]+HISTORICAL+CHALLENGERS]
    by={r['candidate']:r for r in rows};control=by[CONTROL]
    for r in rows[1:]: attach_vs(r,control,'vs_control')
    gates={}
    for name in CHALLENGERS:
        r=by[name];parent=by[PARENT[name]]
        attach_vs(r,parent,'vs_parent')
        cg=control_gate(r,control);pg=parent_gate(r,parent)
        gates[name]={'pass':cg['pass'] and pg['pass'],'control_gate':cg,'parent_gate':pg,'parent':PARENT[name]}
    eligible=[by[n] for n in CHALLENGERS if gates[n]['pass']]
    winner=max([by[n] for n in CHALLENGERS],key=lambda x:x['ending_usd'])
    oldwinner=max([by[n] for n in HISTORICAL],key=lambda x:x['ending_usd'])
    flat=[]
    for r in rows:
        q={k:v for k,v in r.items() if k not in ('monthly_return_pct','monthly_final_balance','vs_control','vs_parent')}
        if r['candidate'] in CHALLENGERS:
            q['parent']=PARENT[r['candidate']]
            q['eligible_to_freeze']=gates[r['candidate']]['pass']
        flat.append(q)
    pd.DataFrame(flat).to_csv(a.csv,index=False,lineterminator='\n')
    out={'schema':'v43_confidence_aware_router_exact_mt5_v1','period':'2025-08-01_to_2026-08-01','book':BOOK,'control_reproducibility':cc,'exact_control':control,'historical_router_variants':[by[n] for n in HISTORICAL],'v43_challengers':[by[n] for n in CHALLENGERS],'v43_gates':gates,'development_v43_return_winner':winner['candidate'],'historical_router_return_winner':oldwinner['candidate'],'eligible_to_freeze_for_fresh_holdout':[r['candidate'] for r in eligible],'aspirational_target':{'geo_month_pct':TARGET_GEO_MONTH_PCT,'end_usd_12m_from_40':TARGET_END_USD,'control_gap_pp':TARGET_GEO_MONTH_PCT-control['geo_month_pct']},'decision_rule':'Exact-MT5 development adjudication only. V43 must beat both accepted control and its frozen HL8/HL10 threshold parent under preregistered gates. No same-window margin retuning. PASS only permits freezing one candidate for genuinely fresh chronological confirmation; never live authorization.'}
    Path(a.output).write_text(json.dumps(out,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'control':{k:control[k] for k in ('ending_usd','geo_month_pct','max_mtm_dd_pct','trades')},'historical_winner':oldwinner['candidate'],'v43_winner':winner['candidate'],'v43_winner_geo':winner['geo_month_pct'],'eligible':out['eligible_to_freeze_for_fresh_holdout'],'target_geo':15.0},indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
