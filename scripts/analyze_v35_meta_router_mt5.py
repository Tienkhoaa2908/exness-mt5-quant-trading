#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
BOOK='usd40_r1p0_cent_continuous';PRIMARY='adaptive_ewma_hl8_thr0';ROUTER='v35_ai_all_expert_meta_router'
def calc(ms,tr,c):
 m=ms[(ms.candidate==c)&(ms.book==BOOK)].copy();g=tr[(tr.candidate==c)&(tr.book==BOOK)].copy()
 if m.empty:return None
 rr=m.return_pct.astype(float).to_numpy()/100;geo=(np.prod(1+rr)**(1/len(rr))-1)*100 if np.all(1+rr>0) else -100
 gp=g.loc[g.total_pnl>0,'total_pnl'].sum();gl=-g.loc[g.total_pnl<0,'total_pnl'].sum();pf=gp/gl if gl>0 else (999 if gp>0 else 0)
 return {'candidate':c,'ending_usd':float(m.final_balance.iloc[-1]),'geo_monthly_pct':float(geo),'positive_months':int((m.return_pct>0).sum()),'months_ge15':int((m.return_pct>=15).sum()),'worst_month_pct':float(m.return_pct.min()),'max_mtm_dd_pct':float(m.max_mtm_dd_pct.max()),'trades':len(g),'avg_r':float(g.r_multiple.mean()) if len(g) else 0,'profit_factor':float(pf),'turnover_x40':float(m.gross_notional_turnover.sum()/40),'volume_rejects':int(m.volume_reject.sum())}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-folder',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();rd=Path(a.run_folder)
 ms=pd.read_csv(rd/'monthly_summary.csv');tr=pd.read_csv(rd/'trades.csv')
 for c in ['return_pct','final_balance','max_mtm_dd_pct','gross_notional_turnover','volume_reject']:ms[c]=pd.to_numeric(ms[c],errors='coerce').fillna(0)
 for c in ['total_pnl','r_multiple']:tr[c]=pd.to_numeric(tr[c],errors='coerce').fillna(0)
 rows=[]
 for c in [PRIMARY,ROUTER,'v34_smc_ict_causal','v34_price_action_causal','v34_wyckoff_proxy_causal','v34_tick_microstructure_proxy','v34_specialist_confluence']:
  x=calc(ms,tr,c)
  if x:rows.append(x)
 b=next((x for x in rows if x['candidate']==PRIMARY),None);r=next((x for x in rows if x['candidate']==ROUTER),None)
 decision='NO_ROUTER_RESULT'
 if b and r:
  if r['geo_monthly_pct']>b['geo_monthly_pct'] and r['max_mtm_dd_pct']<=b['max_mtm_dd_pct']*1.10:decision='ROUTER_RETURN_WINNER_DEVELOPMENT'
  elif r['geo_monthly_pct']>=b['geo_monthly_pct']*0.95 and r['max_mtm_dd_pct']<b['max_mtm_dd_pct'] and r['profit_factor']>b['profit_factor']:decision='ROUTER_RISK_EFFICIENCY_LEAD'
  else:decision='ROUTER_REJECT_OR_RESEARCH_ONLY'
 out={'schema':'v35_meta_router_exact_mt5_analysis_v1','book':BOOK,'comparison':rows,'decision':decision,'warning':'development evidence only; frozen rule requires fresh chronological holdout'}
 Path(a.output).write_text(json.dumps(out,indent=2),encoding='utf-8');print('V35 ANALYSIS PASS',decision)
 for x in rows: print(f"{x['candidate']:32s} end=${x['ending_usd']:.2f} geo={x['geo_monthly_pct']:+.2f}% DD={x['max_mtm_dd_pct']:.2f}% PF={x['profit_factor']:.2f} AvgR={x['avg_r']:+.3f}")
if __name__=='__main__':main()
