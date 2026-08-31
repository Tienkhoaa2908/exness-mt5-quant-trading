#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILDER = REPO / "scripts" / "build_v69_frozen_forward_demo_dashboard_source.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_dashboard_is_ui_only_over_exact_frozen_parent() -> None:
    mod = load(BUILDER, "v69_dashboard_builder_test")
    base = mod.parent.transform()
    text = mod.transform()
    assert mod.sha_bytes(mod.crlf_bytes(base)) == mod.FROZEN_PARENT_SHA256
    for token in (
        "V69 FROZEN FORWARD - DEMO SMOKE VALIDATION",
        "OBJ_RECTANGLE_LABEL",
        "V69_DASHBOARD_HEARTBEAT.txt",
        "V69_SMOKE_PROGRESS.txt",
        "PROGRESS:",
        "DONE:",
        "NEED:",
        "OUTPUT:",
        "Trade #5:",
        "EventSetTimer(1)",
        "void OnTimer()",
        "V69DPositionNet",
        "const bool V69ForwardRealMoneyAuthorized=false;",
        "InpV64AllowedDirection = 1",
        "InpV64Magic = 690169",
    ):
        assert token in text, token
    for forbidden in (
        "V69ForwardRealMoneyAuthorized=true",
        "InpV64AllowedDirection = -1",
    ):
        assert forbidden not in text


def test_critical_frozen_strategy_blocks_are_byte_identical() -> None:
    mod = load(BUILDER, "v69_dashboard_block_test")
    base = mod.parent.transform()
    text = mod.transform()
    for sig, nxt in (
        ("void V66TryMicroEntry", "void V64ManagePendingEntry"),
        ("void V64ManagePendingEntry", "void V64EvaluateBar"),
        ("bool V64BuildStopTarget", "void V64ArmPending"),
    ):
        a0=base.index(sig);a1=base.index(nxt,a0+1);b0=text.index(sig);b1=text.index(nxt,b0+1)
        assert base[a0:a1] == text[b0:b1], sig


def test_dashboard_build_is_deterministic() -> None:
    mod = load(BUILDER, "v69_dashboard_determinism_test")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        a = root / "a.mq5"
        b = root / "b.mq5"
        ha = mod.build(a)
        hb = mod.build(b)
        assert ha == hb
        assert a.read_bytes() == b.read_bytes()


def main() -> int:
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"V69 frozen forward dashboard tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
