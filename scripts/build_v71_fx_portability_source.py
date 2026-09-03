#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v69_confirm_separation_retest_source.py"
V69_ROOT = r"mt5_quant\\v69_confirm_separation_retest"
V71_ROOT = r"mt5_quant\\v71_fx_portability"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parent = load(PARENT, "v69_parent_for_v71_fx")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V71 {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


def transform() -> str:
    text = parent.transform(1)
    text = replace_once(text, '#property version   "69.00"', '#property version   "71.00"', "version")
    text = replace_once(text, "input long   InpV64Magic = 690069;", "input long   InpV64Magic = 710071;", "magic")
    if V69_ROOT not in text:
        raise RuntimeError("V71 inherited V69 root missing")
    text = text.replace(V69_ROOT, V71_ROOT)
    text = text.replace("V69 SEP RETEST L", "V71 FX PORTABILITY L")
    validate(text)
    assert_v69_strategy_equivalence(text)
    return text


def normalize_to_v69(text: str) -> str:
    out = text.replace('#property version   "71.00"', '#property version   "69.00"')
    out = out.replace("input long   InpV64Magic = 710071;", "input long   InpV64Magic = 690069;")
    out = out.replace(V71_ROOT, V69_ROOT)
    out = out.replace("V71 FX PORTABILITY L", "V69 SEP RETEST L")
    return out


def assert_v69_strategy_equivalence(text: str) -> None:
    expected = parent.transform(1)
    actual = normalize_to_v69(text)
    if actual != expected:
        raise RuntimeError("V71 strategy semantics drifted from frozen V69 LONG after metadata normalization")


def validate(text: str) -> None:
    required = (
        '#property version   "71.00"',
        V71_ROOT,
        "InpV64Magic = 710071",
        "InpV64AllowedDirection = 1",
        "InpV64FixedLot = 0.01",
        "InpV64MinStopRiskCash = 0.85",
        "InpV64MaxStopRiskCash = 1.10",
        "InpV64EmergencyLossCash = 1.20",
        "InpV64PrimaryTargetCash = 3.50",
        "InpV64MinRiskSpreadRatio = 4.0",
        "InpV69MinConfirmSeparationRiskCash = 1.30",
        "InpV69MinConfirmAgeSeconds = 30",
        "POST_CONFIRM_SEPARATION",
        "POST_CONFIRM_RETEST_READY",
        "POST_CONFIRM_ENTRY_READY",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V71 source missing token: {token}")
    if V69_ROOT in text:
        raise RuntimeError("V71 stale V69 FILE_COMMON root remains")


def build(output: Path) -> None:
    text = transform().replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    print(f"V71_SOURCE_PATH={output}")
    print("V71_V69_LONG_STRATEGY_EQUIVALENT=1")
    print("V71_LONG_ONLY=1")
    print("V71_SHORT_ENABLED=0")
    print("REAL_MONEY_AUTHORIZED=0")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
