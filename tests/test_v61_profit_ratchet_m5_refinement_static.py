from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILDER = REPO / "scripts" / "build_v61_profit_ratchet_m5_refinement_source.py"
SCREEN_BUILDER = REPO / "scripts" / "build_v61_profit_ratchet_m5_refinement_screen_source.py"
ANALYZER = REPO / "scripts" / "analyze_v61_profit_ratchet_m5_refinement.py"
RUNNER = REPO / "runtime" / "v61_profit_ratchet_m5_refinement" / "RUN_V61_PROFIT_RATCHET_M5_REFINEMENT.py"
LAUNCHER = REPO / "runtime" / "v61_profit_ratchet_m5_refinement" / "START_V61_PROFIT_RATCHET_M5_REFINEMENT_GIT_BASH.sh"
ADR = REPO / "docs" / "adr" / "ADR-063-v61-profit-ratchet-m5-refinement-research.md"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def generated() -> str:
    mod = load(BUILDER, "v61_builder_static")
    text = mod.transform()
    mod.validate(text)
    return text


def test_v61_cash_contract_and_profit_ratchet():
    text = generated()
    for token in (
        "InpV61FixedLot = 0.01",
        "InpV61PrimaryTargetCash = 3.00",
        "InpV61ProfitArmCash = 2.00",
        "InpV61ProfitLockCash = 1.00",
        "InpV61MinStopRiskCash = 0.75",
        "InpV61MaxStopRiskCash = 1.25",
        "V61ManageProfitRatchet",
        "PositionModify(ticket,lock_price,tp)",
        "PROFIT_LOCK",
    ):
        assert token in text, token


def test_v61_m5_refinement_is_causal_and_structural():
    text = generated()
    for token in (
        "CopyRates(_Symbol,PERIOD_M5,1,180,m5)",
        "V61M5RefinedStop",
        "V61ConfirmedSwings(m5",
        "g_v61_stop_source=\"m5\"",
        "structural_risk_too_tight",
    ):
        assert token in text, token
    assert "CopyRates(_Symbol,PERIOD_M5,0," not in text


def test_v61_preserves_strict_h4_h1_and_symmetric_long_short():
    text = generated()
    for token in (
        "f.h1_trend==1 && f.h4_trend==1",
        "f.h1_trend==-1 && f.h4_trend==-1",
        "V61ScoreDirection(1,f)",
        "V61ScoreDirection(-1,f)",
        "g_trade.Buy",
        "g_trade.Sell",
    ):
        assert token in text, token


def test_v61_ordercheck_preflight_quarantines_invalid_stops():
    text = generated()
    for token in (
        "V61OrderPreflight",
        "OrderCheck(req,chk)",
        "ORDER_PREFLIGHT",
        "g_trade.SetTypeFillingBySymbol(_Symbol)",
    ):
        assert token in text, token


def test_v61_screen_builder_sets_screen_mode():
    mod = load(SCREEN_BUILDER, "v61_screen_static")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "screen.mq5"
        mod.build(p)
        text = p.read_text(encoding="utf-8")
    assert "InpV61ScreenOnly = true" in text
    assert "InpV61PrimaryTargetCash = 3.00" in text


def test_v61_analyzer_counts_exit_round_trips_and_lock_events():
    mod = load(ANALYZER, "v61_analyzer_static")
    deals = [
        {"entry":"0","profit":"0","commission":"0","swap":"0","fee":"0","reason":"3"},
        {"entry":"1","profit":"3.0","commission":"0","swap":"0","fee":"0","reason":"5"},
        {"entry":"0","profit":"0","commission":"0","swap":"0","fee":"0","reason":"3"},
        {"entry":"1","profit":"1.0","commission":"0","swap":"0","fee":"0","reason":"4"},
    ]
    events = [{"event":"PROFIT_LOCK","detail":"modified"}]
    s = mod.actual_summary(deals, events)
    assert s["round_trips"] == 2
    assert s["wins"] == 2
    assert s["profit_lock_modified"] == 1
    assert abs(s["net_usd"] - 4.0) < 1e-9


def test_v61_runner_and_launcher_are_branch_pinned_and_portable():
    runner = RUNNER.read_text(encoding="utf-8")
    launcher = LAUNCHER.read_text(encoding="utf-8")
    assert 'agent/v61-profit-ratchet-m5-refinement-research' in runner
    assert "V61_SELECTED_WINDOWS.json" in runner
    assert "two_most_recent_feasible_strict_h4_h1_v61_weeks_not_pnl" in runner
    assert "py.exe" in launcher and "python.exe" in launcher
    assert "RUN_V61_PROFIT_RATCHET_M5_REFINEMENT.py" in launcher
    assert 'risk band $0.75-$1.25' in launcher
    assert 'arm at +$2 -> lock +$1' in launcher


def test_v61_adr_records_evidence_driven_non_real_scope():
    text = ADR.read_text(encoding="utf-8")
    for token in (
        "V60 evidence",
        "profit ratchet",
        "M5",
        "0.75",
        "1.25",
        "not authorization for REAL-money activation",
    ):
        assert token in text, token


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print(f"V61 static tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
