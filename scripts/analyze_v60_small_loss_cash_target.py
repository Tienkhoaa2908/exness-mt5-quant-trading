#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


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


def side(d: int) -> str:
    return "LONG" if d > 0 else "SHORT" if d < 0 else "FLAT"


def cash_summary(rows: list[dict[str, str]], col: str) -> dict:
    vals = [f(r, col) for r in rows]
    wins = [x for x in vals if x > 1e-9]
    losses = [x for x in vals if x < -1e-9]
    gp = sum(wins)
    gl = -sum(losses)
    net = sum(vals)
    by_dir = {}
    for d in (1, -1):
        subset = [r for r in rows if i(r, "direction") == d]
        sv = [f(r, col) for r in subset]
        sw = [x for x in sv if x > 1e-9]
        sl = [x for x in sv if x < -1e-9]
        by_dir[side(d)] = {
            "trades": len(sv),
            "wins": len(sw),
            "losses": len(sl),
            "win_rate": (len(sw) / len(sv) if sv else 0.0),
            "net_usd": sum(sv),
        }
    return {
        "trades": len(vals),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": (len(wins) / len(vals) if vals else 0.0),
        "gross_profit_usd": gp,
        "gross_loss_usd": gl,
        "net_usd": net,
        "profit_factor": (gp / gl if gl > 0 else (999.0 if gp > 0 else 0.0)),
        "avg_win_usd": (gp / len(wins) if wins else 0.0),
        "avg_loss_usd": (sum(losses) / len(losses) if losses else 0.0),
        "max_single_loss_usd": (min(losses) if losses else 0.0),
        "losses_over_1_usd": sum(1 for x in losses if x < -1.0 - 1e-9),
        "losses_over_1p25_usd": sum(1 for x in losses if x < -1.25 - 1e-9),
        "by_direction": by_dir,
    }


