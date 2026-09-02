#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_v70_exit_harvest_shadow_source.py"
ANALYZER = ROOT / "scripts" / "analyze_v70_exit_harvest_shadow.py"
RUNTIME = ROOT / "runtime" / "v70_exit_harvest_research" / "RUN_V70_EXIT_HARVEST_RESEARCH.py"
LAUNCHER = ROOT / "runtime" / "v70_exit_harvest_research" / "RUN_V70_EXIT_HARVEST_RESEARCH_GIT_BASH.sh"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_builder_preserves_frozen_v69_entry_and_real_exit_contract() -> None:
    m = load(BUILDER, "v70_exit_builder_test")
    s = m.transform()
    assert '#property version   "70.00"' in s
    assert "InpV64Magic = 700070" in s
    assert "InpV64AllowedDirection = 1" in s
    assert "InpV64AllowedDirection = -1" not in s
    assert "InpV64FixedLot = 0.01" in s
    assert "InpV64PrimaryTargetCash = 3.50" in s
    assert "InpV64ProfitArmCash = 2.00" in s
    assert "InpV64ProfitLockCash = 1.00" in s
    assert "InpV69MinConfirmSeparationRiskCash = 1.30" in s
    assert "InpV69MinConfirmAgeSeconds = 30" in s
    assert m.V70_ROOT in s
    assert m.V69_ROOT not in s


def test_exit_shadow_is_observability_only_and_cannot_trade() -> None:
    m = load(BUILDER, "v70_exit_shadow_safety_test")
    helper = m.EXIT_SHADOW
    assert "V70_EXIT_POLICY_TRIGGER" in helper
    assert "BASELINE_200_100" in helper
    assert "EARLY_100_025" in helper
    assert "MID_150_050" in helper
    assert "TIERED_100_025_200_100" in helper
    assert "PositionClose" not in helper
    assert "PositionModify" not in helper
    assert ".Buy(" not in helper
    assert ".Sell(" not in helper


def test_analyzer_uses_true_position_lifetime_events_not_v64_noise_shadow() -> None:
    m = load(ANALYZER, "v70_exit_analyzer_test")
    events = [
        {"time": "2025.09.01 00:00:01", "event": "V70_EXIT_SHADOW_START", "detail": "actual_position_lifetime", "v1": "3500", "v2": "1", "v3": "0"},
        {"time": "2025.09.01 00:00:03", "event": "V70_EXIT_POLICY_ARM", "detail": "EARLY_100_025", "v1": "1.10", "v2": "0.25", "v3": "1.10"},
        {"time": "2025.09.01 00:00:05", "event": "V70_EXIT_POLICY_TRIGGER", "detail": "EARLY_100_025", "v1": "0.20", "v2": "0.25", "v3": "1.20"},
        {"time": "2025.09.01 00:00:08", "event": "V70_EXIT_SHADOW_END", "detail": "actual_position_closed", "v1": "1.20", "v2": "-0.40", "v3": "7"},
    ]
    blocks = m.parse_shadow_blocks(events)
    assert len(blocks) == 1
    assert blocks[0]["true_mfe_usd"] == 1.2
    assert blocks[0]["true_mae_usd"] == -0.4
    assert blocks[0]["triggers"]["EARLY_100_025"]["pnl"] == 0.2
    src = ANALYZER.read_text(encoding="utf-8")
    assert "V64_NOISE_SHADOW" not in src


def test_runtime_fails_closed_on_accepted_v69_baseline_identity() -> None:
    m = load(RUNTIME, "v70_exit_runtime_identity_test")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "analysis.json"
        p.write_text(
            json.dumps({"actual": {"trades": 24, "wins": 10, "losses": 14, "net_usd": 7.14}}),
            encoding="utf-8",
        )
        result = m.require_accepted_baseline(p)
        assert result["actual"]["trades"] == 24
        p.write_text(
            json.dumps({"actual": {"trades": 23, "wins": 10, "losses": 13, "net_usd": 7.14}}),
            encoding="utf-8",
        )
        try:
            m.require_accepted_baseline(p)
        except RuntimeError as exc:
            assert "baseline trade identity mismatch" in str(exc)
        else:
            raise AssertionError("baseline identity guard must fail closed")


def test_runtime_is_exact_head_tester_only_long_only() -> None:
    src = RUNTIME.read_text(encoding="utf-8")
    sh = LAUNCHER.read_text(encoding="utf-8")
    assert 'EXPECTED_BRANCH = "agent/v70-exit-harvest-research"' in src
    assert 'EXPECTED_HEAD_ENV = "V70_EXIT_HARVEST_EXPECTED_HEAD"' in src
    assert 'EXPERT = "V70ExitHarvestShadowLong"' in src
    assert "EXPECTED_BASELINE_TRADES = 24" in src
    assert "EXPECTED_BASELINE_WINS = 10" in src
    assert "EXPECTED_BASELINE_LOSSES = 14" in src
    assert "EXPECTED_BASELINE_NET_USD = 7.14" in src
    assert "V70_BASELINE_ACCEPTED_V69_IDENTITY=PASS" in src
    assert "MetaTrader 5 must be closed for the one-pass V70 tester replay" in src
    assert "REAL_MONEY_AUTHORIZED=0" in src
    assert "V70_SHORT_ENABLED=0" in src
    assert "V70_EXIT_HARVEST_EXPECTED_HEAD" in sh
    assert "REAL_MONEY_AUTHORIZED=0" in sh


def main() -> int:
    tests = [
        obj for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V70 exit-harvest research tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
