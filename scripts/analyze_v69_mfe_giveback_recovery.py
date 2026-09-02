#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import math
import statistics
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
TRADE_QUALITY_ANALYZER = REPO / "scripts" / "analyze_v69_forward_trade_quality.py"
CYCLE_ANALYZER = REPO / "scripts" / "analyze_v69_cycle_economics_rearm.py"
DEVELOPMENT_MONTHS = tuple(f"2025-{m:02d}" for m in range(9, 13)) + tuple(
    f"2026-{m:02d}" for m in range(1, 6)
)
MFE_THRESHOLDS_USD = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5)


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


trade_quality = load(TRADE_QUALITY_ANALYZER, "v69_trade_quality_for_mfe_recovery")
cycle_economics = load(CYCLE_ANALYZER, "v69_cycle_economics_for_mfe_recovery")


def median_or_none(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def finite_number(value) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def event_value(row: dict[str, str], *keys: str) -> float | None:
    for key in keys:
        raw = (row.get(key) or "").strip()
        if not raw:
            continue
        try:
            return float(raw)
        except ValueError:
            continue
    return None


def profit_lock_events_for_trade(events: list[dict[str, str]], entry_time, exit_time) -> list[dict]:
    out = []
    if entry_time is None or exit_time is None:
        return out
    for row in events:
        if (row.get("event") or "").strip() != "PROFIT_LOCK":
            continue
        when = trade_quality.parse_time(row.get("time"))
        if when is None or when < entry_time or when > exit_time:
            continue
        out.append(
            {
                "time": row.get("time", ""),
                "detail": (row.get("detail") or "").strip(),
                "reported_floating_usd": event_value(row, "v1", "value1"),
                "lock_price": event_value(row, "v2", "value2"),
                "tp_price": event_value(row, "v3", "value3"),
            }
        )
    return out


def analyze_run(run_dir: Path) -> dict:
    quality = trade_quality.analyze(run_dir)
    cycle = cycle_economics.analyze_run(run_dir)
    trades = list(quality.get("trades", []))
    sent_cycles = [item for item in cycle.get("cycles", []) if item.get("sent")]
    if len(trades) != len(sent_cycles):
        raise RuntimeError(
            f"trade/sent-cycle mismatch run={run_dir.name} trades={len(trades)} sent_cycles={len(sent_cycles)}"
        )

    events = trade_quality.read_csv(run_dir / "V64_EVENTS.csv")
    enriched = []
    for idx, (trade, sent_cycle) in enumerate(zip(trades, sent_cycles), 1):
        row = dict(trade)
        entry_dt = trade_quality.parse_time(row.get("entry_time"))
        exit_dt = trade_quality.parse_time(row.get("exit_time"))
        locks = profit_lock_events_for_trade(events, entry_dt, exit_dt)
        row["run_trade_index"] = idx
        row["archetype"] = sent_cycle.get("archetype", "UNKNOWN")
        row["profit_lock_events"] = locks
        row["profit_lock_event_count"] = len(locks)
        row["profit_lock_modified_count"] = sum(1 for item in locks if item.get("detail") == "modified")
        row["profit_lock_modify_failed_count"] = sum(1 for item in locks if item.get("detail") == "modify_failed")
        enriched.append(row)

    month = cycle_economics.month_from_run(run_dir)
    return {
        "run_dir": run_dir.name,
        "month": month,
        "summary": quality["summary"],
        "diagnosis": quality["diagnosis"],
        "trades": enriched,
    }


def group_summary(trades: list[dict]) -> dict:
    realized = [float(t.get("realized_pnl_usd") or 0.0) for t in trades]
    matched = [t for t in trades if t.get("noise_matched") is True and finite_number(t.get("mfe_usd")) is not None]
    winners = [t for t in trades if float(t.get("realized_pnl_usd") or 0.0) > 1e-9]
    losses = [t for t in trades if float(t.get("realized_pnl_usd") or 0.0) < -1e-9]
    matched_winners = [t for t in matched if float(t.get("realized_pnl_usd") or 0.0) > 1e-9]
    matched_losses = [t for t in matched if float(t.get("realized_pnl_usd") or 0.0) < -1e-9]

    gross_profit = sum(value for value in realized if value > 1e-9)
    gross_loss = -sum(value for value in realized if value < -1e-9)
    ratchet_eligible = [t for t in matched if float(t["mfe_usd"]) >= 2.0 - 1e-9]
    ratchet_miss = [t for t in ratchet_eligible if float(t.get("realized_pnl_usd") or 0.0) < 1.0 - 1e-9]
    positive_mfe_losses = [t for t in matched_losses if float(t["mfe_usd"]) > 1e-9]
    sub2_roundtrip_losses = [
        t for t in matched_losses if 1e-9 < float(t["mfe_usd"]) < 2.0 - 1e-9
    ]

    winner_capture = [
        finite_number(t.get("capture_ratio_of_mfe"))
        for t in matched_winners
        if finite_number(t.get("capture_ratio_of_mfe")) is not None
    ]
    givebacks = [
        finite_number(t.get("giveback_usd"))
        for t in matched
        if finite_number(t.get("giveback_usd")) is not None
    ]
    loss_mfe = [float(t["mfe_usd"]) for t in matched_losses]
    loss_mae = [float(t["mae_usd"]) for t in matched_losses if finite_number(t.get("mae_usd")) is not None]
    win_mfe = [float(t["mfe_usd"]) for t in matched_winners]

    thresholds = {}
    for threshold in MFE_THRESHOLDS_USD:
        reached = [t for t in matched if float(t["mfe_usd"]) >= threshold - 1e-9]
        thresholds[f"{threshold:.1f}"] = {
            "reached": len(reached),
            "realized_loss_after_reaching": sum(
                1 for t in reached if float(t.get("realized_pnl_usd") or 0.0) < -1e-9
            ),
            "realized_below_threshold": sum(
                1 for t in reached if float(t.get("realized_pnl_usd") or 0.0) < threshold - 1e-9
            ),
        }

    return {
        "trades": len(trades),
        "wins": len(winners),
        "losses": len(losses),
        "net_usd": round(sum(realized), 8),
        "gross_profit_usd": round(gross_profit, 8),
        "gross_loss_usd": round(gross_loss, 8),
        "profit_factor": round(gross_profit / gross_loss, 6) if gross_loss > 1e-12 else None,
        "noise_matched_trades": len(matched),
        "noise_match_rate": round(len(matched) / len(trades), 6) if trades else 0.0,
        "median_mfe_all_usd": median_or_none([float(t["mfe_usd"]) for t in matched]),
        "median_mfe_winners_usd": median_or_none(win_mfe),
        "median_mfe_losers_usd": median_or_none(loss_mfe),
        "median_mae_losers_usd": median_or_none(loss_mae),
        "median_giveback_usd": median_or_none([float(x) for x in givebacks if x is not None]),
        "median_winner_capture_ratio_of_mfe": median_or_none(
            [float(x) for x in winner_capture if x is not None]
        ),
        "positive_mfe_realized_loss_count": len(positive_mfe_losses),
        "sub2_peak_roundtrip_loss_count": len(sub2_roundtrip_losses),
        "ratchet_eligible_mfe_ge_2_count": len(ratchet_eligible),
        "mfe_ge_2_realized_below_1_count": len(ratchet_miss),
        "mfe_ge_2_realized_below_1_with_profit_lock_event": sum(
            1 for t in ratchet_miss if int(t.get("profit_lock_event_count") or 0) > 0
        ),
        "mfe_ge_2_realized_below_1_without_profit_lock_event": sum(
            1 for t in ratchet_miss if int(t.get("profit_lock_event_count") or 0) == 0
        ),
        "profit_lock_event_trades": sum(1 for t in trades if int(t.get("profit_lock_event_count") or 0) > 0),
        "profit_lock_modified_trades": sum(1 for t in trades if int(t.get("profit_lock_modified_count") or 0) > 0),
        "profit_lock_modify_failed_trades": sum(
            1 for t in trades if int(t.get("profit_lock_modify_failed_count") or 0) > 0
        ),
        "mfe_threshold_diagnostics": thresholds,
    }


def diagnosis(summary: dict) -> dict:
    trades = int(summary.get("trades", 0))
    matched = int(summary.get("noise_matched_trades", 0))
    match_rate = matched / trades if trades else 0.0
    signals = []
    if trades != 24:
        return {"priority": "IDENTITY_MISMATCH", "signals": ["EXPECTED_24_TRADES"]}
    if match_rate < 0.95:
        return {
            "priority": "INSUFFICIENT_MFE_COVERAGE",
            "signals": [f"NOISE_MATCH_RATE_{match_rate:.3f}"],
        }
    if int(summary.get("mfe_ge_2_realized_below_1_count", 0)) > 0:
        signals.append("RATCHET_ELIGIBLE_BUT_CAPTURE_BELOW_LOCK")
    if int(summary.get("positive_mfe_realized_loss_count", 0)) >= 2:
        signals.append("POSITIVE_MFE_ROUNDTRIP_LOSSES")
    capture = summary.get("median_winner_capture_ratio_of_mfe")
    if isinstance(capture, (int, float)) and capture < 0.55:
        signals.append("LOW_WINNER_MFE_CAPTURE")
    priority = "EXIT_HARVEST_RESEARCH" if signals else "NO_DOMINANT_GIVEBACK_SIGNAL"
    return {"priority": priority, "signals": signals}


def analyze(v69_root: Path) -> dict:
    runs = []
    all_trades = []
    for run_dir in sorted(v69_root.glob("holdout_*_long")):
        month = cycle_economics.month_from_run(run_dir)
        if month not in DEVELOPMENT_MONTHS:
            continue
        block = analyze_run(run_dir)
        runs.append(block)
        for trade in block["trades"]:
            row = dict(trade)
            row["month"] = month
            all_trades.append(row)

    found = [block["month"] for block in runs]
    if found != list(DEVELOPMENT_MONTHS):
        raise RuntimeError(f"expected development months={DEVELOPMENT_MONTHS} actual={found}")

    all_trades.sort(key=lambda row: trade_quality.parse_time(row.get("entry_time")) or trade_quality.datetime.min)
    for idx, trade in enumerate(all_trades, 1):
        trade["global_trade_index"] = idx

    by_month = {
        block["month"]: group_summary(block["trades"])
        for block in runs
    }
    archetypes = sorted({str(t.get("archetype") or "UNKNOWN") for t in all_trades})
    by_archetype = {
        archetype: group_summary([t for t in all_trades if (t.get("archetype") or "UNKNOWN") == archetype])
        for archetype in archetypes
    }
    summary = group_summary(all_trades)
    return {
        "protocol": "v69_mfe_giveback_recovery_v1",
        "development_period": "2025-09_to_2026-05",
        "summary": summary,
        "diagnosis": diagnosis(summary),
        "by_month": by_month,
        "by_archetype": by_archetype,
        "trades": all_trades,
        "interpretation": {
            "development_only_not_independent": True,
            "mfe_mae_source": "V64_NOISE_SHADOW max_pnl/min_pnl matched to deal entry time",
            "mfe_mae_are_price_pnl_excursions": True,
            "realized_pnl_includes_explicit_deal_costs": True,
            "mfe_thresholds_are_diagnostics_not_strategy_parameters": True,
            "trailing_exit_counterfactual_simulated": False,
            "trailing_requires_path_not_only_peak": True,
            "strategy_changed": False,
            "orders_sent": 0,
            "real_money_authorized": False,
            "short_enabled": False,
        },
    }


def write_outputs(result: dict, output: Path, summary_path: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    d = result["diagnosis"]
    lines = [
        "V69_MFE_GIVEBACK_RECOVERY=1",
        f"TRADES={s['trades']}",
        f"NOISE_MATCHED={s['noise_matched_trades']}",
        f"NET_USD={s['net_usd']}",
        f"POSITIVE_MFE_REALIZED_LOSSES={s['positive_mfe_realized_loss_count']}",
        f"SUB2_PEAK_ROUNDTRIP_LOSSES={s['sub2_peak_roundtrip_loss_count']}",
        f"RATCHET_ELIGIBLE_MFE_GE_2={s['ratchet_eligible_mfe_ge_2_count']}",
        f"MFE_GE_2_REALIZED_BELOW_1={s['mfe_ge_2_realized_below_1_count']}",
        f"PROFIT_LOCK_EVENT_TRADES={s['profit_lock_event_trades']}",
        f"MEDIAN_WINNER_CAPTURE_RATIO={s['median_winner_capture_ratio_of_mfe']}",
        f"PRIORITY={d['priority']}",
        "DEVELOPMENT_ONLY=1",
        "TRAILING_COUNTERFACTUAL_SIMULATED=0",
        "STRATEGY_CHANGED=0",
        "ORDERS_SENT=0",
        "REAL_MONEY_AUTHORIZED=0",
    ]
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
