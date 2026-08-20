#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from dataclasses import dataclass

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVR

CANDIDATES = [
    "ema_h1_skip20",
    "macd_h1_gap10",
    "bos_fvg_h1_gap8",
    "trend20_h1_gap5",
    "router_ema_bos8",
    "slow_mom_16h24h_timebox8h",
    "slow_mom_16h24h_peaklock_timebox8h",
    "adaptive_ewma_hl8_thr0",
    "adaptive_ewma_hl8_thr0p05",
    "adaptive_ewma_hl10_thr0p05",
    "adaptive_ewma_hl12_thr0p05",
    "adaptive_cp_fast5_slow20_thr0p30",
]
BOOK = "usd40_r1p0_cent"
TEST_MONTHS = pd.period_range("2025-08", "2026-07", freq="M")
RAW_CONSTANT_HINTS = {
    "real_volume", "tick_agg_ready", "mtf_ready", "spread_bad", "bb_rsi_dir"
}

@dataclass
class Chunk:
    start: pd.Timestamp
    end: pd.Timestamp
    run_id: str

CHUNKS = [
    Chunk(pd.Timestamp("2025-02-01"), pd.Timestamp("2025-08-01"), "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-02-01_00-00-00__756375"),
    Chunk(pd.Timestamp("2025-08-01"), pd.Timestamp("2026-02-01"), "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-08-01_00-00-00__22265"),
    Chunk(pd.Timestamp("2026-02-01"), pd.Timestamp("2026-08-01"), "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2026-02-01_00-00-00__519093"),
]


def _sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dt(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s.astype(str), format="%Y.%m.%d %H:%M:%S", errors="raise")


def find_run(common: pathlib.Path, run_id: str) -> pathlib.Path:
    runs = common / "mt5_quant" / "runs"
    exact = runs / run_id
    if exact.is_dir():
        return exact
    hits = [p for p in runs.glob(f"{run_id}*") if p.is_dir()]
    if len(hits) != 1:
        raise RuntimeError(f"cannot resolve run_id={run_id}; matches={len(hits)}")
    return hits[0]


def load_lake(common: pathlib.Path):
    bars=[]; trades=[]
    schemas=[]
    for ch in CHUNKS:
        rd=find_run(common,ch.run_id)
        bp=rd/"bar_features.csv"; tp=rd/"trades.csv"
        if not bp.is_file() or not tp.is_file():
            raise RuntimeError(f"missing V30 files in {rd}")
        b=pd.read_csv(bp); t=pd.read_csv(tp)
        schemas.append(tuple(b.columns))
        b["time"]=_dt(b["time"])
        b=b[(b["time"]>=ch.start)&(b["time"]<ch.end)].copy()
        bars.append(b)
        t["entry_time"]=_dt(t["entry_time"]); t["exit_time"]=_dt(t["exit_time"])
        trades.append(t)
    if len(set(schemas))!=1: raise RuntimeError("bar schemas differ across chunks")
    bars=pd.concat(bars,ignore_index=True).sort_values("time").reset_index(drop=True)
    trades=pd.concat(trades,ignore_index=True)
    if len(bars)!=35344 or bars["time"].duplicated().any():
        raise RuntimeError(f"unexpected canonical lake shape/duplicates: {len(bars)}")
    bars["feature_available_time"]=bars["time"]+pd.Timedelta(minutes=15)
    return bars,trades


def engineer_bars(b: pd.DataFrame) -> pd.DataFrame:
    x=b.copy()
    # Compact causal expert-change state.
    for e in range(5):
        for a,bn,new in [
            (f"expert{e}_fast5",f"expert{e}_slow20",f"expert{e}_fast_minus_slow"),
            (f"expert{e}_hl8",f"expert{e}_slow20",f"expert{e}_hl8_minus_slow"),
            (f"expert{e}_fast5",f"expert{e}_hl8",f"expert{e}_fast_minus_hl8"),
        ]:
            if a in x.columns and bn in x.columns: x[new]=x[a]-x[bn]
        obs=f"expert{e}_obs"
        if obs in x.columns: x[f"expert{e}_obs_log1p"]=np.log1p(x[obs].clip(lower=0))
    if {f"expert{e}_fast5" for e in range(5)}.issubset(x.columns):
        c=[f"expert{e}_fast5" for e in range(5)]
        x["expert_fast_mean"]=x[c].mean(axis=1); x["expert_fast_std"]=x[c].std(axis=1,ddof=0)
        for e in range(5): x[f"expert{e}_fast_relative"]=x[f"expert{e}_fast5"]-x["expert_fast_mean"]
    if "rv8" in x.columns and "rv32" in x.columns: x["rv8_over_rv32"]=x["rv8"]/(x["rv32"].abs()+1e-9)
    if "plus_di" in x.columns and "minus_di" in x.columns: x["di_spread"]=x["plus_di"]-x["minus_di"]
    if "macd_hist" in x.columns and "atr14" in x.columns: x["macd_hist_atr"]=x["macd_hist"]/(x["atr14"].abs()+1e-9)
    if "m1_range" in x.columns and "atr14" in x.columns: x["m1_range_atr"]=x["m1_range"]/(x["atr14"].abs()+1e-9)
    if "m5_range" in x.columns and "atr14" in x.columns: x["m5_range_atr"]=x["m5_range"]/(x["atr14"].abs()+1e-9)
    if "server_hour" in x.columns:
        h=x["server_hour"].astype(float); x["hour_sin"]=np.sin(2*np.pi*h/24); x["hour_cos"]=np.cos(2*np.pi*h/24)
    if "day_of_week" in x.columns:
        d=x["day_of_week"].astype(float); x["dow_sin"]=np.sin(2*np.pi*d/7); x["dow_cos"]=np.cos(2*np.pi*d/7)
    return x


