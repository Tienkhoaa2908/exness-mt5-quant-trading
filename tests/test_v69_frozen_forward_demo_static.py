#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_v69_frozen_forward_demo_source.py"
PARENT = ROOT / "scripts" / "build_v69_confirm_separation_retest_source.py"
CURRENT = ROOT / "docs" / "handover" / "CURRENT_STATE.md"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_forward_is_long_only_and_keeps_v69_cash_contract() -> None:
    m = load(BUILDER, "v69_forward_builder")
    s = m.transform()
    assert '#property version   "69.10"' in s
    assert "InpV64Magic = 690169" in s
    assert "InpV64AllowedDirection = 1" in s
    assert "InpV64AllowedDirection = -1" not in s
    assert "InpV64FixedLot = 0.01" in s
    assert "InpV64MinStopRiskCash = 0.85" in s
    assert "InpV64MaxStopRiskCash = 1.10" in s
    assert "InpV64EmergencyLossCash = 1.20" in s
    assert "InpV64PrimaryTargetCash = 3.50" in s
    assert "InpV69MinConfirmSeparationRiskCash = 1.30" in s
    assert "InpV69MinConfirmAgeSeconds = 30" in s


def test_forward_replaces_tester_refusal_with_strict_demo_guards() -> None:
    s = load(BUILDER, "v69_forward_demo_guard").transform()
    assert "MQL_TESTER" not in s
    assert "ACCOUNT_TRADE_MODE_DEMO" in s
    assert "v69_forward_demo_only" in s
    assert "V69 FROZEN FORWARD REFUSED: DEMO ACCOUNT REQUIRED" in s
    assert "V69 FROZEN FORWARD HALT: DEMO ACCOUNT REQUIRED" in s
    assert "ExpertRemove();" in s
    assert "const bool V69ForwardRealMoneyAuthorized=false;" in s
    assert "V69ForwardRealMoneyAuthorized=true" not in s
    assert "V48WriteInitDiagnostic" not in s


def test_forward_preserves_v69_entry_state_machine_exactly() -> None:
    parent = load(PARENT, "v69_parent_exact").transform(1)
    forward = load(BUILDER, "v69_forward_exact").transform()

    p = parent[parent.index("void V66TryMicroEntry"):parent.index("void V64ManagePendingEntry")]
    f = forward[forward.index("void V66TryMicroEntry"):forward.index("void V64ManagePendingEntry")]
    f = f.replace("V69 FORWARD DEMO L", "V69 SEP RETEST L")
    assert f == p

    for token in (
        'V64PendingEvent("POST_ZONE_REVERSAL_CONFIRM"',
        'V64PendingEvent("POST_CONFIRM_SEPARATION"',
        'V64PendingEvent("POST_CONFIRM_RETEST_READY"',
        'V64PendingEvent("POST_CONFIRM_ENTRY_READY"',
        "V64OrderPreflight",
    ):
        assert token in f


def test_forward_uses_isolated_common_root() -> None:
    m = load(BUILDER, "v69_forward_root")
    s = m.transform()
    assert m.V69_FORWARD_ROOT in s
    assert m.V69_RESEARCH_ROOT not in s


def test_forward_recovery_contract_is_canonical() -> None:
    assert CURRENT.is_file()
    t = CURRENT.read_text(encoding="utf-8")
    assert "0569701be7846605ac01f94d8b5fc4ec2a6f8dd1" in t
    assert "SHORT rejected/disabled" in t or "SHORT disabled" in t
    assert "REAL authorization false" in t or "REAL_MONEY_AUTHORIZED=0" in t
    assert "LONG only" in t
    # Use durable classification/safety markers rather than prose headings.
    assert "V69_ACTUAL_DEMO_EXECUTION_TRANSPORT=PASS" in t
    assert "REAL_MONEY_AUTHORIZED=0" in t


def main() -> int:
    tests = [
        obj for name, obj in sorted(globals().items())
        if name.startswith("test_forward_") and callable(obj)
    ]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V69 frozen forward static tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
