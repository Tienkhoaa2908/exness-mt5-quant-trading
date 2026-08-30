from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILDER = REPO / "scripts" / "build_v59_integrated_bidirectional_rr_source.py"
SCREEN_BUILDER = REPO / "scripts" / "build_v59_integrated_bidirectional_rr_screen_source.py"
ANALYZER = REPO / "scripts" / "analyze_v59_integrated_bidirectional_rr.py"
RUNNER = REPO / "runtime" / "v59_integrated_bidirectional_rr" / "RUN_V59_INTEGRATED_BIDIRECTIONAL_RR.py"
LAUNCHER = REPO / "runtime" / "v59_integrated_bidirectional_rr" / "START_V59_INTEGRATED_BIDIRECTIONAL_RR_GIT_BASH.sh"
ADR = REPO / "docs" / "adr" / "ADR-061-v59-integrated-bidirectional-rr-research.md"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_standalone_engine_has_symmetric_long_short_path_and_no_v52_dependency():
    text = BUILDER.read_text(encoding="utf-8")
    for token in (
        "V59ScoreDirection(1,f)",
        "V59ScoreDirection(-1,f)",
        "long_regime",
        "short_regime",
        "g_trade.Buy",
        "g_trade.Sell",
        "V59SelectDirection",
    ):
        assert token in text, token
    assert "v52_b4_or_b3_trend_bos" not in text
    assert "V55RiskBoundVolume" not in text


def test_structural_stop_fixed001_and_rr_variants_are_explicit():
    text = BUILDER.read_text(encoding="utf-8")
    for token in (
        "InpV59FixedLot = 0.01",
        "InpV59MaxStopRiskCash = 8.0",
        "InpV59MaxStopATR = 1.50",
        "f.swing_low-InpV59StopAtrBuffer*f.atr15",
        "f.swing_high+InpV59StopAtrBuffer*f.atr15",
        "structural_risk_cash_cap",
        "InpV59ActualRR = 3.0",
        "result_2r,result_2p5r,result_3r",
        "r>=2.0",
        "r>=2.5",
        "r>=3.0",
    ):
        assert token in text, token
    assert "PositionClosePartial" not in text


def test_features_are_causal_closed_bar_and_multi_timeframe():
    text = BUILDER.read_text(encoding="utf-8")
    for token in (
        "CopyRates(_Symbol,PERIOD_M15,1,320,m15)",
        "CopyRates(_Symbol,PERIOD_H1,1,260,h1)",
        "CopyRates(_Symbol,PERIOD_H4,1,140,h4)",
        "V59ConfirmedSwings",
        "const int wing=2",
        "V59RecentFvgDir",
        "V59OrderBlockRetestDir",
        "V59DIADX",
        "V59RSI",
    ):
        assert token in text, token
    assert "CopyRates(_Symbol,PERIOD_M15,0," not in text


def test_screen_builder_only_changes_screen_default():
    base = load(BUILDER, "v59_builder_test")
    screen = load(SCREEN_BUILDER, "v59_screen_builder_test")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "screen.mq5"
        screen.build(p)
        text = p.read_text(encoding="utf-8")
    assert "InpV59ScreenOnly = true" in text
    assert "InpV59FixedLot = 0.01" in text
    assert "g_trade.Buy" in text and "g_trade.Sell" in text
    assert base.MQL.count("InpV59ScreenOnly = false") == 1


def test_runner_uses_pnl_independent_directional_screen_then_model4():
    text = RUNNER.read_text(encoding="utf-8")
    for token in (
        'EXPECTED_BRANCH = "agent/v59-integrated-bidirectional-rr-research"',
        "SCREEN_MODEL = 2",
        "REAL_MODEL = 4",
        'SCREEN_FROM = "2025.09.01"',
        'SCREEN_TO = "2026.08.29"',
        "most_recent_feasible_h4_aligned_signal_week_not_pnl",
        "V59_REAL_TICK_PASS_START",
        "timeout=5400",
        "V59_SELECTED_WINDOWS.json",
    ):
        assert token in text, token
    assert "profit" not in text[text.index("def select_directional_windows"):text.index("def analyze")].lower()


def test_analyzer_reports_direction_rr_and_actual_broker():
    mod = load(ANALYZER, "v59_analyzer_test")
    shadow = [
        {"direction": "1", "risk_cash": "5", "result_2r": "2", "result_2p5r": "2.5", "result_3r": "3"},
        {"direction": "-1", "risk_cash": "4", "result_2r": "-1", "result_2p5r": "-1", "result_3r": "-1"},
    ]
    s = mod.rr_summary(shadow, "result_2p5r")
    assert s["trades"] == 2
    assert s["wins"] == 1 and s["losses"] == 1
    assert abs(s["net_usd"] - 8.5) < 1e-9
    assert s["by_direction"]["LONG"]["wins"] == 1
    assert s["by_direction"]["SHORT"]["losses"] == 1


def test_launcher_is_portable_and_no_v31_venv_hardcode():
    text = LAUNCHER.read_text(encoding="utf-8")
    assert "py.exe" in text
    assert "python.exe" in text
    assert "runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv" not in text
    assert "RUN_V59_INTEGRATED_BIDIRECTIONAL_RR.py" in text


def test_adr_records_no_force_balance_and_tester_only_non_goal():
    text = ADR.read_text(encoding="utf-8")
    assert "Do not force direction balance" in text
    assert "Fixed lot remains 0.01" in text
    assert "Structural stop + cash feasibility" in text
    assert "not authorization for REAL-money activation" in text


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print(f"V59 integrated bidirectional RR static tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
