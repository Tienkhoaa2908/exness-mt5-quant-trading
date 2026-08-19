#!/usr/bin/env python3
"""Strict causal V30 trade expected-R tournament.

Protocol
--------
For each OOS test month after a six-month warm-up:
* immediately previous month is score-calibration month;
* the model is trained only on trades whose exit is strictly before calibration-month start;
* calibration labels are NOT used; only the frozen model's score distribution is used;
* threshold = 60th percentile of calibration scores (target ~40% turnover);
* the frozen model + absolute threshold is then applied to the next test month.

This deliberately uses a one-month-stale model to make threshold calibration fully
causal and avoid test-month quantile peeking.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
import random
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, HistGradientBoostingClassifier, ExtraTreesClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.metrics import roc_auc_score, mean_absolute_error
from sklearn.neural_network import MLPRegressor

SEED = 29
TARGET_KEEP = 0.40
CAL_QUANTILE = 1.0 - TARGET_KEEP
TAIL_CUTOFF = -0.95
MIN_TRAIN = 1000
MIN_CAL = 80
MIN_TEST = 80
MIN_CANDIDATE_CAL = 12


def seed_all(seed: int = SEED):
    random.seed(seed)
    np.random.seed(seed)


def month_start(month: str) -> pd.Timestamp:
    return pd.Timestamp(month.replace("_", "-") + "-01")


def candidate_list(df: pd.DataFrame) -> list[str]:
    return sorted(df["candidate"].astype(str).unique().tolist())


def numeric_columns(df: pd.DataFrame, feature_set: str) -> list[str]:
    bar = [c for c in df.columns if c.startswith("bar__") and pd.api.types.is_numeric_dtype(df[c])]
    static = [
        "direction_code", "entered_after_profit_exit", "entry_gap_bars", "entry_quality_score",
        "entry_adx", "entry_plus_di", "entry_minus_di", "entry_atr_ratio",
        "entry_body_ratio", "entry_close_location", "entry_dist_ema200_atr",
        "entry_rsi2", "entry_rsi14", "entry_macd_hist", "entry_h1_gap_atr",
        "entry_server_hour", "entry_profit_streak_before", "entry_bars_since_exit",
        "adaptive_mode",
    ]
    static = [c for c in static if c in df.columns]
    drop_exact = {
        "bar__atr14", "bar__atr50", "bar__macd_main", "bar__macd_signal",
        "bar__bar_spread_points", "bar__live_spread_points",
        "bar__server_hour", "bar__day_of_week",
    }
    base = [c for c in bar if c not in drop_exact]
    base = [c for c in base if not c.startswith("bar__expert_obs_")]
    base = [c for c in base if not c.startswith("bar__expert_obs_log1p_")]
    is_expert = lambda c: (c.startswith("bar__ewma_") or c.startswith("bar__expert_"))
    market = [c for c in base if not is_expert(c)]
    if feature_set == "market_only":
        return market + static
    if feature_set == "raw_expert":
        raw_keep = []
        for c in base:
            if not is_expert(c):
                continue
            if c.startswith("bar__ewma_fast5_") or c.startswith("bar__ewma_slow20_") or c.startswith("bar__ewma_hl8_"):
                raw_keep.append(c)
            elif c.startswith("bar__expert_confidence_"):
                raw_keep.append(c)
        return market + raw_keep + static
    if feature_set == "engineered_expert":
        eng_keep = []
        for c in base:
            if not is_expert(c):
                continue
            keep_prefixes = (
                "bar__ewma_fast5_", "bar__ewma_slow20_",
                "bar__expert_fast_minus_slow_", "bar__expert_hl8_minus_slow_",
                "bar__expert_fast_minus_hl8_", "bar__expert_change_conf_",
                "bar__expert_confidence_", "bar__expert_fast_mean", "bar__expert_fast_std",
                "bar__expert_slow_mean", "bar__expert_slow_std", "bar__expert_change_mean",
                "bar__expert_change_abs_mean", "bar__expert_change_std",
                "bar__expert_fast_rel_", "bar__expert_slow_rel_",
            )
            if c.startswith(keep_prefixes):
                eng_keep.append(c)
        return market + eng_keep + static
    raise ValueError(feature_set)


@dataclass
class FoldPrep:
    cols: list[str]
    mean: np.ndarray
    std: np.ndarray
    lo: np.ndarray
    hi: np.ndarray
    categories: list[str]
    candidate_aware: bool

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        x = df[self.cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float64)
        x = np.where(np.isfinite(x), x, self.mean)
        x = np.minimum(np.maximum(x, self.lo), self.hi)
        x = (x - self.mean) / self.std
        if self.candidate_aware:
            mapping = {c: i for i, c in enumerate(self.categories)}
            oh = np.zeros((len(df), len(self.categories)), dtype=np.float64)
            for r, c in enumerate(df["candidate"].astype(str).tolist()):
                if c in mapping:
                    oh[r, mapping[c]] = 1.0
            x = np.concatenate([x, oh], axis=1)
        return x.astype(np.float32)


def fit_prep(train: pd.DataFrame, cols: list[str], categories: list[str], candidate_aware: bool) -> FoldPrep:
    x = train[cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float64)
    med = np.nanmedian(x, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    x = np.where(np.isfinite(x), x, med)
    lo = np.quantile(x, 0.005, axis=0)
    hi = np.quantile(x, 0.995, axis=0)
    xw = np.minimum(np.maximum(x, lo), hi)
    mean = xw.mean(axis=0)
    std = xw.std(axis=0)
    std = np.where(std > 1e-8, std, 1.0)
    return FoldPrep(cols, mean, std, lo, hi, categories, candidate_aware)


def regression_model(name: str):
    if name == "ridge":
        return Ridge(alpha=12.0)
    if name == "histgb":
        return HistGradientBoostingRegressor(max_iter=220, learning_rate=0.04, max_leaf_nodes=15, min_samples_leaf=25, l2_regularization=2.0, early_stopping=False, random_state=SEED)
    if name == "extratrees":
        return ExtraTreesRegressor(n_estimators=80, min_samples_leaf=12, max_features=0.65, n_jobs=-1, random_state=SEED)
    if name == "mlp":
        return MLPRegressor(hidden_layer_sizes=(48, 24), activation="relu", alpha=2e-3, learning_rate_init=7e-4, max_iter=140, early_stopping=False, random_state=SEED)
    raise ValueError(name)


def tail_model(name: str):
    if name == "logistic":
        return LogisticRegression(max_iter=2500, C=0.35, class_weight="balanced", random_state=SEED)
    if name == "histgb":
        return HistGradientBoostingClassifier(max_iter=180, learning_rate=0.04, max_leaf_nodes=15, min_samples_leaf=25, l2_regularization=2.0, early_stopping=False, random_state=SEED)
    if name == "extratrees":
        return ExtraTreesClassifier(n_estimators=80, min_samples_leaf=12, max_features=0.65, n_jobs=-1, class_weight="balanced", random_state=SEED)
    raise ValueError(name)


def score_thresholds(cal: pd.DataFrame, scores: np.ndarray, by_candidate: bool) -> dict[str, float]:
    global_thr = float(np.quantile(scores, CAL_QUANTILE))
    thresholds = {"__global__": global_thr}
    if by_candidate:
        tmp = cal[["candidate"]].copy(); tmp["score"] = scores
        for cand, g in tmp.groupby("candidate"):
            if len(g) >= MIN_CANDIDATE_CAL:
                thresholds[str(cand)] = float(g["score"].quantile(CAL_QUANTILE))
    return thresholds


def apply_threshold(df: pd.DataFrame, scores: np.ndarray, thresholds: dict[str, float], by_candidate: bool) -> np.ndarray:
    if not by_candidate:
        return scores >= thresholds["__global__"]
    out = np.zeros(len(df), dtype=bool)
    for i, cand in enumerate(df["candidate"].astype(str).tolist()):
        out[i] = scores[i] >= thresholds.get(cand, thresholds["__global__"])
    return out


def fold_months(df: pd.DataFrame, warmup_months: int = 6):
    months = sorted(df["month"].astype(str).unique().tolist())
    for i in range(warmup_months, len(months)):
        yield months[i - 1], months[i]


def test_metrics(test: pd.DataFrame, pred: np.ndarray, selected: np.ndarray) -> dict:
    y = test["r_multiple"].to_numpy(dtype=float); tail = y <= TAIL_CUTOFF; n = len(y); sel_n = int(selected.sum())
    rec = {
        "n": n, "selected_n": sel_n, "coverage": sel_n / n if n else np.nan,
        "baseline_avg_r": float(np.mean(y)) if n else np.nan, "baseline_sum_r": float(np.sum(y)) if n else np.nan,
        "baseline_win_rate": float(np.mean(y > 0)) if n else np.nan, "baseline_tail_rate": float(np.mean(tail)) if n else np.nan,
        "pred_spearman": float(spearmanr(y, pred).statistic) if n > 2 else np.nan,
        "pred_mae": float(mean_absolute_error(y, pred)) if n else np.nan,
    }
    if sel_n:
        ys = y[selected]
        rec.update({"selected_avg_r": float(np.mean(ys)), "selected_sum_r": float(np.sum(ys)), "selected_win_rate": float(np.mean(ys > 0)), "selected_tail_rate": float(np.mean(ys <= TAIL_CUTOFF)), "avg_r_uplift": float(np.mean(ys) - np.mean(y)), "sum_r_retention": float(np.sum(ys) / np.sum(y)) if abs(np.sum(y)) > 1e-12 else np.nan})
    else:
        rec.update({"selected_avg_r": np.nan, "selected_sum_r": 0.0, "selected_win_rate": np.nan, "selected_tail_rate": np.nan, "avg_r_uplift": np.nan, "sum_r_retention": 0.0})
    return rec


def run_regression_variant(df: pd.DataFrame, feature_set: str, model_name: str, candidate_aware: bool, candidate_threshold: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    cats = candidate_list(df); cols = numeric_columns(df, feature_set); rows, cand_rows = [], []
    for cal_m, test_m in fold_months(df):
        cal_start = month_start(cal_m); test_start = month_start(test_m)
        train = df.loc[df["exit_time"] < cal_start].copy()
        cal = df.loc[(df["month"].astype(str) == cal_m) & (df["exit_time"] < test_start)].copy()
        test = df.loc[df["month"].astype(str) == test_m].copy()
        if len(train) < MIN_TRAIN or len(cal) < MIN_CAL or len(test) < MIN_TEST: continue
        prep = fit_prep(train, cols, cats, candidate_aware)
        Xtr, Xcal, Xte = prep.transform(train), prep.transform(cal), prep.transform(test)
        ytr = train["r_multiple"].to_numpy(dtype=float); seed_all()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore"); model = regression_model(model_name); model.fit(Xtr, ytr)
        pcal = np.asarray(model.predict(Xcal), dtype=float); pte = np.asarray(model.predict(Xte), dtype=float)
        th = score_thresholds(cal, pcal, candidate_threshold); sel = apply_threshold(test, pte, th, candidate_threshold)
        rec = {"cal_month": cal_m, "month": test_m, "model": model_name, "feature_set": feature_set, "candidate_aware": candidate_aware, "candidate_threshold": candidate_threshold, "train_n": len(train), "cal_n": len(cal), "global_threshold": th["__global__"]}
        rec.update(test_metrics(test, pte, sel)); rows.append(rec)
        tt = test[["candidate", "r_multiple"]].copy(); tt["pred"] = pte; tt["selected"] = sel
        for cand, g in tt.groupby("candidate"):
            yy = g["r_multiple"].to_numpy(dtype=float); ss = g["selected"].to_numpy(dtype=bool)
            cand_rows.append({"month": test_m, "model": model_name, "feature_set": feature_set, "candidate_aware": candidate_aware, "candidate_threshold": candidate_threshold, "candidate": cand, "n": len(g), "selected_n": int(ss.sum()), "coverage": float(ss.mean()), "baseline_avg_r": float(yy.mean()), "selected_avg_r": float(yy[ss].mean()) if ss.any() else np.nan, "baseline_sum_r": float(yy.sum()), "selected_sum_r": float(yy[ss].sum()) if ss.any() else 0.0})
    return pd.DataFrame(rows), pd.DataFrame(cand_rows)


def run_tail_classification(df: pd.DataFrame, feature_set: str, model_name: str, candidate_aware: bool) -> pd.DataFrame:
    cats = candidate_list(df); cols = numeric_columns(df, feature_set); rows=[]
    for cal_m, test_m in fold_months(df):
        cal_start=month_start(cal_m); train=df.loc[df["exit_time"]<cal_start].copy(); test=df.loc[df["month"].astype(str)==test_m].copy()
        if len(train)<MIN_TRAIN or len(test)<MIN_TEST: continue
        prep=fit_prep(train,cols,cats,candidate_aware); Xtr=prep.transform(train); Xte=prep.transform(test)
        ytr=(train["r_multiple"].to_numpy(float)<=TAIL_CUTOFF).astype(int); yte=(test["r_multiple"].to_numpy(float)<=TAIL_CUTOFF).astype(int)
        model=tail_model(model_name); model.fit(Xtr,ytr); pp=model.predict_proba(Xte)[:,1]
        rows.append({"month":test_m,"model":model_name,"feature_set":feature_set,"candidate_aware":candidate_aware,"n":len(test),"auc":float(roc_auc_score(yte,pp)) if len(np.unique(yte))>1 else np.nan})
    return pd.DataFrame(rows)


def bootstrap_month_uplift(monthly: pd.DataFrame, iters: int = 20000) -> dict:
    v = monthly["avg_r_uplift"].dropna().to_numpy(dtype=float)
    if len(v)==0: return {}
    rng=np.random.default_rng(SEED); draws=rng.choice(v,size=(iters,len(v)),replace=True).mean(axis=1)
    return {"months":int(len(v)), "mean_uplift":float(v.mean()), "ci95_low":float(np.quantile(draws,0.025)), "ci95_high":float(np.quantile(draws,0.975))}


def summarize_variant(m: pd.DataFrame) -> dict:
    if m.empty: return {}
    base_n=int(m["n"].sum()); sel_n=int(m["selected_n"].sum()); base_sum=float(m["baseline_sum_r"].sum()); sel_sum=float(m["selected_sum_r"].sum())
    return {"months":int(len(m)), "baseline_n":base_n, "selected_n":sel_n, "coverage":sel_n/base_n, "baseline_avg_r":base_sum/base_n, "selected_avg_r":sel_sum/sel_n if sel_n else None, "baseline_sum_r":base_sum,"selected_sum_r":sel_sum, "sum_r_retention":sel_sum/base_sum if abs(base_sum)>1e-12 else None, "positive_selected_months":int((m["selected_sum_r"]>0).sum()), "worst_selected_avg_r":float(m["selected_avg_r"].min(skipna=True)), "mean_monthly_spearman":float(m["pred_spearman"].mean()), "bootstrap_avg_r_uplift":bootstrap_month_uplift(m)}


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("trade_pickle",type=Path); ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args(); seed_all(); df=pd.read_pickle(args.trade_pickle).copy()
    df["entry_time"]=pd.to_datetime(df["entry_time"]); df["exit_time"]=pd.to_datetime(df["exit_time"]); df["direction_code"] = df["direction"].map({"LONG": 1.0, "SHORT": -1.0}).astype(float)
    args.output.mkdir(parents=True,exist_ok=True)
    runs=[]; cand=[]
    specs=[("market_only","ridge",False,True),("raw_expert","ridge",False,True),("engineered_expert","ridge",False,True),("engineered_expert","histgb",False,True),("engineered_expert","extratrees",False,True),("engineered_expert","ridge",True,True),("engineered_expert","histgb",True,True),("engineered_expert","extratrees",True,True)]
    for fs,m,aware,ct in specs:
        mm,cc=run_regression_variant(df,fs,m,aware,ct); runs.append(mm); cand.append(cc)
    monthly=pd.concat(runs,ignore_index=True); cands=pd.concat(cand,ignore_index=True)
    monthly.to_csv(args.output/"tabular_expected_r_monthly.csv",index=False); cands.to_csv(args.output/"tabular_expected_r_candidate_monthly.csv",index=False)
    tail=[]
    for m in ("logistic","histgb","extratrees"): tail.append(run_tail_classification(df,"engineered_expert",m,True))
    taildf=pd.concat(tail,ignore_index=True); taildf.to_csv(args.output/"tabular_tail_loss_monthly.csv",index=False)
    summaries={}; groupcols=["model","feature_set","candidate_aware","candidate_threshold"]
    for key,g in monthly.groupby(groupcols,dropna=False): summaries["|".join(map(str,key))]=summarize_variant(g)
    tail_summary={}
    for key,g in taildf.groupby(["model","feature_set","candidate_aware"]): tail_summary["|".join(map(str,key))]={"months":len(g),"mean_auc":float(g["auc"].mean()),"median_auc":float(g["auc"].median())}
    payload={"protocol":{"warmup_months":6,"calibration_month":"previous month","train_label_cutoff":"exit_time < calibration_month_start","calibration_labels_used":False,"score_threshold_quantile":CAL_QUANTILE,"target_keep_fraction":TARGET_KEEP,"candidate_threshold_min_cal_n":MIN_CANDIDATE_CAL,"tail_cutoff_r":TAIL_CUTOFF},"expected_r":summaries,"tail_loss":tail_summary}
    (args.output/"tabular_tournament_summary.json").write_text(json.dumps(payload,indent=2),encoding="utf-8"); print(json.dumps(payload,indent=2)); return 0

if __name__=="__main__":
    raise SystemExit(main())
