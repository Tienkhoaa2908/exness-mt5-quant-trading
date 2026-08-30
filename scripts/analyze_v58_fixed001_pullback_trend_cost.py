#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import pandas as pd

CANDIDATE="v52_b4_or_b3_trend_bos"
BOOK="usd40_r1p0_cent_continuous"
FIXED_LOT=0.01
INITIAL_BALANCE=40.0
WEEK_START=pd.Timestamp("2026-08-24 00:00:00")
WEEK_END=pd.Timestamp("2026-08-29 00:00:00")
GATES={
    "baseline_fixed001":"gate_baseline",
    "pullback80":"gate_pullback80",
    "pullback70":"gate_pullback70",
    "pullback80_no_opposite":"gate_pullback80_no_opposite",
    "fast_h1_pullback80":"gate_fast_h1_pullback80",
    "fast_both_pullback80":"gate_fast_both_pullback80",
    "fast_both_pullback80_no_opposite":"gate_fast_both_pullback80_no_opposite",
}

def read_csv(path:Path)->pd.DataFrame:
    if not path.is_file() or path.stat().st_size<=0: return pd.DataFrame()
    return pd.read_csv(path)

def to_dt(s:pd.Series)->pd.Series:
    return pd.to_datetime(s.astype(str).str.replace(".","-",regex=False),errors="coerce")

def max_drawdown(path:list[float])->float:
    peak=-math.inf; dd=0.0
    for x in path:
        peak=max(peak,x)
        if peak>0: dd=max(dd,100.0*(peak-x)/peak)
    return dd

def summarize_gate(trades:pd.DataFrame, evals:pd.DataFrame, gate_col:str)->dict:
    merged=trades.merge(evals[["time",gate_col]],left_on="entry_time_dt",right_on="time",how="left")
    sel=merged[pd.to_numeric(merged[gate_col],errors="coerce").fillna(0).astype(int)==1].copy()
    if sel.empty:
        return {"trades":0,"wins":0,"losses":0,"net_pnl_usd_fixed001":0.0,
                "ending_balance_proxy":INITIAL_BALANCE,"return_pct_proxy":0.0,
                "profit_factor":None,"max_balance_dd_pct_proxy":0.0,
                "balance_breach_proxy":False,"sum_r_original":0.0,"entry_times":[]}
    vol=pd.to_numeric(sel["initial_volume_std_equiv"],errors="coerce")
    pnl=pd.to_numeric(sel["total_pnl"],errors="coerce")
    r=pd.to_numeric(sel["r_multiple"],errors="coerce")
    valid=vol.gt(0)&pnl.notna()
    sel=sel.loc[valid].copy()
    sel["p"]=pnl.loc[valid]*(FIXED_LOT/vol.loc[valid])
    sel["r"]=r.loc[valid]
    p=sel["p"]; gp=float(p[p>0].sum()); gl=float(p[p<0].sum())
    pf=None if gl==0 else gp/abs(gl)
    b=INITIAL_BALANCE; balances=[b]; breach=False
    for x in p:
        b+=float(x); balances.append(b); breach |= b<=0
    return {
        "trades":int(len(sel)),"wins":int((p>0).sum()),"losses":int((p<0).sum()),
        "net_pnl_usd_fixed001":round(float(p.sum()),6),
        "gross_profit_usd":round(gp,6),"gross_loss_usd":round(gl,6),
        "ending_balance_proxy":round(b,6),
        "return_pct_proxy":round(100.0*(b-INITIAL_BALANCE)/INITIAL_BALANCE,4),
        "profit_factor":None if pf is None else round(float(pf),6),
        "max_balance_dd_pct_proxy":round(max_drawdown(balances),4),
        "balance_breach_proxy":bool(breach),
        "sum_r_original":round(float(sel["r"].sum()),6),
        "entry_times":[str(x) for x in sel["entry_time"].tolist()],
    }

def broker_pnl(tx:pd.DataFrame)->dict:
    if tx.empty:
        return {"deals":0,"round_trip_exit_deals":0,"net_pnl_usd":0.0,
                "gross_profit_usd":0.0,"gross_loss_usd":0.0}
    tx=tx.copy()
    cols=["profit","commission","swap","fee"]
    for c in cols:
        if c not in tx.columns: tx[c]=0.0
        tx[c]=pd.to_numeric(tx[c],errors="coerce").fillna(0.0)
    tx["net"]=tx[cols].sum(axis=1)
    entry=pd.to_numeric(tx.get("entry",0),errors="coerce").fillna(-1).astype(int)
    exits=tx[entry.isin([1,3])]
    return {
        "deals":int(len(tx)),
        "round_trip_exit_deals":int(len(exits)),
        "net_pnl_usd":round(float(tx["net"].sum()),6),
        "gross_profit_usd":round(float(tx.loc[tx["net"]>0,"net"].sum()),6),
        "gross_loss_usd":round(float(tx.loc[tx["net"]<0,"net"].sum()),6),
    }

