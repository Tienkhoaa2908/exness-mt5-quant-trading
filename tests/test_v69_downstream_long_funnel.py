#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ANALYZER = REPO / "scripts" / "analyze_v69_downstream_long_funnel.py"
RUNNER = REPO / "runtime" / "v69_downstream_funnel_recovery" / "RUN_V69_DOWNSTREAM_FUNNEL_RECOVERY.py"
LAUNCHER = REPO / "runtime" / "v69_downstream_funnel_recovery" / "RUN_V69_DOWNSTREAM_FUNNEL_RECOVERY_GIT_BASH.sh"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = load(ANALYZER, "v69_downstream_test")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_selector_streaks_are_context_not_setup_count() -> None:
    rows = [
        {"time": "2025.09.01 00:00:00", "selected_direction": "1"},
        {"time": "2025.09.01 00:15:00", "selected_direction": "1"},
        {"time": "2025.09.01 00:30:00", "selected_direction": "0"},
        {"time": "2025.09.01 00:45:00", "selected_direction": "1"},
        {"time": "2026.06.01 00:00:00", "selected_direction": "1"},
    ]
    out = mod.selector_context(rows)
    assert out["long_selected_rows"] == 3
    assert out["long_selector_streaks"] == 2
    assert out["by_month"]["2025-09"] == 3


def test_initial_eval_separates_pre_pending_rejects() -> None:
    rows = [
        {"decision_reason": "long_edge", "selected_direction": "1", "reject_reason": "no_complete_archetype"},
        {"decision_reason": "long_edge", "selected_direction": "1", "reject_reason": "invalid_arm_structural_stop"},
        {"decision_reason": "long_edge", "selected_direction": "1", "reject_reason": "pending_bos"},
        {"decision_reason": "post_zone_reclaim_entry", "selected_direction": "1", "reject_reason": ""},
        {"decision_reason": "short_edge", "selected_direction": "-1", "reject_reason": "direction_isolated_out"},
    ]
    out = mod.initial_eval_context(rows)
    assert out["rows"] == 3
    assert out["pending_eval_rows"] == 1
    assert out["pre_pending_reject_rows"] == 2


def test_cycle_progression_localizes_drop() -> None:
    rows = [
        {"time": "2025.09.01 00:00:00", "event": "PENDING_ARM", "detail": "bos"},
        {"time": "2025.09.01 00:01:00", "event": "MICRO_ENTRY_ARM", "detail": "bos"},
        {"time": "2025.09.01 00:02:00", "event": "MICRO_ENTRY_ZONE_TOUCH", "detail": "bos"},
        {"time": "2025.09.01 00:03:00", "event": "MICRO_ENTRY_PENETRATION", "detail": "bos"},
        {"time": "2025.09.01 00:04:00", "event": "POST_ZONE_REVERSAL_CONFIRM", "detail": "ok"},
        {"time": "2025.09.01 00:05:00", "event": "POST_CONFIRM_SEPARATION", "detail": "bos"},
        {"time": "2025.09.01 00:06:00", "event": "POST_CONFIRM_RETEST_READY", "detail": "bos"},
        {"time": "2025.09.01 00:07:00", "event": "POST_CONFIRM_ENTRY_READY", "detail": "bos"},
        {"time": "2025.09.01 00:08:00", "event": "REFINED_ENTRY", "detail": "sent"},
        {"time": "2025.09.02 00:00:00", "event": "PENDING_ARM", "detail": "bos"},
        {"time": "2025.09.02 00:01:00", "event": "MICRO_ENTRY_ARM", "detail": "bos"},
        {"time": "2025.09.02 00:02:00", "event": "MICRO_ENTRY_INVALIDATE", "detail": "micro_structural_stop_breached"},
    ]
    cycles = mod.build_cycles(rows)
    assert len(cycles) == 2
    counts = {stage: sum(1 for cycle in cycles if cycle["reached"][stage]) for stage in mod.STAGES}
    drop = mod.dominant_drop(counts)
    assert counts["PENDING_ARM"] == 2
    assert counts["MICRO_ENTRY_ARM"] == 2
    assert counts["MICRO_ENTRY_ZONE_TOUCH"] == 1
    assert drop["from"] == "MICRO_ENTRY_ARM"
    assert drop["to"] == "MICRO_ENTRY_ZONE_TOUCH"
    assert drop["lost_cycles"] == 1


def test_full_analyze_requires_all_nine_months_and_counts_deals() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        screen = root / "screen.csv"
        screen_rows = []
        for month in mod.DEVELOPMENT_MONTHS:
            year, mon = month.split("-")
            screen_rows.append({"time": f"{year}.{mon}.01 00:00:00", "selected_direction": "1"})
        write_csv(screen, ["time", "selected_direction"], screen_rows)

        v69 = root / "v69"
        for month in mod.DEVELOPMENT_MONTHS:
            year, mon = month.split("-")
            run = v69 / f"holdout_{year}_{mon}_long"
            stamp = f"{year}.{mon}.01 00:00:00"
            write_csv(
                run / "V64_ENTRY_EVAL.csv",
                ["time", "decision_reason", "selected_direction", "reject_reason"],
                [{"time": stamp, "decision_reason": "long_edge", "selected_direction": "1", "reject_reason": "pending_bos"}],
            )
            write_csv(
                run / "V64_EVENTS.csv",
                ["time", "event", "detail"],
                [
                    {"time": stamp, "event": "PENDING_ARM", "detail": "bos"},
                    {"time": f"{year}.{mon}.01 00:01:00", "event": "MICRO_ENTRY_ARM", "detail": "bos"},
                ],
            )
            write_csv(
                run / "V64_DEALS.csv",
                ["time", "entry", "profit", "commission", "swap", "fee"],
                [],
            )
        out = mod.analyze(screen, v69)
        assert out["selector_context"]["long_selected_rows"] == 9
        assert out["pending_arm_cycles"] == 9
        assert out["cycle_stage_reach"]["MICRO_ENTRY_ARM"] == 9
        assert out["deals"]["trades"] == 0


def test_runtime_is_read_only_and_identity_guarded() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    launcher = LAUNCHER.read_text(encoding="utf-8")
    assert "V69_DOWNSTREAM_FUNNEL_EXPECTED_HEAD is required" in runner
    assert "V69_DOWNSTREAM_MT5_CAN_REMAIN_RUNNING=1" in runner
    assert "V69_DOWNSTREAM_ORDERS_SENT=0" in runner
    assert "V69_DOWNSTREAM_STRATEGY_CHANGED=0" in runner
    assert "V69_DOWNSTREAM_ACCEPTED_DEVELOPMENT_IDENTITY=PASS" in runner
    assert 'EXPECTED_V69_DEALS = {"trades": 24, "wins": 10, "losses": 14, "net_usd": 7.14}' in runner
    assert "e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb" in runner
    assert "V69_DOWNSTREAM_FUNNEL_EXPECTED_HEAD is required" in launcher
    forbidden = ("terminal64.exe", "metaeditor64.exe", "OrderSend(", ".Buy(", ".Sell(")
    for token in forbidden:
        assert token.lower() not in runner.lower()


def main() -> int:
    tests = [name for name, value in globals().items() if name.startswith("test_") and callable(value)]
    for name in sorted(tests):
        globals()[name]()
        print(f"PASS {name}")
    print(f"V69 downstream LONG funnel tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
