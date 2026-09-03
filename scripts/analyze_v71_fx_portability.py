#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

TIME_FORMATS = ("%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y.%m.%d")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size <= 0:
        return []
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


def parse_time(raw: str | None) -> datetime | None:
    value = (raw or "").strip()
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def summarize(values: list[float]) -> dict:
    wins = [x for x in values if x > 1e-9]
    losses = [x for x in values if x < -1e-9]
    gp = sum(wins)
    gl = -sum(losses)
    running = peak = max_dd = 0.0
    for value in values:
        running += value
        peak = max(peak, running)
        max_dd = max(max_dd, peak - running)
    return {
        "trades": len(values),
        "wins": len(wins),
        "losses": len(losses),
        "net_usd": round(sum(values), 8),
        "gross_profit_usd": round(gp, 8),
        "gross_loss_usd": round(gl, 8),
        "profit_factor": round(gp / gl, 6) if gl > 1e-12 else (999.0 if gp > 1e-12 else 0.0),
        "win_rate": round(len(wins) / len(values), 6) if values else 0.0,
        "avg_win_usd": round(gp / len(wins), 8) if wins else 0.0,
        "avg_loss_usd": round(sum(losses) / len(losses), 8) if losses else 0.0,
        "max_realized_dd_usd": round(max_dd, 8),
    }


def parse_trades(deals: list[dict[str, str]]) -> list[dict]:
    entries = [r for r in deals if integer(r, "entry") == 0]
    exits = [r for r in deals if integer(r, "entry") != 0]
    if len(entries) != len(exits):
        raise RuntimeError(f"V71 deal pairing mismatch entries={len(entries)} exits={len(exits)}")
    out: list[dict] = []
    for idx, (ent, ex) in enumerate(zip(entries, exits), 1):
        entry_dt = parse_time(ent.get("time"))
        exit_dt = parse_time(ex.get("time"))
        if entry_dt is None or exit_dt is None:
            raise RuntimeError(f"V71 invalid trade time index={idx}")
        entry_cost = num(ent, "commission") + num(ent, "swap") + num(ent, "fee")
        exit_cost = num(ex, "commission") + num(ex, "swap") + num(ex, "fee")
        realized = num(ex, "profit") + entry_cost + exit_cost
        out.append({
            "trade_index": idx,
            "entry_time": ent.get("time", ""),
            "exit_time": ex.get("time", ""),
            "duration_seconds": (exit_dt - entry_dt).total_seconds(),
            "entry_price": num(ent, "price"),
            "exit_price": num(ex, "price"),
            "gross_profit_usd": num(ex, "profit"),
            "explicit_cost_usd": entry_cost + exit_cost,
            "realized_pnl_usd": realized,
            "exit_reason": integer(ex, "reason"),
            "month": exit_dt.strftime("%Y-%m"),
        })
    return out


def analyze_symbol(symbol: str, run_dir: Path) -> dict:
    deals = read_csv(run_dir / "V64_DEALS.csv")
    events = read_csv(run_dir / "V64_EVENTS.csv")
    evals = read_csv(run_dir / "V64_ENTRY_EVAL.csv")
    trades = parse_trades(deals) if deals else []
    values = [float(t["realized_pnl_usd"]) for t in trades]
    base = summarize(values)
    monthly_values: defaultdict[str, list[float]] = defaultdict(list)
    for trade in trades:
        monthly_values[trade["month"]].append(float(trade["realized_pnl_usd"]))
    months = {month: summarize(vals) for month, vals in sorted(monthly_values.items())}
    event_counts = Counter((row.get("event") or "").strip() for row in events)
    eval_rejects = Counter((row.get("reject_reason") or "").strip() for row in evals if (row.get("reject_reason") or "").strip())
    losses = [t for t in trades if float(t["realized_pnl_usd"]) < -1e-9]
    positive_months = sum(1 for m in months.values() if float(m["net_usd"]) > 1e-9)
    negative_months = sum(1 for m in months.values() if float(m["net_usd"]) < -1e-9)
    flat_months = 9 - positive_months - negative_months
    base.update({
        "symbol": symbol,
        "explicit_cost_usd": round(sum(float(t["explicit_cost_usd"]) for t in trades), 8),
        "fast_losses_le_60s": sum(1 for t in losses if float(t["duration_seconds"]) <= 60.0),
        "fast_loss_share": round(sum(1 for t in losses if float(t["duration_seconds"]) <= 60.0) / len(losses), 6) if losses else 0.0,
        "positive_months": positive_months,
        "negative_months": negative_months,
        "flat_months": max(0, flat_months),
        "months": months,
        "event_counts": dict(sorted((k, v) for k, v in event_counts.items() if k)),
        "top_eval_rejects": dict(eval_rejects.most_common(12)),
        "trades_detail": trades,
    })
    return base


