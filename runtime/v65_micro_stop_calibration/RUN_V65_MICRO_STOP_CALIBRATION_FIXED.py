#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE / "RUN_V65_MICRO_STOP_CALIBRATION.py"
REPO = HERE.parents[1]
FIXED_BUILDER = REPO / "scripts" / "build_v65_micro_stop_calibration_source_fixed.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    runner = load(ORIGINAL, "v65_original_runner_with_fixed_builder")
    runner.BUILDER = FIXED_BUILDER
    print(f"V65_FIXED_BUILDER={FIXED_BUILDER}")
    return runner.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}")
        raise
