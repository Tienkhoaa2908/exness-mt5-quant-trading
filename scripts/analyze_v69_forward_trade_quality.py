#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

TIME_FORMATS = (
    "%Y.%m.%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y.%m.%d %H:%M",
    "%Y-%m-%d %H:%M",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size <= 0:
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def num(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, "") or default)
    except (TypeError, ValueError):
        return default


def integer(row: dict[str, str], key: str, default: int = 0) -> int:
    try:
        return int(float(row.get(key, "") or default))
    except (TypeError, ValueError):
        return default


def parse_time(value: str | None) -> datetime | None:
    s = (value or "").strip()
    if not s:
        return None
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def first_present(row: dict[str, str], names: Iterable[str]) -> str:
    for name in names:
        value = (row.get(name) or "").strip()
        if value:
            return value
    return ""


def profit_factor(gross_profit: float, gross_loss_abs: float) -> float:
    if gross_loss_abs > 1e-12:
        return gross_profit / gross_loss_abs
    return 999.0 if gross_profit > 1e-12 else 0.0


def summarize_pnl(values: list[float]) -> dict:
    wins = [x for x in values if x > 1e-9]
    losses = [x for x in values if x < -1e-9]
    gross_profit = sum(wins)
    gross_loss_abs = -sum(losses)
    running = peak = max_dd = 0.0
    for x in values:
        running += x
        peak = max(peak, running)
        max_dd = max(max_dd, peak - running)
    return {
        "trades": len(values),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": len(wins) / len(values) if values else 0.0,
        "gross_profit_usd": gross_profit,
        "gross_loss_usd": gross_loss_abs,
        "net_usd": sum(values),
        "profit_factor": profit_factor(gross_profit, gross_loss_abs),
        "avg_win_usd": gross_profit / len(wins) if wins else 0.0,
        "avg_loss_usd": sum(losses) / len(losses) if losses else 0.0,
        "max_single_loss_usd": min(losses) if losses else 0.0,
        "max_realized_dd_usd": max_dd,
    }


def parse_deals(rows: list[dict[str, str]]) -> list[dict]:
    entries = [r for r in rows if integer(r, "entry") == 0]
    exits = [r for r in rows if integer(r, "entry") != 0]
    trades: list[dict] = []
    for idx, ex in enumerate(exits):
        ent = entries[idx] if idx < len(entries) else {}
        entry_time_raw = ent.get("time", "")
        exit_time_raw = ex.get("time", "")
        entry_time = parse_time(entry_time_raw)
        exit_time = parse_time(exit_time_raw)
        duration = (
            (exit_time - entry_time).total_seconds()
            if entry_time is not None and exit_time is not None
            else None
        )
        realized = (
            num(ex, "profit")
            + num(ex, "commission")
            + num(ex, "swap")
            + num(ex, "fee")
        )
        entry_cost = num(ent, "commission") + num(ent, "swap") + num(ent, "fee")
        exit_cost = num(ex, "commission") + num(ex, "swap") + num(ex, "fee")
        trades.append(
            {
                "trade_index": idx + 1,
                "entry_time": entry_time_raw,
                "exit_time": exit_time_raw,
                "entry_time_dt": entry_time,
                "exit_time_dt": exit_time,
                "entry_price": num(ent, "price"),
                "exit_price": num(ex, "price"),
                "realized_pnl_usd": realized,
                "duration_seconds": duration,
                "exit_reason": integer(ex, "reason"),
                "explicit_cost_usd": entry_cost + exit_cost,
            }
        )
    return trades


def parse_noise(rows: list[dict[str, str]]) -> list[dict]:
    out: list[dict] = []
    for idx, row in enumerate(rows):
        start_raw = first_present(
            row,
            ("started", "start_time", "time_start", "start", "entry_time"),
        )
        end_raw = first_present(
            row,
            ("ended", "end_time", "time_end", "end", "finish_time"),
        )
        out.append(
            {
                "noise_index": idx + 1,
                "start_time": start_raw,
                "end_time": end_raw,
                "start_time_dt": parse_time(start_raw),
                "end_time_dt": parse_time(end_raw),
                "direction": integer(row, "dir"),
                "entry_price": num(row, "entry"),
                "mfe_usd": num(row, "max_pnl"),
                "mae_usd": num(row, "min_pnl"),
                "reason": row.get("reason", ""),
            }
        )
    return out


