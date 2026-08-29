#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

CANDIDATE = "v52_b4_or_b3_trend_bos"
BOOK = "usd40_r1p0_cent_continuous"
FIXED_LOT = 0.01
INITIAL_BALANCE = 40.0
WEEK_START = pd.Timestamp("2026-08-24 00:00:00")
WEEK_END = pd.Timestamp("2026-08-29 00:00:00")
GATES = {
    "baseline_fixed001": "gate_baseline",
    "trend_h1": "gate_trend",
    "trend_adx": "gate_trend_adx",
    "trend_structure": "gate_trend_structure",
    "trend_smc_balanced": "gate_balanced",
    "trend_smc_strict": "gate_strict",
}


def read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file() or path.stat().st_size <= 0:
        return pd.DataFrame()
    return pd.read_csv(path)


def to_dt(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s.astype(str).str.replace(".", "-", regex=False), errors="coerce")


def max_drawdown(balance_path: list[float]) -> float:
    peak = -math.inf
    max_dd = 0.0
    for x in balance_path:
        peak = max(peak, x)
        if peak > 0:
            max_dd = max(max_dd, 100.0 * (peak - x) / peak)
    return max_dd


def summarize_gate(trades: pd.DataFrame, evals: pd.DataFrame, gate_col: str) -> dict:
    merged = trades.merge(evals[["time", gate_col]], left_on="entry_time_dt", right_on="time", how="left")
    selected = merged[pd.to_numeric(merged[gate_col], errors="coerce").fillna(0).astype(int) == 1].copy()
    if selected.empty:
        return {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "net_pnl_usd_fixed001": 0.0,
            "ending_balance_proxy": INITIAL_BALANCE,
            "return_pct_proxy": 0.0,
            "profit_factor": None,
            "max_balance_dd_pct_proxy": 0.0,
            "balance_breach_proxy": False,
            "sum_r_original": 0.0,
        }

    vol = pd.to_numeric(selected["initial_volume_std_equiv"], errors="coerce")
    pnl = pd.to_numeric(selected["total_pnl"], errors="coerce")
    r = pd.to_numeric(selected["r_multiple"], errors="coerce")
    valid = vol.gt(0) & pnl.notna()
    selected = selected.loc[valid].copy()
    selected["fixed001_pnl"] = pnl.loc[valid] * (FIXED_LOT / vol.loc[valid])
    selected["r_multiple_num"] = r.loc[valid]

    p = selected["fixed001_pnl"]
    gp = float(p[p > 0].sum())
    gl = float(p[p < 0].sum())
    pf = None if gl == 0 else gp / abs(gl)
    balances = [INITIAL_BALANCE]
    b = INITIAL_BALANCE
    breach = False
    for x in p:
        b += float(x)
        balances.append(b)
        if b <= 0:
            breach = True

    return {
        "trades": int(len(selected)),
        "wins": int((p > 0).sum()),
        "losses": int((p < 0).sum()),
        "net_pnl_usd_fixed001": round(float(p.sum()), 6),
        "gross_profit_usd": round(gp, 6),
        "gross_loss_usd": round(gl, 6),
        "ending_balance_proxy": round(b, 6),
        "return_pct_proxy": round(100.0 * (b - INITIAL_BALANCE) / INITIAL_BALANCE, 4),
        "profit_factor": None if pf is None else round(float(pf), 6),
        "max_balance_dd_pct_proxy": round(max_drawdown(balances), 4),
        "balance_breach_proxy": breach,
        "sum_r_original": round(float(selected["r_multiple_num"].sum()), 6),
        "entry_times": [str(x) for x in selected["entry_time"].tolist()],
    }