def rank_fx(results: dict[str, dict], control_symbol: str) -> list[dict]:
    rows = []
    for symbol, item in results.items():
        if symbol == control_symbol:
            continue
        rows.append({
            "symbol": symbol,
            "trades": item["trades"],
            "net_usd": item["net_usd"],
            "profit_factor": item["profit_factor"],
            "max_realized_dd_usd": item["max_realized_dd_usd"],
            "positive_months": item["positive_months"],
            "negative_months": item["negative_months"],
            "fast_loss_share": item["fast_loss_share"],
        })
    rows.sort(key=lambda r: (r["net_usd"], r["profit_factor"], r["trades"]), reverse=True)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", required=True, help="SYMBOL=PATH")
    ap.add_argument("--control-symbol", default="XAUUSDm")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    args = ap.parse_args()

    results: dict[str, dict] = {}
    for spec in args.run:
        if "=" not in spec:
            raise RuntimeError(f"invalid --run {spec!r}; expected SYMBOL=PATH")
        symbol, path = spec.split("=", 1)
        symbol = symbol.strip()
        if not symbol or symbol in results:
            raise RuntimeError(f"invalid/duplicate symbol {symbol!r}")
        results[symbol] = analyze_symbol(symbol, Path(path))

    ranking = rank_fx(results, args.control_symbol)
    payload = {
        "protocol": "v71_fx_portability_v1",
        "development_only_not_independent": True,
        "strategy_semantics": "V69 LONG exact after metadata normalization",
        "fixed_lot": 0.01,
        "cash_risk_band_usd": [0.85, 1.10],
        "target_cash_usd": 3.50,
        "separation_cash_usd": 1.30,
        "control_symbol": args.control_symbol,
        "results": results,
        "fx_ranking": ranking,
        "short_enabled": False,
        "real_money_authorized": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "V71_FX_PORTABILITY_ANALYSIS=PASS",
        f"V71_FX_CONTROL_SYMBOL={args.control_symbol}",
        "V71_FX_RESULTS=" + json.dumps({k: {x: v[x] for x in ("trades", "wins", "losses", "net_usd", "profit_factor", "max_realized_dd_usd", "positive_months", "negative_months", "flat_months", "fast_losses_le_60s", "fast_loss_share", "explicit_cost_usd")} for k, v in results.items()}, sort_keys=True),
        "V71_FX_RANKING=" + json.dumps(ranking, sort_keys=True),
        "V71_FX_BY_MONTH=" + json.dumps({k: v["months"] for k, v in results.items()}, sort_keys=True),
        "V71_FX_EVENT_FUNNEL=" + json.dumps({k: v["event_counts"] for k, v in results.items()}, sort_keys=True),
        "V71_FX_TOP_EVAL_REJECTS=" + json.dumps({k: v["top_eval_rejects"] for k, v in results.items()}, sort_keys=True),
        "V71_FX_DEVELOPMENT_ONLY=1",
        "V71_SHORT_ENABLED=0",
        "REAL_MONEY_AUTHORIZED=0",
    ]
    args.summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
