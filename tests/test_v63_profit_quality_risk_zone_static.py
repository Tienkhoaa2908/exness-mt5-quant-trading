from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILDER = REPO / "scripts" / "build_v63_profit_quality_risk_zone_source.py"
SCREEN_BUILDER = REPO / "scripts" / "build_v63_profit_quality_risk_zone_screen_source.py"
ANALYZER = REPO / "scripts" / "analyze_v63_profit_quality_risk_zone.py"
RUNNER = REPO / "runtime" / "v63_profit_quality_risk_zone" / "RUN_V63_PROFIT_QUALITY_RISK_ZONE.py"
LAUNCHER = REPO / "runtime" / "v63_profit_quality_risk_zone" / "START_V63_PROFIT_QUALITY_RISK_ZONE_GIT_BASH.sh"
ADR = REPO / "docs" / "adr" / "ADR-065-v63-profit-quality-risk-zone-research.md"
HANDOFF = REPO / "docs" / "handoff" / "V63_RECOVERY_STATE.md"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_v63_builder_profit_loss_contract_and_direction_isolation():
    mod = load(BUILDER, "v63_builder_contract")
    long_src = mod.transform(1)
    short_src = mod.transform(-1)
    for text in (long_src, short_src):
        for token in (
            "InpV63FixedLot = 0.01",
            "InpV63PrimaryTargetCash = 3.50",
            "InpV63ProfitArmCash = 2.00",
            "InpV63ProfitLockCash = 1.00",
            "InpV63MinStopRiskCash = 0.60",
            "InpV63MaxStopRiskCash = 1.05",
            "InpV63EmergencyLossCash = 1.10",
            "HARD_CASH_LOSS",
            "V63OrderPreflight",
            "V63 RISKZONE L",
            "V63 RISKZONE S",
        ):
            assert token in text, token
    assert "InpV63AllowedDirection = 1" in long_src
    assert "InpV63AllowedDirection = -1" in short_src


def test_v63_first_arm_ttl_cannot_be_refreshed():
    mod = load(BUILDER, "v63_builder_ttl")
    text = mod.transform(1)
    start = text.index("void V63ArmPending")
    end = text.index("void V63ManagePendingEntry", start)
    body = text[start:end]
    assert body.count("g_v63_pending_armed=TimeCurrent()") == 1
    assert body.index("if(g_v63_pending)") < body.index("g_v63_pending_armed=TimeCurrent()")
    assert "first_arm_ttl_preserved" in body
    assert "expired_first_arm_ttl" in text


def test_v63_entry_revalidates_regime_and_waits_for_structural_risk_zone():
    mod = load(BUILDER, "v63_builder_entry")
    text = mod.transform(1)
    start = text.index("void V63ManagePendingEntry")
    end = text.index("void V63EvaluateBar", start)
    body = text[start:end]
    for token in (
        "V63BuildFeatures(cur)",
        "V63SelectDirection(cur,current_why)",
        "V63EntryQualityPass(d,cur,quality)",
        "momentum_double_opposed",
        "weak_trend_chop",
        "V63BuildStopTarget(d,cur,entry",
        "RISK_ZONE_WAIT",
        'g_v63_stop_source!="m5"',
        "V63M1TurnConfirmed(d,m1detail)",
    ):
        assert token in text or token in body, token
    assert "V63MicroEntryReady" not in text


def test_v63_screen_is_directional_only_and_pnl_free():
    mod = load(SCREEN_BUILDER, "v63_screen_builder")
    text = mod.transform()
    assert "V63_DIRECTIONAL_SCREEN_ONLY" in text
    start = text.index("void V63EvaluateBar()")
    end = text.index("int OnInit()", start)
    body = text[start:end]
    assert "V63SelectDirection(f,why)" in body
    for forbidden in ("V63BuildStopTarget(", "g_trade.Buy(", "g_trade.Sell(", "V63StartShadow("):
        assert forbidden not in body


def test_v63_runner_keeps_four_week_benchmark_and_adds_pnl_independent_bearish_short_validation():
    text = RUNNER.read_text(encoding="utf-8")
    for token in (
        'EXPECTED_BRANCH = "agent/v63-profit-quality-risk-zone-research"',
        'SCREEN_MODEL = 2',
        'REAL_MODEL = 4',
        '("week1", "2026.08.03", "2026.08.08")',
        '("week2", "2026.08.10", "2026.08.15")',
        '("week3", "2026.08.17", "2026.08.22")',
        '("week4", "2026.08.24", "2026.08.29")',
        'MIN_BEARISH_SHORT_SIGNALS = 8',
        'MIN_BEARISH_SHORT_SHARE = 0.60',
        'BEARISH_WEEK_COUNT = 4',
        '"selection_uses_pnl": False',
        'V63_BEARISH_WINDOWS=',
        'prefix = "V63_SCREEN_PASS" if model == SCREEN_MODEL else "V63_REAL_TICK_PASS"',
        'print(f"{prefix}_START label={label} config={ini}")',
        'print(f"{prefix}_DONE label={label}")',
    ):
        assert token in text, token
    selector = text[text.index("def select_bearish_weeks"):text.index("def analyze", text.index("def select_bearish_weeks"))]
    assert "result_cash" not in selector


def test_v63_analyzer_round_trips_and_weekly_profit_goal_are_reporting_only():
    mod = load(ANALYZER, "v63_analyzer")
    deals = [
        {"entry": "0", "profit": "0", "commission": "0", "swap": "0", "fee": "0", "reason": "0"},
        {"entry": "1", "profit": "3.50", "commission": "0", "swap": "0", "fee": "0", "reason": "4"},
        {"entry": "0", "profit": "0", "commission": "0", "swap": "0", "fee": "0", "reason": "0"},
        {"entry": "1", "profit": "-1.00", "commission": "0", "swap": "0", "fee": "0", "reason": "5"},
    ]
    result = mod.actual_summary(deals)
    assert result["trades"] == 2
    assert result["wins"] == 1
    assert result["losses"] == 1
    assert abs(result["net_usd"] - 2.50) < 1e-9
    assert mod.WEEKLY_TRADE_GOAL == 3
    assert mod.WEEKLY_PROFIT_GOAL_USD == 6.0


def test_v63_launcher_portable_and_branch_pinned():
    text = LAUNCHER.read_text(encoding="utf-8")
    assert 'EXPECTED_BRANCH="agent/v63-profit-quality-risk-zone-research"' in text
    assert "set -Eeuo pipefail" in text
    assert "py.exe" in text
    assert "python.exe" in text
    assert "RUN_V63_PROFIT_QUALITY_RISK_ZONE.py" in text


def test_v63_adr_and_handoff_freeze_profit_objective_without_guarantee_or_real_scope():
    adr = ADR.read_text(encoding="utf-8")
    handoff = HANDOFF.read_text(encoding="utf-8")
    for text in (adr, handoff):
        assert "$0.60-$1.05" in text
        assert "$3.50" in text
        assert "SHORT" in text
        assert "REAL" in text
        assert "not a promised" in text or "not a promised weekly return" in text
    assert "first M15 arm" in adr
    assert "12" in handoff


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print(f"V63 static tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
