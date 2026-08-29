from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
BUILDER = REPO / "scripts" / "build_v57_fixed001_trend_smc_source.py"
ANALYZER = REPO / "scripts" / "analyze_v57_fixed001_trend_smc.py"
RUNNER = REPO / "runtime" / "v57_fixed001_trend_smc" / "RUN_V57_FIXED001_TREND_SMC.py"
LAUNCHER = REPO / "runtime" / "v57_fixed001_trend_smc" / "START_V57_FIXED001_TREND_SMC_GIT_BASH.sh"
SEED = REPO / "runtime" / "v57_fixed001_trend_smc" / "accepted_v56_week_start_state_20260824.csv"
ADR = REPO / "docs" / "adr" / "ADR-059-v57-fixed001-trend-smc-research.md"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fixed_001_is_explicit_and_risk_bound_rounding_is_removed_from_open_path():
    text = BUILDER.read_text(encoding="utf-8")
    assert 'InpV57FixedLot = 0.01' in text
    assert 'InpV55Magic = 570057' in text
    assert 'double bv=InpV57FixedLot' in text
    assert 'V57FixedLotCompatible' in text
    assert 'v57_fixed_lot_or_margin_incompatible' in text
    assert 'double bv=V55RiskBoundVolume(B[ix].direction,vv,request_px,B[ix].stop,risk_money,loss_per_lot);' in text
    # The old line is present only as the exact removal marker / forbidden assertion in Python,
    # while the generated MQL is required to remove it.
    assert 'for token in forbidden' in text


def test_trend_smc_features_are_causal_and_multi_timeframe():
    text = BUILDER.read_text(encoding="utf-8")
    for token in (
        'PERIOD_H1', 'PERIOD_H4', 'V57EMA', 'V57ConfirmedSwings', 'const int wing=2',
        'V57RecentFvgDir', 'liquidity_sweep_dir', 'bos_choch_dir',
        'entry_adx>=18.0', 'entry_plus_di', 'entry_minus_di', 'entry_rsi14', 'entry_macd_hist',
        'gate_trend', 'gate_trend_adx', 'gate_trend_structure', 'gate_balanced', 'gate_strict',
    ):
        assert token in text, token
    assert 'shift(-' not in text


def test_entry_decision_is_latched_for_whole_virtual_trade():
    text = BUILDER.read_text(encoding="utf-8")
    for token in (
        'g_v57_entry_decided', 'g_v57_entry_allowed', 'g_v57_decision_entry_time',
        'g_v57_decision_entry_time!=B[ix].entry_time', 'v57_model_filter',
    ):
        assert token in text


def test_tester_only_research_observes_capital_limits_instead_of_claiming_production_safety():
    text = BUILDER.read_text(encoding="utf-8")
    assert 'if(!MQLInfoInteger(MQL_TESTER))' in text
    assert 'V57_WOULD_HALT' in text
    assert 'daily_loss_limit' in text
    assert 'max_drawdown_limit' in text
    assert 'DEAL_PROFIT' in text
    assert 'profit,commission,swap,fee' in text


def test_runner_reuses_accepted_week_start_state_and_only_one_real_tick_pass():
    text = RUNNER.read_text(encoding="utf-8")
    assert 'EXPECTED_BRANCH = "agent/v57-fixed001-trend-smc-research"' in text
    assert 'WEEK_START_STATE_SHA256 = "7acf0260b9ab875722ad4888358b21cf4db72d80ec1de6de4ec999676c621259"' in text
    assert 'V56_ACCEPTED_ZIP_SHA256 = "a9ec9c8cb0f7402c6ffac603fc187d79ca7aa281f84e0c0fdf8310bac3a23c55"' in text
    assert 'FROM_DATE = "2026.08.24"' in text
    assert 'TO_DATE = "2026.08.29"' in text
    assert 'Model=4' in text
    assert 'V57_SINGLE_REAL_TICK_PASS=1' in text
    assert 'V57_SKIP_WARMUP=1' in text
    assert 'V57_TRADE_REPORT.csv' in text


def test_seed_sha_is_frozen():
    digest = hashlib.sha256(SEED.read_bytes()).hexdigest()
    assert digest == "7acf0260b9ab875722ad4888358b21cf4db72d80ec1de6de4ec999676c621259"


def test_analyzer_reproduces_v56_week_fixed001_baseline_loss():
    mod = load(ANALYZER, "v57_analyzer_regression")
    rows = [
        ("2026.08.24 00:00:00", 0.0002, -0.334479, -1.00305),
        ("2026.08.24 01:00:00", 0.0001, 0.174590, 0.64616),
        ("2026.08.24 05:00:00", 0.0001, 0.155020, 0.63331),
        ("2026.08.24 11:45:00", 0.0002, 0.216220, 0.56019),
        ("2026.08.24 14:00:00", 0.0001, -0.281920, -1.00079),
        ("2026.08.24 19:15:00", 0.0001, 0.301250, 1.18812),
        ("2026.08.25 05:15:00", 0.0001, -0.263630, -1.00098),
        ("2026.08.25 15:45:00", 0.0001, -0.271350, -1.00008),
        ("2026.08.27 02:15:00", 0.0001, -0.208790, -1.00885),
    ]
    trades = pd.DataFrame([
        {"entry_time": t, "entry_time_dt": pd.Timestamp(t), "initial_volume_std_equiv": v,
         "total_pnl": p, "r_multiple": r}
        for t, v, p, r in rows
    ])
    evals = pd.DataFrame({"time": [pd.Timestamp(x[0]) for x in rows], "gate_baseline": [1]*len(rows)})
    out = mod.summarize_gate(trades, evals, "gate_baseline")
    assert out["trades"] == 9
    assert out["wins"] == 4
    assert out["losses"] == 5
    assert abs(out["net_pnl_usd_fixed001"] - (-45.39595)) < 1e-6
    assert out["balance_breach_proxy"] is True


def test_docs_and_launcher_exist():
    assert ADR.is_file()
    text = LAUNCHER.read_text(encoding="utf-8")
    assert 'agent/v57-fixed001-trend-smc-research' in text
    assert 'RUN_V57_FIXED001_TREND_SMC.py' in text


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print(f"V57 fixed001 trend-SMC static tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
