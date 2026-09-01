#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_v68_v67_holdout_stability_source.py"
ANALYZER = ROOT / "scripts" / "analyze_v68_v67_holdout_stability.py"
RUNNER = ROOT / "runtime" / "v68_v67_holdout_stability" / "RUN_V68_V67_HOLDOUT_STABILITY.py"
LAUNCHER = ROOT / "runtime" / "v68_v67_holdout_stability" / "START_V68_V67_HOLDOUT_STABILITY_GIT_BASH.sh"
ADR = ROOT / "docs" / "adr" / "ADR-070-v68-v67-holdout-stability-research.md"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_v68_generated_source_is_v67_decision_equivalent():
    m = load(BUILDER, "v68_builder_test")
    for d in (-1, 1):
        text = m.transform(d)
        m.assert_strategy_equivalence(text, d)
        assert '#property version   "68.00"' in text
        assert "InpV64Magic = 680068" in text
        assert "InpV64MaxStopRiskCash = 1.10" in text
        assert "InpV67PenetrationRiskCash = 0.92" in text
        assert "POST_ZONE_REVERSAL_CONFIRM" in text
        assert "POST_ZONE_ENTRY_READY" in text
        assert m.V67_ROOT not in text
        assert m.V68_ROOT in text


def test_v68_runner_uses_calendar_holdout_without_pnl_selection():
    text = RUNNER.read_text(encoding="utf-8")
    assert 'EXPECTED_BRANCH = "agent/v68-v67-holdout-stability-research"' in text
    assert 'V67_ACCEPTED_HEAD = "782b44a566c772f833cb666ead1bbb21ce150b75"' in text
    assert 'V67_ACCEPTED_ZIP_SHA256 = "545b0baecba5f9ce077b692be90803623b23106b41eca43ef2728214c4d3707b"' in text
    assert text.count('("2025_') >= 4
    assert '("2026_05", "2026.05.01", "2026.06.01")' in text
    assert '"selection_uses_pnl": False' in text
    assert '"v67_decision_logic_changed": False' in text
    assert 'len(HOLDOUT_MONTHS) * len(DIRECTIONS)' in text


def test_v68_launcher_is_direct_python_and_safe():
    text = LAUNCHER.read_text(encoding="utf-8")
    assert "-m pytest" not in text
    assert 'tasklist.exe' in text
    assert 'git status --porcelain' in text
    assert 'exec "$PY" "$RUNNER"' in text
    assert "git clean" not in text
    assert "stash pop" not in text


def test_v68_analyzer_tracks_stability_and_fast_losses():
    text = ANALYZER.read_text(encoding="utf-8")
    for token in (
        '"positive_months"',
        '"negative_months"',
        '"median_month_usd"',
        '"monthly_stdev_usd"',
        '"max_consecutive_negative_months"',
        '"losses_le_15s"',
        '"losses_le_30s"',
        '"losses_le_60s"',
        '"max_realized_dd_usd"',
    ):
        assert token in text


def test_v68_adr_states_validation_only_objective():
    text = ADR.read_text(encoding="utf-8")
    assert "V67" in text
    assert "holdout" in text.lower()
    assert "REAL" in text
    assert "no strategy threshold change" in text.lower()
    assert "18 Model=4 passes" in text


def main() -> int:
    tests = [
        test_v68_generated_source_is_v67_decision_equivalent,
        test_v68_runner_uses_calendar_holdout_without_pnl_selection,
        test_v68_launcher_is_direct_python_and_safe,
        test_v68_analyzer_tracks_stability_and_fast_losses,
        test_v68_adr_states_validation_only_objective,
    ]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V68 static tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
