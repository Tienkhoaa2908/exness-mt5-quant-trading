#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

CONTROL = "adaptive_ewma_hl8_thr0"
FAST = [
    "v38_adaptive_fast_tp0p50",
    "v38_adaptive_fast_tp0p75",
    "v38_adaptive_fast_tp1p00",
    "v38_adaptive_fast_gb0p25_after0p75",
    "v38_adaptive_velocity_decay_after0p50",
    "v38_adaptive_timebox30m",
]
BOOK = "usd40_r1p0_cent_continuous"
EXPECTED_CONTROL_FINAL = 107.432645
EXPECTED_CONTROL_TRADES = 563
EXPECTED_CONTROL_MONTHS = 12
EXPECTED_CONTROL_MONTHLY_TRADES = [30,72,76,37,43,65,41,37,20,32,62,48]
EXPECTED_CONTROL_MONTHLY_FINAL = [
    38.951141,43.518604,46.317250,47.137010,51.403129,63.068101,
    63.241472,64.790962,64.922339,73.052422,88.574123,107.432645,
]

def parse_time(s):
    return pd.to_datetime(s, format="%Y.%m.%d %H:%M:%S", errors="raise")

def aggregate_candidate(monthly: pd.DataFrame, trades: pd.DataFrame, candidate: str) -> dict:
    m = monthly[(monthly.candidate == candidate) & (monthly.book == BOOK)].copy()
    t = trades[(trades.candidate == candidate) & (trades.book == BOOK)].copy()
    if len(m) != 12:
        raise RuntimeError(f"{candidate}: expected 12 monthly rows, got {len(m)}")
    m = m.sort_values("month").reset_index(drop=True)
    if not t.empty:
        t["entry_dt"] = parse_time(t.entry_time)
        t["exit_dt"] = parse_time(t.exit_time)
        t["hold_minutes"] = (t.exit_dt - t.entry_dt).dt.total_seconds() / 60.0
    end = float(m.final_balance.iloc[-1])
    total_return = 100.0 * (end / 40.0 - 1.0)
    geo = 100.0 * ((end / 40.0) ** (1.0 / 12.0) - 1.0) if end > 0 else -100.0
    max_dd = float(m.max_mtm_dd_pct.max())
    pnl = t.total_pnl.astype(float) if not t.empty else pd.Series(dtype=float)
    gross_profit = float(pnl[pnl > 0].sum()) if len(pnl) else 0.0
    gross_loss = float(-pnl[pnl < 0].sum()) if len(pnl) else 0.0
    pf = gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)
    sum_r = float(t.r_multiple.astype(float).sum()) if not t.empty else 0.0
    total_hours = float(t.hold_minutes.sum() / 60.0) if not t.empty else 0.0
    cap = t.loc[t.mfe_r.astype(float) > 0.25, "capture_eff_pct"].astype(float) if not t.empty else pd.Series(dtype=float)
    return {
        "candidate": candidate,
        "ending_usd": end,
        "total_return_pct": total_return,
        "geo_month_pct": geo,
        "max_mtm_dd_pct": max_dd,
        "return_to_dd": total_return / max_dd if max_dd > 0 else None,
        "trades": int(len(t)),
        "positive_months": int((m.return_pct.astype(float) > 0).sum()),
        "months_ge_15pct": int((m.return_pct.astype(float) >= 15).sum()),
        "worst_month_pct": float(m.return_pct.astype(float).min()),
        "best_month_pct": float(m.return_pct.astype(float).max()),
        "avg_r": float(t.r_multiple.astype(float).mean()) if not t.empty else None,
        "sum_r": sum_r,
        "profit_factor": pf,
        "avg_giveback_r": float(t.giveback_r.astype(float).mean()) if not t.empty else None,
        "avg_mfe_r": float(t.mfe_r.astype(float).mean()) if not t.empty else None,
        "avg_capture_eff_pct": float(cap.mean()) if not cap.empty else None,
        "mean_hold_minutes": float(t.hold_minutes.mean()) if not t.empty else None,
        "median_hold_minutes": float(t.hold_minutes.median()) if not t.empty else None,
        "p90_hold_minutes": float(t.hold_minutes.quantile(0.90)) if not t.empty else None,
        "sum_r_per_market_hour": sum_r / total_hours if total_hours > 0 else None,
        "turnover_x_start40": float(m.gross_notional_turnover.astype(float).sum() / 40.0),
        "exit_reasons": {str(k): int(v) for k, v in t.exit_reason.value_counts().to_dict().items()} if not t.empty else {},
        "monthly_return_pct": {str(r.month): float(r.return_pct) for _, r in m.iterrows()},
    }

