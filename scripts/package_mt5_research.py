#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def parse_manifest(path: Path) -> list[tuple[str,str]]:
    rows=[]
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        raw=raw.strip()
        if not raw:
            continue
        if "  " not in raw:
            raise RuntimeError(f"invalid manifest line: {raw!r}")
        h,name=raw.split("  ",1)
        if len(h)!=64 or any(c not in "0123456789abcdefABCDEF" for c in h):
            raise RuntimeError(f"invalid SHA256 in manifest: {h}")
        if Path(name).name != name or name in {".",".."}:
            raise RuntimeError(f"unsafe manifest filename: {name!r}")
        rows.append((h.lower(),name))
    if not rows:
        raise RuntimeError("manifest is empty")
    return rows

def verify_source(source: Path) -> list[tuple[str,str]]:
    manifest=source/"bundle_manifest_sha256.txt"
    if not manifest.is_file():
        raise RuntimeError(f"bundle_manifest_sha256.txt missing: {manifest}")
    rows=parse_manifest(manifest)
    for expected,name in rows:
        p=source/name
        if not p.is_file():
            raise RuntimeError(f"manifest file missing: {name}")
        got=sha256(p)
        if got!=expected:
            raise RuntimeError(f"manifest mismatch {name}: expected={expected} actual={got}")
    return rows

def discover(repo: Path) -> Path:
    manifests=[
        p for p in (repo/"runtime").rglob("bundle_manifest_sha256.txt")
        if ".venv" not in p.parts and "__pycache__" not in p.parts
    ]
    if not manifests:
        raise RuntimeError(
            "No standardized research bundle manifest found under runtime/. "
            "Run the current research runner first or pass --source."
        )
    manifests.sort(key=lambda p:p.stat().st_mtime_ns, reverse=True)
    return manifests[0].parent

def verify_zip(zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path) as z:
        bad=z.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC failure: {bad}")
        names=set(z.namelist())
        if "bundle_manifest_sha256.txt" not in names:
            raise RuntimeError("ZIP missing bundle_manifest_sha256.txt")
        manifest=z.read("bundle_manifest_sha256.txt").decode("utf-8-sig")
        for raw in manifest.splitlines():
            if not raw.strip():
                continue
            expected,name=raw.split("  ",1)
            if name not in names:
                raise RuntimeError(f"ZIP manifest member missing: {name}")
            got=hashlib.sha256(z.read(name)).hexdigest()
            if got!=expected.lower():
                raise RuntimeError(f"ZIP manifest mismatch: {name}")

def build_zip(source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(source.iterdir(),key=lambda x:x.name):
            if p.is_file():
                z.write(p,p.name)

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--source")
    ap.add_argument("--output")
    args=ap.parse_args()

    repo=Path(args.repo_root).resolve()
    source=Path(args.source).resolve() if args.source else discover(repo)
    if not source.is_dir():
        raise RuntimeError(f"source folder missing: {source}")

    rows=verify_source(source)
    parent=source.parent
    candidates=[
        p for p in parent.glob("*.zip")
        if p.is_file() and p.name.lower() not in {"diagnostic.zip"}
    ]

    if args.output:
        output=Path(args.output).resolve()
        build_zip(source,output)
    elif len(candidates)==1:
        output=candidates[0]
    else:
        output=parent/"mt5_research_bundle.zip"
        build_zip(source,output)

    verify_zip(output)
    print("BUNDLE_MANIFEST_PASS",len(rows))
    print("ZIP_INTEGRITY_PASS")
    print("UPLOAD_THIS_ONE_ZIP="+str(output))
    print("SHA256="+sha256(output))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
