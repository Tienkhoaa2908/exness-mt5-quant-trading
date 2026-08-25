#!/usr/bin/env python3
from __future__ import annotations

import importlib.util, os, shutil, subprocess, sys, time
from datetime import datetime
from pathlib import Path

EXPECTED_BRANCH="agent/v50-execution-probe"
EXPECTED_V49_SOURCE_SHA="b3b012e856d814d36414e26d120674af864fea2c24db0b53f096fe7ba0a8f599"
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
OUT=HERE/"OUTPUT_V50"
V49_RUNNER=REPO/"runtime"/"v49_demo_rehearsal"/"RUN_V49_ONE_SHOT.py"
V50_BUILDER=REPO/"scripts"/"build_v50_execution_probe_source.py"
SUPERVISOR=HERE/"SUPERVISE_V50_EXECUTION_PROBE.py"
SECRET_SCAN=REPO/"scripts"/"secret_scan.py"


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(f"cannot load {path}")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

v49=load_module(V49_RUNNER,"v49_base_for_v50")
base=v49.base


def capture(cmd,*,cwd=None)->str:
    return subprocess.check_output([str(x) for x in cmd],cwd=cwd,text=True,encoding="utf-8",errors="replace").strip()


def run(cmd,*,cwd=None)->None:
    print("+"," ".join(str(x) for x in cmd)); subprocess.run([str(x) for x in cmd],cwd=cwd,check=True)


def kv(path:Path,attempts:int=40,delay:float=0.05)->dict[str,str]:
    """Read a small MT5 status file despite transient Windows share locks."""
    for i in range(attempts):
        try:
            if not path.is_file(): return {}
            text=path.read_text(encoding="utf-8-sig",errors="replace")
            out={}
            for line in text.splitlines():
                if "=" in line:
                    k,v=line.split("=",1); out[k.strip()]=v.strip()
            return out
        except (PermissionError,OSError):
            if i+1>=attempts: raise
            time.sleep(delay)
    return {}


def close_v49_if_flat(common:Path)->None:
    if not base.task_running("terminal64.exe"):
        print("V49_TERMINAL_ALREADY_CLOSED=1"); return
    s=kv(common/"mt5_quant"/"v49"/"V49_DEMO_REHEARSAL_STATUS.txt")
    if not s or not s.get("run_id","").strip(): raise RuntimeError("MT5 running but V49 status/run_id unavailable")
    for key in ("virtual_open","owned_positions","open_pending","close_pending"):
        if s.get(key,"0")!="0": raise RuntimeError(f"V49 not settled: {key}={s.get(key)}. Wait until all four are zero.")
    print(f"V49_FLAT_TRANSITION_PASS run_id={s.get('run_id','')}")
    ps="$p=Get-Process terminal64 -ErrorAction SilentlyContinue; if($p){$p | ForEach-Object {[void]$_.CloseMainWindow()}}"
    subprocess.run(["powershell.exe","-NoProfile","-Command",ps],check=False)
    deadline=time.time()+45
    while time.time()<deadline:
        if not base.task_running("terminal64.exe"):
            print("V49_TERMINAL_CLOSED_GRACEFULLY=1"); return
        time.sleep(1)
    raise RuntimeError("MT5 did not close within 45s")


def transition_state(common:Path)->Path:
    src=common/"mt5_quant"/"paper"/"v49_demo_rehearsal_state.csv"
    if src.is_file():
        print(f"V50_TRANSITION_SOURCE=v49_state sha256={base.sha256(src)} path={src}"); return src
    src=v49.v48.accepted_v46_state(); print(f"V50_TRANSITION_SOURCE=accepted_v46_state path={src}"); return src


def archive_old(common:Path)->None:
    found=[]; root=common/"mt5_quant"/"v50"; paper=common/"mt5_quant"/"paper"
    if root.is_dir(): found.extend(p for p in root.rglob("*") if p.is_file())
    p=paper/"v50_execution_probe_state.csv"
    if p.is_file(): found.append(p)
    if not found: return
    archive=common/"mt5_quant"/f"_v50_previous_{datetime.now().strftime('%Y%m%d_%H%M%S')}"; archive.mkdir(parents=True,exist_ok=False)
    for src in found:
        rel=src.relative_to(common/"mt5_quant"); dst=archive/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.move(str(src),str(dst))
    print(f"V50_PREVIOUS_EVIDENCE_ARCHIVED={archive}")


def build_v50(data:Path,expert_dir:Path)->tuple[Path,str]:
    v49_source,v49_sha=v49.build_v49(data,expert_dir)
    if v49_sha!=EXPECTED_V49_SOURCE_SHA: raise RuntimeError(f"V49 source mismatch expected={EXPECTED_V49_SOURCE_SHA} actual={v49_sha}")
    OUT.mkdir(parents=True,exist_ok=True); out=OUT/"V50ExecutionProbe.mq5"
    run([sys.executable,V50_BUILDER,"--source",v49_source,"--output",out])
    digest=base.sha256(out); print(f"V50_SOURCE_SHA256={digest}"); return out,digest


