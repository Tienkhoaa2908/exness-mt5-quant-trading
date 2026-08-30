#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v61_profit_ratchet_m5_refinement_source.py"

LEGACY_ROOT = r"mt5_quant\\v61_small_loss_cash_target"
CANONICAL_ROOT = r"mt5_quant\\v61_profit_ratchet_m5_refinement"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parent = load(PARENT, "v61_parent_for_file_common_fix")
EXPERT_NAME = parent.EXPERT_NAME
FIXED_LOT = parent.FIXED_LOT
MAGIC = parent.MAGIC


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def transform() -> str:
    text = parent.transform()
    count = text.count(LEGACY_ROOT)
    if count < 5:
        raise RuntimeError(
            f"V61 FILE_COMMON legacy root drifted expected_at_least=5 actual={count}"
        )
    text = text.replace(LEGACY_ROOT, CANONICAL_ROOT)
    parent.validate(text)
    validate(text)
    return text


def validate(text: str) -> None:
    required = (
        CANONICAL_ROOT,
        CANONICAL_ROOT + r"\\V61_ENTRY_EVAL.csv",
        CANONICAL_ROOT + r"\\V61_EVENTS.csv",
        CANONICAL_ROOT + r"\\V61_DEALS.csv",
        CANONICAL_ROOT + r"\\V61_SHADOW_RR.csv",
        CANONICAL_ROOT + r"\\V61_STATUS.txt",
        "InpV61FixedLot = 0.01",
        "InpV61PrimaryTargetCash = 3.00",
        "InpV61ProfitArmCash = 2.00",
        "InpV61ProfitLockCash = 1.00",
        "InpV61MinStopRiskCash = 0.75",
        "InpV61MaxStopRiskCash = 1.25",
        "CopyRates(_Symbol,PERIOD_M5,1,180,m5)",
        "OrderCheck(req,chk)",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V61 fixed required token missing: {token}")
    if LEGACY_ROOT in text:
        raise RuntimeError("V61 fixed source still contains legacy FILE_COMMON root")


def build(output: Path) -> str:
    text = transform().replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = sha256(output)
    print(f"V61_FIXED_SOURCE_SHA256={digest}")
    print(f"V61_FIXED_SOURCE_PATH={output}")
    print(f"V61_FILE_COMMON_ROOT={CANONICAL_ROOT}")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
