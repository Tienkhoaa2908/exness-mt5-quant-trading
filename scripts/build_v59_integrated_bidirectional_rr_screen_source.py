#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_BUILDER = HERE / "build_v59_integrated_bidirectional_rr_source.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("v59_base_builder", BASE_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {BASE_BUILDER}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build(output: Path) -> str:
    mod = load_builder()
    old = "input bool   InpV59ScreenOnly = false;"
    new = "input bool   InpV59ScreenOnly = true;"
    if mod.MQL.count(old) != 1:
        raise RuntimeError("V59 screen-only input marker drifted")
    text = mod.MQL.replace(old, new, 1).replace("\n", "\r\n")
    mod.validate(text)
    if "InpV59ScreenOnly = true" not in text:
        raise RuntimeError("V59 screen-only transform failed")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = mod.sha256(output)
    print(f"V59 screen source built sha256={digest} path={output}")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
