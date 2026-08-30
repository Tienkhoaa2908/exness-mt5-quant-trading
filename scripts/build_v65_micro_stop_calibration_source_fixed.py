#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_v65_micro_stop_calibration_source.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


base = load(BASE, "v65_base_builder_for_fixed_root")
_original_replace_once = base.replace_once


def replace_compat(text: str, old: str, new: str, label: str) -> str:
    if label == "FILE_COMMON root":
        n = text.count(old)
        if n < 1:
            raise RuntimeError("V65 FILE_COMMON root missing before normalization")
        out = text.replace(old, new)
        if old in out:
            raise RuntimeError("V65 stale FILE_COMMON root remains after normalization")
        return out
    return _original_replace_once(text, old, new, label)


base.replace_once = replace_compat


def transform(allowed_direction: int) -> str:
    text = base.transform(allowed_direction)
    stale = r"mt5_quant\\v64_microstructure_trigger_shadow"
    if stale in text:
        raise RuntimeError("V65 fixed builder still contains V64 FILE_COMMON root")
    if base.V65_ROOT not in text:
        raise RuntimeError("V65 fixed builder missing V65 FILE_COMMON root")
    return text


def build(output: Path, allowed_direction: int) -> str:
    text = transform(allowed_direction).replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = base.sha256(output)
    print(f"V65_FIXED_SOURCE_SHA256={digest}")
    print(f"V65_FIXED_SOURCE_PATH={output}")
    print(f"V65_ALLOWED_DIRECTION={allowed_direction}")
    print(f"V65_FILE_COMMON_ROOT={base.V65_ROOT}")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--allowed-direction", required=True, type=int, choices=(-1, 1))
    args = ap.parse_args()
    build(args.output, args.allowed_direction)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
