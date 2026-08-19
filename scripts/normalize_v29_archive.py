#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, hashlib, io, re, zipfile
from pathlib import Path

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def zip_integrity(data: bytes) -> tuple[bool, str]:
    bio = io.BytesIO(data)
    if not zipfile.is_zipfile(bio):
        return False, "not_zip"
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            bad = z.testzip()
            if bad is not None:
                return False, f"crc_failed:{bad}"
            return True, f"ok:{len(z.infolist())}_members"
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        return False, f"zip_error:{type(exc).__name__}:{exc}"

def layer_summary(depth: int, data: bytes) -> str:
    compact = re.sub(rb"\s+", b"", data)
    ok, status = zip_integrity(data)
    return (
        f"ARCHIVE_LAYER depth={depth} bytes={len(data)} compact={len(compact)} "
        f"mod4={len(compact)%4} sha256={sha(data)} prefix_hex={data[:16].hex()} "
        f"suffix_hex={data[-24:].hex()} zip_status={status}"
    )

def decode_to_zip(data: bytes, max_layers: int = 3) -> tuple[bytes, int]:
    data = data.strip()
    for depth in range(max_layers + 1):
        print(layer_summary(depth, data))
        ok, status = zip_integrity(data)
        if ok:
            return data, depth
        if status != "not_zip":
            raise RuntimeError(f"ZIP structure found but integrity failed at layer {depth}: {status}")
        compact = re.sub(rb"\s+", b"", data)
        core = compact.rstrip(b"=")
        normalized = core + b"=" * ((-len(core)) % 4)
        try:
            decoded = base64.b64decode(normalized, validate=False)
        except Exception as exc:
            raise RuntimeError(f"archive encoding invalid at base64 layer {depth}: {exc}") from exc
        if decoded == data or not decoded:
            raise RuntimeError("archive decoding made no progress")
        data = decoded
    raise RuntimeError(f"valid ZIP not reached within {max_layers} base64 layers")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True,
                    help="canonical single-base64 .b64 output")
    ns = ap.parse_args()
    final_zip, depth = decode_to_zip(ns.input.read_bytes())
    ns.output.parent.mkdir(parents=True, exist_ok=True)
    ns.output.write_bytes(base64.b64encode(final_zip) + b"\n")
    print(f"ARCHIVE_NORMALIZE_PASS input_layers={depth} final_zip_sha256={sha(final_zip)} output={ns.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
