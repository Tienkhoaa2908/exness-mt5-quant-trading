#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

RUN_SPECS = [
    (
        "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-02-01_00-00-00__756375",
        pd.Timestamp("2025-02-01"),
        pd.Timestamp("2025-08-01"),
    ),
    (
        "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-08-01_00-00-00__22265",
        pd.Timestamp("2025-08-01"),
        pd.Timestamp("2026-02-01"),
    ),
    (
        "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2026-02-01_00-00-00__519093",
        pd.Timestamp("2026-02-01"),
        pd.Timestamp("2026-08-01"),
    ),
]

MARKET = [
    "atr_ratio",
    "adx",
    "dist_ema200_atr",
    "rsi14",
    "macd_hist",
    "h1_ema50_minus_200_atr",
    "h1_ret1",
    "h1_ret4",
    "m1_efficiency",
    "m1_up_fraction",
    "tick_direction_imbalance",
    "tick_mid_net_move_atr",
    "tick_mid_abs_path_atr",
    "spread_atr",
    "rv8",
    "rv32",
    "ewma_hl8_ema",
    "ewma_hl8_macd",
    "ewma_hl8_bos",
    "ewma_hl8_trend",
    "ewma_hl8_slow",
]

PATH = [
    "unrealized_r",
    "peak_r",
    "mae_r",
    "giveback_from_peak_r",
    "stop_r",
    "tp_r",
    "age_seconds",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_lake(common: Path) -> pd.DataFrame:
    parts = []
    audit = []
    for run_id, start, end in RUN_SPECS:
        path = common / "mt5_quant" / "runs" / run_id / "bar_features.csv"
        if not path.is_file():
            raise FileNotFoundError(path)
        df = pd.read_csv(path)
        df["feature_time"] = pd.to_datetime(
            df.pop("time"), format="%Y.%m.%d %H:%M:%S", errors="raise"
        )
        raw_rows = len(df)
        df = df[(df.feature_time >= start) & (df.feature_time < end)].copy()
        if df.empty:
            raise RuntimeError(f"empty canonical V36 chunk run={run_id}")
        audit.append(
            {
                "run_id": run_id,
                "raw_rows": int(raw_rows),
                "canonical_rows": int(len(df)),
                "start": str(start),
                "end_exclusive": str(end),
            }
        )
        parts.append(df)
    lake = pd.concat(parts, ignore_index=True).sort_values("feature_time").reset_index(drop=True)
    dup = int(lake.feature_time.duplicated().sum())
    if len(lake) != 35344 or dup != 0:
        raise RuntimeError(
            f"canonical V36 bar lake mismatch rows={len(lake)} duplicates={dup} audit={audit}"
        )
    missing = [c for c in MARKET if c not in lake.columns]
    if missing:
        raise RuntimeError(f"V36 market feature columns missing: {missing}")
    lake["available"] = lake["feature_time"] + pd.Timedelta(minutes=15)
    print(f"V36 canonical V30 lake PASS rows={len(lake)} duplicates={dup}")
    return lake


def prepare(common: Path, run: Path, book: str) -> pd.DataFrame:
    telemetry_path = run / "intra_trade_m15.csv"
    trades_path = run / "trades.csv"
    if not telemetry_path.is_file() or not trades_path.is_file():
        raise FileNotFoundError("V34 telemetry/trade ledger missing")

    tel = pd.read_csv(telemetry_path)
    trades = pd.read_csv(trades_path)
    tel = tel[tel.book == book].copy()
    trades = trades[trades.book == book].copy()
    if tel.empty or trades.empty:
        raise RuntimeError(f"no rows for V36 book={book}")

    for col in ["time", "entry_time"]:
        tel[col] = pd.to_datetime(
            tel[col], format="%Y.%m.%d %H:%M:%S", errors="raise"
        )
    for col in ["entry_time", "exit_time"]:
        trades[col] = pd.to_datetime(
            trades[col], format="%Y.%m.%d %H:%M:%S", errors="raise"
        )

    tel["trade_key"] = (
        tel.candidate.astype(str)
        + "|"
        + tel.entry_time.dt.strftime("%Y%m%d%H%M%S")
        + "|"
        + tel.direction.astype(str)
    )
    trades["trade_key"] = (
        trades.candidate.astype(str)
        + "|"
        + trades.entry_time.dt.strftime("%Y%m%d%H%M%S")
        + "|"
        + trades.direction.astype(str)
    )
    if trades.trade_key.duplicated().any():
        raise RuntimeError("duplicate V36 trade_key in V34 trade ledger")

    labels = trades[
        ["trade_key", "exit_time", "r_multiple", "mfe_r", "mae_r", "giveback_r"]
    ].rename(
        columns={
            "r_multiple": "final_r",
            "mfe_r": "final_mfe_r",
            "mae_r": "final_mae_r",
            "giveback_r": "final_giveback_r",
        }
    )
    tel = tel.merge(labels, on="trade_key", how="inner", validate="many_to_one")

    lake = load_lake(common)
    times = tel[["time"]].drop_duplicates().sort_values("time")
    market = pd.merge_asof(
        times,
        lake[["available"] + MARKET].sort_values("available"),
        left_on="time",
        right_on="available",
        direction="backward",
        allow_exact_matches=True,
    ).drop(columns="available")
    if market[MARKET].isna().all(axis=1).any():
        raise RuntimeError("missing causal V36 market state for telemetry rows")
    tel = tel.merge(market, on="time", how="left", validate="many_to_one")

    tel["future_delta_r"] = tel.final_r - tel.unrealized_r
    tel["future_upside_r"] = np.maximum(0.0, tel.final_mfe_r - tel.peak_r)
    tel["future_giveback_r"] = np.maximum(0.0, tel.unrealized_r - tel.final_r)
    tel["hold_label"] = (tel.future_upside_r >= 0.50).astype(np.float32)
    tel["protect_label"] = (tel.future_giveback_r >= 0.50).astype(np.float32)

    tel = tel.sort_values(["trade_key", "time"]).reset_index(drop=True)
    return tel


def make_samples(df: pd.DataFrame, seq_len: int = 32, step: int = 4):
    numeric_features = PATH + MARKET
    candidates = sorted(df.candidate.astype(str).unique().tolist())
    candidate_to_idx = {name: idx for idx, name in enumerate(candidates)}

    x = []
    mask = []
    candidate_idx = []
    y_delta = []
    y_hold = []
    y_protect = []
    meta = []

    for trade_key, group in df.groupby("trade_key", sort=False):
        group = group.sort_values("time").reset_index(drop=True)
        arr = (
            group[numeric_features]
            .astype(float)
            .replace([np.inf, -np.inf], np.nan)
            .ffill()
            .to_numpy(np.float32)
        )
        indices = list(range(1, len(group), max(1, step)))
        if len(group) > 1 and (len(group) - 1) not in indices:
            indices.append(len(group) - 1)
        if not indices:
            continue

        ci = candidate_to_idx[str(group.candidate.iloc[0])]
        for j in indices:
            start = max(0, j - seq_len + 1)
            seq = arr[start : j + 1]
            length = len(seq)
            pad = np.full((seq_len, len(numeric_features)), np.nan, dtype=np.float32)
            valid = np.zeros(seq_len, dtype=np.bool_)
            pad[:length] = seq
            valid[:length] = True
            row = group.iloc[j]
            x.append(pad)
            mask.append(valid)
            candidate_idx.append(ci)
            y_delta.append(float(row.future_delta_r))
            y_hold.append(float(row.hold_label))
            y_protect.append(float(row.protect_label))
            meta.append(
                {
                    "time": row.time,
                    "exit_time": row.exit_time,
                    "trade_key": trade_key,
                    "candidate": str(row.candidate),
                    "unrealized_r": float(row.unrealized_r),
                    "actual_final_r": float(row.final_r),
                }
            )

    if not x:
        raise RuntimeError("V36 produced zero sequence samples")
    return (
        np.asarray(x, dtype=np.float32),
        np.asarray(mask, dtype=np.bool_),
        np.asarray(candidate_idx, dtype=np.int64),
        np.asarray(y_delta, dtype=np.float32),
        np.asarray(y_hold, dtype=np.float32),
        np.asarray(y_protect, dtype=np.float32),
        meta,
        numeric_features,
        candidates,
    )


def safe_auc(y_true: np.ndarray, score: np.ndarray) -> float | None:
    if len(np.unique(y_true)) < 2:
        return None
    return float(roc_auc_score(y_true, score))


def safe_spearman(a: np.ndarray, b: np.ndarray) -> float | None:
    value = pd.Series(a).corr(pd.Series(b), method="spearman")
    return None if pd.isna(value) else float(value)


def train_eval(
    x_numeric,
    mask,
    candidate_idx,
    y_delta,
    y_hold,
    y_protect,
    meta,
    candidates,
    summary_path,
    pred_path,
    epochs=12,
):
    try:
        import torch
        import torch.nn as nn
        import torch.nn.functional as F
        from torch.nn.utils.rnn import pack_padded_sequence
        from torch.utils.data import DataLoader, TensorDataset
    except Exception as exc:
        raise RuntimeError("PyTorch required for V36 sequence models") from exc

    torch.manual_seed(2908)
    np.random.seed(2908)
    random.seed(2908)
    torch.set_num_threads(max(1, min(4, torch.get_num_threads())))

    times = pd.to_datetime([m["time"] for m in meta])
    exits = pd.to_datetime([m["exit_time"] for m in meta])
    current_r = np.asarray([m["unrealized_r"] for m in meta], dtype=np.float32)
    actual_final = np.asarray([m["actual_final_r"] for m in meta], dtype=np.float32)
    n_candidates = len(candidates)
    seq_len = x_numeric.shape[1]
    numeric_dim = x_numeric.shape[2]
    model_dim = numeric_dim + n_candidates + 1

    def make_fold_input(indices, mean, std):
        raw = x_numeric[indices]
        valid = mask[indices]
        scaled = (raw - mean) / std
        scaled[~valid] = 0.0
        scaled = np.nan_to_num(scaled, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
        onehot = np.zeros((len(indices), seq_len, n_candidates), dtype=np.float32)
        cis = candidate_idx[indices]
        for row_i, ci in enumerate(cis):
            onehot[row_i, valid[row_i], ci] = 1.0
        mask_channel = valid.astype(np.float32)[..., None]
        return np.concatenate([scaled, onehot, mask_channel], axis=2)

    class GRU(nn.Module):
        def __init__(self, dim):
            super().__init__()
            self.rnn = nn.GRU(dim, 48, batch_first=True)
            self.head = nn.Sequential(nn.Linear(48, 32), nn.ReLU(), nn.Linear(32, 3))

        def forward(self, xb, lengths, valid_mask):
            packed = pack_padded_sequence(
                xb, lengths.cpu(), batch_first=True, enforce_sorted=False
            )
            _, hidden = self.rnn(packed)
            return self.head(hidden[-1])

    class CausalTCN(nn.Module):
        def __init__(self, dim):
            super().__init__()
            self.inp = nn.Conv1d(dim, 48, 1)
            self.c1 = nn.Conv1d(48, 48, 3, dilation=1)
            self.c2 = nn.Conv1d(48, 48, 3, dilation=2)
            self.c3 = nn.Conv1d(48, 48, 3, dilation=4)
            self.head = nn.Sequential(nn.Linear(48, 32), nn.ReLU(), nn.Linear(32, 3))

        @staticmethod
        def causal(conv, z):
            pad = (conv.kernel_size[0] - 1) * conv.dilation[0]
            z = F.pad(z, (pad, 0))
            return F.relu(conv(z))

        def forward(self, xb, lengths, valid_mask):
            z = F.relu(self.inp(xb.transpose(1, 2)))
            z = self.causal(self.c1, z)
            z = self.causal(self.c2, z)
            z = self.causal(self.c3, z).transpose(1, 2)
            idx = (lengths - 1).clamp(min=0)
            h = z[torch.arange(z.size(0)), idx]
            return self.head(h)

    class Transformer(nn.Module):
        def __init__(self, dim):
            super().__init__()
            self.proj = nn.Linear(dim, 48)
            self.pos = nn.Parameter(torch.zeros(1, seq_len, 48))
            layer = nn.TransformerEncoderLayer(
                48, 4, 96, dropout=0.10, batch_first=True, activation="gelu"
            )
            self.encoder = nn.TransformerEncoder(layer, 2)
            self.head = nn.Sequential(nn.Linear(48, 32), nn.GELU(), nn.Linear(32, 3))

        def forward(self, xb, lengths, valid_mask):
            z = self.proj(xb) + self.pos
            causal_mask = torch.triu(
                torch.ones(seq_len, seq_len, dtype=torch.bool, device=xb.device),
                diagonal=1,
            )
            z = self.encoder(
                z,
                mask=causal_mask,
                src_key_padding_mask=~valid_mask,
            )
            idx = (lengths - 1).clamp(min=0)
            h = z[torch.arange(z.size(0)), idx]
            return self.head(h)

    model_classes = {"gru": GRU, "tcn": CausalTCN, "transformer": Transformer}
    predictions = []
    folds = []

    for test_start in pd.date_range("2026-02-01", "2026-07-01", freq="MS"):
        test_end = test_start + pd.offsets.MonthBegin(1)
        embargo_start = test_start - pd.offsets.MonthBegin(1)
        train_idx = np.where(exits < embargo_start)[0]
        test_idx = np.where((times >= test_start) & (times < test_end))[0]
        if len(train_idx) < 200 or len(test_idx) < 20:
            continue

        train_real = x_numeric[train_idx][mask[train_idx]]
        mean = np.nanmean(train_real, axis=0)
        std = np.nanstd(train_real, axis=0)
        mean = np.nan_to_num(mean, nan=0.0)
        std = np.nan_to_num(std, nan=1.0)
        std[std < 1e-6] = 1.0

        x_train = make_fold_input(train_idx, mean, std)
        x_test = make_fold_input(test_idx, mean, std)
        mask_train = mask[train_idx]
        mask_test = mask[test_idx]
        lengths_train = mask_train.sum(axis=1).astype(np.int64)
        lengths_test = mask_test.sum(axis=1).astype(np.int64)

        train_ds = TensorDataset(
            torch.tensor(x_train),
            torch.tensor(lengths_train),
            torch.tensor(mask_train),
            torch.tensor(y_delta[train_idx]),
            torch.tensor(y_hold[train_idx]),
            torch.tensor(y_protect[train_idx]),
        )
        loader = DataLoader(train_ds, batch_size=256, shuffle=True)

        hold_pos = float(y_hold[train_idx].sum())
        protect_pos = float(y_protect[train_idx].sum())
        hold_neg = float(len(train_idx) - hold_pos)
        protect_neg = float(len(train_idx) - protect_pos)
        hold_weight = torch.tensor(
            min(8.0, max(0.25, hold_neg / max(1.0, hold_pos))), dtype=torch.float32
        )
        protect_weight = torch.tensor(
            min(8.0, max(0.25, protect_neg / max(1.0, protect_pos))), dtype=torch.float32
        )
        hold_loss = nn.BCEWithLogitsLoss(pos_weight=hold_weight)
        protect_loss = nn.BCEWithLogitsLoss(pos_weight=protect_weight)
        delta_loss = nn.SmoothL1Loss(beta=0.50)

        for model_name, model_class in model_classes.items():
            torch.manual_seed(2908)
            model = model_class(model_dim)
            optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
            model.train()
            for _ in range(max(1, epochs)):
                for xb, lb, mb, db, hb, pb in loader:
                    out = model(xb, lb, mb)
                    loss = (
                        delta_loss(out[:, 0], db)
                        + 0.40 * hold_loss(out[:, 1], hb)
                        + 0.40 * protect_loss(out[:, 2], pb)
                    )
                    optimizer.zero_grad()
                    loss.backward()
                    nn.utils.clip_grad_norm_(model.parameters(), 2.0)
                    optimizer.step()

            model.eval()
            with torch.no_grad():
                out = model(
                    torch.tensor(x_test),
                    torch.tensor(lengths_test),
                    torch.tensor(mask_test),
                )
                pred_delta = out[:, 0].numpy()
                p_hold = torch.sigmoid(out[:, 1]).numpy()
                p_protect = torch.sigmoid(out[:, 2]).numpy()

            pred_final = current_r[test_idx] + pred_delta
            fold = {
                "month": test_start.strftime("%Y_%m"),
                "model": model_name,
                "train": int(len(train_idx)),
                "test": int(len(test_idx)),
                "future_delta_spearman": safe_spearman(pred_delta, y_delta[test_idx]),
                "final_r_spearman": safe_spearman(pred_final, actual_final[test_idx]),
                "hold_auc": safe_auc(y_hold[test_idx], p_hold),
                "protect_auc": safe_auc(y_protect[test_idx], p_protect),
            }
            folds.append(fold)

            for local_i, sample_i in enumerate(test_idx):
                predictions.append(
                    {
                        "month": test_start.strftime("%Y_%m"),
                        "model": model_name,
                        "time": str(times[sample_i]),
                        "trade_key": meta[sample_i]["trade_key"],
                        "candidate": meta[sample_i]["candidate"],
                        "unrealized_r": float(current_r[sample_i]),
                        "actual_final_r": float(actual_final[sample_i]),
                        "actual_future_delta_r": float(y_delta[sample_i]),
                        "actual_hold": float(y_hold[sample_i]),
                        "actual_protect": float(y_protect[sample_i]),
                        "pred_future_delta_r": float(pred_delta[local_i]),
                        "pred_final_r": float(pred_final[local_i]),
                        "p_hold": float(p_hold[local_i]),
                        "p_protect": float(p_protect[local_i]),
                    }
                )

    if not folds:
        raise RuntimeError("V36 produced no chronological folds")

    pred_df = pd.DataFrame(predictions)
    pred_df.to_csv(pred_path, index=False, lineterminator="\n")

    aggregate = {}
    for model_name in model_classes:
        rows = [row for row in folds if row["model"] == model_name]
        aggregate[model_name] = {}
        for metric in [
            "future_delta_spearman",
            "final_r_spearman",
            "hold_auc",
            "protect_auc",
        ]:
            values = [row[metric] for row in rows if row[metric] is not None]
            aggregate[model_name][metric] = (
                None if not values else float(np.mean(values))
            )
            if metric.endswith("auc"):
                aggregate[model_name][metric + "_months_gt_0p5"] = int(
                    sum(v > 0.5 for v in values)
                )
            else:
                aggregate[model_name][metric + "_months_gt_0"] = int(
                    sum(v > 0.0 for v in values)
                )

    output = {
        "schema": "v36_intra_trade_sequence_models_v2",
        "models": ["GRU48", "true_causal_TCN48", "Transformer48x2_positional_causal"],
        "sequence_len": int(seq_len),
        "numeric_features": PATH + MARKET,
        "candidate_context": candidates,
        "padding": "explicit mask; train statistics fit on real train timesteps only",
        "targets": [
            "future_incremental_realized_R_from_current_mark",
            "future_upside_ge_0p5R",
            "future_giveback_ge_0p5R",
        ],
        "folds": folds,
        "mean": aggregate,
        "decision_rule": (
            "diagnostic only; no reconstructed PnL. A bounded exit-policy hypothesis may be "
            "exported only if chronological sequence heads are stable; final economics require "
            "tester-only exact MT5 replay."
        ),
    }
    Path(summary_path).write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(aggregate, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--common-files", required=True)
    parser.add_argument("--v34-run-folder", required=True)
    parser.add_argument("--book", default="norm10k_r0p5_continuous")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--seq-len", type=int, default=32)
    parser.add_argument("--sample-step", type=int, default=4)
    args = parser.parse_args()

    prepared = prepare(Path(args.common_files), Path(args.v34_run_folder), args.book)
    (
        x,
        mask,
        candidate_idx,
        y_delta,
        y_hold,
        y_protect,
        meta,
        features,
        candidates,
    ) = make_samples(prepared, seq_len=args.seq_len, step=args.sample_step)
    print(
        "V36 dataset",
        x.shape,
        "numeric_features",
        len(features),
        "candidates",
        len(candidates),
        "telemetry_sha256",
        sha256(Path(args.v34_run_folder) / "intra_trade_m15.csv"),
    )
    train_eval(
        x,
        mask,
        candidate_idx,
        y_delta,
        y_hold,
        y_protect,
        meta,
        candidates,
        args.summary,
        args.predictions,
        epochs=args.epochs,
    )


if __name__ == "__main__":
    main()
