#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

CONTROL = "adaptive_ewma_hl8_thr0"
BOOK = "usd40_r1p0_cent_continuous"
SEED = 2908
MIN_R = 1.0
DOWN_R = 0.25
UP_R = 0.75
MIN_UP_LEVEL_R = 2.0
CAL_MONTHS = 2
SCORE_QUANTILE = 0.80
BASELINE_START_USD = 40.0
BASELINE_END_USD = 107.43
BASELINE_GEO_MONTH = 0.0858
BASELINE_MAX_DD = 0.0990
TARGET_GEO_MONTH = 0.15
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

def source_family(x: str) -> str:
    s=str(x or "").upper()
    if "MACD" in s: return "MACD"
    if "SLOW" in s or "MOM" in s: return "SLOW_MOM"
    if "TREND" in s: return "TREND"
    if "BOS" in s or "FVG" in s: return "BOS_FVG"
    if "EMA" in s: return "EMA"
    return "OTHER"

def safe_auc(y,p):
    y=np.asarray(y); p=np.asarray(p); mask=np.isfinite(y)&np.isfinite(p); y=y[mask]; p=p[mask]
    if len(y)<2 or len(np.unique(y))<2: return None
    return float(roc_auc_score(y.astype(int),p))

def model():
    return HistGradientBoostingClassifier(learning_rate=0.05,max_iter=140,max_leaf_nodes=15,min_samples_leaf=35,l2_regularization=0.75,random_state=SEED)

def fit_weighted(m,X,y):
    yy=y.astype(int).to_numpy(); pos=max(1,int(yy.sum())); neg=max(1,int(len(yy)-yy.sum()))
    w=np.where(yy==1,min(4.0,max(1.0,neg/pos)),1.0)
    return m.fit(X,yy,sample_weight=w)

def first_passage_labels(m1: pd.DataFrame) -> pd.DataFrame:
    out=[]
    for _,g in m1.groupby("trade_key",sort=False):
        g=g.sort_values("time").copy(); arr=g["unrealized_r"].to_numpy(float); times=g["time"].to_numpy()
        for i in np.flatnonzero(arr>=MIN_R):
            cur=float(arr[i]); down=cur-DOWN_R; up=max(cur+UP_R,MIN_UP_LEVEL_R); fut=arr[i+1:]
            di=np.flatnonzero(fut<=down); ui=np.flatnonzero(fut>=up)
            dstep=None if not len(di) else int(di[0])+1; ustep=None if not len(ui) else int(ui[0])+1
            if dstep is None and ustep is None: event="CENSORED"; step=None
            elif ustep is None or (dstep is not None and dstep<ustep): event="GIVEBACK_FIRST"; step=dstep
            else: event="TAIL_FIRST"; step=ustep
            row=g.iloc[i].to_dict(); row.update(fp_event=event,fp_down_level_r=down,fp_up_level_r=up,fp_steps=step)
            row["fp_minutes"]=np.nan if step is None else (pd.Timestamp(times[i+step])-pd.Timestamp(times[i])).total_seconds()/60.0
            out.append(row)
    if not out: raise RuntimeError("zero +1R first-passage states")
    return pd.DataFrame(out)

