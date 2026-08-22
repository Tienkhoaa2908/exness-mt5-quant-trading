#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOVE = ROOT / "runtime" / "v45_multiyear_validation" / "MOVE_V45_TESTER_STORAGE_TO_D.py"
BOOT = ROOT / "runtime" / "v45_multiyear_validation" / "BOOTSTRAP_V45_MULTIYEAR_ONE_SHOT_GIT_BASH.sh"


def rt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_default_target_is_d_drive_and_terminal_id_scoped():
    text = rt(MOVE)
    assert r'D:\MT5TesterCache' in text
    assert 'terminal_id = data.name' in text
    assert 'target = TARGET_ROOT / terminal_id' in text


def test_migration_uses_verified_copy_then_junction_then_backup_delete():
    text = rt(MOVE)
    assert 'robocopy.exe' in text
    assert 'copy verification failed' in text
    assert 'source.rename(backup)' in text
    assert '"mklink", "/J"' in text
    assert 'junction verification failed' in text
    assert 'shutil.rmtree(backup)' in text


def test_migration_rolls_back_if_junction_creation_fails():
    text = rt(MOVE)
    assert 'if renamed and backup.exists() and not source.exists()' in text
    assert 'backup.rename(source)' in text


def test_migration_never_moves_terminal_broker_history_or_project_state():
    text = rt(MOVE)
    assert 'appdata / "MetaQuotes" / "Tester" / terminal_id' in text
    assert 'MetaQuotes" / "Terminal" / terminal_id' not in text
    assert 'v30_ml_dl_feature_lake_state.csv' not in text
    assert 'OUTPUT_V45' not in text


def test_migration_never_launches_mt5_or_metaeditor():
    text = rt(MOVE)
    assert 'terminal64.exe' in text and 'metaeditor64.exe' in text and 'metatester64.exe' in text
    assert '/config:' not in text and '/compile:' not in text


def test_bootstrap_invokes_migration_before_disk_preflight():
    text = rt(BOOT)
    assert 'MOVE_V45_TESTER_STORAGE_TO_D.py' in text
    assert text.index('"$PY" "$(cygpath -w "$MOVE")"') < text.index('"$PY" "$(cygpath -w "$PREP")"')


def _run_without_pytest():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print(f"V45 tester-storage migration static tests PASS count={len(tests)}")


if __name__ == "__main__":
    _run_without_pytest()
