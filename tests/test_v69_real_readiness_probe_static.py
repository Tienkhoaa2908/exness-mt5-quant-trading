#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILDER = REPO / "scripts" / "build_v69_demo_execution_probe_source.py"
ANALYZER = REPO / "scripts" / "analyze_v69_live_signal_path.py"
RUNNER = REPO / "runtime" / "v69_real_readiness_probe" / "RUN_V69_REAL_READINESS_PROBE.py"
LAUNCHER = REPO / "runtime" / "v69_real_readiness_probe" / "START_V69_REAL_READINESS_PROBE_GIT_BASH.sh"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_execution_probe_is_demo_only_and_actually_opens_and_closes() -> None:
    mod = load(BUILDER, "v69_exec_probe_builder")
    mod.validate()
    text = mod.SOURCE
    for token in (
        "ACCOUNT_TRADE_MODE_DEMO",
        "V69ProbeRealMoneyAuthorized=false",
        "V69ProbeLot=0.01",
        "V69ProbeMagic=699901",
        "OrderCheck(req,chk)",
        "g_probe.Buy(V69ProbeLot",
        "g_probe.PositionClose(ticket,50)",
        "actual_demo_open_and_close_verified",
        "TerminalClose(terminal_code)",
    ):
        assert token in text, token
    assert "Sell(" not in text
    assert "V69ProbeRealMoneyAuthorized=true" not in text


def test_execution_probe_builder_is_deterministic() -> None:
    mod = load(BUILDER, "v69_exec_probe_determinism")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        a = root / "a.mq5"
        b = root / "b.mq5"
        ha = mod.build(a)
        hb = mod.build(b)
        assert ha == hb
        assert a.read_bytes() == b.read_bytes()


def write_events(root: Path, events: list[tuple[str, str]]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    with (root / "V64_EVENTS.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["time", "event", "detail"])
        for event, detail in events:
            w.writerow(["2026.09.01 20:00:00", event, detail])
    with (root / "V64_DEALS.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["time", "entry", "price"])


def test_signal_path_funnel_locates_last_reached_stage() -> None:
    mod = load(ANALYZER, "v69_signal_funnel")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_events(
            root,
            [
                ("POST_ZONE_REVERSAL_CONFIRM", "confirm"),
                ("POST_CONFIRM_SEPARATION", "separation"),
            ],
        )
        out = mod.analyze(root)
        assert out["stage_counts"]["POST_ZONE_REVERSAL_CONFIRM"] == 1
        assert out["stage_counts"]["POST_CONFIRM_SEPARATION"] == 1
        assert out["stage_counts"]["POST_CONFIRM_RETEST_READY"] == 0
        assert out["classification"] == "SEPARATION_REACHED_RETEST_NOT_REACHED"


def test_entry_ready_without_trade_is_explicit_order_path_review() -> None:
    mod = load(ANALYZER, "v69_signal_entry_ready")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_events(
            root,
            [
                ("POST_ZONE_REVERSAL_CONFIRM", "confirm"),
                ("POST_CONFIRM_SEPARATION", "separation"),
                ("POST_CONFIRM_RETEST_READY", "retest"),
                ("POST_CONFIRM_ENTRY_READY", "entry"),
            ],
        )
        out = mod.analyze(root)
        assert out["classification"] == "ENTRY_READY_WITHOUT_CLOSED_TRADE_ORDER_PATH_REVIEW"


def test_one_shot_reads_old_telemetry_then_probes_then_relaunches_frozen_v69() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "snapshot_signal_path(common)" in text
    assert "LAUNCH_V69_ACTUAL_DEMO_EXECUTION_PROBE=1" in text
    assert "V69_ACTUAL_DEMO_EXECUTION_VERIFIED=1" in text
    assert "wait_terminal_close(proc)" in text
    assert "RELAUNCH_FROZEN_V69_AFTER_EXECUTION_PROBE=1" in text
    assert "rc = forward.main()" in text
    assert '"real_money_authorized": False' in text
    for forbidden in ("taskkill", ".kill(", ".terminate("):
        assert forbidden not in text


def test_launcher_contract() -> None:
    text = LAUNCHER.read_text(encoding="utf-8")
    assert "V69_REAL_READINESS_EXPECTED_HEAD is required" in text
    assert "PYTHON_REJECTED=" in text
    assert "no working Python 3.10+ found" in text
    assert "DO NOT git clean" in text
    assert "DO NOT stash pop" in text


def main() -> int:
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"V69 real-readiness probe static tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
