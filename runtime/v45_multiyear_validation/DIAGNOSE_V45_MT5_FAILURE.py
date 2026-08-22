#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V45"
DIAG = OUT / "diagnostics"
ZIP_OUT = OUT / "v45_mt5_failure_diagnostics.zip"
V30_SHA = "4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05"

KEYWORDS = (
    "v45", "xauusdm", "tester", "agent", "error", "failed", "failure", "cannot",
    "history", "synchron", "no data", "no prices", "no ticks", "market closed",
    "init", "stopped", "return code", "2022.01.01", "2026.08.01", "100018",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def decode_log(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-16", "utf-8-sig", "utf-8", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")


def sanitize(text: str) -> str:
    # Keep diagnostics useful while avoiding accidental credential/account leakage.
    text = re.sub(r"(?i)(password|pass|token|secret)\s*[=:]\s*\S+", r"\1=<redacted>", text)
    text = re.sub(r"(?i)(login|account)\s*[=:]\s*\d{5,}", r"\1=<redacted>", text)
    return text


def relevant_excerpt(path: Path) -> tuple[str, list[str]]:
    text = sanitize(decode_log(path)).replace("\r", "")
    lines = text.splitlines()
    selected: set[int] = set()
    for i, line in enumerate(lines):
        low = line.lower()
        if any(k in low for k in KEYWORDS):
            for j in range(max(0, i - 3), min(len(lines), i + 4)):
                selected.add(j)
    # Always retain the tail because MT5 often writes the real failure only at shutdown.
    for j in range(max(0, len(lines) - 120), len(lines)):
        selected.add(j)
    excerpt = "\n".join(lines[i] for i in sorted(selected)) + "\n"
    hits = sorted({k for k in KEYWORDS if k in text.lower()})
    return excerpt, hits


def find_data_folder() -> tuple[Path, Path]:
    appdata = Path(os.environ["APPDATA"])
    terminal_root = appdata / "MetaQuotes" / "Terminal"
    matches = []
    for src in terminal_root.glob("*/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5"):
        if src.is_file() and sha256(src) == V30_SHA:
            matches.append(src)
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one accepted V30 terminal data folder; matches={len(matches)}")
    src = matches[0]
    return src.parents[3], terminal_root


def recent_logs(data: Path, terminal_root: Path, horizon_hours: float = 12.0) -> list[Path]:
    cutoff = time.time() - horizon_hours * 3600
    roots = [
        data / "logs",
        data / "MQL5" / "Logs",
        data / "Tester",
        terminal_root.parent / "Tester",
    ]
    found: dict[str, Path] = {}
    for root in roots:
        if not root.exists():
            continue
        try:
            iterator = root.rglob("*.log")
            for p in iterator:
                try:
                    if p.is_file() and p.stat().st_mtime >= cutoff:
                        found[str(p.resolve()).lower()] = p
                except OSError:
                    continue
        except OSError:
            continue
    return sorted(found.values(), key=lambda p: p.stat().st_mtime, reverse=True)


def history_inventory(data: Path) -> list[dict]:
    rows = []
    bases = data / "bases"
    if not bases.exists():
        return rows
    for p in bases.rglob("*"):
        try:
            if not p.is_file():
                continue
        except OSError:
            continue
        low = str(p).lower()
        if "xauusdm" not in low:
            continue
        suffix = p.suffix.lower()
        if suffix not in {".hc", ".hcc", ".tkc", ".dat"}:
            continue
        st = p.stat()
        rows.append({
            "path": str(p.relative_to(data)),
            "size": st.st_size,
            "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
        })
    return sorted(rows, key=lambda r: r["path"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if DIAG.exists():
        for p in sorted(DIAG.rglob("*"), reverse=True):
            if p.is_file(): p.unlink()
            elif p.is_dir(): p.rmdir()
    DIAG.mkdir(parents=True, exist_ok=True)

    data, terminal_root = find_data_folder()
    logs = recent_logs(data, terminal_root)
    inv = history_inventory(data)

    summary = {
        "schema": "v45_mt5_failure_diagnostics_v1",
        "mt5_was_launched": False,
        "metaeditor_was_launched": False,
        "purpose": "diagnostics_only_no_rerun",
        "data_folder": str(data),
        "recent_log_count": len(logs),
        "history_inventory_count": len(inv),
        "history_year_tokens": sorted(set(re.findall(r"20\d{2}", "\n".join(r["path"] for r in inv)))),
        "logs": [],
    }

    for idx, p in enumerate(logs[:40], 1):
        try:
            excerpt, hits = relevant_excerpt(p)
        except Exception as exc:
            summary["logs"].append({"path": str(p), "error": repr(exc)})
            continue
        name = f"log_{idx:02d}_{p.name}.txt"
        (DIAG / name).write_text(excerpt, encoding="utf-8")
        summary["logs"].append({
            "path": str(p),
            "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.stat().st_mtime)),
            "size": p.stat().st_size,
            "hits": hits,
            "excerpt_file": name,
        })

    (DIAG / "history_inventory.json").write_text(json.dumps(inv, indent=2), encoding="utf-8")

    # Include only the V45 tester config and runner log, never generic account configs.
    cfgs = list(data.glob("config/v45_multiyear_single_run.ini"))
    for cfg in cfgs:
        try:
            text = sanitize(decode_log(cfg))
            (DIAG / "v45_multiyear_single_run.ini.txt").write_text(text, encoding="utf-8")
        except Exception:
            pass
    runner_log = OUT / "v45_multiyear_runner.log"
    if runner_log.is_file():
        (DIAG / "v45_multiyear_runner.log.txt").write_text(sanitize(runner_log.read_text(encoding="utf-8", errors="replace")), encoding="utf-8")

    (DIAG / "diagnostic_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if ZIP_OUT.exists(): ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(DIAG.iterdir(), key=lambda x: x.name):
            if p.is_file(): z.write(p, p.name)
    with zipfile.ZipFile(ZIP_OUT) as z:
        bad = z.testzip()
        if bad is not None: raise RuntimeError(f"diagnostic ZIP CRC failure: {bad}")

    print("V45 DIAGNOSTICS ONLY — MT5 WAS NOT RERUN")
    print(f"DATA_FOLDER={data}")
    print(f"RECENT_LOGS={len(logs)}")
    print(f"HISTORY_FILES={len(inv)}")
    print(f"HISTORY_YEAR_TOKENS={','.join(summary['history_year_tokens']) or 'none'}")
    print("UPLOAD THIS ONE DIAGNOSTIC ZIP:")
    print(ZIP_OUT)
    print(f"SHA256={sha256(ZIP_OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
