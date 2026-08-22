#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "runtime" / "v48_demo_paper" / "RUN_V48_DEMO_PAPER_START_HARDENED_V2.py"
START = ROOT / "runtime" / "v48_demo_paper" / "START_V48_DEMO_PAPER_GIT_BASH.sh"


def rt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_terminal_autotrading_is_requested_off_without_changing_mql_strategy():
    t = rt(V2)
    assert 'AllowLiveTrading=0' in t
    assert 'AllowDllImport=0' in t
    assert 'Enabled=0' in t
    assert 'V48_V2_TERMINAL_AUTOTRADING_REQUESTED_OFF=1' in t
    assert 'OrderSend(' not in t
    assert 'OrderSendAsync(' not in t
    assert 'CTrade' not in t


def test_reason8_failed_init_is_the_only_nonseed_auto_recovery_case():
    t = rt(V2)
    assert 'init.get("stage") == "STOPPED"' in t
    assert 'init.get("reason") == "8"' in t
    assert 'init.get("broker_orders") == "0"' in t
    assert 'init.get("live_authorized") == "0"' in t
    assert 'V48_FAILED_INIT_DEBRIS_QUARANTINED=' in t
    assert 'V48_FAILED_INIT_RECOVERY_ALLOWED=1' in t
    assert 'not a proven REASON_INITFAILED=8 artifact' in t


def test_fresh_session_must_reseed_exact_accepted_v46_state():
    t = rt(V2)
    assert 'EXPECTED_SEED_SHA = "36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3"' in t
    assert 'V48_FRESH_SESSION_SEED_PASS=1' in t
    assert 'V48 fresh-session state must equal accepted V46 seed before launch' in t


def test_failed_start_is_archived_and_state_rolled_back_when_no_run_id_exists():
    t = rt(V2)
    assert 'V48_FAILED_START_ARCHIVE=' in t
    assert 'V48_FAILED_START_STATE_ROLLBACK_PASS=1' in t
    assert 'V48_FAILED_START_ACCEPTED_SESSION_CREATED=0' in t
    assert 'V48_FAILED_START_ROLLBACK_SKIPPED_VALID_RUN_ID=1' in t


def test_start_entrypoint_routes_to_v2():
    t = rt(START)
    assert 'RUN_V48_DEMO_PAPER_START_HARDENED_V2.py' in t
    assert 'test_v48_demo_paper_hardened_v2_static.py' in t


def _run_without_pytest():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print(f"V48 hardened v2 static tests PASS count={len(tests)}")


if __name__ == "__main__":
    _run_without_pytest()
