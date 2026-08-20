#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RUN_IDS = [
    "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-02-01_00-00-00__756375",
    "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-08-01_00-00-00__22265",
    "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2026-02-01_00-00-00__519093",
]

BAR_NUM = [
    "rv8", "rv32", "atr_ratio", "dist_ema10_atr", "dist_ema20_atr",
    "dist_ema50_atr", "dist_ema200_atr", "rsi2", "rsi14", "macd_hist",
    "adx", "plus_di", "minus_di", "bb_pos", "bb_width_atr",
    "h1_ema50_minus_200_atr", "don20_pos", "don55_pos", "m1_ret5",
    "m1_ret15", "m1_rv15", "m1_efficiency", "m1_range_atr", "m5_ret1",
    "m5_ret2", "m5_rv3", "m5_range_atr", "h1_ret1", "h1_ret4",
    "h1_range_atr", "h1_close_location", "server_hour", "day_of_week",
    "tick_direction_imbalance", "tick_spread_std_points", "tick_mid_range_atr",
    "tick_mid_abs_path_atr", "tick_mid_net_move_atr", "signal_count_long",
    "signal_count_short",
]

EXPERT = [
    f"{prefix}_{expert}"
    for prefix in ["ewma_hl8", "ewma_fast5", "ewma_slow20"]
    for expert in ["ema", "macd", "bos", "trend", "slow"]
] + [f"expert_obs_{expert}" for expert in ["ema", "macd", "bos", "trend", "slow"]]


def parse_time(series):
    return pd.to_datetime(series, format="%Y.%m.%d %H:%M:%S", errors="raise")


def load_lake(common: Path) -> pd.DataFrame:
    parts = []
    for run_id in RUN_IDS:
        path = common / "mt5_quant" / "runs" / run_id / "bar_features.csv"
        if not path.is_file():
            raise FileNotFoundError(path)
        df = pd.read_csv(path)
        df["dt"] = parse_time(df.time)
        parts.append(df)
    lake = (
        pd.concat(parts, ignore_index=True)
        .sort_values("dt")
        .drop_duplicates("dt", keep="last")
        .reset_index(drop=True)
    )
    lake = lake[(lake.dt >= pd.Timestamp("2025-02-01")) & (lake.dt < pd.Timestamp("2026-08-01"))].copy()
    if len(lake) != 35344 or lake.dt.duplicated().any():
        raise RuntimeError(f"canonical bar lake mismatch rows={len(lake)}")
    lake["available"] = lake.dt + pd.Timedelta(minutes=15)
    missing = [c for c in BAR_NUM + EXPERT if c not in lake.columns]
    if missing:
        raise RuntimeError(f"missing V37 lake features: {missing}")
    return lake


def engineer(df: pd.DataFrame):
    out = df.copy()
    extra = []
    for expert in ["ema", "macd", "bos", "trend", "slow"]:
        for name, expr in [
            (f"fastslow_{expert}", out[f"ewma_fast5_{expert}"] - out[f"ewma_slow20_{expert}"]),
            (f"hl8slow_{expert}", out[f"ewma_hl8_{expert}"] - out[f"ewma_slow20_{expert}"]),
            (f"confidence_{expert}", np.log1p(out[f"expert_obs_{expert}"].clip(lower=0))),
        ]:
            out[name] = expr
            extra.append(name)
    out["vol_ratio"] = out.rv8 / (out.rv32.abs() + 1e-9)
    out["di_spread"] = out.plus_di - out.minus_di
    out["signal_imbalance"] = out.signal_count_long - out.signal_count_short
    extra += ["vol_ratio", "di_spread", "signal_imbalance"]
    return out, extra


