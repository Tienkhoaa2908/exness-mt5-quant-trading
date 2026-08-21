#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

BOOK = "usd40_r1p0_cent_continuous"
CONTROL = "adaptive_ewma_hl8_thr0"
CANDIDATES = [
    CONTROL,
    "adaptive_ewma_hl8_thr0p05",
    "adaptive_ewma_hl10_thr0p05",
]
EXPECTED_CONTROL_FINAL = 107.432645
EXPECTED_CONTROL_TRADES = 563
EXPECTED_MONTHLY_TRADES = [30,72,76,37,43,65,41,37,20,32,62,48]
EXPECTED_MONTHLY_FINAL = [38.951141,43.518604,46.317250,47.137010,51.403129,63.068101,63.241472,64.790962,64.922339,73.052422,88.574123,107.432645]
ANNUAL_TAG = "y01_2025_08_2026_08"

WINDOWS = [
    ("y01_2025_08_2026_08","annual","2025.08.01","2026.08.01",12),
    ("h01_2025_08_2026_02","halfyear","2025.08.01","2026.02.01",6),
    ("h02_2026_02_2026_08","halfyear","2026.02.01","2026.08.01",6),
    ("q01_2025_08_11","quarter","2025.08.01","2025.11.01",3),
    ("q02_2025_11_2026_02","quarter","2025.11.01","2026.02.01",3),
    ("q03_2026_02_05","quarter","2026.02.01","2026.05.01",3),
    ("q04_2026_05_08","quarter","2026.05.01","2026.08.01",3),
    ("m01_2025_08","month","2025.08.01","2025.09.01",1),
    ("m02_2025_09","month","2025.09.01","2025.10.01",1),
    ("m03_2025_10","month","2025.10.01","2025.11.01",1),
    ("m04_2025_11","month","2025.11.01","2025.12.01",1),
    ("m05_2025_12","month","2025.12.01","2026.01.01",1),
    ("m06_2026_01","month","2026.01.01","2026.02.01",1),
    ("m07_2026_02","month","2026.02.01","2026.03.01",1),
    ("m08_2026_03","month","2026.03.01","2026.04.01",1),
    ("m09_2026_04","month","2026.04.01","2026.05.01",1),
    ("m10_2026_05","month","2026.05.01","2026.06.01",1),
    ("m11_2026_06","month","2026.06.01","2026.07.01",1),
    ("m12_2026_07","month","2026.07.01","2026.08.01",1),
]
MONTH_TO_TAG = {
    "2025_08":"m01_2025_08","2025_09":"m02_2025_09","2025_10":"m03_2025_10",
    "2025_11":"m04_2025_11","2025_12":"m05_2025_12","2026_01":"m06_2026_01",
    "2026_02":"m07_2026_02","2026_03":"m08_2026_03","2026_04":"m09_2026_04",
    "2026_05":"m10_2026_05","2026_06":"m11_2026_06","2026_07":"m12_2026_07",
}

def parse_time(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, format="%Y.%m.%d %H:%M:%S", errors="raise")

def pf_from_trades(t: pd.DataFrame) -> float:
    if t.empty:
        return 0.0
    pnl = t["total_pnl"].astype(float)
    gp = float(pnl[pnl > 0].sum())
    gl = float(-pnl[pnl < 0].sum())
    if gl > 0:
        return gp / gl
    return math.inf if gp > 0 else 0.0

def load_window(root: Path, tag: str) -> tuple[pd.DataFrame,pd.DataFrame,str]:
    d = root / tag
    for name in ("monthly_summary.csv","trades.csv","manifest.txt","DONE.txt"):
        p=d/name
        if not p.is_file() or p.stat().st_size == 0:
            raise RuntimeError(f"{tag}: missing completed artifact {name}")
    manifest=(d/"manifest.txt").read_text(encoding="utf-8-sig",errors="replace")
    for tok in (
        "v44_baseline_validation=1",
        "v44_strategy_logic_changed=0",
        "v44_risk_changed=0",
        "tester_only=1",
        "native_broker_orders=0",
        "external_broker_orders=0",
        "v44_live_authorized=0",
    ):
        if tok not in manifest:
            raise RuntimeError(f"{tag}: manifest contract missing {tok}")
    return pd.read_csv(d/"monthly_summary.csv"),pd.read_csv(d/"trades.csv"),manifest

