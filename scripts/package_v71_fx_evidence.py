#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import zipfile
from pathlib import Path

PROTOCOL = "v71_fx_evidence_package_v1"
ANALYSIS_PROTOCOL = "v71_fx_portability_v1"
CONTROL_SYMBOL = "XAUUSDm"
SOURCE_NAME = "V71FxPortabilityLong.mq5"
ANALYSIS_NAME = "v71_fx_portability_analysis.json"
SUMMARY_NAME = "V71_FX_PORTABILITY_SUMMARY.txt"
MANIFEST_NAME = "V71_FX_EVIDENCE_MANIFEST.json"
FULL_ZIP_NAME = "V71_FX_EVIDENCE_FULL.zip"
CORE_ZIP_NAME = "V71_FX_EVIDENCE_CORE.zip"

REQUIRED_RUN_FILES = (
    "V64_DEALS.csv",
    "V64_EVENTS.csv",
    "V64_ENTRY_EVAL.csv",
)
CORE_RUN_FILES = (
    "V64_DEALS.csv",
    "V64_EVENTS.csv",
    "V64_STATUS.txt",
)
ALLOWED_SUFFIXES = {".csv", ".txt", ".json", ".ini", ".mq5", ".log"}


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def label_for(symbol: str) -> str:
    return "fx_" + re.sub(r"[^a-z0-9]+", "_", symbol.lower()).strip("_") + "_long"


def validate_head(value: str, label: str) -> str:
    value = (value or "").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise RuntimeError(f"invalid {label} sha={value!r}")
    return value


def read_analysis(output_root: Path) -> dict:
    path = output_root / ANALYSIS_NAME
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"missing V71 analysis JSON: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("protocol") != ANALYSIS_PROTOCOL:
        raise RuntimeError(f"unexpected analysis protocol={payload.get('protocol')!r}")
    if payload.get("control_symbol") != CONTROL_SYMBOL:
        raise RuntimeError(f"unexpected control symbol={payload.get('control_symbol')!r}")
    if payload.get("short_enabled") is not False:
        raise RuntimeError("V71 evidence claims SHORT enabled")
    if payload.get("real_money_authorized") is not False:
        raise RuntimeError("V71 evidence claims REAL authorized")
    if payload.get("development_only_not_independent") is not True:
        raise RuntimeError("V71 evidence lost development-only classification")
    results = payload.get("results")
    if not isinstance(results, dict) or CONTROL_SYMBOL not in results or len(results) < 3:
        raise RuntimeError("V71 analysis results missing control/FX coverage")
    return payload


def validate_source(repo: Path, output_root: Path) -> str:
    source = output_root / SOURCE_NAME
    if not source.is_file() or source.stat().st_size <= 0:
        raise RuntimeError(f"missing generated V71 source: {source}")
    builder_path = repo / "scripts" / "build_v71_fx_portability_source.py"
    builder = load(builder_path, "v71_builder_for_evidence_package")
    actual = source.read_text(encoding="utf-8").replace("\r\n", "\n")
    expected = builder.transform().replace("\r\n", "\n")
    if actual != expected:
        raise RuntimeError("existing V71 evidence source does not match current V71 builder")
    builder.assert_v69_strategy_equivalence(actual)
    return sha256_file(source)


def count_trade_pairs(deals_path: Path) -> int:
    with deals_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        rows = list(csv.DictReader(fh))
    entries = 0
    exits = 0
    for row in rows:
        try:
            entry = int(float(row.get("entry", "") or 0))
        except (TypeError, ValueError):
            entry = 0
        if entry == 0:
            entries += 1
        else:
            exits += 1
    if entries != exits:
        raise RuntimeError(
            f"V71 evidence deal pairing mismatch path={deals_path} entries={entries} exits={exits}"
        )
    return exits


def validate_runs(output_root: Path, payload: dict) -> dict[str, Path]:
    run_dirs: dict[str, Path] = {}
    for symbol, result in payload["results"].items():
        run_dir = output_root / label_for(symbol)
        if not run_dir.is_dir():
            raise RuntimeError(f"missing V71 symbol evidence directory symbol={symbol} path={run_dir}")
        for name in REQUIRED_RUN_FILES:
            path = run_dir / name
            if not path.is_file() or path.stat().st_size <= 0:
                raise RuntimeError(f"missing V71 raw evidence symbol={symbol} file={path}")
        raw_trades = count_trade_pairs(run_dir / "V64_DEALS.csv")
        analyzed_trades = int((result or {}).get("trades") or 0)
        if raw_trades != analyzed_trades:
            raise RuntimeError(
                f"V71 raw/analyzed trade mismatch symbol={symbol} raw={raw_trades} analyzed={analyzed_trades}"
            )
        run_dirs[symbol] = run_dir
    return run_dirs


def root_payload_files(output_root: Path) -> list[Path]:
    names = [SOURCE_NAME, ANALYSIS_NAME, SUMMARY_NAME]
    compile_name = "V71FxPortabilityLong.compile.txt"
    if (output_root / compile_name).is_file():
        names.append(compile_name)
    files = [output_root / name for name in names if (output_root / name).is_file()]
    files.extend(sorted(output_root.glob("v64_fx_*.ini")))
    return files


