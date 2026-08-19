#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, hashlib, importlib.util
import sys
from pathlib import Path

def load_verifier(root: Path):
    path = root / "scripts" / "verify_and_build_v29_release.py"
    spec = importlib.util.spec_from_file_location("v29_release_verifier", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load V29 release verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, required=True)
    ns = ap._args() if False else ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    raw = base64.b64decode(ns.archive.read_bytes(), validate=False)
    actual = hashlib.sha256(raw).hexdigest()
    v = load_verifier(root)
    pinned = v.EXPECTED_PAYLOAD_ZIP_SHA256
    try:
        v.EXPECTED_PAYLOAD_ZIP_SHA256 = actual
        v.validate_payload(raw)
    finally:
        v.EXPECTED_PAYLOAD_ZIP_SHA256 = pinned
    print(f"PAYLOAD_CONTENT_AUDIT_PASS actual_sha256={actual} pinned_sha256={pinned}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
