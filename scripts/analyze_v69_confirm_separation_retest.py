#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "analyze_v68_v67_holdout_stability.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


base = load(PARENT, "v68_analyzer_for_v69")
EXTRA_STAGE_EVENTS = (
    "POST_CONFIRM_SEPARATION",
    "POST_CONFIRM_RETEST_READY",
    "POST_CONFIRM_ENTRY_READY",
)
base.STAGE_EVENTS = tuple(base.STAGE_EVENTS) + EXTRA_STAGE_EVENTS


def postprocess_run(run: dict, run_dir: Path) -> dict:
    events = base.read_csv(run_dir / "V64_EVENTS.csv")
    ready = [r for r in events if (r.get("event") or "") == "POST_CONFIRM_ENTRY_READY"]
    sep = [r for r in events if (r.get("event") or "") == "POST_CONFIRM_SEPARATION"]
    ages = [base.num(r, "value2") for r in ready]
    max_sep = [base.num(r, "value3") for r in ready]
    run["v69_confirmation_retest"] = {
        "separations": len(sep),
        "entry_ready": len(ready),
        "entry_confirm_age_seconds_median": statistics.median(ages) if ages else 0.0,
        "entry_confirm_age_seconds_min": min(ages) if ages else 0.0,
        "entry_confirm_age_seconds_max": max(ages) if ages else 0.0,
        "entry_max_separation_risk_median": statistics.median(max_sep) if max_sep else 0.0,
    }
    return run


def analyze(run_dirs: list[Path]) -> dict:
    runs = [postprocess_run(base.analyze_run(p), p) for p in run_dirs]
    long_runs = [r for r in runs if r["direction"] == "LONG"]
    short_runs = [r for r in runs if r["direction"] == "SHORT"]
    out = {
        "protocol": "v69_confirm_separation_retest_v68_calendar_replay_model4",
        "runs": runs,
        "lanes": {
            "LONG": base.lane_summary(long_runs),
            "SHORT": base.lane_summary(short_runs),
        },
        "interpretation": {
            "v68_is_development_evidence_for_v69": True,
            "this_is_not_an_independent_holdout": True,
            "fixed_trade_count_quota": False,
            "fixed_weekly_profit_quota": False,
            "lanes_evaluated_independently": True,
            "primary_objective": "reduce_false_post_reclaim_entries_without_widening_structural_loss",
        },
    }
    for lane_name in ("LONG", "SHORT"):
        lane_runs = [r for r in runs if r["direction"] == lane_name]
        ages = []
        for r in lane_runs:
            events = base.read_csv(Path(r["_run_path"])) if False else []
        blocks = [r["v69_confirmation_retest"] for r in lane_runs]
        out["lanes"][lane_name]["v69_confirmation_retest"] = {
            "separations": sum(b["separations"] for b in blocks),
            "entry_ready": sum(b["entry_ready"] for b in blocks),
            "months_with_entries": sum(1 for r in lane_runs if r["actual"]["trades"] > 0),
        }
    return out


def fmt_lane(name: str, lane: dict) -> str:
    a = lane["actual"]
    v = lane["v69_confirmation_retest"]
    return (
        f"LANE={name} trades={a['trades']} wins={a['wins']} losses={a['losses']} "
        f"win_rate={a['win_rate']:.4f} net_usd={a['net_usd']:.4f} pf={a['profit_factor']:.4f} "
        f"avg_win_usd={a['avg_win_usd']:.4f} avg_loss_usd={a['avg_loss_usd']:.4f} "
        f"max_single_loss_usd={a['max_single_loss_usd']:.4f} max_realized_dd_usd={a['max_realized_dd_usd']:.4f} "
        f"positive_months={lane['positive_months']} negative_months={lane['negative_months']} flat_months={lane['flat_months']} "
        f"worst_month_usd={lane['worst_month_usd']:.4f} median_month_usd={lane['median_month_usd']:.4f} "
        f"losses_le_15s={a['losses_le_15s']} losses_le_30s={a['losses_le_30s']} losses_le_60s={a['losses_le_60s']} "
        f"separations={v['separations']} post_confirm_entries={v['entry_ready']} active_entry_months={v['months_with_entries']}"
    )


def write_summary(result: dict, path: Path) -> None:
    lines = [
        "V69_CONFIRM_SEPARATION_RETEST_ANALYSIS=1",
        "V68_REPLAY_IS_INDEPENDENT_HOLDOUT=0",
        "REPLAY_PERIOD=2025.09.01_to_2026.06.01",
        "MODEL4_PASSES=18",
        "MIN_CONFIRM_SEPARATION_RISK_CASH=1.30",
        "MIN_CONFIRM_AGE_SECONDS=30",
        "STRUCTURAL_STOP_WIDENED=0",
        "FIXED_TRADE_COUNT_PROMOTION_QUOTA=0",
        "FIXED_WEEKLY_PROFIT_PROMOTION_QUOTA=0",
    ]
    for lane_name in ("LONG", "SHORT"):
        lane = result["lanes"][lane_name]
        lines.append(fmt_lane(lane_name, lane))
        lines.append(f"LANE={lane_name} MONTH_NET=" + json.dumps(lane["month_net_usd"], sort_keys=True))
        lines.append(f"LANE={lane_name} STAGE=" + json.dumps(lane["stage_events"], sort_keys=True))
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
    print("V69_ANALYZER_PASS=1")
    print(f"V69_ANALYSIS={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
