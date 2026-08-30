#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_v66_post_bos_cash_zone_source.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


base = load(BASE, "v66_base_builder_for_fixed")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V66 fixed {label} expected=1 actual={n}")
    return text.replace(old, new, 1)


def transform(allowed_direction: int) -> str:
    text = base.transform(allowed_direction)
    text = replace_once(
        text,
        "const double current_entry,const double current_risk,",
        "const double current_risk,",
        "unused arm parameter",
    )
    text = replace_once(
        text,
        "V66ArmMicroPending(d,arch,micro_stop,score,entry,risk_cash,spread_cash,ratio);",
        "V66ArmMicroPending(d,arch,micro_stop,score,risk_cash,spread_cash,ratio);",
        "arm call",
    )
    text = replace_once(
        text,
        "bool feasible_now=V64BuildMicroStopTarget(d,entry,micro_stop,stop,tp,risk_cash,risk_pct,",
        "V64BuildMicroStopTarget(d,entry,micro_stop,stop,tp,risk_cash,risk_pct,",
        "unused feasibility local",
    )
    if "feasible_now" in text or "current_entry" in text:
        raise RuntimeError("V66 fixed builder still contains removed unused identifiers")
    return text


def build(output: Path, allowed_direction: int) -> str:
    text = transform(allowed_direction).replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = base.sha256(output)
    print(f"V66_FIXED_SOURCE_SHA256={digest}")
    print(f"V66_FIXED_SOURCE_PATH={output}")
    print(f"V66_ALLOWED_DIRECTION={allowed_direction}")
    print(f"V66_FILE_COMMON_ROOT={base.V66_ROOT}")
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
