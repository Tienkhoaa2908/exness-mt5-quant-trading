#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

PREFIX = "V64"
WEEKLY_TRADE_GOAL = 3
WEEKLY_PROFIT_GOAL_USD = 6.0
NOISE_VARIANTS = {
    "s110_t300": (1.10, 3.00),
    "s110_t350": (1.10, 3.50),
    "s110_t400": (1.10, 4.00),
    "s135_t300": (1.35, 3.00),
    "s135_t350": (1.35, 3.50),
    "s135_t400": (1.35, 4.00),
    "s160_t300": (1.60, 3.00),
    "s160_t350": (1.60, 3.50),
    "s160_t400": (1.60, 4.00),
}


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
        "losses_over_1_usd": sum(1 for x in exits if x < -1.0 - 1e-9),
        "losses_over_1p15_usd": sum(1 for x in exits if x < -1.15 - 1e-9),
        "losses_over_1p25_usd": sum(1 for x in exits if x < -1.25 - 1e-9),
    })
    return out


def noise_summary(rows: list[dict[str, str]]) -> dict:
    out: dict[str, dict] = {}
    for col, (stop, target) in NOISE_VARIANTS.items():
        states = [i(row, col) for row in rows]
        resolved = [x for x in states if x in (-1, 1)]
        vals = [target if x == 1 else -stop for x in resolved]
        block = summarize_values(vals)
        block.update({
            "resolved": len(resolved),
            "unresolved": len(states) - len(resolved),
            "stop_cash": stop,
            "target_cash": target,
            # state=-1 proves stop was hit before target. If max_pnl later reaches
            # target by the fixed horizon, the setup was a stop-then-recovery.
            "stop_then_later_target": sum(
                1 for row in rows if i(row, col) == -1 and f(row, "max_pnl") >= target - 1e-9
            ),
        })
        out[col] = block
    return out


def parse_run_name(run_dir: Path) -> tuple[str, str, str]:
    name = run_dir.name.lower()
    direction = "LONG" if name.endswith("_long") else "SHORT" if name.endswith("_short") else ""
    if not direction:
        raise RuntimeError(f"V64 run directory must end in _long or _short: {run_dir}")
    stem = name.rsplit("_", 1)[0]
    if stem.startswith("benchmark_"):
        return "benchmark", stem.removeprefix("benchmark_"), direction
    if stem.startswith("bearish"):
        return "bearish", stem, direction
    raise RuntimeError(f"V64 unknown run label: {run_dir.name}")


def analyze_run(run_dir: Path) -> dict:
    kind, week, direction = parse_run_name(run_dir)
    evals = read_csv(run_dir / "V64_ENTRY_EVAL.csv")
    events = read_csv(run_dir / "V64_EVENTS.csv")
    deals = read_csv(run_dir / "V64_DEALS.csv")
    noise = read_csv(run_dir / "V64_NOISE_SHADOW.csv")

    event_counts = Counter((row.get("event") or "") for row in events)
    pending_end = Counter((row.get("detail") or "") for row in events if (row.get("event") or "") == "PENDING_END")
    risk_wait = Counter((row.get("detail") or "") for row in events if (row.get("event") or "") == "RISK_ZONE_WAIT")
    refine_wait = Counter((row.get("detail") or "") for row in events if (row.get("event") or "") == "REFINE_WAIT")
    entry_veto = Counter((row.get("detail") or "") for row in events if (row.get("event") or "") == "ENTRY_VETO")
    arms = [row for row in events if (row.get("event") or "") == "PENDING_ARM"]
    arm_arch = Counter((row.get("detail") or "") for row in arms)
    refined = [row for row in events if (row.get("event") or "") == "REFINED_ENTRY"]
    sent = [row for row in refined if (row.get("detail") or "") == "sent"]
    locks = [row for row in events if (row.get("event") or "") == "PROFIT_LOCK"]
    hard = [row for row in events if (row.get("event") or "") == "HARD_CASH_LOSS"]

    allowed = 1 if direction == "LONG" else -1
    selected = [row for row in evals if i(row, "selected_direction") == allowed]
    feasible = [row for row in selected if i(row, "feasible") == 1]
    ratios = []
    for row in feasible:
        risk = f(row, "risk_cash")
        spread = f(row, "spread_cash")
        if spread > 1e-12:
            ratios.append(risk / spread)

    return {
        "kind": kind,
        "week": week,
        "direction": direction,
        "run_dir": run_dir.name,
        "directional_rows_allowed": len(selected),
        "pending_arms": event_counts["PENDING_ARM"],
        "pending_refreshes": event_counts["PENDING_REFRESH"],
        "pending_arm_archetypes": dict(arm_arch),
        "pending_end_reasons": dict(pending_end),
        "risk_zone_wait_reasons": dict(risk_wait),
        "refine_wait_reasons": dict(refine_wait),
        "entry_veto_reasons": dict(entry_veto),
        "refined_entries_sent": len(sent),
        "profit_lock_modified": sum(1 for row in locks if (row.get("detail") or "") == "modified"),
        "hard_cash_loss_closed": sum(1 for row in hard if (row.get("detail") or "") == "closed"),
        "risk_spread_ratio": {
            "min": min(ratios) if ratios else 0.0,
            "avg": sum(ratios) / len(ratios) if ratios else 0.0,
            "max": max(ratios) if ratios else 0.0,
        },
        "actual": actual_summary(deals),
        "noise_shadow": noise_summary(noise),
        "noise_shadow_rows": len(noise),
    }