def merge_v36_asof(m1: pd.DataFrame,v36_path: Path|None):
    for c in ("v36_p_hold","v36_p_protect","v36_pred_final_r","v36_age_minutes"): m1[c]=np.nan
    meta={"available":False,"rows":0,"sha256":None}; cal_rows=[]
    if not v36_path or not v36_path.is_file(): return m1,meta,pd.DataFrame()
    p=pd.read_csv(v36_path); need={"model","time","trade_key","candidate","p_hold","p_protect","pred_final_r"}
    if not need.issubset(p.columns): raise RuntimeError(f"V36 columns missing: {sorted(need-set(p.columns))}")
    p=p[(p.model=="transformer")&(p.candidate==CONTROL)].copy(); p["time"]=ts(p["time"])
    p=p.sort_values(["trade_key","time"]).drop_duplicates(["trade_key","time"],keep="last")
    left=m1.drop(columns=["v36_p_hold","v36_p_protect","v36_pred_final_r","v36_age_minutes"]).sort_values(["time","trade_key"])
    right=p[["trade_key","time","p_hold","p_protect","pred_final_r"]].rename(columns={"p_hold":"v36_p_hold","p_protect":"v36_p_protect","pred_final_r":"v36_pred_final_r"}).sort_values(["time","trade_key"])
    merged=pd.merge_asof(left,right,on="time",by="trade_key",direction="backward",allow_exact_matches=True)
    rt=p[["trade_key","time"]].rename(columns={"time":"v36_time"}).sort_values(["v36_time","trade_key"])
    ages=pd.merge_asof(left[["trade_key","time"]],rt,left_on="time",right_on="v36_time",by="trade_key",direction="backward",allow_exact_matches=True)
    merged["v36_age_minutes"]=((ages.time-ages.v36_time).dt.total_seconds()/60.0).to_numpy()
    meta={"available":True,"rows":int(len(p)),"sha256":sha256(v36_path)}
    for head,prob,actual in (("hold","p_hold","actual_hold"),("protect","p_protect","actual_protect")):
        if actual in p.columns:
            q=p[[prob,actual]].dropna().copy()
            if not q.empty:
                q["bin"]=pd.cut(q[prob],bins=np.linspace(0,1,11),include_lowest=True,duplicates="drop")
                grp=q.groupby("bin",observed=True).agg(count=(actual,"size"),mean_pred=(prob,"mean"),event_rate=(actual,"mean")).reset_index()
                grp["head"]=head; grp["bin"]=grp["bin"].astype(str); cal_rows.append(grp)
    return merged.sort_values(["trade_key","time"]).reset_index(drop=True),meta,(pd.concat(cal_rows,ignore_index=True) if cal_rows else pd.DataFrame())

