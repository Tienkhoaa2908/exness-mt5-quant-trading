#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import tempfile
from pathlib import Path

V48_SHA = "ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa"
V49_BUILDER = Path(__file__).resolve().parent / "build_v49_one_shot_demo_rehearsal_source.py"
FORBIDDEN_PARENT = ("OrderSend(", "OrderSendAsync(", "CTrade", "trade.Buy(", "trade.Sell(", "#import")


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    n=text.count(old)
    if n!=1:
        raise RuntimeError(f"expected exactly one occurrence found={n}: {old[:180]!r}")
    return text.replace(old,new,1)


def load(path: Path, name: str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def add_selected_candidate(v48: Path, output: Path) -> str:
    actual=sha256(v48)
    if actual!=V48_SHA:
        raise RuntimeError(f"V53 requires canonical V48 parent expected={V48_SHA} actual={actual}")
    text=v48.read_text(encoding="utf-8-sig").replace("\r\n","\n").replace("\r","\n")
    for bad in FORBIDDEN_PARENT:
        if bad in text:
            raise RuntimeError(f"unexpected broker path in V48 parent: {bad}")

    text=replace_once(text,"#define CANDIDATE_COUNT 26","#define CANDIDATE_COUNT 27")
    text=replace_once(text,"   double adaptive_breadth_score_threshold;\n","   double adaptive_breadth_score_threshold;\n   int adaptive_b3_allowed_mask;\n")
    text=replace_once(text,"   C[i].adaptive_breadth_score_threshold=0.0;\n","   C[i].adaptive_breadth_score_threshold=0.0;\n   C[i].adaptive_b3_allowed_mask=0;\n")

    marker="void SetupV38FastClone(const int i,const string name,const int mode,const double targetR,\n"
    helper='''void SetupV53SelectedRouter(const int i)\n{\n   SetupAdaptiveBreadthRouter(i,"v52_b4_or_b3_trend_bos",2,0.05,0.00,3,0.05);\n   C[i].family="adaptive_shadow_expert_router_b3_source_aware";\n   C[i].policy_name="breadth4_or_source_filtered_breadth3";\n   C[i].adaptive_b3_allowed_mask=SIG_TREND_H1|SIG_BOS_FVG_H1;\n}\n\n'''
    text=replace_once(text,marker,helper+marker)

    old_catalog='''   SetupAdaptiveBreadthRouter(23,"v46_hl10_thr0p05_breadth4",2,0.05,0.00,4,0.05);\n   SetupAdaptiveBreadthRouter(24,"v46_hl10_thr0p05_breadth3_sensitivity",2,0.05,0.00,3,0.05);\n   SetupAdaptiveBreadthRouter(25,"v46_hl10_thr0p05_breadth5_sensitivity",2,0.05,0.00,5,0.05);\n}'''
    new_catalog='''   SetupAdaptiveBreadthRouter(23,"v46_hl10_thr0p05_breadth4",2,0.05,0.00,4,0.05);\n   SetupAdaptiveBreadthRouter(24,"v46_hl10_thr0p05_breadth3_sensitivity",2,0.05,0.00,3,0.05);\n   SetupAdaptiveBreadthRouter(25,"v46_hl10_thr0p05_breadth5_sensitivity",2,0.05,0.00,5,0.05);\n   SetupV53SelectedRouter(26);\n}'''
    text=replace_once(text,old_catalog,new_catalog)

    old_gate='''   int v=st.adaptive_variant;\n   if(st.adaptive_breadth_min_count>0)\n   {\n      int healthy=0;\n      for(int e=0;e<EXPERT_COUNT;++e)\n         if(AdaptiveExpertScore(v,e)>=st.adaptive_breadth_score_threshold) healthy++;\n      if(healthy<st.adaptive_breadth_min_count) return true;\n   }\n'''
    new_gate='''   int v=st.adaptive_variant;\n   int v53_healthy=0;\n   if(st.adaptive_breadth_min_count>0)\n   {\n      int healthy=0;\n      for(int e=0;e<EXPERT_COUNT;++e)\n         if(AdaptiveExpertScore(v,e)>=st.adaptive_breadth_score_threshold) healthy++;\n      v53_healthy=healthy;\n      if(healthy<st.adaptive_breadth_min_count) return true;\n   }\n'''
    text=replace_once(text,old_gate,new_gate)

    old_select='''   if(bestExpert<0){ return true; }\n   if(second>-DBL_MAX/2 && MathAbs(best-second)<1e-9) return true;\n   direction=bestDir; activeMask=bestMask;\n'''
    new_select='''   if(bestExpert<0){ return true; }\n   if(second>-DBL_MAX/2 && MathAbs(best-second)<1e-9) return true;\n   if(st.adaptive_b3_allowed_mask>0 && v53_healthy==3 && (bestMask & st.adaptive_b3_allowed_mask)==0) return true;\n   direction=bestDir; activeMask=bestMask;\n'''
    text=replace_once(text,old_select,new_select)

    text=text.replace("const int ci=23, bi=3, ix=BI(ci,bi);","const int ci=26, bi=3, ix=BI(ci,bi);")
    text=text.replace("Waiting for breadth4 opportunity","Waiting for trend+bos source-aware opportunity")
    text=text.replace("v48_primary_candidate=v46_hl10_thr0p05_breadth4","v48_primary_candidate=v52_b4_or_b3_trend_bos")

    for tok in ("#define CANDIDATE_COUNT 27","SetupV53SelectedRouter(26)","adaptive_b3_allowed_mask","v53_healthy==3","SIG_TREND_H1|SIG_BOS_FVG_H1","v52_b4_or_b3_trend_bos"):
        if tok not in text:
            raise RuntimeError(f"selected forward candidate token missing: {tok}")
    for bad in FORBIDDEN_PARENT:
        if bad in text:
            raise RuntimeError(f"broker path introduced before DEMO adapter: {bad}")
    output.write_bytes(text.replace("\n","\r\n").encode("utf-8"))
    digest=sha256(output)
    print(f"V53_SELECTED_FORWARD_SHA256={digest}")
    return digest


def build(source: Path, output: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="v53_selected_forward_") as td:
        selected=Path(td)/"V53SelectedForward.mq5"
        selected_sha=add_selected_candidate(source,selected)
        v49=load(V49_BUILDER,"v49_builder_for_v53")
        v49.EXPECTED_PARENT_SHA=selected_sha
        staged=Path(td)/"V53AdapterStage.mq5"
        v49.build(selected,staged)
        text=staged.read_text(encoding="utf-8-sig").replace("\r\n","\n").replace("\r","\n")

        text=text.replace("V49","V53").replace("v49","v53")
        text=text.replace("490049","530053")
        text=text.replace("InpV53MinMarketDays = 3","InpV53MinMarketDays = 2")
        text=text.replace("InpV53MinRoundTrips = 3","InpV53MinRoundTrips = 1")
        text=text.replace("InpV53HardCalendarDays = 14","InpV53HardCalendarDays = 7")
        text=text.replace("const int ci=23,bi=3,ix=BI(ci,bi);","const int ci=26,bi=3,ix=BI(ci,bi);")
        text=text.replace("V53 breadth4","V53 trend_bos")
        text=text.replace("v53_one_shot_demo_rehearsal_v1","v53_trend_bos_demo_confirmation_v1")
        text=text.replace("V53 DEMO-REHEARSAL","V53 TREND+BOS DEMO")
        text=text.replace("V53 DEMO REHEARSAL | ","V53 TREND+BOS DEMO | ")
        text=text.replace("V53OneShotDemoRehearsal.mq5","V53TrendBosDemoConfirmation.mq5")
        text=text.replace("schema=v53_demo_rehearsal_status_v1","schema=v53_trend_bos_demo_status_v1")
        text=text.replace("LIVE_CANDIDATE_READY","DEMO_CONFIRMATION_PASS")
        text=text.replace("one_shot_demo_rehearsal_pass","trend_bos_demo_confirmation_pass")
        text=text.replace("broker_demo_orders=1\\r\\nreal_money_authorized=0","broker_demo_orders=1\\r\\nreal_money_authorized=0\\r\\nv53_candidate=v52_b4_or_b3_trend_bos\\r\\nv53_v52r_selected=1")

        required=("InpV53Magic = 530053","InpV53MinMarketDays = 2","InpV53MinRoundTrips = 1","InpV53HardCalendarDays = 7","const int ci=26,bi=3,ix=BI(ci,bi);","v52_b4_or_b3_trend_bos","ACCOUNT_TRADE_MODE_DEMO","real_money_authorized=0","SendNotification","DEMO_CONFIRMATION_PASS")
        for tok in required:
            if tok not in text:
                raise RuntimeError(f"V53 required token missing: {tok}")
        if "const int ci=23,bi=3,ix=BI(ci,bi);" in text:
            raise RuntimeError("V53 broker adapter still references breadth4 index 23")
        if "LIVE_CANDIDATE_READY" in text:
            raise RuntimeError("V53 must not use V49 LIVE_CANDIDATE_READY verdict")
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_bytes(text.replace("\n","\r\n").encode("utf-8"))
        digest=sha256(output)
        print(f"V53_SOURCE_SHA256={digest} selected_forward_sha256={selected_sha}")
        return digest


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--source",required=True); ap.add_argument("--output",required=True); ns=ap.parse_args()
    build(Path(ns.source),Path(ns.output)); return 0

if __name__=="__main__": raise SystemExit(main())
