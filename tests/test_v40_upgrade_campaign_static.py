from pathlib import Path
import ast
import importlib.util
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def read(rel:str)->str:
    return (ROOT/rel).read_text(encoding="utf-8")

def load_module():
    p=ROOT/"scripts/v40_upgrade_campaign_stage_a.py"
    spec=importlib.util.spec_from_file_location("v40_upgrade_campaign_stage_a",p)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def test_v40_contract_is_first_passage_not_v39_threshold_sweep():
    text=read("scripts/v40_upgrade_campaign_stage_a_core.py")
    tree=ast.parse(text)
    assert 'MIN_R = 1.0' in text
    assert 'DOWN_R = 0.25' in text
    assert 'UP_R = 0.75' in text
    assert 'MIN_UP_LEVEL_R = 2.0' in text
    assert 'SCORE_QUANTILE = 0.80' in text
    assert 'STATIC_PROTECT_0.25R' in text
    assert 'SELECTIVE_TRAIL_0.25R' in text
    assert 'no_test_month_threshold_tuning' in text
    assert not any(isinstance(n,(ast.For,ast.ListComp)) and "quantile" in ast.unparse(n).lower() for n in ast.walk(tree))

def test_first_passage_event_order():
    m=load_module()
    g=pd.DataFrame({
        "trade_key":["g"]*4,
        "time":pd.date_range("2026-01-01",periods=4,freq="min"),
        "unrealized_r":[1.0,1.08,0.74,2.10],
    })
    x=m.first_passage_labels(g)
    assert x.iloc[0].fp_event=="GIVEBACK_FIRST"
    t=pd.DataFrame({
        "trade_key":["t"]*4,
        "time":pd.date_range("2026-01-01",periods=4,freq="min"),
        "unrealized_r":[1.0,1.30,2.01,0.70],
    })
    y=m.first_passage_labels(t)
    assert y.iloc[0].fp_event=="TAIL_FIRST"

def test_signal_source_merge_preserves_existing_and_avoids_suffix_collision():
    m=load_module()
    df=pd.DataFrame({
        "trade_key":["a","b"],
        "signal_sources":["EMA_MAIN", ""],
        "value":[1,2],
    })
    sig=pd.DataFrame({
        "trade_key":["a","b"],
        "signal_sources":["M15_FALLBACK_A","SLOW_MOM"],
    })
    out=m.attach_signal_sources(df,sig,"one_to_one")
    assert "signal_sources_x" not in out.columns and "signal_sources_y" not in out.columns
    assert out.loc[out.trade_key=="a","signal_sources"].iloc[0]=="EMA_MAIN"
    assert out.loc[out.trade_key=="b","signal_sources"].iloc[0]=="SLOW_MOM"
    fresh=m.attach_signal_sources(df.drop(columns="signal_sources"),sig,"one_to_one")
    assert fresh.signal_sources.tolist()==["M15_FALLBACK_A","SLOW_MOM"]

def test_protective_actions_do_not_add_entries_and_preserve_baseline_when_no_hit():
    m=load_module()
    g=pd.DataFrame({
        "time":pd.date_range("2026-01-01",periods=4,freq="min"),
        "unrealized_r":[1.0,1.10,1.30,1.40],
    })
    r,_,hit=m.simulate_action(g,pd.Timestamp("2026-01-01"),1.0,"STATIC_PROTECT_0.25R",1.4)
    assert hit is False and abs(r-1.4)<1e-12
    text=read("scripts/v40_upgrade_campaign_stage_a_core.py")
    assert '"extra_entries":0' in text
    assert '"risk_changed":False' in text

def test_shadow_equity_is_explicitly_not_exact_mt5():
    s=read("scripts/v40_upgrade_campaign_stage_a_core.py")
    r=read("runtime/v40_upgrade_campaign/RUN_V40_UPGRADE_CAMPAIGN_STAGE_A_GIT_BASH.sh")
    assert "Shadow equity is calibrated" in s
    assert "NOT exact-MT5 PnL" in r
    assert "shadow_is_exact_mt5=0" in r
    assert "107.43" in r and "8.58%" in r and "15%" in r

def test_runner_is_offline_safe_and_one_zip():
    r=read("runtime/v40_upgrade_campaign/RUN_V40_UPGRADE_CAMPAIGN_STAGE_A_GIT_BASH.sh")
    entry=read("scripts/v40_upgrade_campaign_stage_a.py")
    core=read("scripts/v40_upgrade_campaign_stage_a_core.py")
    cleaned="\n".join(line for line in r.splitlines() if "grep -Eiq" not in line) + "\n" + entry + "\n" + core
    for tok in ["terminal64.exe","metaeditor64.exe","OrderSend(","OrderSendAsync(","CTrade","trade.Buy(","trade.Sell("]:
        assert tok.lower() not in cleaned.lower()
    assert "live_trading=FORBIDDEN" in r
    assert "risk_changed=0" in r
    assert "extra_entries=0" in r
    assert "bundle_manifest_sha256.txt" in r
    assert "v40_upgrade_campaign_stage_a.zip" in r
    assert "ZIP integrity PASS" in r
    assert "execution_adapter" in entry
    assert "v40_upgrade_campaign_stage_a_core.py" in entry

def test_bootstrap_uses_explicit_refspec_and_preserves_runtime_evidence():
    b=read("runtime/v40_upgrade_campaign/BOOTSTRAP_V40_UPGRADE_CAMPAIGN_ONE_SHOT_GIT_BASH.sh")
    assert "agent/v40-upgrade-campaign" in b
    assert "+refs/heads/$BRANCH:$REMOTE_REF" in b
    assert 'checkout -B "$BRANCH" "$REMOTE_REF"' in b
    assert 'reset --hard "$REMOTE_REF"' in b
    assert "no git clean" in b

def test_v36_dependency_recovery_remains_hardened():
    p=read("runtime/v36_sequence_exit/RUN_V36_SEQUENCE_EXIT_DL_GIT_BASH.sh")
    assert "scikit-learn==1.8.0" in p
    assert "import numpy, pandas, torch, sklearn, scipy" in p

def _run_without_pytest():
    tests=[
        test_v40_contract_is_first_passage_not_v39_threshold_sweep,
        test_first_passage_event_order,
        test_signal_source_merge_preserves_existing_and_avoids_suffix_collision,
        test_protective_actions_do_not_add_entries_and_preserve_baseline_when_no_hit,
        test_shadow_equity_is_explicitly_not_exact_mt5,
        test_runner_is_offline_safe_and_one_zip,
        test_bootstrap_uses_explicit_refspec_and_preserves_runtime_evidence,
        test_v36_dependency_recovery_remains_hardened,
    ]
    for fn in tests:
        fn(); print(f"PASS {fn.__name__}")
    print(f"V40 static tests PASS count={len(tests)}")

if __name__=="__main__":
    _run_without_pytest()
