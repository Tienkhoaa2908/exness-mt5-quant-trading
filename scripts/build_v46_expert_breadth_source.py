#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED_PARENT_SHA = "36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2"
EXPECTED_OUTPUT_SHA = "3695095d80fd81847bbcc4e4ae0902c4ddbf713fe0ac9ab8549f1c19d77c1f13"
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


def build(source: Path, output: Path) -> None:
    if sha256(source) != EXPECTED_PARENT_SHA:
        raise RuntimeError(f"V45 parent SHA mismatch expected={EXPECTED_PARENT_SHA} actual={sha256(source)}")
    text = source.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    for bad in FORBIDDEN:
        if bad in text:
            raise RuntimeError(f"forbidden native order path in parent: {bad}")

    text = replace_once(text, '#define MT5Q_RELEASE_ID "v45_multiyear_single_run_validation_v1"', '#define MT5Q_RELEASE_ID "v46_expert_breadth_walkforward_v1"')
    text = replace_once(text, 'input string InpOutputTag = "v45_multiyear_single_run_validation_v1";', 'input string InpOutputTag = "v46_expert_breadth_walkforward_v1";')
    text = replace_once(text, '#define CANDIDATE_COUNT 23', '#define CANDIDATE_COUNT 26')

    text = replace_once(
        text,
        '   double adaptive_switch_penalty;\n',
        '   double adaptive_switch_penalty;\n   int adaptive_breadth_min_count;\n   double adaptive_breadth_score_threshold;\n',
    )
    text = replace_once(
        text,
        '   C[i].adaptive_switch_penalty=0.0;\n',
        '   C[i].adaptive_switch_penalty=0.0;\n   C[i].adaptive_breadth_min_count=0;\n   C[i].adaptive_breadth_score_threshold=0.0;\n',
    )

    old = '''void SetupV38FastClone(const int i,const string name,const int mode,const double targetR,\n                       const double armR,const double givebackR,const int timeboxSeconds)\n'''
    new = '''void SetupAdaptiveBreadthRouter(const int i,const string name,const int variant,const double minScore,\n                                const double switchPenalty,const int minBreadth,const double breadthThreshold)\n{\n   SetupAdaptiveRouter(i,name,variant,minScore,switchPenalty);\n   C[i].family="adaptive_shadow_expert_router_breadth";\n   C[i].policy_name="hl10_thr0p05_expert_breadth";\n   C[i].adaptive_breadth_min_count=minBreadth;\n   C[i].adaptive_breadth_score_threshold=breadthThreshold;\n}\n\nvoid SetupV38FastClone(const int i,const string name,const int mode,const double targetR,\n                       const double armR,const double givebackR,const int timeboxSeconds)\n'''
    text = replace_once(text, old, new)

    old = '   SetupV38FastClone(22,"v38_adaptive_timebox30m",4,0.0,0.0,0.0,30*60);\n}'
    new = '''   SetupV38FastClone(22,"v38_adaptive_timebox30m",4,0.0,0.0,0.0,30*60);\n\n   // V46 cross-expert health breadth gate. Breadth4 is preregistered primary.\n   // Breadth3/5 are sensitivity comparators only and cannot be promoted from this sample.\n   SetupAdaptiveBreadthRouter(23,"v46_hl10_thr0p05_breadth4",2,0.05,0.00,4,0.05);\n   SetupAdaptiveBreadthRouter(24,"v46_hl10_thr0p05_breadth3_sensitivity",2,0.05,0.00,3,0.05);\n   SetupAdaptiveBreadthRouter(25,"v46_hl10_thr0p05_breadth5_sensitivity",2,0.05,0.00,5,0.05);\n}'''
    text = replace_once(text, old, new)

    old = '   int v=st.adaptive_variant;\n   for(int e=0;e<EXPERT_COUNT;++e)\n'
    new = '''   int v=st.adaptive_variant;\n   if(st.adaptive_breadth_min_count>0)\n   {\n      int healthy=0;\n      for(int e=0;e<EXPERT_COUNT;++e)\n         if(AdaptiveExpertScore(v,e)>=st.adaptive_breadth_score_threshold) healthy++;\n      if(healthy<st.adaptive_breadth_min_count) return true;\n   }\n   for(int e=0;e<EXPERT_COUNT;++e)\n'''
    text = replace_once(text, old, new)

    replacements = {
        "v45_multiyear_validation=1": "v46_expert_breadth=1",
        "v45_strategy_logic_changed=0": "v46_strategy_logic_changed=1",
        "v45_risk_changed=0": "v46_risk_changed=0",
        "v45_candidate_focus=adaptive_ewma_hl8_thr0,adaptive_ewma_hl8_thr0p05,adaptive_ewma_hl10_thr0p05": "v46_candidate_focus=v46_hl10_thr0p05_breadth4,v46_hl10_thr0p05_breadth3_sensitivity,v46_hl10_thr0p05_breadth5_sensitivity",
        "v45_state_protocol=cold_start_no_2025_state": "v46_state_protocol=cold_start_no_future_state",
        "v45_default_from=2022.01.01": "v46_default_from=2021.01.03",
        "v45_default_to=2026.08.01": "v46_default_to=2026.08.01",
        "v45_warmup_months=6": "v46_warmup_months=6",
        "v45_single_tester_run=1": "v46_single_tester_run=1",
        "v45_monthly_logging=1": "v46_monthly_logging=1",
        "v45_live_authorized=0": "v46_live_authorized=0",
        "V45_MULTIYEAR_VALIDATION START": "V46_EXPERT_BREADTH START",
        "V45_MULTIYEAR_VALIDATION DONE": "V46_EXPERT_BREADTH DONE",
    }
    for old, new in replacements.items():
        if old not in text:
            raise RuntimeError(f"missing parent marker: {old}")
        text = text.replace(old, new)

    required = (
        '#define CANDIDATE_COUNT 26',
        'v46_hl10_thr0p05_breadth4',
        'v46_hl10_thr0p05_breadth3_sensitivity',
        'v46_hl10_thr0p05_breadth5_sensitivity',
        'adaptive_breadth_min_count',
        'v46_expert_breadth=1',
        'v46_strategy_logic_changed=1',
        'v46_risk_changed=0',
        'v46_state_protocol=cold_start_no_future_state',
        'v46_live_authorized=0',
        'MQLInfoInteger(MQL_TESTER)',
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V46 token missing after build: {token}")
    for bad in FORBIDDEN:
        if bad in text:
            raise RuntimeError(f"forbidden native order path introduced: {bad}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    actual = sha256(output)
    if actual != EXPECTED_OUTPUT_SHA:
        raise RuntimeError(f"V46 output SHA mismatch expected={EXPECTED_OUTPUT_SHA} actual={actual}")
    print(f"V46 source PASS sha256={actual} path={output}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    build(Path(a.source), Path(a.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
