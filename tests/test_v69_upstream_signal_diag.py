#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ANALYZER = REPO / "scripts" / "analyze_v69_upstream_signal_funnel.py"
RUNNER = REPO / "runtime" / "v69_real_readiness_probe" / "RUN_V69_UPSTREAM_SIGNAL_DIAG.py"
LAUNCHER = REPO / "runtime" / "v69_real_readiness_probe" / "RUN_V69_UPSTREAM_SIGNAL_DIAG_GIT_BASH.sh"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_events(root: Path, events: list[tuple[str, str]], *, partial_tail: bool = False) -> None:
    root.mkdir(parents=True, exist_ok=True)
    events_path = root / "V64_EVENTS.csv"
    with events_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["time", "event", "detail"])
        for event, detail in events:
            w.writerow(["2026.09.02 12:00:00", event, detail])
    if partial_tail:
        with events_path.open("ab") as fh:
            fh.write(b"2026.09.02 12:00:01,POST_ZONE_REVERSAL_CONFIRM")
    with (root / "V64_DEALS.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["time", "entry", "price"])


def test_confirm_wait_reason_localizes_upstream_block() -> None:
    mod = load(ANALYZER, "v69_upstream_reason")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_events(
            root,
            [
                ("PENDING_ARM", "ok"),
                ("MICRO_ENTRY_ARM", "ok"),
                ("MICRO_ENTRY_ZONE_TOUCH", "ok"),
                ("MICRO_ENTRY_PENETRATION", "ok"),
                ("POST_ZONE_CONFIRM_WAIT", "reclaim_body_too_small"),
                ("POST_ZONE_CONFIRM_WAIT", "reason=reclaim_body_too_small body=0.2"),
                ("POST_ZONE_CONFIRM_WAIT", "reclaim_candle_wrong_direction"),
            ],
        )
        out = mod.analyze(root)
        assert out["classification"] == "RECLAIM_CONFIRM_QUALITY_BLOCK"
        assert out["dominant_blocker"] == "reclaim_body_too_small"
        assert out["confirm_wait_reason_counts"]["reclaim_body_too_small"] == 2
        assert out["stage_counts"]["POST_ZONE_REVERSAL_CONFIRM"] == 0


def test_funnel_classifies_each_pre_reclaim_transition() -> None:
    mod = load(ANALYZER, "v69_upstream_transitions")
    cases = [
        ([], "INITIAL_SETUP_OR_PENDING_ARM_BLOCK"),
        (["PENDING_ARM"], "PENDING_ARM_REACHED_MICRO_ENTRY_NOT_ARMED"),
        (["PENDING_ARM", "MICRO_ENTRY_ARM"], "MICRO_ENTRY_ARMED_ZONE_NOT_TOUCHED"),
        (["PENDING_ARM", "MICRO_ENTRY_ARM", "MICRO_ENTRY_ZONE_TOUCH"], "ZONE_TOUCH_REACHED_PENETRATION_NOT_REACHED"),
        (["PENDING_ARM", "MICRO_ENTRY_ARM", "MICRO_ENTRY_ZONE_TOUCH", "MICRO_ENTRY_PENETRATION"], "PENETRATION_REACHED_CONFIRM_EVALUATION_NOT_OBSERVED"),
    ]
    for idx, (events, expected) in enumerate(cases):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_events(root, [(event, "ok") for event in events])
            out = mod.analyze(root)
            assert out["classification"] == expected, (idx, out)


def test_partial_live_tail_is_ignored_not_invented() -> None:
    mod = load(ANALYZER, "v69_upstream_partial")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_events(root, [("PENDING_ARM", "ok")], partial_tail=True)
        out = mod.analyze(root)
        assert out["events_rows"] == 1
        assert out["stage_counts"]["PENDING_ARM"] == 1
        assert out["stage_counts"]["POST_ZONE_REVERSAL_CONFIRM"] == 0


def test_header_only_event_file_is_valid_upstream_evidence() -> None:
    mod = load(ANALYZER, "v69_upstream_header_only")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_events(root, [])
        out = mod.analyze(root)
        assert out["events_file_present"] is True
        assert out["events_rows"] == 0
        assert out["stage_counts"]["PENDING_ARM"] == 0
        assert out["classification"] == "INITIAL_SETUP_OR_PENDING_ARM_BLOCK"
        assert out["dominant_blocker"] == "PENDING_ARM"


def test_runner_accepts_zero_event_rows_and_uses_pre_probe_snapshot() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    assert "V69_PRE_PROBE_SIGNAL_PATH.json" in runner
    assert "V69_UPSTREAM_ZERO_EVENT_ROWS_VALID=1" in runner
    assert "none contain readable V64_EVENTS.csv rows" not in runner
    assert "PRE_PROBE_SIGNAL_PATH_JSON" in runner
    assert "INITIAL_SETUP_OR_PENDING_ARM_BLOCK" in ANALYZER.read_text(encoding="utf-8")


def test_runner_and_launcher_are_strictly_read_only() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    launcher = LAUNCHER.read_text(encoding="utf-8")
    assert "V69_UPSTREAM_MT5_CAN_REMAIN_RUNNING=1" in runner
    assert "V69_UPSTREAM_ORDERS_SENT=0" in runner
    assert "_v69_forward_previous_*" in runner
    assert "v69_frozen_forward_demo" in runner
    assert "V69_UPSTREAM_DIAG_EXPECTED_HEAD is required" in runner
    assert "V69_UPSTREAM_DIAG_EXPECTED_HEAD is required" in launcher
    assert "PYTHON_REJECTED=" in launcher
    assert "DO NOT git clean" in launcher
    assert "DO NOT stash pop" in launcher
    for forbidden in (
        "terminal64.exe",
        "metaeditor64.exe",
        "OrderSend(",
        ".Buy(",
        ".Sell(",
        "taskkill",
        ".terminate(",
        ".kill(",
    ):
        assert forbidden not in runner, forbidden
        assert forbidden not in launcher, forbidden


def main() -> int:
    tests = [value for name, value in globals().items() if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"V69 upstream signal diagnostic tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
