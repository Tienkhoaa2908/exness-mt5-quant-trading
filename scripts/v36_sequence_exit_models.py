#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,hashlib,math,random
from pathlib import Path
import numpy as np,pandas as pd

RUN_IDS=[
 'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-02-01_00-00-00__756375',
 'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-08-01_00-00-00__22265',
 'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2026-02-01_00-00-00__519093']
MARKET=['atr_ratio','adx','dist_ema200_atr','rsi14','macd_hist','h1_ema50_minus_200_atr','h1_ret1','h1_ret4','m1_efficiency','m1_up_fraction','tick_direction_imbalance','tick_mid_net_move_atr','tick_mid_abs_path_atr','spread_atr','rv8','rv32','ewma_hl8_ema','ewma_hl8_macd','ewma_hl8_bos','ewma_hl8_trend','ewma_hl8_slow']
PATH=['unrealized_r','peak_r','mae_r','giveback_from_peak_r','stop_r','tp_r','age_seconds']

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_lake(common:Path):
 ps=[]
 for rid in RUN_IDS:
  p=common/'mt5_quant'/'runs'/rid/'bar_features.csv';d=pd.read_csv(p);d['feature_time']=pd.to_datetime(d.pop('time'),format='%Y.%m.%d %H:%M:%S');ps.append(d)
 x=pd.concat(ps,ignore_index=True).sort_values('feature_time').drop_duplicates('feature_time',keep='last');x['available']=x.feature_time+pd.Timedelta(minutes=15);return x

def prepare(common:Path,run:Path,book:str):
 tel=pd.read_csv(run/'intra_trade_m15.csv');tr=pd.read_csv(run/'trades.csv')
 tel=tel[tel.book==book].copy();tr=tr[tr.book==book].copy()
 for c in ['time','entry_time']:tel[c]=pd.to_datetime(tel[c],format='%Y.%m.%d %H:%M:%S')
 for c in ['entry_time','exit_time']:tr[c]=pd.to_datetime(tr[c],format='%Y.%m.%d %H:%M:%S')
 tel['trade_key']=tel.candidate.astype(str)+'|'+tel.entry_time.dt.strftime('%Y%m%d%H%M%S')+'|'+tel.direction.astype(str)
 tr['trade_key']=tr.candidate.astype(str)+'|'+tr.entry_time.dt.strftime('%Y%m%d%H%M%S')+'|'+tr.direction.astype(str)
 labels=tr[['trade_key','exit_time','r_multiple','mfe_r','mae_r','giveback_r']].drop_duplicates('trade_key')
 tel=tel.merge(labels,on='trade_key',how='inner',validate='many_to_one')
 lake=load_lake(common);q=tel[['time']].drop_duplicates().sort_values('time');m=pd.merge_asof(q,lake[['available']+MARKET].sort_values('available'),left_on='time',right_on='available',direction='backward',allow_exact_matches=True).drop(columns='available')
 tel=tel.merge(m,on='time',how='left',validate='many_to_one')
 tel['future_upside_r']=np.maximum(0,tel.mfe_r_y-tel.peak_r)
 tel['future_giveback_r']=np.maximum(0,tel.unrealized_r-tel.r_multiple)
 tel['protect_label']=(tel['future_giveback_r']>=0.50).astype(float)
 tel['hold_label']=(tel['future_upside_r']>=0.50).astype(float)
 tel=tel.sort_values(['trade_key','time']).reset_index(drop=True)
 return tel

def make_samples(df,seq_len=32):
 feats=PATH+MARKET
 X=[];yr=[];yh=[];yp=[];meta=[]
 for key,g in df.groupby('trade_key',sort=False):
  arr=g[feats].astype(float).replace([np.inf,-np.inf],np.nan).ffill().fillna(0).to_numpy(np.float32)
  idx=list(range(4,len(g),4))
  if len(g)>1 and (len(g)-1) not in idx: idx.append(len(g)-1)
  for j in idx:
   a=max(0,j-seq_len+1);seq=arr[a:j+1];pad=np.zeros((seq_len,len(feats)),np.float32);pad[-len(seq):]=seq
   row=g.iloc[j];X.append(pad);yr.append(float(row.r_multiple));yh.append(float(row.hold_label));yp.append(float(row.protect_label));meta.append((row.time,row.exit_time,key,float(row.unrealized_r)))
 return np.asarray(X),np.asarray(yr,np.float32),np.asarray(yh,np.float32),np.asarray(yp,np.float32),meta,feats

