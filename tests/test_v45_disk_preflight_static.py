#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / "runtime" / "v45_multiyear_validation" / "PREPARE_V45_DISK.py"
BOOT = ROOT / "runtime" / "v45_multiyear_validation" / "BOOTSTRAP_V45_MULTIYEAR_ONE_SHOT_GIT_BASH.sh"


def rt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_disk_gate_is_split_between_terminal_and_tester_volumes():
    text = rt(PREP)
    assert "MIN_TERMINAL_FREE_GIB = 2.0" in text
    assert "MIN_TESTER_FREE_GIB = 12.0" in text
    assert "TESTER_STORAGE_PHYSICAL" in text
    assert "shutil.disk_usage" in text
    assert "V45_DISK_PREFLIGHT_PASS" in text


def test_cleanup_is_limited_to_recomputable_tester_cache():
    text = rt(PREP)
    assert 'glob("Agent-127.0.0.1-*/bases")' in text
    assert '"Manager" / "temp"' in text
    assert '"Tester" / "cache"' in text
    assert "shutil.rmtree(path)" in text
    assert "rmtree(data)" not in text
    assert "rmtree(appdata)" not in text


def test_disk_prep_never_launches_mt5_or_metaeditor():
    text = rt(PREP)
    assert "terminal64.exe" in text and "metaeditor64.exe" in text and "metatester64.exe" in text
    assert "subprocess.run([str(TERMINAL" not in text
    assert "/config:" not in text
    assert "/compile:" not in text


def test_bootstrap_runs_migration_then_disk_prep_then_v45_runner():
    text = rt(BOOT)
    move_call = '"$PY" "$(cygpath -w "$MOVE")"'
    prep_call = '"$PY" "$(cygpath -w "$PREP")"'
    runner_call = '"$PY" "$(cygpath -w "$RUNNER")"'
    assert move_call in text and prep_call in text and runner_call in text
    assert text.index(move_call) < text.index(prep_call) < text.index(runner_call)


def _run_without_pytest():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print(f"V45 disk preflight static tests PASS count={len(tests)}")


if __name__ == "__main__":
    _run_without_pytest()
