#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

CONTROL = "adaptive_ewma_hl8_thr0"
BOOK = "usd40_r1p0_cent_continuous"
V38_ZIP_SHA256 = "224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b"
MIN_R = 1.0
GIVEBACK_R = 0.25
TAIL_EXTENSION_R = 0.75
CALIBRATION_SCORE_QUANTILE = 0.85
CALIBRATION_MONTHS = 2
V36_HOLD_CEILING = 0.15
V36_MAX_AGE_MINUTES = 75.0
SEED = 2908

FEATURES = [
    "unrealized_r","mfe_r","mae_r","giveback_from_peak_r","r_delta_1m",
    "tick_count","tick_direction_imbalance","mid_net_move_r","mid_abs_path_r",
    "mid_range_r","spread_mean_points","spread_max_points","age_seconds",
    "direction_num","r_delta_mean_3m","r_delta_mean_5m","r_delta_mean_15m",
    "r_delta_std_5m","r_accel_1m","giveback_delta_1m","tick_count_log1p","age_log1p",
]

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def ts(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s,format="mixed",errors="raise")

def make_key(df: pd.DataFrame) -> pd.Series:
    return df["candidate"].astype(str)+"|"+ts(df["entry_time"]).dt.strftime("%Y%m%d%H%M%S")+"|"+df["direction"].astype(str)

def safe_auc(y: pd.Series,p: np.ndarray):
    return None if y.nunique(dropna=True)<2 else float(roc_auc_score(y.astype(int),p))

def source_family(x: str) -> str:
    s=str(x or "").upper()
    if "MACD" in s: return "MACD"
    if "SLOW" in s or "MOM" in s: return "SLOW_MOM"
    if "TREND" in s: return "TREND"
    if "BOS" in s or "FVG" in s: return "BOS_FVG"
    if "EMA" in s: return "EMA"
    return "OTHER"

def model():
    return HistGradientBoostingClassifier(
        learning_rate=0.05,max_iter=120,max_leaf_nodes=15,min_samples_leaf=30,
        l2_regularization=0.5,random_state=SEED,
    )

def fit_weighted(m,X,y):
    yy=y.astype(int).to_numpy()
    pos=max(1,int(yy.sum())); neg=max(1,int(len(yy)-yy.sum()))
    w=np.where(yy==1,min(5.0,max(1.0,neg/pos)),1.0)
    return m.fit(X,yy,sample_weight=w)

