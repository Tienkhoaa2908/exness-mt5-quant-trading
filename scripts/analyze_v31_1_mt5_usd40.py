#!/usr/bin/env python3
from __future__ import annotations
import argparse, pathlib
import numpy as np
import pandas as pd

BOOK='usd40_r1p0_cent_continuous'
MODES=('baseline','catboost','extratrees','deep_mlp','linear_svm','catboost_and_extratrees','majority_2of4')
PRIMARY='adaptive_ewma_hl8_thr0'
START_CAPITAL=40.0
TARGET_MONTHLY=15.0

def geom_from_end(start,end,months):
    if months<=0 or start<=0 or end<=0: return float('nan')
    return float(((end/start)**(1/months)-1)*100)

def analyze(root:pathlib.Path,out:pathlib.Path):
    rows=[]; monthly=[]
    for mode in MODES:
        d=root/mode; sp=d/'monthly_summary.csv'; tp=d/'trades.csv'
        if not sp.is_file() or not tp.is_file(): raise RuntimeError(f'missing exact MT5 evidence for {mode}: {d}')
        s=pd.read_csv(sp); t=pd.read_csv(tp)
        s=s[s.book==BOOK].copy(); t=t[t.book==BOOK].copy()
        if s.empty: raise RuntimeError(f'no {BOOK} summary rows for {mode}')
        for cand,g in s.groupby('candidate',sort=True):
            g=g.sort_values('month').reset_index(drop=True); tr=t[t.candidate==cand].copy()
            if abs(float(g.iloc[0].initial_balance)-START_CAPITAL)>0.01: raise RuntimeError(f'{mode}/{cand}: starting balance != $40')
            if len(g)>1:
                gaps=(g.initial_balance.iloc[1:].to_numpy(float)-g.final_balance.iloc[:-1].to_numpy(float))
                if np.max(np.abs(gaps))>0.02: raise RuntimeError(f'{mode}/{cand}: capital continuity mismatch max={np.max(np.abs(gaps))}')
            start=float(g.iloc[0].initial_balance); end=float(g.iloc[-1].final_balance); months=len(g)
            rr=g.return_pct.astype(float)
            pos=tr.loc[tr.net_pnl>0,'net_pnl'].sum() if 'net_pnl' in tr else np.nan
            neg=-tr.loc[tr.net_pnl<0,'net_pnl'].sum() if 'net_pnl' in tr else np.nan
            pf=float(pos/neg) if np.isfinite(neg) and neg>0 else (float('inf') if np.isfinite(pos) and pos>0 else np.nan)
            geo=geom_from_end(start,end,months)
            rows.append({'mode':mode,'candidate':cand,'months':months,'starting_capital_usd':start,'ending_capital_usd':end,'total_return_pct':(end/start-1)*100.0,'arith_mean_monthly_return_pct':float(rr.mean()),'geometric_mean_monthly_return_pct':geo,'target_15pct_geo_met':bool(geo>=TARGET_MONTHLY),'months_ge_15pct':int((rr>=TARGET_MONTHLY).sum()),'positive_months':int((rr>0).sum()),'worst_month_return_pct':float(rr.min()),'best_month_return_pct':float(rr.max()),'full_period_max_mtm_dd_pct':float(g.max_mtm_dd_pct.max()),'trades':int(g.trades.sum()),'trade_ledger_rows':int(len(tr)),'avg_r':float(tr.r_multiple.mean()) if len(tr) else np.nan,'profit_factor':pf,'net_pnl_usd':float(end-start),'volume_rejects':int(g.volume_reject.sum()),'margin_rejects':int(g.margin_reject_1_200.sum()),'gross_turnover_usd':float(g.gross_notional_turnover.sum()),'turnover_x_start_capital_sum':float(g.gross_notional_turnover.sum()/start),'target_gap_geo_pp':float(TARGET_MONTHLY-geo)})
            z=g[['month','initial_balance','final_balance','return_pct','max_mtm_dd_pct','trades','volume_reject','margin_reject_1_200','gross_notional_turnover','turnover_x_initial']].copy(); z.insert(0,'candidate',cand); z.insert(0,'mode',mode); monthly.append(z)
    comp=pd.DataFrame(rows).sort_values(['geometric_mean_monthly_return_pct','full_period_max_mtm_dd_pct'],ascending=[False,True]).reset_index(drop=True)
    out.mkdir(parents=True,exist_ok=True); comp.to_csv(out/'v31_1_usd40_exact_mt5_comparison.csv',index=False); pd.concat(monthly,ignore_index=True).to_csv(out/'v31_1_usd40_exact_mt5_monthly.csv',index=False)
    primary=comp[comp.candidate==PRIMARY].copy().sort_values('geometric_mean_monthly_return_pct',ascending=False); primary.to_csv(out/'v31_1_usd40_primary_same_candidate.csv',index=False)
    best=comp.groupby('mode',as_index=False).first().sort_values('geometric_mean_monthly_return_pct',ascending=False); best.to_csv(out/'v31_1_usd40_best_candidate_exploratory.csv',index=False)
    with (out/'V31_1_EXACT_MT5_REPORT.txt').open('w',encoding='utf-8') as f:
        f.write('V31.1 exact MT5 Strategy Tester — continuous USD40 research account\n')
        f.write('Tester Deposit=40 USD; target book=usd40_r1p0_cent_continuous; risk=1.00%/trade; leverage assumption=1:200.\n')
        f.write('Capital carries month-to-month. Positions are liquidated at month-end to preserve the existing monthly measurement contract.\n')
        f.write('15%/month is an aspirational research target, not a guarantee; risk is not increased to force it.\n\n')
        cols=['mode','starting_capital_usd','ending_capital_usd','total_return_pct','geometric_mean_monthly_return_pct','months_ge_15pct','positive_months','worst_month_return_pct','full_period_max_mtm_dd_pct','trades','profit_factor','volume_rejects','turnover_x_start_capital_sum','target_15pct_geo_met']
        f.write('PRIMARY SAME-CANDIDATE: adaptive_ewma_hl8_thr0\n'); f.write(primary[cols].to_string(index=False)); f.write('\n\n')
        f.write('BEST CANDIDATE PER MODE — exploratory only, not promotion evidence\n'); f.write(best[['mode','candidate']+cols[1:]].to_string(index=False)); f.write('\n')
    print(primary[['mode','ending_capital_usd','geometric_mean_monthly_return_pct','months_ge_15pct','worst_month_return_pct','full_period_max_mtm_dd_pct','trades','target_15pct_geo_met']].to_string(index=False))
    print(f'Exact continuous USD40 MT5 analysis PASS -> {out}')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--package-root',required=True); ap.add_argument('--output',required=True); a=ap.parse_args(); analyze(pathlib.Path(a.package_root),pathlib.Path(a.output))
if __name__=='__main__': main()
