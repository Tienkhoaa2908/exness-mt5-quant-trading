#!/usr/bin/env python3
from __future__ import annotations
import argparse, pathlib
import numpy as np
import pandas as pd

BOOK="usd40_r1p0_cent"
MODES=("baseline","catboost","extratrees","mlp_32_16","linear_svm")
PRIMARY="adaptive_ewma_hl8_thr0"

def geom_mean_pct(r: pd.Series) -> float:
    x=1.0+r.astype(float).to_numpy()/100.0
    if len(x)==0 or np.any(x<=0): return float("nan")
    return float((np.prod(x)**(1.0/len(x))-1.0)*100.0)

def analyze(root:pathlib.Path,out:pathlib.Path):
    rows=[]
    monthly=[]
    for mode in MODES:
        d=root/mode
        sp=d/"monthly_summary.csv"; tp=d/"trades.csv"
        if not sp.is_file() or not tp.is_file(): raise RuntimeError(f"missing MT5 evidence for {mode}: {d}")
        s=pd.read_csv(sp); t=pd.read_csv(tp)
        s=s[s.book==BOOK].copy(); t=t[t.book==BOOK].copy()
        if s.empty: raise RuntimeError(f"no {BOOK} summary rows for {mode}")
        for cand,g in s.groupby("candidate",sort=True):
            g=g.sort_values("month")
            tr=t[t.candidate==cand].copy()
            pos=tr.loc[tr.net_pnl>0,"net_pnl"].sum() if "net_pnl" in tr else np.nan
            neg=-tr.loc[tr.net_pnl<0,"net_pnl"].sum() if "net_pnl" in tr else np.nan
            pf=float(pos/neg) if np.isfinite(neg) and neg>0 else (float("inf") if np.isfinite(pos) and pos>0 else np.nan)
            rr=g.return_pct.astype(float)
            rows.append({
                "mode":mode,"candidate":cand,"months":len(g),
                "arith_mean_monthly_return_pct":float(rr.mean()),
                "geometric_mean_monthly_return_pct":geom_mean_pct(rr),
                "months_ge_15pct":int((rr>=15).sum()),
                "positive_months":int((rr>0).sum()),
                "worst_month_return_pct":float(rr.min()),
                "best_month_return_pct":float(rr.max()),
                "max_mtm_dd_pct":float(g.max_mtm_dd_pct.max()),
                "trades":int(g.trades.sum()),
                "trade_ledger_rows":int(len(tr)),
                "avg_r_trade_weighted":float(np.average(g.avg_r.astype(float),weights=np.maximum(g.trades.astype(float),1e-12))) if g.trades.sum()>0 else np.nan,
                "trade_ledger_mean_r":float(tr.r_multiple.mean()) if len(tr) else np.nan,
                "profit_factor_from_trade_ledger":pf,
                "net_pnl_usd":float(g.net_pnl.sum()),
                "volume_rejects":int(g.volume_reject.sum()),
                "margin_rejects":int(g.margin_reject_1_200.sum()),
                "turnover_x_initial_sum":float(g.turnover_x_initial.sum()),
                "monthly_target_gap_vs_15pct_geo_pp":float(15.0-geom_mean_pct(rr)),
            })
            z=g[["month","return_pct","max_mtm_dd_pct","trades","volume_reject","turnover_x_initial"]].copy()
            z.insert(0,"candidate",cand); z.insert(0,"mode",mode); monthly.append(z)
    comp=pd.DataFrame(rows).sort_values(["geometric_mean_monthly_return_pct","arith_mean_monthly_return_pct"],ascending=False).reset_index(drop=True)
    out.mkdir(parents=True,exist_ok=True)
    comp.to_csv(out/"v31_usd40_exact_mt5_comparison.csv",index=False)
    pd.concat(monthly,ignore_index=True).to_csv(out/"v31_usd40_exact_mt5_monthly.csv",index=False)
    primary=comp[comp.candidate==PRIMARY].copy().sort_values("geometric_mean_monthly_return_pct",ascending=False)
    primary.to_csv(out/"v31_usd40_primary_candidate_comparison.csv",index=False)
    best=comp.groupby("mode",as_index=False).first().sort_values("geometric_mean_monthly_return_pct",ascending=False)
    best.to_csv(out/"v31_usd40_best_candidate_per_mode.csv",index=False)
    with (out/"V31_EXACT_MT5_REPORT.txt").open("w",encoding="utf-8") as f:
        f.write("V31 USD40 exact MT5 Strategy Tester report\n")
        f.write("Decision book: usd40_r1p0_cent; research risk ceiling: 1.00% per trade\n")
        f.write("Aspirational target: 15% monthly; not a guarantee. Risk is not increased to force target.\n\n")
        f.write("PRIMARY SAME-CANDIDATE COMPARISON: adaptive_ewma_hl8_thr0\n")
        f.write(primary[["mode","arith_mean_monthly_return_pct","geometric_mean_monthly_return_pct","months_ge_15pct","positive_months","worst_month_return_pct","max_mtm_dd_pct","trades","profit_factor_from_trade_ledger","volume_rejects","turnover_x_initial_sum"]].to_string(index=False))
        f.write("\n\nBEST CANDIDATE PER MODE (exploratory; do not use alone for promotion)\n")
        f.write(best[["mode","candidate","arith_mean_monthly_return_pct","geometric_mean_monthly_return_pct","months_ge_15pct","worst_month_return_pct","max_mtm_dd_pct","trades"]].to_string(index=False))
        f.write("\n")
    print(primary[["mode","arith_mean_monthly_return_pct","geometric_mean_monthly_return_pct","months_ge_15pct","worst_month_return_pct","max_mtm_dd_pct","trades"]].to_string(index=False))
    print(f"Exact MT5 analysis PASS -> {out}")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--package-root",required=True); ap.add_argument("--output",required=True)
    a=ap.parse_args(); analyze(pathlib.Path(a.package_root),pathlib.Path(a.output))
if __name__=="__main__": main()
