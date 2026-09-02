#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

EXPECTED_BRANCH = "agent/v69-one-shot-prospective-demo"
EXPECTED_IDENTITY = {"trades": 24, "wins": 10, "losses": 14, "net_usd": 7.14}

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V69_MFE_GIVEBACK_RECOVERY"
ANALYZER = REPO / "scripts" / "analyze_v69_mfe_giveback_recovery.py"
DOWNSTREAM_RUNNER = (
    REPO / "runtime" / "v69_downstream_funnel_recovery" / "RUN_V69_DOWNSTREAM_FUNNEL_RECOVERY.py"
)


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def capture(cmd, *, cwd=None) -> str:
    return subprocess.check_output(
        [str(x) for x in cmd], cwd=cwd, text=True, encoding="utf-8", errors="replace"
    ).strip()


def ensure_repo() -> tuple[str, str]:
    expected = os.environ.get("V69_MFE_GIVEBACK_EXPECTED_HEAD", "").strip()
    if not expected:
        raise RuntimeError("V69_MFE_GIVEBACK_EXPECTED_HEAD is required")
    origin = capture(["git", "remote", "get-url", "origin"], cwd=REPO)
    branch = capture(["git", "branch", "--show-current"], cwd=REPO)
    head = capture(["git", "rev-parse", "HEAD"], cwd=REPO)
    dirty = capture(["git", "status", "--porcelain"], cwd=REPO)
    print(f"ORIGIN={origin}")
    print(f"BRANCH={branch}")
    print(f"HEAD={head}")
    print(f"EXPECTED_HEAD={expected}")
    if "Tienkhoaa2908/exness-mt5-quant-trading" not in origin:
        raise RuntimeError("wrong repository")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")
    if head != expected:
        raise RuntimeError(f"wrong HEAD expected={expected} actual={head}")
    if dirty:
        raise RuntimeError("working tree must be clean; do not git clean or stash pop")
    return branch, head


def assert_accepted_identity(result: dict) -> None:
    summary = result.get("summary", {})
    mismatches = []
    for key in ("trades", "wins", "losses"):
        actual = int(summary.get(key, -1))
        if actual != EXPECTED_IDENTITY[key]:
            mismatches.append(f"{key}:expected={EXPECTED_IDENTITY[key]} actual={actual}")
    try:
        net = float(summary.get("net_usd"))
    except (TypeError, ValueError):
        net = float("nan")
    if not (abs(net - EXPECTED_IDENTITY["net_usd"]) <= 0.02):
        mismatches.append(f"net_usd:expected=7.14 actual={summary.get('net_usd')}")
    if mismatches:
        raise RuntimeError("V69 MFE/giveback accepted identity mismatch: " + "; ".join(mismatches))
    print("V69_MFE_GIVEBACK_ACCEPTED_DEVELOPMENT_IDENTITY=PASS")


def compact_trades(result: dict) -> list[dict]:
    rows = []
    for trade in result.get("trades", []):
        rows.append(
            {
                "i": trade.get("global_trade_index"),
                "month": trade.get("month"),
                "archetype": trade.get("archetype"),
                "entry": trade.get("entry_time"),
                "exit": trade.get("exit_time"),
                "duration_s": trade.get("duration_seconds"),
                "realized": trade.get("realized_pnl_usd"),
                "mfe": trade.get("mfe_usd"),
                "mae": trade.get("mae_usd"),
                "giveback": trade.get("giveback_usd"),
                "capture": trade.get("capture_ratio_of_mfe"),
                "profit_lock_events": trade.get("profit_lock_event_count"),
                "profit_lock_modified": trade.get("profit_lock_modified_count"),
                "profit_lock_failed": trade.get("profit_lock_modify_failed_count"),
            }
        )
    return rows


