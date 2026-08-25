#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

BRANCH="agent/v52-source-aware-challenger"
V46_SHA="6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3"
V51_ACCEPTED_SHA="927611f7313793505d23c4c3d205a8ce0282869ad3ab8e4b49efe2ecc7ec79f6"
V45_SHA="36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2"
V38_SHA="4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12"
FROM_DATE="2021.01.03"; TO_DATE="2026.08.01"; WARMUP_MONTHS=6
EXPERT_NAME="V52SourceAwareTournament"

HERE=Path(__file__).resolve().parent; REPO=HERE.parents[1]
OUT=HERE/"OUTPUT_V52"; CP=OUT/"checkpoint"; DATA_CP=CP/"data"; BUNDLE=OUT/"bundle"
ZIP_OUT=OUT/"v52_source_aware_tournament.zip"; LOG=OUT/"v52_runner.log"
V46_RUNNER=REPO/"runtime"/"v46_expert_breadth"/"RUN_V46_EXPERT_BREADTH_ONE_SHOT.py"
V46_CANONICAL_BUILDER=REPO/"scripts"/"build_v46_expert_breadth_source_canonical.py"
V51_BUILDER=REPO/"scripts"/"build_v51_higher_frequency_source.py"
V52_BUILDER=REPO/"scripts"/"build_v52_source_aware_source.py"
ANALYZER=REPO/"scripts"/"analyze_v52_source_aware.py"
TEST=REPO/"tests"/"test_v52_source_aware_static.py"
SECRET_SCAN=REPO/"scripts"/"secret_scan.py"


def load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(f"cannot load {path}")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

v46=load(V46_RUNNER,"v46_for_v52"); base=v46.base; rec=v46.rec


def run(cmd,*,cwd=None):
    print("+"," ".join(str(x) for x in cmd)); subprocess.run([str(x) for x in cmd],cwd=cwd,check=True)


def capture(cmd,*,cwd=None)->str:
    return subprocess.check_output([str(x) for x in cmd],cwd=cwd,text=True,encoding="utf-8",errors="replace").strip()


def sha(path:Path)->str:return base.sha256(path)


def build_source(expert_dir:Path)->tuple[Path,str]:
    parent=rec.get_accepted_parent(base,expert_dir)
    if sha(parent)!=V38_SHA: raise RuntimeError("accepted V38 parent identity lost")
    v45_source,v45_sha=base.build_source(parent)
    if v45_sha!=V45_SHA: raise RuntimeError(f"V45 source mismatch {v45_sha}")

    v46a=OUT/"V46CanonicalForV52.a.mq5"; v46b=OUT/"V46CanonicalForV52.b.mq5"
    run([sys.executable,V46_CANONICAL_BUILDER,"--source",v45_source,"--output",v46a])
    run([sys.executable,V46_CANONICAL_BUILDER,"--source",v45_source,"--output",v46b])
    if sha(v46a)!=V46_SHA or sha(v46b)!=V46_SHA: raise RuntimeError("canonical V46 deterministic identity lost")

    v51a=OUT/"V51AcceptedForV52.a.mq5"; v51b=OUT/"V51AcceptedForV52.b.mq5"
    run([sys.executable,V51_BUILDER,"--source",v46a,"--output",v51a])
    run([sys.executable,V51_BUILDER,"--source",v46b,"--output",v51b])
    v51_sha=sha(v51a); v51_sha_b=sha(v51b)
    if v51_sha!=V51_ACCEPTED_SHA or v51_sha_b!=V51_ACCEPTED_SHA:
        raise RuntimeError(f"accepted V51 source identity lost a={v51_sha} b={v51_sha_b}")
    print(f"V51_ACCEPTED_SOURCE_PASS sha256={v51_sha}")

    a=OUT/f"{EXPERT_NAME}.base.a.mq5"; b=OUT/f"{EXPERT_NAME}.base.b.mq5"
    run([sys.executable,V52_BUILDER,"--source",v51a,"--output",a])
    run([sys.executable,V52_BUILDER,"--source",v51b,"--output",b])
    ha,hb=sha(a),sha(b)
    if ha!=hb: raise RuntimeError(f"V52 deterministic source mismatch a={ha} b={hb}")
    print(f"V52_SOURCE_SHA256={ha}"); return a,ha


def compile_source(source:Path,source_sha:str,data:Path,expert_dir:Path)->Path:
    installed=expert_dir/f"{EXPERT_NAME}.mq5"; ex5=installed.with_suffix(".ex5"); log=installed.with_suffix(".log"); marker=installed.with_suffix(".compile_source_sha256")
    shutil.copy2(source,installed)
    for p in (ex5,log,marker):
        try:p.unlink()
        except FileNotFoundError:pass
    if base.task_running("metaeditor64.exe"): raise RuntimeError("MetaEditor is open. Close it and rerun.")
    cp=subprocess.run([str(base.METAEDITOR_EXE),f"/compile:{installed}",f"/include:{data/'MQL5'}","/log"]); print(f"METAEDITOR_LAUNCH_RC={cp.returncode}")
    def ready():
        if not ex5.is_file() or ex5.stat().st_size<=0 or not log.is_file():return False
        s=base.compile_summary(log); return bool(s and "0 errors, 0 warnings" in s.lower())
    base.wait_until(ready,120,0.5,"V52 MetaEditor 0/0 + EX5")
    marker.write_text(source_sha+"\n",encoding="utf-8")
    c=OUT/f"{EXPERT_NAME}.compile.txt"; c.write_text(base.decode_compile_log(log),encoding="utf-8")
    print(f"V52_COMPILE_PASS summary={base.compile_summary(log)} ex5_sha256={sha(ex5)}")
    return c