def run_payload_files(run_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(run_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in ALLOWED_SUFFIXES:
            files.append(path)
    return files


def arcname(output_root: Path, path: Path) -> str:
    return path.relative_to(output_root).as_posix()


def file_entry(output_root: Path, path: Path) -> dict:
    return {
        "path": arcname(output_root, path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def make_manifest(
    *,
    output_root: Path,
    files: list[Path],
    packaging_head: str,
    evidence_head: str,
    source_sha256: str,
    payload: dict,
    package_kind: str,
    symbol: str | None = None,
) -> dict:
    return {
        "protocol": PROTOCOL,
        "package_kind": package_kind,
        "symbol": symbol,
        "packaging_head": packaging_head,
        "evidence_head": evidence_head,
        "strategy_source_sha256": source_sha256,
        "analysis_protocol": payload.get("protocol"),
        "development_only_not_independent": True,
        "strategy_semantics": payload.get("strategy_semantics"),
        "control_symbol": payload.get("control_symbol"),
        "symbols": list(payload["results"].keys()),
        "short_enabled": False,
        "real_money_authorized": False,
        "files": [file_entry(output_root, p) for p in sorted(files, key=lambda p: arcname(output_root, p))],
    }


def zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    return info


def write_zip(path: Path, output_root: Path, files: list[Path], manifest: dict) -> str:
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.unlink()
    except FileNotFoundError:
        pass
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr(zip_info(MANIFEST_NAME), manifest_bytes)
        for src in sorted(files, key=lambda p: arcname(output_root, p)):
            zf.writestr(zip_info(arcname(output_root, src)), src.read_bytes())
    tmp.replace(path)
    return sha256_file(path)


def package_evidence(
    *,
    repo: Path,
    output_root: Path,
    packaging_head: str,
    evidence_head: str,
) -> dict:
    repo = repo.resolve()
    output_root = output_root.resolve()
    packaging_head = validate_head(packaging_head, "packaging_head")
    evidence_head = validate_head(evidence_head, "evidence_head")

    payload = read_analysis(output_root)
    source_sha = validate_source(repo, output_root)
    run_dirs = validate_runs(output_root, payload)
    root_files = root_payload_files(output_root)

    full_files = list(root_files)
    for run_dir in run_dirs.values():
        full_files.extend(run_payload_files(run_dir))
    full_files = sorted(set(full_files))

    core_files = list(root_files)
    for run_dir in run_dirs.values():
        for name in CORE_RUN_FILES:
            path = run_dir / name
            if path.is_file() and path.stat().st_size > 0:
                core_files.append(path)
    core_files = sorted(set(core_files))

    external_manifest = make_manifest(
        output_root=output_root,
        files=full_files,
        packaging_head=packaging_head,
        evidence_head=evidence_head,
        source_sha256=source_sha,
        payload=payload,
        package_kind="full",
    )
    (output_root / MANIFEST_NAME).write_text(
        json.dumps(external_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    full_path = output_root / FULL_ZIP_NAME
    full_sha = write_zip(full_path, output_root, full_files, external_manifest)

    core_manifest = make_manifest(
        output_root=output_root,
        files=core_files,
        packaging_head=packaging_head,
        evidence_head=evidence_head,
        source_sha256=source_sha,
        payload=payload,
        package_kind="core",
    )
    core_path = output_root / CORE_ZIP_NAME
    core_sha = write_zip(core_path, output_root, core_files, core_manifest)

    symbol_packages = {}
    for symbol, run_dir in run_dirs.items():
        files = list(root_files) + run_payload_files(run_dir)
        files = sorted(set(files))
        manifest = make_manifest(
            output_root=output_root,
            files=files,
            packaging_head=packaging_head,
            evidence_head=evidence_head,
            source_sha256=source_sha,
            payload=payload,
            package_kind="symbol_full",
            symbol=symbol,
        )
        path = output_root / f"V71_FX_EVIDENCE_{symbol}.zip"
        digest = write_zip(path, output_root, files, manifest)
        symbol_packages[symbol] = {"path": str(path), "sha256": digest, "files": len(files)}

    result = {
        "source_sha256": source_sha,
        "symbols": list(run_dirs.keys()),
        "full": {"path": str(full_path), "sha256": full_sha, "files": len(full_files)},
        "core": {"path": str(core_path), "sha256": core_sha, "files": len(core_files)},
        "symbol_packages": symbol_packages,
    }
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--packaging-head", required=True)
    ap.add_argument("--evidence-head", required=True)
    args = ap.parse_args()

    result = package_evidence(
        repo=args.repo,
        output_root=args.output_root,
        packaging_head=args.packaging_head,
        evidence_head=args.evidence_head,
    )
    print(f"V71_FX_EVIDENCE_SOURCE=PASS sha256={result['source_sha256']}")
    print("V71_FX_EVIDENCE_SYMBOLS=" + ",".join(result["symbols"]))
    print(
        "V71_FX_EVIDENCE_FULL_ZIP="
        f"{result['full']['path']} sha256={result['full']['sha256']} files={result['full']['files']}"
    )
    print(
        "V71_FX_EVIDENCE_CORE_ZIP="
        f"{result['core']['path']} sha256={result['core']['sha256']} files={result['core']['files']}"
    )
    for symbol, item in result["symbol_packages"].items():
        print(
            f"V71_FX_EVIDENCE_SYMBOL_ZIP symbol={symbol} path={item['path']} "
            f"sha256={item['sha256']} files={item['files']}"
        )
    print("V71_FX_EVIDENCE_PACKAGE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