def make_trade_samples(bars: pd.DataFrame,trades: pd.DataFrame):
    t=trades[trades["book"]==BOOK].copy().sort_values("entry_time").reset_index(drop=True)
    # Strict causal asof on feature availability.
    b=bars.sort_values("feature_available_time").copy()
    joined=pd.merge_asof(t,b,left_on="entry_time",right_on="feature_available_time",direction="backward",allow_exact_matches=True,suffixes=("_trade","_bar"))
    if joined["time"].isna().any(): raise RuntimeError("causal join left missing rows")
    if (joined["feature_available_time"]>joined["entry_time"]).any(): raise RuntimeError("causal join violation")
    # Duplicate opportunity weighting.
    mult=joined.groupby(["entry_time","direction"])["candidate"].transform("count").astype(float)
    joined["sample_weight"]=1.0/mult
    return joined


def feature_columns(df: pd.DataFrame):
    deny={
        "time","feature_available_time","entry_time","exit_time","candidate","book","month","r_multiple","net_pnl","pnl","direction",
        "entry_price","exit_price","entry","exit","volume","risk_cash","initial_risk_cash","exit_reason","signal_sources","policy_name","family",
    }
    cols=[]
    for c in df.columns:
        if c in deny or c in RAW_CONSTANT_HINTS: continue
        if c.endswith("_ready"): continue
        if c.startswith("target_") or c.startswith("label_") or c.startswith("future_"): continue
        if pd.api.types.is_numeric_dtype(df[c]):
            v=df[c]
            if v.notna().sum()==0 or v.nunique(dropna=True)<=1: continue
            cols.append(c)
    return cols


def add_static(df: pd.DataFrame,base_cols:list[str]):
    out=df[base_cols].copy()
    out["direction_static"]=df["direction"].astype(float)
    for i,c in enumerate(CANDIDATES): out[f"cand_{i}"]=(df["candidate"]==c).astype(float)
    return out


def models(seed=20260820):
    return {
        "catboost": CatBoostRegressor(iterations=220,depth=5,learning_rate=0.035,loss_function="RMSE",random_seed=seed,verbose=False,thread_count=-1,l2_leaf_reg=5),
        "extratrees": ExtraTreesRegressor(n_estimators=320,max_depth=9,min_samples_leaf=8,max_features=0.72,random_state=seed,n_jobs=-1),
        "mlp_32_16": make_pipeline(StandardScaler(),MLPRegressor(hidden_layer_sizes=(32,16),alpha=0.02,learning_rate_init=0.001,max_iter=260,early_stopping=True,validation_fraction=0.15,n_iter_no_change=20,random_state=seed)),
        "linear_svr": make_pipeline(StandardScaler(),LinearSVR(C=0.03,epsilon=0.05,loss="squared_epsilon_insensitive",max_iter=12000,random_state=seed)),
    }


def fit_model(name,model,X,y,w):
    if name=="catboost": model.fit(X,y,sample_weight=w)
    elif name=="extratrees": model.fit(X,y,sample_weight=w)
    else:
        # sklearn pipelines used here do not route sample_weight consistently across all target versions; duplicate control is enforced by deterministic weighted resampling.
        rng=np.random.default_rng(20260820)
        p=w/np.sum(w); n=len(X)
        idx=rng.choice(np.arange(n),size=n,replace=True,p=p)
        model.fit(X.iloc[idx],y.iloc[idx])
    return model