def main()->int:
    ap=argparse.ArgumentParser()
    for a in ("trades","evals","events","transactions","output","summary","trade_report"):
        ap.add_argument("--"+a.replace("_","-"),dest=a,required=True)
    ns=ap.parse_args()
    trades=read_csv(Path(ns.trades)); evals=read_csv(Path(ns.evals))
    events=read_csv(Path(ns.events)); tx=read_csv(Path(ns.transactions))
    if trades.empty: raise RuntimeError("V58 missing trades.csv")
    if evals.empty: raise RuntimeError("V58 missing V58_ENTRY_EVAL.csv")

    trades=trades[(trades["candidate"]==CANDIDATE)&(trades["book"]==BOOK)].copy()
    trades["entry_time_dt"]=to_dt(trades["entry_time"])
    trades=trades[(trades["entry_time_dt"]>=WEEK_START)&(trades["entry_time_dt"]<WEEK_END)].copy()
    evals["time"]=to_dt(evals["time"])
    evals=evals[(evals["time"]>=WEEK_START)&(evals["time"]<WEEK_END)].copy()

    gate_results={n:summarize_gate(trades,evals,c) for n,c in GATES.items()}
    broker=broker_pnl(tx)

    keep=["time"]+list(GATES.values())+[
        "feature_ready","trend_h1","trend_h4","fast_trend_h1","fast_trend_m15",
        "structure_dir","bos_choch_dir","fvg_dir","liquidity_sweep_dir",
        "adx","plus_di","minus_di","rsi2","rsi14","macd_hist","score",
        "risk_cash_fixed001","risk_pct_equity","margin_cash","spread_points_entry",
        "spread_cash_entry","spread_risk_pct","lot_ok","allow_actual"
    ]
    keep=[c for c in keep if c in evals.columns]
    report=trades.merge(evals[keep],left_on="entry_time_dt",right_on="time",how="left")
    vv=pd.to_numeric(report["initial_volume_std_equiv"],errors="coerce")
    vp=pd.to_numeric(report["total_pnl"],errors="coerce")
    report["fixed001_pnl_shadow_usd"]=vp*(FIXED_LOT/vv.where(vv>0))
    report.to_csv(Path(ns.trade_report),index=False)

    num=evals.copy()
    for c in ["spread_points_entry","spread_cash_entry","spread_risk_pct","risk_cash_fixed001",
              "risk_pct_equity","margin_cash","rsi2","rsi14","score"]:
        if c in num.columns: num[c]=pd.to_numeric(num[c],errors="coerce")

    guard_counts={}; spread_blocks=[]; attempts=0
    if not events.empty and "action" in events.columns:
        g=events[events["action"]=="GUARD"]
        if not g.empty: guard_counts=g["direction"].astype(str).value_counts().to_dict()
        sb=events[events["action"]=="V58_SPREAD_BLOCK"]
        if not sb.empty: spread_blocks=sb.astype(str).to_dict("records")
        attempts=int((events["action"]=="V58_FIXED001_ATTEMPT").sum())

    payload={
        "schema":"v58_fixed001_pullback_trend_cost_weekly_replay_v1",
        "candidate":CANDIDATE,"book":BOOK,"fixed_lot":FIXED_LOT,
        "initial_balance_usd":INITIAL_BALANCE,"week":"2026-08-24..2026-08-28",
        "gate_results_shadow_fixed001":gate_results,
        "actual_broker_pullback80_gate":broker,
        "entry_evaluations":int(len(evals)),
        "actual_order_attempt_events":attempts,
        "guard_reason_counts":guard_counts,
        "spread_block_events":spread_blocks,
        "spread_points_entry_min":None if num.empty else round(float(num["spread_points_entry"].min()),4),
        "spread_points_entry_max":None if num.empty else round(float(num["spread_points_entry"].max()),4),
        "spread_cash_entry_min":None if num.empty else round(float(num["spread_cash_entry"].min()),6),
        "spread_cash_entry_max":None if num.empty else round(float(num["spread_cash_entry"].max()),6),
        "methodology":{
            "actual_gate":"RSI2 anti-chase: LONG<=80, SHORT>=20; tester-only",
            "spread_guard":"min($0.75, 5% of planned stop-risk cash)",
            "fast_trend":"closed-bar EMA20/EMA50 plus EMA20 slope on H1 and M15",
            "same_week_hypothesis_is_exploratory":True,
            "fixed_lot_001":True,
        },
    }
    Path(ns.output).write_text(json.dumps(payload,indent=2),encoding="utf-8")
    lines=[
        "V58_FIXED001_PULLBACK_TREND_COST_REPLAY=1",
        f"WEEK={payload['week']}",f"FIXED_LOT={FIXED_LOT:.2f}",
        f"ENTRY_EVALUATIONS={payload['entry_evaluations']}",
        f"ACTUAL_ORDER_ATTEMPTS={attempts}",
        f"ACTUAL_BROKER_DEALS={broker['deals']}",
        f"ACTUAL_BROKER_EXIT_DEALS={broker['round_trip_exit_deals']}",
        f"ACTUAL_BROKER_NET_USD={broker['net_pnl_usd']:.6f}",
        f"SPREAD_POINTS_ENTRY_MIN={payload['spread_points_entry_min']}",
        f"SPREAD_POINTS_ENTRY_MAX={payload['spread_points_entry_max']}",
        f"SPREAD_CASH_ENTRY_MIN={payload['spread_cash_entry_min']}",
        f"SPREAD_CASH_ENTRY_MAX={payload['spread_cash_entry_max']}",
    ]
    for name in GATES:
        r=gate_results[name]
        lines.append(
            f"GATE={name} trades={r['trades']} wins={r['wins']} losses={r['losses']} "
            f"net_usd={r['net_pnl_usd_fixed001']:.6f} return_pct_proxy={r['return_pct_proxy']:.4f} "
            f"pf={r['profit_factor']} max_dd_pct_proxy={r['max_balance_dd_pct_proxy']:.4f} "
            f"balance_breach={int(r['balance_breach_proxy'])}"
        )
    lines.append(f"GUARD_REASON_COUNTS={json.dumps(guard_counts,sort_keys=True)}")
    lines.append("NOTE=same-week RSI2 threshold is exploratory; V58 is not a production promotion")
    lines.append(f"TRADE_REPORT={ns.trade_report}")
    Path(ns.summary).write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
