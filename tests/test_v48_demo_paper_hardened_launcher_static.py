#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARD = ROOT / "runtime" / "v48_demo_paper" / "RUN_V48_DEMO_PAPER_START_HARDENED.py"
START = ROOT / "runtime" / "v48_demo_paper" / "START_V48_DEMO_PAPER_GIT_BASH.sh"


def rt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_root_alias_removes_nested_startup_resolution_dependency():
    t = rt(HARD)
    assert 'ALIAS_NAME = "V48DemoPaperObserver"' in t
    assert 'root = data / "MQL5" / "Experts"' in t
    assert 'alias_ex5 = root / f"{ALIAS_NAME}.ex5"' in t
    assert 'Expert=V48DemoPaperObserver' in t
    assert 'V48_STARTUP_ALIAS_PASS=1' in t


def test_startup_ini_is_self_verified_and_keeps_execution_locked():
    t = rt(HARD)
    for token in (
        'AllowLiveTrading=0',
        'AllowDllImport=0',
        'Enabled=1',
        'Symbol=XAUUSDm',
        'Period=M15',
        'V48_CONFIG_SELF_CHECK_PASS=1',
    ):
        assert token in t
    assert 'OrderSend(' not in t
    assert 'OrderSendAsync(' not in t
    assert 'CTrade' not in t


def test_incomplete_metadata_is_quarantined_but_ambiguous_state_fails_closed():
    t = rt(HARD)
    assert 'V48_INCOMPLETE_METADATA_QUARANTINED=' in t
    assert 'V48_ACTIVE_STATE_PRESERVED=1' in t
    assert 'existing V48 paper session has a non-empty run_id' in t
    assert 'orphan/non-seed V48 paper state found without a valid session run_id' in t
    assert 'EXPECTED_SEED_SHA = "36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3"' in t


def test_diagnostics_are_launch_scoped_not_historical_log_scrapes():
    t = rt(HARD)
    assert 'snapshot_logs' in t
    assert 'launch_log_delta' in t
    assert 'LAUNCH-SCOPED LOG DELTA' in t
    assert 'CONFIG_CONSUMED_EVIDENCE=' in t
    assert 'EXPERT_REFERENCE_EVIDENCE=' in t
    assert 'IGNORED_UNRELATED_MQL5_COMMUNITY_VPS_LINES=' in t
    assert 'PRE_ONINIT_OR_READY_TIMEOUT' in t


def test_market_closed_readiness_uses_file_refresh_not_tick_time():
    t = rt(HARD)
    assert 'before_mtime = paths["status"].stat().st_mtime_ns' in t
    assert 'paths["status"].stat().st_mtime_ns > before_mtime' in t
    assert 'STATUS_TIMER_REFRESH_PASS=1' in t
    assert 'market-close-safe heartbeat gate failed' in t


def test_git_bash_entrypoint_uses_hardened_launcher():
    t = rt(START)
    assert 'RUN_V48_DEMO_PAPER_START_HARDENED.py' in t
    assert 'test_v48_demo_paper_hardened_launcher_static.py' in t


def _run_without_pytest():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print(f"V48 hardened launcher static tests PASS count={len(tests)}")


if __name__ == "__main__":
    _run_without_pytest()
