#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, binascii, re, shutil, struct, zlib
from pathlib import Path, PurePosixPath

LOCAL = 0x04034B50
HEADER = struct.Struct("<IHHHHHIIIHH")
REQUIRED_SUFFIXES = (
    "/mql5/Experts/AdaptiveExpertLabV1.mq5",
    "/scripts/run_adaptive_expert_lab_v1.ps1",
    "/scripts/analyze_adaptive_expert_bundle.py",
    "/experiments/adaptive_expert_lab_v1/template.ini",
    "/experiments/adaptive_expert_lab_v1/chunks.csv",
    "/tests/test_adaptive_expert_lab_static.py",
    "/RUN_ADAPTIVE_EXPERT_LAB_V1.cmd",
)

def decode_transport(path: Path) -> bytes:
    compact = re.sub(rb"\s+", b"", path.read_bytes()).rstrip(b"=")
    compact += b"=" * ((-len(compact)) % 4)
    return base64.b64decode(compact, validate=False)

def safe_rel(name: str, root_name: str) -> Path:
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts:
        raise RuntimeError(f"unsafe archive path: {name}")
    parts = p.parts
    if parts and parts[0] == root_name:
        parts = parts[1:]
    if not parts:
        return Path(".")
    return Path(*parts)

def inflate(method: int, payload: bytes) -> bytes:
    if method == 0:
        return payload
    if method == 8:
        return zlib.decompress(payload, -15)
    raise RuntimeError(f"unsupported compression method {method}")

def recover(raw: bytes, output: Path) -> list[str]:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    off = 0
    names: list[str] = []
    root_name: str | None = None
    while off + HEADER.size <= len(raw):
        sig = struct.unpack_from("<I", raw, off)[0]
        if sig != LOCAL:
            break
        (sig, version, flags, method, mtime, mdate, crc, csize, usize, nlen, xlen) = HEADER.unpack_from(raw, off)
        if flags & 0x08:
            raise RuntimeError(f"data-descriptor ZIP entry unsupported at offset {off}")
        start = off + HEADER.size
        end_name = start + nlen
        end_extra = end_name + xlen
        end_data = end_extra + csize
        if end_data > len(raw):
            raise RuntimeError(f"truncated local entry at offset {off}")
        name_bytes = raw[start:end_name]
        encoding = "utf-8" if flags & 0x800 else "cp437"
        name = name_bytes.decode(encoding)
        if root_name is None and "/" in name:
            root_name = name.split("/", 1)[0]
        compressed = raw[end_extra:end_data]
        data = inflate(method, compressed)
        if len(data) != usize:
            raise RuntimeError(f"size mismatch {name}: expected={usize} actual={len(data)}")
        actual_crc = binascii.crc32(data) & 0xFFFFFFFF
        if actual_crc != crc:
            raise RuntimeError(f"CRC mismatch {name}: expected={crc:08x} actual={actual_crc:08x}")
        rel = safe_rel(name, root_name or "")
        target = output / rel
        if name.endswith("/"):
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            names.append(name)
        off = end_data
    if not names:
        raise RuntimeError("no recoverable ZIP local-file entries")
    missing = [suffix for suffix in REQUIRED_SUFFIXES if not any(n.replace("\\", "/").endswith(suffix) for n in names)]
    if missing:
        raise RuntimeError(f"required recovered members missing: {missing}")
    print(f"LOCAL_HEADER_RECOVERY_PASS files={len(names)} stop_offset={off} raw_bytes={len(raw)}")
    for n in names:
        print(f"RECOVERED {n}")
    return names

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ns = ap.parse_args()
    raw = decode_transport(ns.input)
    recover(raw, ns.output)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
