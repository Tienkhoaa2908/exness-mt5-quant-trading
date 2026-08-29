from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIXED = REPO / "scripts" / "build_v55_account_agnostic_source_windows_fixed.py"
GATE = REPO / "runtime" / "v55_account_agnostic" / "RUN_V55_WINDOWS_GATE.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def actual_v54_guard_fixture(mod) -> str:
    return (
        "prefix\n"
        + mod.INHERITED_DEMO_GUARD_PREFIX
        + mod.V54_DEMO_ONLY_PRINT
        + " return INIT_FAILED; }\n"
        + "suffix\n"
    )


def test_fixed_builder_removes_actual_v54_inherited_demo_guard():
    mod = load(FIXED, "v55_fixed_builder_regression")
    sample = actual_v54_guard_fixture(mod)
    out = mod.sanitize_inherited_demo_guard(sample)
    assert mod.INHERITED_DEMO_GUARD_PREFIX not in out
    assert mod.V54_DEMO_ONLY_PRINT not in out
    assert mod.V55_ACCOUNT_MODE_GUARD_PREFIX in out
    assert mod.V55_SUPPORTED_MODE_PRINT in out
    assert "real_or_non_demo_account" not in out
    assert "ACCOUNT_TRADE_MODE_DEMO" in out
    assert "ACCOUNT_TRADE_MODE_REAL" in out
    assert "unsupported_account_mode" in out


def test_fixed_builder_fails_closed_if_guard_prefix_drifts():
    mod = load(FIXED, "v55_fixed_builder_drift_prefix")
    sample = mod.V54_DEMO_ONLY_PRINT
    try:
        mod.sanitize_inherited_demo_guard(sample)
    except RuntimeError as exc:
        assert "guard prefix" in str(exc)
    else:
        raise AssertionError("expected fail-closed prefix drift error")


def test_fixed_builder_fails_closed_if_v54_print_drifted():
    mod = load(FIXED, "v55_fixed_builder_drift_print")
    sample = mod.INHERITED_DEMO_GUARD_PREFIX + 'Print("unexpected label"); return INIT_FAILED; }'
    try:
        mod.sanitize_inherited_demo_guard(sample)
    except RuntimeError as exc:
        assert "diagnostic" in str(exc)
    else:
        raise AssertionError("expected fail-closed diagnostic drift error")


def test_windows_gate_routes_runtime_to_corrected_builder():
    text = GATE.read_text(encoding="utf-8")
    assert 'build_v55_account_agnostic_source_windows_fixed.py' in text
    assert "v55.BUILDER = FIXED_BUILDER" in text
    assert "V55_WINDOWS_BUILDER=" in text


def test_original_failure_tokens_are_explicitly_quarantined():
    text = FIXED.read_text(encoding="utf-8")
    assert "real_or_non_demo_account" in text
    assert 'V55Halt(\"non_demo_account\")' in text
    assert "forbidden in" in text
