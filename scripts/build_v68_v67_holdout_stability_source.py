#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v67_post_zone_reclaim_quality_source.py"
V67_ROOT = r"mt5_quant\\v67_post_zone_reclaim_quality"
V68_ROOT = r"mt5_quant\\v68_v67_holdout_stability"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parent = load(PARENT, "v67_parent_for_v68")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V68 {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


def transform(allowed_direction: int) -> str:
    if allowed_direction not in (-1, 1):
        raise ValueError("allowed_direction must be -1 or 1")
    text = parent.transform(allowed_direction)
    text = replace_once(text, '#property version   "67.00"', '#property version   "68.00"', "version")
    text = replace_once(text, "input long   InpV64Magic = 670067;", "input long   InpV64Magic = 680068;", "magic")
    nroot = text.count(V67_ROOT)
    if nroot < 1:
        raise RuntimeError("V68 inherited V67 FILE_COMMON root missing")
    text = text.replace(V67_ROOT, V68_ROOT)
    text = text.replace("V67 RECLAIM L", "V68 HOLDOUT L")
    text = text.replace("V67 RECLAIM S", "V68 HOLDOUT S")
    validate(text, allowed_direction)
    assert_strategy_equivalence(text, allowed_direction)
    return text


def normalize_v68_to_v67(text: str) -> str:
    out = text.replace('#property version   "68.00"', '#property version   "67.00"')
    out = out.replace("input long   InpV64Magic = 680068;", "input long   InpV64Magic = 670067;")
    out = out.replace(V68_ROOT, V67_ROOT)
    out = out.replace("V68 HOLDOUT L", "V67 RECLAIM L")
    out = out.replace("V68 HOLDOUT S", "V67 RECLAIM S")
    return out


def assert_strategy_equivalence(v68_text: str, allowed_direction: int) -> None:
    expected = parent.transform(allowed_direction)
    actual = normalize_v68_to_v67(v68_text)
    if actual != expected:
        raise RuntimeError("V68 decision logic drifted from V67 after observability normalization")


def validate(text: str, allowed_direction: int) -> None:
    required = (
        '#property version   "68.00"',
        V68_ROOT,
        "InpV64Magic = 680068",
        "InpV64FixedLot = 0.01",
        "InpV64MinStopRiskCash = 0.85",
        "InpV64MaxStopRiskCash = 1.10",
        "InpV64EmergencyLossCash = 1.20",
        "InpV64PrimaryTargetCash = 3.50",
        "InpV64MinRiskSpreadRatio = 4.0",
        "InpV67PenetrationRiskCash = 0.92",
        "InpV67ConfirmValidityMinutes = 5",
        "MICRO_ENTRY_ZONE_TOUCH",
        "MICRO_ENTRY_PENETRATION",
        "POST_ZONE_REVERSAL_CONFIRM",
        "POST_ZONE_ENTRY_READY",
        f"InpV64AllowedDirection = {allowed_direction}",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V68 generated source missing token: {token}")
    if V67_ROOT in text:
        raise RuntimeError("V68 stale V67 FILE_COMMON root remains")
    if "LongToString(" in text:
        raise RuntimeError("V68 generated source contains unsupported LongToString")


def build(output: Path, allowed_direction: int) -> str:
    text = transform(allowed_direction).replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = sha256(output)
    print(f"V68_SOURCE_SHA256={digest}")
    print(f"V68_SOURCE_PATH={output}")
    print(f"V68_ALLOWED_DIRECTION={allowed_direction}")
    print("V68_V67_DECISION_LOGIC_EQUIVALENT=1")
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
