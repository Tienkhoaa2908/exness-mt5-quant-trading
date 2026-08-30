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
    gp, gl = sum(wins), -sum(losses)
    by_dir = {}
    for d in (1, -1):
        subset = [r for r in rows if i(r, "direction") == d]
        sv = [f(r, col) for r in subset]
        sw = [x for x in sv if x > 1e-9]
        sl = [x for x in sv if x < -1e-9]
        by_dir[side(d)] = {
            "trades": len(sv), "wins": len(sw), "losses": len(sl),
            "win_rate": (len(sw) / len(sv) if sv else 0.0), "net_usd": sum(sv),
        }
    return {
        "trades": len(vals), "wins": len(wins), "losses": len(losses),
        "win_rate": (len(wins) / len(vals) if vals else 0.0),
        "gross_profit_usd": gp, "gross_loss_usd": gl, "net_usd": sum(vals),
        "profit_factor": (gp / gl if gl > 0 else (999.0 if gp > 0 else 0.0)),
        "avg_win_usd": (gp / len(wins) if wins else 0.0),
        "avg_loss_usd": (sum(losses) / len(losses) if losses else 0.0),
        "max_single_loss_usd": (min(losses) if losses else 0.0),
        "losses_over_1_usd": sum(1 for x in losses if x < -1.0 - 1e-9),
        "losses_over_1p25_usd": sum(1 for x in losses if x < -1.25 - 1e-9),
        "by_direction": by_dir,
    }


def actual_summary(deals: list[dict[str, str]], events: list[dict[str, str]]) -> dict:
    all_net, exits = [], []
    for r in deals:
        net = f(r, "profit") + f(r, "commission") + f(r, "swap") + f(r, "fee")
        all_net.append(net)
        if i(r, "entry") != 0:
            exits.append((r, net))
    wins = [x for _, x in exits if x > 1e-9]
    losses = [x for _, x in exits if x < -1e-9]
    gp, gl = sum(wins), -sum(losses)
    running = peak = max_dd = 0.0
    for x in all_net:
        running += x
        peak = max(peak, running)
        max_dd = max(max_dd, peak - running)
    reasons = Counter(str(i(r, "reason")) for r, _ in exits)
    locks = [r for r in events if (r.get("event") or "") == "PROFIT_LOCK"]
    preflight = [r for r in events if (r.get("event") or "") == "ORDER_PREFLIGHT"]
    return {
        "round_trips": len(exits),
        "entry_deals": sum(1 for r in deals if i(r, "entry") == 0),
        "exit_deals": len(exits), "wins": len(wins), "losses": len(losses),
        "win_rate": (len(wins) / len(exits) if exits else 0.0),
        "gross_profit_usd": gp, "gross_loss_usd": gl, "net_usd": sum(all_net),
        "profit_factor": (gp / gl if gl > 0 else (999.0 if gp > 0 else 0.0)),
        "avg_win_usd": (gp / len(wins) if wins else 0.0),
        "avg_loss_usd": (sum(losses) / len(losses) if losses else 0.0),
        "max_single_loss_usd": (min(losses) if losses else 0.0),
        "losses_over_1_usd": sum(1 for x in losses if x < -1.0 - 1e-9),
        "losses_over_1p25_usd": sum(1 for x in losses if x < -1.25 - 1e-9),
        "max_realized_dd_usd": max_dd,
        "exit_reason_codes": dict(reasons),
        "profit_lock_modified": sum(1 for r in locks if (r.get("detail") or "") == "modified"),
        "profit_lock_failed": sum(1 for r in locks if (r.get("detail") or "") != "modified"),
        "order_preflight_blocks": len(preflight),
        "order_preflight_details": dict(Counter((r.get("detail") or "") for r in preflight)),
        "soft_loss_cut_exits": sum(1 for r in events if (r.get("event") or "") == "SOFT_LOSS_CUT" and (r.get("detail") or "") == "closed"),
    }