def build(common:pathlib.Path,out:pathlib.Path,metadata:pathlib.Path|None):
    bars,trades=load_lake(common)
    bars=engineer_bars(bars)
    ts=make_trade_samples(bars,trades)
    base_cols=feature_columns(bars)
    # Keep only fields that survived join and are numeric.
    base_cols=[c for c in base_cols if c in ts.columns and pd.api.types.is_numeric_dtype(ts[c])]
    if len(base_cols)<40: raise RuntimeError(f"unexpectedly small feature set: {len(base_cols)}")
    rows=[]; month_meta=[]
    for tm in TEST_MONTHS:
        test_start=tm.to_timestamp(); test_end=(tm+1).to_timestamp(); cal=(tm-1)
        cal_start=cal.to_timestamp(); cal_end=(cal+1).to_timestamp()
        train=ts[ts["exit_time"]<cal_start].copy()
        caldf=ts[(ts["entry_time"]>=cal_start)&(ts["entry_time"]<cal_end)].copy()
        if train.empty or caldf.empty: raise RuntimeError(f"empty train/cal for {tm}")
        Xtr=add_static(train,base_cols); ytr=train["r_multiple"].astype(float); w=train["sample_weight"].astype(float)
        Xcal=add_static(caldf,base_cols)
        fitted={}; thresholds={}
        for name,m in models().items():
            fitted[name]=fit_model(name,m,Xtr,ytr,w)
            pred=fitted[name].predict(Xcal)
            thresholds[name]=float(np.median(pred))
        # Every canonical bar in test month, every candidate, both directions.
        mb=bars[(bars["time"]>=test_start)&(bars["time"]<test_end)].copy()
        # Gate is evaluated at r[0].time; score state available at same bar start is the previous closed bar.
        avail=bars[["time","feature_available_time"]+base_cols].copy().sort_values("feature_available_time")
        q=pd.DataFrame({"bar_time":mb["time"].values}).sort_values("bar_time")
        q=pd.merge_asof(q,avail,left_on="bar_time",right_on="feature_available_time",direction="backward",allow_exact_matches=True)
        if q[base_cols].isna().any().any(): raise RuntimeError(f"missing causal state for month {tm}")
        for _,br in q.iterrows():
            vals=[br["bar_time"].strftime("%Y.%m.%d %H:%M:%S")]
            for ci,cand in enumerate(CANDIDATES):
                masks=[]
                for direction in (1,-1):
                    X=pd.DataFrame([{c:br[c] for c in base_cols}])
                    X["direction_static"]=float(direction)
                    for i,_c in enumerate(CANDIDATES): X[f"cand_{i}"]=float(i==ci)
                    preds={n:float(fitted[n].predict(X)[0]) for n in fitted}
                    bits=0
                    pass0=preds["catboost"]>=thresholds["catboost"]
                    pass1=preds["extratrees"]>=thresholds["extratrees"]
                    pass2=preds["mlp_32_16"]>=thresholds["mlp_32_16"]
                    pass3=preds["linear_svr"]>=thresholds["linear_svr"]
                    for bit,p in enumerate((pass0,pass1,pass2,pass3)):
                        if p: bits|=(1<<bit)
                    if pass0 and pass1: bits|=(1<<4)
                    if sum((pass0,pass1,pass2,pass3))>=2: bits|=(1<<5)
                    masks.append(bits)
                vals += masks
            rows.append(vals)
        month_meta.append({
            "test_month":str(tm).replace("-","_"),"calibration_month":str(cal).replace("-","_"),
            "thresholds":thresholds,"train_rows":int(len(train)),"cal_rows":int(len(caldf)),"bars":int(len(q))
        })
    columns=["bar_time"]
    for c in CANDIDATES: columns += [f"{c}__long_mask",f"{c}__short_mask"]
    tape=pd.DataFrame(rows,columns=columns)
    if len(tape)!=23616: raise RuntimeError(f"unexpected tape rows {len(tape)}")
    out.parent.mkdir(parents=True,exist_ok=True); tape.to_csv(out,index=False,line_terminator="\n" if False else None)
    h=_sha(out)
    meta={"models_bits":{"0":"catboost","1":"extratrees","2":"mlp_32_16","3":"linear_svr","4":"catboost_AND_extratrees","5":"majority_2of4"},"candidate_order":CANDIDATES,"months":month_meta,"feature_count":len(base_cols),"protocol":"fit exits before prior calibration month; threshold=median prior-month scores; inverse opportunity weighting; score every bar/candidate/direction causally","tape_rows":len(tape),"tape_sha256":h}
    if metadata:
        metadata.parent.mkdir(parents=True,exist_ok=True); metadata.write_text(json.dumps(meta,indent=2)+"\n",encoding="utf-8")
    print(f"V31 tape PASS rows={len(tape)} features={len(base_cols)} sha256={h} path={out}")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--common-files",required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--metadata")
    a=ap.parse_args()
    build(pathlib.Path(a.common_files),pathlib.Path(a.output),pathlib.Path(a.metadata) if a.metadata else None)

if __name__=="__main__": main()
