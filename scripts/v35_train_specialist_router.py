#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error

RUN_IDS=[
 'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-02-01_00-00-00__756375',
 'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-08-01_00-00-00__22265',
 'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2026-02-01_00-00-00__519093']
BASE_EXPERTS=['ema_h1_skip20','macd_h1_gap10','bos_fvg_h1_gap8','trend20_h1_gap5','slow_mom_16h24h_timebox8h']
NEW_SPECIALISTS=['v34_smc_ict_causal','v34_price_action_causal','v34_wyckoff_proxy_causal','v34_tick_microstructure_proxy','v34_specialist_confluence']
SPECIALISTS=BASE_EXPERTS+NEW_SPECIALISTS
SOURCE_ID={n:i for i,n in enumerate(SPECIALISTS)}
TAPE_PREFIX=['smc_ict','price_action','wyckoff','microstructure','confluence']
BASE_DIR=['ema_dir','macd_dir','bos_fvg_dir','trend20_dir','slow_mom_dir']
BASE_SCORE=['ewma_hl8_ema','ewma_hl8_macd','ewma_hl8_bos','ewma_hl8_trend','ewma_hl8_slow']
MARKET=['atr_ratio','adx','dist_ema200_atr','rsi14','macd_hist','h1_ema50_minus_200_atr','h1_ret1','h1_ret4','m1_efficiency','m1_up_fraction','tick_direction_imbalance','tick_mid_net_move_atr','tick_mid_abs_path_atr','spread_atr','rv8','rv32','server_hour','ewma_hl8_ema','ewma_hl8_macd','ewma_hl8_bos','ewma_hl8_trend','ewma_hl8_slow']
SCORE_COLS=[f'{p}_score' for p in TAPE_PREFIX]

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_lake(common:Path):
 ps=[]
 for rid in RUN_IDS:
  p=common/'mt5_quant'/'runs'/rid/'bar_features.csv'
  d=pd.read_csv(p);d['feature_time']=pd.to_datetime(d.pop('time'),format='%Y.%m.%d %H:%M:%S');ps.append(d)
 x=pd.concat(ps,ignore_index=True).sort_values('feature_time').drop_duplicates('feature_time',keep='last').reset_index(drop=True)
 x['available']=x.feature_time+pd.Timedelta(minutes=15)
 return x

def causal_market_for_bars(lake:pd.DataFrame,bars:pd.Series):
 q=pd.DataFrame({'bar_time':pd.to_datetime(bars)}).drop_duplicates().sort_values('bar_time')
 use=lake[['available']+MARKET+BASE_DIR].sort_values('available')
 z=pd.merge_asof(q,use,left_on='bar_time',right_on='available',direction='backward',allow_exact_matches=True)
 if z[MARKET].isna().all(axis=1).any(): raise RuntimeError('market asof join failed')
 return z.drop(columns=['available'])

def load_alpha_tape(p:Path):
 a=pd.read_csv(p);a['bar_time']=pd.to_datetime(a.pop('time'),format='%Y.%m.%d %H:%M:%S')
 return a

def build_opportunity_frame(alpha:pd.DataFrame,lake:pd.DataFrame,start='2025-08-01',end='2026-08-01'):
 a=alpha[(alpha.bar_time>=pd.Timestamp(start))&(alpha.bar_time<pd.Timestamp(end))].copy()
 m=causal_market_for_bars(lake,a.bar_time)
 a=a.merge(m,on='bar_time',how='left',validate='one_to_one')
 rows=[]
 for sid,(name,dcol,scol) in enumerate(zip(BASE_EXPERTS,BASE_DIR,BASE_SCORE)):
  q=a[a[dcol]!=0].copy();q['candidate']=name;q['source_id']=sid;q['direction']=q[dcol].astype(int);q['source_score']=q[scol].astype(float)
  rows.append(q[['bar_time','candidate','source_id','direction','source_score']+SCORE_COLS+MARKET])
 off=len(BASE_EXPERTS)
 for j,(name,prefix) in enumerate(zip(NEW_SPECIALISTS,TAPE_PREFIX)):
  q=a[a[f'{prefix}_dir']!=0].copy();q['candidate']=name;q['source_id']=off+j;q['direction']=q[f'{prefix}_dir'].astype(int);q['source_score']=q[f'{prefix}_score'].astype(float)
  rows.append(q[['bar_time','candidate','source_id','direction','source_score']+SCORE_COLS+MARKET])
 return pd.concat(rows,ignore_index=True).sort_values(['bar_time','source_id']).reset_index(drop=True)

def load_outcomes(run:Path):
 t=pd.read_csv(run/'trades.csv')
 t=t[(t.candidate.isin(SPECIALISTS))&(t.book=='norm10k_r0p5_continuous')].copy()
 t['entry_time']=pd.to_datetime(t.entry_time,format='%Y.%m.%d %H:%M:%S');t['exit_time']=pd.to_datetime(t.exit_time,format='%Y.%m.%d %H:%M:%S')
 t['bar_time']=t.entry_time.dt.floor('15min');t['direction']=t.direction.map({'LONG':1,'SHORT':-1}).astype(int)
 return t

