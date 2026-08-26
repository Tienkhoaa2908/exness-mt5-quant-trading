#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import time
import zipfile
from datetime import datetime
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
OUT=HERE/"OUTPUT_V53"
V45_BASE=REPO/"runtime"/"v45_multiyear_validation"/"RUN_V45_MULTIYEAR_ONE_SHOT.py"


def load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(f"cannot load {path}")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

base=load(V45_BASE,"v45_base_v53_supervisor")


def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()


def read_retry(path:Path,attempts:int=80,delay:float=0.05)->str:
    for i in range(attempts):
        try:return path.read_text(encoding="utf-8-sig",errors="replace")
        except (PermissionError,OSError):
            if i+1>=attempts:raise
            time.sleep(delay)
    return ""


def kv(path:Path)->dict[str,str]:
    if not path.is_file():return {}
    out={}
    for line in read_retry(path).replace("\\r\\n","\n").splitlines():
        if "=" in line:
            k,v=line.split("=",1);out[k.strip()]=v.strip()
    return out


def add_tree(files:list[tuple[Path,str]],root:Path,prefix:str)->None:
    if not root.exists():return
    for p in root.rglob("*"):
        if p.is_file():files.append((p,f"{prefix}/{p.relative_to(root).as_posix()}"))


def package(common:Path,reason:str)->Path:
    OUT.mkdir(parents=True,exist_ok=True)
    paper=common/"mt5_quant"/"paper"; v53=common/"mt5_quant"/"v53"
    status=v53/"V53_DEMO_REHEARSAL_STATUS.txt"; s=kv(status)
    run_folder=s.get("run_folder","").replace("\\","/"); run_dir=common/Path(run_folder) if run_folder else None
    files=[]
    for p in (
        v53/"V53_DEMO_REHEARSAL_STATUS.txt",
        v53/"V53_DEMO_REHEARSAL_FINAL.txt",
        v53/"V53_DEMO_REHEARSAL_EVENTS.csv",
        v53/"V53_DEMO_REHEARSAL_TRANSACTIONS.csv",
        paper/"v53_demo_rehearsal_state.csv",
        paper/"V53_DEMO_REHEARSAL_LATEST.txt",
        paper/"V53_DEMO_REHEARSAL_INIT.txt",
    ):
        if p.is_file():files.append((p,f"common/{p.relative_to(common).as_posix()}"))
    if run_dir is not None:add_tree(files,run_dir,"run")
    for p in (
        OUT/"V53TrendBosDemoConfirmation.mq5",
        OUT/"V53TrendBosDemoConfirmation.compile.txt",
        REPO/"scripts"/"build_v53_trend_bos_demo_confirmation_source.py",
        REPO/"runtime"/"v53_trend_bos_demo"/"RUN_V53_TREND_BOS_DEMO.py",
        REPO/"runtime"/"v53_trend_bos_demo"/"SUPERVISE_V53_TREND_BOS_DEMO.py",
        REPO/"tests"/"test_v53_trend_bos_demo_static.py",
        REPO/"docs"/"research"/"v52r_real_tick_results_2026-08-26.md",
    ):
        if p.is_file():files.append((p,f"repo/{p.name}"))
    meta=OUT/"v53_supervisor_final.txt"
    meta.write_text(f"packaged_at={datetime.now().isoformat(timespec='seconds')}\nreason={reason}\nrun_id={s.get('run_id','')}\nmarket_days={s.get('market_days','')}\nround_trips={s.get('round_trips','')}\nrequests={s.get('requests','')}\nrejects={s.get('rejects','')}\n",encoding="utf-8")
    files.append((meta,"v53_supervisor_final.txt"))
    manifest=OUT/"bundle_manifest_sha256.txt"
    manifest.write_text("\n".join(f"{sha(src)}  {arc}" for src,arc in sorted(files,key=lambda x:x[1]))+"\n",encoding="utf-8")
    files.append((manifest,"bundle_manifest_sha256.txt"))
    zpath=OUT/f"V53_TREND_BOS_DEMO_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(zpath,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for src,arc in files:z.write(src,arc)
    with zipfile.ZipFile(zpath) as z:
        bad=z.testzip()
        if bad is not None:raise RuntimeError(f"ZIP CRC failure {bad}")
    (OUT/"LATEST_V53_ZIP.txt").write_text(f"path={zpath}\nsha256={sha(zpath)}\nreason={reason}\n",encoding="utf-8")
    return zpath


def main()->int:
    _,common,_,_=base.locate_mt5(); v53=common/"mt5_quant"/"v53"
    final=v53/"V53_DEMO_REHEARSAL_FINAL.txt"; status=v53/"V53_DEMO_REHEARSAL_STATUS.txt"
    OUT.mkdir(parents=True,exist_ok=True); log=OUT/"v53_supervisor.log"
    deadline=time.time()+8*86400; last=0.0; stale=None
    while time.time()<deadline:
        if final.is_file() and final.stat().st_size>0:
            verdict=kv(final).get("verdict","FINAL"); z=package(common,f"EA_FINAL_{verdict}")
            with log.open("a",encoding="utf-8") as fh:fh.write(f"{datetime.now().isoformat()} FINAL={verdict} ZIP={z} SHA={sha(z)}\n")
            return 0
        if status.is_file():
            mt=status.stat().st_mtime
            if mt>last:last=mt;stale=None
            elif stale is None:stale=time.time()
            elif time.time()-stale>300:
                with log.open("a",encoding="utf-8") as fh:fh.write(f"{datetime.now().isoformat()} WARNING=status_stale_gt_300s\n")
                stale=time.time()
        time.sleep(30)
    z=package(common,"SUPERVISOR_8D_TIMEOUT_NO_EA_FINAL")
    with log.open("a",encoding="utf-8") as fh:fh.write(f"{datetime.now().isoformat()} TIMEOUT ZIP={z} SHA={sha(z)}\n")
    return 2

if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as exc:
        OUT.mkdir(parents=True,exist_ok=True);(OUT/"v53_supervisor_fatal.txt").write_text(f"{type(exc).__name__}: {exc}\n",encoding="utf-8");raise
