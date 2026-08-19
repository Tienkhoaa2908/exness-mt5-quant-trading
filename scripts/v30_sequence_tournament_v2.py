#!/usr/bin/env python3
"""True-sequence expected-R tournament for V30 causal lake.

Uses 64 historical M15 feature rows ending at the last row available at trade entry,
plus causal static trade context. No flattening of future bars, no broker connection.
Threshold protocol matches v30_trade_tournament_v2.py: previous-month score distribution,
frozen model, candidate-specific 60th percentile when calibration sample is sufficient.
"""
from __future__ import annotations

import argparse, json, math, os, random, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v30_trade_tournament_v2 as tab

SEED=29
SEQ_LEN=64
BATCH=256
EPOCHS=3
PATIENCE=1


def seed_all(seed=SEED):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)


def sequence_cols(trades: pd.DataFrame) -> list[str]:
    pref=[c for c in tab.numeric_columns(trades,"engineered_expert") if c.startswith("bar__")]
    return [c[5:] for c in pref]


def static_cols(trades: pd.DataFrame) -> list[str]:
    return [c for c in tab.numeric_columns(trades,"engineered_expert") if not c.startswith("bar__")]


class SeqTradeDS(Dataset):
    def __init__(self, xbars, xstatic, y, bar_idx, rows, seq_len=SEQ_LEN):
        self.xbars=xbars; self.xstatic=xstatic; self.y=y; self.bar_idx=bar_idx
        self.rows=np.asarray(rows,dtype=np.int64); self.seq_len=seq_len
    def __len__(self): return len(self.rows)
    def __getitem__(self,i):
        r=int(self.rows[i]); e=int(self.bar_idx[r]); s=e-self.seq_len+1
        return (torch.from_numpy(self.xbars[s:e+1]).float(), torch.from_numpy(self.xstatic[r]).float(), torch.tensor(self.y[r]).float())


class GRUModel(nn.Module):
    def __init__(self,nf,ns,h=24):
        super().__init__(); self.inp=nn.Sequential(nn.Linear(nf,16),nn.LayerNorm(16),nn.GELU()); self.gru=nn.GRU(16,h,batch_first=True); self.head=nn.Sequential(nn.Linear(h+ns,32),nn.GELU(),nn.Dropout(0.10),nn.Linear(32,1))
    def forward(self,x,s):
        z=self.inp(x); _,h=self.gru(z); q=h[-1]; return self.head(torch.cat([q,s],dim=1)).squeeze(1)


class CausalBlock(nn.Module):
    def __init__(self,c,d):
        super().__init__(); self.d=d; self.conv=nn.Conv1d(c,c,kernel_size=3,dilation=d,padding=0); self.norm=nn.GroupNorm(4,c); self.act=nn.GELU(); self.drop=nn.Dropout(0.08)
    def forward(self,x):
        y=torch.nn.functional.pad(x,(2*self.d,0)); y=self.drop(self.act(self.norm(self.conv(y)))); return x+y


class TCNModel(nn.Module):
    def __init__(self,nf,ns,h=24):
        super().__init__(); self.inp=nn.Linear(nf,h); self.net=nn.Sequential(CausalBlock(h,1),CausalBlock(h,2),CausalBlock(h,4),CausalBlock(h,8)); self.head=nn.Sequential(nn.Linear(h+ns,32),nn.GELU(),nn.Dropout(0.10),nn.Linear(32,1))
    def forward(self,x,s):
        z=self.inp(x).transpose(1,2); z=self.net(z); q=z[:,:,-1]; return self.head(torch.cat([q,s],dim=1)).squeeze(1)


