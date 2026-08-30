#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILDER = HERE / "build_v61_profit_ratchet_m5_refinement_source.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


base = load(BUILDER, "v61_base_for_screen")
EXPERT_NAME = "V61ProfitRatchetM5RefinementScreen"


def build(output: Path) -> str:
    text = base.transform()
    old = "input bool   InpV61ScreenOnly = false;"
    if text.count(old) != 1:
        raise RuntimeError(f"V61 screen flag drifted actual={text.count(old)}")
    text = text.replace(old, "input bool   InpV61ScreenOnly = true;", 1)
    base.validate(text)
    text = text.replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = base.sha256(output)
    print(f"V61 screen source built sha256={digest} path={output}")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
