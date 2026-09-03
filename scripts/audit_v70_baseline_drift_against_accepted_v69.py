#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

ACCEPTED_V69_ZIP_SHA256 = "e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb"
MONTHS = ("2025_09", "2025_10", "2025_11", "2025_12", "2026_01", "2026_02", "2026_03", "2026_04", "2026_05")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rows_from_text(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def num(row: dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def integer(row: dict[str, str], key: str) -> int:
    try:
        return int(float(row.get(key, "") or 0))
    except (TypeError, ValueError):
        return 0


def exit_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [r for r in rows if integer(r, "entry") != 0]


def legacy_pnl(row: dict[str, str]) -> float:
    return num(row, "profit") + num(row, "commission") + num(row, "swap") + num(row, "fee")


def locate_member(zf: zipfile.ZipFile, month: str) -> str:
    suffix = f"holdout_{month}_long/V64_DEALS.csv"
    matches = [n for n in zf.namelist() if n.replace("\\", "/").endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(f"accepted V69 ZIP member mismatch month={month} matches={len(matches)}")
    return matches[0]


def find_accepted_zip(repo: Path, explicit: Path | None) -> Path:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    candidates += [
        repo / "runtime" / "v69_confirm_separation_retest" / "OUTPUT_V69" / "v69_confirm_separation_retest_research.zip",
        repo / "v69_confirm_separation_retest_research.zip",
    ]
    seen: set[Path] = set()
    for path in candidates:
        path = path.resolve()
        if path in seen:
            continue
        seen.add(path)
        if path.is_file() and sha256(path) == ACCEPTED_V69_ZIP_SHA256:
            return path
    # Last resort: search only the repo tree for the exact historical filename/hash.
    for path in repo.rglob("v69_confirm_separation_retest_research.zip"):
        if path.is_file() and sha256(path) == ACCEPTED_V69_ZIP_SHA256:
            return path.resolve()
    raise RuntimeError(
        "accepted V69 ZIP not found with exact SHA256=" + ACCEPTED_V69_ZIP_SHA256
    )


def compact(row: dict[str, str]) -> dict:
    return {
        "time": row.get("time", ""),
        "entry": integer(row, "entry"),
        "price": num(row, "price"),
        "profit": num(row, "profit"),
        "commission": num(row, "commission"),
        "swap": num(row, "swap"),
        "fee": num(row, "fee"),
        "reason": integer(row, "reason"),
        "legacy_pnl": legacy_pnl(row),
    }


def classify_pair(a: dict[str, str], b: dict[str, str]) -> str:
    if (a.get("time") or "") != (b.get("time") or ""):
        return "EXIT_TIME_DRIFT"
    if abs(num(a, "price") - num(b, "price")) > 1e-9:
        return "EXIT_PRICE_DRIFT"
    if abs(num(a, "profit") - num(b, "profit")) > 1e-9:
        return "EXIT_PROFIT_DRIFT"
    cost_a = num(a, "commission") + num(a, "swap") + num(a, "fee")
    cost_b = num(b, "commission") + num(b, "swap") + num(b, "fee")
    if abs(cost_a - cost_b) > 1e-9:
        return "EXIT_COST_DRIFT"
    if integer(a, "reason") != integer(b, "reason"):
        return "EXIT_REASON_DRIFT"
    return "IDENTICAL"


def audit(repo: Path, accepted_zip: Path | None = None) -> dict:
    zpath = find_accepted_zip(repo, accepted_zip)
    v70_root = repo / "runtime" / "v70_exit_harvest_research" / "OUTPUT_V70"
    diffs: list[dict] = []
    accepted_total = 0.0
    v70_total = 0.0
    accepted_trades = 0
    v70_trades = 0
    by_month: dict[str, dict] = {}

    with zipfile.ZipFile(zpath) as zf:
        if zf.testzip() is not None:
            raise RuntimeError("accepted V69 ZIP CRC failure")
        for month in MONTHS:
            member = locate_member(zf, month)
            accepted_rows = rows_from_text(zf.read(member).decode("utf-8-sig", errors="replace"))
            v70_path = v70_root / f"holdout_{month}_long" / "V64_DEALS.csv"
            if not v70_path.is_file():
                raise RuntimeError(f"missing V70 deals: {v70_path}")
            v70_rows = read_rows(v70_path)
            ae = exit_rows(accepted_rows)
            ve = exit_rows(v70_rows)
            accepted_trades += len(ae)
            v70_trades += len(ve)
            am = sum(legacy_pnl(r) for r in ae)
            vm = sum(legacy_pnl(r) for r in ve)
            accepted_total += am
            v70_total += vm
            by_month[month] = {
                "accepted_trades": len(ae),
                "v70_trades": len(ve),
                "accepted_net_usd": round(am, 8),
                "v70_net_usd": round(vm, 8),
                "delta_usd": round(vm - am, 8),
            }
            if len(ae) != len(ve):
                diffs.append({"month": month, "classification": "EXIT_COUNT_DRIFT", "accepted": len(ae), "v70": len(ve)})
            for idx, (a, b) in enumerate(zip(ae, ve), 1):
                pa = legacy_pnl(a)
                pb = legacy_pnl(b)
                cls = classify_pair(a, b)
                if cls != "IDENTICAL" or abs(pb - pa) > 1e-9:
                    diffs.append({
                        "month": month,
                        "trade_index_in_month": idx,
                        "classification": cls,
                        "accepted": compact(a),
                        "v70": compact(b),
                        "pnl_delta_usd": round(pb - pa, 8),
                    })

    delta = v70_total - accepted_total
    classes: dict[str, int] = {}
    for d in diffs:
        classes[d["classification"]] = classes.get(d["classification"], 0) + 1
    if accepted_trades != v70_trades:
        overall = "COHORT_DRIFT"
    elif not diffs:
        overall = "IDENTICAL_BASELINE"
    elif all(d.get("classification") in {"EXIT_PRICE_DRIFT", "EXIT_PROFIT_DRIFT", "EXIT_COST_DRIFT"} for d in diffs):
        overall = "SAME_EXIT_TIMES_VALUE_DRIFT"
    elif any(d.get("classification") == "EXIT_TIME_DRIFT" for d in diffs):
        overall = "EXIT_TIMING_DRIFT"
    else:
        overall = "MIXED_BASELINE_DRIFT"
    return {
        "accepted_zip": str(zpath),
        "accepted_zip_sha256": sha256(zpath),
        "accepted_trades": accepted_trades,
        "v70_trades": v70_trades,
        "accepted_net_usd": round(accepted_total, 8),
        "v70_net_usd": round(v70_total, 8),
        "delta_usd": round(delta, 8),
        "classification": overall,
        "difference_classes": classes,
        "by_month": by_month,
        "differences": diffs,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--accepted-zip", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = audit(args.repo.resolve(), args.accepted_zip)
    output = args.output or (args.repo / "runtime" / "v70_exit_harvest_research" / "OUTPUT_V70" / "V70_BASELINE_DRIFT_AUDIT.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"V70_BASELINE_AUDIT_ACCEPTED_ZIP=PASS sha256={result['accepted_zip_sha256']}")
    print(f"V70_BASELINE_AUDIT_TRADES=accepted:{result['accepted_trades']} v70:{result['v70_trades']}")
    print(f"V70_BASELINE_AUDIT_NET=accepted:{result['accepted_net_usd']:.8f} v70:{result['v70_net_usd']:.8f} delta:{result['delta_usd']:.8f}")
    print(f"V70_BASELINE_AUDIT_CLASSIFICATION={result['classification']}")
    print("V70_BASELINE_AUDIT_CLASSES=" + json.dumps(result["difference_classes"], sort_keys=True))
    print("V70_BASELINE_AUDIT_BY_MONTH=" + json.dumps(result["by_month"], sort_keys=True))
    print("V70_BASELINE_AUDIT_DIFFERENCES=" + json.dumps(result["differences"], sort_keys=True))
    print(f"V70_BASELINE_AUDIT_JSON={output}")
    print("V70_BASELINE_DRIFT_AUDIT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
