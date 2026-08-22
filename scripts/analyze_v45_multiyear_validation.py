#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

BOOK = "usd40_r1p0_cent_continuous"
CANDIDATES = [
    "adaptive_ewma_hl8_thr0",
    "adaptive_ewma_hl8_thr0p05",
    "adaptive_ewma_hl10_thr0p05",
]
PRIMARY = "adaptive_ewma_hl10_thr0p05"
WARMUP_MONTHS_DEFAULT = 6
MIN_TOTAL_MONTHS = 48
MIN_EVAL_MONTHS = 42


def month_period(value) -> pd.Period:
    s = str(value).strip().replace("_", "-").replace(".", "-")
    if len(s) >= 7:
        s = s[:7]
    return pd.Period(s, freq="M")


def parse_time(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, format="%Y.%m.%d %H:%M:%S", errors="raise")


def pf_from_r(r: pd.Series) -> float:
    if r.empty:
        return 0.0
    gp = float(r[r > 0].sum())
    gl = float(-r[r < 0].sum())
    if gl > 0:
        return gp / gl
    return math.inf if gp > 0 else 0.0


def compound_pct(values) -> float:
    arr = np.asarray(list(values), dtype=float)
    if len(arr) == 0:
        return 0.0
    return float(100.0 * (np.prod(1.0 + arr / 100.0) - 1.0))


def geo_month_pct(total_return_pct: float, months: int) -> float:
    if months <= 0:
        return 0.0
    factor = 1.0 + total_return_pct / 100.0
    return -100.0 if factor <= 0 else float(100.0 * (factor ** (1.0 / months) - 1.0))


def load_run(run: Path):
    for name in ("monthly_summary.csv", "trades.csv", "manifest.txt"):
        p = run / name
        if not p.is_file() or p.stat().st_size == 0:
            raise RuntimeError(f"missing run artifact: {name}")
    manifest = (run / "manifest.txt").read_text(encoding="utf-8-sig", errors="replace")
    for tok in (
        "v45_multiyear_validation=1",
        "v45_strategy_logic_changed=0",
        "v45_risk_changed=0",
        "v45_state_protocol=cold_start_no_2025_state",
        "v45_single_tester_run=1",
        "tester_only=1",
        "native_broker_orders=0",
        "external_broker_orders=0",
        "v45_live_authorized=0",
    ):
        if tok not in manifest:
            raise RuntimeError(f"manifest contract missing {tok}")
    return pd.read_csv(run / "monthly_summary.csv"), pd.read_csv(run / "trades.csv"), manifest


def rolling_rows(months: pd.DataFrame, candidate: str) -> list[dict]:
    out = []
    vals = months["return_pct"].astype(float).to_numpy()
    labels = months["period"].tolist()
    for window in (3, 6, 12):
        if len(vals) < window:
            continue
        for i in range(window - 1, len(vals)):
            chunk = vals[i - window + 1 : i + 1]
            out.append({"candidate": candidate, "window_months": window, "end_month": str(labels[i]), "return_pct": compound_pct(chunk)})
    return out


