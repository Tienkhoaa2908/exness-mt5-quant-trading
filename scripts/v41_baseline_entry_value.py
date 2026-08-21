from __future__ import annotations
import numpy as np
import pandas as pd
from v41_baseline_stack_common import CAL_MONTHS,ENTRY_FEATURES,ENTRY_KEEP_TARGET,make_regressor,safe_spearman

def entry_fold(trades,test_start):
 end=test_start+pd.offsets.MonthBegin(1);cal_start=test_start-pd.offsets.MonthBegin(CAL_MONTHS);train=trades[trades.exit_time<cal_start].copy();cal=trades[(trades.entry_time>=cal_start)&(trades.entry_time<test_start)&(trades.exit_time<test_start)].copy();test=trades[(trades.entry_time>=test_start)&(trades.entry_time<end)].copy()
 if len(train)<150 or len(cal)<15 or len(test)<15:return None
 model=make_regressor().fit(train[ENTRY_FEATURES].astype(float),train.r_multiple.astype(float));pc=model.predict(cal[ENTRY_FEATURES].astype(float));pt=model.predict(test[ENTRY_FEATURES].astype(float));thr=float(np.quantile(pc,1-ENTRY_KEEP_TARGET));test['entry_pred_r']=pt;test['entry_keep']=pt>=thr;kept=test[test.entry_keep]
 return test,dict(month=test_start.strftime('%Y-%m'),train_trades=len(train),cal_trades=len(cal),test_trades=len(test),threshold=thr,coverage=float(test.entry_keep.mean()),spearman=safe_spearman(test.r_multiple,pt),baseline_avg_r=float(test.r_multiple.mean()),selected_avg_r=float(kept.r_multiple.mean()) if len(kept) else None,baseline_sum_r=float(test.r_multiple.sum()),selected_sum_r=float(kept.r_multiple.sum()),delta_sum_r=float(kept.r_multiple.sum()-test.r_multiple.sum()),kept_trades=len(kept))

def evaluate_entry_layer(trades):
 scored=[];folds=[]
 for p in sorted(trades.entry_time.dt.to_period('M').unique()):
  r=entry_fold(trades,p.to_timestamp())
  if r is not None:scored.append(r[0]);folds.append(r[1])
 return (pd.concat(scored,ignore_index=True) if scored else pd.DataFrame(),pd.DataFrame(folds))
