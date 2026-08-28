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


def kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if "=" not in raw:
            continue
        k, v = raw.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def safe_copy(src: Path, dst: Path) -> bool:
    if not src.is_file():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def package(repo: Path, common: Path, output_dir: Path, label: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    zip_path = output_dir / f"V55_ACCOUNT_AGNOSTIC_EVIDENCE_{label}_{stamp}.zip"

    v55_common = common / "mt5_quant" / "v55"
    paper = common / "mt5_quant" / "paper"
    output_v55 = repo / "runtime" / "v55_account_agnostic" / "OUTPUT_V55"
    status_path = v55_common / "V55_PRODUCTION_READINESS_STATUS.txt"
    status = kv(status_path)

    candidates = [
        (status_path, "runtime/V55_PRODUCTION_READINESS_STATUS.txt", True),
        (v55_common / "V55_PRODUCTION_READINESS_EVENTS.csv", "runtime/V55_PRODUCTION_READINESS_EVENTS.csv", False),
        (v55_common / "V55_PRODUCTION_READINESS_TRANSACTIONS.csv", "runtime/V55_PRODUCTION_READINESS_TRANSACTIONS.csv", False),
        (v55_common / "V55_PRODUCTION_READINESS_FINAL.txt", "runtime/V55_PRODUCTION_READINESS_FINAL.txt", False),
        (paper / "v55_demo_rehearsal_state.csv", "runtime/v55_demo_rehearsal_state.csv", False),
        (output_v55 / "V55AccountAgnosticProduction.mq5", "build/V55AccountAgnosticProduction.mq5", True),
        (output_v55 / "V55AccountAgnosticProduction.compile.txt", "build/V55AccountAgnosticProduction.compile.txt", True),
        (repo / "scripts" / "build_v55_account_agnostic_source.py", "source/build_v55_account_agnostic_source.py", True),
        (repo / "runtime" / "v55_account_agnostic" / "RUN_V55_ACCOUNT_AGNOSTIC.py", "source/RUN_V55_ACCOUNT_AGNOSTIC.py", True),
        (repo / "runtime" / "v55_account_agnostic" / "PACKAGE_V55_EVIDENCE.py", "source/PACKAGE_V55_EVIDENCE.py", True),
    ]

    with tempfile.TemporaryDirectory(prefix="v55_evidence_snapshot_") as td:
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
            "schema": "v55_immutable_evidence_v1",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "candidate": CANDIDATE,
            "account_model": "DEMO_AND_REAL_SAME_BINARY",
            "account_mode": status.get("account_mode", "UNKNOWN"),
            "production_activation": status.get("production_activation", "UNKNOWN"),
            "real_money_authorized": status.get("real_money_authorized", "UNKNOWN"),
            "owned_magic": status.get("magic", "550055"),
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

        # Immutable snapshot rule: ZIP reads staged files only, never mutable runtime files.
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
    print(f"V55_EVIDENCE_ZIP={zip_path}")
    print(f"V55_EVIDENCE_ZIP_SHA256={sha256(zip_path)}")
    print("V55_EVIDENCE_CRC=PASS")
    print("V55_EVIDENCE_MANIFEST=PASS")
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