class PatchTransformerModel(nn.Module):
    def __init__(self,nf,ns,seq_len=SEQ_LEN,patch=8,d=24):
        super().__init__(); assert seq_len%patch==0
        self.pre=nn.Sequential(nn.Linear(nf,16),nn.LayerNorm(16),nn.GELU()); self.patch=patch; self.np=seq_len//patch
        self.proj=nn.Linear(16*patch,d); self.pos=nn.Parameter(torch.zeros(1,self.np,d))
        layer=nn.TransformerEncoderLayer(d_model=d,nhead=4,dim_feedforward=64,batch_first=True,dropout=0.10,activation="gelu",norm_first=True)
        self.enc=nn.TransformerEncoder(layer,num_layers=1); self.head=nn.Sequential(nn.Linear(d+ns,32),nn.GELU(),nn.Dropout(0.10),nn.Linear(32,1))
    def forward(self,x,s):
        z=self.pre(x); b,t,f=z.shape; z=z.reshape(b,self.np,self.patch*f); z=self.enc(self.proj(z)+self.pos).mean(dim=1); return self.head(torch.cat([z,s],dim=1)).squeeze(1)


def make_model(name,nf,ns):
    if name=="gru": return GRUModel(nf,ns)
    if name=="tcn": return TCNModel(nf,ns)
    if name=="patch_transformer": return PatchTransformerModel(nf,ns)
    raise ValueError(name)


def fit_scaler(x: np.ndarray):
    med=np.nanmedian(x,axis=0); med=np.where(np.isfinite(med),med,0.0); xi=np.where(np.isfinite(x),x,med)
    lo=np.quantile(xi,0.005,axis=0); hi=np.quantile(xi,0.995,axis=0); xw=np.minimum(np.maximum(xi,lo),hi); mean=xw.mean(axis=0); std=xw.std(axis=0); std=np.where(std>1e-8,std,1.0)
    return med,lo,hi,mean,std


def apply_scaler(x,sc):
    med,lo,hi,mean,std=sc; xi=np.where(np.isfinite(x),x,med); xi=np.minimum(np.maximum(xi,lo),hi); return ((xi-mean)/std).astype(np.float32)


def static_matrix(df: pd.DataFrame, cols: list[str], cats: list[str], train_rows: np.ndarray):
    x=df[cols].apply(pd.to_numeric,errors="coerce").to_numpy(dtype=np.float64); sc=fit_scaler(x[train_rows]); xs=apply_scaler(x,sc)
    mapping={c:i for i,c in enumerate(cats)}; oh=np.zeros((len(df),len(cats)),dtype=np.float32)
    for r,c in enumerate(df["candidate"].astype(str).tolist()):
        if c in mapping: oh[r,mapping[c]]=1.0
    return np.concatenate([xs,oh],axis=1).astype(np.float32)


def loader(xb,xs,y,bi,rows,shuffle=False):
    return DataLoader(SeqTradeDS(xb,xs,y,bi,rows),batch_size=BATCH,shuffle=shuffle,num_workers=0)


def train_model(model, train_loader, val_loader, device):
    model.to(device); lossfn=nn.SmoothL1Loss(beta=0.5); opt=torch.optim.AdamW(model.parameters(),lr=8e-4,weight_decay=2e-4); best=None; bestv=float("inf"); stale=0
    for ep in range(EPOCHS):
        model.train()
        for xb,xs,y in train_loader:
            xb=xb.to(device); xs=xs.to(device); y=y.to(device); opt.zero_grad(set_to_none=True); p=model(xb,xs); loss=lossfn(p,y); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step()
        model.eval(); vals=[]
        with torch.no_grad():
            for xb,xs,y in val_loader: vals.append(float(lossfn(model(xb.to(device),xs.to(device)),y.to(device)).cpu()))
        v=float(np.mean(vals)) if vals else float("inf")
        if v < bestv-1e-4: bestv=v; best={k:t.detach().cpu().clone() for k,t in model.state_dict().items()}; stale=0
        else:
            stale+=1
            if stale>=PATIENCE: break
    if best is not None: model.load_state_dict(best)
    return model


def predict(model, dl, device):
    model.to(device).eval(); out=[]
    with torch.no_grad():
        for xb,xs,_ in dl: out.append(model(xb.to(device),xs.to(device)).cpu().numpy())
    return np.concatenate(out) if out else np.empty(0)


