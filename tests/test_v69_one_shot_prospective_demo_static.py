#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "runtime" / "v69_one_shot_prospective_demo" / "RUN_V69_ONE_SHOT_PROSPECTIVE_DEMO.py"
SUPERVISOR = REPO / "runtime" / "v69_one_shot_prospective_demo" / "SUPERVISE_V69_ONE_SHOT_PROSPECTIVE_DEMO.py"
LAUNCHER = REPO / "runtime" / "v69_one_shot_prospective_demo" / "START_V69_ONE_SHOT_PROSPECTIVE_DEMO_GIT_BASH.sh"
BUILDER = REPO / "scripts" / "build_v69_frozen_forward_demo_dashboard_source.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_contract_is_frozen_demo_long_only_with_ui_overlay() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    required = (
        'FROZEN_V69_RESEARCH_HEAD = "0569701be7846605ac01f94d8b5fc4ec2a6f8dd1"',
        'FROZEN_FORWARD_SOURCE_SHA256 = "0e3f168fa3de9ea62d7ec12d06efbf4d8d67989815056683a939f1d46d8d5f93"',
        'DASHBOARD_SOURCE_SHA256 = "5d00901309c949deafbd7c89164257ca2779fdbddc0e570a09cd82a8272875a0"',
        'EXPERT_NAME = "V69FrozenForwardSmokeDashboardLong"',
        'SMOKE_MIN_CLOSED_TRADES = 2',
        'SMOKE_HARD_CAP_HOURS = 48',
        '"direction": "LONG_ONLY"',
        '"demo_only": True',
        '"real_money_authorized": False',
        '"short_enabled": False',
        '"strategy_changed": False',
        '"dashboard_ui_only": True',
        '"real_money_auto_promotion": False',
    )
    for token in required:
        assert token in text, token
    assert "V69ForwardRealMoneyAuthorized=true" not in text


def test_dashboard_pin_matches_builder_output() -> None:
    runner = load(RUNNER, "v69_one_shot_runner_pin_test")
    builder = load(BUILDER, "v69_one_shot_builder_pin_test")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "dashboard.mq5"
        actual = builder.build(out)
    assert actual == runner.DASHBOARD_SOURCE_SHA256, (
        f"runner dashboard pin stale expected_builder={actual} runner_pin={runner.DASHBOARD_SOURCE_SHA256}"
    )


def test_startup_is_config_driven_and_waits_for_live_tick_heartbeat() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    for token in (
        "[StartUp]", "Expert={EXPERT_NAME}", "Symbol={SYMBOL}", "Period={PERIOD}",
        "AllowLiveTrading=1", "AllowDllImport=0", "TERMINAL_EXE",
        "V69_FORWARD_DEMO_READY=1", "V69_DASHBOARD_HEARTBEAT.txt",
        'hb.get("period") == "PERIOD_M15"', 'ticks > 0', "V69_RUNTIME_SMOKE_VERIFIED=1",
    ):
        assert token in text, token
    assert "attach manually" not in text.lower()


def test_runner_does_not_force_kill_terminal_or_metaeditor() -> None:
    text = RUNNER.read_text(encoding="utf-8").lower()
    for forbidden in ("taskkill", "terminate()", "kill()", "stop-process"):
        assert forbidden not in text, forbidden
    assert "already running. close mt5 once" in text
    assert "already running. close metaeditor once" in text


def test_launcher_probes_real_python_execution() -> None:
    text = LAUNCHER.read_text(encoding="utf-8")
    assert "probe_python" in text
    assert "PYTHON_REJECTED=" in text
    assert "V31_PINNED_VENV" in text
    assert "py.exe -3" in text
    assert "python.exe" in text
    assert "V69_ONE_SHOT_EXPECTED_HEAD is required" in text
    assert "DO NOT git clean" in text
    assert "DO NOT stash pop" in text


def test_supervisor_drops_partial_final_record() -> None:
    mod = load(SUPERVISOR, "v69_one_shot_supervisor_test")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        src = root / "src.csv"
        dst = root / "dst.csv"
        src.write_bytes(b"a,b\n1,2\n3,")
        copied = mod.snapshot_complete_lines(src, dst)
        assert copied == len(b"a,b\n1,2\n")
        assert dst.read_bytes() == b"a,b\n1,2\n"


def test_supervisor_drives_panel_and_exports_short_review() -> None:
    text = SUPERVISOR.read_text(encoding="utf-8")
    for token in (
        "V69_SMOKE_PROGRESS.txt", "panel_progress=", "panel_done=", "panel_need=", "panel_output=",
        "QUICK_REVIEW_READY", "TIME_CAP_REVIEW_READY", "v69_forward_smoke_final.zip",
        "V69_FORWARD_OUTPUT_READY=1", "OUTPUT_EXPORTED", "notify_output",
    ):
        assert token in text, token


def test_supervisor_never_auto_authorizes_real_money_or_sends_orders() -> None:
    text = SUPERVISOR.read_text(encoding="utf-8")
    assert '"real_money_authorized": False' in text
    assert '"real_money_auto_promotion": False' in text
    for forbidden in ("g_trade.Buy", "g_trade.Sell", "OrderSend(", "OrderSendAsync("):
        assert forbidden not in text


def main() -> int:
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"V69 one-shot prospective static tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