def verify_control(monthly: pd.DataFrame, trades: pd.DataFrame) -> dict:
    m = monthly[(monthly.candidate == CONTROL) & (monthly.book == BOOK)].sort_values("month").reset_index(drop=True)
    t = trades[(trades.candidate == CONTROL) & (trades.book == BOOK)]
    errors = []
    if len(m) != EXPECTED_CONTROL_MONTHS:
        errors.append(f"months={len(m)} expected={EXPECTED_CONTROL_MONTHS}")
    if len(t) != EXPECTED_CONTROL_TRADES:
        errors.append(f"trades={len(t)} expected={EXPECTED_CONTROL_TRADES}")
    if len(m) == EXPECTED_CONTROL_MONTHS:
        if list(m.trades.astype(int)) != EXPECTED_CONTROL_MONTHLY_TRADES:
            errors.append("monthly trade counts differ from accepted V34 control")
        diff = np.max(np.abs(m.final_balance.astype(float).to_numpy() - np.asarray(EXPECTED_CONTROL_MONTHLY_FINAL)))
        if diff > 1e-5:
            errors.append(f"monthly final balance max diff={diff:.9g}")
        if abs(float(m.final_balance.iloc[-1]) - EXPECTED_CONTROL_FINAL) > 1e-5:
            errors.append("final control balance mismatch")
    return {"pass": not errors, "errors": errors}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-folder", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--csv", required=True)
    a = ap.parse_args()
    run = Path(a.run_folder)
    monthly = pd.read_csv(run / "monthly_summary.csv")
    trades = pd.read_csv(run / "trades.csv")
    manifest = (run / "manifest.txt").read_text(encoding="utf-8-sig", errors="replace")
    if "v38_fast_harvest_lab=1" not in manifest:
        raise RuntimeError("V38 manifest marker missing")
    if "tester_only=1" not in manifest or "native_broker_orders=0" not in manifest or "external_broker_orders=0" not in manifest:
        raise RuntimeError("V38 safety manifest mismatch")
    control_check = verify_control(monthly, trades)
    if not control_check["pass"]:
        raise RuntimeError("V38 control reproducibility failed: " + "; ".join(control_check["errors"]))

    rows = [aggregate_candidate(monthly, trades, c) for c in [CONTROL] + FAST]
    frame = pd.DataFrame([{k:v for k,v in r.items() if k not in ("exit_reasons","monthly_return_pct")} for r in rows])
    frame.to_csv(a.csv, index=False, lineterminator="\n")

    control = rows[0]
    for r in rows[1:]:
        r["vs_control"] = {
            "ending_usd_delta": r["ending_usd"] - control["ending_usd"],
            "geo_month_pp": r["geo_month_pct"] - control["geo_month_pct"],
            "dd_reduction_pct": 100.0 * (control["max_mtm_dd_pct"] - r["max_mtm_dd_pct"]) / control["max_mtm_dd_pct"],
            "trade_change_pct": 100.0 * (r["trades"] - control["trades"]) / control["trades"],
            "median_hold_reduction_pct": (
                100.0 * (control["median_hold_minutes"] - r["median_hold_minutes"]) / control["median_hold_minutes"]
                if control["median_hold_minutes"] else None
            ),
            "turnover_change_pct": 100.0 * (r["turnover_x_start40"] - control["turnover_x_start40"]) / control["turnover_x_start40"],
        }

    fast = rows[1:]
    return_winner = max(fast, key=lambda r: r["ending_usd"])
    efficiency_winner = max(fast, key=lambda r: r["return_to_dd"] if r["return_to_dd"] is not None else -1e99)
    speed_winner = min(fast, key=lambda r: r["median_hold_minutes"] if r["median_hold_minutes"] is not None else 1e99)

    qualified = [
        r for r in fast
        if r["ending_usd"] >= 0.90 * control["ending_usd"]
        and r["max_mtm_dd_pct"] <= control["max_mtm_dd_pct"]
        and r["median_hold_minutes"] <= 0.60 * control["median_hold_minutes"]
    ]
    output = {
        "schema": "v38_fast_harvest_exact_mt5_v1",
        "period": "2025-08-01_to_2026-08-01",
        "book": BOOK,
        "control_reproducibility": control_check,
        "control": control,
        "fast_arms": rows[1:],
        "development_return_winner": return_winner["candidate"],
        "development_efficiency_winner": efficiency_winner["candidate"],
        "development_speed_winner": speed_winner["candidate"],
        "qualified_fast_harvest_candidates": [r["candidate"] for r in qualified],
        "decision_rule": (
            "development only. Preserve accepted baseline/keep60/V36 evidence. "
            "No fast arm is promoted without exact-MT5 economics and a later fresh chronological confirmation."
        ),
    }
    Path(a.output).write_text(json.dumps(output, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({
        "control": {k:control[k] for k in ["ending_usd","geo_month_pct","max_mtm_dd_pct","trades","avg_r","median_hold_minutes"]},
        "return_winner": return_winner["candidate"],
        "efficiency_winner": efficiency_winner["candidate"],
        "speed_winner": speed_winner["candidate"],
        "qualified": output["qualified_fast_harvest_candidates"],
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
