from __future__ import annotations
import math
import numpy as np
import pandas as pd
import v40_upgrade_campaign_stage_a as v40
from v41_baseline_stack_common import BASELINE_END_USD,BASELINE_START_USD

def solve_risk_scale(rs,start,target):
 a=np.asarray(rs,float)
 def end(k):
  f=1+k*a;return 0. if np.any(f<=0) else float(start*np.prod(f))
 lo,hi=0.,.05
 while end(hi)<target and hi<.25:hi*=1.5
 if end(hi)<target:return None
 for _ in range(100):
  mid=(lo+hi)/2
  if end(mid)<target:lo=mid
  else:hi=mid
 return (lo+hi)/2

def equity_metrics(rs,k,start=BASELINE_START_USD):
 eq=peak=start;dd=0.
 for r in rs:eq*=max(1e-9,1+k*float(r));peak=max(peak,eq);dd=max(dd,1-eq/peak)
 return dict(end_usd=float(eq),geo_month=float((eq/start)**(1/12)-1),max_dd=float(dd))

def apply_entry(trades,scored):
 x=trades.copy();x['entry_oos']=False;x['entry_keep']=True;x['entry_pred_r']=np.nan
 if not scored.empty:
  mp=scored.set_index('trade_key')[['entry_keep','entry_pred_r']];idx=x.trade_key.isin(mp.index);x.loc[idx,'entry_oos']=True;x.loc[idx,'entry_keep']=x.loc[idx,'trade_key'].map(mp.entry_keep).astype(bool);x.loc[idx,'entry_pred_r']=x.loc[idx,'trade_key'].map(mp.entry_pred_r)
 x['entry_layer_r']=np.where(x.entry_keep,x.r_multiple,0.);return x

def apply_action(m1,x,triggers):
 x=x.copy();x['action_triggered']=False;x['selected_action']='BASELINE';x['action_layer_r']=x.r_multiple.astype(float);x['action_pred_delta_r']=np.nan
 if triggers.empty:return x
 groups={k:g for k,g in m1.groupby('trade_key',sort=False)}
 for t in triggers.itertuples(index=False):
  m=x.trade_key==t.trade_key
  if not m.any():continue
  final=float(x.loc[m,'r_multiple'].iloc[0]);rr,_,_=v40.simulate_action(groups[t.trade_key],pd.Timestamp(t.time),float(t.unrealized_r),str(t.selected_action),final);x.loc[m,'action_triggered']=True;x.loc[m,'selected_action']=str(t.selected_action);x.loc[m,'action_layer_r']=float(rr);x.loc[m,'action_pred_delta_r']=float(t.pred_delta_r)
 return x

def build_stack(trades,entry,m1,actions):
 x=apply_entry(trades,entry);x=apply_action(m1,x,actions);x['stack_r']=np.where(x.entry_keep,x.action_layer_r,0.);return x

def shadow_metrics(stack):
 x=stack.sort_values(['entry_time','trade_key']).reset_index(drop=True);k=solve_risk_scale(x.r_multiple,BASELINE_START_USD,BASELINE_END_USD)
 if k is None:raise RuntimeError('could not calibrate baseline shadow')
 rows=[]
 for name,col in [('BASELINE','r_multiple'),('ENTRY_VALUE','entry_layer_r'),('ACTION_VALUE','action_layer_r'),('INTEGRATED_STACK','stack_r')]:
  met=equity_metrics(x[col],k);d=x[col]-x.r_multiple;rows.append(dict(lane=name,risk_scale=k,**met,total_delta_r=float(d.sum()),mean_r=float(x[col].mean()),trades_nonzero=int((x[col]!=0).sum())))
 return pd.DataFrame(rows),k

def layer_audit(trades):
 x=trades.copy();x['month']=x.entry_time.dt.strftime('%Y-%m');rules={'TARGETED_SHORT_EXHAUSTION':x.source_family.isin(['EMA','BOS_FVG'])&(x.direction=='SHORT')&(x.third_same_dir_after_2wins>0),'EMA_LATE_SESSION_22_23':(x.source_family=='EMA')&(x.entry_time.dt.hour>=22),'RAPID_POST_PROFIT_SAME_DIR':x.rapid_post_profit>0};rows=[];monthly=[]
 for name,mask in rules.items():
  g=x[mask];rows.append(dict(layer=name,flagged_trades=len(g),flagged_avg_r=float(g.r_multiple.mean()) if len(g) else None,flagged_sum_r=float(g.r_multiple.sum()) if len(g) else 0.,skip_shadow_delta_r=float(-g.r_multiple.sum()) if len(g) else 0.,status='DIAGNOSTIC_ONLY_NOT_AUTO_INTEGRATED'))
  for mo,gm in g.groupby('month'):monthly.append(dict(layer=name,month=mo,flagged_trades=len(gm),flagged_sum_r=float(gm.r_multiple.sum()),skip_shadow_delta_r=float(-gm.r_multiple.sum())))
 return pd.DataFrame(rows),pd.DataFrame(monthly)

