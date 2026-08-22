#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "build_v46_expert_breadth_source.py"
CORRECT_V46_SHA = "6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3"
ORIGINAL_MISFROZEN_SHA = "3695095d80fd81847bbcc4e4ae0902c4ddbf713fe0ac9ab8549f1c19d77c1f13"
EXPECTED_V45_PARENT_SHA = "36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2"


def load_base():
    spec = importlib.util.spec_from_file_location("v46_builder_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load V46 builder: {BASE_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    mod = load_base()
    if mod.EXPECTED_PARENT_SHA != EXPECTED_V45_PARENT_SHA:
        raise RuntimeError("V46 builder parent provenance changed unexpectedly")
    if mod.EXPECTED_OUTPUT_SHA not in (ORIGINAL_MISFROZEN_SHA, CORRECT_V46_SHA):
        raise RuntimeError(f"unexpected V46 frozen SHA in base builder: {mod.EXPECTED_OUTPUT_SHA}")
    mod.EXPECTED_OUTPUT_SHA = CORRECT_V46_SHA
    print(f"V46_CANONICAL_FROZEN_SHA={CORRECT_V46_SHA}")
    return mod.main()


if __name__ == "__main__":
    raise SystemExit(main())
