from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
import pandas as pd

REPO=Path(__file__).resolve().parents[1]
BUILDER=REPO/"scripts"/"build_v58_fixed001_pullback_trend_cost_source.py"
ANALYZER=REPO/"scripts"/"analyze_v58_fixed001_pullback_trend_cost.py"
RUNNER=REPO/"runtime"/"v58_fixed001_pullback_trend_cost"/"RUN_V58_FIXED001_PULLBACK_TREND_COST.py"
LAUNCHER=REPO/"runtime"/"v58_fixed001_pullback_trend_cost"/"START_V58_FIXED001_PULLBACK_TREND_COST_GIT_BASH.sh"
SEED=REPO/"runtime"/"v57_fixed001_trend_smc"/"accepted_v56_week_start_state_20260824.csv"
ADR=REPO/"docs"/"adr"/"ADR-060-v58-fixed001-pullback-trend-cost-research.md"

def load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    assert spec is not None and spec.loader is not None
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def test_fixed_001_and_pullback_hypothesis_are_explicit():
    t=BUILDER.read_text(encoding="utf-8")
    for tok in ("InpV57FixedLot = 0.01","InpV58PullbackRsi2MaxLong = 80.0",
                "InpV58PullbackRsi2MinShort = 20.0","gate_pullback80",
                "allow_actual=gate_pullback80","InpV55Magic = 580058"):
        assert tok in t

def test_spread_guard_is_cost_based_and_auditable():
    t=BUILDER.read_text(encoding="utf-8")
    for tok in ("InpV58MaxSpreadCash = 0.75","InpV58MaxSpreadRiskPct = 5.0",
                "V58SpreadCashNow","V58SpreadCostOk","V58_SPREAD_BLOCK",
                "V58_FIXED001_ATTEMPT","spread_points>InpV55MaxSpreadPoints"):
        assert tok in t
    assert 'for token in forbidden' in t

def test_fast_trend_is_closed_bar_multi_timeframe():
    t=BUILDER.read_text(encoding="utf-8")
    for tok in ("V58FastTrendDir","PERIOD_H1","PERIOD_M15","CopyRates(_Symbol,tf,1,need,r)",
                "gate_fast_h1_pullback80","gate_fast_both_pullback80"):
        assert tok in t

def test_runner_reuses_week_seed_and_one_real_tick_pass():
    t=RUNNER.read_text(encoding="utf-8")
    assert 'EXPECTED_BRANCH="agent/v58-fixed001-pullback-trend-cost-research"' in t
    assert 'WEEK_START_STATE_SHA256="7acf0260b9ab875722ad4888358b21cf4db72d80ec1de6de4ec999676c621259"' in t
    assert 'FROM_DATE="2026.08.24"' in t and 'TO_DATE="2026.08.29"' in t
    assert 'Model=4' in t
    assert 'V58_SINGLE_REAL_TICK_PASS=1' in t
    assert 'V58_SKIP_WARMUP=1' in t
    assert 'V58_ENTRY_EVAL.csv' in t

def test_seed_sha_preserved():
    assert hashlib.sha256(SEED.read_bytes()).hexdigest()=="7acf0260b9ab875722ad4888358b21cf4db72d80ec1de6de4ec999676c621259"

def test_pullback80_regression_on_v57_week():
    mod=load(ANALYZER,"v58_analyzer_regression")
    rows=[
        ("2026.08.24 00:00:00",0.0002,-0.334479,-1.00305,82.1121),
        ("2026.08.24 01:00:00",0.0001,0.174590,0.64616,68.8368),
        ("2026.08.24 05:00:00",0.0001,0.155020,0.63331,40.6705),
        ("2026.08.24 11:45:00",0.0002,0.216220,0.56019,96.2722),
        ("2026.08.24 14:00:00",0.0001,-0.281920,-1.00079,49.2694),
        ("2026.08.24 19:15:00",0.0001,0.301250,1.18812,51.0772),
        ("2026.08.25 05:15:00",0.0001,-0.263630,-1.00098,85.3091),
        ("2026.08.25 15:45:00",0.0001,-0.271350,-1.00008,96.0940),
        ("2026.08.27 02:15:00",0.0001,-0.208790,-1.00885,91.3939),
    ]
    trades=pd.DataFrame([{"entry_time":t,"entry_time_dt":pd.Timestamp(t),"initial_volume_std_equiv":v,
                          "total_pnl":p,"r_multiple":r} for t,v,p,r,_ in rows])
    evals=pd.DataFrame({"time":[pd.Timestamp(x[0]) for x in rows],
                        "gate_pullback80":[1 if x[4]<=80 else 0 for x in rows]})
    out=mod.summarize_gate(trades,evals,"gate_pullback80")
    assert out["trades"]==4 and out["wins"]==3 and out["losses"]==1
    assert abs(out["net_pnl_usd_fixed001"]-34.894)<1e-6
    assert out["profit_factor"] is not None and out["profit_factor"]>2.2

def test_launcher_is_portable_and_not_v31_hardcoded():
    t=LAUNCHER.read_text(encoding="utf-8")
    assert "agent/v58-fixed001-pullback-trend-cost-research" in t
    assert "V58_PYTHON_BOOTSTRAP=PASS" in t
    assert "v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv" not in t
    assert "RUN_V58_FIXED001_PULLBACK_TREND_COST.py" in t

def test_adr_exists_and_marks_same_week_as_exploratory():
    assert ADR.is_file()
    t=ADR.read_text(encoding="utf-8")
    assert "same-week" in t.lower() and "exploratory" in t.lower()
    assert "0.01" in t

def main()->int:
    tests=[v for k,v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn(); print("PASS",fn.__name__)
    print(f"V58 static tests PASS count={len(tests)}")
    return 0

if __name__=="__main__": raise SystemExit(main())
