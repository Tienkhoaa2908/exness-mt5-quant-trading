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


def test_fixed_builder_removes_exact_inherited_v48_demo_guard():
    mod = load(FIXED, "v55_fixed_builder_regression")
    sample = "prefix\n" + mod.INHERITED_V48_DEMO_GUARD + "\nsuffix\n"
    out = mod.sanitize_inherited_demo_guard(sample)
    assert mod.INHERITED_V48_DEMO_GUARD not in out
    assert mod.V55_ACCOUNT_MODE_GUARD in out
    assert "real_or_non_demo_account" not in out
    assert "ACCOUNT_TRADE_MODE_DEMO" in out
    assert "ACCOUNT_TRADE_MODE_REAL" in out
    assert "unsupported_account_mode" in out


def test_fixed_builder_fails_closed_if_parent_guard_drifts():
    mod = load(FIXED, "v55_fixed_builder_drift")
    try:
        mod.sanitize_inherited_demo_guard("no inherited guard here")
    except RuntimeError as exc:
        assert "guard drifted" in str(exc)
    else:
        raise AssertionError("expected fail-closed guard drift error")


def test_windows_gate_routes_runtime_to_corrected_builder():
    text = GATE.read_text(encoding="utf-8")
    assert 'build_v55_account_agnostic_source_windows_fixed.py' in text
    assert "v55.BUILDER = FIXED_BUILDER" in text
    assert "V55_WINDOWS_BUILDER=" in text


def test_original_failure_token_is_explicitly_quarantined():
    text = FIXED.read_text(encoding="utf-8")
    assert "real_or_non_demo_account" in text
    assert 'V55Halt(\"non_demo_account\")' in text
    assert "for forbidden in" in text
