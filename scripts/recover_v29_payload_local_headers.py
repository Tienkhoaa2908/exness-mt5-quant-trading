#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, binascii, re, shutil, struct, zlib
from pathlib import Path, PurePosixPath

LOCAL = 0x04034B50
LOCAL_BYTES = b"PK\x03\x04"
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

def next_local(raw: bytes, start: int) -> int:
    return raw.find(LOCAL_BYTES, start)

def recover(raw: bytes, output: Path, diagnostic: bool = False) -> tuple[list[str], list[str]]:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    off = 0
    names: list[str] = []
    errors: list[str] = []
    report: list[str] = []
    root_name: str | None = None
    while off + HEADER.size <= len(raw):
        sig = struct.unpack_from("<I", raw, off)[0]
        if sig != LOCAL:
            nxt = next_local(raw, off + 1)
            if nxt < 0:
                report.append(f"STOP offset={off} signature=0x{sig:08x} raw_bytes={len(raw)} no_later_local_header=1")
                break
            report.append(f"RESYNC from={off} to={nxt} skipped={nxt-off}")
            errors.append(f"transport_gap from={off} to={nxt} skipped={nxt-off}")
            off = nxt
            continue
        (sig, version, flags, method, mtime, mdate, crc, csize, usize, nlen, xlen) = HEADER.unpack_from(raw, off)
        if flags & 0x08:
            errors.append(f"data_descriptor offset={off}")
            nxt = next_local(raw, off + 4)
            if nxt < 0:
                break
            off = nxt
            continue
        start = off + HEADER.size
        end_name = start + nlen
        end_extra = end_name + xlen
        end_data = end_extra + csize
        if end_data > len(raw):
            errors.append(f"truncated offset={off} end_data={end_data} raw_bytes={len(raw)}")
            nxt = next_local(raw, off + 4)
            if nxt < 0:
                break
            off = nxt
            continue
        name_bytes = raw[start:end_name]
        encoding = "utf-8" if flags & 0x800 else "cp437"
        try:
            name = name_bytes.decode(encoding)
        except UnicodeDecodeError as exc:
            errors.append(f"name_decode_failed offset={off}: {exc}")
            nxt = next_local(raw, off + 4)
            if nxt < 0:
                break
            off = nxt
            continue
        if root_name is None and "/" in name:
            root_name = name.split("/", 1)[0]
        compressed = raw[end_extra:end_data]
        try:
            data = inflate(method, compressed)
            size_ok = len(data) == usize
            actual_crc = binascii.crc32(data) & 0xFFFFFFFF
            crc_ok = actual_crc == crc
        except Exception as exc:
            data = b""
            size_ok = False
            actual_crc = -1
            crc_ok = False
            errors.append(f"inflate_failed {name}: {type(exc).__name__}: {exc}")
        rel = safe_rel(name, root_name or "")
        target = output / rel
        if name.endswith("/"):
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            if data:
                target.write_bytes(data)
            names.append(name)
        status = "PASS" if size_ok and crc_ok else "FAIL"
        report.append(
            f"{status} offset={off} name={name} method={method} csize={csize} usize={usize} "
            f"actual_size={len(data)} expected_crc={crc:08x} actual_crc={actual_crc & 0xffffffff:08x}"
        )
        if not size_ok:
            errors.append(f"size_mismatch {name}: expected={usize} actual={len(data)}")
        if not crc_ok:
            errors.append(f"crc_mismatch {name}: expected={crc:08x} actual={actual_crc & 0xffffffff:08x}")
        off = end_data
    if not names:
        errors.append("no recoverable ZIP local-file entries")
    missing = [suffix for suffix in REQUIRED_SUFFIXES if not any(n.replace("\\", "/").endswith(suffix) for n in names)]
    if missing:
        errors.append(f"required recovered members missing: {missing}")
    (output / "RECOVERY_INTEGRITY_REPORT.txt").write_text("\n".join(report + ["", "ERRORS:"] + errors) + "\n", encoding="utf-8")
    print(f"LOCAL_HEADER_RECOVERY files={len(names)} errors={len(errors)} stop_offset={off} raw_bytes={len(raw)}")
    for line in report:
        print(line)
    for err in errors:
        print(f"RECOVERY_ERROR {err}")
    if errors and not diagnostic:
        raise RuntimeError(f"recovery integrity failed with {len(errors)} issue(s)")
    return names, errors

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--diagnostic", action="store_true", help="write all recoverable members/report and return success despite integrity failures")
    ns = ap.parse_args()
    raw = decode_transport(ns.input)
    _, errors = recover(raw, ns.output, diagnostic=ns.diagnostic)
    if ns.diagnostic:
        print(f"LOCAL_HEADER_DIAGNOSTIC_COMPLETE integrity_issues={len(errors)}")
    else:
        print("LOCAL_HEADER_RECOVERY_PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
