#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v63_profit_quality_risk_zone_screen_source.py"
V64_ROOT = r"mt5_quant\\v64_microstructure_trigger_shadow"
EXPERT_NAME = "V64MicrostructureTriggerShadowScreen"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parent = load(PARENT, "v63_screen_for_v64")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V64 screen {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


def transform() -> str:
    text = parent.transform()
    text = replace_once(text, '#property version   "63.01"', '#property version   "64.01"', "version")
    text = text.replace("V63", "V64").replace("v63", "v64")
    text = text.replace(r"mt5_quant\\v64_profit_quality_risk_zone", V64_ROOT)
    text = replace_once(text, "input long   InpV64Magic = 630063;", "input long   InpV64Magic = 640064;", "magic")
    validate(text)
    return text


def validate(text: str) -> None:
    required = (
        V64_ROOT,
        "InpV64ScreenOnly = true",
        "V64_DIRECTIONAL_SCREEN_ONLY",
        "V64BuildFeatures(f)",
        "V64SelectDirection(f,why)",
        "V64Append(V64_EVAL,row)",
        "datetime bar=iTime(_Symbol,PERIOD_M15,0)",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V64 screen required token missing: {token}")
    eval_start = text.index("void V64EvaluateBar()")
    eval_end = text.index("int OnInit()", eval_start)
    eval_body = text[eval_start:eval_end]
    for token in ("V64BuildStopTarget(", "OrderCalcMargin(", "V64OrderPreflight(", "g_trade.Buy(", "g_trade.Sell("):
        if token in eval_body:
            raise RuntimeError(f"V64 directional screen execution token leaked: {token}")


def build(output: Path) -> str:
    text = transform().replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = sha256(output)
    print(f"V64_SCREEN_SOURCE_SHA256={digest}")
    print(f"V64_SCREEN_SOURCE_PATH={output}")
    print(f"V64_SCREEN_FILE_COMMON_ROOT={V64_ROOT}")
    print("V64_DIRECTIONAL_SCREEN_ONLY=1")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
