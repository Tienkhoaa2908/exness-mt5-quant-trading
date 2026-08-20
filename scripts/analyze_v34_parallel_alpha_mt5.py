#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
import pandas as pd
SPECIALISTS=['v34_smc_ict_causal','v34_price_action_causal','v34_wyckoff_proxy_causal','v34_tick_microstructure_proxy','v34_specialist_confluence']
BASELINES=['ema_h1_skip20','macd_h1_gap10','bos_fvg_h1_gap8','trend20_h1_gap5','router_ema_bos8','slow_mom_16h24h_timebox8h','adaptive_ewma_hl8_thr0','adaptive_ewma_hl10_thr0p05','adaptive_ewma_hl12_thr0p05']
BOOK='usd40_r1p0_cent_continuous'

def pf(g):
 p=g.loc[g.total_pnl>0,'total_pnl'].sum();l=-g.loc[g.total_pnl<0,'total_pnl'].sum();return float(p/l) if l>0 else (999. if p>0 else 0.)
def metrics(ms,tr,c):
 m=ms[(ms.candidate==c)&(ms.book==BOOK)].copy();g=tr[(tr.candidate==c)&(tr.book==BOOK)].copy()
 if m.empty:return None
 r=m.return_pct.astype(float).to_numpy()/100
 geo=float(np.prod(1+r)**(1/len(r))-1) if np.all(1+r>0) else -1.0
 return {'candidate':c,'months':len(m),'ending_usd':float(m.final_balance.iloc[-1]),'total_return_pct':float((m.final_balance.iloc[-1]/40-1)*100),'geo_monthly_pct':geo*100,'positive_months':int((m.return_pct>0).sum()),'months_ge15':int((m.return_pct>=15).sum()),'worst_month_pct':float(m.return_pct.min()),'best_month_pct':float(m.return_pct.max()),'max_mtm_dd_pct':float(m.max_mtm_dd_pct.max()),'trades':int(len(g)),'avg_r':float(g.r_multiple.mean()) if len(g) else 0.,'profit_factor':pf(g) if len(g) else 0.,'turnover_x40':float(m.gross_notional_turnover.sum()/40) if 'gross_notional_turnover' in m else float(m.turnover_x_initial.sum()),'volume_rejects':int(m.volume_reject.sum()),'margin_rejects':int(m.margin_reject_1_200.sum())}
def overlap(tr,a,b):
 x=tr[(tr.book=='norm10k_r0p5_continuous')&(tr.candidate==a)][['entry_time','direction']].drop_duplicates();y=tr[(tr.book=='norm10k_r0p5_continuous')&(tr.candidate==b)][['entry_time','direction']].drop_duplicates();
 if len(x)==0 or len(y)==0:return None
 inter=len(x.merge(y,on=['entry_time','direction']));return {'a':a,'b':b,'n_a':len(x),'n_b':len(y),'intersection':inter,'jaccard':inter/(len(x)+len(y)-inter) if len(x)+len(y)>inter else 1.0}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-folder',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();rd=Path(a.run_folder)
 ms=pd.read_csv(rd/'monthly_summary.csv');tr=pd.read_csv(rd/'trades.csv')
 for c in ['return_pct','max_mtm_dd_pct','final_balance','gross_notional_turnover','volume_reject','margin_reject_1_200']: ms[c]=pd.to_numeric(ms[c],errors='coerce').fillna(0)
 for c in ['total_pnl','r_multiple']:tr[c]=pd.to_numeric(tr[c],errors='coerce').fillna(0)
 rows=[metrics(ms,tr,c) for c in sorted(ms.candidate.unique())];rows=[r for r in rows if r]
 base='adaptive_ewma_hl8_thr0';ovs=[]
 for s in SPECIALISTS:
  ovs.append(overlap(tr,s,base))
  for s2 in SPECIALISTS:
   if s<s2: ovs.append(overlap(tr,s,s2))
 ovs=[x for x in ovs if x]
 spec=[r for r in rows if r['candidate'] in SPECIALISTS]
 ranked=sorted(spec,key=lambda x:(x['geo_monthly_pct'], -x['max_mtm_dd_pct']),reverse=True)
 verdict=[]
 for r in ranked:
  verdict.append({'candidate':r['candidate'],'promising':bool(r['profit_factor']>1.15 and r['avg_r']>0.08 and r['positive_months']>=7 and r['max_mtm_dd_pct']<=20),'reason':'development screen only; exact MT5 economics, not promotion evidence'})
 out={'schema':'v34_parallel_alpha_analysis_v1','book':BOOK,'rows':rows,'specialist_ranked':ranked,'overlap':ovs,'verdict':verdict,'notes':['specialist independence judged from norm-book exact entry_time+direction overlap','microstructure candidate is L1/tick-path proxy, not true L2/L3 order flow','V34 is development evidence and is used to create labels for V35 meta-router']}
 Path(a.output).write_text(json.dumps(out,indent=2),encoding='utf-8')
 print('V34 ANALYSIS PASS')
 for r in ranked:print(f"{r['candidate']:32s} end=${r['ending_usd']:.2f} geo={r['geo_monthly_pct']:+.2f}% DD={r['max_mtm_dd_pct']:.2f}% PF={r['profit_factor']:.2f} AvgR={r['avg_r']:+.3f} trades={r['trades']}")
if __name__=='__main__':main()
