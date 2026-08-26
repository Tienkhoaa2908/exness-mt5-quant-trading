#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

EXPECTED_BRANCH="agent/v53-trend-bos-demo-confirmation"
V48_SOURCE_SHA="ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa"
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
OUT=HERE/"OUTPUT_V53"
V48_RUNNER=REPO/"runtime"/"v48_demo_paper"/"RUN_V48_DEMO_PAPER_START.py"
BUILDER=REPO/"scripts"/"build_v53_trend_bos_demo_confirmation_source.py"
SUPERVISOR=HERE/"SUPERVISE_V53_TREND_BOS_DEMO.py"
TEST=REPO/"tests"/"test_v53_trend_bos_demo_static.py"
SECRET_SCAN=REPO/"scripts"/"secret_scan.py"
EXPERT_NAME="V53TrendBosDemoConfirmation"


def load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(f"cannot load {path}")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

v48=load(V48_RUNNER,"v48_base_for_v53"); base=v48.base


def run(cmd,*,cwd=None):
    print("+"," ".join(str(x) for x in cmd)); subprocess.run([str(x) for x in cmd],cwd=cwd,check=True)


def capture(cmd,*,cwd=None)->str:
    return subprocess.check_output([str(x) for x in cmd],cwd=cwd,text=True,encoding="utf-8",errors="replace").strip()


def kv_retry(path:Path,attempts:int=80,delay:float=0.05)->dict[str,str]:
    for i in range(attempts):
        try:
            if not path.is_file(): return {}
            text=path.read_text(encoding="utf-8-sig",errors="replace")
            out={}
            for line in text.replace("\\r\\n","\n").splitlines():
                if "=" in line:
                    k,v=line.split("=",1); out[k.strip()]=v.strip()
            return out
        except (PermissionError,OSError):
            if i+1>=attempts: raise
            time.sleep(delay)
    return {}


def build_v53(expert_dir:Path)->tuple[Path,str]:
    v46=v48.accepted_v46_source(expert_dir)
    parent=v48.build_source(v46)
    if base.sha256(parent)!=V48_SOURCE_SHA: raise RuntimeError("canonical V48 parent identity mismatch")
    OUT.mkdir(parents=True,exist_ok=True)
    out=OUT/f"{EXPERT_NAME}.mq5"
    run([sys.executable,BUILDER,"--source",parent,"--output",out])
    digest=base.sha256(out); print(f"V53_SOURCE_SHA256={digest}"); return out,digest


def compile_v53(source:Path,source_sha:str,data:Path)->tuple[Path,Path,Path]:
    root=data/"MQL5"/"Experts"; root.mkdir(parents=True,exist_ok=True)
    installed=root/f"{EXPERT_NAME}.mq5"; ex5=installed.with_suffix(".ex5"); log=installed.with_suffix(".log"); marker=installed.with_suffix(".compile_source_sha256")
    shutil.copy2(source,installed)
    for p in (ex5,log,marker):
        try:p.unlink()
        except FileNotFoundError:pass
    if base.task_running("metaeditor64.exe"): raise RuntimeError("MetaEditor is open. Close it and rerun.")
    cp=subprocess.run([str(base.METAEDITOR_EXE),f"/compile:{installed}",f"/include:{data/'MQL5'}","/log"]); print(f"METAEDITOR_LAUNCH_RC={cp.returncode}")
    def ready():
        if not ex5.is_file() or ex5.stat().st_size<=0 or not log.is_file(): return False
        s=base.compile_summary(log); return bool(s and "0 errors, 0 warnings" in s.lower())
    base.wait_until(ready,120,0.5,"V53 MetaEditor 0/0 + EX5")
    marker.write_text(source_sha+"\n",encoding="utf-8")
    compile_copy=OUT/f"{EXPERT_NAME}.compile.txt"; compile_copy.write_text(base.decode_compile_log(log),encoding="utf-8")
    print(f"V53_COMPILE_PASS summary={base.compile_summary(log)} ex5_sha256={base.sha256(ex5)}")
    return installed,ex5,compile_copy


def choose_state(common:Path)->Path:
    paper=common/"mt5_quant"/"paper"
    for name in ("v50_execution_probe_state.csv","v49_demo_rehearsal_state.csv","v48_demo_paper_state.csv"):
        p=paper/name
        if p.is_file() and p.stat().st_size>0:
            print(f"V53_STATE_SOURCE={name} sha256={base.sha256(p)}"); return p
    p=v48.accepted_v46_state(); print(f"V53_STATE_SOURCE=accepted_v46_state sha256={base.sha256(p)}"); return p


def archive_old(common:Path)->None:
    root=common/"mt5_quant"/"v53"; paper=common/"mt5_quant"/"paper"
    found=[]
    if root.is_dir(): found.extend(p for p in root.rglob("*") if p.is_file())
    for name in ("v53_demo_rehearsal_state.csv","V53_DEMO_REHEARSAL_LATEST.txt","V53_DEMO_REHEARSAL_INIT.txt"):
        p=paper/name
        if p.is_file(): found.append(p)
    if not found:return
    dstroot=common/"mt5_quant"/f"_v53_previous_{datetime.now().strftime('%Y%m%d_%H%M%S')}"; dstroot.mkdir(parents=True,exist_ok=False)
    for src in found:
        rel=src.relative_to(common/"mt5_quant"); dst=dstroot/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.move(str(src),str(dst))
    print(f"V53_PREVIOUS_EVIDENCE_ARCHIVED={dstroot}")