def load_inputs(run: Path,v36_path: Path|None):
    p1,p15,pt=run/"intra_trade_m1_fast.csv",run/"intra_trade_m15.csv",run/"trades.csv"
    for p in (p1,p15,pt):
        if not p.is_file(): raise FileNotFoundError(p)
    m1,m15,trades=pd.read_csv(p1),pd.read_csv(p15),pd.read_csv(pt)
    need_m1={"time","candidate","book","entry_time","direction","age_seconds","unrealized_r","mfe_r","mae_r","giveback_from_peak_r","r_delta_1m","tick_count","tick_direction_imbalance","mid_net_move_r","mid_abs_path_r","mid_range_r","spread_mean_points","spread_max_points"}
    miss=sorted(need_m1-set(m1.columns))
    if miss: raise RuntimeError(f"V38 M1 columns missing: {miss}")
    need_tr={"candidate","book","entry_time","exit_time","direction","r_multiple","mfe_r","mae_r","giveback_r"}
    miss=sorted(need_tr-set(trades.columns))
    if miss: raise RuntimeError(f"V38 trades columns missing: {miss}")
    for d in (m1,m15,trades): d.drop(d[(d.candidate!=CONTROL)|(d.book!=BOOK)].index,inplace=True)
    if len(trades)!=563: raise RuntimeError(f"control trades expected=563 actual={len(trades)}")
    for d in (m1,m15): d["time"]=ts(d["time"]); d["entry_time"]=ts(d["entry_time"]); d["trade_key"]=make_key(d)
    trades["entry_time"]=ts(trades["entry_time"]); trades["exit_time"]=ts(trades["exit_time"]); trades["trade_key"]=make_key(trades)
    if trades.trade_key.duplicated().any(): raise RuntimeError("duplicate trade_key")
    if m1.trade_key.nunique()!=563: raise RuntimeError(f"M1 trade coverage expected=563 actual={m1.trade_key.nunique()}")
    labels=trades[["trade_key","exit_time","r_multiple","mfe_r","mae_r","giveback_r"]].rename(columns={"r_multiple":"final_r","mfe_r":"final_mfe_r","mae_r":"final_mae_r","giveback_r":"final_giveback_r"})
    m1=m1.merge(labels,on="trade_key",how="inner",validate="many_to_one")
    sig=(m15[["trade_key","time","signal_sources"]].sort_values(["trade_key","time"]).groupby("trade_key",as_index=False).first()[["trade_key","signal_sources"]])
    m1=m1.merge(sig,on="trade_key",how="left",validate="many_to_one"); trades=trades.merge(sig,on="trade_key",how="left",validate="one_to_one")
    m1["source_family"]=m1.signal_sources.fillna("").map(source_family); trades["source_family"]=trades.signal_sources.fillna("").map(source_family)
    m1=m1.sort_values(["trade_key","time"]).reset_index(drop=True); g=m1.groupby("trade_key",sort=False)
    for n in (3,5,15): m1[f"r_delta_mean_{n}m"]=g.r_delta_1m.transform(lambda s,n=n:s.rolling(n,min_periods=1).mean())
    m1["r_delta_std_5m"]=g.r_delta_1m.transform(lambda s:s.rolling(5,min_periods=2).std()).fillna(0)
    m1["r_accel_1m"]=g.r_delta_1m.diff().fillna(0); m1["giveback_delta_1m"]=g.giveback_from_peak_r.diff().fillna(0)
    m1["tick_count_log1p"]=np.log1p(m1.tick_count.clip(lower=0)); m1["age_log1p"]=np.log1p(m1.age_seconds.clip(lower=0))
    m1["direction_num"]=m1.direction.map({"LONG":1.0,"SHORT":-1.0}).fillna(0)
    m1,v36_meta,v36_cal=merge_v36_asof(m1,v36_path); zone=first_passage_labels(m1)
    return m1,zone,trades,{"m1_sha256":sha256(p1),"m15_sha256":sha256(p15),"trades_sha256":sha256(pt),"m1_rows":int(len(m1)),"control_trades":int(len(trades)),"m1_trade_coverage":int(m1.trade_key.nunique()),"zone_rows":int(len(zone)),"zone_trades":int(zone.trade_key.nunique()),"v36":v36_meta},v36_cal

