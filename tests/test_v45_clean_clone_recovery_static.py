#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOT = ROOT / "runtime" / "v45_multiyear_validation" / "BOOTSTRAP_V45_MULTIYEAR_ONE_SHOT_GIT_BASH.sh"
RECOVER = ROOT / "runtime" / "v45_multiyear_validation" / "RUN_V45_MULTIYEAR_ONE_SHOT_RECOVERABLE.py"


def rt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_bootstrap_uses_script_relative_repo_not_home_c_drive():
    text = rt(BOOT)
    assert 'SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"' in text
    assert 'DEFAULT_WORK="$(cd -- "$SCRIPT_DIR/../.." && pwd -P)"' in text
    assert 'WORK="${WORK:-$DEFAULT_WORK}"' in text
    assert 'WORK="${WORK:-$HOME/v31_mt5_40usd}"' not in text


def test_bootstrap_can_recreate_pinned_venv_after_clean_clone():
    text = rt(BOOT)
    for tok in [
        'Create pinned V45 Python environment',
        '-m venv',
        'numpy==2.3.5',
        'pandas==2.2.3',
        'scikit-learn==1.8.0',
        'assert numpy.__version__=="2.3.5"',
    ]:
        assert tok in text, tok


def test_recovery_preserves_exact_parent_sha_gate():
    text = rt(RECOVER)
    assert 'V38_PARENT_SOURCE_SHA' in text
    assert 'V45_SOURCE_SHA' in text
    assert 'RECOVERED FROM INSTALLED V45 PASS' in text
    assert 'reverse recovery did not reproduce accepted V38 parent exactly' in text


def test_recovery_is_exact_inverse_of_v45_validation_only_changes():
    text = rt(RECOVER)
    for tok in [
        'v45_multiyear_single_run_validation_v1',
        'v38_fast_harvest_lab_v1',
        'InpV34WriteIntraTradeTelemetry = false;',
        'InpV34WriteIntraTradeTelemetry = true;',
        'InpV38WriteM1FastTelemetry = false;',
        'InpV38WriteM1FastTelemetry = true;',
        'V45_MULTIYEAR_VALIDATION START',
        'V38_FAST_HARVEST_LAB START',
    ]:
        assert tok in text, tok


def test_recovery_does_not_weaken_safety_or_live_guards():
    text = rt(RECOVER)
    assert 'LIVE-MONEY' not in text
    assert 'REAL-MONEY LIVE TRADING remains FORBIDDEN' in text
    assert 'base.run_mt5_once' in text
    assert 'base.build_source' in text


def _run_without_pytest():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print(f"V45 clean-clone recovery static tests PASS count={len(tests)}")


if __name__ == "__main__":
    _run_without_pytest()
