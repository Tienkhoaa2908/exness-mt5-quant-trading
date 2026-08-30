#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

PREFIX = "V62"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size <= 0:
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def f(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, "") or default)
    except (TypeError, ValueError):
        return default


def i(row: dict[str, str], key: str, default: int = 0) -> int:
    try:
        return int(float(row.get(key, "") or default))
    except (TypeError, ValueError):
        return default


def pf(gp: float, gl: float) -> float:
    return gp / gl if gl > 1e-12 else (999.0 if gp > 1e-12 else 0.0)


def summarize_values(vals: list[float]) -> dict:
    wins = [x for x in vals if x > 1e-9]
    losses = [x for x in vals if x < -1e-9]
    gp = sum(wins)
    gl = -sum(losses)
    return {
        "trades": len(vals),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": len(wins) / len(vals) if vals else 0.0,
        "gross_profit_usd": gp,
        "gross_loss_usd": gl,
        "net_usd": sum(vals),
        "profit_factor": pf(gp, gl),
        "avg_win_usd": gp / len(wins) if wins else 0.0,
        "avg_loss_usd": sum(losses) / len(losses) if losses else 0.0,
        "max_single_loss_usd": min(losses) if losses else 0.0,
        "losses_over_1_usd": sum(1 for x in losses if x < -1.0 - 1e-9),
        "losses_over_1p25_usd": sum(1 for x in losses if x < -1.25 - 1e-9),
    }


def actual_summary(deals: list[dict[str, str]]) -> dict:
    all_net: list[float] = []
    exits: list[float] = []
    reasons = Counter()
    for row in deals:
        net = f(row, "profit") + f(row, "commission") + f(row, "swap") + f(row, "fee")
        all_net.append(net)
        if i(row, "entry") != 0:
            exits.append(net)
            reasons[str(i(row, "reason"))] += 1
    out = summarize_values(exits)
    running = peak = max_dd = 0.0
    for x in all_net:
        running += x
        peak = max(peak, running)
        max_dd = max(max_dd, peak - running)
    out.update({
        "all_deal_net_usd": sum(all_net),
        "entry_deals": sum(1 for row in deals if i(row, "entry") == 0),
        "exit_deals": len(exits),
        "max_realized_dd_usd": max_dd,
        "exit_reason_codes": dict(reasons),
    })
    return out


def shadow_summary(rows: list[dict[str, str]], col: str) -> dict:
    return summarize_values([f(row, col) for row in rows])


def analyze_run(run_dir: Path, direction: str, week: str) -> dict:
    evals = read_csv(run_dir / "V62_ENTRY_EVAL.csv")
    events = read_csv(run_dir / "V62_EVENTS.csv")
    deals = read_csv(run_dir / "V62_DEALS.csv")
    shadows = read_csv(run_dir / "V62_SHADOW_RR.csv")

    event_counts = Counter((row.get("event") or "") for row in events)
    pending_end = Counter((row.get("detail") or "") for row in events if (row.get("event") or "") == "PENDING_END")
    refine_wait = Counter((row.get("detail") or "") for row in events if (row.get("event") or "") == "REFINE_WAIT")
    refined = [row for row in events if (row.get("event") or "") == "REFINED_ENTRY"]
    sent = [row for row in refined if (row.get("detail") or "") == "sent"]
    locks = [row for row in events if (row.get("event") or "") == "PROFIT_LOCK"]
    preflight = [row for row in events if (row.get("event") or "") == "ORDER_PREFLIGHT"]

    allowed = 1 if direction == "LONG" else -1
    selected_allowed = [row for row in evals if i(row, "selected_direction") == allowed]
    selected_opposite = [row for row in evals if i(row, "selected_direction") == -allowed]
    feasible = [row for row in selected_allowed if i(row, "feasible") == 1]
    risk = [f(row, "risk_cash") for row in feasible if f(row, "risk_cash") > 0]
    stop_sources = Counter((row.get("stop_source") or "unknown") for row in feasible)

    return {
        "week": week,
        "direction": direction,
        "run_dir": run_dir.name,
        "directional_rows_allowed": len(selected_allowed),
        "directional_rows_opposite_filtered": len(selected_opposite),
        "pending_arms": event_counts["PENDING_ARM"],
        "pending_end_reasons": dict(pending_end),
        "refine_wait_reasons": dict(refine_wait),
        "refined_entry_attempts": len(refined),
        "refined_entries_sent": len(sent),
        "feasible_eval_rows": len(feasible),
        "stop_source_counts": dict(stop_sources),
        "risk_cash": {
            "min": min(risk) if risk else 0.0,
            "avg": sum(risk) / len(risk) if risk else 0.0,
            "max": max(risk) if risk else 0.0,
        },
        "profit_lock_modified": sum(1 for row in locks if (row.get("detail") or "") == "modified"),
        "profit_lock_failed": sum(1 for row in locks if (row.get("detail") or "") != "modified"),
        "order_preflight_blocks": len(preflight),
        "order_preflight_details": dict(Counter((row.get("detail") or "") for row in preflight)),
        "actual": actual_summary(deals),
        "shadow_2": shadow_summary(shadows, "result_cash_2"),
        "shadow_3": shadow_summary(shadows, "result_cash_3"),
        "shadow_4": shadow_summary(shadows, "result_cash_4"),
    }


