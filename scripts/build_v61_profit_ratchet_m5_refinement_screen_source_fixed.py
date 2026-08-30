#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
REAL_BUILDER = HERE / "build_v61_profit_ratchet_m5_refinement_source_fixed.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


real = load(REAL_BUILDER, "v61_fixed_real_for_directional_screen")
EXPERT_NAME = "V61ProfitRatchetM5RefinementScreen"

SCREEN_EVALUATE = r'''
void V61EvaluateBar()
{
   // V61_DIRECTIONAL_SCREEN_ONLY:
   // Window selection must observe every M15 bar and must not run execution
   // feasibility, M5 stop refinement, shadow lifecycle, margin, spread or orders.
   V61Features f;
   bool ready=V61BuildFeatures(f);
   string why=(ready ? "" : "feature_not_ready");
   int d=(ready ? V61SelectDirection(f,why) : 0);
   string reject=(d==0 ? why : "screen_direction_only");

   string row=TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+
      IntegerToString(f.h4_trend)+","+IntegerToString(f.h1_trend)+","+IntegerToString(f.m15_trend)+","+
      IntegerToString(f.structure_dir)+","+IntegerToString(f.bos_choch_dir)+","+IntegerToString(f.fvg_dir)+","+
      IntegerToString(f.liquidity_sweep_dir)+","+IntegerToString(f.order_block_retest_dir)+","+
      IntegerToString(f.pullback_dir)+","+IntegerToString(f.di_dir)+","+IntegerToString(f.macd_dir)+","+
      IntegerToString(f.location_dir)+","+DoubleToString(f.atr15,5)+","+DoubleToString(f.rsi2,3)+","+
      DoubleToString(f.rsi14,3)+","+DoubleToString(f.adx,3)+","+DoubleToString(f.plus_di,3)+","+
      DoubleToString(f.minus_di,3)+","+DoubleToString(f.macd,6)+","+DoubleToString(f.macd_slope,6)+","+
      DoubleToString(f.distance_ema_atr,4)+","+DoubleToString(f.range_location,4)+","+
      IntegerToString(f.long_score)+","+IntegerToString(f.short_score)+","+IntegerToString(d)+","+why+","+
      "0,0,0,0,0,0,0,0,"+IntegerToString(0)+","+reject+",screen,1";
   V61Append(V61_EVAL,row);
}
'''

SCREEN_ON_TICK = r'''
void OnTick()
{
   datetime bar=iTime(_Symbol,PERIOD_M15,0);
   if(bar<=0 || bar==g_last_m15_bar) return;
   g_last_m15_bar=bar;
   V61EvaluateBar();
}
'''


def replace_function(text: str, start_sig: str, next_sig: str, replacement: str, label: str) -> str:
    start = text.find(start_sig)
    if start < 0:
        raise RuntimeError(f"V61 fixed screen missing {label} start: {start_sig}")
    end = text.find(next_sig, start + len(start_sig))
    if end < 0:
        raise RuntimeError(f"V61 fixed screen missing {label} next: {next_sig}")
    return text[:start] + replacement.strip() + "\n\n" + text[end:]


def transform() -> str:
    text = real.transform()
    old = "input bool   InpV61ScreenOnly = false;"
    new = "input bool   InpV61ScreenOnly = true;"
    if text.count(old) != 1:
        raise RuntimeError(f"V61 fixed screen default drifted count={text.count(old)}")
    text = text.replace(old, new, 1)

    # Screen is deliberately not the execution EA with a boolean flipped. It has a
    # dedicated evaluation path so screen coverage cannot be throttled by shadow or
    # execution state and window selection cannot depend on Model=2 broker geometry.
    text = replace_function(text, "void V61EvaluateBar()", "int OnInit()", SCREEN_EVALUATE, "evaluate")
    text = replace_function(text, "void OnTick()", "void OnTradeTransaction", SCREEN_ON_TICK, "OnTick")

    real.validate(text)
    validate_screen(text)
    return text


def validate_screen(text: str) -> None:
    required = (
        "InpV61ScreenOnly = true",
        "V61_DIRECTIONAL_SCREEN_ONLY",
        "screen_direction_only",
        "V61BuildFeatures(f)",
        "V61SelectDirection(f,why)",
        "V61Append(V61_EVAL,row)",
        "datetime bar=iTime(_Symbol,PERIOD_M15,0)",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V61 directional screen required token missing: {token}")

    eval_start = text.index("void V61EvaluateBar()")
    eval_end = text.index("int OnInit()", eval_start)
    eval_body = text[eval_start:eval_end]
    for token in (
        "V61BuildStopTarget(",
        "V61StartShadow(",
        "OrderCalcMargin(",
        "V61OrderPreflight(",
        "g_trade.Buy(",
        "g_trade.Sell(",
    ):
        if token in eval_body:
            raise RuntimeError(f"V61 directional screen execution token leaked into evaluate: {token}")

    tick_start = text.index("void OnTick()")
    tick_end = text.index("void OnTradeTransaction", tick_start)
    tick_body = text[tick_start:tick_end]
    for token in (
        "V61UpdateShadow(",
        "V61ManageProfitRatchet(",
        "V61MaybeSoftLossCut(",
        "V61OwnedPosition(",
    ):
        if token in tick_body:
            raise RuntimeError(f"V61 directional screen stateful token leaked into OnTick: {token}")


def build(output: Path) -> str:
    text = transform()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text.replace("\n", "\r\n"), encoding="utf-8", newline="")
    digest = real.sha256(output)
    print(f"V61_FIXED_SCREEN_SOURCE_SHA256={digest}")
    print(f"V61_FIXED_SCREEN_SOURCE_PATH={output}")
    print("V61_DIRECTIONAL_SCREEN_ONLY=1")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
