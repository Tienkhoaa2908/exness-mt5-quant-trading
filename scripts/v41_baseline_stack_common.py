from __future__ import annotations
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score
import v40_upgrade_campaign_stage_a as v40

CONTROL="adaptive_ewma_hl8_thr0"; BOOK="usd40_r1p0_cent_continuous"; SEED=2908
BASELINE_START_USD=40.0; BASELINE_END_USD=107.43; BASELINE_GEO_MONTH=0.0858; BASELINE_MAX_DD=0.0990; TARGET_GEO_MONTH=0.15
ENTRY_KEEP_TARGET=0.60; ACTION_COVERAGE_TARGET=0.20; CAL_MONTHS=1; MIN_ACTION_R=1.0; DOWN_R=0.25
ACTIONS=("STATIC_PROTECT_0.25R","SELECTIVE_TRAIL_0.25R")
SOURCE_CODE={"EMA":0.0,"SLOW_MOM":1.0,"MACD":2.0,"TREND":3.0,"BOS_FVG":4.0,"OTHER":5.0}
ENTRY_FEATURES=["direction_num","source_code","entry_hour_sin","entry_hour_cos","entry_dow_sin","entry_dow_cos","prev_r","prev2_r","prev_win","prev2_win","same_dir_prev","same_dir_prev2","minutes_since_prev_exit_log1p","same_dir_win_streak","rapid_post_profit","third_same_dir_after_2wins"]
ACTION_FEATURES=list(v40.FEATURES)+["source_code","entry_hour_sin","entry_hour_cos","entry_dow_sin","entry_dow_cos","prev_r","prev2_r","prev_win","prev2_win","same_dir_prev","same_dir_prev2","minutes_since_prev_exit_log1p","same_dir_win_streak","rapid_post_profit","third_same_dir_after_2wins","v36_hold_cal","v36_protect_cal","v36_pred_final_r_filled","v36_missing"]

def sha256(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def safe_auc(y,p):
 y=np.asarray(y);p=np.asarray(p);m=np.isfinite(y)&np.isfinite(p);y=y[m];p=p[m]
 return None if len(y)<2 or len(np.unique(y))<2 else float(roc_auc_score(y.astype(int),p))

def safe_spearman(y,p):
 s=pd.DataFrame({'y':y,'p':p}).dropna()
 return None if len(s)<3 or s.y.nunique()<2 or s.p.nunique()<2 else float(s.y.corr(s.p,method='spearman'))

def make_regressor():return HistGradientBoostingRegressor(loss='squared_error',learning_rate=.05,max_iter=140,max_leaf_nodes=15,min_samples_leaf=25,l2_regularization=1.0,random_state=SEED)
def make_classifier():return HistGradientBoostingClassifier(learning_rate=.05,max_iter=140,max_leaf_nodes=15,min_samples_leaf=25,l2_regularization=1.0,random_state=SEED)

def add_clock_features(df,time_col):
 x=df.copy();t=pd.to_datetime(x[time_col]);h=t.dt.hour+t.dt.minute/60.;d=t.dt.dayofweek.astype(float)
 x['entry_hour_sin']=np.sin(2*np.pi*h/24);x['entry_hour_cos']=np.cos(2*np.pi*h/24);x['entry_dow_sin']=np.sin(2*np.pi*d/7);x['entry_dow_cos']=np.cos(2*np.pi*d/7);return x

def add_trade_sequence_features(trades):
 x=trades.sort_values(['entry_time','trade_key']).reset_index(drop=True).copy();x['direction_num']=x.direction.map({'LONG':1.,'SHORT':-1.}).fillna(0.);x['source_code']=x.source_family.map(SOURCE_CODE).fillna(SOURCE_CODE['OTHER']).astype(float);x=add_clock_features(x,'entry_time')
 vals=[];past=[]
 for row in x.itertuples(index=False):
  et=pd.Timestamp(row.entry_time);done=sorted((p for p in past if pd.Timestamp(p['exit_time'])<=et),key=lambda p:pd.Timestamp(p['exit_time']));p1=done[-1] if done else None;p2=done[-2] if len(done)>=2 else None
  r1=float(p1['r_multiple']) if p1 else 0.;r2=float(p2['r_multiple']) if p2 else 0.;s1=float(bool(p1 and p1['direction']==row.direction));s2=float(bool(p2 and p2['direction']==row.direction));gap=(et-pd.Timestamp(p1['exit_time'])).total_seconds()/60 if p1 else 1e9
  streak=0
  for p in reversed(done):
   if p['direction']==row.direction and float(p['r_multiple'])>0:streak+=1
   else:break
  vals.append(dict(prev_r=r1,prev2_r=r2,prev_win=float(r1>0),prev2_win=float(r2>0),same_dir_prev=s1,same_dir_prev2=s2,minutes_since_prev_exit_log1p=float(np.log1p(max(0.,min(gap,10080.)))),same_dir_win_streak=float(min(streak,5)),rapid_post_profit=float(bool(p1 and s1 and r1>0 and gap<=240)),third_same_dir_after_2wins=float(bool(p1 and p2 and s1 and s2 and r1>0 and r2>0 and gap<=240))))
  past.append(dict(exit_time=row.exit_time,direction=row.direction,r_multiple=row.r_multiple))
 return pd.concat([x,pd.DataFrame(vals)],axis=1)

def attach_sequence_to_m1(m1,trades):
 cols=['trade_key','source_code','entry_hour_sin','entry_hour_cos','entry_dow_sin','entry_dow_cos','prev_r','prev2_r','prev_win','prev2_win','same_dir_prev','same_dir_prev2','minutes_since_prev_exit_log1p','same_dir_win_streak','rapid_post_profit','third_same_dir_after_2wins']
 return m1.merge(trades[cols],on='trade_key',how='left',validate='many_to_one')

def load_v36_calibration_table(path,trades):
 p=pd.read_csv(path);need={'model','trade_key','time','p_hold','p_protect','actual_hold','actual_protect'};miss=sorted(need-set(p.columns))
 if miss:raise RuntimeError(f'V36 calibration columns missing: {miss}')
 p=p[p.model=='transformer'].copy()
 if 'candidate' in p.columns:p=p[p.candidate==CONTROL].copy()
 p['time']=pd.to_datetime(p.time,format='mixed',errors='raise');p['exit_time']=p.trade_key.map(trades.set_index('trade_key').exit_time);return p[p.exit_time.notna()].copy()

def fit_v36_calibrators(v36,cutoff):
 hist=v36[v36.exit_time<cutoff];out={}
 for raw,actual in [('p_hold','actual_hold'),('p_protect','actual_protect')]:
  q=hist[[raw,actual]].dropna();out[raw]=IsotonicRegression(out_of_bounds='clip').fit(q[raw].astype(float),q[actual].astype(int)) if len(q)>=30 and q[actual].nunique()>=2 else None
 return out

def apply_v36_calibrators(x,cal):
 x=x.copy()
 for raw,outcol in [('v36_p_hold','v36_hold_cal'),('v36_p_protect','v36_protect_cal')]:
  a=pd.to_numeric(x[raw],errors='coerce').to_numpy(float);m=np.isfinite(a);model=cal.get(raw.replace('v36_',''))
  if model is not None and m.any():a[m]=model.predict(a[m])
  x[outcol]=a
 x['v36_missing']=x[['v36_p_hold','v36_p_protect']].isna().any(axis=1).astype(float);x['v36_hold_cal']=x.v36_hold_cal.fillna(.5);x['v36_protect_cal']=x.v36_protect_cal.fillna(.5);x['v36_pred_final_r_filled']=x.v36_pred_final_r.fillna(0.);return x