def load_inputs(run: Path,v36_path: Path|None):
    p1,p15,pt=run/"intra_trade_m1_fast.csv",run/"intra_trade_m15.csv",run/"trades.csv"
    for p in (p1,p15,pt):
        if not p.is_file(): raise FileNotFoundError(p)
    m1,m15,trades=pd.read_csv(p1),pd.read_csv(p15),pd.read_csv(pt)
    required={
        "time","month","candidate","book","entry_time","direction","age_seconds","unrealized_r",
        "mfe_r","mae_r","giveback_from_peak_r","r_delta_1m","tick_count",
        "tick_direction_imbalance","mid_net_move_r","mid_abs_path_r","mid_range_r",
        "spread_mean_points","spread_max_points",
    }
    miss=sorted(required-set(m1.columns))
    if miss: raise RuntimeError(f"V38 M1 columns missing: {miss}")
    for d in (m1,m15,trades):
        if not {"candidate","book"}.issubset(d.columns): raise RuntimeError("candidate/book columns missing")
        d.drop(d[(d.candidate!=CONTROL)|(d.book!=BOOK)].index,inplace=True)
    if m1.empty or m15.empty or trades.empty: raise RuntimeError("accepted control evidence empty")
    for d in (m1,m15):
        d["time"]=ts(d["time"]); d["entry_time"]=ts(d["entry_time"]); d["trade_key"]=make_key(d)
    trades["entry_time"]=ts(trades["entry_time"]); trades["exit_time"]=ts(trades["exit_time"]); trades["trade_key"]=make_key(trades)
    if trades.trade_key.duplicated().any(): raise RuntimeError("duplicate control trade_key")
    if len(trades)!=563: raise RuntimeError(f"V38 control trades expected=563 actual={len(trades)}")
    covered=m1.trade_key.nunique()
    if covered!=563: raise RuntimeError(f"V38 M1 coverage expected=563 actual={covered}")

    labels=trades[["trade_key","exit_time","r_multiple","mfe_r","mae_r","giveback_r"]].rename(columns={
        "r_multiple":"final_r","mfe_r":"final_mfe_r","mae_r":"final_mae_r","giveback_r":"final_giveback_r"})
    m1=m1.merge(labels,on="trade_key",how="inner",validate="many_to_one")
    sig=(m15[["trade_key","time","signal_sources"]].sort_values(["trade_key","time"])
         .groupby("trade_key",as_index=False).first()[["trade_key","signal_sources"]])
    m1=m1.merge(sig,on="trade_key",how="left",validate="many_to_one")
    m1["source_family"]=m1.signal_sources.fillna("").map(source_family)

    m1=m1.sort_values(["trade_key","time"]).reset_index(drop=True)
    g=m1.groupby("trade_key",sort=False)
    m1["future_max_r"]=g.unrealized_r.transform(lambda s:s.iloc[::-1].cummax().iloc[::-1])
    for n in (3,5,15):
        m1[f"r_delta_mean_{n}m"]=g.r_delta_1m.transform(lambda s,n=n:s.rolling(n,min_periods=1).mean())
    m1["r_delta_std_5m"]=g.r_delta_1m.transform(lambda s:s.rolling(5,min_periods=2).std()).fillna(0)
    m1["r_accel_1m"]=g.r_delta_1m.diff().fillna(0)
    m1["giveback_delta_1m"]=g.giveback_from_peak_r.diff().fillna(0)
    m1["tick_count_log1p"]=np.log1p(m1.tick_count.clip(lower=0))
    m1["age_log1p"]=np.log1p(m1.age_seconds.clip(lower=0))
    m1["direction_num"]=m1.direction.map({"LONG":1.0,"SHORT":-1.0}).fillna(0)
    m1["giveback_label"]=(m1.final_r<=m1.unrealized_r-GIVEBACK_R).astype(int)
    m1["tail_label"]=(m1.future_max_r>=np.maximum(m1.unrealized_r+TAIL_EXTENSION_R,2.0)).astype(int)

    vmeta={"available":False,"rows":0,"sha256":None}
    for c in ("p_hold","p_protect","pred_final_r","v36_age_minutes"): m1[c]=np.nan
    if v36_path and v36_path.is_file():
        pred=pd.read_csv(v36_path)
        need={"model","time","trade_key","candidate","p_hold","p_protect","pred_final_r"}
        if not need.issubset(pred.columns): raise RuntimeError(f"V36 columns missing: {sorted(need-set(pred.columns))}")
        pred=pred[(pred.model=="transformer")&(pred.candidate==CONTROL)].copy()
        pred["time"]=ts(pred["time"])
        pred=pred.sort_values(["trade_key","time"]).drop_duplicates(["trade_key","time"],keep="last")
        left=m1.drop(columns=["p_hold","p_protect","pred_final_r","v36_age_minutes"]).sort_values(["time","trade_key"])
        right=pred[["trade_key","time","p_hold","p_protect","pred_final_r"]].sort_values(["time","trade_key"])
        merged=pd.merge_asof(left,right,on="time",by="trade_key",direction="backward",allow_exact_matches=True)
        ages=pd.merge_asof(
            left[["trade_key","time"]],
            pred[["trade_key","time"]].rename(columns={"time":"v36_time"}).sort_values(["v36_time","trade_key"]),
            left_on="time",right_on="v36_time",by="trade_key",direction="backward",allow_exact_matches=True)
        merged["v36_age_minutes"]=((ages.time-ages.v36_time).dt.total_seconds()/60).to_numpy()
        m1=merged.sort_values(["trade_key","time"]).reset_index(drop=True)
        vmeta={"available":True,"rows":int(len(pred)),"sha256":sha256(v36_path)}

    return m1,{
        "m1_sha256":sha256(p1),"m15_sha256":sha256(p15),"trades_sha256":sha256(pt),
        "m1_rows_filtered":int(len(m1)),"control_trades":int(len(trades)),
        "m1_trade_coverage":int(covered),"v36":vmeta,
    }

