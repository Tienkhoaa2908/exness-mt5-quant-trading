#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED_PARENT_SHA = "927611f7313793505d23c4c3d205a8ce0282869ad3ab8e4b49efe2ecc7ec79f6"
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
        raise RuntimeError(f"expected exactly one occurrence found={n}: {old[:180]!r}")
    return text.replace(old, new, 1)


def build(source: Path, output: Path) -> str:
    actual = sha256(source)
    if actual != EXPECTED_PARENT_SHA:
        raise RuntimeError(f"V52 requires accepted V51 source expected={EXPECTED_PARENT_SHA} actual={actual}")

    text = source.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    for bad in FORBIDDEN:
        if bad in text:
            raise RuntimeError(f"forbidden native/external execution path in V51 parent: {bad}")

    text = replace_once(text,
        '#define MT5Q_RELEASE_ID "v51_higher_frequency_challenger_v1"',
        '#define MT5Q_RELEASE_ID "v52_source_aware_challenger_v1"')
    text = replace_once(text,
        'input string InpOutputTag = "v51_higher_frequency_challenger_v1";',
        'input string InpOutputTag = "v52_source_aware_challenger_v1";')
    text = replace_once(text, '#define CANDIDATE_COUNT 29', '#define CANDIDATE_COUNT 32')

    text = replace_once(text,
        '   double adaptive_b3_quality_avg_min;\n',
        '   double adaptive_b3_quality_avg_min;\n   int adaptive_b3_allowed_mask;\n')
    text = replace_once(text,
        '   C[i].adaptive_b3_quality_avg_min=0.0;\n',
        '   C[i].adaptive_b3_quality_avg_min=0.0;\n   C[i].adaptive_b3_allowed_mask=0;\n')

    marker = 'void SetupV38FastClone(const int i,const string name,const int mode,const double targetR,\n'
    helper = '''void SetupV52SourceAwareRouter(const int i,const string name,const int allowedMask)\n{\n   SetupAdaptiveBreadthRouter(i,name,2,0.05,0.00,3,0.05);\n   C[i].family="adaptive_shadow_expert_router_b3_source_aware";\n   C[i].policy_name="breadth4_or_source_filtered_breadth3";\n   C[i].adaptive_b3_quality_avg_min=0.0;\n   C[i].adaptive_b3_allowed_mask=allowedMask;\n}\n\n'''
    text = replace_once(text, marker, helper + marker)

    old_catalog = '''   SetupV51HybridRouter(26,"v51_b4_or_b3_avg0p075",0.075);\n   SetupV51HybridRouter(27,"v51_b4_or_b3_avg0p10",0.100);\n   SetupV51HybridRouter(28,"v51_b4_or_b3_avg0p15",0.150);\n}'''
    new_catalog = '''   SetupV51HybridRouter(26,"v51_b4_or_b3_avg0p075",0.075);\n   SetupV51HybridRouter(27,"v51_b4_or_b3_avg0p10",0.100);\n   SetupV51HybridRouter(28,"v51_b4_or_b3_avg0p15",0.150);\n\n   // V52 preregistered source-aware exactly-three-healthy opportunity lanes.\n   // The >=4 healthy path remains unchanged; source filtering applies only at healthy==3.\n   SetupV52SourceAwareRouter(29,"v52_b4_or_b3_trend",SIG_TREND_H1);\n   SetupV52SourceAwareRouter(30,"v52_b4_or_b3_bos",SIG_BOS_FVG_H1);\n   SetupV52SourceAwareRouter(31,"v52_b4_or_b3_trend_bos",SIG_TREND_H1|SIG_BOS_FVG_H1);\n}'''
    text = replace_once(text, old_catalog, new_catalog)

    old_gate = '''   int v=st.adaptive_variant;\n   if(st.adaptive_breadth_min_count>0)\n   {\n      int healthy=0; double healthy_sum=0.0;\n      for(int e=0;e<EXPERT_COUNT;++e)\n      {\n         double hs=AdaptiveExpertScore(v,e);\n         if(hs>=st.adaptive_breadth_score_threshold){ healthy++; healthy_sum+=hs; }\n      }\n      if(healthy<st.adaptive_breadth_min_count) return true;\n      // Hybrid semantics: >=4 healthy is exactly the frozen baseline path.\n      // Only the extra exactly-3 lane is quality-filtered.\n      if(st.adaptive_b3_quality_avg_min>0.0 && healthy==3)\n      {\n         double avg3=healthy_sum/3.0;\n         if(avg3<st.adaptive_b3_quality_avg_min) return true;\n      }\n   }\n'''
    new_gate = '''   int v=st.adaptive_variant;\n   int v52_healthy=0;\n   if(st.adaptive_breadth_min_count>0)\n   {\n      int healthy=0; double healthy_sum=0.0;\n      for(int e=0;e<EXPERT_COUNT;++e)\n      {\n         double hs=AdaptiveExpertScore(v,e);\n         if(hs>=st.adaptive_breadth_score_threshold){ healthy++; healthy_sum+=hs; }\n      }\n      v52_healthy=healthy;\n      if(healthy<st.adaptive_breadth_min_count) return true;\n      // V51 compatibility: only V51 average-quality candidates use this field.\n      if(st.adaptive_b3_quality_avg_min>0.0 && healthy==3)\n      {\n         double avg3=healthy_sum/3.0;\n         if(avg3<st.adaptive_b3_quality_avg_min) return true;\n      }\n   }\n'''
    text = replace_once(text, old_gate, new_gate)

    old_select = '''   if(bestExpert<0){ return true; }\n   if(second>-DBL_MAX/2 && MathAbs(best-second)<1e-9) return true;\n   direction=bestDir; activeMask=bestMask;\n'''
    new_select = '''   if(bestExpert<0){ return true; }\n   if(second>-DBL_MAX/2 && MathAbs(best-second)<1e-9) return true;\n   // V52 source-aware gate: apply only to the extra exactly-three-healthy lane.\n   // At breadth>=4 the selected expert is never filtered, preserving breadth4 behavior.\n   if(st.adaptive_b3_allowed_mask>0 && v52_healthy==3 && (bestMask & st.adaptive_b3_allowed_mask)==0) return true;\n   direction=bestDir; activeMask=bestMask;\n'''
    text = replace_once(text, old_select, new_select)

    token = 'v51_higher_frequency_challenger=1\\r\\n'
    if text.count(token) != 1:
        raise RuntimeError(f"expected one V51 manifest token found={text.count(token)}")
    text = text.replace(token, token +
        'v52_source_aware_challenger=1\\r\\n'
        'v52_baseline=v46_hl10_thr0p05_breadth4\\r\\n'
        'v52_challengers=v52_b4_or_b3_trend,v52_b4_or_b3_bos,v52_b4_or_b3_trend_bos\\r\\n'
        'v52_extra_lane=healthy_eq_3_selected_source_mask\\r\\n'
        'v52_risk_changed=0\\r\\n'
        'v52_single_tester_run=1\\r\\n', 1)

    text = text.replace("V51_HIGHER_FREQUENCY START", "V52_SOURCE_AWARE START")
    text = text.replace("V51_HIGHER_FREQUENCY DONE", "V52_SOURCE_AWARE DONE")

    required = (
        '#define CANDIDATE_COUNT 32',
        'adaptive_b3_allowed_mask',
        'v52_healthy==3',
        'v52_b4_or_b3_trend',
        'v52_b4_or_b3_bos',
        'v52_b4_or_b3_trend_bos',
        'SIG_TREND_H1|SIG_BOS_FVG_H1',
        'v52_source_aware_challenger=1',
        'v52_risk_changed=0',
        'v52_single_tester_run=1',
        'MQLInfoInteger(MQL_TESTER)',
    )
    for tok in required:
        if tok not in text:
            raise RuntimeError(f"V52 required token missing: {tok}")
    for bad in FORBIDDEN:
        if bad in text:
            raise RuntimeError(f"forbidden path introduced by V52: {bad}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    digest = sha256(output)
    print(f"V52 source built sha256={digest} parent_sha256={actual} path={output}")
    return digest


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--source",required=True); ap.add_argument("--output",required=True); ns=ap.parse_args()
    build(Path(ns.source),Path(ns.output)); return 0


if __name__ == "__main__": raise SystemExit(main())
