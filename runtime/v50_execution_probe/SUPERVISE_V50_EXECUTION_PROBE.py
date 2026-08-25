#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, time, zipfile
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent; REPO=HERE.parents[1]; OUT=HERE/"OUTPUT_V50"; V49_SUP=REPO/"runtime"/"v49_demo_rehearsal"/"SUPERVISE_V49_ONE_SHOT.py"
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
v49sup=load(V49_SUP,"v49sup_for_v50"); base=v49sup.base
def sha256(path):
    h=hashlib.sha256();
    with path.open("rb") as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()
def kv(path):
    out={}
    if not path.is_file():return out
    for line in path.read_text(encoding="utf-8-sig",errors="replace").splitlines():
        if "=" in line:k,v=line.split("=",1);out[k.strip()]=v.strip()
    return out
def add_tree(files,root,prefix):
    if root.exists():
        for p in root.rglob("*"):
            if p.is_file():files.append((p,f"{prefix}/{p.relative_to(root).as_posix()}"))
def package(common,reason):
    OUT.mkdir(parents=True,exist_ok=True);v50=common/"mt5_quant"/"v50";v49=common/"mt5_quant"/"v49";paper=common/"mt5_quant"/"paper";s=kv(v50/"V50_EXECUTION_PROBE_STATUS.txt")
    run_id=s.get("run_id","");run_dir=common/"mt5_quant"/"runs"/run_id if run_id else None;files=[]
    for p in (v50/"V50_EXECUTION_PROBE_STATUS.txt",v50/"V50_EXECUTION_PROBE_FINAL.txt",v50/"V50_EXECUTION_PROBE_EVENTS.csv",v50/"V50_EXECUTION_PROBE_TRANSACTIONS.csv",v49/"V49_DEMO_REHEARSAL_STATUS.txt",v49/"V49_DEMO_REHEARSAL_EVENTS.csv",v49/"V49_DEMO_REHEARSAL_TRANSACTIONS.csv",paper/"v50_execution_probe_state.csv"):
        if p.is_file():files.append((p,f"common/{p.relative_to(common).as_posix()}"))
    if run_dir is not None:add_tree(files,run_dir,"run")
    meta=OUT/"v50_supervisor_final.txt";meta.write_text(f"packaged_at={datetime.now().isoformat(timespec='seconds')}\nreason={reason}\nrun_id={run_id}\n",encoding="utf-8");files.append((meta,"v50_supervisor_final.txt"))
    manifest=OUT/"bundle_manifest_sha256.txt";manifest.write_text("\n".join(f"{sha256(src)}  {arc}" for src,arc in sorted(files,key=lambda x:x[1]))+"\n",encoding="utf-8");files.append((manifest,"bundle_manifest_sha256.txt"))
    z=OUT/f"V50_EXECUTION_PROBE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(z,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as zf:
        for src,arc in files:zf.write(src,arc)
    with zipfile.ZipFile(z,"r") as zf:
        bad=zf.testzip();
        if bad is not None:raise RuntimeError(f"ZIP CRC failure: {bad}")
    (OUT/"LATEST_V50_ZIP.txt").write_text(f"path={z}\nsha256={sha256(z)}\nreason={reason}\n",encoding="utf-8");return z
def main():
    _,common,_,_=base.locate_mt5();v50=common/"mt5_quant"/"v50";final=v50/"V50_EXECUTION_PROBE_FINAL.txt";status=v50/"V50_EXECUTION_PROBE_STATUS.txt";OUT.mkdir(parents=True,exist_ok=True);log=OUT/"v50_supervisor.log";deadline=time.time()+5*3600;last=0.0;stale=None
    while time.time()<deadline:
        if final.is_file() and final.stat().st_size>0:
            verdict=kv(final).get("verdict","FINAL");z=package(common,f"EA_FINAL_{verdict}");log.open("a",encoding="utf-8").write(f"{datetime.now().isoformat()} FINAL={verdict} ZIP={z} SHA={sha256(z)}\n");return 0
        if status.is_file():
            mt=status.stat().st_mtime
            if mt>last:last=mt;stale=None
            elif stale is None:stale=time.time()
            elif time.time()-stale>300:log.open("a",encoding="utf-8").write(f"{datetime.now().isoformat()} WARNING=status_stale_gt_300s\n");stale=time.time()
        time.sleep(15)
    z=package(common,"SUPERVISOR_5H_TIMEOUT_NO_EA_FINAL");log.open("a",encoding="utf-8").write(f"{datetime.now().isoformat()} TIMEOUT ZIP={z} SHA={sha256(z)}\n");return 2
if __name__=="__main__":raise SystemExit(main())
