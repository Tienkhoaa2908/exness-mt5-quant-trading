from pathlib import Path
import ast
import re

ROOT = Path(__file__).resolve().parents[1]

def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")

def test_v39_stage_a_is_bounded_and_not_target_forcing():
    text = read("scripts/v39_selective_harvest_stage_a.py")
    tree = ast.parse(text)
    assert "CONTROL = \"adaptive_ewma_hl8_thr0\"" in text
    assert "MIN_R = 1.0" in text
    assert "CALIBRATION_SCORE_QUANTILE = 0.85" in text
    assert "CALIBRATION_MONTHS = 2" in text
    assert "V36_HOLD_CEILING = 0.15" in text
    assert "V36_MAX_AGE_MINUTES = 75.0" in text
    assert "no_test_month_threshold_tuning" in text
    assert "Do not optimize risk or thresholds merely to force 15%/month" in text
    assert not any(isinstance(n, (ast.For, ast.ListComp)) and "threshold" in ast.unparse(n).lower() for n in ast.walk(tree))

def test_v39_stage_a_has_no_mt5_or_native_order_execution_path():
    script = read("scripts/v39_selective_harvest_stage_a.py")
    runner = read("runtime/v39_selective_harvest/RUN_V39_SELECTIVE_HARVEST_STAGE_A_GIT_BASH.sh")
    combined = script + "\n" + runner
    # The runner deliberately contains a grep safety pattern naming forbidden APIs.
    # Remove that one preflight statement before checking for actual execution paths.
    cleaned_lines = [line for line in combined.splitlines() if "grep -Eiq" not in line]
    cleaned = "\n".join(cleaned_lines)
    forbidden = [
        r"terminal64\.exe",
        r"metaeditor64\.exe",
        r"OrderSend\s*\(",
        r"OrderSendAsync\s*\(",
        r"\bCTrade\b",
        r"trade\.Buy\s*\(",
        r"trade\.Sell\s*\(",
    ]
    for pattern in forbidden:
        assert re.search(pattern, cleaned, flags=re.I) is None, pattern
    assert "mt5_launched=0" in runner
    assert "metaeditor_launched=0" in runner
    assert "live_trading=FORBIDDEN" in runner

def test_v39_runner_verifies_evidence_and_one_zip_manifest():
    runner = read("runtime/v39_selective_harvest/RUN_V39_SELECTIVE_HARVEST_STAGE_A_GIT_BASH.sh")
    assert "224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b" in runner
    assert "bundle_manifest_sha256.txt" in runner
    assert "ZIP integrity PASS" in runner
    assert "v39_selective_harvest_stage_a.zip" in runner
    assert "-m py_compile" in runner
    assert "-m pytest -q" in runner
    assert 'scripts/secret_scan.py' in runner or 'SECRET_SCAN=' in runner

def test_v39_bootstrap_uses_recovered_branch_without_local_strategy_patch():
    text = read("runtime/v39_selective_harvest/BOOTSTRAP_V39_SELECTIVE_HARVEST_ONE_SHOT_GIT_BASH.sh")
    assert 'agent/v39-selective-harvest' in text
    assert 'reset --hard "origin/$BRANCH"' in text
    assert "python - " not in text
    assert "terminal64.exe" not in text.lower()
    assert "metaeditor64.exe" not in text.lower()

def test_standard_one_run_one_zip_tools_exist_and_verify_manifest():
    pack = read("scripts/package_mt5_research.py")
    cmd = read("scripts/package_mt5_research.cmd")
    analyze = read("scripts/analyze_mt5_research_bundle.py")
    assert "bundle_manifest_sha256.txt" in pack
    assert "verify_zip" in pack
    assert "package_mt5_research.py" in cmd
    assert "bundle_manifest_sha256.txt" in analyze
    assert "manifest_pass" in analyze
    assert "testzip" in analyze

def _run_without_pytest():
    tests = [
        test_v39_stage_a_is_bounded_and_not_target_forcing,
        test_v39_stage_a_has_no_mt5_or_native_order_execution_path,
        test_v39_runner_verifies_evidence_and_one_zip_manifest,
        test_v39_bootstrap_uses_recovered_branch_without_local_strategy_patch,
        test_standard_one_run_one_zip_tools_exist_and_verify_manifest,
    ]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V39 static tests PASS count={len(tests)}")

if __name__ == "__main__":
    _run_without_pytest()