def broker_pnl(transactions: pd.DataFrame) -> dict:
    if transactions.empty:
        return {"deals": 0, "round_trip_exit_deals": 0, "net_pnl_usd": 0.0, "gross_profit_usd": 0.0, "gross_loss_usd": 0.0}
    numeric_cols = ["profit", "commission", "swap", "fee"]
    for c in numeric_cols:
        if c not in transactions.columns:
            transactions[c] = 0.0
        transactions[c] = pd.to_numeric(transactions[c], errors="coerce").fillna(0.0)
    transactions["net"] = transactions[numeric_cols].sum(axis=1)
    entry = pd.to_numeric(transactions.get("entry", 0), errors="coerce").fillna(-1).astype(int)
    # MQL5 DEAL_ENTRY_OUT=1, OUT_BY=3. Count only realized exit legs for round-trip evidence.
    exits = transactions[entry.isin([1, 3])]
    net = float(transactions["net"].sum())
    gp = float(transactions.loc[transactions["net"] > 0, "net"].sum())
    gl = float(transactions.loc[transactions["net"] < 0, "net"].sum())
    return {
        "deals": int(len(transactions)),
        "round_trip_exit_deals": int(len(exits)),
        "net_pnl_usd": round(net, 6),
        "gross_profit_usd": round(gp, 6),
        "gross_loss_usd": round(gl, 6),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True)
    ap.add_argument("--evals", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--transactions", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--trade-report", required=True)
    ns = ap.parse_args()

    trades = read_csv(Path(ns.trades))
    evals = read_csv(Path(ns.evals))
    events = read_csv(Path(ns.events))
    tx = read_csv(Path(ns.transactions))
    if trades.empty:
        raise RuntimeError("V57 missing trades.csv")
    if evals.empty:
        raise RuntimeError("V57 missing V57_ENTRY_EVAL.csv")

    trades = trades[(trades["candidate"] == CANDIDATE) & (trades["book"] == BOOK)].copy()
    trades["entry_time_dt"] = to_dt(trades["entry_time"])
    trades = trades[(trades["entry_time_dt"] >= WEEK_START) & (trades["entry_time_dt"] < WEEK_END)].copy()
    evals["time"] = to_dt(evals["time"])
    evals = evals[(evals["time"] >= WEEK_START) & (evals["time"] < WEEK_END)].copy()

    gate_results = {name: summarize_gate(trades, evals, col) for name, col in GATES.items()}
    broker = broker_pnl(tx)

    trade_report = trades.merge(
        evals[["time"] + list(GATES.values()) + [
            "feature_ready", "trend_h1", "trend_h4", "structure_dir", "bos_choch_dir",
            "fvg_dir", "liquidity_sweep_dir", "di_dir", "macd_dir", "score",
            "risk_cash_fixed001", "risk_pct_equity", "margin_cash", "lot_ok"
        ]],
        left_on="entry_time_dt", right_on="time", how="left"
    )
    vv = pd.to_numeric(trade_report["initial_volume_std_equiv"], errors="coerce")
    vp = pd.to_numeric(trade_report["total_pnl"], errors="coerce")
    trade_report["fixed001_pnl_shadow_usd"] = vp * (FIXED_LOT / vv.where(vv > 0))
    report_cols = [
        "entry_time", "exit_time", "direction", "entry", "exit", "stop", "tp",
        "initial_volume_std_equiv", "total_pnl", "r_multiple", "fixed001_pnl_shadow_usd",
        "feature_ready", "trend_h1", "trend_h4", "structure_dir", "bos_choch_dir",
        "fvg_dir", "liquidity_sweep_dir", "di_dir", "macd_dir", "score",
        "risk_cash_fixed001", "risk_pct_equity", "margin_cash", "lot_ok"
    ] + list(GATES.values())
    trade_report[[c for c in report_cols if c in trade_report.columns]].to_csv(Path(ns.trade_report), index=False)

    eval_numeric = evals.copy()
    for c in ["risk_cash_fixed001", "risk_pct_equity", "margin_cash", "score"]:
        if c in eval_numeric.columns:
            eval_numeric[c] = pd.to_numeric(eval_numeric[c], errors="coerce")

    guard_counts = {}
    would_halt_counts = {}
    if not events.empty and "action" in events.columns:
        guards = events[events["action"] == "GUARD"]
        if not guards.empty:
            guard_counts = guards["direction"].astype(str).value_counts().to_dict()
        wh = events[events["action"] == "V57_WOULD_HALT"]
        if not wh.empty:
            would_halt_counts = wh["direction"].astype(str).value_counts().to_dict()

    payload = {
        "schema": "v57_fixed001_trend_smc_weekly_replay_v1",
        "candidate": CANDIDATE,
        "book": BOOK,
        "fixed_lot": FIXED_LOT,
        "initial_balance_usd": INITIAL_BALANCE,
        "week": "2026-08-24..2026-08-28",
        "gate_results_shadow_fixed001": gate_results,
        "actual_broker_balanced_gate": broker,
        "entry_evaluations": int(len(evals)),
        "risk_cash_fixed001_min": None if eval_numeric.empty else round(float(eval_numeric["risk_cash_fixed001"].min()), 6),
        "risk_cash_fixed001_max": None if eval_numeric.empty else round(float(eval_numeric["risk_cash_fixed001"].max()), 6),
        "risk_pct_equity_max_observed": None if eval_numeric.empty else round(float(eval_numeric["risk_pct_equity"].max()), 4),
        "confluence_score_min": None if eval_numeric.empty else int(eval_numeric["score"].min()),
        "confluence_score_max": None if eval_numeric.empty else int(eval_numeric["score"].max()),
        "guard_reason_counts": guard_counts,
        "capital_limits_would_halt": would_halt_counts,
        "methodology": {
            "smc_features": ["confirmed H1 swing structure", "BOS/CHoCH proxy", "3-candle displacement FVG", "liquidity sweep"],
            "trend_features": ["H1 EMA50/EMA200 + EMA50 slope", "H4 EMA20/EMA50", "ADX + DI", "MACD", "RSI14"],
            "causal_swing_confirmation": "two closed H1 bars after pivot are required before the pivot can be used",
            "same_week_gate_comparison_is_exploratory": True,
        },
    }

    Path(ns.output).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "V57_FIXED001_TREND_SMC_REPLAY=1",
        f"WEEK={payload['week']}",
        f"FIXED_LOT={FIXED_LOT:.2f}",
        f"ENTRY_EVALUATIONS={payload['entry_evaluations']}",
        f"ACTUAL_BALANCED_BROKER_NET_USD={broker['net_pnl_usd']:.6f}",
        f"ACTUAL_BALANCED_BROKER_DEALS={broker['deals']}",
        f"RISK_CASH_FIXED001_MIN={payload['risk_cash_fixed001_min']}",
        f"RISK_CASH_FIXED001_MAX={payload['risk_cash_fixed001_max']}",
    ]
    for name in GATES:
        r = gate_results[name]
        lines.append(
            f"GATE={name} trades={r['trades']} wins={r['wins']} losses={r['losses']} "
            f"net_usd={r['net_pnl_usd_fixed001']:.6f} return_pct_proxy={r['return_pct_proxy']:.4f} "
            f"pf={r['profit_factor']} max_dd_pct_proxy={r['max_balance_dd_pct_proxy']:.4f} "
            f"balance_breach={int(r['balance_breach_proxy'])}"
        )
    lines.append("NOTE=same-week gate comparison is exploratory; no promotion from one week alone")
    lines.append(f"TRADE_REPORT={ns.trade_report}")
    Path(ns.summary).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
