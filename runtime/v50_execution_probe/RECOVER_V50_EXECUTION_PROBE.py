#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import os
import time
import zipfile
from datetime import datetime
from pathlib import Path

REPO=Path(os.environ.get("V50_REPO",Path.cwd())).resolve()
OUT=REPO/"runtime"/"v50_execution_probe"/"OUTPUT_V50"
V45_BASE=REPO/"runtime"/"v45_multiyear_validation"/"RUN_V45_MULTIYEAR_ONE_SHOT.py"


def load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(f"cannot load {path}")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

base=load(V45_BASE,"v45_base_v50_recovery")


def read_bytes_retry(path:Path,attempts:int=80,delay:float=0.05)->bytes:
    for i in range(attempts):
        try:return path.read_bytes()
        except (PermissionError,OSError):
            if i+1>=attempts:raise
            time.sleep(delay)
    raise RuntimeError(f"unreadable path: {path}")


def kv_bytes(data:bytes)->dict[str,str]:
    text=data.decode("utf-8-sig",errors="replace");out={}
    for line in text.splitlines():
        if "=" in line:
            k,v=line.split("=",1);out[k.strip()]=v.strip()
    return out


def maybe_bytes(path:Path)->bytes|None:
    if not path.is_file():return None
    return read_bytes_retry(path)


def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()


def main()->int:
    _,common,_,_=base.locate_mt5()
    v50=common/"mt5_quant"/"v50";v49=common/"mt5_quant"/"v49";paper=common/"mt5_quant"/"paper"
    status_path=v50/"V50_EXECUTION_PROBE_STATUS.txt";final_path=v50/"V50_EXECUTION_PROBE_FINAL.txt"

    final_data=None
    deadline=time.time()+120
    while time.time()<deadline:
        final_data=maybe_bytes(final_path)
        if final_data:break
        time.sleep(1)

    status_data=maybe_bytes(status_path)
    status=kv_bytes(status_data) if status_data else {}
    final=kv_bytes(final_data) if final_data else {}
    run_id=status.get("run_id","")

    print(f"V50_RECOVERY_RUN_ID={run_id}")
    print(f"PROBE_ROUND_TRIPS={status.get('probe_round_trips','UNKNOWN')}")
    print(f"PROBE_REQUESTS={status.get('probe_requests','UNKNOWN')}")
    print(f"PROBE_REJECTS={status.get('probe_rejects','UNKNOWN')}")
    print(f"PROBE_POSITIONS={status.get('probe_positions','UNKNOWN')}")
    print(f"PROBE_HALTED={status.get('probe_halted','UNKNOWN')}")
    print(f"EA_FINAL_FOUND={1 if final_data else 0}")
    if final:print(f"EA_VERDICT={final.get('verdict','UNKNOWN')}")

    files:list[tuple[str,bytes]]=[]
    candidates=[
        (status_path,"common/mt5_quant/v50/V50_EXECUTION_PROBE_STATUS.txt"),
        (final_path,"common/mt5_quant/v50/V50_EXECUTION_PROBE_FINAL.txt"),
        (v50/"V50_EXECUTION_PROBE_EVENTS.csv","common/mt5_quant/v50/V50_EXECUTION_PROBE_EVENTS.csv"),
        (v50/"V50_EXECUTION_PROBE_TRANSACTIONS.csv","common/mt5_quant/v50/V50_EXECUTION_PROBE_TRANSACTIONS.csv"),
        (v49/"V49_DEMO_REHEARSAL_STATUS.txt","common/mt5_quant/v49/V49_DEMO_REHEARSAL_STATUS.txt"),
        (v49/"V49_DEMO_REHEARSAL_EVENTS.csv","common/mt5_quant/v49/V49_DEMO_REHEARSAL_EVENTS.csv"),
        (v49/"V49_DEMO_REHEARSAL_TRANSACTIONS.csv","common/mt5_quant/v49/V49_DEMO_REHEARSAL_TRANSACTIONS.csv"),
        (paper/"v50_execution_probe_state.csv","common/mt5_quant/paper/v50_execution_probe_state.csv"),
    ]
    for path,arc in candidates:
        data=maybe_bytes(path)
        if data is not None:files.append((arc,data))

    if run_id:
        run_dir=common/"mt5_quant"/"runs"/run_id
        if run_dir.is_dir():
            for p in sorted(run_dir.rglob("*")):
                if p.is_file():
                    try:data=read_bytes_retry(p)
                    except OSError:continue
                    files.append((f"run/{p.relative_to(run_dir).as_posix()}",data))

    reason=(f"EA_FINAL_{final.get('verdict','FINAL')}" if final_data else "RECOVERY_NO_EA_FINAL")
    meta=(f"packaged_at={datetime.now().isoformat(timespec='seconds')}\nreason={reason}\nrun_id={run_id}\n"
          f"probe_round_trips={status.get('probe_round_trips','')}\n"
          f"probe_requests={status.get('probe_requests','')}\n"
          f"probe_rejects={status.get('probe_rejects','')}\n").encode()
    files.append(("v50_recovery_final.txt",meta))

    manifest="\n".join(f"{sha(data)}  {arc}" for arc,data in sorted(files))+"\n"
    manifest_data=manifest.encode();files.append(("bundle_manifest_sha256.txt",manifest_data))

    OUT.mkdir(parents=True,exist_ok=True)
    z=OUT/f"V50_EXECUTION_PROBE_RECOVERED_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(z,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as zf:
        for arc,data in files:zf.writestr(arc,data)
    with zipfile.ZipFile(z,"r") as zf:
        bad=zf.testzip()
        if bad is not None:raise RuntimeError(f"ZIP CRC failure: {bad}")
    zsha=hashlib.sha256(z.read_bytes()).hexdigest()
    (OUT/"LATEST_V50_ZIP.txt").write_text(f"path={z}\nsha256={zsha}\nreason={reason}\n",encoding="utf-8")
    print(f"V50_RECOVERY_ZIP={z}")
    print(f"V50_RECOVERY_ZIP_SHA256={zsha}")
    print(f"V50_RECOVERY_REASON={reason}")
    print("V50_RECOVERY_PACKAGE_PASS=1")
    return 0

if __name__=="__main__":raise SystemExit(main())
