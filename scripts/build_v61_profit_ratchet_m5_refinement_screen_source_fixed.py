#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
REAL_BUILDER = HERE / "build_v61_profit_ratchet_m5_refinement_source_fixed.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


real = load(REAL_BUILDER, "v61_fixed_real_for_screen")
EXPERT_NAME = "V61ProfitRatchetM5RefinementScreen"


def build(output: Path) -> str:
    text = real.transform()
    old = "input bool   InpV61ScreenOnly = false;"
    new = "input bool   InpV61ScreenOnly = true;"
    if text.count(old) != 1:
        raise RuntimeError(f"V61 fixed screen default drifted count={text.count(old)}")
    text = text.replace(old, new, 1)
    real.validate(text)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text.replace("\n", "\r\n"), encoding="utf-8", newline="")
    digest = real.sha256(output)
    print(f"V61_FIXED_SCREEN_SOURCE_SHA256={digest}")
    print(f"V61_FIXED_SCREEN_SOURCE_PATH={output}")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
