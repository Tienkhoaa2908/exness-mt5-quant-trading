#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_v49_one_shot_demo_rehearsal_source.py"
RUNNER = ROOT / "runtime" / "v49_demo_rehearsal" / "RUN_V49_ONE_SHOT.py"
SUPERVISOR = ROOT / "runtime" / "v49_demo_rehearsal" / "SUPERVISE_V49_ONE_SHOT.py"
START = ROOT / "runtime" / "v49_demo_rehearsal" / "START_V49_ONE_SHOT_GIT_BASH.sh"
ADR = ROOT / "docs" / "adr" / "ADR-048-v49-one-shot-production-rehearsal.md"


def rt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_v49_inherits_frozen_parent_instead_of_reoptimizing():
    t = rt(BUILDER)
    assert 'EXPECTED_PARENT_SHA = "ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa"' in t
    assert 'v46_hl10_thr0p05_breadth4' in t
    assert 'InpV49Magic = 490049' in t


def test_native_execution_is_demo_only_and_real_money_remains_forbidden():
    t = rt(BUILDER)
    assert '#include <Trade/Trade.mqh>' in t
    assert 'CTrade g_v49_trade' in t
    assert 'ACCOUNT_TRADE_MODE_DEMO' in t
    assert 'V49InitExecution' in t
    assert 'real_money_authorized=0' in t
    assert 'g_v49_trade.Buy' in t
    assert 'g_v49_trade.Sell' in t
    assert 'PositionClose' in t
    assert 'real_money_authorized=1' not in t


def test_execution_reconciliation_uses_trade_transactions_and_magic_ownership():
    t = rt(BUILDER)
    assert 'OnTradeTransaction' in t
    assert 'DEAL_MAGIC' in t
    assert 'POSITION_MAGIC' in t
    assert 'duplicate_owned_positions' in t
    assert 'virtual_broker_direction_mismatch' in t
    assert 'V49OwnedPositionCount' in t


def test_notifications_cover_start_open_close_halt_final_without_repo_secret():
    t = rt(BUILDER)
    assert 'SendNotification' in t
    for token in ('V49 START', 'V49 DEMO OPEN confirmed', 'V49 DEMO CLOSE confirmed', 'V49 HALT', 'V49 FINAL'):
        assert token in t
    assert 'MetaQuotes ID' not in t
    assert 'password=' not in t.lower()


def test_one_shot_campaign_has_small_execution_sample_and_finite_stop():
    t = rt(BUILDER)
    assert 'InpV49MinMarketDays = 3' in t
    assert 'InpV49MinRoundTrips = 3' in t
    assert 'InpV49HardCalendarDays = 14' in t
    assert 'LIVE_CANDIDATE_READY' in t
    assert 'INSUFFICIENT_EXECUTION_SAMPLE' in t


def test_runner_requires_flat_transition_and_launches_detached_supervisor():
    t = rt(RUNNER)
    assert 'position_open' in t
    assert 'V48 virtual position is OPEN' in t
    assert 'AllowLiveTrading=1' in t
    assert 'AllowDllImport=0' in t
    assert 'V49_DEMO_REHEARSAL_READY=1' in t
    assert 'start_supervisor()' in t
    assert 'REAL_MONEY_AUTHORIZED=0' in t


def test_supervisor_packages_exactly_one_final_bundle_with_sha_manifest():
    t = rt(SUPERVISOR)
    assert 'bundle_manifest_sha256.txt' in t
    assert 'V49_ONE_SHOT_DEMO_REHEARSAL_' in t
    assert 'testzip()' in t
    assert 'LATEST_V49_ZIP.txt' in t
    assert 'EA_FINAL_' in t


def test_entrypoint_really_is_single_user_task():
    t = rt(START)
    assert 'RUN_V49_ONE_SHOT.py' in t
    assert 'SUPERVISE_V49_ONE_SHOT.py' in t
    assert 'test_v49_one_shot_demo_rehearsal_static.py' in t
    assert 'Git Bash may be closed after START PASS' in t


def test_adr_explicitly_collapses_old_gate_ladder():
    t = rt(ADR)
    assert 'one-shot production rehearsal' in t
    assert 'Historical/alpha evidence is inherited' in t
    assert '>=3 actual XAUUSD market-active dates' in t
    assert '>=3 completed native broker-DEMO round trips' in t
    assert '14 calendar days' in t


def _run_without_pytest():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print(f"V49 one-shot static tests PASS count={len(tests)}")


if __name__ == "__main__":
    _run_without_pytest()
