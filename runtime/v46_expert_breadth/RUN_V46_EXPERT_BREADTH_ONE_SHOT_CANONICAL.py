#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BASE_RUNNER = HERE / "RUN_V46_EXPERT_BREADTH_ONE_SHOT.py"
CANONICAL_BUILDER = REPO / "scripts" / "build_v46_expert_breadth_source_canonical.py"
CORRECT_V46_SHA = "6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3"
ORIGINAL_MISFROZEN_SHA = "3695095d80fd81847bbcc4e4ae0902c4ddbf713fe0ac9ab8549f1c19d77c1f13"
EXPECTED_V45_SHA = "36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2"
EXPECTED_V38_SHA = "4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12"


def load_base():
    spec = importlib.util.spec_from_file_location("v46_runner_base", BASE_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load V46 runner: {BASE_RUNNER}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    mod = load_base()
    if mod.V45_SOURCE_SHA != EXPECTED_V45_SHA or mod.V38_PARENT_SOURCE_SHA != EXPECTED_V38_SHA:
        raise RuntimeError("V46 upstream provenance constants changed unexpectedly")
    if mod.V46_SOURCE_SHA not in (ORIGINAL_MISFROZEN_SHA, CORRECT_V46_SHA):
        raise RuntimeError(f"unexpected V46 source SHA in base runner: {mod.V46_SOURCE_SHA}")
    if not CANONICAL_BUILDER.is_file():
        raise RuntimeError(f"canonical V46 builder missing: {CANONICAL_BUILDER}")
    mod.V46_SOURCE_SHA = CORRECT_V46_SHA
    mod.BUILDER = CANONICAL_BUILDER
    print(f"V46_CANONICAL_SOURCE_SHA={CORRECT_V46_SHA}")
    print("V46_SHA_FIX_PROVENANCE=accepted_v45_zip_reproduction+windows_match")
    return mod.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}")
        raise
