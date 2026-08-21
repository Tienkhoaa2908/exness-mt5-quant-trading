#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def parse_manifest(text: str) -> list[tuple[str,str]]:
    rows=[]
    for raw in text.splitlines():
        raw=raw.strip()
        if not raw: continue
        if "  " not in raw: raise RuntimeError(f"invalid manifest line: {raw!r}")
        expected,name=raw.split("  ",1)
        if len(expected)!=64 or any(c not in "0123456789abcdefABCDEF" for c in expected): raise RuntimeError(f"invalid SHA256: {expected}")
        if Path(name).name!=name or name in {".",".."}: raise RuntimeError(f"unsafe manifest member: {name!r}")
        rows.append((expected.lower(),name))
    if not rows: raise RuntimeError("manifest is empty")
    return rows

def parse_evidence(text: str) -> dict:
    out={}
    for line in text.splitlines():
        if "=" in line:
            k,v=line.split("=",1); out[k.strip()]=v.strip()
    return out

def analyze(zip_path: Path) -> dict:
    result={"zip":str(zip_path),"zip_sha256":hashlib.sha256(zip_path.read_bytes()).hexdigest(),"testzip":None,"manifest_pass":False,"manifest_files":0,"evidence":{},"summary_kind":None,"summary":None}
    with zipfile.ZipFile(zip_path) as z:
        bad=z.testzip(); result["testzip"]=bad
        if bad: raise RuntimeError(f"ZIP CRC failure: {bad}")
        names=set(z.namelist()); man="bundle_manifest_sha256.txt"
        if man not in names: raise RuntimeError("bundle_manifest_sha256.txt missing")
        rows=parse_manifest(z.read(man).decode("utf-8-sig"))
        for expected,name in rows:
            if name not in names: raise RuntimeError(f"manifest member missing: {name}")
            got=sha256_bytes(z.read(name))
            if got!=expected: raise RuntimeError(f"manifest mismatch {name}: expected={expected} actual={got}")
        result["manifest_pass"]=True; result["manifest_files"]=len(rows)
        for ev in ("V40_EVIDENCE.txt","V39_EVIDENCE.txt"):
            if ev in names:
                result["evidence"]=parse_evidence(z.read(ev).decode("utf-8-sig")); break
        for kind,name in (("v40","v40_upgrade_campaign_summary.json"),("v39","v39_selective_harvest_summary.json")):
            if name in names:
                result["summary_kind"]=kind; result["summary"]=json.loads(z.read(name)); break
    return result

def main()->int:
    ap=argparse.ArgumentParser(description="Verify and summarize one MT5 research ZIP"); ap.add_argument("zip"); ap.add_argument("--json-output"); args=ap.parse_args()
    path=Path(args.zip).resolve()
    if not path.is_file(): raise FileNotFoundError(path)
    result=analyze(path); text=json.dumps(result,indent=2,ensure_ascii=False)
    if args.json_output: Path(args.json_output).write_text(text+"\n",encoding="utf-8")
    print(text); print("BUNDLE_ANALYSIS_PASS"); return 0

if __name__=="__main__": raise SystemExit(main())
