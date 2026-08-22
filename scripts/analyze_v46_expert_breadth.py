#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

BOOK = "usd40_r1p0_cent_continuous"
PRIMARY = "v46_hl10_thr0p05_breadth4"
CANDIDATES = [
    PRIMARY,
    "v46_hl10_thr0p05_breadth3_sensitivity",
    "v46_hl10_thr0p05_breadth5_sensitivity",
]
WARMUP_MONTHS = 6


def month_period(value) -> pd.Period:
    s = str(value).strip().replace("_", "-").replace(".", "-")[:7]
    return pd.Period(s, freq="M")


def pf_from_r(r: pd.Series) -> float:
    gp = float(r[r > 0].sum())
    gl = float(-r[r < 0].sum())
    if gl > 0:
        return gp / gl
    return math.inf if gp > 0 else 0.0


def compound_pct(values) -> float:
    a = np.asarray(list(values), dtype=float)
    if len(a) == 0:
        return 0.0
    return float(100.0 * (np.prod(1.0 + a / 100.0) - 1.0))


def geo_month_pct(total_return_pct: float, months: int) -> float:
    if months <= 0:
        return 0.0
    f = 1.0 + total_return_pct / 100.0
    return -100.0 if f <= 0 else float(100.0 * (f ** (1.0 / months) - 1.0))


def load_run(run: Path):
    for name in ("monthly_summary.csv", "trades.csv", "manifest.txt"):
        p = run / name
        if not p.is_file() or p.stat().st_size == 0:
            raise RuntimeError(f"missing run artifact: {name}")
    manifest = (run / "manifest.txt").read_text(encoding="utf-8-sig", errors="replace")
    required = (
        "v46_expert_breadth=1",
        "v46_strategy_logic_changed=1",
        "v46_risk_changed=0",
        "v46_state_protocol=cold_start_no_future_state",
        "v46_single_tester_run=1",
        "tester_only=1",
        "native_broker_orders=0",
        "external_broker_orders=0",
        "v46_live_authorized=0",
    )
    for token in required:
        if token not in manifest:
            raise RuntimeError(f"manifest contract missing {token}")
    return pd.read_csv(run / "monthly_summary.csv"), pd.read_csv(run / "trades.csv"), manifest


