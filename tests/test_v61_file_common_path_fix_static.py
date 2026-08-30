from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REAL = REPO / "scripts" / "build_v61_profit_ratchet_m5_refinement_source_fixed.py"
SCREEN = REPO / "scripts" / "build_v61_profit_ratchet_m5_refinement_screen_source_fixed.py"
RUNNER = REPO / "runtime" / "v61_profit_ratchet_m5_refinement" / "RUN_V61_PROFIT_RATCHET_M5_REFINEMENT_FIXED.py"
LAUNCHER = REPO / "runtime" / "v61_profit_ratchet_m5_refinement" / "START_V61_PROFIT_RATCHET_M5_REFINEMENT_FIXED_GIT_BASH.sh"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fixed_builder_uses_only_canonical_file_common_root():
    mod = load(REAL, "v61_fixed_builder_test")
    text = mod.transform()
    assert mod.CANONICAL_ROOT in text
    assert text.count(mod.CANONICAL_ROOT) >= 5
    assert mod.LEGACY_ROOT not in text
    assert r"mt5_quant\\v61_profit_ratchet_m5_refinement\\V61_ENTRY_EVAL.csv" in text


def test_fixed_screen_is_dedicated_directional_per_bar_path():
    mod = load(SCREEN, "v61_fixed_directional_screen_test")
    real = load(REAL, "v61_fixed_real_for_screen_test")
    text = mod.transform()
    real.validate(text)
    assert "InpV61ScreenOnly = true" in text
    assert real.CANONICAL_ROOT in text
    assert real.LEGACY_ROOT not in text
    assert "V61_DIRECTIONAL_SCREEN_ONLY" in text
    assert "screen_direction_only" in text

    eval_start = text.index("void V61EvaluateBar()")
    eval_end = text.index("int OnInit()", eval_start)
    eval_body = text[eval_start:eval_end]
    assert "V61BuildFeatures(f)" in eval_body
    assert "V61SelectDirection(f,why)" in eval_body
    assert "V61Append(V61_EVAL,row)" in eval_body
    assert '"0,0,0,0,0,0,0,0,"+IntegerToString(0)' in eval_body
    assert '"0,0,0,0,0,0,0,0,0,"+IntegerToString(0)' not in eval_body
    for token in (
        "V61BuildStopTarget(",
        "V61StartShadow(",
        "OrderCalcMargin(",
        "V61OrderPreflight(",
        "g_trade.Buy(",
        "g_trade.Sell(",
    ):
        assert token not in eval_body, token

    tick_start = text.index("void OnTick()")
    tick_end = text.index("void OnTradeTransaction", tick_start)
    tick_body = text[tick_start:tick_end]
    assert "V61EvaluateBar();" in tick_body
    for token in (
        "V61UpdateShadow(",
        "V61ManageProfitRatchet(",
        "V61MaybeSoftLossCut(",
        "V61OwnedPosition(",
    ):
        assert token not in tick_body, token


def test_fixed_runner_archives_legacy_and_canonical_and_has_diagnostics():
    text = RUNNER.read_text(encoding="utf-8")
    for token in (
        'CANONICAL_DIR = "v61_profit_ratchet_m5_refinement"',
        'LEGACY_DIR = "v61_small_loss_cash_target"',
        "V61_FILE_COMMON_ROOT_MISMATCH",
        "V61_CANONICAL_LISTING",
        "V61_LEGACY_LISTING",
        "V61_EVIDENCE_ROOT_PASS",
        "V61_COMPILE_PASS",
        "V61_TESTER_PASS_START",
        "V61_SCREEN_DIAGNOSTICS",
        "not_pnl_not_screen_feasibility",
        "V61_SCREEN_COVERAGE_PASS",
        "MIN_SCREEN_ROWS = 5000",
        "MIN_SCREEN_SPAN_DAYS = 250",
    ):
        assert token in text, token


def write_screen_csv(path: Path, rows: list[list[str]]) -> None:
    fields = ["time", "selected_direction", "feasible", "h4_trend", "h1_trend", "reject_reason"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(fields)
        wr.writerows(rows)


def test_screen_selector_does_not_require_model2_execution_feasibility():
    mod = load(RUNNER, "v61_fixed_runner_selector_test")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        screen = root / "screen"
        screen.mkdir()
        out = root / "out"
        out.mkdir()
        mod.v61.OUT = out
        path = screen / "V61_ENTRY_EVAL.csv"
        rows = [
            ["2026.08.24 10:00:00", "1", "0", "1", "1", "screen_direction_only"],
            ["2026.08.17 10:00:00", "1", "0", "1", "1", "screen_direction_only"],
            ["2026.08.10 10:00:00", "-1", "0", "-1", "-1", "screen_direction_only"],
            ["2026.08.03 10:00:00", "-1", "0", "-1", "-1", "screen_direction_only"],
        ]
        write_screen_csv(path, rows)
        result = mod.select_directional_windows(screen, enforce_coverage=False)
        assert len(result["long"]) == 2
        assert len(result["short"]) == 2
        assert all(x["screen_feasible_signal_count"] == 0 for x in result["long"] + result["short"])
        assert (out / "V61_SCREEN_DIAGNOSTICS.json").is_file()


def test_screen_coverage_guard_rejects_truncated_one_row_run():
    mod = load(RUNNER, "v61_fixed_runner_coverage_test")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        screen = root / "screen"
        screen.mkdir()
        out = root / "out"
        out.mkdir()
        mod.v61.OUT = out
        path = screen / "V61_ENTRY_EVAL.csv"
        write_screen_csv(path, [["2025.09.01 00:00:00", "1", "0", "1", "1", "screen_direction_only"]])
        try:
            mod.select_directional_windows(screen, enforce_coverage=True)
        except RuntimeError as exc:
            msg = str(exc)
            assert "screen coverage insufficient" in msg
            assert "rows=1" in msg
        else:
            raise AssertionError("truncated one-row screen must fail coverage guard")


def test_fixed_launcher_points_only_to_fixed_runner():
    text = LAUNCHER.read_text(encoding="utf-8")
    assert "RUN_V61_PROFIT_RATCHET_M5_REFINEMENT_FIXED.py" in text
    assert "set -Eeuo pipefail" in text
    assert 'EXPECTED_BRANCH="agent/v61-profit-ratchet-m5-refinement-research"' in text


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print(f"V61 fixed-layer static tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
