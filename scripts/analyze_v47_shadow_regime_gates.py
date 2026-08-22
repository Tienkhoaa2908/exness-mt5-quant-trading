#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

PRIMARY = "v46_hl10_thr0p05_breadth4"
BOOK = "usd40_r1p0_cent_continuous"


def f(row: dict, key: str) -> float:
    try:
        return float(row.get(key, "") or 0.0)
    except ValueError:
        return 0.0


def passes_di(row: dict) -> bool:
    pdi, mdi = f(row, "entry_plus_di"), f(row, "entry_minus_di")
    d = row.get("direction", "")
    return (d == "LONG" and pdi > mdi) or (d == "SHORT" and mdi > pdi)


def passes_adx30(row: dict) -> bool:
    return f(row, "entry_adx") <= 30.0


def stats(rows: list[dict]) -> dict:
    rs = [f(r, "r_multiple") for r in rows]
    gp = sum(x for x in rs if x > 0)
    gl = -sum(x for x in rs if x < 0)
    pf = gp / gl if gl > 0 else (999.0 if gp > 0 else 0.0)
    return {
        "trades": len(rows),
        "sum_r": sum(rs),
        "avg_r": (sum(rs) / len(rs)) if rs else 0.0,
        "profit_factor_r": pf,
        "positive_trade_ratio": (sum(x > 0 for x in rs) / len(rs)) if rs else 0.0,
        "gross_positive_r": gp,
        "gross_negative_r_abs": gl,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--start-month", default="")
    args = ap.parse_args()

    with Path(args.trades).open("r", encoding="utf-8-sig", newline="") as fh:
        all_rows = list(csv.DictReader(fh))

    rows = [r for r in all_rows if r.get("candidate") == PRIMARY and r.get("book") == BOOK]
    if args.start_month:
        rows = [r for r in rows if (r.get("month", "").replace("_", "-") >= args.start_month)]

    variants = {
        "primary_breadth4": rows,
        "shadow_adx_le_30": [r for r in rows if passes_adx30(r)],
        "shadow_di_aligned": [r for r in rows if passes_di(r)],
        "shadow_adx_le_30_and_di_aligned": [r for r in rows if passes_adx30(r) and passes_di(r)],
    }

    primary_stats = stats(rows)
    out = {
        "schema": "v47_shadow_regime_gates_v1",
        "primary_candidate": PRIMARY,
        "book": BOOK,
        "shadow_only": True,
        "eligible_to_promote_from_this_analysis": False,
        "adx_rule": "entry_adx <= 30",
        "di_rule": "LONG: entry_plus_di > entry_minus_di; SHORT: entry_minus_di > entry_plus_di",
        "start_month": args.start_month,
        "variants": {},
        "yearly": {},
    }

    for name, subset in variants.items():
        s = stats(subset)
        if name != "primary_breadth4":
            kept = {id(r) for r in subset}
            removed = [r for r in rows if id(r) not in kept]
            removed_rs = [f(r, "r_multiple") for r in removed]
            s["trade_retention_ratio"] = len(subset) / len(rows) if rows else 0.0
            s["positive_r_retention_ratio"] = (
                s["gross_positive_r"] / primary_stats["gross_positive_r"]
                if primary_stats["gross_positive_r"] > 0 else 0.0
            )
            s["negative_r_avoided"] = -sum(x for x in removed_rs if x < 0)
            s["positive_r_removed"] = sum(x for x in removed_rs if x > 0)
        out["variants"][name] = s

        by_year = defaultdict(list)
        for r in subset:
            y = (r.get("entry_time") or r.get("month", ""))[:4]
            by_year[y].append(r)
        out["yearly"][name] = {y: stats(v) for y, v in sorted(by_year.items())}

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out["variants"], indent=2))
    print("V47 shadow analysis only; promotion is forbidden from this same-sample analysis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