def score_fold(zone: pd.DataFrame,test_start: pd.Timestamp):
    test_end=test_start+pd.offsets.MonthBegin(1); cal_start=test_start-pd.offsets.MonthBegin(CAL_MONTHS)
    train=zone[(zone.exit_time<cal_start)&(zone.fp_event!="CENSORED")].copy()
    cal=zone[(zone.time>=cal_start)&(zone.time<test_start)&(zone.exit_time<test_start)&(zone.fp_event!="CENSORED")].copy()
    test=zone[(zone.time>=test_start)&(zone.time<test_end)].copy()
    if train.trade_key.nunique()<80 or cal.trade_key.nunique()<10 or test.trade_key.nunique()<10: return None
    train["y"]=(train.fp_event=="GIVEBACK_FIRST").astype(int); cal["y"]=(cal.fp_event=="GIVEBACK_FIRST").astype(int)
    if train.y.nunique()<2 or cal.y.nunique()<2: return None
    Xtr=train[FEATURES].replace([np.inf,-np.inf],np.nan).astype(float); Xcal=cal[FEATURES].replace([np.inf,-np.inf],np.nan).astype(float); Xtest=test[FEATURES].replace([np.inf,-np.inf],np.nan).astype(float)
    m=fit_weighted(model(),Xtr,train.y); pcal=m.predict_proba(Xcal)[:,1]; ptest=m.predict_proba(Xtest)[:,1]
    threshold=float(np.quantile(pcal,SCORE_QUANTILE)); test=test.copy(); test["p_giveback_first"]=ptest; test["signal"]=ptest>=threshold
    triggers=test[test.signal].sort_values(["trade_key","time"]).groupby("trade_key",as_index=False,sort=False).head(1).copy()
    mask=test.fp_event.to_numpy()!="CENSORED"; ry=(test.loc[mask].fp_event=="GIVEBACK_FIRST").astype(int)
    ntr=len(triggers); elig=test.trade_key.nunique()
    return triggers,{"month":test_start.strftime("%Y-%m"),"train_rows":int(len(train)),"train_trades":int(train.trade_key.nunique()),"cal_rows":int(len(cal)),"cal_trades":int(cal.trade_key.nunique()),"test_rows":int(len(test)),"test_trades":int(elig),"threshold":threshold,"auc_giveback_vs_tail":safe_auc(ry,ptest[mask]),"triggers":int(ntr),"coverage":float(ntr/elig) if elig else None,"giveback_first_triggers":int((triggers.fp_event=="GIVEBACK_FIRST").sum()) if ntr else 0,"tail_first_triggers":int((triggers.fp_event=="TAIL_FIRST").sum()) if ntr else 0,"censored_triggers":int((triggers.fp_event=="CENSORED").sum()) if ntr else 0,"giveback_first_rate":float((triggers.fp_event=="GIVEBACK_FIRST").mean()) if ntr else None,"tail_first_rate":float((triggers.fp_event=="TAIL_FIRST").mean()) if ntr else None,"censored_rate":float((triggers.fp_event=="CENSORED").mean()) if ntr else None,"mean_immediate_delta_r":float((triggers.unrealized_r-triggers.final_r).mean()) if ntr else None}

def evaluate(zone):
    trigs=[]; folds=[]
    for p in sorted(zone.time.dt.to_period("M").unique()):
        r=score_fold(zone,p.to_timestamp())
        if r is not None: trigs.append(r[0]); folds.append(r[1])
    trig=pd.concat(trigs,ignore_index=True) if trigs else pd.DataFrame()
    if not trig.empty: trig=trig.sort_values(["trade_key","time"]).groupby("trade_key",as_index=False,sort=False).head(1)
    return trig,pd.DataFrame(folds)

def simulate_action(g: pd.DataFrame,trigger_time: pd.Timestamp,trigger_r: float,action: str,final_r: float):
    fut=g[g.time>trigger_time].sort_values("time")
    if action=="IMMEDIATE": return trigger_r,trigger_time,True
    if action=="STATIC_PROTECT_0.25R":
        hit=fut[fut.unrealized_r<=trigger_r-DOWN_R]
        if hit.empty: return final_r,pd.NaT,False
        row=hit.iloc[0]; return float(row.unrealized_r),row.time,True
    if action=="SELECTIVE_TRAIL_0.25R":
        peak=trigger_r
        for row in fut.itertuples(index=False):
            r=float(row.unrealized_r); peak=max(peak,r)
            if r<=peak-DOWN_R: return r,row.time,True
        return final_r,pd.NaT,False
    raise ValueError(action)

