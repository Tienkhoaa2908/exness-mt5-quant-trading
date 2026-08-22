#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import os
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V49"
V45_BASE = REPO / "runtime" / "v45_multiyear_validation" / "RUN_V45_MULTIYEAR_ONE_SHOT.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


base = load_module(V45_BASE, "v45_base_v49_supervisor")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def add_tree(files: list[tuple[Path, str]], root: Path, arc_prefix: str) -> None:
    if not root.exists():
        return
    for p in root.rglob("*"):
        if p.is_file():
            files.append((p, f"{arc_prefix}/{p.relative_to(root).as_posix()}"))


def package(common: Path, final_reason: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    paper = common / "mt5_quant" / "paper"
    v49 = common / "mt5_quant" / "v49"
    status = v49 / "V49_DEMO_REHEARSAL_STATUS.txt"
    s = kv(status)
    run_folder = s.get("run_folder", "").replace("\\", "/")
    run_dir = common / Path(run_folder) if run_folder else None

    files: list[tuple[Path, str]] = []
    for p in (
        v49 / "V49_DEMO_REHEARSAL_STATUS.txt",
        v49 / "V49_DEMO_REHEARSAL_FINAL.txt",
        v49 / "V49_DEMO_REHEARSAL_EVENTS.csv",
        v49 / "V49_DEMO_REHEARSAL_TRANSACTIONS.csv",
        paper / "v49_demo_rehearsal_state.csv",
        paper / "V49_DEMO_REHEARSAL_LATEST.txt",
        paper / "V49_DEMO_REHEARSAL_INIT.txt",
    ):
        if p.is_file():
            files.append((p, f"common/{p.relative_to(common).as_posix()}"))
    if run_dir is not None:
        add_tree(files, run_dir, "run")

    meta = OUT / "v49_supervisor_final.txt"
    meta.write_text(
        f"packaged_at={datetime.now().isoformat(timespec='seconds')}\n"
        f"reason={final_reason}\n"
        f"run_id={s.get('run_id','')}\n",
        encoding="utf-8",
    )
    files.append((meta, "v49_supervisor_final.txt"))

    manifest_lines = []
    for src, arc in sorted(files, key=lambda x: x[1]):
        manifest_lines.append(f"{sha256(src)}  {arc}")
    manifest = OUT / "bundle_manifest_sha256.txt"
    manifest.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    files.append((manifest, "bundle_manifest_sha256.txt"))

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zpath = OUT / f"V49_ONE_SHOT_DEMO_REHEARSAL_{stamp}.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for src, arc in files:
            zf.write(src, arc)
    with zipfile.ZipFile(zpath, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP CRC failure: {bad}")
    (OUT / "LATEST_V49_ZIP.txt").write_text(
        f"path={zpath}\nsha256={sha256(zpath)}\nreason={final_reason}\n",
        encoding="utf-8",
    )
    return zpath


def main() -> int:
    _, common, _, _ = base.locate_mt5()
    v49 = common / "mt5_quant" / "v49"
    final = v49 / "V49_DEMO_REHEARSAL_FINAL.txt"
    status = v49 / "V49_DEMO_REHEARSAL_STATUS.txt"
    OUT.mkdir(parents=True, exist_ok=True)
    log = OUT / "v49_supervisor.log"

    deadline = time.time() + 15 * 86400
    last_status_mtime = 0.0
    stale_since: float | None = None
    while time.time() < deadline:
        if final.is_file() and final.stat().st_size > 0:
            verdict = kv(final).get("verdict", "FINAL")
            z = package(common, f"EA_FINAL_{verdict}")
            with log.open("a", encoding="utf-8") as fh:
                fh.write(f"{datetime.now().isoformat()} FINAL={verdict} ZIP={z} SHA={sha256(z)}\n")
            return 0

        if status.is_file():
            mt = status.stat().st_mtime
            if mt > last_status_mtime:
                last_status_mtime = mt
                stale_since = None
            elif stale_since is None:
                stale_since = time.time()
            elif time.time() - stale_since > 300:
                with log.open("a", encoding="utf-8") as fh:
                    fh.write(f"{datetime.now().isoformat()} WARNING=status_stale_gt_300s\n")
                stale_since = time.time()

        time.sleep(30)

    z = package(common, "SUPERVISOR_15D_TIMEOUT_NO_EA_FINAL")
    with log.open("a", encoding="utf-8") as fh:
        fh.write(f"{datetime.now().isoformat()} TIMEOUT ZIP={z} SHA={sha256(z)}\n")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "v49_supervisor_fatal.txt").write_text(
            f"{type(exc).__name__}: {exc}\n", encoding="utf-8"
        )
        raise
