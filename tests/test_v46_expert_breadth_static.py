#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_v46_expert_breadth_source.py"
AN = ROOT / "scripts" / "analyze_v46_expert_breadth.py"
RUN = ROOT / "runtime" / "v46_expert_breadth" / "RUN_V46_EXPERT_BREADTH_ONE_SHOT.py"
BOOT = ROOT / "runtime" / "v46_expert_breadth" / "BOOTSTRAP_V46_EXPERT_BREADTH_ONE_SHOT_GIT_BASH.sh"
PKG = ROOT / "runtime" / "v46_expert_breadth" / "PACKAGE_V46_EXISTING_OUTPUT_GIT_BASH.sh"


def rt(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_source_builder_freezes_primary_breadth4_and_sensitivity_only():
    text = rt(BUILD)
    assert 'SetupAdaptiveBreadthRouter(23,"v46_hl10_thr0p05_breadth4",2,0.05,0.00,4,0.05)' in text
    assert 'SetupAdaptiveBreadthRouter(24,"v46_hl10_thr0p05_breadth3_sensitivity",2,0.05,0.00,3,0.05)' in text
    assert 'SetupAdaptiveBreadthRouter(25,"v46_hl10_thr0p05_breadth5_sensitivity",2,0.05,0.00,5,0.05)' in text
    assert '#define CANDIDATE_COUNT 26' in text
    assert 'EXPECTED_OUTPUT_SHA = "3695095d80fd81847bbcc4e4ae0902c4ddbf713fe0ac9ab8549f1c19d77c1f13"' in text


def test_breadth_gate_is_causal_shadow_score_health():
    text = rt(BUILD)
    assert 'AdaptiveExpertScore(v,e)>=st.adaptive_breadth_score_threshold' in text
    assert 'healthy<st.adaptive_breadth_min_count' in text
    assert 'CopyRates' not in text and 'CopyBuffer' not in text
    assert 'TimeCurrent' not in text


def test_v46_is_one_long_2021_2026_run():
    text = rt(RUN)
    assert 'FROM_DATE = "2021.01.03"' in text
    assert 'TO_DATE = "2026.08.01"' in text
    assert 'WARMUP_MONTHS = 6' in text
    assert text.count('subprocess.run([str(base.TERMINAL_EXE), f"/config:{ini}"])') == 1


def test_cold_start_and_no_live_orders():
    run_text = rt(RUN)
    build_text = rt(BUILD)
    assert 'if state.exists(): state.unlink()' in run_text
    assert 'AllowLiveTrading=0' in run_text
    assert 'AllowDllImport=0' in run_text
    assert 'native_broker_orders=0' in run_text
    assert 'external_broker_orders=0' in run_text

    # The builder must contain the forbidden token literals because it uses them
    # as scanner signatures. The safety property is that every parent/generated
    # source is rejected when any signature is present; banning the literals from
    # the scanner itself is a false positive.
    assert 'FORBIDDEN = ("OrderSend(", "OrderSendAsync(", "CTrade", "trade.Buy(", "trade.Sell(")' in build_text
    assert 'for bad in FORBIDDEN:' in build_text
    assert 'forbidden native order path in parent' in build_text
    assert 'forbidden native order path introduced' in build_text
    assert 'MQLInfoInteger(MQL_TESTER)' in build_text


def test_analyzer_only_allows_primary_to_pass():
    text = rt(AN)
    assert 'PRIMARY = "v46_hl10_thr0p05_breadth4"' in text
    assert 'sensitivity_candidates_eligible_to_promote' in text
    assert 'False' in text
    for gate in (
        'raw_max_mtm_dd_at_most_20pct',
        'profit_factor_r_at_least_1p20',
        'annualized_return_at_least_10pct',
        'worst_full_year_not_below_minus10pct',
        'worst_rolling12_not_below_minus10pct',
        'unseen_2021_postwarmup_return_not_below_minus10pct',
        'sum_r_after_extra_0p05r_per_trade_positive',
    ):
        assert gate in text


def test_bootstrap_is_d_drive_portable_and_preserves_recovery_order():
    text = rt(BOOT)
    assert 'SCRIPT_DIR=' in text and '$HOME/v31_mt5_40usd' not in text
    assert 'MOVE_V45_TESTER_STORAGE_TO_D.py' in text
    assert 'PREPARE_V45_DISK.py' in text
    assert text.index('"$PY" "$(cygpath -w "$MOVE")"') < text.index('"$PY" "$(cygpath -w "$PREP")"') < text.index('"$PY" "$(cygpath -w "$RUNNER")"')
    assert 'git clean' not in text


def test_checkpoint_and_package_only_prevent_expensive_rerun():
    text = rt(RUN) + "\n" + rt(BOOT) + "\n" + rt(PKG)
    assert 'MT5_DONE.json' in text
    assert 'DONE.txt' in text
    assert 'MT5 NOT RERUN' in text
    assert 'MT5 WAS NOT RERUN' in text
    assert 'package_research_bundle_portable.py' in text


def test_manifest_markers_and_risk_contract():
    text = rt(BUILD) + "\n" + rt(RUN)
    for token in (
        'v46_expert_breadth=1',
        'v46_strategy_logic_changed=1',
        'v46_risk_changed=0',
        'v46_state_protocol=cold_start_no_future_state',
        'v46_single_tester_run=1',
        'v46_live_authorized=0',
    ):
        assert token in text


def _run_without_pytest():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn(); print("PASS", fn.__name__)
    print(f"V46 static tests PASS count={len(tests)}")


if __name__ == "__main__":
    _run_without_pytest()
