#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED_PARENT_SHA = "6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3"
FORBIDDEN = ("OrderSend(", "OrderSendAsync(", "CTrade", "trade.Buy(", "trade.Sell(", "#import")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"expected exactly one occurrence found={n}: {old[:160]!r}")
    return text.replace(old, new, 1)


def build(source: Path, output: Path) -> str:
    actual = sha256(source)
    if actual != EXPECTED_PARENT_SHA:
        raise RuntimeError(f"V51 requires canonical V46 parent expected={EXPECTED_PARENT_SHA} actual={actual}")
    text = source.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    for bad in FORBIDDEN:
        if bad in text:
            raise RuntimeError(f"forbidden native/external execution path in V46 parent: {bad}")

    text = replace_once(text, '#define MT5Q_RELEASE_ID "v46_expert_breadth_walkforward_v1"', '#define MT5Q_RELEASE_ID "v51_higher_frequency_challenger_v1"')
    text = replace_once(text, 'input string InpOutputTag = "v46_expert_breadth_walkforward_v1";', 'input string InpOutputTag = "v51_higher_frequency_challenger_v1";')
    text = replace_once(text, '#define CANDIDATE_COUNT 26', '#define CANDIDATE_COUNT 29')

    text = replace_once(text,
        '   double adaptive_breadth_score_threshold;\n',
        '   double adaptive_breadth_score_threshold;\n   double adaptive_b3_quality_avg_min;\n')
    text = replace_once(text,
        '   C[i].adaptive_breadth_score_threshold=0.0;\n',
        '   C[i].adaptive_breadth_score_threshold=0.0;\n   C[i].adaptive_b3_quality_avg_min=0.0;\n')

    marker = 'void SetupV38FastClone(const int i,const string name,const int mode,const double targetR,\n'
    helper = '''void SetupV51HybridRouter(const int i,const string name,const double b3AvgMin)\n{\n   SetupAdaptiveBreadthRouter(i,name,2,0.05,0.00,3,0.05);\n   C[i].family="adaptive_shadow_expert_router_hybrid_b3_quality";\n   C[i].policy_name="breadth4_or_strong_breadth3";\n   C[i].adaptive_b3_quality_avg_min=b3AvgMin;\n}\n\n'''
    text = replace_once(text, marker, helper + marker)

    old_catalog = '''   SetupAdaptiveBreadthRouter(23,"v46_hl10_thr0p05_breadth4",2,0.05,0.00,4,0.05);\n   SetupAdaptiveBreadthRouter(24,"v46_hl10_thr0p05_breadth3_sensitivity",2,0.05,0.00,3,0.05);\n   SetupAdaptiveBreadthRouter(25,"v46_hl10_thr0p05_breadth5_sensitivity",2,0.05,0.00,5,0.05);\n}'''
    new_catalog = '''   SetupAdaptiveBreadthRouter(23,"v46_hl10_thr0p05_breadth4",2,0.05,0.00,4,0.05);\n   SetupAdaptiveBreadthRouter(24,"v46_hl10_thr0p05_breadth3_sensitivity",2,0.05,0.00,3,0.05);\n   SetupAdaptiveBreadthRouter(25,"v46_hl10_thr0p05_breadth5_sensitivity",2,0.05,0.00,5,0.05);\n\n   // V51 preregistered higher-frequency challengers. Baseline breadth4 behavior is inherited.\n   // When exactly three experts are healthy, the average health score must clear the fixed quality floor.\n   SetupV51HybridRouter(26,"v51_b4_or_b3_avg0p075",0.075);\n   SetupV51HybridRouter(27,"v51_b4_or_b3_avg0p10",0.100);\n   SetupV51HybridRouter(28,"v51_b4_or_b3_avg0p15",0.150);\n}'''
    text = replace_once(text, old_catalog, new_catalog)

    old_gate = '''   if(st.adaptive_breadth_min_count>0)\n   {\n      int healthy=0;\n      for(int e=0;e<EXPERT_COUNT;++e)\n         if(AdaptiveExpertScore(v,e)>=st.adaptive_breadth_score_threshold) healthy++;\n      if(healthy<st.adaptive_breadth_min_count) return true;\n   }\n'''
    new_gate = '''   if(st.adaptive_breadth_min_count>0)\n   {\n      int healthy=0; double healthy_sum=0.0;\n      for(int e=0;e<EXPERT_COUNT;++e)\n      {\n         double hs=AdaptiveExpertScore(v,e);\n         if(hs>=st.adaptive_breadth_score_threshold){ healthy++; healthy_sum+=hs; }\n      }\n      if(healthy<st.adaptive_breadth_min_count) return true;\n      // Hybrid semantics: >=4 healthy is exactly the frozen baseline path.\n      // Only the extra exactly-3 lane is quality-filtered.\n      if(st.adaptive_b3_quality_avg_min>0.0 && healthy==3)\n      {\n         double avg3=healthy_sum/3.0;\n         if(avg3<st.adaptive_b3_quality_avg_min) return true;\n      }\n   }\n'''
    text = replace_once(text, old_gate, new_gate)

    # Preserve historical V46 markers while adding V51 provenance to the same tester-only manifest.
    token = 'v46_expert_breadth=1\\r\\n'
    if text.count(token) != 1:
        raise RuntimeError(f"expected one V46 manifest token, found={text.count(token)}")
    text = text.replace(token, token + 'v51_higher_frequency_challenger=1\\r\\nv51_baseline=v46_hl10_thr0p05_breadth4\\r\\nv51_challengers=v51_b4_or_b3_avg0p075,v51_b4_or_b3_avg0p10,v51_b4_or_b3_avg0p15\\r\\nv51_risk_changed=0\\r\\nv51_single_tester_run=1\\r\\n', 1)
    text = text.replace("V46_EXPERT_BREADTH START", "V51_HIGHER_FREQUENCY START")
    text = text.replace("V46_EXPERT_BREADTH DONE", "V51_HIGHER_FREQUENCY DONE")

    required = (
        '#define CANDIDATE_COUNT 29',
        'v46_hl10_thr0p05_breadth4',
        'v51_b4_or_b3_avg0p075',
        'v51_b4_or_b3_avg0p10',
        'v51_b4_or_b3_avg0p15',
        'adaptive_b3_quality_avg_min',
        'healthy==3',
        'v51_higher_frequency_challenger=1',
        'v51_risk_changed=0',
        'v51_single_tester_run=1',
        'MQLInfoInteger(MQL_TESTER)',
    )
    for tok in required:
        if tok not in text:
            raise RuntimeError(f"V51 required token missing: {tok}")
    for bad in FORBIDDEN:
        if bad in text:
            raise RuntimeError(f"forbidden path introduced by V51: {bad}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    digest = sha256(output)
    print(f"V51 source built sha256={digest} parent_sha256={actual} path={output}")
    return digest


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--source",required=True); ap.add_argument("--output",required=True); ns=ap.parse_args()
    build(Path(ns.source),Path(ns.output)); return 0

if __name__ == "__main__": raise SystemExit(main())
