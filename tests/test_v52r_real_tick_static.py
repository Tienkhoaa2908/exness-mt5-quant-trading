#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "runtime" / "v52r_real_tick" / "RUN_V52R_REAL_TICK_ONE_SHOT.py"
START = ROOT / "runtime" / "v52r_real_tick" / "START_V52R_REAL_TICK_GIT_BASH.sh"
ANALYZER = ROOT / "scripts" / "analyze_v52r_real_tick.py"
ADR = ROOT / "docs" / "adr" / "ADR-053-real-tick-reproducibility-gate.md"
RESULT = ROOT / "docs" / "research" / "v52_source_aware_results_2026-08-26.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_exact_v52_source_is_reused_without_alpha_retune():
    t = read(RUNNER)
    assert 'V52_SOURCE_SHA = "676823fd380ee3d1654f17b348b04a42cd4ad8afe5fdbecb4247dfe552f8df09"' in t
    assert "v52.build_source(expert_dir)" in t
    assert "V52R_EXACT_V52_SOURCE_PASS=1" in t


def test_real_tick_model_is_explicit():
    t = read(RUNNER)
    assert "Model=4" in t
    assert '"tester_model=4"' in t
    assert '"real_ticks=1"' in t


def test_data_integrity_fails_closed_before_selection():
    t = read(ANALYZER)
    assert "MAX_PRICE_RATIO = 1.25" in t
    assert "MAX_ABS_R = 10.0" in t
    assert "V52R_DATA_INTEGRITY_FAIL" in t
    assert "if not report.get(\"pass\")" in t
    assert "V52R_CHALLENGER_SELECTED" in t
    assert "V52R_KEEP_BREADTH4" in t


def test_v52_contaminated_run_is_not_promoted():
    t = read(RESULT)
    assert "V52_RESULT=INVALID_DATA_CONTAMINATION" in t
    assert "29846.016" in t
    assert "30363.760" in t
    assert "30836.912" in t
    assert "825" in t and "795" in t


def test_adr_freezes_hypothesis_and_prohibits_tuning_on_data_failure():
    t = read(ADR)
    assert "Model=4" in t
    assert "V52R_DATA_INTEGRITY_FAIL" in t
    assert "must not trigger parameter tuning" in t


def test_start_is_one_user_task():
    t = read(START)
    assert t.count("RUN_V52R_REAL_TICK_ONE_SHOT.py") == 1
    assert "v52r_real_tick_repro.zip" in t


def _run_without_pytest():
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in funcs:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V52R real-tick static tests PASS count={len(funcs)}")


if __name__ == "__main__":
    _run_without_pytest()