def build_trade_shadow(m1,trades,triggers):
    tr=trades[["trade_key","entry_time","exit_time","direction","source_family","r_multiple"]].rename(columns={"r_multiple":"baseline_r"}).copy()
    trigger_map={} if triggers.empty else {r.trade_key:r for r in triggers.itertuples(index=False)}; groups={k:g for k,g in m1.groupby("trade_key",sort=False)}; rows=[]
    for row in tr.itertuples(index=False):
        base={"trade_key":row.trade_key,"entry_time":row.entry_time,"exit_time":row.exit_time,"direction":row.direction,"source_family":row.source_family,"baseline_r":float(row.baseline_r),"triggered":row.trade_key in trigger_map}
        if row.trade_key not in trigger_map:
            for a in ("IMMEDIATE","STATIC_PROTECT_0.25R","SELECTIVE_TRAIL_0.25R"): base[f"{a}_r"]=float(row.baseline_r); base[f"{a}_delta_r"]=0.0; base[f"{a}_exit_hit"]=False
            base.update(trigger_time=pd.NaT,trigger_r=np.nan,fp_event=None,p_giveback_first=np.nan); rows.append(base); continue
        t=trigger_map[row.trade_key]; base.update(trigger_time=pd.Timestamp(t.time),trigger_r=float(t.unrealized_r),fp_event=t.fp_event,p_giveback_first=float(t.p_giveback_first),v36_p_hold=getattr(t,"v36_p_hold",np.nan),v36_p_protect=getattr(t,"v36_p_protect",np.nan))
        for a in ("IMMEDIATE","STATIC_PROTECT_0.25R","SELECTIVE_TRAIL_0.25R"):
            rr,et,hit=simulate_action(groups[row.trade_key],pd.Timestamp(t.time),float(t.unrealized_r),a,float(row.baseline_r)); base[f"{a}_r"]=float(rr); base[f"{a}_delta_r"]=float(rr-row.baseline_r); base[f"{a}_exit_hit"]=bool(hit); base[f"{a}_exit_time"]=et
        rows.append(base)
    return pd.DataFrame(rows)

def solve_risk_scale(rs,start,target):
    arr=np.asarray(rs,float)
    def end(k):
        f=1+k*arr
        return 0.0 if np.any(f<=0) else float(start*np.prod(f))
    lo,hi=0.0,0.05
    while end(hi)<target and hi<0.25: hi*=1.5
    if end(hi)<target: return None
    for _ in range(100):
        mid=(lo+hi)/2
        if end(mid)<target: lo=mid
        else: hi=mid
    return (lo+hi)/2

def equity_metrics(rs,k,start=BASELINE_START_USD):
    eq=peak=start; maxdd=0.0
    for r in rs:
        eq*=max(1e-9,1+k*float(r)); peak=max(peak,eq); maxdd=max(maxdd,1-eq/peak)
    return {"end_usd":float(eq),"geo_month":float((eq/start)**(1/12)-1),"max_dd":float(maxdd)}

def action_metrics(trade_shadow):
    ordered=trade_shadow.sort_values(["entry_time","trade_key"]).reset_index(drop=True); k=solve_risk_scale(ordered.baseline_r,BASELINE_START_USD,BASELINE_END_USD)
    if k is None: raise RuntimeError("could not calibrate shadow risk scale")
    base=equity_metrics(ordered.baseline_r,k); rows=[]
    for a in ("IMMEDIATE","STATIC_PROTECT_0.25R","SELECTIVE_TRAIL_0.25R"):
        met=equity_metrics(ordered[f"{a}_r"],k); d=ordered[f"{a}_delta_r"]; trig=ordered[ordered.triggered]
        rows.append({"action":a,"calibrated_risk_scale":k,"shadow_end_usd":met["end_usd"],"shadow_geo_month":met["geo_month"],"shadow_max_dd":met["max_dd"],"baseline_shadow_end_usd":base["end_usd"],"baseline_shadow_geo_month":base["geo_month"],"baseline_shadow_max_dd":base["max_dd"],"delta_end_usd":met["end_usd"]-base["end_usd"],"delta_geo_month_pp":100*(met["geo_month"]-base["geo_month"]),"total_delta_r":float(d.sum()),"mean_trigger_delta_r":float(trig[f"{a}_delta_r"].mean()) if len(trig) else None,"positive_delta_triggers":int((trig[f"{a}_delta_r"]>0).sum()) if len(trig) else 0,"negative_delta_triggers":int((trig[f"{a}_delta_r"]<0).sum()) if len(trig) else 0,"turnover_trade_count":int(len(ordered)),"extra_entries":0})
    return pd.DataFrame(rows),k

