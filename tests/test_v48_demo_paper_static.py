#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_v48_demo_paper_observer_source.py"
RUN = ROOT / "runtime" / "v48_demo_paper" / "RUN_V48_DEMO_PAPER_START.py"
STATUS = ROOT / "runtime" / "v48_demo_paper" / "STATUS_V48_DEMO_PAPER.py"
PLAN = ROOT / "docs" / "research" / "v48_demo_paper_forward_plan.md"


def rt(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_frozen_parent_and_output_identity():
    t = rt(BUILD) + "\n" + rt(RUN)
    assert 'EXPECTED_PARENT_SHA = "7685dd83f576841532970d43e21fda80c896c407f313edae1fb12b0b39387e44"' in t
    assert 'EXPECTED_OUTPUT_SHA = "ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa"' in t
    assert 'V48_SOURCE_SHA = "ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa"' in t


def test_demo_only_and_real_account_refusal_are_hard_gates():
    t = rt(BUILD)
    assert 'ACCOUNT_TRADE_MODE_DEMO' in t
    assert 'DEMO ACCOUNT REQUIRED' in t
    assert 'real_account_forbidden=1' in t
    assert 'demo_paper_only=1' in t
    assert 'v48_live_authorized=0' in t


def test_terminal_trade_and_dll_permissions_are_hard_off():
    t = rt(BUILD) + "\n" + rt(RUN)
    assert 'TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)' in t
    assert 'TerminalInfoInteger(TERMINAL_DLLS_ALLOWED)' in t
    assert 'AllowLiveTrading=0' in t
    assert 'AllowDllImport=0' in t
    assert 'Enabled=1' in t
    assert '"terminal_trade_allowed": "0"' in t
    assert '"terminal_dlls_allowed": "0"' in t
    # Per-program flags are diagnostic only. Global terminal locks plus source-level
    # absence of broker/DLL paths are the effective safety barriers.
    assert 'MQL_TRADE_ALLOWED={kv.get' in t
    assert 'MQL_DLLS_ALLOWED={kv.get' in t


def test_no_broker_or_dll_execution_route_can_be_introduced():
    t = rt(BUILD)
    assert 'FORBIDDEN = ("OrderSend(", "OrderSendAsync(", "CTrade", "trade.Buy(", "trade.Sell(", "#import")' in t
    assert 'for bad in FORBIDDEN:' in t
    assert 'forbidden native/external execution path in parent' in t
    assert 'forbidden native/external execution path introduced' in t
    assert 'v48_broker_orders=0' in t


def test_paper_state_and_latest_are_isolated():
    t = rt(BUILD) + "\n" + rt(RUN)
    assert 'v48_demo_paper_state.csv' in t
    assert 'mt5_quant' in t and 'paper' in t
    assert 'V48_DEMO_PAPER_LATEST.txt' in t
    assert 'V48_DEMO_PAPER_STATUS.txt' in t
    assert 'V48_DEMO_PAPER_INIT.txt' in t
    assert 'accepted_v46_state_not_modified=1' in t
    assert 'historical_midmonth_catchup=0' in t


def test_deinit_does_not_fake_month_end_close():
    t = rt(BUILD)
    assert 'V48 OnDeinit must not fabricate an EOM close' in t
    assert 'EventKillTimer();' in t
    assert 'SaveAdaptiveState(); WritePaperStatus(); WriteManifest(); WriteLatest();' in t
    assert 'Comment("");' in t


def test_live_observer_uses_startup_config_not_tester():
    t = rt(RUN)
    assert '[StartUp]' in t
    assert 'Expert=mt5_quant\\\\V48DemoPaperObserver' in t
    assert 'Symbol=XAUUSDm' in t
    assert 'Period=M15' in t
    assert '[Tester]' not in t


def test_chart_dashboard_is_realtime_and_visible():
    t = rt(BUILD)
    for token in ('UpdatePaperDashboard', 'Comment(x)', 'Balance: $', 'Equity: $', 'Breadth: ', 'Position: ', 'Heartbeat: ', 'REAL MONEY AUTHORIZED: NO'):
        assert token in t
    # The builder validates generated-MQL control flow after transformation. This is
    # intentionally whitespace/escape agnostic so formatting changes cannot create
    # another false static failure.
    assert 'V48 generated OnTick dashboard control flow invalid' in t
    assert 'V48 generated OnTimer dashboard control flow invalid' in t
    assert 'V48 generated OnInit dashboard control flow invalid' in t
    assert 'ProcessExits(tick);' in t
    assert 'g_prev_tick=tick' in t
    assert 'void OnTimer()' in t
    assert t.count('UpdatePaperDashboard();') >= 3


def test_attach_failure_becomes_diagnostic_not_blind_timeout():
    t = rt(RUN) + "\n" + rt(STATUS)
    assert 'V48_DEMO_PAPER_INIT.txt' in t
    assert 'collect_attach_diagnostics' in t
    assert 'EA_REFUSED_DURING_ONINIT' in t
    assert 'TIMEOUT_WAITING_FOR_V48_READY' in t
    assert 'v48_mt5_attach_diagnostics.txt' in t


def test_campaign_is_finite_not_open_ended():
    t = rt(PLAN)
    assert 'at least 10 XAUUSD trading days' in t
    assert 'at least 20 primary breadth4 paper trades have closed' in t
    assert 'Hard maximum observation horizon: 30 calendar days' in t
    assert 'Do not automatically extend the campaign.' in t
    assert 'PAPER_OPERATIONAL_PASS' in t
    assert 'Real-money order execution remains outside the authorized scope' in t


def _run_without_pytest():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn(); print("PASS", fn.__name__)
    print(f"V48 static tests PASS count={len(tests)}")


if __name__ == "__main__":
    _run_without_pytest()
