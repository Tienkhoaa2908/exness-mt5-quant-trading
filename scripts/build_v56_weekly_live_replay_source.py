#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
V55_FIXED_BUILDER = HERE / "build_v55_account_agnostic_source_windows_fixed.py"
CANDIDATE = "v52_b4_or_b3_trend_bos"
V56_STATE_FILE = r"mt5_quant\\v56_weekly_live_replay\\seed_state.csv"

V48_TESTER_REFUSAL = (
    '   if(MQLInfoInteger(MQL_TESTER)){ V48WriteInitDiagnostic("REFUSED","tester_mode"); '
    'Print("V48 DEMO-PAPER refuses tester mode; use frozen V46 for historical tests"); return INIT_FAILED; }'
)
V56_TESTER_ONLY_GUARD = (
    '   if(!MQLInfoInteger(MQL_TESTER)){ V48WriteInitDiagnostic("REFUSED","v56_tester_only"); '
    'Print("V56 WEEKLY REAL-TICK REPLAY REFUSED: STRATEGY TESTER REQUIRED"); return INIT_FAILED; }'
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"V56 {label} drifted expected=1 actual={count}")
    return text.replace(old, new, 1)


def transform_v55_to_v56(text: str) -> str:
    # V56 is diagnostic only. It must never be attachable to a live chart.
    text = replace_once(text, V48_TESTER_REFUSAL, V56_TESTER_ONLY_GUARD, "tester-only guard")

    # Keep V55 alpha, candidate, sizing and execution mapping unchanged. Disable push
    # notifications only because tester notifications are non-actionable/noisy.
    text = replace_once(
        text,
        "input bool InpV55PushNotifications = true;",
        "input bool InpV55PushNotifications = false;",
        "tester notification default",
    )

    # Force the adaptive state onto an isolated V56 FILE_COMMON path. The runner seeds
    # this from the accepted V52R state-after snapshot and never uses current live state.
    pattern = re.compile(r'input string InpAdaptiveStateFile = "[^"]+";')
    text, count = pattern.subn(
        'input string InpAdaptiveStateFile = "' + V56_STATE_FILE + '";',
        text,
        count=1,
    )
    if count != 1:
        raise RuntimeError(f"V56 adaptive-state input drifted expected=1 actual={count}")

    # Isolate all mutable paper/runtime output from production V55 evidence/state.
    replacements = (
        (r"mt5_quant\\v55\\", r"mt5_quant\\v56_weekly_live_replay\\"),
        (r"mt5_quant\\paper\\", r"mt5_quant\\v56_weekly_live_replay\\paper\\"),
        (r"mt5_quant\\runs\\", r"mt5_quant\\v56_weekly_live_replay\\runs\\"),
    )
    for old, new in replacements:
        if old not in text:
            raise RuntimeError(f"V56 isolation marker missing: {old}")
        text = text.replace(old, new)

    # Tester-only instrumentation: observe the selected virtual book transitions without
    # changing the strategy decision or broker-mapping code.
    globals_old = "bool g_v55_real_entry_epoch_ready=false;"
    globals_new = (
        "bool g_v55_real_entry_epoch_ready=false;\n"
        "bool g_v56_prev_virtual_open=false;\n"
        "int g_v56_prev_virtual_direction=0;"
    )
    text = replace_once(text, globals_old, globals_new, "virtual transition globals")

    marker = "   int owned=V55OwnedPositionCount(ticket,broker_dir,broker_vol);"
    instrumentation = r'''   if(B[ix].open!=g_v56_prev_virtual_open || (B[ix].open && B[ix].direction!=g_v56_prev_virtual_direction))
   {
      string ev=(B[ix].open?"V56_VIRTUAL_OPEN":"V56_VIRTUAL_CLOSE");
      string row=TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+ev+","+
         IntegerToString(B[ix].direction)+","+DoubleToString(B[ix].entry,_Digits)+","+
         DoubleToString(B[ix].stop,_Digits)+","+DoubleToString(B[ix].tp,_Digits)+","+
         DoubleToString(B[ix].volume,6);
      V55AppendCsv(g_v55_events_file,row);
      g_v56_prev_virtual_open=B[ix].open;
      g_v56_prev_virtual_direction=B[ix].direction;
   }
   int owned=V55OwnedPositionCount(ticket,broker_dir,broker_vol);'''
    text = replace_once(text, marker, instrumentation, "selected virtual transition instrumentation")

    required = (
        CANDIDATE,
        "V56 WEEKLY REAL-TICK REPLAY REFUSED: STRATEGY TESTER REQUIRED",
        "if(!MQLInfoInteger(MQL_TESTER))",
        'input bool InpV55PushNotifications = false;',
        V56_STATE_FILE,
        "V56_VIRTUAL_OPEN",
        "V56_VIRTUAL_CLOSE",
        "V55NewRiskAuthorized",
        "V55StopsGeometryOk",
        "OrderCalcProfit",
        "OrderCalcMargin",
        "InpV55Magic = 550055",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V56 required token missing: {token}")

    forbidden = (
        "V48 DEMO-PAPER refuses tester mode; use frozen V46 for historical tests",
        r"mt5_quant\\v55\\",
        'input bool InpV55PushNotifications = true;',
    )
    for token in forbidden:
        if token in text:
            raise RuntimeError(f"V56 forbidden token remains: {token}")

    return text


def build(source: Path, output: Path) -> str:
    if not source.is_file():
        raise RuntimeError(f"V56 parent source missing: {source}")
    with tempfile.TemporaryDirectory(prefix="v56_weekly_replay_") as td:
        staged = Path(td) / "V55AccountAgnosticProduction.mq5"
        subprocess.run(
            [sys.executable, str(V55_FIXED_BUILDER), "--source", str(source), "--output", str(staged)],
            check=True,
        )
        text = staged.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        out = transform_v55_to_v56(text)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(out.replace("\n", "\r\n").encode("utf-8"))
    digest = sha256(output)
    print(f"V56_SOURCE_SHA256={digest}")
    print("V56_ALPHA_CHANGED=0")
    print("V56_EXECUTION_MAPPING_CHANGED=0")
    print("V56_TESTER_ONLY=1")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--output", required=True)
    ns = ap.parse_args()
    build(Path(ns.source), Path(ns.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
