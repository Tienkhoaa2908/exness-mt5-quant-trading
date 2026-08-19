#!/usr/bin/env python3
"""Exploratory family-threshold gate for V30 weighted expected-R scores.

Fits the shared ExtraTrees expected-R model with inverse opportunity multiplicity
weights. Thresholds are calibrated from previous-month score distributions per
family (global fallback), then frozen into the next month. Runs both candidate-aware
and candidate-blind variants to expose identity dependence. Offline only.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
import v30_trade_tournament_v2 as t

KEEP_TARGETS=(0.40,0.50,0.60)
MIN_FAMILY_CAL=20

def load(path:Path)->pd.DataFrame:
 d=pd.read_pickle(path).copy();d['entry_time']=pd.to_datetime(d.entry_time);d['exit_time']=pd.to_datetime(d.exit_time);d['month']=d.month.astype(str);d['direction_code']=d.direction.map({'LONG':1.0,'SHORT':-1.0}).astype(float);return d

def sample_weights(d:pd.DataFrame)->np.ndarray:
 m=d.groupby(['entry_time','direction'])['candidate'].transform('size').to_numpy(float);w=1.0/m;return w/w.mean()

def thresholds(cal:pd.DataFrame,scores:np.ndarray,keep:float)->dict[str,float]:
 q=1.0-keep;out={'__global__':float(np.quantile(scores,q))};z=cal[['family']].copy();z['score']=scores
 for fam,g in z.groupby('family'):
  if len(g)>=MIN_FAMILY_CAL:out[str(fam)]=float(g.score.quantile(q))
 return out

def apply(test:pd.DataFrame,scores:np.ndarray,th:dict[str,float])->np.ndarray:
 return np.asarray([s>=th.get(str(f),th['__global__']) for s,f in zip(scores,test.family)],dtype=bool)

def run(df:pd.DataFrame,candidate_aware:bool):
 cats=t.candidate_list(df) if candidate_aware else [];cols=t.numeric_columns(df,'engineered_expert');overall=[];famrows=[]
 for cal_m,test_m in t.fold_months(df):
  cs=t.month_start(cal_m);ts=t.month_start(test_m);train=df[df.exit_time<cs].copy();cal=df[(df.month==cal_m)&(df.exit_time<ts)].copy();test=df[df.month==test_m].copy()
  if len(train)<t.MIN_TRAIN or len(cal)<t.MIN_CAL or len(test)<t.MIN_TEST:continue
  prep=t.fit_prep(train,cols,cats,candidate_aware);model=t.regression_model('extratrees');model.fit(prep.transform(train),train.r_multiple.to_numpy(float),sample_weight=sample_weights(train));pcal=model.predict(prep.transform(cal));ptest=model.predict(prep.transform(test))
  for keep in KEEP_TARGETS:
   th=thresholds(cal,pcal,keep);sel=apply(test,ptest,th);rec={'month':test_m,'cal_month':cal_m,'keep_target':keep,'candidate_aware':candidate_aware};rec.update(t.test_metrics(test,ptest,sel));overall.append(rec)
   z=test[['family','r_multiple']].copy();z['pred']=ptest;z['selected']=sel
   for fam,g in z.groupby('family'):
    y=g.r_multiple.to_numpy(float);s=g.selected.to_numpy(bool);famrows.append({'month':test_m,'keep_target':keep,'candidate_aware':candidate_aware,'family':fam,'n':len(g),'selected_n':int(s.sum()),'coverage':float(s.mean()),'baseline_avg_r':float(y.mean()),'baseline_sum_r':float(y.sum()),'selected_avg_r':float(y[s].mean()) if s.any() else np.nan,'selected_sum_r':float(y[s].sum()) if s.any() else 0.0,'avg_r_uplift':float(y[s].mean()-y.mean()) if s.any() else np.nan,'pred_spearman':float(pd.Series(y).corr(pd.Series(g.pred.to_numpy()),method='spearman')) if len(g)>2 else np.nan})
 return pd.DataFrame(overall),pd.DataFrame(famrows)

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('trade_pickle',type=Path);ap.add_argument('--output-dir',type=Path,required=True);a=ap.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True);df=load(a.trade_pickle);ovs=[];fams=[]
 for aware in (False,True):
  o,f=run(df,aware);ovs.append(o);fams.append(f)
 overall=pd.concat(ovs,ignore_index=True);byfam=pd.concat(fams,ignore_index=True);overall.to_csv(a.output_dir/'family_threshold_overall.csv',index=False);byfam.to_csv(a.output_dir/'family_threshold_by_family.csv',index=False)
 summary={}
 for key,g in overall.groupby(['candidate_aware','keep_target']):summary['|'.join(map(str,key))]=t.summarize_variant(g)
 famsummary={}
 for key,g in byfam.groupby(['candidate_aware','keep_target','family']):famsummary['|'.join(map(str,key))]=t.summarize_variant(g)
 payload={'overall':summary,'by_family':famsummary};(a.output_dir/'family_gate_summary.json').write_text(json.dumps(payload,indent=2),encoding='utf-8');print(json.dumps(payload,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
