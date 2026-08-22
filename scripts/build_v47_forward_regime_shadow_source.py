#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED_PARENT_SHA = "6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3"
EXPECTED_OUTPUT_SHA = "7685dd83f576841532970d43e21fda80c896c407f313edae1fb12b0b39387e44"
FORBIDDEN = ("OrderSend(", "OrderSendAsync(", "CTrade", "trade.Buy(", "trade.Sell(")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"expected exactly one occurrence, found={n}: {old[:120]!r}")
    return text.replace(old, new, 1)


def build(source: Path, output: Path) -> str:
    actual_parent = sha256(source)
    if actual_parent != EXPECTED_PARENT_SHA:
        raise RuntimeError(f"V46 parent SHA mismatch expected={EXPECTED_PARENT_SHA} actual={actual_parent}")

    text = source.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    for bad in FORBIDDEN:
        if bad in text:
            raise RuntimeError(f"forbidden native order path in parent: {bad}")

    text = replace_once(text,
        '#define MT5Q_RELEASE_ID "v46_expert_breadth_walkforward_v1"',
        '#define MT5Q_RELEASE_ID "v47_forward_regime_shadow_v1"')
    text = replace_once(text,
        'input string InpOutputTag = "v46_expert_breadth_walkforward_v1";',
        'input string InpOutputTag = "v47_forward_regime_shadow_v1";')

    # Observability-only repair. No signal, entry, exit, state, sizing or risk logic changes.
    text = replace_once(text,
        'x+="format=mt5_quant_v38_fast_harvest_lab_v1\\r\\n";',
        'x+="format=mt5_quant_v47_forward_regime_shadow_v1\\r\\n";')
    text = replace_once(text,
        'x+="source_file=V38FastHarvestLab.mq5\\r\\n";',
        'x+="source_file=V47ForwardRegimeShadowLab.mq5\\r\\n";')
    text = replace_once(text,
        'x+="candidate_count=23\\r\\nbook_count=4\\r\\nmonthly_reset=1\\r\\nmonths_written="+IntegerToString((int)g_months_written)+"\\r\\n";',
        'x+="candidate_count="+IntegerToString(CANDIDATE_COUNT)+"\\r\\nbook_count="+IntegerToString(BOOK_COUNT)+"\\r\\nmonthly_reset=1\\r\\nmonths_written="+IntegerToString((int)g_months_written)+"\\r\\n";')
    text = replace_once(text,
        'x+="v46_live_authorized=0\\r\\n";',
        'x+="v46_live_authorized=0\\r\\n";\n   x+="v47_forward_regime_shadow=1\\r\\nv47_primary_logic_changed=0\\r\\nv47_shadow_adx_di_only=1\\r\\nv47_live_authorized=0\\r\\n";')
    text = replace_once(text,
        'PrintFormat("V46_EXPERT_BREADTH START %s %s candidates=%d books=%d",_Symbol,PeriodText(),CANDIDATE_COUNT,BOOK_COUNT);',
        'PrintFormat("V47_FORWARD_REGIME_SHADOW START %s %s candidates=%d books=%d",_Symbol,PeriodText(),CANDIDATE_COUNT,BOOK_COUNT);')
    text = replace_once(text,
        'PrintFormat("V46_EXPERT_BREADTH DONE months=%d",(int)g_months_written);',
        'PrintFormat("V47_FORWARD_REGIME_SHADOW DONE months=%d",(int)g_months_written);')

    required = (
        '#define CANDIDATE_COUNT 26',
        'v46_hl10_thr0p05_breadth4',
        'candidate_count="+IntegerToString(CANDIDATE_COUNT)',
        'source_file=V47ForwardRegimeShadowLab.mq5',
        'v47_forward_regime_shadow=1',
        'v47_primary_logic_changed=0',
        'v47_shadow_adx_di_only=1',
        'v47_live_authorized=0',
        'MQLInfoInteger(MQL_TESTER)',
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V47 required token missing: {token}")

    for bad in FORBIDDEN:
        if bad in text:
            raise RuntimeError(f"forbidden native order path introduced: {bad}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    actual = sha256(output)
    if actual != EXPECTED_OUTPUT_SHA:
        raise RuntimeError(f"V47 output SHA mismatch expected={EXPECTED_OUTPUT_SHA} actual={actual}")
    print(f"V47 source PASS sha256={actual} path={output}")
    return actual


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    build(Path(a.source), Path(a.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
