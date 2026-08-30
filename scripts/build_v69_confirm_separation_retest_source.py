#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v68_v67_holdout_stability_source.py"
V68_ROOT = r"mt5_quant\\v68_v67_holdout_stability"
V69_ROOT = r"mt5_quant\\v69_confirm_separation_retest"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parent = load(PARENT, "v68_parent_for_v69")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V69 {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


def transform(allowed_direction: int) -> str:
    if allowed_direction not in (-1, 1):
        raise ValueError("allowed_direction must be -1 or 1")

    text = parent.transform(allowed_direction)
    text = replace_once(text, '#property version   "68.00"', '#property version   "69.00"', "version")
    text = replace_once(text, "input long   InpV64Magic = 680068;", "input long   InpV64Magic = 690069;", "magic")

    nroot = text.count(V68_ROOT)
    if nroot < 1:
        raise RuntimeError("V69 inherited V68 FILE_COMMON root missing")
    text = text.replace(V68_ROOT, V69_ROOT)
    text = text.replace("V68 HOLDOUT L", "V69 SEP RETEST L")
    text = text.replace("V68 HOLDOUT S", "V69 SEP RETEST S")

    input_anchor = "input int    InpV67ConfirmValidityMinutes = 5;"
    input_block = input_anchor + "\n" + (
        "input double InpV69MinConfirmSeparationRiskCash = 1.30;\n"
        "input int    InpV69MinConfirmAgeSeconds = 30;"
    )
    text = replace_once(text, input_anchor, input_block, "inputs")

    global_anchor = "double g_v67_confirm_extreme=0.0;"
    global_block = global_anchor + "\n" + (
        "bool g_v69_post_confirm_separated=false;\n"
        "datetime g_v69_post_confirm_separated_at=0;\n"
        "double g_v69_max_post_confirm_risk=0.0;"
    )
    text = replace_once(text, global_anchor, global_block, "globals")

    reset_anchor = "   g_v67_confirm_extreme=0.0;\n}"
    reset_block = (
        "   g_v67_confirm_extreme=0.0;\n"
        "   g_v69_post_confirm_separated=false;\n"
        "   g_v69_post_confirm_separated_at=0;\n"
        "   g_v69_max_post_confirm_risk=0.0;\n"
        "}"
    )
    text = replace_once(text, reset_anchor, reset_block, "zone reset")

    adverse_reset_anchor = (
        "         g_v67_reversal_confirmed=false;\n"
        "         g_v67_reversal_confirmed_at=0;\n"
        "         V64PendingEvent(\"POST_ZONE_CONFIRM_RESET\",d,\"new_adverse_extreme_requires_fresh_reclaim\","
    )
    adverse_reset_block = (
        "         g_v67_reversal_confirmed=false;\n"
        "         g_v67_reversal_confirmed_at=0;\n"
        "         g_v69_post_confirm_separated=false;\n"
        "         g_v69_post_confirm_separated_at=0;\n"
        "         g_v69_max_post_confirm_risk=0.0;\n"
        "         V64PendingEvent(\"POST_ZONE_CONFIRM_RESET\",d,\"new_adverse_extreme_requires_fresh_reclaim\","
    )
    text = replace_once(text, adverse_reset_anchor, adverse_reset_block, "adverse reset")

    expiry_reset_anchor = (
        "      g_v67_reversal_confirmed=false;\n"
        "      g_v67_reversal_confirmed_at=0;\n"
        "      V64PendingEvent(\"POST_ZONE_CONFIRM_RESET\",d,\"reclaim_confirmation_expired\",risk_cash,spread_cash,ratio);"
    )
    expiry_reset_block = (
        "      g_v67_reversal_confirmed=false;\n"
        "      g_v67_reversal_confirmed_at=0;\n"
        "      g_v69_post_confirm_separated=false;\n"
        "      g_v69_post_confirm_separated_at=0;\n"
        "      g_v69_max_post_confirm_risk=0.0;\n"
        "      V64PendingEvent(\"POST_ZONE_CONFIRM_RESET\",d,\"reclaim_confirmation_expired\",risk_cash,spread_cash,ratio);"
    )
    text = replace_once(text, expiry_reset_anchor, expiry_reset_block, "expiry reset")

    confirm_anchor = (
        "      g_v67_reversal_confirmed=true;\n"
        "      g_v67_reversal_confirmed_at=TimeCurrent();\n"
        "      g_v67_confirm_extreme=g_v67_zone_extreme;\n"
        "      g_v66_micro_wait_reason=\"\";\n"
        "      V64PendingEvent(\"POST_ZONE_REVERSAL_CONFIRM\",d,confirm_detail,risk_cash,spread_cash,ratio);\n"
        "   }\n\n"
        "   double stop=0,tp=0,risk_pct=0,margin_cash=0,build_spread_points=0,build_spread_cash=0,build_ratio=0;string reject=\"\";"
    )
    confirm_block = (
        "      g_v67_reversal_confirmed=true;\n"
        "      g_v67_reversal_confirmed_at=TimeCurrent();\n"
        "      g_v67_confirm_extreme=g_v67_zone_extreme;\n"
        "      g_v69_post_confirm_separated=false;\n"
        "      g_v69_post_confirm_separated_at=0;\n"
        "      g_v69_max_post_confirm_risk=risk_cash;\n"
        "      g_v66_micro_wait_reason=\"\";\n"
        "      V64PendingEvent(\"POST_ZONE_REVERSAL_CONFIRM\",d,confirm_detail,risk_cash,spread_cash,ratio);\n"
        "      // V69: confirmation itself can never send an order. A favorable\n"
        "      // separation away from the fixed stop and a later retest are required.\n"
        "      return;\n"
        "   }\n\n"
        "   if(risk_cash>g_v69_max_post_confirm_risk)\n"
        "      g_v69_max_post_confirm_risk=risk_cash;\n\n"
        "   if(!g_v69_post_confirm_separated)\n"
        "   {\n"
        "      if(g_v69_max_post_confirm_risk<InpV69MinConfirmSeparationRiskCash-1e-9)\n"
        "      {\n"
        "         V66MicroWaitEvent(d,\"waiting_post_confirm_separation\",risk_cash,spread_cash,ratio);\n"
        "         return;\n"
        "      }\n"
        "      g_v69_post_confirm_separated=true;\n"
        "      g_v69_post_confirm_separated_at=TimeCurrent();\n"
        "      g_v66_micro_wait_reason=\"\";\n"
        "      V64PendingEvent(\"POST_CONFIRM_SEPARATION\",d,V64ArchName(g_v66_micro_arch),\n"
        "                      g_v69_max_post_confirm_risk,\n"
        "                      (double)(TimeCurrent()-g_v67_reversal_confirmed_at),ratio);\n"
        "      // The separation tick itself is not a retest.\n"
        "      return;\n"
        "   }\n\n"
        "   int confirm_age=(int)(TimeCurrent()-g_v67_reversal_confirmed_at);\n"
        "   if(confirm_age<InpV69MinConfirmAgeSeconds)\n"
        "   {\n"
        "      V66MicroWaitEvent(d,\"post_confirm_age_wait\",risk_cash,spread_cash,ratio);\n"
        "      return;\n"
        "   }\n"
        "   if(risk_cash>InpV64MaxStopRiskCash+1e-9)\n"
        "   {\n"
        "      V66MicroWaitEvent(d,\"separated_waiting_cash_zone_retest\",risk_cash,spread_cash,ratio);\n"
        "      return;\n"
        "   }\n"
        "   V64PendingEvent(\"POST_CONFIRM_RETEST_READY\",d,V64ArchName(g_v66_micro_arch),\n"
        "                   risk_cash,(double)confirm_age,g_v69_max_post_confirm_risk);\n\n"
        "   double stop=0,tp=0,risk_pct=0,margin_cash=0,build_spread_points=0,build_spread_cash=0,build_ratio=0;string reject=\"\";"
    )
    text = replace_once(text, confirm_anchor, confirm_block, "separation state machine")

    entry_ready_anchor = (
        "   V64PendingEvent(\"POST_ZONE_ENTRY_READY\",d,V64ArchName(g_v66_micro_arch),risk_cash,spread_cash,ratio);"
    )
    entry_ready_block = (
        "   V64PendingEvent(\"POST_CONFIRM_ENTRY_READY\",d,V64ArchName(g_v66_micro_arch),\n"
        "                   risk_cash,(double)(TimeCurrent()-g_v67_reversal_confirmed_at),\n"
        "                   g_v69_max_post_confirm_risk);\n"
        "   V64PendingEvent(\"POST_ZONE_ENTRY_READY\",d,V64ArchName(g_v66_micro_arch),risk_cash,spread_cash,ratio);"
    )
    text = replace_once(text, entry_ready_anchor, entry_ready_block, "entry ready telemetry")

    validate(text, allowed_direction)
    return text


def validate(text: str, allowed_direction: int) -> None:
    required = (
        '#property version   "69.00"',
        V69_ROOT,
        "InpV64Magic = 690069",
        "InpV64FixedLot = 0.01",
        "InpV64MinStopRiskCash = 0.85",
        "InpV64MaxStopRiskCash = 1.10",
        "InpV64EmergencyLossCash = 1.20",
        "InpV64PrimaryTargetCash = 3.50",
        "InpV69MinConfirmSeparationRiskCash = 1.30",
        "InpV69MinConfirmAgeSeconds = 30",
        "POST_CONFIRM_SEPARATION",
        "POST_CONFIRM_RETEST_READY",
        "POST_CONFIRM_ENTRY_READY",
        "waiting_post_confirm_separation",
        "separated_waiting_cash_zone_retest",
        f"InpV64AllowedDirection = {allowed_direction}",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V69 generated source missing token: {token}")
    if V68_ROOT in text:
        raise RuntimeError("V69 stale V68 FILE_COMMON root remains")
    if "LongToString(" in text:
        raise RuntimeError("V69 generated source contains unsupported LongToString")

    stage = text[text.index("void V66TryMicroEntry"):text.index("void V64ManagePendingEntry")]
    confirm_pos = stage.index('V64PendingEvent("POST_ZONE_REVERSAL_CONFIRM"')
    confirm_return = stage.index("return;", confirm_pos)
    sep_pos = stage.index('V64PendingEvent("POST_CONFIRM_SEPARATION"')
    retest_pos = stage.index('V64PendingEvent("POST_CONFIRM_RETEST_READY"')
    preflight_pos = stage.index("V64OrderPreflight")
    if not (confirm_pos < confirm_return < sep_pos < retest_pos < preflight_pos):
        raise RuntimeError("V69 state ordering invalid")


def build(output: Path, allowed_direction: int) -> str:
    text = transform(allowed_direction).replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = sha256(output)
    print(f"V69_SOURCE_SHA256={digest}")
    print(f"V69_SOURCE_PATH={output}")
    print(f"V69_ALLOWED_DIRECTION={allowed_direction}")
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
