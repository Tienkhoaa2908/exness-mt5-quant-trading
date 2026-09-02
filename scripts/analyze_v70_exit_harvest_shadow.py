#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
TRADE_ANALYZER = REPO / "scripts" / "analyze_v69_forward_trade_quality.py"
POLICIES = (
    "BASELINE_200_100",
    "EARLY_100_025",
    "MID_150_050",
    "TIERED_100_025_200_100",
)


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


trade_quality = load(TRADE_ANALYZER, "v69_trade_quality_for_v70_exit_shadow")


def event_num(row: dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def parse_shadow_blocks(events: list[dict[str, str]]) -> list[dict]:
    blocks: list[dict] = []
    current: dict | None = None
    for row in events:
        event = (row.get("event") or "").strip()
        if event == "V70_EXIT_SHADOW_START":
            if current is not None:
                raise RuntimeError("V70 overlapping exit shadow starts")
            current = {
                "start_time": row.get("time", ""),
                "start_time_dt": trade_quality.parse_time(row.get("time")),
                "entry_price": event_num(row, "v1"),
                "triggers": {},
                "arms": {},
                "upgrades": {},
            }
            continue
        if current is None:
            continue
        if event == "V70_EXIT_POLICY_ARM":
            name = (row.get("detail") or "").strip()
            if name in POLICIES and name not in current["arms"]:
                current["arms"][name] = {
                    "time": row.get("time", ""),
                    "pnl": event_num(row, "v1"),
                    "floor": event_num(row, "v2"),
                }
        elif event == "V70_EXIT_POLICY_UPGRADE":
            name = (row.get("detail") or "").strip()
            if name in POLICIES and name not in current["upgrades"]:
                current["upgrades"][name] = {
                    "time": row.get("time", ""),
                    "pnl": event_num(row, "v1"),
                    "floor": event_num(row, "v2"),
                }
        elif event == "V70_EXIT_POLICY_TRIGGER":
            name = (row.get("detail") or "").strip()
            if name in POLICIES and name not in current["triggers"]:
                current["triggers"][name] = {
                    "time": row.get("time", ""),
                    "pnl": event_num(row, "v1"),
                    "floor": event_num(row, "v2"),
                    "max_pnl_at_trigger": event_num(row, "v3"),
                }
        elif event == "V70_EXIT_SHADOW_END":
            current["end_time"] = row.get("time", "")
            current["end_time_dt"] = trade_quality.parse_time(row.get("time"))
            current["true_mfe_usd"] = event_num(row, "v1")
            current["true_mae_usd"] = event_num(row, "v2")
            current["shadow_duration_seconds"] = event_num(row, "v3")
            blocks.append(current)
            current = None
    if current is not None:
        raise RuntimeError("V70 unterminated exit shadow block")
    return blocks


def match_blocks(trades: list[dict], blocks: list[dict], max_start_delta_seconds: float = 15.0) -> list[dict]:
    if len(trades) != len(blocks):
        raise RuntimeError(f"V70 trade/shadow count mismatch trades={len(trades)} shadows={len(blocks)}")
    out = []
    for idx, (trade, block) in enumerate(zip(trades, blocks), 1):
        entry_dt = trade.get("entry_time_dt") or trade_quality.parse_time(trade.get("entry_time"))
        start_dt = block.get("start_time_dt")
        if entry_dt is None or start_dt is None:
            raise RuntimeError(f"V70 missing trade/shadow time index={idx}")
        delta = abs((start_dt - entry_dt).total_seconds())
        if delta > max_start_delta_seconds:
            raise RuntimeError(f"V70 trade/shadow start mismatch index={idx} delta_s={delta}")
        row = dict(trade)
        row["true_mfe_usd"] = float(block["true_mfe_usd"])
        row["true_mae_usd"] = float(block["true_mae_usd"])
        row["shadow_start_delta_seconds"] = delta
        row["shadow_duration_seconds"] = float(block["shadow_duration_seconds"])
        row["policy_arms"] = block["arms"]
        row["policy_upgrades"] = block["upgrades"]
        row["policy_triggers"] = block["triggers"]
        cost = float(row.get("explicit_cost_usd") or 0.0)
        actual = float(row.get("realized_pnl_usd") or 0.0)
        policy_net: dict[str, float] = {}
        for name in POLICIES:
            trigger = block["triggers"].get(name)
            policy_net[name] = float(trigger["pnl"]) + cost if trigger else actual
        row["policy_net_usd"] = policy_net
        out.append(row)
    return out


def finite_median(values: list[float]) -> float | None:
    vals = [float(x) for x in values if isinstance(x, (int, float)) and math.isfinite(float(x))]
    return statistics.median(vals) if vals else None


def summary_for(values: list[float]) -> dict:
    s = trade_quality.summarize_pnl(values)
    return {
        "trades": s["trades"],
        "wins": s["wins"],
        "losses": s["losses"],
        "net_usd": round(s["net_usd"], 8),
        "profit_factor": round(s["profit_factor"], 6),
        "max_realized_dd_usd": round(s["max_realized_dd_usd"], 8),
        "avg_win_usd": round(s["avg_win_usd"], 8),
        "avg_loss_usd": round(s["avg_loss_usd"], 8),
    }


def analyze_run(run_dir: Path) -> list[dict]:
    deals = trade_quality.read_csv(run_dir / "V64_DEALS.csv")
    events = trade_quality.read_csv(run_dir / "V64_EVENTS.csv")
    trades = trade_quality.parse_deals(deals)
    blocks = parse_shadow_blocks(events)
    return match_blocks(trades, blocks)


def analyze(run_dirs: list[Path]) -> dict:
    all_trades: list[dict] = []
    by_run: dict[str, dict] = {}
    for run_dir in run_dirs:
        trades = analyze_run(run_dir)
        for row in trades:
            row["run_dir"] = run_dir.name
        all_trades.extend(trades)
        by_run[run_dir.name] = {
            "actual": summary_for([float(t["realized_pnl_usd"]) for t in trades]),
            "policies": {
                name: summary_for([float(t["policy_net_usd"][name]) for t in trades])
                for name in POLICIES
            },
        }

    all_trades.sort(key=lambda r: trade_quality.parse_time(r.get("entry_time")) or trade_quality.datetime.min)
    for idx, row in enumerate(all_trades, 1):
        row["global_trade_index"] = idx

    actual_values = [float(t["realized_pnl_usd"]) for t in all_trades]
    actual = summary_for(actual_values)
    policies = {}
    for name in POLICIES:
        vals = [float(t["policy_net_usd"][name]) for t in all_trades]
        s = summary_for(vals)
        s["net_delta_vs_actual_usd"] = round(s["net_usd"] - actual["net_usd"], 8)
        s["changed_trade_count"] = sum(
            1 for t in all_trades if name in t.get("policy_triggers", {})
        )
        s["baseline_winner_cut_count"] = sum(
            1
            for t in all_trades
            if float(t["realized_pnl_usd"]) > 1e-9
            and float(t["policy_net_usd"][name]) + 1e-9 < float(t["realized_pnl_usd"])
        )
        s["baseline_loss_improved_count"] = sum(
            1
            for t in all_trades
            if float(t["realized_pnl_usd"]) < -1e-9
            and float(t["policy_net_usd"][name]) > float(t["realized_pnl_usd"]) + 1e-9
        )
        policies[name] = s

    true_mfe = [float(t["true_mfe_usd"]) for t in all_trades]
    true_mae = [float(t["true_mae_usd"]) for t in all_trades]
    winners = [t for t in all_trades if float(t["realized_pnl_usd"]) > 1e-9]
    losses = [t for t in all_trades if float(t["realized_pnl_usd"]) < -1e-9]
    excursion = {
        "trades": len(all_trades),
        "median_true_mfe_all_usd": finite_median(true_mfe),
        "median_true_mfe_winners_usd": finite_median([float(t["true_mfe_usd"]) for t in winners]),
        "median_true_mfe_losers_usd": finite_median([float(t["true_mfe_usd"]) for t in losses]),
        "median_true_mae_losers_usd": finite_median([float(t["true_mae_usd"]) for t in losses]),
        "positive_true_mfe_realized_loss_count": sum(
            1 for t in losses if float(t["true_mfe_usd"]) > 1e-9
        ),
        "true_mfe_ge_1_count": sum(1 for t in all_trades if float(t["true_mfe_usd"]) >= 1.0 - 1e-9),
        "true_mfe_ge_2_count": sum(1 for t in all_trades if float(t["true_mfe_usd"]) >= 2.0 - 1e-9),
        "true_mfe_ge_2_realized_loss_count": sum(
            1 for t in losses if float(t["true_mfe_usd"]) >= 2.0 - 1e-9
        ),
    }

    return {
        "protocol": "v70_exit_harvest_shadow_v1",
        "development_only_not_independent": True,
        "actual": actual,
        "true_in_position_excursion": excursion,
        "policies": policies,
        "by_run": by_run,
        "trades": all_trades,
        "policy_notes": {
            "BASELINE_200_100": "idealized cash-floor shadow of inherited +2 arm / +1 floor",
            "EARLY_100_025": "research-only +1 arm / +0.25 floor",
            "MID_150_050": "research-only +1.5 arm / +0.5 floor",
            "TIERED_100_025_200_100": "research-only +1/+0.25 early floor upgraded to +1 after +2",
            "counterfactual_cost_model": "trigger OrderCalcProfit plus actual explicit deal costs for same 0.01 cohort",
            "entry_semantics_changed": False,
            "real_exit_semantics_changed": False,
            "orders_added": 0,
            "real_money_authorized": False,
            "short_enabled": False,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", action="append", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    args = ap.parse_args()

    result = analyze(args.run_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    lines = [
        "V70_EXIT_HARVEST_SHADOW=PASS",
        f"TRADES={result['actual']['trades']}",
        f"ACTUAL_NET_USD={result['actual']['net_usd']}",
        f"ACTUAL_PF={result['actual']['profit_factor']}",
        f"TRUE_EXCURSION={json.dumps(result['true_in_position_excursion'], sort_keys=True)}",
    ]
    for name in POLICIES:
        lines.append(f"POLICY_{name}={json.dumps(result['policies'][name], sort_keys=True)}")
    lines += [
        "DEVELOPMENT_ONLY=1",
        "ENTRY_SEMANTICS_CHANGED=0",
        "REAL_EXIT_SEMANTICS_CHANGED=0",
        "SHORT_ENABLED=0",
        "REAL_MONEY_AUTHORIZED=0",
    ]
    args.summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"V70_RESULT_JSON={args.output}")
    print(f"V70_SUMMARY={args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