def first_trigger(df):
    return df.sort_values(["trade_key","time"]).groupby("trade_key",sort=False,as_index=False).head(1).copy()

def trigger_metrics(t,eligible):
    if t.empty:
        return {"triggers":0,"eligible_trades":int(eligible),"coverage":0.0 if eligible else None,
                "mean_avoided_giveback_r":None,"median_avoided_giveback_r":None,
                "mean_foregone_extension_r":None,"false_big_winner_rate":None,"finish_below_trigger_rate":None}
    avoided=t.trigger_r-t.final_r
    foregone=np.maximum(0,t.future_max_r-t.trigger_r)
    return {"triggers":int(len(t)),"eligible_trades":int(eligible),"coverage":float(len(t)/eligible),
            "mean_avoided_giveback_r":float(avoided.mean()),"median_avoided_giveback_r":float(avoided.median()),
            "mean_foregone_extension_r":float(foregone.mean()),
            "false_big_winner_rate":float((foregone>=TAIL_EXTENSION_R).mean()),
            "finish_below_trigger_rate":float((t.final_r<t.trigger_r).mean())}

def score_fold(zone,test_start,use_v36):
    test_end=test_start+pd.offsets.MonthBegin(1)
    cal_start=test_start-pd.offsets.MonthBegin(CALIBRATION_MONTHS)
    train=zone[zone.exit_time<cal_start].copy()
    cal=zone[(zone.time>=cal_start)&(zone.time<test_start)&(zone.exit_time<test_start)].copy()
    test=zone[(zone.time>=test_start)&(zone.time<test_end)].copy()
    if use_v36:
        test=test[test.p_hold.notna()&test.p_protect.notna()&test.v36_age_minutes.notna()&
                  (test.v36_age_minutes<=V36_MAX_AGE_MINUTES)].copy()
    if train.trade_key.nunique()<80 or cal.trade_key.nunique()<10 or test.trade_key.nunique()<10: return None
    if train.giveback_label.nunique()<2 or train.tail_label.nunique()<2: return None
    Xtr=train[FEATURES].replace([np.inf,-np.inf],np.nan).astype(float)
    Xcal=cal[FEATURES].replace([np.inf,-np.inf],np.nan).astype(float)
    Xtest=test[FEATURES].replace([np.inf,-np.inf],np.nan).astype(float)
    mg=fit_weighted(model(),Xtr,train.giveback_label); mt=fit_weighted(model(),Xtr,train.tail_label)
    cg,ct=mg.predict_proba(Xcal)[:,1],mt.predict_proba(Xcal)[:,1]
    tg,tt=mg.predict_proba(Xtest)[:,1],mt.predict_proba(Xtest)[:,1]
    cal_score=cg*(1-ct); test_score=tg*(1-tt)
    if len(cal_score)<20: return None
    threshold=float(np.quantile(cal_score,CALIBRATION_SCORE_QUANTILE))
    guard=np.ones(len(test),dtype=bool)
    if use_v36:
        guard=(test.p_hold.to_numpy()<=V36_HOLD_CEILING)&(test.v36_age_minutes.to_numpy()<=V36_MAX_AGE_MINUTES)
    test=test.copy()
    test["p_giveback"]=tg; test["p_tail"]=tt; test["harvest_score"]=test_score
    test["harvest_signal"]=(test_score>=threshold)&guard; test["trigger_r"]=test.unrealized_r
    test["model_lane"]="fusion_v36_m1" if use_v36 else "m1_only"
    trig=first_trigger(test[test.harvest_signal].copy())
    met=trigger_metrics(trig,test.trade_key.nunique())
    met.update({"month":test_start.strftime("%Y-%m"),"model_lane":"fusion_v36_m1" if use_v36 else "m1_only",
                "train_rows":int(len(train)),"train_trades":int(train.trade_key.nunique()),
                "cal_rows":int(len(cal)),"cal_trades":int(cal.trade_key.nunique()),
                "test_rows":int(len(test)),"test_trades":int(test.trade_key.nunique()),
                "score_threshold":threshold,"giveback_auc":safe_auc(test.giveback_label,tg),
                "tail_auc":safe_auc(test.tail_label,tt),"feature_count":len(FEATURES)})
    return trig,met

