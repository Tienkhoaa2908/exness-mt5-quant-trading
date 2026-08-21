#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_manifest(text: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        if "  " not in raw:
            raise RuntimeError(f"invalid manifest line: {raw!r}")
        expected, name = raw.split("  ", 1)
        if len(expected) != 64 or any(c not in "0123456789abcdefABCDEF" for c in expected):
            raise RuntimeError(f"invalid SHA256: {expected}")
        if Path(name).name != name or name in {".", ".."}:
            raise RuntimeError(f"unsafe manifest member: {name!r}")
        rows.append((expected.lower(), name))
    if not rows:
        raise RuntimeError("manifest is empty")
    return rows


def analyze(zip_path: Path) -> dict:
    result = {
        "zip": str(zip_path),
        "zip_sha256": hashlib.sha256(zip_path.read_bytes()).hexdigest(),
        "testzip": None,
        "manifest_pass": False,
        "manifest_files": 0,
        "evidence": {},
        "v39_summary": None,
    }
    with zipfile.ZipFile(zip_path) as z:
        bad = z.testzip()
        result["testzip"] = bad
        if bad:
            raise RuntimeError(f"ZIP CRC failure: {bad}")
        names = set(z.namelist())
        manifest_name = "bundle_manifest_sha256.txt"
        if manifest_name not in names:
            raise RuntimeError("bundle_manifest_sha256.txt missing")
        rows = parse_manifest(z.read(manifest_name).decode("utf-8-sig"))
        for expected, name in rows:
            if name not in names:
                raise RuntimeError(f"manifest member missing: {name}")
            got = sha256_bytes(z.read(name))
            if got != expected:
                raise RuntimeError(f"manifest mismatch {name}: expected={expected} actual={got}")
        result["manifest_pass"] = True
        result["manifest_files"] = len(rows)

        if "V39_EVIDENCE.txt" in names:
            evidence = {}
            for line in z.read("V39_EVIDENCE.txt").decode("utf-8-sig").splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    evidence[key.strip()] = value.strip()
            result["evidence"] = evidence

        if "v39_selective_harvest_summary.json" in names:
            result["v39_summary"] = json.loads(z.read("v39_selective_harvest_summary.json"))

    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify and summarize one MT5 research ZIP")
    ap.add_argument("zip")
    ap.add_argument("--json-output")
    args = ap.parse_args()
    path = Path(args.zip).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    result = analyze(path)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.json_output:
        Path(args.json_output).write_text(text + "\n", encoding="utf-8")
    print(text)
    print("BUNDLE_ANALYSIS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