def analyze_candidate(monthly: pd.DataFrame, trades: pd.DataFrame, candidate: str):
    m = monthly[(monthly["candidate"] == candidate) & (monthly["book"] == BOOK)].copy()
    if m.empty:
        raise RuntimeError(f"candidate missing from monthly summary: {candidate}")
    m["period"] = m["month"].map(month_period)
    m = m.sort_values("period").drop_duplicates("period", keep="last")
    periods = pd.period_range(m.period.min(), m.period.max(), freq="M")
    if list(m.period) != list(periods):
        raise RuntimeError(f"monthly coverage not contiguous for {candidate}")
    m["warmup"] = np.arange(len(m)) < WARMUP_MONTHS
    ev = m[~m.warmup].copy()

    t = trades[(trades["candidate"] == candidate) & (trades["book"] == BOOK)].copy()
    if not t.empty:
        t["entry_dt"] = pd.to_datetime(t["entry_time"], format="%Y.%m.%d %H:%M:%S", errors="raise")
        eval_start = ev.period.min().start_time
        te = t[t.entry_dt >= eval_start].copy()
    else:
        te = t

    eval_comp = compound_pct(ev.return_pct)
    eval_geo = geo_month_pct(eval_comp, len(ev))
    annualized = float(100.0 * ((1.0 + eval_geo / 100.0) ** 12 - 1.0))
    active = ev[ev.trades > 0]

    yearly_rows = []
    for year, g in ev.groupby(ev.period.map(lambda p: p.year)):
        full = len(g) == 12
        yearly_rows.append({
            "candidate": candidate,
            "year": int(year),
            "months": int(len(g)),
            "full_year": bool(full),
            "return_pct": compound_pct(g.return_pct),
            "trades": int(g.trades.sum()),
            "positive_months": int((g.return_pct > 0).sum()),
        })
    yearly = pd.DataFrame(yearly_rows)
    full = yearly[yearly.full_year].copy()

    rolling = []
    vals = ev.return_pct.to_numpy(dtype=float)
    for window in (3, 6, 12):
        for i in range(window - 1, len(ev)):
            rolling.append({
                "candidate": candidate,
                "window_months": window,
                "end_month": str(ev.iloc[i].period),
                "return_pct": compound_pct(vals[i-window+1:i+1]),
            })
    rolling_df = pd.DataFrame(rolling)
    r12 = rolling_df[rolling_df.window_months == 12]

    holdout_2021 = ev[ev.period.map(lambda p: p.year == 2021)]
    holdout_2021_return = compound_pct(holdout_2021.return_pct)

    sum_r = float(te.r_multiple.sum()) if not te.empty else 0.0
    pf = pf_from_r(te.r_multiple) if not te.empty else 0.0
    raw_final = float(m.iloc[-1].final_balance)
    raw_return = float(100.0 * (raw_final / 40.0 - 1.0))
    raw_dd = float(m.max_mtm_dd_pct.max())

    checks = {
        "evaluation_months_at_least_60": len(ev) >= 60,
        "raw_max_mtm_dd_at_most_20pct": raw_dd <= 20.0,
        "profit_factor_r_at_least_1p20": pf >= 1.20,
        "annualized_return_at_least_10pct": annualized >= 10.0,
        "at_least_4_full_calendar_years": len(full) >= 4,
        "at_least_75pct_full_years_nonnegative": (float((full.return_pct >= 0).mean()) if len(full) else 0.0) >= 0.75,
        "worst_full_year_not_below_minus10pct": (float(full.return_pct.min()) if len(full) else -999.0) >= -10.0,
        "rolling12_at_least_75pct_not_worse_than_minus5pct": (float((r12.return_pct >= -5.0).mean()) if len(r12) else 0.0) >= 0.75,
        "worst_rolling12_not_below_minus10pct": (float(r12.return_pct.min()) if len(r12) else -999.0) >= -10.0,
        "active_months_at_least_24": len(active) >= 24,
        "positive_active_month_ratio_at_least_50pct": (float((active.return_pct > 0).mean()) if len(active) else 0.0) >= 0.50,
        "unseen_2021_postwarmup_return_not_below_minus10pct": holdout_2021_return >= -10.0,
        "trades_at_least_400": len(te) >= 400,
        "sum_r_after_extra_0p05r_per_trade_positive": sum_r - 0.05 * len(te) > 0.0,
    }

    result = {
        "candidate": candidate,
        "coverage": {
            "raw_first_month": str(m.period.min()),
            "raw_last_month": str(m.period.max()),
            "raw_months": int(len(m)),
            "warmup_months": WARMUP_MONTHS,
            "evaluation_first_month": str(ev.period.min()),
            "evaluation_last_month": str(ev.period.max()),
            "evaluation_months": int(len(ev)),
        },
        "raw_cold_start": {
            "final_balance": raw_final,
            "total_return_pct": raw_return,
            "max_mtm_dd_pct": raw_dd,
        },
        "evaluation": {
            "compounded_return_pct": eval_comp,
            "geo_month_pct": eval_geo,
            "annualized_return_pct": annualized,
            "active_months": int(len(active)),
            "positive_active_month_ratio": float((active.return_pct > 0).mean()) if len(active) else 0.0,
            "trades": int(len(te)),
            "avg_r": float(te.r_multiple.mean()) if len(te) else 0.0,
            "sum_r": sum_r,
            "profit_factor_r": pf,
        },
        "year_stability": {
            "full_years": int(len(full)),
            "nonnegative_full_years": int((full.return_pct >= 0).sum()) if len(full) else 0,
            "worst_full_year_pct": float(full.return_pct.min()) if len(full) else None,
            "best_full_year_pct": float(full.return_pct.max()) if len(full) else None,
        },
        "rolling_12m": {
            "observations": int(len(r12)),
            "not_worse_than_minus5pct_ratio": float((r12.return_pct >= -5.0).mean()) if len(r12) else 0.0,
            "worst_pct": float(r12.return_pct.min()) if len(r12) else None,
            "best_pct": float(r12.return_pct.max()) if len(r12) else None,
        },
        "unseen_2021_postwarmup_return_pct": holdout_2021_return,
        "friction_stress": {
            "sum_r_minus_0p02r_each_trade": sum_r - 0.02 * len(te),
            "sum_r_minus_0p05r_each_trade": sum_r - 0.05 * len(te),
        },
        "readiness": {"pass": bool(all(checks.values())), "checks": checks},
    }
    return result, m, yearly, rolling_df


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-folder", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--monthly-csv", required=True)
    ap.add_argument("--yearly-csv", required=True)
    ap.add_argument("--rolling-csv", required=True)
    a = ap.parse_args()

    monthly, trades, _ = load_run(Path(a.run_folder))
    results, ms, ys, rs = [], [], [], []
    for candidate in CANDIDATES:
        result, m, y, r = analyze_candidate(monthly, trades, candidate)
        results.append(result); ms.append(m); ys.append(y); rs.append(r)

    primary = next(x for x in results if x["candidate"] == PRIMARY)
    # Sensitivity candidates are deliberately ineligible for promotion from this sample.
    status = "V46_BREADTH_PRIMARY_PASS" if primary["readiness"]["pass"] else "HOLD"
    payload = {
        "schema": "v46_expert_breadth_walkforward_exact_mt5_v1",
        "primary_candidate": PRIMARY,
        "primary_pass": primary["readiness"]["pass"],
        "status": status,
        "candidates": results,
        "sensitivity_candidates_eligible_to_promote": False,
        "live_authorized": False,
        "decision_rule": "Only preregistered breadth4 can pass V46. Breadth3/5 are sensitivity evidence only. Any pass permits paper/demo research only.",
    }
    Path(a.output).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pd.concat(ms, ignore_index=True).to_csv(a.monthly_csv, index=False)
    pd.concat(ys, ignore_index=True).to_csv(a.yearly_csv, index=False)
    pd.concat(rs, ignore_index=True).to_csv(a.rolling_csv, index=False)
    print(f"STATUS={status}")
    print(f"PRIMARY={PRIMARY}")
    print(f"PRIMARY_PASS={int(primary['readiness']['pass'])}")
    print("LIVE_AUTHORIZED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