def train_eval(X,yr,yh,yp,meta,summary_path,pred_path,epochs=25):
 try:
  import torch,torch.nn as nn
  from torch.utils.data import DataLoader,TensorDataset
 except Exception as e: raise RuntimeError('PyTorch required for V36 sequence models') from e
 torch.manual_seed(2908);np.random.seed(2908);random.seed(2908);torch.set_num_threads(max(1,min(4,torch.get_num_threads())))
 times=pd.to_datetime([m[0] for m in meta]);exits=pd.to_datetime([m[1] for m in meta])
 class GRU(nn.Module):
  def __init__(self,d):super().__init__();self.r=nn.GRU(d,48,batch_first=True);self.h=nn.Sequential(nn.Linear(48,32),nn.ReLU());self.o=nn.Linear(32,3)
  def forward(self,x):_,h=self.r(x);return self.o(self.h(h[-1]))
 class TCN(nn.Module):
  def __init__(self,d):super().__init__();self.n=nn.Sequential(nn.Conv1d(d,48,3,padding=2,dilation=1),nn.ReLU(),nn.Conv1d(48,48,3,padding=4,dilation=2),nn.ReLU(),nn.Conv1d(48,48,3,padding=8,dilation=4),nn.ReLU());self.o=nn.Linear(48,3)
  def forward(self,x):z=self.n(x.transpose(1,2));return self.o(z[:,:,-1])
 class Transformer(nn.Module):
  def __init__(self,d):super().__init__();self.p=nn.Linear(d,48);enc=nn.TransformerEncoderLayer(48,4,96,dropout=.1,batch_first=True);self.e=nn.TransformerEncoder(enc,2);self.o=nn.Linear(48,3)
  def forward(self,x):z=self.e(self.p(x));return self.o(z[:,-1])
 models={'gru':GRU,'tcn':TCN,'transformer':Transformer};preds=[];folds=[]
 for test_start in pd.date_range('2026-02-01','2026-07-01',freq='MS'):
  test_end=test_start+pd.offsets.MonthBegin(1);cal_start=test_start-pd.offsets.MonthBegin(1)
  tr=np.where(exits<cal_start)[0];te=np.where((times>=test_start)&(times<test_end))[0]
  if len(tr)<200 or len(te)<20:continue
  mu=X[tr].reshape(-1,X.shape[-1]).mean(0);sd=X[tr].reshape(-1,X.shape[-1]).std(0);sd[sd<1e-6]=1
  Xtr=(X[tr]-mu)/sd;Xte=(X[te]-mu)/sd
  for name,Cls in models.items():
   model=Cls(X.shape[-1]);opt=torch.optim.AdamW(model.parameters(),lr=1e-3,weight_decay=1e-4);bce=nn.BCEWithLogitsLoss();mse=nn.SmoothL1Loss()
   ds=TensorDataset(torch.tensor(Xtr),torch.tensor(yr[tr]),torch.tensor(yh[tr]),torch.tensor(yp[tr]));dl=DataLoader(ds,batch_size=128,shuffle=True)
   model.train()
   for _ in range(epochs):
    for xb,rb,hb,pb in dl:
     o=model(xb);loss=mse(o[:,0],rb)+.5*bce(o[:,1],hb)+.5*bce(o[:,2],pb);opt.zero_grad();loss.backward();nn.utils.clip_grad_norm_(model.parameters(),2);opt.step()
   model.eval();
   with torch.no_grad():o=model(torch.tensor(Xte));pr=o[:,0].numpy();ph=torch.sigmoid(o[:,1]).numpy();pp=torch.sigmoid(o[:,2]).numpy()
   sr=pd.Series(pr).corr(pd.Series(yr[te]),method='spearman');hold_auc=float(pd.Series(ph).corr(pd.Series(yh[te]),method='spearman'));prot_auc=float(pd.Series(pp).corr(pd.Series(yp[te]),method='spearman'))
   folds.append({'month':test_start.strftime('%Y_%m'),'model':name,'train':len(tr),'test':len(te),'final_r_spearman':None if pd.isna(sr) else float(sr),'hold_rank':None if pd.isna(hold_auc) else float(hold_auc),'protect_rank':None if pd.isna(prot_auc) else float(prot_auc)})
   for k,ix in enumerate(te):preds.append({'month':test_start.strftime('%Y_%m'),'model':name,'time':str(times[ix]),'trade_key':meta[ix][2],'unrealized_r':meta[ix][3],'actual_final_r':float(yr[ix]),'actual_hold':float(yh[ix]),'actual_protect':float(yp[ix]),'pred_final_r':float(pr[k]),'p_hold':float(ph[k]),'p_protect':float(pp[k])})
 pdf=pd.DataFrame(preds);pdf.to_csv(pred_path,index=False)
 agg={}
 for name in models:
  z=[f for f in folds if f['model']==name]
  agg[name]={k:float(np.nanmean([f[k] if f[k] is not None else np.nan for f in z])) for k in ['final_r_spearman','hold_rank','protect_rank']}
 out={'schema':'v36_intra_trade_sequence_models_v1','models':['GRU48','causal_TCN48','Transformer48x2'],'sequence_len':X.shape[1],'targets':['final_r','future_upside_ge_0p5R','future_giveback_ge_0p5R'],'folds':folds,'mean':agg,'decision_rule':'diagnostic only; no reconstructed PnL. Only export policy if sequence heads show stable chronological signal; final economics require MT5.'}
 Path(summary_path).write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(agg,indent=2))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--common-files',required=True);ap.add_argument('--v34-run-folder',required=True);ap.add_argument('--book',default='norm10k_r0p5_continuous');ap.add_argument('--summary',required=True);ap.add_argument('--predictions',required=True);ap.add_argument('--epochs',type=int,default=25);a=ap.parse_args()
 df=prepare(Path(a.common_files),Path(a.v34_run_folder),a.book);X,yr,yh,yp,meta,feats=make_samples(df);print('V36 dataset',X.shape,'features',len(feats));train_eval(X,yr,yh,yp,meta,a.summary,a.predictions,a.epochs)
if __name__=='__main__':main()