def compile_v50(source:Path,source_sha:str,data:Path)->tuple[Path,Path]:
    root=data/"MQL5"/"Experts"; installed=root/"V50ExecutionProbe.mq5"; ex5=installed.with_suffix(".ex5"); log=installed.with_suffix(".log"); marker=installed.with_suffix(".compile_source_sha256")
    shutil.copy2(source,installed)
    for p in (ex5,log,marker):
        try:p.unlink()
        except FileNotFoundError:pass
    if base.task_running("metaeditor64.exe"): raise RuntimeError("MetaEditor is open")
    cp=subprocess.run([str(base.METAEDITOR_EXE),f"/compile:{installed}",f"/include:{data/'MQL5'}","/log"]); print(f"METAEDITOR_LAUNCH_RC={cp.returncode}")
    def ready()->bool:
        if not ex5.is_file() or ex5.stat().st_size<=0 or not log.is_file(): return False
        s=base.compile_summary(log); return bool(s and "0 errors, 0 warnings" in s.lower())
    base.wait_until(ready,120,0.5,"V50 MetaEditor 0/0 + EX5"); marker.write_text(source_sha+"\n",encoding="utf-8")
    print(f"V50_COMPILE_PASS summary={base.compile_summary(log)} ex5_sha256={base.sha256(ex5)}"); return installed,ex5


def seed(common:Path,src:Path)->Path:
    paper=common/"mt5_quant"/"paper"; paper.mkdir(parents=True,exist_ok=True); dst=paper/"v50_execution_probe_state.csv"; shutil.copy2(src,dst)
    if base.sha256(dst)!=base.sha256(src): raise RuntimeError("V50 state copy mismatch")
    print(f"V50_STATE_SEEDED sha256={base.sha256(dst)} path={dst}"); return dst


def write_config(data:Path)->Path:
    ini=data/"config"/"v50_execution_probe.ini"
    text="""[Common]\nKeepPrivate=1\nNewsEnable=0\n[Experts]\nAllowLiveTrading=1\nAllowDllImport=0\nEnabled=1\nAccount=0\nProfile=0\n[StartUp]\nExpert=V50ExecutionProbe\nSymbol=XAUUSDm\nPeriod=M15\n"""
    base.write_utf16_ini(ini,text); decoded=ini.read_bytes().decode("utf-16")
    for token in ("AllowLiveTrading=1","AllowDllImport=0","Enabled=1","Expert=V50ExecutionProbe","Symbol=XAUUSDm","Period=M15"):
        if token not in decoded: raise RuntimeError(f"V50 config missing {token}")
    print(f"V50_CONFIG_PASS sha256={base.sha256(ini)} path={ini}"); return ini


def wait_ready(common:Path)->dict[str,str]:
    status=common/"mt5_quant"/"v50"/"V50_EXECUTION_PROBE_STATUS.txt"; deadline=time.time()+120
    while time.time()<deadline:
        s=kv(status)
        if s:
            if s.get("ready")=="1" and s.get("account_mode")=="DEMO" and s.get("run_id","").strip(): print("V50_EXECUTION_PROBE_READY=1"); return s
            if s.get("probe_halted")=="1": raise RuntimeError(f"V50 halted at startup: {s.get('probe_halt_reason','')}")
        if not base.task_running("terminal64.exe"): raise RuntimeError("MT5 exited before V50 READY")
        time.sleep(1)
    raise RuntimeError("timeout waiting for V50 READY")


def start_supervisor()->int:
    py=Path(sys.executable); pythonw=py.with_name("pythonw.exe"); exe=pythonw if pythonw.is_file() else py; flags=0
    if os.name=="nt": flags=getattr(subprocess,"DETACHED_PROCESS",0x00000008)|getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0x00000200)
    proc=subprocess.Popen([str(exe),str(SUPERVISOR)],cwd=str(REPO),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags,close_fds=True)
    print(f"V50_SUPERVISOR_PID={proc.pid}"); return proc.pid


def main()->int:
    branch=capture(["git","branch","--show-current"],cwd=REPO)
    if branch!=EXPECTED_BRANCH: raise RuntimeError(f"checkout {EXPECTED_BRANCH} first; actual={branch}")
    print(f"BRANCH={branch}\nHEAD={capture(['git','rev-parse','HEAD'],cwd=REPO)}")
    print("V50 MODE: frozen breadth4 + DEMO execution probe; alpha is not relaxed.")
    run([sys.executable,SECRET_SCAN,REPO]); data,common,expert_dir,_=base.locate_mt5(); print(f"MT5_DATA={data}")
    if base.task_running("metaeditor64.exe"): raise RuntimeError("MetaEditor is open")
    source,source_sha=build_v50(data,expert_dir); compile_v50(source,source_sha,data); print("V50_PRETRANSITION_BUILD_COMPILE_PASS=1")
    close_v49_if_flat(common); src=transition_state(common); archive_old(common); seed(common,src); ini=write_config(data)
    print("LAUNCH V50 EXECUTION PROBE"); proc=subprocess.Popen([str(base.TERMINAL_EXE),f"/config:{ini}"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); print(f"TERMINAL_PID={proc.pid}")
    status=wait_ready(common); start_supervisor()
    print("V50_EXECUTION_PROBE_STARTED=1"); print(f"RUN_ID={status.get('run_id','')}"); print(f"PROBE_TARGET={status.get('probe_target_round_trips','3')}"); print("ALPHA=breadth4_frozen"); print("DEMO_BROKER_EXECUTION=1"); print("REAL_MONEY_AUTHORIZED=0")
    return 0


if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}",file=sys.stderr); raise
