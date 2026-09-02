#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYZER = ROOT / "scripts" / "analyze_v69_mfe_giveback_recovery.py"
RUNNER = ROOT / "runtime" / "v69_mfe_giveback_recovery" / "RUN_V69_MFE_GIVEBACK_RECOVERY.py"
LAUNCHER = ROOT / "runtime" / "v69_mfe_giveback_recovery" / "RUN_V69_MFE_GIVEBACK_RECOVERY_GIT_BASH.sh"


def load():
    spec = importlib.util.spec_from_file_location("v69_mfe_giveback_test", ANALYZER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fixture(root: Path, *, second_mfe: float = 0.8, second_lock: bool = False) -> None:
    deals = [
        {"time": "2025.09.01 10:00:00", "entry": 0, "profit": 0, "commission": 0, "swap": 0, "fee": 0, "reason": 0, "price": 3500.0},
        {"time": "2025.09.01 10:05:00", "entry": 1, "profit": 1.5, "commission": 0, "swap": 0, "fee": 0, "reason": 4, "price": 3501.5},
        {"time": "2025.09.01 11:00:00", "entry": 0, "profit": 0, "commission": 0, "swap": 0, "fee": 0, "reason": 0, "price": 3502.0},
        {"time": "2025.09.01 11:01:00", "entry": 1, "profit": -1.0, "commission": 0, "swap": 0, "fee": 0, "reason": 4, "price": 3501.0},
    ]
    write_csv(root / "V64_DEALS.csv", ["time", "entry", "profit", "commission", "swap", "fee", "reason", "price"], deals)

    noise = [
        {"id": 1, "started": "2025.09.01 10:00:00", "ended": "2025.09.01 10:05:00", "dir": 1, "entry": 3500.0, "max_pnl": 3.0, "min_pnl": -0.2, "reason": "closed"},
        {"id": 2, "started": "2025.09.01 11:00:00", "ended": "2025.09.01 11:01:00", "dir": 1, "entry": 3502.0, "max_pnl": second_mfe, "min_pnl": -1.0, "reason": "closed"},
    ]
    write_csv(root / "V64_NOISE_SHADOW.csv", ["id", "started", "ended", "dir", "entry", "max_pnl", "min_pnl", "reason"], noise)

    events = [
        {"time": "2025.09.01 09:59:00", "event": "PENDING_ARM", "dir": 1, "detail": "BREAKOUT_RETEST_BOS", "v1": 3500, "v2": 3499, "v3": 0},
        {"time": "2025.09.01 10:00:00", "event": "REFINED_ENTRY", "dir": 1, "detail": "sent", "v1": 0, "v2": 0, "v3": 0},
        {"time": "2025.09.01 10:02:00", "event": "PROFIT_LOCK", "dir": 1, "detail": "modified", "v1": 2.2, "v2": 3501, "v3": 3503.5},
        {"time": "2025.09.01 10:02:01", "event": "MICRO_ENTRY_END", "dir": 1, "detail": "order_sent_after_reclaim", "v1": 0, "v2": 0, "v3": 0},
        {"time": "2025.09.01 10:59:00", "event": "PENDING_ARM", "dir": 1, "detail": "PULLBACK_SWEEP_BOS", "v1": 3502, "v2": 3501, "v3": 0},
        {"time": "2025.09.01 11:00:00", "event": "REFINED_ENTRY", "dir": 1, "detail": "sent", "v1": 0, "v2": 0, "v3": 0},
        {"time": "2025.09.01 11:00:20", "event": "MICRO_ENTRY_END", "dir": 1, "detail": "order_sent_after_reclaim", "v1": 0, "v2": 0, "v3": 0},
    ]
    if second_lock:
        events.insert(
            -1,
            {"time": "2025.09.01 11:00:30", "event": "PROFIT_LOCK", "dir": 1, "detail": "modified", "v1": 2.1, "v2": 3503, "v3": 3505.5},
        )
    write_csv(root / "V64_EVENTS.csv", ["time", "event", "dir", "detail", "v1", "v2", "v3"], events)


def test_analyze_run_pairs_mfe_archetype_and_profit_lock() -> None:
    m = load()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        fixture(root)
        result = m.analyze_run(root)
    assert len(result["trades"]) == 2
    assert result["trades"][0]["archetype"] == "BREAKOUT_RETEST_BOS"
    assert result["trades"][1]["archetype"] == "PULLBACK_SWEEP_BOS"
    assert result["trades"][0]["mfe_usd"] == 3.0
    assert result["trades"][0]["profit_lock_modified_count"] == 1


def test_group_summary_separates_sub2_roundtrip_from_ratchet_eligible() -> None:
    m = load()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        fixture(root)
        trades = m.analyze_run(root)["trades"]
    summary = m.group_summary(trades)
    assert summary["noise_matched_trades"] == 2
    assert summary["positive_mfe_realized_loss_count"] == 1
    assert summary["sub2_peak_roundtrip_loss_count"] == 1
    assert summary["ratchet_eligible_mfe_ge_2_count"] == 1
    assert summary["mfe_ge_2_realized_below_1_count"] == 0
    assert summary["profit_lock_modified_trades"] == 1


def test_ratchet_audit_flags_mfe_ge2_loss_with_lock_event() -> None:
    m = load()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        fixture(root, second_mfe=2.4, second_lock=True)
        trades = m.analyze_run(root)["trades"]
    summary = m.group_summary(trades)
    assert summary["mfe_ge_2_realized_below_1_count"] == 1
    assert summary["mfe_ge_2_realized_below_1_with_profit_lock_event"] == 1


def test_runtime_contract_is_read_only_and_does_not_simulate_trailing() -> None:
    analyzer = ANALYZER.read_text(encoding="utf-8")
    runner = RUNNER.read_text(encoding="utf-8")
    launcher = LAUNCHER.read_text(encoding="utf-8") if LAUNCHER.exists() else ""
    combined = analyzer + "\n" + runner + "\n" + launcher
    assert "V69_MFE_GIVEBACK_MT5_CAN_REMAIN_RUNNING=1" in runner
    assert "V69_MFE_GIVEBACK_ORDERS_SENT=0" in runner
    assert "V69_MFE_GIVEBACK_STRATEGY_CHANGED=0" in runner
    assert "V69_MFE_GIVEBACK_TRAILING_COUNTERFACTUAL_SIMULATED=0" in runner
    assert "OrderSend(" not in combined
    assert ".Buy(" not in combined
    assert ".Sell(" not in combined
    assert "terminal64.exe" not in combined.lower()
    assert "metaeditor64.exe" not in combined.lower()


def main() -> int:
    tests = [obj for name, obj in sorted(globals().items()) if name.startswith("test_") and callable(obj)]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V69 MFE/giveback recovery tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
