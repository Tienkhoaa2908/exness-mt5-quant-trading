#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEGACY_DASHBOARD_TEST = REPO / "tests" / "test_v69_frozen_forward_demo_dashboard_static.py"
BUILDER = REPO / "scripts" / "build_v69_frozen_forward_demo_broker_ready_dashboard_source.py"
RUNNER = REPO / "runtime" / "v69_one_shot_prospective_demo" / "RUN_V69_ONE_SHOT_BROKER_READY_DEMO.py"
SUPERVISOR = REPO / "runtime" / "v69_one_shot_prospective_demo" / "SUPERVISE_V69_ONE_SHOT_PROSPECTIVE_DEMO.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_broker_dashboard_is_dry_run_only_and_strategy_frozen() -> None:
    mod = load(BUILDER, "v69_broker_dashboard_static")
    base = mod.parent.transform()
    text = mod.transform()
    assert mod.sha_bytes(mod.crlf_bytes(base)) == mod.PARENT_DASHBOARD_SHA256
    for token in (
        "V69DBrokerCapabilityRaw",
        "V69DRefreshBrokerCapability",
        "SYMBOL_VOLUME_MIN",
        "SYMBOL_VOLUME_MAX",
        "SYMBOL_VOLUME_STEP",
        "SYMBOL_TRADE_MODE",
        "SYMBOL_FILLING_MODE",
        "OrderCheck(req,chk)",
        "broker_ready=",
        "broker_detail=",
        "broker_ordercheck_retcode=",
        "BROKER: READY",
        "BROKER: BLOCKED",
        "lot_out_of_range",
        "lot_not_on_step",
    ):
        assert token in text, token
    for token in ("g_trade.Buy(", "g_trade.Sell(", "OrderSend(", "OrderSendAsync("):
        assert text.count(token) == base.count(token), token


def test_actual_trade_path_still_exists_after_broker_overlay() -> None:
    mod = load(BUILDER, "v69_broker_dashboard_trade_path")
    text = mod.transform()
    assert "InpV64FixedLot = 0.01" in text
    assert "V64OrderPreflight" in text
    assert "g_trade.SetTypeFillingBySymbol(_Symbol);" in text
    assert "g_trade.Buy(InpV64FixedLot,_Symbol,0.0,stop,tp" in text
    # One OrderCheck belongs to the frozen strategy preflight and one is the
    # new no-send broker capability check.
    assert text.count("OrderCheck(req,chk)") >= 2


def test_broker_dashboard_build_is_deterministic() -> None:
    mod = load(BUILDER, "v69_broker_dashboard_determinism")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        a = root / "a.mq5"
        b = root / "b.mq5"
        ha = mod.build(a)
        hb = mod.build(b)
        assert ha == hb
        assert a.read_bytes() == b.read_bytes()


def test_runner_has_no_redundant_generated_dashboard_hash_pin() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "broker dashboard deterministic build mismatch" in text
    assert "V69_BROKER_PREFLIGHT_READY=1" in text
    assert 'broker_ready = hb.get("broker_ready") == "1"' in text
    assert "BROKER PREFLIGHT BLOCKED before any strategy signal" in text
    assert "DASHBOARD_SOURCE_SHA256 =" not in text


def test_background_helpers_cannot_flash_console() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    supervisor = SUPERVISOR.read_text(encoding="utf-8")
    assert "CREATE_NO_WINDOW" in runner
    assert "CREATE_NO_WINDOW" in supervisor
    assert "hidden_subprocess_kwargs" in supervisor
    assert '"tasklist.exe"' in supervisor


def main() -> int:
    # Preserve every pre-existing dashboard isolation/compile-api regression test.
    legacy = load(LEGACY_DASHBOARD_TEST, "v69_legacy_dashboard_tests_from_broker_gate")
    legacy.main()

    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"V69 broker-ready one-shot static tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