def run_model(bars: pd.DataFrame, trades: pd.DataFrame, name: str, checkpoint: Path | None = None) -> pd.DataFrame:
    seed_all(); torch.set_num_threads(min(4,os.cpu_count() or 1)); device="cpu"; cats=sorted(trades["candidate"].astype(str).unique()); bcols=sequence_cols(trades); scols=static_cols(trades)
    rawb=bars[bcols].apply(pd.to_numeric,errors="coerce").to_numpy(dtype=np.float64); y=trades["r_multiple"].to_numpy(dtype=np.float32); bi=trades["bar_index"].to_numpy(dtype=int)
    rows=[]; done=set()
    if checkpoint is not None and checkpoint.exists():
        old=pd.read_csv(checkpoint); rows=old.to_dict("records"); done=set(old["month"].astype(str)) if not old.empty else set()
    for cal_m,test_m in tab.fold_months(trades):
        if test_m in done: continue
        cal_start=tab.month_start(cal_m); test_start=tab.month_start(test_m)
        train_idx=np.flatnonzero((trades["exit_time"]<cal_start).to_numpy() & (trades["sequence_ready"].to_numpy()==1))
        cal_idx=np.flatnonzero(((trades["month"].astype(str)==cal_m)&(trades["exit_time"]<test_start)&(trades["sequence_ready"]==1)).to_numpy())
        test_idx=np.flatnonzero(((trades["month"].astype(str)==test_m)&(trades["sequence_ready"]==1)).to_numpy())
        if len(train_idx)<tab.MIN_TRAIN or len(cal_idx)<tab.MIN_CAL or len(test_idx)<tab.MIN_TEST: continue
        hist_end=np.searchsorted(bars["feature_available_time"].to_numpy(dtype="datetime64[ns]"),np.datetime64(cal_start),side="left")
        bsc=fit_scaler(rawb[:hist_end]); xb=apply_scaler(rawb,bsc); xs=static_matrix(trades,scols,cats,train_idx)
        ordered=train_idx[np.argsort(trades.iloc[train_idx]["entry_time"].to_numpy())]; cut=max(1,int(len(ordered)*0.85)); tr_idx=ordered[:cut]; va_idx=ordered[cut:]
        seed_all(); model=make_model(name,len(bcols),xs.shape[1]); model=train_model(model,loader(xb,xs,y,bi,tr_idx,True),loader(xb,xs,y,bi,va_idx,False),device)
        pcal=predict(model,loader(xb,xs,y,bi,cal_idx,False),device); pte=predict(model,loader(xb,xs,y,bi,test_idx,False),device)
        cal=trades.iloc[cal_idx]; test=trades.iloc[test_idx]; th=tab.score_thresholds(cal,pcal,True); sel=tab.apply_threshold(test,pte,th,True)
        rec={"cal_month":cal_m,"month":test_m,"model":name,"train_n":len(train_idx),"cal_n":len(cal_idx),"n_features":len(bcols),"static_dim":xs.shape[1],"global_threshold":th["__global__"]}; rec.update(tab.test_metrics(test,pte,sel)); rows.append(rec)
        if checkpoint is not None: pd.DataFrame(rows).to_csv(checkpoint,index=False)
    return pd.DataFrame(rows)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("bars_pickle",type=Path); ap.add_argument("trades_pickle",type=Path); ap.add_argument("--model",choices=["gru","tcn","patch_transformer"],required=True); ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args(); bars=pd.read_pickle(a.bars_pickle); trades=pd.read_pickle(a.trades_pickle)
    trades["entry_time"]=pd.to_datetime(trades["entry_time"]); trades["exit_time"]=pd.to_datetime(trades["exit_time"]); trades["direction_code"]=trades["direction"].map({"LONG":1.0,"SHORT":-1.0}).astype(float); a.output.parent.mkdir(parents=True,exist_ok=True)
    out=run_model(bars,trades,a.model,a.output); out.to_csv(a.output,index=False); summary=tab.summarize_variant(out); print(json.dumps(summary,indent=2)); a.output.with_suffix(".summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")

if __name__=="__main__": main()
