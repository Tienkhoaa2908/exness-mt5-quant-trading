from __future__ import annotations
import numpy as np
import pandas as pd
from v41_baseline_stack_common import ACTIONS,ACTION_COVERAGE_TARGET,ACTION_FEATURES,CAL_MONTHS,DOWN_R,MIN_ACTION_R,apply_v36_calibrators,fit_v36_calibrators,make_classifier,make_regressor,safe_auc,safe_spearman

def build_action_targets(m1):
 rows=[]
 for _,g in m1.groupby('trade_key',sort=False):
  g=g.sort_values('time').reset_index(drop=True);final=float(g.final_r.iloc[0]);arr=g.unrealized_r.to_numpy(float)
  for i in np.flatnonzero(arr>=MIN_ACTION_R):
   cur=float(arr[i]);fut=arr[i+1:];rec=g.iloc[i].to_dict();hit=np.flatnonzero(fut<=cur-DOWN_R);sr=float(fut[int(hit[0])]) if len(hit) else final;rec['STATIC_PROTECT_0.25R_r']=sr;rec['STATIC_PROTECT_0.25R_delta_r']=sr-final;rec['STATIC_PROTECT_0.25R_positive']=int(sr>final);rec['STATIC_PROTECT_0.25R_hit']=bool(len(hit))
   if len(fut):path=np.concatenate(([cur],fut));peak=np.maximum.accumulate(path);th=np.flatnonzero(path[1:]<=peak[1:]-DOWN_R)
   else:th=np.array([],dtype=int)
   tr=float(fut[int(th[0])]) if len(th) else final;rec['SELECTIVE_TRAIL_0.25R_r']=tr;rec['SELECTIVE_TRAIL_0.25R_delta_r']=tr-final;rec['SELECTIVE_TRAIL_0.25R_positive']=int(tr>final);rec['SELECTIVE_TRAIL_0.25R_hit']=bool(len(th));rows.append(rec)
 if not rows:raise RuntimeError('no >=+1R action-value states')
 return pd.DataFrame(rows)

def fit_models(train,action):
 y=train[f'{action}_delta_r'].astype(float);yb=(y>0).astype(int);w=1/train.groupby('trade_key').trade_key.transform('size').astype(float).clip(lower=1);reg=make_regressor().fit(train[ACTION_FEATURES].astype(float),y,sample_weight=w);clf=make_classifier().fit(train[ACTION_FEATURES].astype(float),yb,sample_weight=w) if yb.nunique()>=2 else None;return reg,clf

def score(pair,df):
 reg,clf=pair;d=reg.predict(df[ACTION_FEATURES].astype(float));p=clf.predict_proba(df[ACTION_FEATURES].astype(float))[:,1] if clf is not None else np.full(len(df),.5);return d,p,d*p

def action_fold(states,v36,test_start,action):
 end=test_start+pd.offsets.MonthBegin(1);cs=test_start-pd.offsets.MonthBegin(CAL_MONTHS);train=states[states.exit_time<cs].copy();cal=states[(states.time>=cs)&(states.time<test_start)&(states.exit_time<test_start)].copy();test=states[(states.time>=test_start)&(states.time<end)].copy()
 if train.trade_key.nunique()<100 or cal.trade_key.nunique()<10 or test.trade_key.nunique()<10:return None
 iso=fit_v36_calibrators(v36,cs);train=apply_v36_calibrators(train,iso);cal=apply_v36_calibrators(cal,iso);test=apply_v36_calibrators(test,iso);pair=fit_models(train,action);cd,cp,csco=score(pair,cal);td,tp,ts=score(pair,test);thr=float(np.quantile(csco,1-ACTION_COVERAGE_TARGET));test['pred_delta_r']=td;test['p_positive']=tp;test['action_score']=ts;test['signal']=(ts>=thr)&(td>0);test['selected_action']=action;tr=test[test.signal].sort_values(['trade_key','time']).groupby('trade_key',as_index=False,sort=False).head(1).copy();actual=test[f'{action}_delta_r'].astype(float);sel=tr[f'{action}_delta_r'].astype(float) if len(tr) else pd.Series(dtype=float);elig=test.trade_key.nunique()
 return tr,dict(month=test_start.strftime('%Y-%m'),action=action,train_rows=len(train),train_trades=train.trade_key.nunique(),cal_rows=len(cal),cal_trades=cal.trade_key.nunique(),test_rows=len(test),test_trades=elig,threshold=thr,triggers=len(tr),coverage=float(len(tr)/elig) if elig else None,delta_spearman=safe_spearman(actual,td),positive_auc=safe_auc((actual>0).astype(int),tp),sum_delta_r=float(sel.sum()) if len(sel) else 0.,mean_delta_r=float(sel.mean()) if len(sel) else None,positive_delta_rate=float((sel>0).mean()) if len(sel) else None,large_harm_rate=float((sel<=-.75).mean()) if len(sel) else None)

def evaluate_action_layer(states,v36):
 tr=[];folds=[]
 for action in ACTIONS:
  for p in sorted(states.time.dt.to_period('M').unique()):
   r=action_fold(states,v36,p.to_timestamp(),action)
   if r is not None:tr.append(r[0]);folds.append(r[1])
 return (pd.concat(tr,ignore_index=True) if tr else pd.DataFrame(),pd.DataFrame(folds))

def choose_best_action(tr):
 if tr.empty:return tr.copy()
 x=tr.copy()
 if 'selected_action' not in x or not x.selected_action.isin(ACTIONS).all():raise RuntimeError('action trigger rows missing action identity')
 x=x.sort_values(['trade_key','time','pred_delta_r'],ascending=[True,True,False]);first=x.groupby('trade_key').time.transform('min');x=x[x.time==first].sort_values(['trade_key','pred_delta_r'],ascending=[True,False]);return x.groupby('trade_key',as_index=False,sort=False).head(1).copy()