def make_models():
 nums=['source_score']+SCORE_COLS+MARKET+['direction'];cats=['candidate']
 prep=ColumnTransformer([('num',Pipeline([('imp',SimpleImputer(strategy='median')),('sc',StandardScaler())]),nums),('cat',OneHotEncoder(handle_unknown='ignore',sparse_output=False),cats)],remainder='drop')
 et=ExtraTreesRegressor(n_estimators=400,min_samples_leaf=8,max_features=.7,random_state=2908,n_jobs=-1)
 hgb=HistGradientBoostingRegressor(max_iter=220,learning_rate=.04,max_leaf_nodes=15,l2_regularization=1.0,random_state=2908)
 mlp=MLPRegressor(hidden_layer_sizes=(64,32,16),activation='relu',alpha=.002,learning_rate_init=.001,max_iter=350,early_stopping=True,validation_fraction=.15,n_iter_no_change=20,random_state=2908)
 return prep,et,hgb,mlp,nums,cats

def fit_predict(train,cal,test):
 prep,et,hgb,mlp,_,_=make_models();Xtr=prep.fit_transform(train);Xc=prep.transform(cal);Xt=prep.transform(test);y=train.r_multiple.to_numpy(float)
 mult=train.groupby(['bar_time','direction']).candidate.transform('count').to_numpy(float);w=1/np.maximum(mult,1)
 et.fit(Xtr,y,sample_weight=w);hgb.fit(Xtr,y,sample_weight=w)
 try: mlp.fit(Xtr,y,sample_weight=w)
 except TypeError: mlp.fit(Xtr,y)
 pc=np.column_stack([et.predict(Xc),hgb.predict(Xc),mlp.predict(Xc)]).mean(axis=1)
 pt=np.column_stack([et.predict(Xt),hgb.predict(Xt),mlp.predict(Xt)]).mean(axis=1)
 return pc,pt

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--common-files',required=True);ap.add_argument('--v34-run-folder',required=True);ap.add_argument('--alpha-tape',required=True);ap.add_argument('--output',required=True);ap.add_argument('--metadata',required=True);a=ap.parse_args()
 common=Path(a.common_files);run=Path(a.v34_run_folder);alpha=load_alpha_tape(Path(a.alpha_tape));lake=load_lake(common);opp=build_opportunity_frame(alpha,lake)
 outc=load_outcomes(run)
 lab=opp.merge(outc[['bar_time','candidate','direction','exit_time','r_multiple','mfe_r','mae_r','giveback_r']],on=['bar_time','candidate','direction'],how='inner')
 if len(lab)<300: raise RuntimeError(f'too few V34 specialist outcomes: {len(lab)}')
 router=pd.DataFrame({'time':alpha.bar_time,'router_dir':0,'router_source_id':-1,'router_score':np.nan,'threshold':np.nan})
 folds=[]
 for test_start in pd.date_range('2026-02-01','2026-07-01',freq='MS'):
  test_end=test_start+pd.offsets.MonthBegin(1);cal_start=test_start-pd.offsets.MonthBegin(1)
  tr=lab[lab.exit_time<cal_start].copy();cal=lab[(lab.bar_time>=cal_start)&(lab.bar_time<test_start)].copy();te=opp[(opp.bar_time>=test_start)&(opp.bar_time<test_end)].copy()
  if len(tr)<250 or len(cal)<30 or len(te)==0: raise RuntimeError(f'insufficient fold {test_start}: train={len(tr)} cal={len(cal)} test={len(te)}')
  pc,pt=fit_predict(tr,cal,te);threshold=float(np.quantile(pc,0.50));te=te.copy();te['pred']=pt
  picks=[]
  for bt,g in te.groupby('bar_time',sort=False):
   j=g.pred.idxmax();r=g.loc[j]
   if float(r.pred)>=threshold: picks.append((bt,int(r.direction),int(r.source_id),float(r.pred)))
  mask=(router.time>=test_start)&(router.time<test_end);router.loc[mask,'threshold']=threshold
  idx={bt:(d,s,p) for bt,d,s,p in picks}
  for i in router.index[mask]:
   bt=router.at[i,'time']
   if bt in idx: router.at[i,'router_dir'],router.at[i,'router_source_id'],router.at[i,'router_score']=idx[bt]
  cal_actual=cal.r_multiple.to_numpy(float);cal_mae=mean_absolute_error(cal_actual,pc)
  folds.append({'test_month':test_start.strftime('%Y_%m'),'train_rows':len(tr),'cal_rows':len(cal),'active_opportunities':len(te),'selected_bars':len(picks),'threshold':threshold,'cal_pred_mae':float(cal_mae)})
 router=router[(router.time>=pd.Timestamp('2026-02-01'))&(router.time<pd.Timestamp('2026-08-01'))].copy()
 router['time']=router.time.dt.strftime('%Y.%m.%d %H:%M:%S');router['router_score']=router.router_score.fillna(-999).round(8);router['threshold']=router.threshold.fillna(999).round(8)
 out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);router.to_csv(out,index=False,lineterminator='\n')
 meta={'schema':'v35_all_expert_meta_router_v1','models':['ExtraTreesRegressor','HistGradientBoostingRegressor','MLPRegressor_64_32_16'],'target':'V34 exact-MT5 norm-book r_multiple across existing + new experts','weighting':'inverse (entry_bar,direction) multiplicity','calibration':'previous-month median predicted-R threshold','test_months':[f['test_month'] for f in folds],'rows':len(router),'sha256':sha(out),'folds':folds,'warning':'offline diagnostics do not constitute PnL evidence; exact MT5 replay required'}
 Path(a.metadata).write_text(json.dumps(meta,indent=2),encoding='utf-8');print(f"V35 all-expert router tape PASS rows={len(router)} sha256={meta['sha256']}");print(json.dumps(folds,indent=2))
if __name__=='__main__': main()
