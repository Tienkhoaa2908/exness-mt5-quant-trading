#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, hashlib, re
from pathlib import Path

ZIP_MAGIC = b"PK\x03\x04"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def decode_to_zip(data: bytes, max_layers: int = 3) -> tuple[bytes, int]:
    data = data.strip()
    for depth in range(max_layers + 1):
        if data.startswith(ZIP_MAGIC):
            return data, depth
        compact = re.sub(rb"\s+", b"", data)
        # Historical recovery payloads were written with non-canonical padding.
        # Transport decoding is deliberately permissive; final ZIP magic, pinned
        # SHA-256 and full content contracts remain mandatory downstream.
        try:
            decoded = base64.b64decode(compact, validate=False)
        except Exception as exc:
            raise RuntimeError(f"archive encoding invalid at base64 layer {depth}: {exc}") from exc
        if decoded == data or not decoded:
            raise RuntimeError("archive decoding made no progress")
        data = decoded
    raise RuntimeError(f"ZIP magic not reached within {max_layers} base64 layers")

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
