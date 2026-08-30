#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path

START_BALANCE = 40.0


def rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size <= 0:
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def f(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        v = float(row.get(key, "") or default)
        return v if math.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def i(row: dict[str, str], key: str, default: int = 0) -> int:
    try:
        return int(float(row.get(key, "") or default))
    except (TypeError, ValueError):
        return default


def pnl_stats(pnls: list[float], rvals: list[float]) -> dict:
    wins = [x for x in pnls if x > 1e-12]
    losses = [x for x in pnls if x < -1e-12]
    gross_profit = sum(wins)
    gross_loss = sum(losses)
    balance = START_BALANCE
    peak = balance
    max_dd = 0.0
    min_balance = balance
    for p in pnls:
        balance += p
        peak = max(peak, balance)
        min_balance = min(min_balance, balance)
        if peak > 0:
            max_dd = max(max_dd, 100.0 * (peak - balance) / peak)
    win_r = [r for r in rvals if r > 0]
    loss_r = [r for r in rvals if r < 0]
    return {
        "trades": len(pnls),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": 100.0 * len(wins) / len(pnls) if pnls else 0.0,
        "gross_profit_usd": gross_profit,
        "gross_loss_usd": gross_loss,
        "net_usd": sum(pnls),
        "profit_factor": gross_profit / abs(gross_loss) if gross_loss < -1e-12 else (999.0 if gross_profit > 0 else 0.0),
        "avg_win_r": sum(win_r) / len(win_r) if win_r else 0.0,
        "avg_loss_r": sum(loss_r) / len(loss_r) if loss_r else 0.0,
        "sum_r": sum(rvals),
        "end_balance_proxy": balance,
        "return_pct_proxy": 100.0 * (balance - START_BALANCE) / START_BALANCE,
        "max_realized_dd_pct_proxy": max_dd,
        "min_balance_proxy": min_balance,
        "balance_breach_proxy": min_balance <= 0.0,
    }


def rr_summary(shadow: list[dict[str, str]], col: str) -> dict:
    pnls: list[float] = []
    rvals: list[float] = []
    by_dir: dict[str, list[tuple[float, float]]] = {"LONG": [], "SHORT": []}
    for row in shadow:
        r = f(row, col)
        risk = f(row, "risk_cash")
        if risk <= 0 or abs(r) < 1e-12:
            continue
        p = r * risk
        pnls.append(p)
        rvals.append(r)
        key = "LONG" if i(row, "direction") > 0 else "SHORT"
        by_dir[key].append((p, r))
    out = pnl_stats(pnls, rvals)
    out["by_direction"] = {
        k: pnl_stats([x[0] for x in vals], [x[1] for x in vals]) for k, vals in by_dir.items()
    }
    return out


def actual_summary(deals: list[dict[str, str]]) -> dict:
    pnls: list[float] = []
    entries = exits = 0
    reasons: Counter[str] = Counter()
    direction_entries: Counter[str] = Counter()
    for row in deals:
        entry = i(row, "entry", -1)
        dtype = i(row, "deal_type", -1)
        reason = i(row, "reason", -1)
        net = f(row, "profit") + f(row, "commission") + f(row, "swap") + f(row, "fee")
        pnls.append(net)
        if entry in (0, 2):
            entries += 1
            if dtype == 0:
                direction_entries["LONG"] += 1
            elif dtype == 1:
                direction_entries["SHORT"] += 1
        if entry in (1, 2):
            exits += 1
            reasons[str(reason)] += 1
    s = pnl_stats(pnls, [])
    s.update({
        "entry_deals": entries,
        "exit_deals": exits,
        "entry_direction_counts": dict(direction_entries),
        "exit_reason_codes": dict(reasons),
        "sl_exit_deals": reasons.get("4", 0),
        "tp_exit_deals": reasons.get("5", 0),
    })
    return s


def eval_summary(evals: list[dict[str, str]]) -> dict:
    selected = Counter()
    feasible = Counter()
    rejects = Counter()
    decision = Counter()
    score_long: list[int] = []
    score_short: list[int] = []
    align = Counter()
    for row in evals:
        d = i(row, "selected_direction")
        decision[row.get("decision_reason", "") or ""] += 1
        if d:
            key = "LONG" if d > 0 else "SHORT"
            selected[key] += 1
            score_long.append(i(row, "long_score"))
            score_short.append(i(row, "short_score"))
            if i(row, "feasible") == 1:
                feasible[key] += 1
            else:
                rejects[row.get("reject_reason", "") or "unknown"] += 1
            for feature in (
                "h4_trend", "h1_trend", "m15_trend", "structure_dir", "bos_choch_dir",
                "fvg_dir", "liquidity_sweep_dir", "order_block_retest_dir", "pullback_dir",
                "di_dir", "macd_dir", "location_dir",
            ):
                if i(row, feature) == d:
                    align[f"{key}:{feature}"] += 1
    return {
        "bars_evaluated": len(evals),
        "selected_direction_counts": dict(selected),
        "feasible_direction_counts": dict(feasible),
        "reject_reason_counts": dict(rejects),
        "decision_reason_counts": dict(decision),
        "avg_long_score_on_selected": sum(score_long) / len(score_long) if score_long else 0.0,
        "avg_short_score_on_selected": sum(score_short) / len(score_short) if score_short else 0.0,
        "aligned_feature_counts": dict(align),
    }


def analyze_run(run_dir: Path) -> dict:
    evals = rows(run_dir / "V59_ENTRY_EVAL.csv")
    shadow = rows(run_dir / "V59_SHADOW_RR.csv")
    deals = rows(run_dir / "V59_DEALS.csv")
    return {
        "run": run_dir.name,
        "evaluation": eval_summary(evals),
        "rr_2_0": rr_summary(shadow, "result_2r"),
        "rr_2_5": rr_summary(shadow, "result_2p5r"),
        "rr_3_0": rr_summary(shadow, "result_3r"),
        "actual_broker": actual_summary(deals),
        "shadow_rows": len(shadow),
        "deal_rows": len(deals),
    }


def combine(run_dirs: list[Path]) -> dict:
    eval_all: list[dict[str, str]] = []
    shadow_all: list[dict[str, str]] = []
    deals_all: list[dict[str, str]] = []
    individual = []
    for rd in run_dirs:
        individual.append(analyze_run(rd))
        eval_all += rows(rd / "V59_ENTRY_EVAL.csv")
        shadow_all += rows(rd / "V59_SHADOW_RR.csv")
        deals_all += rows(rd / "V59_DEALS.csv")
    return {
        "runs": individual,
        "combined": {
            "evaluation": eval_summary(eval_all),
            "rr_2_0": rr_summary(shadow_all, "result_2r"),
            "rr_2_5": rr_summary(shadow_all, "result_2p5r"),
            "rr_3_0": rr_summary(shadow_all, "result_3r"),
            "actual_broker": actual_summary(deals_all),
        },
    }


def fmt_stats(name: str, s: dict) -> str:
    return (
        f"{name}: trades={s['trades']} wins={s['wins']} losses={s['losses']} "
        f"win_rate={s['win_rate_pct']:.2f}% gross_profit=${s['gross_profit_usd']:.4f} "
        f"gross_loss=${s['gross_loss_usd']:.4f} net=${s['net_usd']:.4f} "
        f"PF={s['profit_factor']:.4f} avg_win_R={s['avg_win_r']:.4f} "
        f"avg_loss_R={s['avg_loss_r']:.4f} maxDD={s['max_realized_dd_pct_proxy']:.2f}% "
        f"end=${s['end_balance_proxy']:.4f}"
    )


def make_summary(result: dict) -> str:
    c = result["combined"]
    e = c["evaluation"]
    a = c["actual_broker"]
    lines = [
        "V59_INTEGRATED_BIDIRECTIONAL_RR_ANALYSIS=1",
        f"RUNS={len(result['runs'])}",
        f"SELECTED_LONG={e['selected_direction_counts'].get('LONG', 0)}",
        f"SELECTED_SHORT={e['selected_direction_counts'].get('SHORT', 0)}",
        f"FEASIBLE_LONG={e['feasible_direction_counts'].get('LONG', 0)}",
        f"FEASIBLE_SHORT={e['feasible_direction_counts'].get('SHORT', 0)}",
        f"REJECT_REASON_COUNTS={json.dumps(e['reject_reason_counts'], sort_keys=True)}",
        fmt_stats("RR_2_0", c["rr_2_0"]),
        fmt_stats("RR_2_5", c["rr_2_5"]),
        fmt_stats("RR_3_0", c["rr_3_0"]),
        f"ACTUAL_ENTRY_DEALS={a['entry_deals']}",
        f"ACTUAL_EXIT_DEALS={a['exit_deals']}",
        f"ACTUAL_LONG_ENTRIES={a['entry_direction_counts'].get('LONG', 0)}",
        f"ACTUAL_SHORT_ENTRIES={a['entry_direction_counts'].get('SHORT', 0)}",
        f"ACTUAL_SL_EXITS={a['sl_exit_deals']}",
        f"ACTUAL_TP_EXITS={a['tp_exit_deals']}",
        f"ACTUAL_BROKER_NET_USD={a['net_usd']:.4f}",
        f"ACTUAL_BROKER_MAX_REALIZED_DD_PCT={a['max_realized_dd_pct_proxy']:.2f}",
    ]
    for run in result["runs"]:
        ev = run["evaluation"]
        lines.append(
            f"RUN={run['run']} LONG={ev['selected_direction_counts'].get('LONG',0)} "
            f"SHORT={ev['selected_direction_counts'].get('SHORT',0)} "
            f"FEASIBLE_LONG={ev['feasible_direction_counts'].get('LONG',0)} "
            f"FEASIBLE_SHORT={ev['feasible_direction_counts'].get('SHORT',0)}"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", action="append", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--summary", required=True, type=Path)
    args = ap.parse_args()
    result = combine(args.run_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    summary = make_summary(result)
    args.summary.write_text(summary, encoding="utf-8")
    print(summary, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
