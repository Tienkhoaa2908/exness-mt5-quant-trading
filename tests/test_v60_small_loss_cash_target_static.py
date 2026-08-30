from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILDER = REPO / "scripts" / "build_v60_small_loss_cash_target_source.py"
SCREEN_BUILDER = REPO / "scripts" / "build_v60_small_loss_cash_target_screen_source.py"
ANALYZER = REPO / "scripts" / "analyze_v60_small_loss_cash_target.py"
RUNNER = REPO / "runtime" / "v60_small_loss_cash_target" / "RUN_V60_SMALL_LOSS_CASH_TARGET.py"
LAUNCHER = REPO / "runtime" / "v60_small_loss_cash_target" / "START_V60_SMALL_LOSS_CASH_TARGET_GIT_BASH.sh"
ADR = REPO / "docs" / "adr" / "ADR-062-v60-small-loss-cash-target-research.md"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def generated() -> str:
    mod = load(BUILDER, "v60_builder_static")
    text = mod.transform()
    mod.validate(text)
    return text


def test_v60_fixed_lot_cash_target_and_small_loss_contract():
    text = generated()
    for token in (
        "InpV60FixedLot = 0.01",
        "InpV60PrimaryTargetCash = 2.00",
        "InpV60ShadowTargetCash2 = 2.00",
        "InpV60ShadowTargetCash3 = 3.00",
        "InpV60ShadowTargetCash4 = 4.00",
        "InpV60SoftLossCash = 1.00",
        "InpV60MaxStopRiskCash = 1.25",
        "V60PriceForCashTarget",
        "structural_risk_cash_cap",
        "SOFT_LOSS_CUT",
    ):
        assert token in text, token
    assert "InpV60ActualRR" not in text


def test_v60_strict_bidirectional_trend_and_location_symmetry():
    text = generated()
    for token in (
        "f.h1_trend==1 && f.h4_trend==1",
        "f.h1_trend==-1 && f.h4_trend==-1",
        "f.range_location<=0.45",
        "f.range_location>=0.55",
        "V60ScoreDirection(1,f)",
        "V60ScoreDirection(-1,f)",
        "g_trade.Buy",
        "g_trade.Sell",
    ):
        assert token in text, token
    assert "f.h4_trend!=-1" not in text
    assert "f.h4_trend!=1" not in text
    assert "range_location<=0.55) f.location_dir=1" not in text
    assert "range_location>=0.45) f.location_dir=-1" not in text


def test_v60_causal_and_no_v59_runtime_dependency_in_generated_mql():
    text = generated()
    for token in (
        "CopyRates(_Symbol,PERIOD_M15,1,320,m15)",
        "CopyRates(_Symbol,PERIOD_H1,1,260,h1)",
        "CopyRates(_Symbol,PERIOD_H4,1,140,h4)",
        "V60ConfirmedSwings",
        "const int wing=2",
    ):
        assert token in text, token
    assert "V59" not in text
    assert "PositionClosePartial" not in text


def test_screen_builder_sets_only_screen_default():
    screen = load(SCREEN_BUILDER, "v60_screen_static")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "screen.mq5"
        screen.build(p)
        text = p.read_text(encoding="utf-8")
    assert "InpV60ScreenOnly = true" in text
    assert "InpV60FixedLot = 0.01" in text
    assert "InpV60PrimaryTargetCash = 2.00" in text
    assert "g_trade.Buy" in text and "g_trade.Sell" in text


def test_v60_analyzer_counts_round_trips_not_entry_deals():
    mod = load(ANALYZER, "v60_analyzer_static")
    deals = [
        {"entry": "0", "profit": "0", "commission": "-0.05", "swap": "0", "fee": "0", "reason": "0"},
        {"entry": "1", "profit": "2.00", "commission": "-0.05", "swap": "0", "fee": "0", "reason": "5"},
        {"entry": "0", "profit": "0", "commission": "-0.05", "swap": "0", "fee": "0", "reason": "0"},
        {"entry": "1", "profit": "-1.20", "commission": "-0.05", "swap": "0", "fee": "0", "reason": "4"},
    ]
    s = mod.actual_summary(deals, [])
    assert s["round_trips"] == 2
    assert s["entry_deals"] == 2
    assert s["exit_deals"] == 2
    assert abs(s["net_usd"] - 0.6) < 1e-9
    assert s["losses_over_1_usd"] == 1
    assert s["losses_over_1p25_usd"] == 0


def test_v60_shadow_cash_summary_is_loss_first():
    mod = load(ANALYZER, "v60_cash_summary_static")
    rows = [
        {"direction": "1", "result_cash_2": "2.0"},
        {"direction": "1", "result_cash_2": "2.0"},
        {"direction": "-1", "result_cash_2": "-1.0"},
    ]
    s = mod.cash_summary(rows, "result_cash_2")
    assert s["trades"] == 3
    assert s["wins"] == 2 and s["losses"] == 1
    assert abs(s["net_usd"] - 3.0) < 1e-9
    assert abs(s["avg_loss_usd"] + 1.0) < 1e-9


def test_v60_runner_validates_two_long_and_two_short_windows_without_pnl_selection():
    text = RUNNER.read_text(encoding="utf-8")
    for token in (
        'EXPECTED_BRANCH = "agent/v60-small-loss-cash-target-research"',
        "SCREEN_MODEL = 2",
        "REAL_MODEL = 4",
        'SCREEN_FROM = "2025.09.01"',
        'SCREEN_TO = "2026.08.29"',
        "two_most_recent_feasible_strict_h4_h1_aligned_weeks_not_pnl",
        "len(result[\"long\"]) < 2",
        "len(result[\"short\"]) < 2",
        "V60_REAL_TICK_PASS_START",
    ):
        assert token in text, token
    section = text[text.index("def select_directional_windows"):text.index("def analyze")].lower()
    assert "profit" not in section


def test_v60_launcher_is_portable_and_tester_only_workflow():
    text = LAUNCHER.read_text(encoding="utf-8")
    assert "py.exe" in text and "python.exe" in text
    assert "RUN_V60_SMALL_LOSS_CASH_TARGET.py" in text
    assert "runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv" not in text


def test_adr_records_loss_first_non_forced_stop_policy():
    text = ADR.read_text(encoding="utf-8")
    for token in (
        "Loss-first objective",
        "Fixed lot remains 0.01",
        "Do not fake a $1 stop",
        "Primary target is $2",
        "not authorization for REAL-money activation",
    ):
        assert token in text, token


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print(f"V60 small-loss cash-target static tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