def monthly_action_metrics(trade_shadow):
    x=trade_shadow[trade_shadow.triggered].copy()
    if x.empty: return pd.DataFrame()
    x["month"]=pd.to_datetime(x.trigger_time).dt.strftime("%Y-%m"); rows=[]
    for month,g in x.groupby("month"):
        for a in ("IMMEDIATE","STATIC_PROTECT_0.25R","SELECTIVE_TRAIL_0.25R"):
            d=g[f"{a}_delta_r"]; rows.append({"month":month,"action":a,"triggers":int(len(g)),"sum_delta_r":float(d.sum()),"mean_delta_r":float(d.mean()),"positive_delta_rate":float((d>0).mean())})
    return pd.DataFrame(rows)

def segment_metrics(trades):
    x=trades.copy(); x["month"]=x.entry_time.dt.to_period("M").astype(str); rows=[]
    for dims in (("source_family",),("direction",),("source_family","direction")):
        for keys,g in x.groupby(list(dims),dropna=False):
            if not isinstance(keys,tuple): keys=(keys,)
            rec={d:str(v) for d,v in zip(dims,keys)}; monthly=g.groupby("month").r_multiple.sum()
            rec.update(dimension="+".join(dims),trades=int(len(g)),mean_r=float(g.r_multiple.mean()),total_r=float(g.r_multiple.sum()),win_rate=float((g.r_multiple>0).mean()),mean_mfe_r=float(g.mfe_r.mean()),mean_giveback_r=float(g.giveback_r.mean()),positive_months=int((monthly>0).sum()),months=int(len(monthly))); rows.append(rec)
    return pd.DataFrame(rows)