def candidate_metrics(monthly: pd.DataFrame, trades: pd.DataFrame, candidate: str, warmup: int) -> tuple[dict, list[dict], list[dict], list[dict]]:
    m = monthly[(monthly["candidate"] == candidate) & (monthly["book"] == BOOK)].copy()
    if m.empty:
        raise RuntimeError(f"{candidate}: no monthly rows")
    m["period"] = [month_period(x) for x in m["month"]]
    m = m.sort_values("period").drop_duplicates("period", keep="last").reset_index(drop=True)
    if len(m) < MIN_TOTAL_MONTHS:
        raise RuntimeError(f"{candidate}: expected at least {MIN_TOTAL_MONTHS} monthly rows, got {len(m)}")
    eval_m = m.iloc[warmup:].copy().reset_index(drop=True)
    if len(eval_m) < MIN_EVAL_MONTHS:
        raise RuntimeError(f"{candidate}: only {len(eval_m)} evaluation months after warmup={warmup}")

    t = trades[(trades["candidate"] == candidate) & (trades["book"] == BOOK)].copy()
    if not t.empty:
        t["entry_dt"] = parse_time(t["entry_time"])
        t["exit_dt"] = parse_time(t["exit_time"])
        eval_start = eval_m["period"].iloc[0].start_time
        t_eval = t[t["entry_dt"] >= eval_start].copy()
    else:
        t_eval = t.copy()

    monthly_returns = eval_m["return_pct"].astype(float)
    total = compound_pct(monthly_returns)
    geo = geo_month_pct(total, len(eval_m))
    max_dd = float(eval_m["max_mtm_dd_pct"].astype(float).max())
    r = t_eval["r_multiple"].astype(float) if len(t_eval) else pd.Series(dtype=float)
    pf = pf_from_r(r)
    positive_months = int((monthly_returns > 0).sum())

    yearly = []
    for year, g in eval_m.groupby(eval_m["period"].map(lambda p: p.year), sort=True):
        yr_ret = compound_pct(g["return_pct"].astype(float))
        gt = t_eval[t_eval["entry_dt"].dt.year == int(year)] if len(t_eval) else t_eval
        gr = gt["r_multiple"].astype(float) if len(gt) else pd.Series(dtype=float)
        yearly.append({
            "candidate": candidate, "year": int(year), "months": int(len(g)), "full_year": bool(len(g) == 12),
            "return_pct": yr_ret, "geo_month_pct": geo_month_pct(yr_ret, len(g)),
            "positive_months": int((g["return_pct"].astype(float) > 0).sum()),
            "worst_month_pct": float(g["return_pct"].astype(float).min()), "best_month_pct": float(g["return_pct"].astype(float).max()),
            "max_mtm_dd_pct": float(g["max_mtm_dd_pct"].astype(float).max()), "trades": int(len(gt)),
            "avg_r": float(gr.mean()) if len(gr) else None, "sum_r": float(gr.sum()) if len(gr) else 0.0,
            "profit_factor_r": pf_from_r(gr),
        })

    rolling = rolling_rows(eval_m, candidate)
    roll12 = [x for x in rolling if x["window_months"] == 12]
    full_years = [x for x in yearly if x["full_year"]]
    positive_full_years = sum(x["return_pct"] > 0 for x in full_years)
    rolling12_positive = sum(x["return_pct"] > 0 for x in roll12)
    rolling12_ratio = rolling12_positive / len(roll12) if roll12 else 0.0
    worst_roll12 = min((x["return_pct"] for x in roll12), default=float("nan"))

    positive_r = r[r > 0].sort_values(ascending=False) if len(r) else pd.Series(dtype=float)
    top10_share = float(positive_r.head(10).sum() / r.sum()) if len(r) and r.sum() > 0 else None
    stress02 = float(r.sum() - 0.02 * len(r)) if len(r) else 0.0
    stress05 = float(r.sum() - 0.05 * len(r)) if len(r) else 0.0

    checks = {
        "evaluation_months_at_least_42": len(eval_m) >= 42,
        "positive_month_ratio_at_least_60pct": positive_months / len(eval_m) >= 0.60,
        "at_least_3_full_calendar_years": len(full_years) >= 3,
        "at_least_75pct_full_years_positive": len(full_years) >= 1 and positive_full_years / len(full_years) >= 0.75,
        "worst_full_year_not_below_minus15pct": not full_years or min(x["return_pct"] for x in full_years) >= -15.0,
        "rolling_12m_positive_ratio_at_least_75pct": rolling12_ratio >= 0.75,
        "worst_rolling_12m_not_below_minus15pct": bool(roll12) and worst_roll12 >= -15.0,
        "max_mtm_dd_at_most_20pct": max_dd <= 20.0,
        "profit_factor_r_at_least_1p20": pf >= 1.20,
        "worst_month_not_below_minus15pct": float(monthly_returns.min()) >= -15.0,
        "sum_r_after_extra_0p05r_per_trade_positive": stress05 > 0.0,
    }

    summary = {
        "candidate": candidate,
        "coverage": {"raw_first_month": str(m["period"].iloc[0]), "raw_last_month": str(m["period"].iloc[-1]), "raw_months": int(len(m)), "warmup_months": int(warmup), "evaluation_first_month": str(eval_m["period"].iloc[0]), "evaluation_last_month": str(eval_m["period"].iloc[-1]), "evaluation_months": int(len(eval_m))},
        "evaluation": {
            "compounded_return_pct": total, "geo_month_pct": geo,
            "annualized_return_pct": float(100.0 * ((1.0 + total / 100.0) ** (12.0 / len(eval_m)) - 1.0)) if total > -100 else -100.0,
            "max_mtm_dd_pct": max_dd, "positive_months": positive_months, "positive_month_ratio": positive_months / len(eval_m),
            "worst_month_pct": float(monthly_returns.min()), "best_month_pct": float(monthly_returns.max()),
            "trades": int(len(t_eval)), "avg_r": float(r.mean()) if len(r) else None, "sum_r": float(r.sum()) if len(r) else 0.0,
            "profit_factor_r": pf, "turnover_x_start40": float(eval_m["gross_notional_turnover"].astype(float).sum() / 40.0),
            "top10_winner_share_of_net_r": top10_share,
        },
        "year_stability": {"full_years": int(len(full_years)), "positive_full_years": int(positive_full_years), "worst_full_year_pct": float(min((x["return_pct"] for x in full_years), default=float("nan"))), "best_full_year_pct": float(max((x["return_pct"] for x in full_years), default=float("nan")))},
        "rolling_12m": {"observations": int(len(roll12)), "positive": int(rolling12_positive), "positive_ratio": float(rolling12_ratio), "worst_pct": float(worst_roll12) if roll12 else None, "best_pct": float(max((x["return_pct"] for x in roll12), default=float("nan"))) if roll12 else None},
        "friction_stress": {"sum_r_minus_0p02r_each_trade": stress02, "sum_r_minus_0p05r_each_trade": stress05},
        "multiyear_readiness": {"pass": all(checks.values()), "checks": checks},
    }

    month_rows = [{"candidate": candidate, "month": str(r.period), "warmup": bool(i < warmup), "return_pct": float(r.return_pct), "final_balance": float(r.final_balance), "max_mtm_dd_pct": float(r.max_mtm_dd_pct), "trades": int(r.trades), "gross_notional_turnover": float(r.gross_notional_turnover)} for i, r in m.iterrows()]
    return summary, month_rows, yearly, rolling


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-folder", required=True); ap.add_argument("--output", required=True)
    ap.add_argument("--monthly-csv", required=True); ap.add_argument("--yearly-csv", required=True); ap.add_argument("--rolling-csv", required=True)
    ap.add_argument("--warmup-months", type=int, default=WARMUP_MONTHS_DEFAULT)
    a = ap.parse_args()

    monthly, trades, _ = load_run(Path(a.run_folder))
    summaries=[]; month_rows=[]; yearly_rows=[]; rolling_rows_all=[]
    for candidate in CANDIDATES:
        s,mr,yr,rr=candidate_metrics(monthly,trades,candidate,a.warmup_months)
        summaries.append(s); month_rows.extend(mr); yearly_rows.extend(yr); rolling_rows_all.extend(rr)
    ready=[s for s in summaries if s["multiyear_readiness"]["pass"]]
    def robustness_key(s):
        ys=s["year_stability"]; r12=s["rolling_12m"]; ev=s["evaluation"]
        return (ys["positive_full_years"],r12["positive_ratio"],ev["geo_month_pct"],-ev["max_mtm_dd_pct"],ev["profit_factor_r"])
    robustness_winner=max(ready if ready else summaries,key=robustness_key)
    return_winner=max(summaries,key=lambda s:s["evaluation"]["geo_month_pct"])
    primary=next(s for s in summaries if s["candidate"]==PRIMARY)
    status="MULTIYEAR_ROBUSTNESS_PASS" if primary["multiyear_readiness"]["pass"] else "HOLD"

    pd.DataFrame(month_rows).to_csv(a.monthly_csv,index=False,lineterminator="\n")
    pd.DataFrame(yearly_rows).to_csv(a.yearly_csv,index=False,lineterminator="\n")
    pd.DataFrame(rolling_rows_all).to_csv(a.rolling_csv,index=False,lineterminator="\n")
    out={
        "schema":"v45_multiyear_single_run_validation_v1",
        "protocol":{"single_tester_run":True,"default_from":"2022.01.01","default_to":"2026.08.01","cold_start":True,"warmup_months":int(a.warmup_months),"monthly_logging":True,"note":"One continuous exact-MT5 run. No 2025 state is injected. Warmup months are excluded from deployment-readiness metrics."},
        "candidates":summaries,"status":status,"primary_candidate":PRIMARY,"primary_pass":primary["multiyear_readiness"]["pass"],
        "robustness_winner":robustness_winner["candidate"],"return_winner":return_winner["candidate"],"ready_candidates":[x["candidate"] for x in ready],
        "live_authorized":False,"decision_rule":"A V45 pass supports continued paper/demo deployment validation only. It does not authorize real-money live trading and does not permit same-sample retuning.",
    }
    Path(a.output).write_text(json.dumps(out,indent=2,allow_nan=False),encoding="utf-8")
    print(json.dumps({"status":status,"primary":PRIMARY,"primary_pass":primary["multiyear_readiness"]["pass"],"robustness_winner":robustness_winner["candidate"],"return_winner":return_winner["candidate"],"ready":out["ready_candidates"],"live_authorized":False},indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