def actual_summary(deals: list[dict[str, str]], events: list[dict[str, str]]) -> dict:
    all_net = []
    exit_rows = []
    for r in deals:
        net = f(r, "profit") + f(r, "commission") + f(r, "swap") + f(r, "fee")
        all_net.append(net)
        # MQL5 DEAL_ENTRY_IN == 0. Everything else is a closing/round-trip completion leg.
        if i(r, "entry") != 0:
            exit_rows.append((r, net))

    wins = [x for _, x in exit_rows if x > 1e-9]
    losses = [x for _, x in exit_rows if x < -1e-9]
    gp = sum(wins)
    gl = -sum(losses)
    running = 0.0
    peak = 0.0
    max_dd = 0.0
    for x in all_net:
        running += x
        peak = max(peak, running)
        max_dd = max(max_dd, peak - running)

    reasons = Counter(str(i(r, "reason")) for r, _ in exit_rows)
    soft_cuts = sum(1 for r in events if (r.get("event") or "") == "SOFT_LOSS_CUT" and (r.get("detail") or "") == "closed")
    return {
        "round_trips": len(exit_rows),
        "entry_deals": sum(1 for r in deals if i(r, "entry") == 0),
        "exit_deals": len(exit_rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": (len(wins) / len(exit_rows) if exit_rows else 0.0),
        "gross_profit_usd": gp,
        "gross_loss_usd": gl,
        "net_usd": sum(all_net),
        "profit_factor": (gp / gl if gl > 0 else (999.0 if gp > 0 else 0.0)),
        "avg_win_usd": (gp / len(wins) if wins else 0.0),
        "avg_loss_usd": (sum(losses) / len(losses) if losses else 0.0),
        "max_single_loss_usd": (min(losses) if losses else 0.0),
        "losses_over_1_usd": sum(1 for x in losses if x < -1.0 - 1e-9),
        "losses_over_1p25_usd": sum(1 for x in losses if x < -1.25 - 1e-9),
        "max_realized_dd_usd": max_dd,
        "exit_reason_codes": dict(reasons),
        "soft_loss_cut_exits": soft_cuts,
    }


def analyze(run_dirs: list[Path]) -> dict:
    evals: list[dict[str, str]] = []
    shadows: list[dict[str, str]] = []
    deals: list[dict[str, str]] = []
    events: list[dict[str, str]] = []
    for rd in run_dirs:
        evals.extend(read_csv(rd / "V60_ENTRY_EVAL.csv"))
        shadows.extend(read_csv(rd / "V60_SHADOW_RR.csv"))
        deals.extend(read_csv(rd / "V60_DEALS.csv"))
        events.extend(read_csv(rd / "V60_EVENTS.csv"))

    selected = [r for r in evals if i(r, "selected_direction") in (1, -1)]
    feasible = [r for r in selected if i(r, "feasible") == 1]
    reject_counts = Counter((r.get("reject_reason") or "") for r in selected if i(r, "feasible") != 1)
    direction_counts = Counter(side(i(r, "selected_direction")) for r in feasible)
    risk = [f(r, "risk_cash") for r in feasible if f(r, "risk_cash") > 0]
    spread = [f(r, "spread_cash") for r in feasible if f(r, "spread_cash") >= 0]

    result = {
        "selected_setups": len(selected),
        "feasible_setups": len(feasible),
        "feasible_by_direction": dict(direction_counts),
        "reject_reason_counts": dict(reject_counts),
        "risk_cash": {
            "min": min(risk) if risk else 0.0,
            "avg": sum(risk) / len(risk) if risk else 0.0,
            "max": max(risk) if risk else 0.0,
        },
        "spread_cash": {
            "min": min(spread) if spread else 0.0,
            "avg": sum(spread) / len(spread) if spread else 0.0,
            "max": max(spread) if spread else 0.0,
        },
        "shadow_cash_2": cash_summary(shadows, "result_cash_2"),
        "shadow_cash_3": cash_summary(shadows, "result_cash_3"),
        "shadow_cash_4": cash_summary(shadows, "result_cash_4"),
        "actual_broker": actual_summary(deals, events),
        "shadow_trade_count": len(shadows),
    }
    return result


def write_summary(result: dict, path: Path) -> None:
    lines = [
        "V60_SMALL_LOSS_CASH_TARGET_ANALYSIS=1",
        f"SELECTED_SETUPS={result['selected_setups']}",
        f"FEASIBLE_SETUPS={result['feasible_setups']}",
        "FEASIBLE_BY_DIRECTION=" + json.dumps(result["feasible_by_direction"], sort_keys=True),
        "REJECT_REASON_COUNTS=" + json.dumps(result["reject_reason_counts"], sort_keys=True),
        "RISK_CASH=" + json.dumps(result["risk_cash"], sort_keys=True),
        "SPREAD_CASH=" + json.dumps(result["spread_cash"], sort_keys=True),
    ]
    for label, key in (("TP_$2", "shadow_cash_2"), ("TP_$3", "shadow_cash_3"), ("TP_$4", "shadow_cash_4")):
        s = result[key]
        lines.append(
            f"{label} trades={s['trades']} wins={s['wins']} losses={s['losses']} "
            f"win_rate={s['win_rate']:.4f} net_usd={s['net_usd']:.4f} pf={s['profit_factor']:.4f} "
            f"avg_win_usd={s['avg_win_usd']:.4f} avg_loss_usd={s['avg_loss_usd']:.4f} "
            f"max_single_loss_usd={s['max_single_loss_usd']:.4f} losses_over_$1={s['losses_over_1_usd']} "
            f"losses_over_$1.25={s['losses_over_1p25_usd']}"
        )
        lines.append(label + "_BY_DIRECTION=" + json.dumps(s["by_direction"], sort_keys=True))
    a = result["actual_broker"]
    lines += [
        f"ACTUAL_ROUND_TRIPS={a['round_trips']}",
        f"ACTUAL_ENTRY_DEALS={a['entry_deals']}",
        f"ACTUAL_EXIT_DEALS={a['exit_deals']}",
        f"ACTUAL_WINS={a['wins']}",
        f"ACTUAL_LOSSES={a['losses']}",
        f"ACTUAL_WIN_RATE={a['win_rate']:.4f}",
        f"ACTUAL_NET_USD={a['net_usd']:.4f}",
        f"ACTUAL_PF={a['profit_factor']:.4f}",
        f"ACTUAL_AVG_WIN_USD={a['avg_win_usd']:.4f}",
        f"ACTUAL_AVG_LOSS_USD={a['avg_loss_usd']:.4f}",
        f"ACTUAL_MAX_SINGLE_LOSS_USD={a['max_single_loss_usd']:.4f}",
        f"ACTUAL_LOSSES_OVER_$1={a['losses_over_1_usd']}",
        f"ACTUAL_LOSSES_OVER_$1.25={a['losses_over_1p25_usd']}",
        f"ACTUAL_MAX_REALIZED_DD_USD={a['max_realized_dd_usd']:.4f}",
        f"ACTUAL_SOFT_LOSS_CUT_EXITS={a['soft_loss_cut_exits']}",
        "ACTUAL_EXIT_REASON_CODES=" + json.dumps(a["exit_reason_codes"], sort_keys=True),
    ]
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
    print(args.summary.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
