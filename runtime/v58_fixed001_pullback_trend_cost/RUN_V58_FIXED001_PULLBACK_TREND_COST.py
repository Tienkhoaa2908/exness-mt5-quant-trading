#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

EXPECTED_BRANCH="agent/v58-fixed001-pullback-trend-cost-research"
WEEK_START_STATE_SHA256="7acf0260b9ab875722ad4888358b21cf4db72d80ec1de6de4ec999676c621259"
V57_EVIDENCE_ZIP_SHA256="c6f3eaeb2c6da585589ab71265eaee236d13eefea54aed9dc8ef84cd8c146bde"
FROM_DATE="2026.08.24"
TO_DATE="2026.08.29"
EXPERT_NAME="V58Fixed001PullbackTrendCost"
FIXED_LOT=0.01

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
OUT=HERE/"OUTPUT_V58"
RUN_CP=OUT/"run"
ZIP_OUT=OUT/"v58_fixed001_pullback_trend_cost_weekly_replay.zip"

V57_RUNNER=REPO/"runtime"/"v57_fixed001_trend_smc"/"RUN_V57_FIXED001_TREND_SMC.py"
V57_BUILDER=REPO/"scripts"/"build_v57_fixed001_trend_smc_source.py"
BUILDER=REPO/"scripts"/"build_v58_fixed001_pullback_trend_cost_source.py"
ANALYZER=REPO/"scripts"/"analyze_v58_fixed001_pullback_trend_cost.py"
STATIC_TEST=REPO/"tests"/"test_v58_fixed001_pullback_trend_cost_static.py"
SECRET_SCAN=REPO/"scripts"/"secret_scan.py"
SEED=REPO/"runtime"/"v57_fixed001_trend_smc"/"accepted_v56_week_start_state_20260824.csv"
ADR=REPO/"docs"/"adr"/"ADR-060-v58-fixed001-pullback-trend-cost-research.md"

def load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(f"cannot load {path}")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

v57=load(V57_RUNNER,"v57_base_for_v58")
v56=v57.v56
base=v57.base

def run(cmd,*,cwd=None):
    print("+"," ".join(str(x) for x in cmd))
    subprocess.run([str(x) for x in cmd],cwd=cwd,check=True)

def capture(cmd,*,cwd=None)->str:
    return subprocess.check_output([str(x) for x in cmd],cwd=cwd,text=True,encoding="utf-8",errors="replace").strip()

def sha(path:Path)->str: return base.sha256(path)

def ensure_repo()->tuple[str,str]:
    branch=capture(["git","branch","--show-current"],cwd=REPO)
    head=capture(["git","rev-parse","HEAD"],cwd=REPO)
    dirty=capture(["git","status","--porcelain"],cwd=REPO)
    print(f"BRANCH={branch}"); print(f"HEAD={head}")
    if branch!=EXPECTED_BRANCH: raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")
    if dirty: raise RuntimeError("working tree must be clean before V58 replay")
    return branch,head

def verify_seed()->None:
    if not SEED.is_file() or SEED.stat().st_size<=0: raise RuntimeError(f"V58 seed missing: {SEED}")
    actual=sha(SEED)
    if actual!=WEEK_START_STATE_SHA256:
        raise RuntimeError(f"V58 week-start seed mismatch expected={WEEK_START_STATE_SHA256} actual={actual}")
    print(f"V58_WEEK_START_STATE_PASS=1 sha256={actual}")
    print(f"V58_PARENT_V57_EVIDENCE_ZIP_SHA256={V57_EVIDENCE_ZIP_SHA256}")
    print("V58_SKIP_WARMUP=1")

def build_source(expert_dir:Path)->tuple[Path,str]:
    v56_source,_=v56.build_source(expert_dir)
    OUT.mkdir(parents=True,exist_ok=True)
    v57_parent=OUT/"V57Fixed001TrendSMC.parent.mq5"
    run([sys.executable,V57_BUILDER,"--source",v56_source,"--output",v57_parent])
    source=OUT/f"{EXPERT_NAME}.mq5"
    run([sys.executable,BUILDER,"--source",v57_parent,"--output",source])
    digest=sha(source)
    print(f"V58_SOURCE_SHA256={digest}")
    return source,digest

