#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, hashlib, io, re, zipfile
from pathlib import Path

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def is_valid_zip(data: bytes) -> bool:
    try:
        if not zipfile.is_zipfile(io.BytesIO(data)):
            return False
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            return z.testzip() is None
    except (OSError, zipfile.BadZipFile, RuntimeError):
        return False

def decode_to_zip(data: bytes, max_layers: int = 3) -> tuple[bytes, int]:
    data = data.strip()
    for depth in range(max_layers + 1):
        if is_valid_zip(data):
            return data, depth
        compact = re.sub(rb"\s+", b"", data)
        try:
            decoded = base64.b64decode(compact, validate=False)
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