def combine_actual(parts: list[dict]) -> dict:
    gp = sum(x["actual"]["gross_profit_usd"] for x in parts)
    gl = sum(x["actual"]["gross_loss_usd"] for x in parts)
    trades = sum(x["actual"]["trades"] for x in parts)
    wins = sum(x["actual"]["wins"] for x in parts)
    losses = sum(x["actual"]["losses"] for x in parts)
    max_loss = min((x["actual"]["max_single_loss_usd"] for x in parts), default=0.0)
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
        "max_single_loss_usd": max_loss,
        "note": "sum_of_direction_isolated_passes_not_concurrent_portfolio_equity",
    }


def combine_noise(parts: list[dict]) -> dict:
    rows: dict[str, dict] = {}
    for col, (stop, target) in NOISE_VARIANTS.items():
        wins = losses = unresolved = recoveries = 0
        for p in parts:
            b = p["noise_shadow"][col]
            wins += b["wins"]
            losses += b["losses"]
            unresolved += b["unresolved"]
            recoveries += b["stop_then_later_target"]
        vals = [target] * wins + [-stop] * losses
        block = summarize_values(vals)
        block.update({"unresolved": unresolved, "stop_then_later_target": recoveries, "stop_cash": stop, "target_cash": target})
        rows[col] = block
    return rows


def analyze(run_dirs: list[Path]) -> dict:
    runs = [analyze_run(rd) for rd in run_dirs]
    bench = [x for x in runs if x["kind"] == "benchmark"]
    bearish = [x for x in runs if x["kind"] == "bearish"]

    groups: defaultdict[str, list[dict]] = defaultdict(list)
    for r in bench:
        groups[r["week"]].append(r)
    weeks = {}
    for week, parts in sorted(groups.items()):
        weeks[week] = {
            "LONG": next((x for x in parts if x["direction"] == "LONG"), None),
            "SHORT": next((x for x in parts if x["direction"] == "SHORT"), None),
            "combined_isolated_sum": combine_actual(parts),
            "noise_shadow": combine_noise(parts),
        }

    bench_actual = combine_actual(bench)
    weekly = [x["combined_isolated_sum"] for x in weeks.values()]
    goals = {
        "avg_trades_per_week": bench_actual["trades"] / len(weekly) if weekly else 0.0,
        "weeks_at_least_3_trades": sum(1 for x in weekly if x["trades"] >= WEEKLY_TRADE_GOAL),
        "positive_weeks": sum(1 for x in weekly if x["net_usd"] > 0),
        "weeks_net_at_least_5_usd": sum(1 for x in weekly if x["net_usd"] >= 5.0),
        "weeks_net_at_least_6_usd": sum(1 for x in weekly if x["net_usd"] >= WEEKLY_PROFIT_GOAL_USD),
    }

    bearish_short = [x for x in bearish if x["direction"] == "SHORT"]
    return {
        "protocol": "v64_fixed_august_benchmark_plus_pnl_independent_bearish_short_validation",
        "runs": runs,
        "benchmark_weeks": weeks,
        "benchmark": {
            "LONG": combine_actual([x for x in bench if x["direction"] == "LONG"]),
            "SHORT": combine_actual([x for x in bench if x["direction"] == "SHORT"]),
            "combined_isolated_sum": bench_actual,
            "goals": goals,
            "noise_shadow": combine_noise(bench),
        },
        "bearish_short_validation": {
            "actual": combine_actual(bearish_short),
            "noise_shadow": combine_noise(bearish_short),
            "short_execution_observed": sum(x["actual"]["trades"] for x in bearish_short) > 0,
        },
    }


