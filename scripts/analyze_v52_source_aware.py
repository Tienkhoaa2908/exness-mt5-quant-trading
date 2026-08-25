#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
V46_ANALYZER = REPO / "scripts" / "analyze_v46_expert_breadth.py"
BASELINE = "v46_hl10_thr0p05_breadth4"
CHALLENGERS = [
    "v52_b4_or_b3_trend",
    "v52_b4_or_b3_bos",
    "v52_b4_or_b3_trend_bos",
]
ALL = [BASELINE] + CHALLENGERS


def load_module(path: Path, name: str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(f"cannot load {path}")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

v46=load_module(V46_ANALYZER,"v46_analyzer_for_v52")


def finite_or(value, fallback: float) -> float:
    return fallback if value is None else float(value)


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-folder",required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--summary-csv",required=True)
    ap.add_argument("--monthly-csv",required=True)
    ns=ap.parse_args()

    run=Path(ns.run_folder)
    monthly,trades,manifest=v46.load_run(run)
    for token in ("v52_source_aware_challenger=1","v52_risk_changed=0","v52_single_tester_run=1"):
        if token not in manifest: raise RuntimeError(f"V52 manifest token missing: {token}")

    results=[]; monthly_parts=[]
    for cand in ALL:
        result,m,_,_=v46.analyze_candidate(monthly,trades,cand)
        results.append(result); monthly_parts.append(m.assign(candidate=cand))

    baseline=next(x for x in results if x["candidate"]==BASELINE)
    be=baseline["evaluation"]
    bdd=float(baseline["raw_cold_start"]["max_mtm_dd_pct"])
    bpf=float(be["profit_factor_r"]); bavgr=float(be["avg_r"])

    guardrails={
        "min_frequency_ratio":1.05,
        "max_dd_absolute_pct":20.0,
        "max_dd_increase_points":3.0,
        "min_pf_absolute":1.20,
        "min_pf_ratio_vs_baseline":0.95,
        "min_avgr_absolute":0.10,
        "min_avgr_ratio_vs_baseline":0.75,
        "min_annualized_return_pct":10.0,
        "min_worst_full_year_pct":-10.0,
        "min_worst_rolling12_pct":-10.0,
        "friction_cost_r_per_trade":0.05,
    }

    rows=[]; eligible=[]
    for result in results:
        e=result["evaluation"]; dd=float(result["raw_cold_start"]["max_mtm_dd_pct"])
        freq=float(e["trades"])/max(1,float(be["trades"]))
        stress=float(result["friction_stress"]["sum_r_minus_0p05r_each_trade"])
        worst_year=finite_or(result["year_stability"]["worst_full_year_pct"],-999.0)
        worst_roll=finite_or(result["rolling_12m"]["worst_pct"],-999.0)
        if result["candidate"]==BASELINE:
            checks={"baseline_reference":True}; ok=True
        else:
            checks={
                "frequency_gain_at_least_5pct":freq>=guardrails["min_frequency_ratio"],
                "dd_not_above_20pct":dd<=guardrails["max_dd_absolute_pct"],
                "dd_increase_not_above_3_points":dd<=bdd+guardrails["max_dd_increase_points"],
                "pf_preserved":float(e["profit_factor_r"])>=max(guardrails["min_pf_absolute"],bpf*guardrails["min_pf_ratio_vs_baseline"]),
                "avgr_preserved":float(e["avg_r"])>=max(guardrails["min_avgr_absolute"],bavgr*guardrails["min_avgr_ratio_vs_baseline"]),
                "annualized_at_least_10pct":float(e["annualized_return_pct"])>=guardrails["min_annualized_return_pct"],
                "friction_stress_positive":stress>0.0,
                "worst_full_year_not_below_minus10":worst_year>=guardrails["min_worst_full_year_pct"],
                "worst_rolling12_not_below_minus10":worst_roll>=guardrails["min_worst_rolling12_pct"],
            }
            ok=all(checks.values())
        utility=stress/max(5.0,dd)
        row={
            "candidate":result["candidate"],"eligible":int(ok),"frequency_ratio":freq,"frequency_gain_pct":100.0*(freq-1.0),
            "trades":int(e["trades"]),"avg_r":float(e["avg_r"]),"sum_r":float(e["sum_r"]),"profit_factor_r":float(e["profit_factor_r"]),
            "annualized_return_pct":float(e["annualized_return_pct"]),"max_mtm_dd_pct":dd,
            "stress_sum_r_minus_0p05r":stress,"utility_stress_per_dd":utility,
            "worst_full_year_pct":worst_year,"worst_rolling12_pct":worst_roll,"checks":checks,
        }
        rows.append(row)
        if result["candidate"]!=BASELINE and ok: eligible.append(row)

    if eligible:
        selected=max(eligible,key=lambda r:(r["utility_stress_per_dd"],r["stress_sum_r_minus_0p05r"],-r["max_mtm_dd_pct"],r["frequency_ratio"]))
        status="V52_CHALLENGER_SELECTED"; selected_name=selected["candidate"]
    else:
        status="V52_KEEP_BREADTH4"; selected_name=BASELINE

    payload={
        "schema":"v52_source_aware_tournament_v1",
        "status":status,
        "baseline":BASELINE,
        "selected_candidate":selected_name,
        "guardrails":guardrails,
        "same_sample_research_note":"V52 is a small preregistered source-aware follow-up motivated by V51 diagnostics. A selected candidate still requires short broker-DEMO confirmation.",
        "candidates":rows,
        "raw_v46_style_results":results,
    }
    Path(ns.output).write_text(json.dumps(payload,indent=2),encoding="utf-8")

    import pandas as pd
    pd.DataFrame([{k:v for k,v in r.items() if k!="checks"} for r in rows]).to_csv(ns.summary_csv,index=False)
    pd.concat(monthly_parts,ignore_index=True).to_csv(ns.monthly_csv,index=False)

    print(f"STATUS={status}")
    print(f"BASELINE={BASELINE}")
    print(f"SELECTED={selected_name}")
    for r in rows:
        print("CANDIDATE",r["candidate"],"eligible="+str(r["eligible"]),"trades="+str(r["trades"]),"freq="+f"{r['frequency_ratio']:.3f}","AvgR="+f"{r['avg_r']:.4f}","PF="+f"{r['profit_factor_r']:.4f}","DD="+f"{r['max_mtm_dd_pct']:.3f}","stress="+f"{r['stress_sum_r_minus_0p05r']:.3f}")
    return 0


if __name__=="__main__": raise SystemExit(main())
