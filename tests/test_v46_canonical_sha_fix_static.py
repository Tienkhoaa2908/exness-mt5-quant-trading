#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_v46_expert_breadth_source_canonical.py"
RUNNER = ROOT / "runtime" / "v46_expert_breadth" / "RUN_V46_EXPERT_BREADTH_ONE_SHOT_CANONICAL.py"
BOOT = ROOT / "runtime" / "v46_expert_breadth" / "BOOTSTRAP_V46_CANONICAL_GIT_BASH.sh"
CORRECT = "6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3"
WRONG = "3695095d80fd81847bbcc4e4ae0902c4ddbf713fe0ac9ab8549f1c19d77c1f13"


def rt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_correct_sha_is_hard_gated_in_canonical_builder_and_runner():
    assert CORRECT in rt(BUILDER)
    assert CORRECT in rt(RUNNER)
    assert WRONG in rt(BUILDER)
    assert WRONG in rt(RUNNER)


def test_canonical_builder_preserves_v45_parent_identity():
    text = rt(BUILDER)
    assert "36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2" in text
    assert "EXPECTED_PARENT_SHA" in text


def test_canonical_runner_preserves_v38_v45_chain_and_uses_canonical_builder():
    text = rt(RUNNER)
    assert "4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12" in text
    assert "36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2" in text
    assert "build_v46_expert_breadth_source_canonical.py" in text
    assert "mod.V46_SOURCE_SHA = CORRECT_V46_SHA" in text
    assert "mod.BUILDER = CANONICAL_BUILDER" in text


def test_bootstrap_uses_canonical_runner_before_any_mt5_call():
    text = rt(BOOT)
    assert "RUN_V46_EXPERT_BREADTH_ONE_SHOT_CANONICAL.py" in text
    assert "test_v46_canonical_sha_fix_static.py" in text
    assert "MOVE_V45_TESTER_STORAGE_TO_D.py" in text
    assert "PREPARE_V45_DISK.py" in text
    assert "git clean" not in text


def _run_without_pytest():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn(); print("PASS", fn.__name__)
    print(f"V46 canonical SHA-fix tests PASS count={len(tests)}")


if __name__ == "__main__":
    _run_without_pytest()