def main() -> int:
    branch, head = ensure_repo()
    analyzer = load(ANALYZER, "v69_mfe_giveback_recovery")
    downstream = load(DOWNSTREAM_RUNNER, "v69_downstream_source_for_mfe_giveback")
    v69_root, source_kind = downstream.discover_v69_root()
    print(f"V69_MFE_GIVEBACK_V69_SOURCE_KIND={source_kind}")
    print(f"V69_MFE_GIVEBACK_V69_ROOT={v69_root}")

    result = analyzer.analyze(v69_root)
    assert_accepted_identity(result)
    result["branch"] = branch
    result["head"] = head
    result["v69_source_kind"] = source_kind
    result["v69_root"] = str(v69_root)

    OUT.mkdir(parents=True, exist_ok=True)
    output = OUT / "V69_MFE_GIVEBACK_RECOVERY.json"
    summary_path = OUT / "V69_MFE_GIVEBACK_SUMMARY.txt"
    analyzer.write_outputs(result, output, summary_path)

    s = result["summary"]
    print(f"V69_MFE_GIVEBACK_NOISE_MATCHED_TRADES={s['noise_matched_trades']}")
    print(f"V69_MFE_GIVEBACK_NOISE_MATCH_RATE={s['noise_match_rate']}")
    print(f"V69_MFE_GIVEBACK_MEDIAN_MFE_ALL_USD={s['median_mfe_all_usd']}")
    print(f"V69_MFE_GIVEBACK_MEDIAN_MFE_WINNERS_USD={s['median_mfe_winners_usd']}")
    print(f"V69_MFE_GIVEBACK_MEDIAN_MFE_LOSERS_USD={s['median_mfe_losers_usd']}")
    print(f"V69_MFE_GIVEBACK_MEDIAN_MAE_LOSERS_USD={s['median_mae_losers_usd']}")
    print(f"V69_MFE_GIVEBACK_MEDIAN_GIVEBACK_USD={s['median_giveback_usd']}")
    print(
        "V69_MFE_GIVEBACK_MEDIAN_WINNER_CAPTURE_RATIO="
        f"{s['median_winner_capture_ratio_of_mfe']}"
    )
    print(
        "V69_MFE_GIVEBACK_POSITIVE_MFE_REALIZED_LOSS_COUNT="
        f"{s['positive_mfe_realized_loss_count']}"
    )
    print(
        "V69_MFE_GIVEBACK_SUB2_PEAK_ROUNDTRIP_LOSS_COUNT="
        f"{s['sub2_peak_roundtrip_loss_count']}"
    )
    print(
        "V69_MFE_GIVEBACK_RATCHET_ELIGIBLE_MFE_GE_2_COUNT="
        f"{s['ratchet_eligible_mfe_ge_2_count']}"
    )
    print(
        "V69_MFE_GIVEBACK_MFE_GE_2_REALIZED_BELOW_1_COUNT="
        f"{s['mfe_ge_2_realized_below_1_count']}"
    )
    print(
        "V69_MFE_GIVEBACK_MFE_GE_2_BELOW_1_WITH_LOCK_EVENT="
        f"{s['mfe_ge_2_realized_below_1_with_profit_lock_event']}"
    )
    print(
        "V69_MFE_GIVEBACK_MFE_GE_2_BELOW_1_WITHOUT_LOCK_EVENT="
        f"{s['mfe_ge_2_realized_below_1_without_profit_lock_event']}"
    )
    print(f"V69_MFE_GIVEBACK_PROFIT_LOCK_EVENT_TRADES={s['profit_lock_event_trades']}")
    print(f"V69_MFE_GIVEBACK_PROFIT_LOCK_MODIFIED_TRADES={s['profit_lock_modified_trades']}")
    print(f"V69_MFE_GIVEBACK_PROFIT_LOCK_FAILED_TRADES={s['profit_lock_modify_failed_trades']}")
    print(
        "V69_MFE_GIVEBACK_THRESHOLD_DIAGNOSTICS="
        + json.dumps(s["mfe_threshold_diagnostics"], sort_keys=True)
    )
    print("V69_MFE_GIVEBACK_BY_ARCHETYPE=" + json.dumps(result["by_archetype"], sort_keys=True))
    print("V69_MFE_GIVEBACK_BY_MONTH=" + json.dumps(result["by_month"], sort_keys=True))
    print("V69_MFE_GIVEBACK_DIAGNOSIS=" + json.dumps(result["diagnosis"], sort_keys=True))
    print("V69_MFE_GIVEBACK_TRADE_ROWS=" + json.dumps(compact_trades(result), sort_keys=True))
    print(f"V69_MFE_GIVEBACK_RESULT_JSON={output}")
    print(f"V69_MFE_GIVEBACK_SUMMARY={summary_path}")
    print("V69_MFE_GIVEBACK_DEVELOPMENT_ONLY=1")
    print("V69_MFE_GIVEBACK_INDEPENDENT_EDGE_EVIDENCE=0")
    print("V69_MFE_GIVEBACK_TRAILING_COUNTERFACTUAL_SIMULATED=0")
    print("V69_MFE_GIVEBACK_MT5_CAN_REMAIN_RUNNING=1")
    print("V69_MFE_GIVEBACK_METAEDITOR_REQUIRED=0")
    print("V69_MFE_GIVEBACK_ORDERS_SENT=0")
    print("V69_MFE_GIVEBACK_STRATEGY_CHANGED=0")
    print("REAL_MONEY_AUTHORIZED=0")
    print("V69_MFE_GIVEBACK_RECOVERY=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