def configure_v46_runtime_helpers():
    v46.OUT=OUT; v46.CP=CP; v46.DATA_CP=DATA_CP; v46.BUNDLE=BUNDLE; v46.LOG=LOG; v46.ZIP_OUT=ZIP_OUT
    v46.EXPERT_NAME=EXPERT_NAME; v46.FROM_DATE=FROM_DATE; v46.TO_DATE=TO_DATE; v46.WARMUP_MONTHS=WARMUP_MONTHS


def package(head:str,source_sha:str,compile_txt:Path)->None:
    analysis=OUT/"v52_source_aware_analysis.json"; summary=OUT/"v52_candidate_summary.csv"; monthly=OUT/"v52_monthly.csv"
    run([sys.executable,ANALYZER,"--run-folder",DATA_CP,"--output",analysis,"--summary-csv",summary,"--monthly-csv",monthly])
    result=json.loads(analysis.read_text(encoding="utf-8"))
    evidence=OUT/"V52_EVIDENCE.txt"
    evidence.write_text("\n".join([
        "V52_SOURCE_AWARE_SINGLE_RUN=1",f"head={head}",f"branch={BRANCH}",f"v46_parent_sha256={V46_SHA}",f"v51_parent_sha256={V51_ACCEPTED_SHA}",f"v52_source_sha256={source_sha}",
        f"from={FROM_DATE}",f"to={TO_DATE}","cold_start=1",f"warmup_months={WARMUP_MONTHS}",
        "baseline=v46_hl10_thr0p05_breadth4","challengers=v52_b4_or_b3_trend,v52_b4_or_b3_bos,v52_b4_or_b3_trend_bos",
        "extra_lane=healthy_eq_3_selected_source_mask","native_broker_orders=0","external_broker_orders=0","risk_changed=0",
        f"status={result['status']}",f"selected={result['selected_candidate']}",""])
        ,encoding="utf-8")

    files=[]
    for p in [DATA_CP/"monthly_summary.csv",DATA_CP/"trades.csv",DATA_CP/"manifest.txt",analysis,summary,monthly,evidence,compile_txt,
              OUT/f"{EXPERT_NAME}.base.a.mq5",V52_BUILDER,ANALYZER,Path(__file__).resolve(),TEST,LOG,
              REPO/"docs"/"adr"/"ADR-052-source-aware-breadth3-opportunity-lane.md",
              REPO/"docs"/"research"/"v51_higher_frequency_results_2026-08-26.md",
              REPO/"docs"/"research"/"v52_source_aware_plan.md",
              REPO/"docs"/"handover"/"CURRENT_STATE.md",REPO/"docs"/"handover"/"RECOVERY_PROMPT.md"]:
        if p.is_file():files.append(p)

    if BUNDLE.exists(): shutil.rmtree(BUNDLE)
    BUNDLE.mkdir(parents=True,exist_ok=True)
    manifest_lines=[]
    used=set()
    for p in files:
        name=p.name
        if name in used: raise RuntimeError(f"duplicate bundle basename: {name}")
        used.add(name)
        dst=BUNDLE/name; shutil.copy2(p,dst); manifest_lines.append(f"{sha(dst)}  {name}")
    manifest=BUNDLE/"bundle_manifest_sha256.txt"; manifest.write_text("\n".join(sorted(manifest_lines))+"\n",encoding="utf-8")

    if ZIP_OUT.exists():ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(BUNDLE.iterdir()):
            if p.is_file():z.write(p,p.name)
    with zipfile.ZipFile(ZIP_OUT) as z:
        bad=z.testzip()
        if bad is not None:raise RuntimeError(f"ZIP CRC failure {bad}")

    print(f"STATUS={result['status']}"); print(f"SELECTED={result['selected_candidate']}")
    print(f"V52_ZIP={ZIP_OUT}"); print(f"V52_ZIP_SHA256={sha(ZIP_OUT)}"); print("V52_PACKAGE_PASS=1")


def main()->int:
    OUT.mkdir(parents=True,exist_ok=True); CP.mkdir(parents=True,exist_ok=True)
    head=capture(["git","rev-parse","HEAD"],cwd=REPO); branch=capture(["git","branch","--show-current"],cwd=REPO)
    print(f"HEAD={head}\nBRANCH={branch}")
    if branch!=BRANCH:raise RuntimeError(f"wrong branch expected={BRANCH} actual={branch}")
    print("V52 one-shot: frozen breadth4 vs source-aware exactly-three-healthy opportunity lanes")

    run([sys.executable,"-m","py_compile",V52_BUILDER,ANALYZER,TEST,Path(__file__).resolve()])
    run([sys.executable,TEST]); run([sys.executable,SECRET_SCAN,REPO])
    data,common,expert_dir,inputs=base.locate_mt5(); print(f"MT5_DATA={data}"); base.verify_tape(inputs)
    source,source_sha=build_source(expert_dir); compile_txt=compile_source(source,source_sha,data,expert_dir)
    if base.task_running("terminal64.exe"): raise RuntimeError("MetaTrader 5 is open. Close it before the single historical tester run.")
    configure_v46_runtime_helpers(); v46.run_mt5_once(data,common,inputs)
    package(head,source_sha,compile_txt)
    return 0


if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}",file=sys.stderr); raise
