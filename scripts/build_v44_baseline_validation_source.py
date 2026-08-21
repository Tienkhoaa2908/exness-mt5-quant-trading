#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, pathlib

EXPECTED_PARENT_RELEASE = "v38_fast_harvest_lab_v1"
NEW_RELEASE = "v44_baseline_robustness_validation_v1"
FORBIDDEN = ("OrderSend(", "OrderSendAsync(", "CTrade", "trade.Buy(", "trade.Sell(")

def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def replace_once(text: str, old: str, new: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"expected exactly one occurrence, found {n}: {old[:160]!r}")
    return text.replace(old, new, 1)

def build(source: pathlib.Path, output: pathlib.Path) -> None:
    text = source.read_text(encoding="utf-8-sig")
    required = [
        f'#define MT5Q_RELEASE_ID "{EXPECTED_PARENT_RELEASE}"',
        '#define CANDIDATE_COUNT 23',
        'adaptive_ewma_hl8_thr0',
        'adaptive_ewma_hl8_thr0p05',
        'adaptive_ewma_hl10_thr0p05',
        'MQLInfoInteger(MQL_TESTER)',
    ]
    for token in required:
        if token not in text:
            raise RuntimeError(f"accepted V38 parent token missing: {token}")
    for bad in FORBIDDEN:
        if bad in text:
            raise RuntimeError(f"forbidden native order path already present: {bad}")

    text = replace_once(
        text,
        f'#define MT5Q_RELEASE_ID "{EXPECTED_PARENT_RELEASE}"',
        f'#define MT5Q_RELEASE_ID "{NEW_RELEASE}"',
    )
    text = replace_once(
        text,
        'input string InpOutputTag = "v38_fast_harvest_lab_v1";',
        'input string InpOutputTag = "v44_baseline_robustness_validation_v1";',
    )
    text = replace_once(
        text,
        'input bool   InpV34WriteIntraTradeTelemetry = true;',
        'input bool   InpV34WriteIntraTradeTelemetry = false;',
    )
    text = replace_once(
        text,
        'input bool   InpV38WriteM1FastTelemetry = true;',
        'input bool   InpV38WriteM1FastTelemetry = false;',
    )
    marker = '   x+="v38_m1_fast_telemetry="+(InpV38WriteM1FastTelemetry?"1":"0")+"\\r\\n";'
    extra = (
        '   x+="v44_baseline_validation=1\\r\\n";\n'
        '   x+="v44_strategy_logic_changed=0\\r\\n";\n'
        '   x+="v44_risk_changed=0\\r\\n";\n'
        '   x+="v44_candidate_focus=adaptive_ewma_hl8_thr0,adaptive_ewma_hl8_thr0p05,adaptive_ewma_hl10_thr0p05\\r\\n";\n'
        '   x+="v44_window_protocol=12_monthly_4_quarter_2_halfyear_1_annual_restart_windows\\r\\n";\n'
        '   x+="v44_live_authorized=0\\r\\n";'
    )
    text = replace_once(text, marker, marker + "\n" + extra)
    text = text.replace("V38_FAST_HARVEST_LAB START", "V44_BASELINE_VALIDATION START")
    text = text.replace("V38_FAST_HARVEST_LAB DONE", "V44_BASELINE_VALIDATION DONE")

    if '#define CANDIDATE_COUNT 23' not in text:
        raise RuntimeError("candidate catalog changed unexpectedly")
    for token in [
        'v44_baseline_validation=1',
        'v44_strategy_logic_changed=0',
        'v44_risk_changed=0',
        'adaptive_ewma_hl8_thr0',
        'adaptive_ewma_hl8_thr0p05',
        'adaptive_ewma_hl10_thr0p05',
    ]:
        if token not in text:
            raise RuntimeError(f"V44 marker missing after build: {token}")
    for bad in FORBIDDEN:
        if bad in text:
            raise RuntimeError(f"forbidden native order path introduced: {bad}")
    if "MQLInfoInteger(MQL_TESTER)" not in text:
        raise RuntimeError("tester-only guard lost")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="\r\n")
    print(f"V44 source PASS sha256={sha256(output)} path={output}")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    build(pathlib.Path(args.source), pathlib.Path(args.output))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