def evaluate(zone,use_v36):
    trigs=[]; mets=[]
    for p in sorted(zone.time.dt.to_period("M").unique()):
        r=score_fold(zone,p.to_timestamp(),use_v36)
        if r is not None: trigs.append(r[0]); mets.append(r[1])
    return (pd.concat(trigs,ignore_index=True) if trigs else pd.DataFrame(),pd.DataFrame(mets))

def aggregate(trig,folds):
    if folds.empty: return {"folds":0,"status":"INSUFFICIENT"}
    valid=folds.mean_avoided_giveback_r.dropna()
    n=int(folds.triggers.sum()); elig=int(folds.eligible_trades.sum())
    out={"folds":int(len(folds)),"months":folds.month.tolist(),"triggers":n,"eligible_trades_month_sum":elig,
         "coverage":float(n/elig) if elig else None,"positive_avoided_giveback_months":int((valid>0).sum()),
         "mean_monthly_avoided_giveback_r":None if valid.empty else float(valid.mean()),
         "mean_monthly_foregone_extension_r":float(folds.mean_foregone_extension_r.dropna().mean()) if folds.mean_foregone_extension_r.notna().any() else None,
         "mean_monthly_false_big_winner_rate":float(folds.false_big_winner_rate.dropna().mean()) if folds.false_big_winner_rate.notna().any() else None,
         "mean_giveback_auc":float(folds.giveback_auc.dropna().mean()) if folds.giveback_auc.notna().any() else None,
         "mean_tail_auc":float(folds.tail_auc.dropna().mean()) if folds.tail_auc.notna().any() else None}
    ok=(out["folds"]>=4 and n>=30 and out["coverage"] is not None and .03<=out["coverage"]<=.35
        and out["positive_avoided_giveback_months"]>=max(3,math.ceil(.75*out["folds"]))
        and out["mean_monthly_avoided_giveback_r"] is not None and out["mean_monthly_avoided_giveback_r"]>0
        and out["mean_monthly_false_big_winner_rate"] is not None and out["mean_monthly_false_big_winner_rate"]<=.20)
    out["status"]="STAGE_A_PASS" if ok else "STAGE_A_HOLD"
    return out

