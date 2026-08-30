#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v61_profit_ratchet_m5_refinement_screen_source_fixed.py"
V63_ROOT = r"mt5_quant\\v63_profit_quality_risk_zone"
EXPERT_NAME = "V63ProfitQualityRiskZoneScreen"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parent = load(PARENT, "v61_directional_screen_for_v63")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V63 screen {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


def transform() -> str:
    text = parent.transform()
    text = replace_once(text, '#property version   "61.00"', '#property version   "63.01"', "version")
    text = text.replace("V61", "V63").replace("v61", "v63")
    text = text.replace(r"mt5_quant\\v63_profit_ratchet_m5_refinement", V63_ROOT)
    text = replace_once(text, "input long   InpV63Magic = 610061;", "input long   InpV63Magic = 630063;", "magic")
    validate(text)
    return text


def validate(text: str) -> None:
    required = (
        V63_ROOT,
        "InpV63ScreenOnly = true",
        "V63_DIRECTIONAL_SCREEN_ONLY",
        "V63BuildFeatures(f)",
        "V63SelectDirection(f,why)",
        "V63Append(V63_EVAL,row)",
        "datetime bar=iTime(_Symbol,PERIOD_M15,0)",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V63 screen required token missing: {token}")

    eval_start = text.index("void V63EvaluateBar()")
    eval_end = text.index("int OnInit()", eval_start)
    eval_body = text[eval_start:eval_end]
    for token in (
        "V63BuildStopTarget(",
        "V63StartShadow(",
        "OrderCalcMargin(",
        "V63OrderPreflight(",
        "g_trade.Buy(",
        "g_trade.Sell(",
    ):
        if token in eval_body:
            raise RuntimeError(f"V63 directional screen execution token leaked into evaluate: {token}")

    tick_start = text.index("void OnTick()")
    tick_end = text.index("void OnTradeTransaction", tick_start)
    tick_body = text[tick_start:tick_end]
    for token in (
        "V63UpdateShadow(",
        "V63ManageProfitRatchet(",
        "V63MaybeSoftLossCut(",
        "V63OwnedPosition(",
    ):
        if token in tick_body:
            raise RuntimeError(f"V63 directional screen stateful token leaked into OnTick: {token}")


def build(output: Path) -> str:
    text = transform().replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = sha256(output)
    print(f"V63_SCREEN_SOURCE_SHA256={digest}")
    print(f"V63_SCREEN_SOURCE_PATH={output}")
    print(f"V63_SCREEN_FILE_COMMON_ROOT={V63_ROOT}")
    print("V63_DIRECTIONAL_SCREEN_ONLY=1")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