def match_noise(trades: list[dict], noise: list[dict], max_seconds: float = 10.0) -> None:
    available = set(range(len(noise)))
    for trade in trades:
        entry_time = trade["entry_time_dt"]
        best: tuple[float, int] | None = None
        if entry_time is not None:
            for ni in available:
                nt = noise[ni]["start_time_dt"]
                if nt is None:
                    continue
                delta = abs((nt - entry_time).total_seconds())
                if delta <= max_seconds and (best is None or delta < best[0]):
                    best = (delta, ni)
        if best is None:
            trade["noise_matched"] = False
            trade["mfe_usd"] = None
            trade["mae_usd"] = None
            continue
        _, ni = best
        available.remove(ni)
        n = noise[ni]
        trade["noise_matched"] = True
        trade["noise_index"] = n["noise_index"]
        trade["mfe_usd"] = n["mfe_usd"]
        trade["mae_usd"] = n["mae_usd"]
        trade["noise_reason"] = n["reason"]


def enrich_trade_quality(trades: list[dict]) -> None:
    prev: dict | None = None
    for trade in trades:
        mfe = trade.get("mfe_usd")
        realized = trade["realized_pnl_usd"]
        if isinstance(mfe, (int, float)):
            giveback = max(0.0, mfe - realized)
            trade["giveback_usd"] = giveback
            trade["capture_ratio_of_mfe"] = realized / mfe if mfe > 1e-9 else None
            trade["ratchet_eligible_mfe_ge_2"] = mfe >= 2.0 - 1e-9
            trade["mfe_positive_but_realized_loss"] = mfe > 1e-9 and realized < -1e-9
            trade["sub2_peak_roundtrip_loss"] = (
                mfe > 1e-9 and mfe < 2.0 - 1e-9 and realized < -1e-9
            )
            trade["mfe_ge_2_but_realized_below_1"] = (
                mfe >= 2.0 - 1e-9 and realized < 1.0 - 1e-9
            )
        else:
            trade["giveback_usd"] = None
            trade["capture_ratio_of_mfe"] = None
            trade["ratchet_eligible_mfe_ge_2"] = None
            trade["mfe_positive_but_realized_loss"] = None
            trade["sub2_peak_roundtrip_loss"] = None
            trade["mfe_ge_2_but_realized_below_1"] = None

        if prev is not None:
            cur_entry = trade["entry_time_dt"]
            prev_entry = prev["entry_time_dt"]
            prev_exit = prev["exit_time_dt"]
            trade["gap_from_prev_entry_seconds"] = (
                (cur_entry - prev_entry).total_seconds()
                if cur_entry is not None and prev_entry is not None
                else None
            )
            trade["gap_from_prev_exit_seconds"] = (
                (cur_entry - prev_exit).total_seconds()
                if cur_entry is not None and prev_exit is not None
                else None
            )
            trade["prev_trade_was_win"] = prev["realized_pnl_usd"] > 1e-9
            trade["prev_trade_was_loss"] = prev["realized_pnl_usd"] < -1e-9
        else:
            trade["gap_from_prev_entry_seconds"] = None
            trade["gap_from_prev_exit_seconds"] = None
            trade["prev_trade_was_win"] = None
            trade["prev_trade_was_loss"] = None
        prev = trade


def event_summary(rows: list[dict[str, str]]) -> dict:
    event_counts = Counter((r.get("event") or "") for r in rows)
    profit_lock_details = Counter(
        (r.get("detail") or "")
        for r in rows
        if (r.get("event") or "") == "PROFIT_LOCK"
    )
    entry_arch = Counter(
        (r.get("detail") or "")
        for r in rows
        if (r.get("event") or "") == "POST_CONFIRM_ENTRY_READY"
    )
    return {
        "event_counts": dict(sorted(event_counts.items())),
        "profit_lock_details": dict(sorted(profit_lock_details.items())),
        "post_confirm_entry_ready_archetypes": dict(sorted(entry_arch.items())),
    }