def analyze(run_dirs: list[Path]) -> dict:
    evals, shadows, deals, events = [], [], [], []
    for rd in run_dirs:
        evals.extend(read_csv(rd / "V61_ENTRY_EVAL.csv"))
        shadows.extend(read_csv(rd / "V61_SHADOW_RR.csv"))
        deals.extend(read_csv(rd / "V61_DEALS.csv"))
        events.extend(read_csv(rd / "V61_EVENTS.csv"))
    selected = [r for r in evals if i(r, "selected_direction") in (1, -1)]
    feasible = [r for r in selected if i(r, "feasible") == 1]
    rejects = Counter((r.get("reject_reason") or "") for r in selected if i(r, "feasible") != 1)
    dirs = Counter(side(i(r, "selected_direction")) for r in feasible)
    sources = Counter((r.get("stop_source") or "unknown") for r in feasible)
    risk = [f(r, "risk_cash") for r in feasible if f(r, "risk_cash") > 0]
    spread = [f(r, "spread_cash") for r in feasible if f(r, "spread_cash") >= 0]
    return {
        "selected_setups": len(selected), "feasible_setups": len(feasible),
        "feasible_by_direction": dict(dirs), "stop_source_counts": dict(sources),
        "reject_reason_counts": dict(rejects),
        "risk_cash": {"min": min(risk) if risk else 0.0, "avg": sum(risk)/len(risk) if risk else 0.0, "max": max(risk) if risk else 0.0},
        "spread_cash": {"min": min(spread) if spread else 0.0, "avg": sum(spread)/len(spread) if spread else 0.0, "max": max(spread) if spread else 0.0},
        "shadow_cash_2": cash_summary(shadows, "result_cash_2"),
        "shadow_cash_3": cash_summary(shadows, "result_cash_3"),
        "shadow_cash_4": cash_summary(shadows, "result_cash_4"),
        "actual_broker": actual_summary(deals, events), "shadow_trade_count": len(shadows),
    }


def write_summary(r: dict, path: Path) -> None:
    lines = [
        "V61_PROFIT_RATCHET_M5_REFINEMENT_ANALYSIS=1",
        f"SELECTED_SETUPS={r['selected_setups']}", f"FEASIBLE_SETUPS={r['feasible_setups']}",
        "FEASIBLE_BY_DIRECTION=" + json.dumps(r["feasible_by_direction"], sort_keys=True),
        "STOP_SOURCE_COUNTS=" + json.dumps(r["stop_source_counts"], sort_keys=True),
        "REJECT_REASON_COUNTS=" + json.dumps(r["reject_reason_counts"], sort_keys=True),
        "RISK_CASH=" + json.dumps(r["risk_cash"], sort_keys=True),
        "SPREAD_CASH=" + json.dumps(r["spread_cash"], sort_keys=True),
    ]
    for label, key in (("TP_$2","shadow_cash_2"),("TP_$3","shadow_cash_3"),("TP_$4","shadow_cash_4")):
        s=r[key]
        lines.append(f"{label} trades={s['trades']} wins={s['wins']} losses={s['losses']} win_rate={s['win_rate']:.4f} net_usd={s['net_usd']:.4f} pf={s['profit_factor']:.4f} avg_win_usd={s['avg_win_usd']:.4f} avg_loss_usd={s['avg_loss_usd']:.4f} max_single_loss_usd={s['max_single_loss_usd']:.4f}")
        lines.append(label+"_BY_DIRECTION="+json.dumps(s["by_direction"], sort_keys=True))
    a=r["actual_broker"]
    lines += [
        f"ACTUAL_ROUND_TRIPS={a['round_trips']}", f"ACTUAL_WINS={a['wins']}", f"ACTUAL_LOSSES={a['losses']}",
        f"ACTUAL_WIN_RATE={a['win_rate']:.4f}", f"ACTUAL_NET_USD={a['net_usd']:.4f}", f"ACTUAL_PF={a['profit_factor']:.4f}",
        f"ACTUAL_AVG_WIN_USD={a['avg_win_usd']:.4f}", f"ACTUAL_AVG_LOSS_USD={a['avg_loss_usd']:.4f}",
        f"ACTUAL_MAX_SINGLE_LOSS_USD={a['max_single_loss_usd']:.4f}", f"ACTUAL_MAX_REALIZED_DD_USD={a['max_realized_dd_usd']:.4f}",
        f"ACTUAL_PROFIT_LOCK_MODIFIED={a['profit_lock_modified']}", f"ACTUAL_PROFIT_LOCK_FAILED={a['profit_lock_failed']}",
        f"ACTUAL_ORDER_PREFLIGHT_BLOCKS={a['order_preflight_blocks']}", "ACTUAL_ORDER_PREFLIGHT_DETAILS="+json.dumps(a['order_preflight_details'], sort_keys=True),
        f"ACTUAL_SOFT_LOSS_CUT_EXITS={a['soft_loss_cut_exits']}", "ACTUAL_EXIT_REASON_CODES="+json.dumps(a['exit_reason_codes'], sort_keys=True),
    ]
    path.write_text("\n".join(lines)+"\n", encoding="utf-8")


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-dir", action="append", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--summary", required=True, type=Path)
    args=ap.parse_args()
    result=analyze(args.run_dir)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    write_summary(result,args.summary)
    print(args.summary.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