def seed_state(common:Path,source:Path)->Path:
    paper=common/"mt5_quant"/"paper"; paper.mkdir(parents=True,exist_ok=True)
    dst=paper/"v53_demo_rehearsal_state.csv"; shutil.copy2(source,dst)
    if base.sha256(dst)!=base.sha256(source): raise RuntimeError("V53 state copy mismatch")
    print(f"V53_STATE_SEEDED sha256={base.sha256(dst)} path={dst}"); return dst


def write_config(data:Path)->Path:
    ini=data/"config"/"v53_trend_bos_demo_confirmation.ini"
    text=f"""[Common]\nKeepPrivate=1\nNewsEnable=0\n[Experts]\nAllowLiveTrading=1\nAllowDllImport=0\nEnabled=1\nAccount=0\nProfile=0\n[StartUp]\nExpert={EXPERT_NAME}\nSymbol=XAUUSDm\nPeriod=M15\n"""
    base.write_utf16_ini(ini,text)
    decoded=ini.read_bytes().decode("utf-16")
    for token in ("AllowLiveTrading=1","AllowDllImport=0","Enabled=1",f"Expert={EXPERT_NAME}","Symbol=XAUUSDm","Period=M15"):
        if token not in decoded: raise RuntimeError(f"V53 config missing {token}")
    print(f"V53_CONFIG_PASS sha256={base.sha256(ini)} path={ini}"); return ini


def wait_ready(common:Path)->dict[str,str]:
    status=common/"mt5_quant"/"v53"/"V53_DEMO_REHEARSAL_STATUS.txt"
    deadline=time.time()+120
    while time.time()<deadline:
        s=kv_retry(status)
        if s:
            if s.get("account_mode")=="DEMO" and s.get("terminal_trade_allowed")=="1" and s.get("mql_trade_allowed")=="1" and s.get("terminal_dlls_allowed")=="0" and s.get("real_money_authorized")=="0" and s.get("run_id","").strip():
                print("V53_DEMO_CONFIRMATION_READY=1"); return s
            if s.get("halted")=="1": raise RuntimeError(f"V53 halted during startup reason={s.get('halt_reason','')}")
        if not base.task_running("terminal64.exe"): raise RuntimeError("MT5 exited before V53 READY")
        time.sleep(1)
    raise RuntimeError("timeout waiting for V53 READY")


def start_supervisor()->int:
    py=Path(sys.executable); pythonw=py.with_name("pythonw.exe"); exe=pythonw if pythonw.is_file() else py
    flags=0
    if os.name=="nt": flags=getattr(subprocess,"DETACHED_PROCESS",0x8)|getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0x200)
    proc=subprocess.Popen([str(exe),str(SUPERVISOR)],cwd=str(REPO),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags,close_fds=True)
    print(f"V53_SUPERVISOR_PID={proc.pid}"); return proc.pid


def main()->int:
    branch=capture(["git","branch","--show-current"],cwd=REPO); head=capture(["git","rev-parse","HEAD"],cwd=REPO)
    print(f"BRANCH={branch}\nHEAD={head}")
    if branch!=EXPECTED_BRANCH: raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")
    print("V53: selected V52R trend+bos candidate, natural broker-DEMO confirmation only")
    run([sys.executable,"-m","py_compile",BUILDER,TEST,Path(__file__).resolve(),SUPERVISOR])
    run([sys.executable,TEST]); run([sys.executable,SECRET_SCAN,REPO])
    data,common,expert_dir,_=base.locate_mt5(); print(f"MT5_DATA={data}")
    source,source_sha=build_v53(expert_dir); compile_v53(source,source_sha,data); print("V53_PRESTART_BUILD_COMPILE_PASS=1")
    if base.task_running("terminal64.exe"): raise RuntimeError("MetaTrader 5 is open. Close it before V53 DEMO confirmation start.")
    state=choose_state(common); archive_old(common); seed_state(common,state); ini=write_config(data)
    proc=subprocess.Popen([str(base.TERMINAL_EXE),f"/config:{ini}"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); print(f"TERMINAL_PID={proc.pid}")
    status=wait_ready(common); start_supervisor()
    print("V53_TREND_BOS_DEMO_STARTED=1")
    print(f"RUN_ID={status.get('run_id','')}")
    print(f"MARKET_DAYS={status.get('market_days','0')}")
    print(f"ROUND_TRIPS={status.get('round_trips','0')}")
    print("TARGET=2_market_days_and_1_natural_round_trip")
    print("DEMO_BROKER_EXECUTION=1")
    print("REAL_MONEY_AUTHORIZED=0")
    print("Keep MT5/PC/Internet running. Detached supervisor packages one ZIP after FINAL.")
    return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}",file=sys.stderr); raise
