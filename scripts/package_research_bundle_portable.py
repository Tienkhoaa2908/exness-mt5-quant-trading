#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
import zipfile

MANIFEST = "bundle_manifest_sha256.txt"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bundle_files(bundle: Path) -> list[Path]:
    return sorted(
        (p for p in bundle.iterdir() if p.is_file() and p.name != MANIFEST),
        key=lambda p: p.name,
    )


def write_manifest(bundle: Path) -> list[tuple[str, str]]:
    files = bundle_files(bundle)
    if not files:
        raise RuntimeError(f"bundle has no files: {bundle}")
    rows = [(sha256_file(p), p.name) for p in files]
    text = "".join(f"{digest}  {name}\n" for digest, name in rows)
    (bundle / MANIFEST).write_text(text, encoding="utf-8", newline="\n")
    return rows


def verify_manifest(bundle: Path) -> list[tuple[str, str]]:
    manifest = bundle / MANIFEST
    if not manifest.is_file() or manifest.stat().st_size == 0:
        raise RuntimeError(f"manifest missing: {manifest}")
    rows: list[tuple[str, str]] = []
    for lineno, raw in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if len(raw) < 67 or raw[64:66] != "  ":
            raise RuntimeError(f"portable manifest format error line {lineno}: {raw!r}")
        digest, name = raw[:64].lower(), raw[66:]
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise RuntimeError(f"invalid SHA256 line {lineno}: {raw!r}")
        if not name or Path(name).name != name:
            raise RuntimeError(f"invalid bundle filename line {lineno}: {name!r}")
        path = bundle / name
        if not path.is_file():
            raise RuntimeError(f"manifest member missing: {name}")
        actual = sha256_file(path)
        if actual != digest:
            raise RuntimeError(f"manifest hash mismatch: {name} expected={digest} actual={actual}")
        rows.append((digest, name))
    if not rows:
        raise RuntimeError("manifest has no rows")
    return rows


def build_zip(bundle: Path, output: Path) -> str:
    write_manifest(bundle)
    rows = verify_manifest(bundle)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    members = [bundle / name for _, name in rows] + [bundle / MANIFEST]
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in sorted(members, key=lambda p: p.name):
            zf.write(path, path.name)
    with zipfile.ZipFile(output) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP CRC failure: {bad}")
        names = zf.namelist()
        if len(names) != len(set(names)):
            raise RuntimeError("ZIP contains duplicate members")
        if MANIFEST not in names:
            raise RuntimeError("ZIP missing internal manifest")
    return sha256_file(output)


def main() -> int:
    ap = argparse.ArgumentParser(description="Create a portable one-ZIP research bundle without relying on sha256sum text/binary marker formatting.")
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    bundle = Path(args.bundle).resolve()
    output = Path(args.output).resolve()
    if not bundle.is_dir():
        raise RuntimeError(f"bundle directory missing: {bundle}")
    digest = build_zip(bundle, output)
    print(f"PORTABLE_BUNDLE_PASS files={len(bundle_files(bundle)) + 1}")
    print(f"ZIP={output}")
    print(f"SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
