#!/usr/bin/env python3
"""Opportunity-duplication controls for V30 expected-R research.

Two mandatory controls for a multi-candidate catalog:
1) inverse multiplicity sample weights for repeated (entry_time, direction) trades;
2) unique-opportunity models with one row per (entry_time, direction).
Offline only; no broker or order path.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v30_trade_tournament_v2 as t

KEEP_TARGETS = (0.40, 0.50)


def load_trades(path: Path) -> pd.DataFrame:
    df = pd.read_pickle(path).copy()
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    df["exit_time"] = pd.to_datetime(df["exit_time"])
    df["direction_code"] = df["direction"].map({"LONG": 1.0, "SHORT": -1.0}).astype(float)
    return df


def duplicate_stats(df: pd.DataFrame) -> dict:
    g = df.groupby(["entry_time", "direction"]).size()
    return {
        "candidate_trades": int(len(df)),
        "unique_opportunities": int(len(g)),
        "mean_multiplicity": float(g.mean()),
        "duplicated_group_fraction": float((g > 1).mean()),
        "max_multiplicity": int(g.max()),
    }


def run_weighted(df: pd.DataFrame, output: Path) -> pd.DataFrame:
    cats = t.candidate_list(df)
    cols = t.numeric_columns(df, "engineered_expert")
    rows = []
    for cal_m, test_m in t.fold_months(df):
        cal_start = t.month_start(cal_m); test_start = t.month_start(test_m)
        train = df[df.exit_time < cal_start].copy()
        cal = df[(df.month.astype(str) == cal_m) & (df.exit_time < test_start)].copy()
        test = df[df.month.astype(str) == test_m].copy()
        if len(train) < t.MIN_TRAIN or len(cal) < t.MIN_CAL or len(test) < t.MIN_TEST:
            continue
        prep = t.fit_prep(train, cols, cats, True)
        xtr, xcal, xte = prep.transform(train), prep.transform(cal), prep.transform(test)
        multiplicity = train.groupby(["entry_time", "direction"])["candidate"].transform("size").to_numpy(float)
        weights = 1.0 / multiplicity
        weights /= weights.mean()
        model = t.regression_model("extratrees")
        model.fit(xtr, train.r_multiple.to_numpy(float), sample_weight=weights)
        pcal = model.predict(xcal); pte = model.predict(xte)
        for keep in KEEP_TARGETS:
            threshold = float(np.quantile(pcal, 1.0 - keep))
            selected = pte >= threshold
            rec = {
                "month": test_m, "cal_month": cal_m, "keep_target": keep,
                "weighting": "inverse_entry_time_direction_multiplicity",
                "candidate_threshold": False, "train_n": len(train), "cal_n": len(cal),
                "train_unique_opportunities": int(train.groupby(["entry_time", "direction"]).ngroups),
                "global_threshold": threshold,
            }
            rec.update(t.test_metrics(test, pte, selected)); rows.append(rec)
    out = pd.DataFrame(rows)
    out.to_csv(output, index=False)
    return out


def build_groups(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    barcols = [c for c in t.numeric_columns(df, "engineered_expert") if c.startswith("bar__")]
    agg = {"month": "first", "exit_time": "max", "r_multiple": ["mean", "median", "count"]}
    for c in barcols:
        agg[c] = "first"
    g = df.groupby(["entry_time", "direction", "direction_code"], as_index=False).agg(agg)
    names = []
    for col in g.columns:
        if isinstance(col, tuple):
            if col[0] == "r_multiple":
                names.append({"mean": "target_mean_r", "median": "target_median_r", "count": "group_size"}[col[1]])
            else:
                names.append(col[0])
        else:
            names.append(col)
    g.columns = names
    g = g.rename(columns={"exit_time": "max_exit_time"})
    g["month"] = g["month"].astype(str)
    return g, barcols + ["direction_code"]


def run_unique_group(df: pd.DataFrame, output: Path) -> pd.DataFrame:
    groups, cols = build_groups(df)
    rows = []
    for model_name in ("extratrees", "histgb"):
        for cal_m, test_m in t.fold_months(groups):
            cal_start = t.month_start(cal_m); test_start = t.month_start(test_m)
            train = groups[groups.max_exit_time < cal_start].copy()
            cal = groups[(groups.month == cal_m) & (groups.max_exit_time < test_start)].copy()
            test = groups[groups.month == test_m].copy()
            if len(train) < 300 or len(cal) < 20 or len(test) < 20:
                continue
            prep = t.fit_prep(train, cols, [], False)
            model = t.regression_model(model_name)
            model.fit(prep.transform(train), train.target_mean_r.to_numpy(float))
            pcal = model.predict(prep.transform(cal)); pte = model.predict(prep.transform(test))
            for keep in KEEP_TARGETS:
                threshold = float(np.quantile(pcal, 1.0 - keep)); selected = pte >= threshold
                y = test.target_mean_r.to_numpy(float)
                rec = {
                    "model": model_name, "month": test_m, "cal_month": cal_m, "keep_target": keep,
                    "n_groups": len(test), "selected_groups": int(selected.sum()),
                    "group_coverage": float(selected.mean()), "group_base_avg_r": float(y.mean()),
                    "group_sel_avg_r": float(y[selected].mean()) if selected.any() else np.nan,
                    "group_spearman": float(pd.Series(y).corr(pd.Series(pte), method="spearman")),
                }
                keys = test[["entry_time", "direction"]].copy(); keys["selected"] = selected.astype(int)
                tt = df[df.month.astype(str) == test_m].merge(keys, on=["entry_time", "direction"], how="inner")
                predmap = dict(zip(zip(test.entry_time, test.direction), pte))
                tt["pred_r"] = [predmap[(x, ydir)] for x, ydir in zip(tt.entry_time, tt.direction)]
                rec.update(t.test_metrics(tt, tt.pred_r.to_numpy(float), tt.selected.to_numpy(bool)))
                rows.append(rec)
    out = pd.DataFrame(rows)
    out.to_csv(output, index=False)
    return out


def summarize(df: pd.DataFrame, keys: list[str]) -> dict:
    result = {}
    for key, g in df.groupby(keys):
        if not isinstance(key, tuple): key = (key,)
        result["|".join(map(str, key))] = t.summarize_variant(g)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("trade_pickle", type=Path)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args(); args.output_dir.mkdir(parents=True, exist_ok=True)
    df = load_trades(args.trade_pickle)
    weighted = run_weighted(df, args.output_dir / "extratrees_weighted_robustness.csv")
    grouped = run_unique_group(df, args.output_dir / "group_opportunity_models.csv")
    payload = {
        "duplicate_stats_all": duplicate_stats(df),
        "duplicate_stats_oos": duplicate_stats(df[df.month.astype(str) >= "2025_08"]),
        "weighted": summarize(weighted, ["keep_target"]),
        "unique_group": summarize(grouped, ["model", "keep_target"]),
    }
    (args.output_dir / "opportunity_weighting_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
