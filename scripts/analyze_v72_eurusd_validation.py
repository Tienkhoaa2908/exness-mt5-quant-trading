#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

TIME_FORMAT = "%Y.%m.%d %H:%M:%S"
MIN_TRADES = 8
MIN_PROFIT_FACTOR = 1.25
MAX_DD_USD = 5.00
MIN_POSITIVE_MONTHS = 2


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"missing evidence file: {path}")
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


def summarize(values: list[float]) -> dict:
    wins = [x for x in values if x > 1e-9]
    losses = [x for x in values if x < -1e-9]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    running = peak = max_dd = 0.0
    for value in values:
        running += value
        peak = max(peak, running)
        max_dd = max(max_dd, peak - running)
    best = max(values) if values else 0.0
    return {
        "trades": len(values),
        "wins": len(wins),
        "losses": len(losses),
        "net_usd": round(sum(values), 8),
        "gross_profit_usd": round(gross_profit, 8),
        "gross_loss_usd": round(gross_loss, 8),
        "profit_factor": round(gross_profit / gross_loss, 6) if gross_loss > 1e-12 else (999.0 if gross_profit > 1e-12 else 0.0),
        "max_realized_dd_usd": round(max_dd, 8),
        "best_trade_usd": round(best, 8),
        "ex_best_trade_net_usd": round(sum(values) - best, 8),
    }


def analyze(run_dir: Path) -> dict:
    deals = read_csv(run_dir / "V64_DEALS.csv")
    events = read_csv(run_dir / "V64_EVENTS.csv")
    evals = read_csv(run_dir / "V64_ENTRY_EVAL.csv")
    entries = [r for r in deals if integer(r, "entry") == 0]
    exits = [r for r in deals if integer(r, "entry") != 0]
    if len(entries) != len(exits):
        raise RuntimeError(f"V72 deal pairing mismatch entries={len(entries)} exits={len(exits)}")

    values: list[float] = []
    durations: list[float] = []
    months: dict[str, float] = {}
    for idx, (ent, ex) in enumerate(zip(entries, exits), 1):
        try:
            t0 = datetime.strptime((ent.get("time") or "").strip(), TIME_FORMAT)
            t1 = datetime.strptime((ex.get("time") or "").strip(), TIME_FORMAT)
        except ValueError as exc:
            raise RuntimeError(f"V72 invalid deal time index={idx}") from exc
        pnl = num(ex, "profit") + num(ent, "commission") + num(ent, "swap") + num(ent, "fee") + num(ex, "commission") + num(ex, "swap") + num(ex, "fee")
        values.append(pnl)
        durations.append((t1 - t0).total_seconds())
        month = t1.strftime("%Y-%m")
        months[month] = months.get(month, 0.0) + pnl

    stats = summarize(values)
    positive_months = sum(1 for value in months.values() if value > 1e-9)
    losses_durations = [d for d, pnl in zip(durations, values) if pnl < -1e-9]
    stats.update({
        "positive_months": positive_months,
        "negative_months": sum(1 for value in months.values() if value < -1e-9),
        "months": {k: round(v, 8) for k, v in sorted(months.items())},
        "losses_le_15m": sum(1 for d in losses_durations if d <= 900.0),
        "losses_le_15m_share": round(sum(1 for d in losses_durations if d <= 900.0) / len(losses_durations), 6) if losses_durations else 0.0,
        "refined_entries": sum(1 for r in events if (r.get("event") or "").strip() == "REFINED_ENTRY"),
        "profit_locks": sum(1 for r in events if (r.get("event") or "").strip() == "PROFIT_LOCK"),
        "entry_eval_rows": len(evals),
    })

    if stats["trades"] < MIN_TRADES:
        classification = "INSUFFICIENT_SAMPLE"
    else:
        passed = (
            stats["net_usd"] > 0.0
            and stats["profit_factor"] >= MIN_PROFIT_FACTOR
            and stats["max_realized_dd_usd"] <= MAX_DD_USD
            and stats["positive_months"] >= MIN_POSITIVE_MONTHS
            and stats["ex_best_trade_net_usd"] > 0.0
        )
        classification = "PASS" if passed else "FAIL"

    return {
        "protocol": "v72_eurusd_untouched_validation_v1",
        "symbol": "EURUSDm",
        "period": ["2024.09.01", "2025.09.01"],
        "strategy": "exact V71/V69 LONG candidate; no retune",
        "preregistered_acceptance": {
            "min_trades": MIN_TRADES,
            "net_usd_gt": 0.0,
            "profit_factor_gte": MIN_PROFIT_FACTOR,
            "max_realized_dd_usd_lte": MAX_DD_USD,
            "positive_months_gte": MIN_POSITIVE_MONTHS,
            "ex_best_trade_net_usd_gt": 0.0,
        },
        "metrics": stats,
        "classification": classification,
        "short_enabled": False,
        "real_money_authorized": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    args = ap.parse_args()
    result = analyze(args.run_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "V72_EURUSD_VALIDATION_ANALYSIS=PASS",
        "V72_EURUSD_VALIDATION_CLASSIFICATION=" + result["classification"],
        "V72_EURUSD_VALIDATION_METRICS=" + json.dumps(result["metrics"], sort_keys=True),
        "V72_EURUSD_VALIDATION_ACCEPTANCE=" + json.dumps(result["preregistered_acceptance"], sort_keys=True),
        "V72_EURUSD_ENTRY_RETUNE=0",
        "V72_EURUSD_EXIT_RETUNE=0",
        "V72_SHORT_ENABLED=0",
        "REAL_MONEY_AUTHORIZED=0",
    ]
    args.summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