def metrics(root: Path, window: tuple[str,str,str,str,int], candidate: str) -> dict:
    tag,kind,start,end,nmonths=window
    monthly,trades,_=load_window(root,tag)
    m=monthly[(monthly["candidate"]==candidate)&(monthly["book"]==BOOK)].copy().sort_values("month").reset_index(drop=True)
    t=trades[(trades["candidate"]==candidate)&(trades["book"]==BOOK)].copy()
    if len(m)!=nmonths:
        raise RuntimeError(f"{tag}/{candidate}: expected {nmonths} monthly rows got {len(m)}")
    initial=float(m["initial_balance"].iloc[0])
    if abs(initial-40.0)>1e-6:
        raise RuntimeError(f"{tag}/{candidate}: restart initial balance {initial} != 40")
    ending=float(m["final_balance"].iloc[-1])
    total_return=100.0*(ending/initial-1.0)
    geo=100.0*((ending/initial)**(1.0/nmonths)-1.0) if ending>0 else -100.0
    dd=float(m["max_mtm_dd_pct"].astype(float).max())
    if not t.empty:
        t["entry_dt"]=parse_time(t["entry_time"])
        t["exit_dt"]=parse_time(t["exit_time"])
        t["hold_minutes"]=(t["exit_dt"]-t["entry_dt"]).dt.total_seconds()/60.0
    return {
        "tag":tag,"kind":kind,"from":start,"to":end,"months":nmonths,"candidate":candidate,
        "initial_usd":initial,"ending_usd":ending,"total_return_pct":total_return,
        "geo_month_pct":geo,"max_mtm_dd_pct":dd,"return_to_dd":total_return/dd if dd>0 else None,
        "trades":int(len(t)),"positive_submonths":int((m["return_pct"].astype(float)>0).sum()),
        "worst_submonth_pct":float(m["return_pct"].astype(float).min()),
        "best_submonth_pct":float(m["return_pct"].astype(float).max()),
        "avg_r":float(t["r_multiple"].astype(float).mean()) if len(t) else None,
        "sum_r":float(t["r_multiple"].astype(float).sum()) if len(t) else 0.0,
        "profit_factor":pf_from_trades(t),
        "turnover_x_start40":float(m["gross_notional_turnover"].astype(float).sum()/40.0),
        "median_hold_minutes":float(t["hold_minutes"].median()) if len(t) else None,
        "monthly_labels":[str(x) for x in m["month"]],
        "monthly_return_pct":[float(x) for x in m["return_pct"].astype(float)],
        "monthly_final_balance":[float(x) for x in m["final_balance"].astype(float)],
        "monthly_trades":[int(x) for x in m["trades"].astype(int)],
    }

def verify_annual_control(root: Path) -> dict:
    annual=next(w for w in WINDOWS if w[0]==ANNUAL_TAG)
    row=metrics(root,annual,CONTROL)
    errors=[]
    if row["trades"]!=EXPECTED_CONTROL_TRADES:
        errors.append(f"trades={row['trades']} expected={EXPECTED_CONTROL_TRADES}")
    if row["monthly_trades"]!=EXPECTED_MONTHLY_TRADES:
        errors.append("monthly trade-count vector differs from accepted V38")
    if len(row["monthly_final_balance"])==12:
        diff=float(np.max(np.abs(np.asarray(row["monthly_final_balance"])-np.asarray(EXPECTED_MONTHLY_FINAL))))
        if diff>1e-5:
            errors.append(f"monthly final-balance max diff={diff:.9g}")
    else:
        errors.append("annual control missing 12 monthly balances")
    if abs(row["ending_usd"]-EXPECTED_CONTROL_FINAL)>1e-5:
        errors.append(f"ending={row['ending_usd']} expected={EXPECTED_CONTROL_FINAL}")
    return {"pass":not errors,"errors":errors,"control":row}

