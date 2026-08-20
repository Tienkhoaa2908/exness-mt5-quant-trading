#!/usr/bin/env python3
from __future__ import annotations
import argparse, pathlib
import numpy as np
import pandas as pd

BOOK='usd40_r1p0_cent_continuous'
MODES=('baseline','mlp_keep50','mlp_keep60','mlp_keep70','mlp_keep80','mlp_keep90')
PRIMARY='adaptive_ewma_hl8_thr0'
START_CAPITAL=40.0
TARGET_MONTHLY=15.0

def geom(start,end,months):
    if months<=0 or start<=0 or end<=0: return float('nan')
    return float(((end/start)**(1.0/months)-1.0)*100.0)

def pf(tr):
    col='total_pnl' if 'total_pnl' in tr.columns else ('net_pnl' if 'net_pnl' in tr.columns else None)
    if col is None: raise RuntimeError('trade ledger lacks realized PnL column')
    p=pd.to_numeric(tr[col],errors='coerce').dropna(); pos=float(p[p>0].sum()); neg=float(-p[p<0].sum())
    if neg>0: return pos/neg
    if pos>0: return float('inf')
    return float('nan')

def analyze(root:pathlib.Path,out:pathlib.Path):
    rows=[]; monthly=[]
    for mode in MODES:
        d=root/mode; s=pd.read_csv(d/'monthly_summary.csv'); t=pd.read_csv(d/'trades.csv')
        s=s[s.book==BOOK].copy(); t=t[t.book==BOOK].copy()
        if s.empty: raise RuntimeError(f'no {BOOK} rows for {mode}')
        for cand,g in s.groupby('candidate',sort=True):
            g=g.sort_values('month').reset_index(drop=True); tr=t[t.candidate==cand].copy()
            if abs(float(g.iloc[0].initial_balance)-START_CAPITAL)>0.01: raise RuntimeError(f'{mode}/{cand}: start != 40')
            if len(g)>1:
                gaps=g.initial_balance.iloc[1:].to_numpy(float)-g.final_balance.iloc[:-1].to_numpy(float)
                if np.max(np.abs(gaps))>0.02: raise RuntimeError(f'{mode}/{cand}: continuity mismatch')
            start=float(g.iloc[0].initial_balance); end=float(g.iloc[-1].final_balance); months=len(g)
            rr=g.return_pct.astype(float); dd=float(g.max_mtm_dd_pct.max()); total=(end/start-1)*100; turn=float(g.gross_notional_turnover.sum()); ge=geom(start,end,months)
            rows.append({'mode':mode,'candidate':cand,'months':months,'starting_capital_usd':start,'ending_capital_usd':end,'total_return_pct':total,'arith_mean_monthly_return_pct':float(rr.mean()),'geometric_mean_monthly_return_pct':ge,'months_ge_15pct':int((rr>=TARGET_MONTHLY).sum()),'positive_months':int((rr>0).sum()),'worst_month_return_pct':float(rr.min()),'best_month_return_pct':float(rr.max()),'full_period_max_mtm_dd_pct':dd,'return_to_max_dd':float(total/dd) if dd>0 else np.nan,'trades':int(g.trades.sum()),'avg_r':float(tr.r_multiple.mean()) if len(tr) else np.nan,'profit_factor':pf(tr),'volume_rejects':int(g.volume_reject.sum()),'margin_rejects':int(g.margin_reject_1_200.sum()),'gross_turnover_usd':turn,'turnover_x_start_capital_sum':turn/start,'net_pnl_bps_of_turnover':float((end-start)/turn*10000) if turn>0 else np.nan,'target_15pct_geo_met':bool(ge>=TARGET_MONTHLY),'target_gap_geo_pp':TARGET_MONTHLY-ge})
            q=g[['month','initial_balance','final_balance','return_pct','max_mtm_dd_pct','trades','volume_reject','gross_notional_turnover']].copy(); q.insert(0,'candidate',cand); q.insert(0,'mode',mode); monthly.append(q)
    comp=pd.DataFrame(rows).sort_values(['geometric_mean_monthly_return_pct','full_period_max_mtm_dd_pct'],ascending=[False,True]).reset_index(drop=True)
    out.mkdir(parents=True,exist_ok=True); comp.to_csv(out/'v32_exact_mt5_comparison.csv',index=False); pd.concat(monthly,ignore_index=True).to_csv(out/'v32_exact_mt5_monthly.csv',index=False)
    primary=comp[comp.candidate==PRIMARY].sort_values('geometric_mean_monthly_return_pct',ascending=False); primary.to_csv(out/'v32_primary_same_candidate.csv',index=False)
    with (out/'V32_EXACT_MT5_REPORT.txt').open('w',encoding='utf-8') as f:
        f.write('V32 DeepMLP keep-rate sweep — exact MT5 continuous USD40 research account\n')
        f.write('Deposit=40 USD; risk ceiling=1.00%/trade; 2026-02-01 -> 2026-08-01; monthly liquidation retained.\n')
        f.write('Development sweep on already-inspected months; NOT fresh confirmation. 15%/month remains an aspirational target.\n\n')
        cols=['mode','ending_capital_usd','total_return_pct','geometric_mean_monthly_return_pct','months_ge_15pct','positive_months','worst_month_return_pct','full_period_max_mtm_dd_pct','return_to_max_dd','trades','avg_r','profit_factor','volume_rejects','turnover_x_start_capital_sum','target_15pct_geo_met']
        f.write('PRIMARY SAME-CANDIDATE: adaptive_ewma_hl8_thr0\n'); f.write(primary[cols].to_string(index=False)); f.write('\n')
    print(primary[['mode','ending_capital_usd','geometric_mean_monthly_return_pct','full_period_max_mtm_dd_pct','trades','avg_r','profit_factor']].to_string(index=False))
    print(f'V32 exact MT5 analysis PASS -> {out}')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--package-root',required=True); ap.add_argument('--output',required=True); a=ap.parse_args(); analyze(pathlib.Path(a.package_root),pathlib.Path(a.output))
if __name__=='__main__': main()