def compile_source(source:Path,source_sha:str,data:Path,expert_dir:Path)->tuple[Path,Path,Path]:
    installed=expert_dir/f"{EXPERT_NAME}.mq5"; ex5=installed.with_suffix(".ex5"); log=installed.with_suffix(".log")
    shutil.copy2(source,installed)
    for p in (ex5,log):
        try:p.unlink()
        except FileNotFoundError:pass
    if base.task_running("metaeditor64.exe"): raise RuntimeError("MetaEditor is open before V58 replay")
    cp=subprocess.run([str(base.METAEDITOR_EXE),f"/compile:{installed}",f"/include:{data/'MQL5'}","/log"])
    print(f"METAEDITOR_LAUNCH_RC={cp.returncode}")
    def ready():
        if not ex5.is_file() or ex5.stat().st_size<=0 or not log.is_file(): return False
        s=base.compile_summary(log)
        return bool(s and "0 errors, 0 warnings" in s.lower())
    base.wait_until(ready,120,0.5,"V58 MetaEditor 0/0 + EX5")
    compile_copy=OUT/f"{EXPERT_NAME}.compile.txt"
    compile_copy.write_text(base.decode_compile_log(log),encoding="utf-8")
    print(f"V58_COMPILE_PASS summary={base.compile_summary(log)} ex5_sha256={sha(ex5)}")
    return installed,ex5,compile_copy

def prepare_common(common:Path)->Path:
    root=common/"mt5_quant"/"v58_fixed001_pullback_trend_cost"
    root.parent.mkdir(parents=True,exist_ok=True)
    if root.exists():
        archived=root.parent/f"_v58_previous_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        root.rename(archived); print(f"V58_PREVIOUS_COMMON_ARCHIVED={archived}")
    root.mkdir(parents=True,exist_ok=True)
    dst=root/"seed_state.csv"; shutil.copy2(SEED,dst)
    if sha(dst)!=WEEK_START_STATE_SHA256: raise RuntimeError("V58 common seed copy mismatch")
    return root

def write_config(data:Path)->Path:
    ini=data/"config"/"v58_fixed001_pullback_trend_cost.ini"
    text=f"""[Common]
KeepPrivate=1
NewsEnable=0
[Experts]
AllowLiveTrading=1
AllowDllImport=0
Enabled=1
Account=0
Profile=0
[Tester]
Expert=mt5_quant\\{EXPERT_NAME}.ex5
Symbol=XAUUSDm
Period=M15
Optimization=0
Model=4
FromDate={FROM_DATE}
ToDate={TO_DATE}
ForwardMode=0
Deposit=40
Currency=USD
Leverage=1:200
ExecutionMode=0
OptimizationCriterion=0
UseCloud=0
Visual=0
ShutdownTerminal=1
"""
    base.write_utf16_ini(ini,text)
    OUT.mkdir(parents=True,exist_ok=True); shutil.copy2(ini,OUT/ini.name)
    print(f"V58_CONFIG_PASS sha256={sha(ini)}")
    print("V58_TESTER_MODEL=4"); print("V58_REAL_TICKS=1"); print("V58_SINGLE_REAL_TICK_PASS=1")
    return ini

def newest_complete_run(runs_root:Path,started:float)->Path|None:
    if not runs_root.is_dir(): return None
    out=[]
    for p in runs_root.iterdir():
        if not p.is_dir(): continue
        req=[p/n for n in ("monthly_summary.csv","trades.csv","manifest.txt")]
        if not all(x.is_file() and x.stat().st_size>0 for x in req): continue
        if max(x.stat().st_mtime for x in req)<started-5: continue
        out.append(p)
    return max(out,key=lambda x:x.stat().st_mtime) if out else None

def run_mt5(root:Path,ini:Path)->Path:
    if base.task_running("terminal64.exe"): raise RuntimeError("MetaTrader 5 is open before V58 replay")
    if base.task_running("metaeditor64.exe"): raise RuntimeError("MetaEditor is open before V58 replay")
    started=time.time()
    print(f"RUN_V58_REAL_TICKS from={FROM_DATE} to={TO_DATE} fixed_lot={FIXED_LOT:.2f}")
    cp=subprocess.run([str(base.TERMINAL_EXE),f"/config:{ini}"])
    print(f"V58_MT5_LAUNCH_RC={cp.returncode}")
    rd=newest_complete_run(root/"runs",started)
    if rd is None:
        rd=base.wait_until(lambda:newest_complete_run(root/"runs",started) or False,180,1.0,"V58 complete run artifacts")
    print(f"V58_RUN_DIR={rd}")
    return rd