def summarize_candidate(rows: list[dict], candidate: str, annual_continuous: dict, control_annual: dict) -> dict:
    crows=[r for r in rows if r["candidate"]==candidate]
    bykind={k:[r for r in crows if r["kind"]==k] for k in ("month","quarter","halfyear","annual")}
    annual=bykind["annual"][0]
    months=sorted(bykind["month"],key=lambda r:r["tag"])
    quarters=sorted(bykind["quarter"],key=lambda r:r["tag"])
    halves=sorted(bykind["halfyear"],key=lambda r:r["tag"])
    cont_month_returns=dict(zip(annual_continuous["monthly_labels"],annual_continuous["monthly_return_pct"]))
    restart_deltas=[]
    sign_agree=0
    for r in months:
        label=r["monthly_labels"][0]
        cont=cont_month_returns[label]
        restart=r["total_return_pct"]
        restart_deltas.append(restart-cont)
        if (restart>0)==(cont>0) or (abs(restart)<1e-12 and abs(cont)<1e-12):
            sign_agree+=1
    control_turnover=control_annual["turnover_x_start40"]
    control_trades=control_annual["trades"]
    checks={
        "annual_total_return_at_least_100pct": annual["total_return_pct"]>=100.0,
        "annual_max_dd_at_most_12p5pct": annual["max_mtm_dd_pct"]<=12.5,
        "annual_profit_factor_at_least_1p30": annual["profit_factor"]>=1.30,
        "positive_month_restart_at_least_8_of_12": sum(r["total_return_pct"]>0 for r in months)>=8,
        "positive_quarter_restart_at_least_3_of_4": sum(r["total_return_pct"]>0 for r in quarters)>=3,
        "positive_halfyears_2_of_2": sum(r["total_return_pct"]>0 for r in halves)==2,
        "worst_restart_month_not_below_minus10pct": min(r["total_return_pct"] for r in months)>=-10.0,
        "restart_vs_continuous_month_sign_agreement_at_least_9_of_12": sign_agree>=9,
        "annual_turnover_at_most_110pct_control": annual["turnover_x_start40"]<=1.10*control_turnover,
        "annual_trade_breadth_at_least_85pct_control": annual["trades"]>=math.ceil(0.85*control_trades),
    }
    return {
        "candidate":candidate,
        "annual":annual,
        "monthly_restart_positive":int(sum(r["total_return_pct"]>0 for r in months)),
        "quarter_restart_positive":int(sum(r["total_return_pct"]>0 for r in quarters)),
        "halfyear_restart_positive":int(sum(r["total_return_pct"]>0 for r in halves)),
        "worst_restart_month_pct":float(min(r["total_return_pct"] for r in months)),
        "median_restart_month_pct":float(np.median([r["total_return_pct"] for r in months])),
        "restart_vs_continuous_sign_agreement":sign_agree,
        "restart_vs_continuous_mean_abs_delta_pp":float(np.mean(np.abs(restart_deltas))),
        "extra_friction_stress":{"sum_r_minus_0p02r_each_trade":annual["sum_r"]-0.02*annual["trades"],
                                 "sum_r_minus_0p05r_each_trade":annual["sum_r"]-0.05*annual["trades"]},
        "paper_demo_readiness":{"pass":all(checks.values()),"checks":checks},
    }

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--checkpoint-root",required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--csv",required=True)
    ap.add_argument("--verify-annual-only",action="store_true")
    args=ap.parse_args()
    root=Path(args.checkpoint_root)
    annual_check=verify_annual_control(root)
    if not annual_check["pass"]:
        raise RuntimeError("V44 annual control reproduction failed: "+"; ".join(annual_check["errors"]))
    if args.verify_annual_only:
        Path(args.output).write_text(json.dumps({"schema":"v44_annual_preflight_v1","annual_control_reproduction":annual_check},indent=2,allow_nan=False),encoding="utf-8")
        pd.DataFrame([{k:v for k,v in annual_check["control"].items() if not isinstance(v,list)}]).to_csv(args.csv,index=False,lineterminator="\n")
        print(json.dumps({"annual_control_reproduction":"PASS","ending_usd":annual_check["control"]["ending_usd"],"trades":annual_check["control"]["trades"]},indent=2))
        return 0

    all_rows=[]
    for w in WINDOWS:
        for c in CANDIDATES:
            all_rows.append(metrics(root,w,c))
    annual_rows={c:next(r for r in all_rows if r["candidate"]==c and r["tag"]==ANNUAL_TAG) for c in CANDIDATES}
    summaries=[summarize_candidate(all_rows,c,annual_rows[c],annual_rows[CONTROL]) for c in CANDIDATES]
    ready=[s for s in summaries if s["paper_demo_readiness"]["pass"]]
    winner=max(ready if ready else summaries,key=lambda s:(s["annual"]["geo_month_pct"],-s["annual"]["max_mtm_dd_pct"]))
    status="PAPER_DEMO_READY" if ready else "HOLD"
    flat=[]
    for r in all_rows:
        flat.append({k:v for k,v in r.items() if not isinstance(v,list)})
    pd.DataFrame(flat).to_csv(args.csv,index=False,lineterminator="\n")
    out={
        "schema":"v44_baseline_robustness_validation_exact_mt5_v1",
        "window_protocol":{"count":len(WINDOWS),"monthly":12,"quarter_blocks":4,"halfyears":2,"annual":1,
                           "restart_semantics":"Each exact window resets to the accepted 2025-08 state. Annual run additionally provides continuous monthly path for restart-vs-continuous comparison."},
        "annual_control_reproduction":annual_check,
        "candidates":summaries,
        "status":status,
        "deployment_research_winner":winner["candidate"],
        "paper_demo_ready_candidates":[s["candidate"] for s in ready],
        "live_authorized":False,
        "decision_rule":"This campaign validates robustness only and does not retune the three frozen routers on these 19 windows. A readiness PASS permits paper/demo deployment research only. Real-money live trading remains forbidden.",
    }
    Path(args.output).write_text(json.dumps(out,indent=2,allow_nan=False),encoding="utf-8")
    print(json.dumps({"status":status,"winner":winner["candidate"],"ready":out["paper_demo_ready_candidates"],
                      "control_end":annual_rows[CONTROL]["ending_usd"],
                      "control_geo":annual_rows[CONTROL]["geo_month_pct"],
                      "live_authorized":False},indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