def fmt_actual(prefix: str, a: dict) -> str:
    return (
        f"{prefix} trades={a['trades']} wins={a['wins']} losses={a['losses']} "
        f"win_rate={a['win_rate']:.4f} net_usd={a['net_usd']:.4f} pf={a['profit_factor']:.4f} "
        f"avg_win_usd={a['avg_win_usd']:.4f} avg_loss_usd={a['avg_loss_usd']:.4f} "
        f"max_single_loss_usd={a['max_single_loss_usd']:.4f}"
    )


def write_summary(result: dict, path: Path) -> None:
    lines = [
        "V64_MICROSTRUCTURE_TRIGGER_SHADOW_ANALYSIS=1",
        "ACTUAL_TARGET_CASH=3.50",
        "PLANNED_RISK_BAND_CASH=0.85,1.20",
        "EMERGENCY_LOSS_CASH=1.15",
        "MIN_RISK_SPREAD_RATIO=4.0",
        "WEEKLY_RESEARCH_GOAL=about_3_quality_trades_and_6_usd_not_a_guarantee",
    ]
    for week, block in sorted(result["benchmark_weeks"].items()):
        for d in ("LONG", "SHORT"):
            r = block[d]
            if not r:
                continue
            lines.append(fmt_actual(f"BENCHMARK WEEK={week} DIR={d}", r["actual"]))
            lines.append(f"BENCHMARK WEEK={week} DIR={d} ARCHETYPES=" + json.dumps(r["pending_arm_archetypes"], sort_keys=True))
            lines.append(f"BENCHMARK WEEK={week} DIR={d} VETO=" + json.dumps(r["entry_veto_reasons"], sort_keys=True))
            lines.append(f"BENCHMARK WEEK={week} DIR={d} RISK_WAIT=" + json.dumps(r["risk_zone_wait_reasons"], sort_keys=True))
            lines.append(f"BENCHMARK WEEK={week} DIR={d} REFINE_WAIT=" + json.dumps(r["refine_wait_reasons"], sort_keys=True))
        lines.append(fmt_actual(f"BENCHMARK WEEK={week} COMBINED_ISOLATED_SUM", block["combined_isolated_sum"]))
    b = result["benchmark"]
    lines.append(fmt_actual("BENCHMARK MONTH DIR=LONG", b["LONG"]))
    lines.append(fmt_actual("BENCHMARK MONTH DIR=SHORT", b["SHORT"]))
    lines.append(fmt_actual("BENCHMARK MONTH COMBINED_ISOLATED_SUM", b["combined_isolated_sum"]))
    lines.append("BENCHMARK GOALS=" + json.dumps(b["goals"], sort_keys=True))
    lines.append(fmt_actual("BEARISH SHORT", result["bearish_short_validation"]["actual"]))
    for name, block in sorted(b["noise_shadow"].items()):
        lines.append(
            f"NOISE BENCHMARK {name} trades={block['trades']} wins={block['wins']} losses={block['losses']} "
            f"net_usd={block['net_usd']:.4f} pf={block['profit_factor']:.4f} "
            f"stop_then_later_target={block['stop_then_later_target']} unresolved={block['unresolved']}"
        )
    for name, block in sorted(result["bearish_short_validation"]["noise_shadow"].items()):
        lines.append(
            f"NOISE BEARISH_SHORT {name} trades={block['trades']} wins={block['wins']} losses={block['losses']} "
            f"net_usd={block['net_usd']:.4f} pf={block['profit_factor']:.4f} "
            f"stop_then_later_target={block['stop_then_later_target']} unresolved={block['unresolved']}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", action="append", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--summary", required=True, type=Path)
    args = ap.parse_args()
    result = analyze(args.run_dir)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result, args.summary)
    print(f"V64_ANALYSIS={args.output}")
    print(f"V64_SUMMARY={args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