def grouped(t,col):
    rows=[]
    if t.empty: return pd.DataFrame()
    for k,g in t.groupby(col,dropna=False):
        avoided=g.trigger_r-g.final_r; foregone=np.maximum(0,g.future_max_r-g.trigger_r)
        rows.append({col:str(k),"triggers":len(g),"mean_avoided_giveback_r":float(avoided.mean()),
                     "mean_foregone_extension_r":float(foregone.mean()),
                     "false_big_winner_rate":float((foregone>=TAIL_EXTENSION_R).mean()),
                     "finish_below_trigger_rate":float((g.final_r<g.trigger_r).mean())})
    return pd.DataFrame(rows).sort_values("triggers",ascending=False)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--v38-run-folder",required=True); ap.add_argument("--v36-predictions"); ap.add_argument("--output-dir",required=True)
    a=ap.parse_args(); out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    data,meta=load_inputs(Path(a.v38_run_folder),Path(a.v36_predictions) if a.v36_predictions else None)
    zone=data[data.unrealized_r>=MIN_R].copy()
    if zone.trade_key.nunique()<100: raise RuntimeError(f"too few +1R trades: {zone.trade_key.nunique()}")
    tm,fm=evaluate(zone,False); lanes={"m1_only":aggregate(tm,fm)}; all_t=[tm] if not tm.empty else []; all_f=[fm] if not fm.empty else []
    if meta["v36"]["available"]:
        tf,ff=evaluate(zone,True); lanes["fusion_v36_m1"]=aggregate(tf,ff)
        if not tf.empty: all_t.append(tf)
        if not ff.empty: all_f.append(ff)
    else: lanes["fusion_v36_m1"]={"folds":0,"status":"V36_MISSING"}
    triggers=pd.concat(all_t,ignore_index=True) if all_t else pd.DataFrame()
    folds=pd.concat(all_f,ignore_index=True) if all_f else pd.DataFrame()
    primary=lanes["fusion_v36_m1"] if lanes["fusion_v36_m1"].get("folds",0) else lanes["m1_only"]
    summary={"schema":"v39_selective_harvest_stage_a_v1","control":CONTROL,"book":BOOK,"decision_zone_min_r":MIN_R,
      "label_contract":{"giveback_label":f"final_r <= current_r - {GIVEBACK_R:.2f}R",
                        "tail_label":f"future_max_r >= max(current_r + {TAIL_EXTENSION_R:.2f}R, 2.0R)"},
      "selection_contract":{"threshold":f"trailing-{CALIBRATION_MONTHS}-month calibration {CALIBRATION_SCORE_QUANTILE:.0%} quantile",
                            "v36_guard":f"M1 threshold AND p_hold <= {V36_HOLD_CEILING:.2f} AND V36 age <= {V36_MAX_AGE_MINUTES:.0f}m",
                            "first_trigger_per_trade":True,"no_test_month_threshold_tuning":True},
      "input":meta,"zone_rows":int(len(zone)),"zone_trades":int(zone.trade_key.nunique()),"lanes":lanes,
      "primary_lane":"fusion_v36_m1" if lanes["fusion_v36_m1"].get("folds",0) else "m1_only",
      "stage_a_status":primary.get("status","INSUFFICIENT"),
      "economic_interpretation":"Diagnostic only. Trigger-vs-original-final metrics are path labels, not exact-MT5 PnL. Stage B requires frozen policy and exact MT5.",
      "aspirational_geo_month_target":0.15,
      "target_rule":"Do not optimize risk or thresholds merely to force 15%/month; stop-risk ceiling remains <=1.00%."}
    (out/"v39_selective_harvest_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    folds.to_csv(out/"v39_fold_metrics.csv",index=False,lineterminator="\n")
    if not triggers.empty:
        keep=["model_lane","month","time","trade_key","candidate","book","direction","source_family","trigger_r","final_r",
              "future_max_r","p_giveback","p_tail","harvest_score","p_hold","p_protect","pred_final_r",
              "giveback_from_peak_r","r_delta_1m","r_delta_mean_5m","r_delta_mean_15m","tick_count",
              "tick_direction_imbalance","mid_net_move_r","mid_abs_path_r","mid_range_r","spread_mean_points",
              "spread_max_points","age_seconds"]
        triggers[[c for c in keep if c in triggers]].sort_values(["model_lane","time"]).to_csv(out/"v39_first_triggers.csv",index=False)
        grouped(triggers,"source_family").to_csv(out/"v39_source_metrics.csv",index=False)
        triggers["direction_source"]=triggers.direction.astype(str)+"|"+triggers.source_family.astype(str)
        grouped(triggers,"direction_source").to_csv(out/"v39_direction_source_metrics.csv",index=False)
    else:
        for name in ("v39_first_triggers.csv","v39_source_metrics.csv","v39_direction_source_metrics.csv"):
            pd.DataFrame().to_csv(out/name,index=False)
    print(json.dumps({"stage_a_status":summary["stage_a_status"],"primary_lane":summary["primary_lane"],"lanes":lanes},indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
