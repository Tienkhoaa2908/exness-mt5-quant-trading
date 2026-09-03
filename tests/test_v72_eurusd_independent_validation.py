#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYZER = ROOT / "scripts" / "analyze_v72_eurusd_validation.py"
RUNNER = ROOT / "runtime" / "v72_eurusd_independent_validation" / "RUN_V72_EURUSD_INDEPENDENT_VALIDATION.py"
LAUNCHER = ROOT / "runtime" / "v72_eurusd_independent_validation" / "RUN_V72_EURUSD_INDEPENDENT_VALIDATION_GIT_BASH.sh"
BUILDER = ROOT / "scripts" / "build_v71_fx_portability_source.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def make_run(root: Path, pnls: list[float]) -> None:
    deal_fields = ["time", "entry", "profit", "commission", "swap", "fee"]
    rows = []
    for idx, pnl in enumerate(pnls, 1):
        day = idx
        rows.append({"time": f"2024.09.{day:02d} 10:00:00", "entry": 0, "profit": 0, "commission": 0, "swap": 0, "fee": 0})
        rows.append({"time": f"2024.09.{day:02d} 10:30:00", "entry": 1, "profit": pnl, "commission": 0, "swap": 0, "fee": 0})
    write_csv(root / "V64_DEALS.csv", deal_fields, rows)
    write_csv(root / "V64_EVENTS.csv", ["event"], [{"event": "REFINED_ENTRY"} for _ in pnls])
    write_csv(root / "V64_ENTRY_EVAL.csv", ["time"], [{"time": "2024.09.01 00:00:00"}])


def make_recovery_root(common: Path, when: str) -> Path:
    root = common / "mt5_quant" / "v71_fx_portability"
    root.mkdir(parents=True)
    write_csv(root / "V64_ENTRY_EVAL.csv", ["time"], [{"time": when}])
    write_csv(root / "V64_EVENTS.csv", ["time", "event"], [{"time": when, "event": "REFINED_ENTRY"}])
    write_csv(
        root / "V64_DEALS.csv",
        ["time", "entry", "profit", "commission", "swap", "fee"],
        [
            {"time": when, "entry": 0, "profit": 0, "commission": 0, "swap": 0, "fee": 0},
            {"time": when, "entry": 1, "profit": 1, "commission": 0, "swap": 0, "fee": 0},
        ],
    )
    return root


def test_preregistered_acceptance_and_ex_best_guard() -> None:
    mod = load(ANALYZER, "v72_analyzer_test")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_run(root, [3.5, 2.0, 2.0, 1.0, -1.0, -1.0, -1.0, -1.0])
        result = mod.analyze(root)
        assert result["metrics"]["trades"] == 8
        assert result["metrics"]["net_usd"] > 0
        assert result["metrics"]["ex_best_trade_net_usd"] > 0
        # One synthetic month intentionally cannot satisfy the positive-month gate.
        assert result["classification"] == "FAIL"
    print("PASS test_preregistered_acceptance_and_ex_best_guard")


def test_insufficient_sample_is_not_false_pass() -> None:
    mod = load(ANALYZER, "v72_analyzer_small_test")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_run(root, [3.5, 1.0, -1.0])
        result = mod.analyze(root)
        assert result["classification"] == "INSUFFICIENT_SAMPLE"
    print("PASS test_insufficient_sample_is_not_false_pass")


def test_runner_is_exact_source_untouched_long_only() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    builder = BUILDER.read_text(encoding="utf-8")
    assert 'EXPECTED_BRANCH = "agent/v72-eurusd-independent-validation"' in text
    assert 'SYMBOL = "EURUSDm"' in text
    assert 'FROM_DATE = "2024.09.01"' in text
    assert 'TO_DATE = "2025.09.01"' in text
    assert 'EXPECTED_SOURCE_SHA256 = "32615744d81e48be9f95638a8062e590b690bf1ec56437dc3293fda4bb202e7c"' in text
    assert 'BUILDER = REPO / "scripts" / "build_v71_fx_portability_source.py"' in text
    assert 'SOURCE_COMMON_DIR = "v71_fx_portability"' in text
    assert 'runner.COMMON_DIR = SOURCE_COMMON_DIR' in text
    assert 'V71_ROOT = r"mt5_quant\\\\v71_fx_portability"' in builder
    assert 'V72_EURUSD_ENTRY_RETUNE=0' in text
    assert 'V72_EURUSD_EXIT_RETUNE=0' in text
    assert 'V72_SHORT_ENABLED=0' in text
    assert 'REAL_MONEY_AUTHORIZED=0' in text
    print("PASS test_runner_is_exact_source_untouched_long_only")


def test_existing_completed_run_is_recovered_without_rerun() -> None:
    mod = load(RUNNER, "v72_runner_recovery_test")

    class StubRunner:
        def __init__(self):
            self.calls = 0

        def copy_run(self, root: Path, label: str) -> Path:
            self.calls += 1
            assert label == "v72_eurusdm_untouched_long"
            return root

    with tempfile.TemporaryDirectory() as td:
        common = Path(td)
        expected_root = make_recovery_root(common, "2024.10.15 12:00:00")
        stub = StubRunner()
        result = mod.recover_existing_v72_evidence(stub, common, "v72_eurusdm_untouched_long")
        assert result == expected_root
        assert stub.calls == 1
    print("PASS test_existing_completed_run_is_recovered_without_rerun")


def test_stale_v71_period_is_not_recovered() -> None:
    mod = load(RUNNER, "v72_runner_stale_recovery_test")

    class StubRunner:
        def copy_run(self, root: Path, label: str) -> Path:
            raise AssertionError("stale evidence must not be copied")

    with tempfile.TemporaryDirectory() as td:
        common = Path(td)
        make_recovery_root(common, "2025.10.15 12:00:00")
        result = mod.recover_existing_v72_evidence(StubRunner(), common, "v72_eurusdm_untouched_long")
        assert result is None
    print("PASS test_stale_v71_period_is_not_recovered")


def test_launcher_is_one_pass_fail_closed() -> None:
    text = LAUNCHER.read_text(encoding="utf-8")
    assert 'V72_EURUSD_EXPECTED_HEAD is required' in text
    assert 'V72_EURUSD_TESTER_RUNS=1' in text
    assert 'V72_EURUSD_UNTOUCHED_PERIOD=2024.09.01,2025.09.01' in text
    assert 'V72_SHORT_ENABLED=0' in text
    assert 'REAL_MONEY_AUTHORIZED=0' in text
    print("PASS test_launcher_is_one_pass_fail_closed")


if __name__ == "__main__":
    test_preregistered_acceptance_and_ex_best_guard()
    test_insufficient_sample_is_not_false_pass()
    test_runner_is_exact_source_untouched_long_only()
    test_existing_completed_run_is_recovered_without_rerun()
    test_stale_v71_period_is_not_recovered()
    test_launcher_is_one_pass_fail_closed()
    print("V72 EURUSD independent validation tests PASS count=6")