def aggregate_gate(folds,triggers,monthly_actions,action_metrics_df):
    if folds.empty: return {"status":"INSUFFICIENT","reasons":["no folds"]}
    nfold=len(folds); ntr=len(triggers); coverage=float(folds.triggers.sum()/folds.test_trades.sum()) if folds.test_trades.sum() else 0.0
    tail_rate=float((triggers.fp_event=="TAIL_FIRST").mean()) if ntr else 1.0; give_rate=float((triggers.fp_event=="GIVEBACK_FIRST").mean()) if ntr else 0.0; aucs=folds.auc_giveback_vs_tail.dropna()
    sm=monthly_actions[monthly_actions.action=="STATIC_PROTECT_0.25R"] if not monthly_actions.empty else pd.DataFrame(); positive_months=int((sm.sum_delta_r>0).sum()) if not sm.empty else 0; mean_month_delta=float(sm.sum_delta_r.mean()) if not sm.empty else None
    sr=action_metrics_df[action_metrics_df.action=="STATIC_PROTECT_0.25R"].iloc[0]
    checks={"folds":nfold>=5,"triggers":ntr>=30,"coverage":0.05<=coverage<=0.35,"mean_auc":not aucs.empty and float(aucs.mean())>=0.60,"giveback_first_rate":give_rate>=0.60,"tail_first_rate":tail_rate<=0.25,"positive_shadow_months":positive_months>=4,"total_static_delta_r":float(sr.total_delta_r)>0}
    return {"status":"STAGE_A_PASS" if all(checks.values()) else "STAGE_A_HOLD","checks":checks,"folds":int(nfold),"triggers":int(ntr),"coverage":coverage,"mean_auc":None if aucs.empty else float(aucs.mean()),"giveback_first_rate":give_rate,"tail_first_rate":tail_rate,"censored_rate":float((triggers.fp_event=="CENSORED").mean()) if ntr else None,"positive_static_shadow_months":positive_months,"mean_month_static_delta_r":mean_month_delta,"static_total_delta_r":float(sr.total_delta_r),"static_shadow_end_usd":float(sr.shadow_end_usd),"static_shadow_geo_month":float(sr.shadow_geo_month),"static_shadow_max_dd":float(sr.shadow_max_dd)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--v38-run-folder",required=True); ap.add_argument("--v36-predictions"); ap.add_argument("--output-dir",required=True); args=ap.parse_args()
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    m1,zone,trades,meta,v36_cal=load_inputs(Path(args.v38_run_folder),Path(args.v36_predictions) if args.v36_predictions else None)
    triggers,folds=evaluate(zone); shadow=build_trade_shadow(m1,trades,triggers); actions,k=action_metrics(shadow); monthly=monthly_action_metrics(shadow); segments=segment_metrics(trades); gate=aggregate_gate(folds,triggers,monthly,actions)
    summary={"schema":"v40_upgrade_campaign_stage_a_v1","research_contract":{"primary_model":"HistGradientBoostingClassifier binary first-passage GIVEBACK_FIRST vs TAIL_FIRST","decision_zone_min_r":MIN_R,"giveback_boundary_r":DOWN_R,"tail_extension_r":UP_R,"tail_min_level_r":MIN_UP_LEVEL_R,"calibration_months":CAL_MONTHS,"score_quantile":SCORE_QUANTILE,"no_test_month_threshold_tuning":True,"primary_action":"STATIC_PROTECT_0.25R","secondary_action":"SELECTIVE_TRAIL_0.25R","risk_changed":False,"extra_entries":0},"accepted_exact_baseline":{"start_usd":BASELINE_START_USD,"end_usd":BASELINE_END_USD,"geo_month":BASELINE_GEO_MONTH,"max_dd":BASELINE_MAX_DD,"trades":563},"aspirational_target":{"geo_month":TARGET_GEO_MONTH,"target_end_usd_12m":BASELINE_START_USD*((1+TARGET_GEO_MONTH)**12),"gap_percentage_points":100*(TARGET_GEO_MONTH-BASELINE_GEO_MONTH)},"inputs":meta,"gate":gate,"actions":actions.to_dict(orient="records"),"frozen_risk_efficiency_reference":{"name":"V32 DeepMLP keep60","window":"2026-02_to_2026-07","baseline_geo_month":0.076807,"deepmlp_geo_month":0.076193,"baseline_max_dd":0.108159,"deepmlp_max_dd":0.073639,"baseline_trades":222,"deepmlp_trades":153,"baseline_avg_r":0.2401,"deepmlp_avg_r":0.3250,"baseline_pf":1.5579,"deepmlp_pf":1.8326,"status":"FROZEN_REFERENCE_NOT_RETUNED"},"notes":["Shadow equity is calibrated to reproduce the accepted exact baseline, but altered exits can change path/sizing; it is NOT exact-MT5 PnL.","Source/direction segment metrics are diagnostic only and cannot be converted into filters on this sample.","Stage-A PASS only permits a frozen exact-MT5 Stage B test; it does not authorize live trading."]}
    folds.to_csv(out/"v40_fold_metrics.csv",index=False,lineterminator="\n"); triggers.to_csv(out/"v40_first_triggers.csv",index=False,lineterminator="\n"); shadow.to_csv(out/"v40_trade_shadow.csv",index=False,lineterminator="\n"); actions.to_csv(out/"v40_action_metrics.csv",index=False,lineterminator="\n"); monthly.to_csv(out/"v40_monthly_action_metrics.csv",index=False,lineterminator="\n"); segments.to_csv(out/"v40_segment_metrics.csv",index=False,lineterminator="\n"); v36_cal.to_csv(out/"v40_v36_calibration.csv",index=False,lineterminator="\n"); (out/"v40_upgrade_campaign_summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"status":gate["status"],"folds":gate.get("folds"),"triggers":gate.get("triggers"),"coverage":gate.get("coverage"),"static_shadow_geo_month":gate.get("static_shadow_geo_month"),"exact_baseline_geo_month":BASELINE_GEO_MONTH,"target_geo_month":TARGET_GEO_MONTH},indent=2))

if __name__=="__main__": main()