def models():
    return {
        "histgb": HistGradientBoostingRegressor(
            max_iter=180,
            max_leaf_nodes=15,
            learning_rate=0.05,
            l2_regularization=2.0,
            random_state=2908,
        ),
        "extratrees": ExtraTreesRegressor(
            n_estimators=240,
            min_samples_leaf=10,
            max_features=0.70,
            n_jobs=-1,
            random_state=2908,
        ),
        "mlp": Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "model",
                    MLPRegressor(
                        hidden_layer_sizes=(48, 24),
                        alpha=0.01,
                        max_iter=160,
                        early_stopping=True,
                        n_iter_no_change=15,
                        random_state=2908,
                    ),
                ),
            ]
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--common-files", required=True)
    parser.add_argument("--v34-run-folder", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--predictions", required=True)
    args = parser.parse_args()

    common = Path(args.common_files)
    run = Path(args.v34_run_folder)
    trades_path = run / "trades.csv"
    if not trades_path.is_file():
        raise FileNotFoundError(trades_path)

    trades = pd.read_csv(trades_path)
    trades = trades[
        (trades.book == "norm10k_r0p5_continuous")
        & (trades.candidate == "v34_smc_ict_causal")
    ].copy()
    trades["entry_dt"] = parse_time(trades.entry_time)
    trades["exit_dt"] = parse_time(trades.exit_time)
    trades["direction_num"] = trades.direction.map({"LONG": 1, "SHORT": -1}).astype(int)
    if trades.empty:
        raise RuntimeError("no V34 SMC exact-MT5 trades")

    lake = load_lake(common)
    joined = pd.merge_asof(
        trades.sort_values("entry_dt"),
        lake[["available"] + BAR_NUM + EXPERT].sort_values("available"),
        left_on="entry_dt",
        right_on="available",
        direction="backward",
        allow_exact_matches=True,
    ).reset_index(drop=True)
    if joined[BAR_NUM + EXPERT].isna().all(axis=1).any():
        raise RuntimeError("missing causal V37 state at some SMC entries")

    joined, engineered = engineer(joined)
    features = BAR_NUM + EXPERT + engineered + ["direction_num"]
    x = joined[features].replace([np.inf, -np.inf], np.nan).fillna(0.0).astype(float)
    y = joined.r_multiple.astype(float).to_numpy()

    rows = []
    predictions = []
    for test_start in pd.date_range("2026-02-01", "2026-07-01", freq="MS"):
        test_end = test_start + pd.offsets.MonthBegin(1)
        calibration_start = test_start - pd.offsets.MonthBegin(1)
        train = np.where(joined.exit_dt < calibration_start)[0]
        calibration = np.where(
            (joined.entry_dt >= calibration_start) & (joined.entry_dt < test_start)
        )[0]
        test = np.where((joined.entry_dt >= test_start) & (joined.entry_dt < test_end))[0]
        if len(train) < 200 or len(calibration) < 20 or len(test) < 20:
            continue

        for name, model in models().items():
            model.fit(x.iloc[train], y[train])
            calibration_scores = model.predict(x.iloc[calibration])
            # Frozen development hypothesis: keep approximately top 60% of prior-month score distribution.
            threshold = float(np.quantile(calibration_scores, 0.40))
            score = model.predict(x.iloc[test])
            keep = score >= threshold
            base_avg = float(np.mean(y[test]))
            selected_avg = None if not keep.any() else float(np.mean(y[test][keep]))
            spearman = pd.Series(score).corr(pd.Series(y[test]), method="spearman")
            rows.append(
                {
                    "month": test_start.strftime("%Y_%m"),
                    "model": name,
                    "train": int(len(train)),
                    "calibration": int(len(calibration)),
                    "test": int(len(test)),
                    "kept": int(keep.sum()),
                    "coverage": float(keep.mean()),
                    "threshold": threshold,
                    "baseline_avg_r": base_avg,
                    "selected_avg_r": selected_avg,
                    "uplift_avg_r": None if selected_avg is None else selected_avg - base_avg,
                    "baseline_sum_r": float(y[test].sum()),
                    "selected_sum_r": float(y[test][keep].sum()) if keep.any() else 0.0,
                    "score_spearman": None if pd.isna(spearman) else float(spearman),
                }
            )
            for local_i, idx in enumerate(test):
                predictions.append(
                    {
                        "month": test_start.strftime("%Y_%m"),
                        "model": name,
                        "entry_time": str(joined.entry_dt.iloc[idx]),
                        "direction": str(joined.direction.iloc[idx]),
                        "actual_r": float(y[idx]),
                        "score": float(score[local_i]),
                        "keep": int(keep[local_i]),
                    }
                )

    if not rows:
        raise RuntimeError("V37 produced no chronological folds")

    fold_df = pd.DataFrame(rows)
    pred_df = pd.DataFrame(predictions)
    pred_df.to_csv(args.predictions, index=False, lineterminator="\n")

    aggregate = {}
    for model_name, group in fold_df.groupby("model"):
        selected = group.selected_avg_r.dropna()
        uplift = group.uplift_avg_r.dropna()
        aggregate[model_name] = {
            "months": int(len(group)),
            "mean_coverage": float(group.coverage.mean()),
            "mean_baseline_avg_r": float(group.baseline_avg_r.mean()),
            "mean_selected_avg_r": None if selected.empty else float(selected.mean()),
            "mean_uplift_avg_r": None if uplift.empty else float(uplift.mean()),
            "months_selected_avg_r_positive": int((selected > 0).sum()),
            "months_uplift_positive": int((uplift > 0).sum()),
            "total_baseline_sum_r": float(group.baseline_sum_r.sum()),
            "total_selected_sum_r": float(group.selected_sum_r.sum()),
            "mean_score_spearman": float(group.score_spearman.dropna().mean()),
        }

    # This is deliberately a development diagnostic, not an MT5 PnL claim.
    hist = aggregate.get("histgb", {})
    promising = (
        hist.get("months_selected_avg_r_positive", 0) >= 5
        and hist.get("months_uplift_positive", 0) >= 4
        and (hist.get("mean_selected_avg_r") or -999) > (hist.get("mean_baseline_avg_r") or 999)
    )
    output = {
        "schema": "v37_smc_quality_research_v1",
        "source": "V34 exact-MT5 norm-book SMC trades + causal V30 bar state",
        "candidate": "v34_smc_ict_causal",
        "models": ["HistGradientBoostingRegressor", "ExtraTreesRegressor", "MLPRegressor_48_24"],
        "keep_rule": "score >= prior-month 40th percentile (approximately keep60)",
        "test_months": sorted(fold_df.month.unique().tolist()),
        "feature_count": int(len(features)),
        "folds": rows,
        "aggregate": aggregate,
        "decision": "PROMISING_DEVELOPMENT_ONLY" if promising else "REJECT_OR_REDESIGN",
        "warning": "trade-level diagnostic only; no reconstructed PnL and no promotion. Any selected rule must be materialized on all active SMC bars and replayed in exact MT5 with aggregate stop-risk <=1%.",
    }
    Path(args.output).write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output["aggregate"], indent=2))
    print("V37 decision", output["decision"])


if __name__ == "__main__":
    main()