def segments(trades):
 x=trades.copy();x['month']=x.entry_time.dt.strftime('%Y-%m');rows=[]
 for dims in [('source_family',),('direction',),('source_family','direction')]:
  for keys,g in x.groupby(list(dims),dropna=False):
   if not isinstance(keys,tuple):keys=(keys,)
   rec={d:str(v) for d,v in zip(dims,keys)};mo=g.groupby('month').r_multiple.sum();rec.update(dimension='+'.join(dims),trades=len(g),mean_r=float(g.r_multiple.mean()),total_r=float(g.r_multiple.sum()),win_rate=float((g.r_multiple>0).mean()),positive_months=int((mo>0).sum()),months=len(mo));rows.append(rec)
 return pd.DataFrame(rows)

def monthly_delta(x,col,months):
 z=x.copy();z['month']=z.entry_time.dt.strftime('%Y-%m');z=z[z.month.isin(months)]
 if z.empty:return {}
 a=z.groupby('month').apply(lambda g:float((g[col]-g.r_multiple).sum()),include_groups=False);return {str(k):float(v) for k,v in a.items()}

def aggregate_gate(entry_folds,action_folds,actions,metrics,stack):
 r={x.lane:x for x in metrics.itertuples(index=False)};em=sorted(entry_folds.month.unique().tolist()) if not entry_folds.empty else [];am=sorted(action_folds.month.unique().tolist()) if not action_folds.empty else [];allm=sorted(set(em)|set(am));ed=monthly_delta(stack,'entry_layer_r',em);ad=monthly_delta(stack,'action_layer_r',am);sd=monthly_delta(stack,'stack_r',allm)
 pos=lambda d:sum(v>0 for v in d.values());stable=lambda d:bool(d) and pos(d)>=max(4,math.ceil(.75*len(d)));b,e,a,s=r['BASELINE'],r['ENTRY_VALUE'],r['ACTION_VALUE'],r['INTEGRATED_STACK'];ec=float(len(actions)/max(1,stack[stack.entry_time.dt.strftime('%Y-%m').isin(am)].trade_key.nunique())) if am else 0.
 er=bool(e.geo_month>b.geo_month and e.total_delta_r>0 and stable(ed));ee=bool(e.geo_month>=b.geo_month-.0025 and e.max_dd<=b.max_dd*.85);ap=bool(a.geo_month>b.geo_month and a.total_delta_r>0 and stable(ad) and len(actions)>=30 and .03<=ec<=.30);sp=bool(s.geo_month>b.geo_month and s.total_delta_r>0 and stable(sd) and s.max_dd<=b.max_dd+.01);promotion='INTEGRATED_STACK' if sp else ('ACTION_VALUE' if ap else ('ENTRY_VALUE' if er else None))
 return dict(status='STAGE_A_PASS' if promotion else 'STAGE_A_HOLD',promotion_lane=promotion,entry_return_pass=er,entry_efficiency_keep=ee,action_pass=ap,stack_pass=sp,entry_oos_months=em,action_oos_months=am,all_oos_months=allm,entry_positive_months=pos(ed),action_positive_months=pos(ad),stack_positive_months=pos(sd),entry_monthly_delta_r=ed,action_monthly_delta_r=ad,stack_monthly_delta_r=sd,best_action_count=len(actions),best_action_coverage=ec,baseline_shadow_geo_month=float(b.geo_month),baseline_shadow_max_dd=float(b.max_dd),entry_shadow_end_usd=float(e.end_usd),entry_shadow_geo_month=float(e.geo_month),entry_shadow_max_dd=float(e.max_dd),entry_total_delta_r=float(e.total_delta_r),action_shadow_end_usd=float(a.end_usd),action_shadow_geo_month=float(a.geo_month),action_shadow_max_dd=float(a.max_dd),action_total_delta_r=float(a.total_delta_r),integrated_shadow_end_usd=float(s.end_usd),integrated_shadow_geo_month=float(s.geo_month),integrated_shadow_max_dd=float(s.max_dd),integrated_total_delta_r=float(s.total_delta_r))
