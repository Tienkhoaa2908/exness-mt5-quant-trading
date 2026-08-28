#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

CANDIDATE = "v52_b4_or_b3_trend_bos"
V52R_ACCEPTED_ZIP_SHA256 = "4eddfce34c25b915e921a35e993f68f0a78644f3d6055bfa26180ba60ec9762c"
V53_ACCEPTED_ZIP_SHA256 = "602115bc6161e8947835c43033a1899637cc8a288f5192b2631acd6a6dd629db"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(repo: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=repo, text=True, encoding="utf-8", errors="replace"
        ).strip()
    except Exception:
        return "UNAVAILABLE"


def safe_copy(src: Path, dst: Path) -> bool:
    if not src.is_file():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def package(repo: Path, common: Path, output_dir: Path, label: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    zip_path = output_dir / f"V54_PRODUCTION_READINESS_EVIDENCE_{label}_{stamp}.zip"

    v54_common = common / "mt5_quant" / "v54"
    paper = common / "mt5_quant" / "paper"
    output_v54 = repo / "runtime" / "v54_production_readiness" / "OUTPUT_V54"
    candidates = [
        (v54_common / "V54_PRODUCTION_READINESS_STATUS.txt", "runtime/V54_PRODUCTION_READINESS_STATUS.txt", True),
        (v54_common / "V54_PRODUCTION_READINESS_EVENTS.csv", "runtime/V54_PRODUCTION_READINESS_EVENTS.csv", False),
        (v54_common / "V54_PRODUCTION_READINESS_TRANSACTIONS.csv", "runtime/V54_PRODUCTION_READINESS_TRANSACTIONS.csv", False),
        (paper / "v54_demo_rehearsal_state.csv", "runtime/v54_demo_rehearsal_state.csv", False),
        (output_v54 / "V54ProductionReadiness.mq5", "build/V54ProductionReadiness.mq5", True),
        (output_v54 / "V54ProductionReadiness.compile.txt", "build/V54ProductionReadiness.compile.txt", True),
        (repo / "scripts" / "build_v54_production_readiness_source.py", "source/build_v54_production_readiness_source.py", True),
        (repo / "runtime" / "v54_production_readiness" / "RUN_V54_PRODUCTION_READINESS.py", "source/RUN_V54_PRODUCTION_READINESS.py", True),
        (repo / "runtime" / "v54_production_readiness" / "PACKAGE_V54_EVIDENCE.py", "source/PACKAGE_V54_EVIDENCE.py", True),
        (repo / "docs" / "adr" / "ADR-056-v54-production-readiness-safety-envelope.md", "docs/ADR-056-v54-production-readiness-safety-envelope.md", True),
        (repo / "docs" / "runbooks" / "V54_PRODUCTION_READINESS_RUNBOOK.md", "docs/V54_PRODUCTION_READINESS_RUNBOOK.md", True),
    ]

    with tempfile.TemporaryDirectory(prefix="v54_evidence_snapshot_") as td:
        stage = Path(td) / "snapshot"
        stage.mkdir()
        missing_required: list[str] = []
        copied: list[str] = []
        for src, rel, required in candidates:
            ok = safe_copy(src, stage / rel)
            if ok:
                copied.append(rel)
            elif required:
                missing_required.append(str(src))
        if missing_required:
            raise RuntimeError("required evidence missing: " + "; ".join(missing_required))

        provenance = {
            "schema": "v54_immutable_evidence_v1",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "candidate": CANDIDATE,
            "production_activation": "DISABLED_DEMO_SAFE",
            "v52r_accepted_zip_sha256": V52R_ACCEPTED_ZIP_SHA256,
            "v53_accepted_zip_sha256": V53_ACCEPTED_ZIP_SHA256,
            "branch": git(repo, "branch", "--show-current"),
            "head": git(repo, "rev-parse", "HEAD"),
            "working_tree_porcelain": git(repo, "status", "--porcelain"),
            "files_copied": copied,
        }
        (stage / "PROVENANCE.json").write_text(
            json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        manifest_lines: list[str] = []
        for path in sorted(p for p in stage.rglob("*") if p.is_file()):
            rel = path.relative_to(stage).as_posix()
            manifest_lines.append(f"{sha256(path)}  {rel}")
        (stage / "SHA256SUMS.txt").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

        # Snapshot is now immutable input. ZIP reads only staged files.
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(p for p in stage.rglob("*") if p.is_file()):
                zf.write(path, path.relative_to(stage).as_posix())

    with zipfile.ZipFile(zip_path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP CRC failure at {bad}")
        names = set(zf.namelist())
        if "SHA256SUMS.txt" not in names or "PROVENANCE.json" not in names:
            raise RuntimeError("evidence ZIP missing manifest/provenance")
        manifest = zf.read("SHA256SUMS.txt").decode("utf-8")
        for line in manifest.splitlines():
            if not line.strip():
                continue
            expected, rel = line.split("  ", 1)
            actual = hashlib.sha256(zf.read(rel)).hexdigest()
            if actual != expected:
                raise RuntimeError(f"manifest mismatch {rel}")

    sidecar = zip_path.with_suffix(zip_path.suffix + ".sha256")
    sidecar.write_text(f"{sha256(zip_path)}  {zip_path.name}\n", encoding="utf-8")
    print(f"V54_EVIDENCE_ZIP={zip_path}")
    print(f"V54_EVIDENCE_ZIP_SHA256={sha256(zip_path)}")
    print("V54_EVIDENCE_CRC=PASS")
    print("V54_EVIDENCE_MANIFEST=PASS")
    return zip_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--common", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--label", default="snapshot")
    ns = ap.parse_args()
    package(Path(ns.repo).resolve(), Path(ns.common).resolve(), Path(ns.output_dir).resolve(), ns.label)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