def combine_actual(parts: list[dict]) -> dict:
    gp = sum(x["actual"]["gross_profit_usd"] for x in parts)
    gl = sum(x["actual"]["gross_loss_usd"] for x in parts)
    trades = sum(x["actual"]["trades"] for x in parts)
    wins = sum(x["actual"]["wins"] for x in parts)
    losses = sum(x["actual"]["losses"] for x in parts)
    return {
        "trades": trades,
        "wins": wins,
        "losses": losses,
        "win_rate": wins / trades if trades else 0.0,
        "gross_profit_usd": gp,
        "gross_loss_usd": gl,
        "net_usd": gp - gl,
        "profit_factor": pf(gp, gl),
        "avg_win_usd": gp / wins if wins else 0.0,
        "avg_loss_usd": -gl / losses if losses else 0.0,
        "max_single_loss_usd": min((x["actual"]["max_single_loss_usd"] for x in parts), default=0.0),
        "note": "sum_of_direction_isolated_passes_not_concurrent_portfolio_equity",
    }


def analyze(run_dirs: list[Path]) -> dict:
    runs: list[dict] = []
    for rd in run_dirs:
        name = rd.name.lower()
        if "_long" in name:
            direction = "LONG"
        elif "_short" in name:
            direction = "SHORT"
        else:
            raise RuntimeError(f"run directory must end in _long or _short: {rd}")
        week = name.split("_", 1)[0]
        runs.append(analyze_run(rd, direction, week))

    by_week: dict[str, dict] = {}
    groups: defaultdict[str, list[dict]] = defaultdict(list)
    for run in runs:
        groups[run["week"]].append(run)
    for week, parts in sorted(groups.items()):
        long = next((x for x in parts if x["direction"] == "LONG"), None)
        short = next((x for x in parts if x["direction"] == "SHORT"), None)
        by_week[week] = {
            "LONG": long,
            "SHORT": short,
            "combined_isolated_sum": combine_actual(parts),
        }

    long_runs = [x for x in runs if x["direction"] == "LONG"]
    short_runs = [x for x in runs if x["direction"] == "SHORT"]
    return {
        "protocol": "four_fixed_recent_weeks_x_two_direction_isolated_model4_real_tick_passes",
        "runs": runs,
        "weeks": by_week,
        "month": {
            "LONG": combine_actual(long_runs),
            "SHORT": combine_actual(short_runs),
            "combined_isolated_sum": combine_actual(runs),
            "pending_arms_long": sum(x["pending_arms"] for x in long_runs),
            "pending_arms_short": sum(x["pending_arms"] for x in short_runs),
            "refined_entries_long": sum(x["refined_entries_sent"] for x in long_runs),
            "refined_entries_short": sum(x["refined_entries_sent"] for x in short_runs),
        },
    }


def write_summary(result: dict, path: Path) -> None:
    lines = [
        "V62_DIRECTION_ISOLATED_ENTRY_REFINEMENT_ANALYSIS=1",
        "PROTOCOL=four_fixed_recent_weeks_x_long_short_model4_real_ticks",
    ]
    for week, block in sorted(result["weeks"].items()):
        for direction in ("LONG", "SHORT"):
            run = block.get(direction)
            if not run:
                continue
            a = run["actual"]
            lines.append(
                f"WEEK={week} DIR={direction} signals={run['directional_rows_allowed']} arms={run['pending_arms']} "
                f"refined_sent={run['refined_entries_sent']} trades={a['trades']} wins={a['wins']} losses={a['losses']} "
                f"win_rate={a['win_rate']:.4f} net_usd={a['net_usd']:.4f} pf={a['profit_factor']:.4f} "
                f"avg_win_usd={a['avg_win_usd']:.4f} avg_loss_usd={a['avg_loss_usd']:.4f} "
                f"max_single_loss_usd={a['max_single_loss_usd']:.4f}"
            )
            lines.append(f"WEEK={week} DIR={direction} PENDING_END=" + json.dumps(run["pending_end_reasons"], sort_keys=True))
            lines.append(f"WEEK={week} DIR={direction} REFINE_WAIT=" + json.dumps(run["refine_wait_reasons"], sort_keys=True))
        c = block["combined_isolated_sum"]
        lines.append(
            f"WEEK={week} COMBINED_ISOLATED_SUM trades={c['trades']} wins={c['wins']} losses={c['losses']} "
            f"net_usd={c['net_usd']:.4f} pf={c['profit_factor']:.4f}"
        )

    month = result["month"]
    for direction in ("LONG", "SHORT"):
        a = month[direction]
        lines.append(
            f"MONTH DIR={direction} trades={a['trades']} wins={a['wins']} losses={a['losses']} "
            f"win_rate={a['win_rate']:.4f} gross_profit_usd={a['gross_profit_usd']:.4f} "
            f"gross_loss_usd={a['gross_loss_usd']:.4f} net_usd={a['net_usd']:.4f} pf={a['profit_factor']:.4f} "
            f"avg_win_usd={a['avg_win_usd']:.4f} avg_loss_usd={a['avg_loss_usd']:.4f} "
            f"max_single_loss_usd={a['max_single_loss_usd']:.4f}"
        )
    c = month["combined_isolated_sum"]
    lines += [
        f"MONTH_COMBINED_ISOLATED_SUM trades={c['trades']} wins={c['wins']} losses={c['losses']} net_usd={c['net_usd']:.4f} pf={c['profit_factor']:.4f}",
        f"MONTH_PENDING_ARMS_LONG={month['pending_arms_long']}",
        f"MONTH_PENDING_ARMS_SHORT={month['pending_arms_short']}",
        f"MONTH_REFINED_ENTRIES_LONG={month['refined_entries_long']}",
        f"MONTH_REFINED_ENTRIES_SHORT={month['refined_entries_short']}",
        "COMBINED_NOTE=sum_of_direction_isolated_passes_not_concurrent_portfolio_equity",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", action="append", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    args = ap.parse_args()
    result = analyze(args.run_dir)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result, args.summary)
    print(args.summary.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
