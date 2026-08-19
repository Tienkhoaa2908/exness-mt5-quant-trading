#!/usr/bin/env python3
"""V30 causal feature-lake + trade expected-R research utilities.

Offline only. No broker connection or order path.
Critical timing contract: each bar_features row is stamped with the just-closed
M15 bar OPEN time and only becomes available at `time + 15 minutes`.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

BAR_MINUTES = 15
BAR_DELTA = pd.Timedelta(minutes=BAR_MINUTES)
HORIZONS = (1, 4, 8, 16, 32)
EXPERTS = ("ema", "macd", "bos", "trend", "slow")

# EA/raw metadata or intentionally non-model fields.
BAR_META = {
    "time", "month", "bar_seq", "open", "high", "low", "close",
    "tick_volume", "real_volume",
}
BAR_EXCLUDE = {
    "real_volume",
    "tick_agg_ready", "mtf_ready",
    "ema_ready", "trend20_ready", "rsi2_ready", "macd_ready", "don55_ready",
    "bb_rsi_ready", "liq_sweep_ready", "bos_fvg_ready", "slow_mom_ready",
    "bb_rsi_dir",
}
# Outcome/post-entry trade fields must never enter model features.
TRADE_OUTCOME = {
    "exit_time", "exit", "final_stop", "final_volume_std_equiv",
    "partial_realized_pnl", "final_leg_pnl", "total_pnl", "r_multiple",
    "mfe_r", "mae_r", "giveback_r", "capture_eff_pct", "partial_done",
    "balance_after", "exit_reason",
}
SAFE_TRADE_NUMERIC = (
    "direction", "entered_after_profit_exit", "entry_gap_bars",
    "entry_quality_score", "entry_adx", "entry_plus_di", "entry_minus_di",
    "entry_atr_ratio", "entry_body_ratio", "entry_close_location",
    "entry_dist_ema200_atr", "entry_rsi2", "entry_rsi14", "entry_macd_hist",
    "entry_h1_gap_atr", "entry_server_hour", "entry_profit_streak_before",
    "entry_bars_since_exit", "adaptive_mode",
)

@dataclass(frozen=True)
class ChunkSpec:
    bars: Path
    trades: Path | None
    start: pd.Timestamp
    end: pd.Timestamp


def parse_time(s: pd.Series) -> pd.Series:
    # MT5 CSV uses `YYYY.MM.DD HH:MM:SS`; pandas inference handles it but an
    # explicit format keeps results deterministic.
    return pd.to_datetime(s, format="%Y.%m.%d %H:%M:%S", errors="raise")


def read_trimmed_bars(path: Path, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "time" not in df or len(df.columns) != 136:
        raise ValueError(f"{path}: expected V30 136-column bar schema")
    df["time"] = parse_time(df["time"])
    df = df.loc[(df["time"] >= start) & (df["time"] < end)].copy()
    if df.empty:
        raise ValueError(f"{path}: no rows inside [{start}, {end})")
    return df


def stitch_bars(specs: Sequence[ChunkSpec]) -> pd.DataFrame:
    frames = [read_trimmed_bars(s.bars, s.start, s.end) for s in specs]
    schemas = [tuple(f.columns) for f in frames]
    if len(set(schemas)) != 1:
        raise ValueError("V30 bar schemas differ across chunks")
    df = pd.concat(frames, ignore_index=True).sort_values("time").reset_index(drop=True)
    if df["time"].duplicated().any():
        d = df.loc[df["time"].duplicated(False), "time"].head().tolist()
        raise ValueError(f"duplicate canonical timestamps: {d}")
    if not df["time"].is_monotonic_increasing:
        raise ValueError("canonical bars are not monotonic")
    numeric = df.select_dtypes(include=[np.number])
    if np.isinf(numeric.to_numpy(dtype=float, copy=False)).any():
        raise ValueError("canonical bars contain Inf")
    if numeric.isna().any().any():
        bad = numeric.columns[numeric.isna().any()].tolist()
        raise ValueError(f"canonical bars contain NaN: {bad[:10]}")
    # Critical contract: stamped OPEN time of closed bar -> available at close.
    df["feature_available_time"] = df["time"] + BAR_DELTA
    gap = df["feature_available_time"].diff().dt.total_seconds().div(60)
    df["gap_minutes"] = gap.fillna(BAR_MINUTES).astype(float)
    return add_causal_state_features(df)


def add_causal_state_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    eps = 1e-9
    # Cyclic clock state.
    hour = pd.to_numeric(out["server_hour"], errors="raise").astype(float)
    dow = pd.to_numeric(out["day_of_week"], errors="raise").astype(float)
    out["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
    out["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)
    out["dow_sin"] = np.sin(2 * np.pi * dow / 7.0)
    out["dow_cos"] = np.cos(2 * np.pi * dow / 7.0)

    # Microstructure/range efficiency.
    out["rv8_to_rv32"] = out["rv8"] / (np.abs(out["rv32"]) + eps)
    out["m1_to_m5_range"] = out["m1_range_atr"] / (np.abs(out["m5_range_atr"]) + eps)
    out["m5_to_h1_range"] = out["m5_range_atr"] / (np.abs(out["h1_range_atr"]) + eps)
    out["tick_path_efficiency"] = np.abs(out["tick_mid_net_move_atr"]) / (np.abs(out["tick_mid_abs_path_atr"]) + eps)
    out["tick_change_fraction"] = (out["bid_change_count"] + out["ask_change_count"]) / (np.abs(out["tick_count"]) + eps)
    out["tick_spread_cv"] = out["tick_spread_std_points"] / (np.abs(out["tick_spread_mean_points"]) + eps)
    out["di_spread"] = out["plus_di"] - out["minus_di"]
    out["signal_imbalance"] = out["signal_count_long"] - out["signal_count_short"]
    out["signal_activity"] = out["signal_count_long"] + out["signal_count_short"]
    out["macd_hist_atr"] = out["macd_hist"] / (np.abs(out["atr14"]) + eps)

    fast_cols, slow_cols = [], []
    for e in EXPERTS:
        fast = f"ewma_fast5_{e}"
        slow = f"ewma_slow20_{e}"
        hl8 = f"ewma_hl8_{e}"
        hl12 = f"ewma_hl12_{e}"
        obs = f"expert_obs_{e}"
        out[f"expert_fast_minus_slow_{e}"] = out[fast] - out[slow]
        out[f"expert_hl8_minus_slow_{e}"] = out[hl8] - out[slow]
        out[f"expert_fast_minus_hl8_{e}"] = out[fast] - out[hl8]
        out[f"expert_hl8_minus_hl12_{e}"] = out[hl8] - out[hl12]
        out[f"expert_obs_log1p_{e}"] = np.log1p(np.maximum(out[obs], 0))
        out[f"expert_confidence_{e}"] = 1.0 - np.exp(-np.maximum(out[obs], 0) / 20.0)
        out[f"expert_change_conf_{e}"] = out[f"expert_fast_minus_slow_{e}"] * out[f"expert_confidence_{e}"]
        fast_cols.append(fast); slow_cols.append(slow)

    fast_mat = out[fast_cols].to_numpy(dtype=float)
    slow_mat = out[slow_cols].to_numpy(dtype=float)
    change = fast_mat - slow_mat
    out["expert_fast_mean"] = fast_mat.mean(axis=1)
    out["expert_fast_std"] = fast_mat.std(axis=1)
    out["expert_slow_mean"] = slow_mat.mean(axis=1)
    out["expert_slow_std"] = slow_mat.std(axis=1)
    out["expert_change_mean"] = change.mean(axis=1)
    out["expert_change_abs_mean"] = np.abs(change).mean(axis=1)
    out["expert_change_std"] = change.std(axis=1)
    # Relative state removes common-level drift.
    for j, e in enumerate(EXPERTS):
        out[f"expert_fast_rel_{e}"] = fast_mat[:, j] - out["expert_fast_mean"].to_numpy()
        out[f"expert_slow_rel_{e}"] = slow_mat[:, j] - out["expert_slow_mean"].to_numpy()
    return out


def add_bar_labels(df: pd.DataFrame, horizons: Iterable[int] = HORIZONS) -> pd.DataFrame:
    """Offline future labels. Tail rows remain NaN; no NaN->class-0 bug."""
    out = df.copy()
    close = pd.to_numeric(out["close"], errors="raise").astype(float)
    high = pd.to_numeric(out["high"], errors="raise").astype(float)
    low = pd.to_numeric(out["low"], errors="raise").astype(float)
    atr = pd.to_numeric(out["atr14"], errors="raise").astype(float).replace(0, np.nan)
    logc = np.log(close)
    for h in horizons:
        ret = logc.shift(-h) - logc
        out[f"target_logret_{h}"] = ret
        out[f"target_up_{h}"] = np.where(ret.notna(), (ret > 0).astype(float), np.nan)
        future_hi = pd.concat([high.shift(-i) for i in range(1, h + 1)], axis=1).max(axis=1, skipna=False)
        future_lo = pd.concat([low.shift(-i) for i in range(1, h + 1)], axis=1).min(axis=1, skipna=False)
        out[f"target_mfe_atr_{h}"] = (future_hi - close) / atr
        out[f"target_mae_atr_{h}"] = (close - future_lo) / atr
        out[f"target_range_atr_{h}"] = (future_hi - future_lo) / atr
    return out


def load_norm_trades(specs: Sequence[ChunkSpec], book: str = "norm10k_r0p5_continuous") -> pd.DataFrame:
    frames = []
    for s in specs:
        if s.trades is None:
            continue
        t = pd.read_csv(s.trades)
        t["entry_time"] = parse_time(t["entry_time"])
        t["exit_time"] = parse_time(t["exit_time"])
        t = t.loc[(t["entry_time"] >= s.start) & (t["entry_time"] < s.end) & (t["book"] == book)].copy()
        frames.append(t)
    if not frames:
        raise ValueError("no trade ledgers supplied")
    out = pd.concat(frames, ignore_index=True).sort_values(["entry_time", "candidate"]).reset_index(drop=True)
    if out["r_multiple"].isna().any():
        raise ValueError("trade target r_multiple contains NaN")
    return out


def join_trades_to_causal_bars(trades: pd.DataFrame, bars: pd.DataFrame, seq_len: int = 64) -> pd.DataFrame:
    avail = bars["feature_available_time"].to_numpy(dtype="datetime64[ns]")
    ent = trades["entry_time"].to_numpy(dtype="datetime64[ns]")
    idx = np.searchsorted(avail, ent, side="right") - 1
    if (idx < 0).any():
        raise ValueError("trade precedes first causal feature availability")
    out = trades.copy()
    out["bar_index"] = idx.astype(int)
    out["feature_time"] = bars.iloc[idx]["time"].to_numpy()
    out["feature_available_time"] = bars.iloc[idx]["feature_available_time"].to_numpy()
    out["feature_age_minutes"] = (out["entry_time"] - out["feature_time"]).dt.total_seconds() / 60.0
    out["availability_lag_minutes"] = (out["entry_time"] - out["feature_available_time"]).dt.total_seconds() / 60.0
    if (out["feature_available_time"] > out["entry_time"]).any():
        raise ValueError("causal join violation: unavailable feature row joined")
    out["sequence_ready"] = (out["bar_index"] >= seq_len - 1).astype(int)
    return out


def bar_model_features(df: pd.DataFrame) -> list[str]:
    cols = []
    for c in df.columns:
        if c in BAR_META or c in BAR_EXCLUDE or c in {"feature_available_time"}:
            continue
        if c.startswith("target_"):
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            cols.append(c)
    return cols


def trade_static_features(df: pd.DataFrame) -> list[str]:
    return [c for c in SAFE_TRADE_NUMERIC if c in df.columns]


def materialize_trade_table(trades: pd.DataFrame, bars: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    bar_cols = bar_model_features(bars)
    static_cols = trade_static_features(trades)
    idx = trades["bar_index"].to_numpy(dtype=int)
    b = bars.iloc[idx][bar_cols].reset_index(drop=True).add_prefix("bar__")
    t = trades.reset_index(drop=True).copy()
    result = pd.concat([t, b], axis=1)
    return result, [f"bar__{c}" for c in bar_cols], static_cols


def write_dataset(specs: Sequence[ChunkSpec], output: Path, seq_len: int = 64) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    bars = stitch_bars(specs)
    labeled = add_bar_labels(bars)
    trades = load_norm_trades(specs)
    joined = join_trades_to_causal_bars(trades, bars, seq_len=seq_len)
    trade_table, bar_cols, static_cols = materialize_trade_table(joined, bars)

    bars.to_pickle(output / "v30_causal_bars.pkl")
    labeled.to_pickle(output / "v30_causal_bars_labeled.pkl")
    trade_table.to_pickle(output / "v30_causal_norm_trades.pkl")
    meta = {
        "bar_rows": int(len(bars)),
        "raw_bar_columns": 136,
        "engineered_bar_columns": int(len(bars.columns)),
        "bar_model_feature_count": len(bar_cols),
        "trade_rows": int(len(trade_table)),
        "trade_static_feature_count": len(static_cols),
        "seq_len": int(seq_len),
        "feature_availability_rule": "bar_features.time + 15 minutes",
        "causal_join_violations": int((joined["feature_available_time"] > joined["entry_time"]).sum()),
        "sequence_ready": int(joined["sequence_ready"].sum()),
        "start": str(bars["time"].min()),
        "end": str(bars["time"].max()),
        "months": sorted(bars["month"].astype(str).unique().tolist()),
        "bar_model_features": bar_cols,
        "trade_static_features": static_cols,
    }
    (output / "dataset_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def _ts(s: str) -> pd.Timestamp:
    return pd.Timestamp(s)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--chunk1-bars", type=Path, required=True)
    p.add_argument("--chunk1-trades", type=Path, required=True)
    p.add_argument("--chunk2-bars", type=Path, required=True)
    p.add_argument("--chunk2-trades", type=Path, required=True)
    p.add_argument("--chunk3-bars", type=Path, required=True)
    p.add_argument("--chunk3-trades", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seq-len", type=int, default=64)
    a = p.parse_args()
    specs = [
        ChunkSpec(a.chunk1_bars, a.chunk1_trades, _ts("2025-02-01"), _ts("2025-08-01")),
        ChunkSpec(a.chunk2_bars, a.chunk2_trades, _ts("2025-08-01"), _ts("2026-02-01")),
        ChunkSpec(a.chunk3_bars, a.chunk3_trades, _ts("2026-02-01"), _ts("2026-08-01")),
    ]
    print(json.dumps(write_dataset(specs, a.output, a.seq_len), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
