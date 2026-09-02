#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
ANALYZER = REPO / "scripts" / "analyze_v69_cycle_economics_rearm.py"
RUNTIME = REPO / "runtime" / "v69_cycle_economics_recovery" / "RUN_V69_CYCLE_ECONOMICS_RECOVERY.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


a = load(ANALYZER, "v69_cycle_economics_test_target")


def event(time: str, name: str, detail: str = "", v1: str = "0", v2: str = "0", v3: str = "0") -> dict[str, str]:
    return {"time": time, "event": name, "direction": "1", "detail": detail, "v1": v1, "v2": v2, "v3": v3}


def test_terminal_family_classification_is_fail_closed() -> None:
    assert a.classify_terminal("PENDING_END:invalidated_before_entry", False) == "HARD_STRUCTURAL"
    assert a.classify_terminal("MICRO_ENTRY_END:micro_structural_stop_breached", False) == "HARD_STRUCTURAL"
    assert a.classify_terminal("MICRO_ENTRY_END:expired_first_micro_arm_ttl", False) == "TTL_EXPIRY"
    assert a.classify_terminal("PENDING_END:weak_trend_chop", False) == "CONTEXT_QUALITY"
    assert a.classify_terminal("", False) == "UNTERMINATED"
    assert a.classify_terminal("MICRO_ENTRY_END:order_sent_after_reclaim", True) == "SENT_ORDER"


def test_cycle_pairing_preserves_archetype_and_realized_pnl() -> None:
    events = [
        event("2025.10.01 10:00:00", "PENDING_ARM", "BREAKOUT_RETEST_BOS", "100", "99"),
        event("2025.10.01 10:10:00", "REFINED_ENTRY", "sent", "100.2", "1", "0.1"),
        event("2025.10.01 10:10:01", "MICRO_ENTRY_END", "order_sent_after_reclaim", "99.5", "10", "1"),
    ]
    cycles = a.build_cycles(events)
    deals = [{"time": a.parse_time("2025.10.01 10:25:00"), "pnl": 2.5}]
    a.pair_sent_cycles_with_deals(cycles, deals)
    assert len(cycles) == 1
    assert cycles[0]["archetype"] == "BREAKOUT_RETEST_BOS"
    assert cycles[0]["terminal_family"] == "SENT_ORDER"
    assert cycles[0]["pnl"] == 2.5
    econ = a.summarize_economics(cycles)
    assert econ["sent"] == 1 and econ["wins"] == 1 and econ["net_usd"] == 2.5


def test_rearm_reports_archetype_level_only_not_setup_identity() -> None:
    events = [
        event("2025.10.01 10:00:00", "PENDING_ARM", "PULLBACK_SWEEP_BOS"),
        event("2025.10.01 10:05:00", "PENDING_END", "expired_first_arm_ttl"),
        event("2025.10.01 10:20:00", "PENDING_ARM", "PULLBACK_SWEEP_BOS"),
        event("2025.10.01 10:25:00", "REFINED_ENTRY", "sent"),
        event("2025.10.01 10:25:01", "MICRO_ENTRY_END", "order_sent_after_reclaim"),
    ]
    cycles = a.build_cycles(events)
    a.pair_sent_cycles_with_deals(cycles, [{"time": a.parse_time("2025.10.01 10:35:00"), "pnl": -1.0}])
    result = a.rearm_summary(cycles)
    ttl = result["by_terminal_family"]["TTL_EXPIRY"]
    assert ttl["eligible_rejected"] == 1
    assert ttl["same_archetype_next"] == 1
    assert ttl["rearm_within_15m"] == 1
    assert ttl["next_cycle_sent"] == 1
    assert ttl["next_cycle_losses"] == 1
    assert result["same_archetype_is_not_setup_identity"] is True


def test_trade_transition_counts_loss_after_win() -> None:
    cycles = [
        {"sent": True, "pnl": 3.0, "sent_at": a.parse_time("2025.10.01 10:00:00")},
        {"sent": True, "pnl": -1.0, "sent_at": a.parse_time("2025.10.01 11:00:00")},
        {"sent": True, "pnl": -0.5, "sent_at": a.parse_time("2025.10.01 12:00:00")},
        {"sent": True, "pnl": 2.0, "sent_at": a.parse_time("2025.10.01 13:00:00")},
    ]
    result = a.trade_transition_summary(cycles)
    assert result["counts"] == {"L->L": 1, "L->W": 1, "W->L": 1}
    assert result["destination_trade_net_usd"]["W->L"] == -1.0


def test_runtime_contract_is_read_only_and_development_only() -> None:
    if not RUNTIME.is_file():
        return
    text = RUNTIME.read_text(encoding="utf-8")
    for token in (
        "V69_CYCLE_ECONOMICS_MT5_CAN_REMAIN_RUNNING=1",
        "V69_CYCLE_ECONOMICS_METAEDITOR_REQUIRED=0",
        "V69_CYCLE_ECONOMICS_ORDERS_SENT=0",
        "V69_CYCLE_ECONOMICS_STRATEGY_CHANGED=0",
        "V69_CYCLE_ECONOMICS_INDEPENDENT_EDGE_EVIDENCE=0",
        "V69_CYCLE_ECONOMICS_COUNTERFACTUAL_REJECT_EDGE_PROVEN=0",
    ):
        assert token in text
    forbidden = ("terminal64.exe", "metaeditor64.exe", "OrderSend(", ".Buy(", ".Sell(", "MetaTrader5")
    for token in forbidden:
        assert token not in text


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"V69 cycle economics/rearm tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