def median_or_zero(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def quality_summary(trades: list[dict], events: list[dict[str, str]]) -> dict:
    pnl = [t["realized_pnl_usd"] for t in trades]
    base = summarize_pnl(pnl)
    matched = [t for t in trades if t.get("noise_matched")]
    losses = [t for t in trades if t["realized_pnl_usd"] < -1e-9]
    wins = [t for t in trades if t["realized_pnl_usd"] > 1e-9]
    matched_losses = [t for t in matched if t["realized_pnl_usd"] < -1e-9]
    matched_wins = [t for t in matched if t["realized_pnl_usd"] > 1e-9]

    fast_loss = {}
    for seconds in (15, 30, 60):
        fast_loss[str(seconds)] = sum(
            1
            for t in losses
            if t["duration_seconds"] is not None and t["duration_seconds"] <= seconds
        )

    givebacks = [float(t["giveback_usd"]) for t in matched if t["giveback_usd"] is not None]
    capture = [
        float(t["capture_ratio_of_mfe"])
        for t in matched
        if t["capture_ratio_of_mfe"] is not None and math.isfinite(float(t["capture_ratio_of_mfe"]))
    ]
    winner_capture = [
        float(t["capture_ratio_of_mfe"])
        for t in matched_wins
        if t["capture_ratio_of_mfe"] is not None and math.isfinite(float(t["capture_ratio_of_mfe"]))
    ]
    loss_mfe = [float(t["mfe_usd"]) for t in matched_losses if t["mfe_usd"] is not None]
    loss_mae = [float(t["mae_usd"]) for t in matched_losses if t["mae_usd"] is not None]

    gaps = [
        float(t["gap_from_prev_exit_seconds"])
        for t in trades
        if t["gap_from_prev_exit_seconds"] is not None and t["gap_from_prev_exit_seconds"] >= 0
    ]
    cluster = {}
    for minutes in (5, 15, 30, 60):
        threshold = minutes * 60
        cluster[str(minutes)] = {
            "reentries": sum(1 for g in gaps if g <= threshold),
            "loss_after_win": sum(
                1
                for t in trades
                if t["realized_pnl_usd"] < -1e-9
                and t.get("prev_trade_was_win") is True
                and t.get("gap_from_prev_exit_seconds") is not None
                and 0 <= t["gap_from_prev_exit_seconds"] <= threshold
            ),
            "loss_after_loss": sum(
                1
                for t in trades
                if t["realized_pnl_usd"] < -1e-9
                and t.get("prev_trade_was_loss") is True
                and t.get("gap_from_prev_exit_seconds") is not None
                and 0 <= t["gap_from_prev_exit_seconds"] <= threshold
            ),
        }

    entry_days = {
        t["entry_time_dt"].date().isoformat()
        for t in trades
        if t["entry_time_dt"] is not None
    }
    explicit_cost = sum(float(t["explicit_cost_usd"]) for t in trades)

    base.update(
        {
            "noise_matched_trades": len(matched),
            "noise_match_rate": len(matched) / len(trades) if trades else 0.0,
            "fast_losses": fast_loss,
            "mfe_mae": {
                "median_mfe_all_usd": median_or_zero([float(t["mfe_usd"]) for t in matched]),
                "median_mae_all_usd": median_or_zero([float(t["mae_usd"]) for t in matched]),
                "median_mfe_losers_usd": median_or_zero(loss_mfe),
                "median_mae_losers_usd": median_or_zero(loss_mae),
                "median_mfe_winners_usd": median_or_zero([float(t["mfe_usd"]) for t in matched_wins]),
                "median_giveback_usd": median_or_zero(givebacks),
                "median_capture_ratio_of_mfe": median_or_zero(capture),
                "median_winner_capture_ratio_of_mfe": median_or_zero(winner_capture),
                "positive_mfe_realized_loss_count": sum(bool(t["mfe_positive_but_realized_loss"]) for t in matched),
                "sub2_peak_roundtrip_loss_count": sum(bool(t["sub2_peak_roundtrip_loss"]) for t in matched),
                "mfe_ge_2_realized_below_1_count": sum(bool(t["mfe_ge_2_but_realized_below_1"]) for t in matched),
            },
            "reentry_clusters": cluster,
            "turnover": {
                "active_entry_days": len(entry_days),
                "trades_per_active_day": len(trades) / len(entry_days) if entry_days else 0.0,
                "median_gap_from_previous_exit_seconds": median_or_zero(gaps),
                "explicit_commission_swap_fee_usd": explicit_cost,
            },
            "events": event_summary(events),
        }
    )
    return base


def diagnosis(summary: dict) -> dict:
    trades = int(summary.get("trades", 0))
    losses = int(summary.get("losses", 0))
    matched = int(summary.get("noise_matched_trades", 0))
    q = summary["mfe_mae"]
    c15 = summary["reentry_clusters"]["15"]

    signals: list[str] = []
    priority = "INSUFFICIENT_SAMPLE"
    if trades >= 8 and matched >= max(5, math.ceil(0.7 * trades)):
        fast60_rate = summary["fast_losses"]["60"] / losses if losses else 0.0
        low_mfe_loss = q["median_mfe_losers_usd"] < 0.50
        giveback_heavy = (
            q["positive_mfe_realized_loss_count"] >= 2
            or q["median_winner_capture_ratio_of_mfe"] < 0.55
        )
        clustered = c15["loss_after_win"] + c15["loss_after_loss"] >= 2

        if fast60_rate >= 0.40 and low_mfe_loss:
            signals.append("FAST_LOSS_LOW_MFE_ENTRY_FAILURE")
        if giveback_heavy:
            signals.append("PROFIT_GIVEBACK_OR_LATE_HARVEST")
        if clustered:
            signals.append("REENTRY_CLUSTERING")

        if "FAST_LOSS_LOW_MFE_ENTRY_FAILURE" in signals and "REENTRY_CLUSTERING" in signals:
            priority = "ENTRY_STATE_AND_REENTRY_SUPPRESSION"
        elif "FAST_LOSS_LOW_MFE_ENTRY_FAILURE" in signals:
            priority = "ENTRY_QUALITY"
        elif "PROFIT_GIVEBACK_OR_LATE_HARVEST" in signals:
            priority = "EXIT_HARVEST"
        elif "REENTRY_CLUSTERING" in signals:
            priority = "REENTRY_SUPPRESSION"
        else:
            priority = "NO_DOMINANT_FAILURE_MODE_YET"

    return {
        "sample_gate_trades": 8,
        "sample_gate_noise_match_rate": 0.70,
        "priority": priority,
        "signals": signals,
        "thresholds_are_diagnostic_not_strategy_parameters": True,
        "strategy_mutation_recommended_during_frozen_forward": False,
    }


def clean_trade_for_json(trade: dict) -> dict:
    return {
        k: v
        for k, v in trade.items()
        if not k.endswith("_dt")
    }


def analyze(root: Path) -> dict:
    deals_path = root / "V64_DEALS.csv"
    events_path = root / "V64_EVENTS.csv"
    noise_path = root / "V64_NOISE_SHADOW.csv"
    deals = read_csv(deals_path)
    events = read_csv(events_path)
    noise_rows = read_csv(noise_path)
    trades = parse_deals(deals)
    noise = parse_noise(noise_rows)
    match_noise(trades, noise)
    enrich_trade_quality(trades)
    summary = quality_summary(trades, events)
    return {
        "protocol": "v69_forward_trade_quality_read_only_diagnostics",
        "telemetry_root": str(root),
        "files": {
            "deals": str(deals_path),
            "events": str(events_path),
            "noise_shadow": str(noise_path),
        },
        "read_only": True,
        "changes_strategy": False,
        "summary": summary,
        "diagnosis": diagnosis(summary),
        "trades": [clean_trade_for_json(t) for t in trades],
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Read-only V69 forward trade-quality diagnostics: MFE/MAE, giveback, fast loss, re-entry clusters and turnover."
    )
    ap.add_argument("--telemetry-root", required=True, type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    result = analyze(args.telemetry_root)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")

    s = result["summary"]
    d = result["diagnosis"]
    print(
        "V69_TRADE_QUALITY "
        f"trades={s['trades']} wins={s['wins']} losses={s['losses']} "
        f"net_usd={s['net_usd']:.4f} pf={s['profit_factor']:.4f} "
        f"noise_match_rate={s['noise_match_rate']:.4f} priority={d['priority']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