def collect(root:Path,run_dir:Path)->None:
    if RUN_CP.exists(): shutil.rmtree(RUN_CP)
    RUN_CP.mkdir(parents=True,exist_ok=True)
    for n in ("monthly_summary.csv","trades.csv","manifest.txt"): shutil.copy2(run_dir/n,RUN_CP/n)
    mapping={
        "V55_PRODUCTION_READINESS_EVENTS.csv":"events.csv",
        "V55_PRODUCTION_READINESS_TRANSACTIONS.csv":"transactions.csv",
        "V55_PRODUCTION_READINESS_STATUS.txt":"status.txt",
        "V55_PRODUCTION_READINESS_FINAL.txt":"final.txt",
        "V58_ENTRY_EVAL.csv":"V58_ENTRY_EVAL.csv",
        "seed_state.csv":"state_after_replay.csv",
    }
    for s,d in mapping.items():
        p=root/s
        if p.is_file() and p.stat().st_size>0: shutil.copy2(p,RUN_CP/d)
    for p in [RUN_CP/"trades.csv",RUN_CP/"events.csv",RUN_CP/"transactions.csv",RUN_CP/"V58_ENTRY_EVAL.csv"]:
        if not p.is_file() or p.stat().st_size<=0: raise RuntimeError(f"V58 required evidence missing: {p}")

def analyze()->dict:
    analysis=OUT/"v58_analysis.json"; summary=OUT/"V58_SUMMARY.txt"; report=OUT/"V58_TRADE_REPORT.csv"
    run([sys.executable,ANALYZER,
         "--trades",RUN_CP/"trades.csv","--evals",RUN_CP/"V58_ENTRY_EVAL.csv",
         "--events",RUN_CP/"events.csv","--transactions",RUN_CP/"transactions.csv",
         "--output",analysis,"--summary",summary,"--trade-report",report])
    return json.loads(analysis.read_text(encoding="utf-8"))

def package(branch:str,head:str,source:Path,source_sha:str,compile_txt:Path,result:dict)->None:
    evidence=OUT/"V58_EVIDENCE.txt"
    evidence.write_text("\n".join([
        "V58_FIXED001_PULLBACK_TREND_COST_REPLAY=1",
        f"branch={branch}",f"head={head}",f"source_sha256={source_sha}",
        "candidate=v52_b4_or_b3_trend_bos",f"fixed_lot={FIXED_LOT:.2f}",
        f"from={FROM_DATE}",f"to={TO_DATE}","tester_model=4","real_ticks=1",
        "single_real_tick_pass=1","warmup_rerun=0",
        f"week_start_state_sha256={WEEK_START_STATE_SHA256}",
        f"parent_v57_evidence_zip_sha256={V57_EVIDENCE_ZIP_SHA256}",
        "actual_gate=pullback80","spread_guard=cost_based",
        f"actual_broker_net_usd={result.get('actual_broker_pullback80_gate',{}).get('net_pnl_usd')}",
        "same_week_hypothesis_exploratory=1","tester_only=1",""
    ]),encoding="utf-8")
    files=[source,compile_txt,SEED,ADR,Path(__file__).resolve(),BUILDER,ANALYZER,STATIC_TEST,
           OUT/"v58_fixed001_pullback_trend_cost.ini",OUT/"v58_analysis.json",
           OUT/"V58_SUMMARY.txt",OUT/"V58_TRADE_REPORT.csv",evidence]
    files += [p for p in RUN_CP.iterdir() if p.is_file()]
    stage=OUT/"bundle"
    if stage.exists(): shutil.rmtree(stage)
    stage.mkdir(parents=True)
    used=set(); manifest=[]
    for p in files:
        if not p.is_file(): continue
        name=p.name
        if name in used: name="run__"+name
        used.add(name); dst=stage/name; shutil.copy2(p,dst); manifest.append(f"{sha(dst)}  {name}")
    (stage/"bundle_manifest_sha256.txt").write_text("\n".join(sorted(manifest))+"\n",encoding="utf-8")
    if ZIP_OUT.exists(): ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(stage.iterdir()):
            if p.is_file(): z.write(p,p.name)
    with zipfile.ZipFile(ZIP_OUT) as z:
        bad=z.testzip()
        if bad is not None: raise RuntimeError(f"V58 ZIP CRC failure: {bad}")
    print(f"V58_ZIP={ZIP_OUT}"); print(f"V58_ZIP_SHA256={sha(ZIP_OUT)}"); print("V58_PACKAGE_PASS=1")

def main()->int:
    branch,head=ensure_repo(); verify_seed()
    run([sys.executable,"-m","py_compile",BUILDER,ANALYZER,STATIC_TEST,Path(__file__).resolve()])
    run([sys.executable,STATIC_TEST]); run([sys.executable,SECRET_SCAN,REPO])
    data,common,expert_dir,_=base.locate_mt5(); print(f"MT5_DATA={data}")
    source,source_sha=build_source(expert_dir)
    _,_,compile_txt=compile_source(source,source_sha,data,expert_dir)
    root=prepare_common(common); ini=write_config(data); run_dir=run_mt5(root,ini)
    collect(root,run_dir); result=analyze(); package(branch,head,source,source_sha,compile_txt,result)
    print("V58_DONE=1"); return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}",file=sys.stderr)
        raise
