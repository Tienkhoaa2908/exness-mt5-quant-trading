#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v60_small_loss_cash_target_source.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v60 = load(PARENT, "v60_parent_for_screen")
EXPERT_NAME = "V60SmallLossCashTargetScreen"


def build(output: Path) -> str:
    text = v60.transform()
    old = "input bool   InpV60ScreenOnly = false;"
    if text.count(old) != 1:
        raise RuntimeError(f"V60 screen flag drifted count={text.count(old)}")
    text = text.replace(old, "input bool   InpV60ScreenOnly = true;", 1)
    text = text.replace("V60 small-loss cash-target research - TESTER ONLY", "V60 small-loss cash-target SCREEN - TESTER ONLY")
    text = text.replace("\n", "\r\n")
    v60.validate(text)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = v60.v59.sha256(output)
    print(f"V60 screen source built sha256={digest} path={output}")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
