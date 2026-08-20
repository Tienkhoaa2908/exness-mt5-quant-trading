#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd

RUN_IDS = [
    'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-02-01_00-00-00__756375',
    'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-08-01_00-00-00__22265',
    'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2026-02-01_00-00-00__519093',
]
SPECIALISTS = ['smc_ict','price_action','wyckoff','microstructure','confluence']

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load_lake(common: Path) -> pd.DataFrame:
    parts=[]
    for rid in RUN_IDS:
        p=common/'mt5_quant'/'runs'/rid/'bar_features.csv'
        if not p.is_file(): raise FileNotFoundError(p)
        d=pd.read_csv(p)
        d['time']=pd.to_datetime(d['time'],format='%Y.%m.%d %H:%M:%S',errors='raise')
        parts.append(d)
    x=pd.concat(parts,ignore_index=True)
    # Each tester chunk contains one pre-roll row. Timestamp is the bar OPEN time.
    x=x.sort_values('time').drop_duplicates('time',keep='last').reset_index(drop=True)
    if x['time'].duplicated().any(): raise RuntimeError('duplicate bar timestamps after stitch')
    # The row describes the just-closed M15 bar and is only causal after its close.
    x['feature_available_time']=x['time']+pd.Timedelta(minutes=15)
    return x

def confirmed_swings(x: pd.DataFrame,left:int=3,right:int=3):
    h=x.high.to_numpy(float); l=x.low.to_numpy(float); n=len(x)
    confirm_hi=np.full(n,np.nan); confirm_lo=np.full(n,np.nan)
    for i in range(left,n-right):
        if h[i] > np.max(h[i-left:i]) and h[i] >= np.max(h[i+1:i+right+1]):
            confirm_hi[i+right]=h[i]
        if l[i] < np.min(l[i-left:i]) and l[i] <= np.min(l[i+1:i+right+1]):
            confirm_lo[i+right]=l[i]
    last_hi=np.full(n,np.nan); last_lo=np.full(n,np.nan)
    hi=np.nan; lo=np.nan
    for i in range(n):
        # use pivots confirmed on or before this CLOSED bar
        if np.isfinite(confirm_hi[i]): hi=confirm_hi[i]
        if np.isfinite(confirm_lo[i]): lo=confirm_lo[i]
        last_hi[i]=hi; last_lo[i]=lo
    return last_hi,last_lo,confirm_hi,confirm_lo

def build_closed_bar_specialists(x: pd.DataFrame) -> pd.DataFrame:
    x=x.copy()
    n=len(x)
    atr=x.atr14.replace(0,np.nan).to_numpy(float)
    o=x.open.to_numpy(float); h=x.high.to_numpy(float); l=x.low.to_numpy(float); c=x.close.to_numpy(float)
    last_hi,last_lo,confirm_hi,confirm_lo=confirmed_swings(x,3,3)

    # ---------- SMC / ICT, explicitly causal ----------
    prior_hi=np.roll(last_hi,1); prior_lo=np.roll(last_lo,1); prior_hi[0]=np.nan; prior_lo[0]=np.nan
    bull_bos=np.isfinite(prior_hi) & (c>prior_hi) & (np.roll(c,1)<=prior_hi)
    bear_bos=np.isfinite(prior_lo) & (c<prior_lo) & (np.roll(c,1)>=prior_lo)
    bull_sweep=np.isfinite(prior_lo) & (l<prior_lo) & (c>prior_lo)
    bear_sweep=np.isfinite(prior_hi) & (h>prior_hi) & (c<prior_hi)
    bull_fvg=np.zeros(n,bool); bear_fvg=np.zeros(n,bool)
    bull_fvg[2:]=l[2:] > h[:-2]
    bear_fvg[2:]=h[2:] < l[:-2]
    bull_fvg_recent=pd.Series(bull_fvg).rolling(8,min_periods=1).max().to_numpy(bool)
    bear_fvg_recent=pd.Series(bear_fvg).rolling(8,min_periods=1).max().to_numpy(bool)
    # displacement is based only on the bar that just closed
    body=np.abs(c-o); disp=(body/np.where(np.isfinite(atr),atr,np.nan))
    bull_disp=(c>o)&(disp>=0.55); bear_disp=(c<o)&(disp>=0.55)
    # premium/discount within last confirmed swing range
    swing_mid=(last_hi+last_lo)/2
    discount=np.isfinite(swing_mid)&(c<swing_mid); premium=np.isfinite(swing_mid)&(c>swing_mid)
    smc_long=(bull_bos.astype(int)*32 + bull_sweep.astype(int)*28 + bull_fvg_recent.astype(int)*15 + bull_disp.astype(int)*15 + discount.astype(int)*10)
    smc_short=(bear_bos.astype(int)*32 + bear_sweep.astype(int)*28 + bear_fvg_recent.astype(int)*15 + bear_disp.astype(int)*15 + premium.astype(int)*10)
    smc_dir=np.where((smc_long>=45)&(smc_long>smc_short),1,np.where((smc_short>=45)&(smc_short>smc_long),-1,0))
    smc_score=np.maximum(smc_long,smc_short).clip(0,100)

    # ---------- Price Action ----------
    prev_o=np.roll(o,1); prev_c=np.roll(c,1); prev_h=np.roll(h,1); prev_l=np.roll(l,1)
    prev_o[0]=prev_c[0]=prev_h[0]=prev_l[0]=np.nan
    bull_eng=(c>o)&(prev_c<prev_o)&(c>=prev_o)&(o<=prev_c)
    bear_eng=(c<o)&(prev_c>prev_o)&(c<=prev_o)&(o>=prev_c)
    rng=np.maximum(h-l,1e-12); lower=(np.minimum(o,c)-l)/rng; upper=(h-np.maximum(o,c))/rng; br=body/rng
    bull_pin=(lower>=0.55)&(upper<=0.20)&(br<=0.40)
    bear_pin=(upper>=0.55)&(lower<=0.20)&(br<=0.40)
    high20=pd.Series(h).rolling(20,min_periods=20).max().shift(1).to_numpy()
    low20=pd.Series(l).rolling(20,min_periods=20).min().shift(1).to_numpy()
    bull_break=np.isfinite(high20)&(c>high20); bear_break=np.isfinite(low20)&(c<low20)
    inside=(h<prev_h)&(l>prev_l)
    inside_prev=np.roll(inside,1); inside_prev[0]=False
    bull_inside_break=inside_prev&(c>prev_h); bear_inside_break=inside_prev&(c<prev_l)
    range_atr=x.range_atr.to_numpy(float)
    q25=pd.Series(range_atr).rolling(64,min_periods=32).quantile(.25).shift(1).to_numpy()
    compressed=np.isfinite(q25)&(range_atr<=q25)
    compression_recent=pd.Series(compressed).rolling(4,min_periods=1).max().shift(1,fill_value=0).to_numpy(bool)
    pa_long=bull_eng.astype(int)*30+bull_pin.astype(int)*22+bull_break.astype(int)*30+bull_inside_break.astype(int)*22+compression_recent.astype(int)*8+(x.h1_ret1.to_numpy(float)>0).astype(int)*8
    pa_short=bear_eng.astype(int)*30+bear_pin.astype(int)*22+bear_break.astype(int)*30+bear_inside_break.astype(int)*22+compression_recent.astype(int)*8+(x.h1_ret1.to_numpy(float)<0).astype(int)*8
    pa_dir=np.where((pa_long>=38)&(pa_long>pa_short),1,np.where((pa_short>=38)&(pa_short>pa_long),-1,0))
    pa_score=np.maximum(pa_long,pa_short).clip(0,100)

    # ---------- Wyckoff-style causal phase proxies ----------
    rhi=pd.Series(h).rolling(96,min_periods=48).max().shift(1).to_numpy()
    rlo=pd.Series(l).rolling(96,min_periods=48).min().shift(1).to_numpy()
    width=rhi-rlo; loc=np.where(width>0,(c-rlo)/width,np.nan)
    tv=x.tick_volume.astype(float)
    tv_mean=tv.rolling(64,min_periods=32).mean().shift(1); tv_std=tv.rolling(64,min_periods=32).std(ddof=0).shift(1).replace(0,np.nan)
    vol_z=((tv-tv_mean)/tv_std).fillna(0).to_numpy()
    spring=np.isfinite(rlo)&(l<rlo)&(c>rlo)&(loc<0.35)
    upthrust=np.isfinite(rhi)&(h>rhi)&(c<rhi)&(loc>0.65)
    effort_result=np.abs(x.logret1.to_numpy(float))/np.maximum(np.abs(vol_z),0.5)
    absorption=(np.abs(vol_z)>=1.2)&(range_atr<np.nanmedian(range_atr[np.isfinite(range_atr)]))
    bull_absorb=absorption&(c>=o)&(loc<0.5); bear_absorb=absorption&(c<=o)&(loc>0.5)
    accumulation=np.isfinite(loc)&(loc<0.45)&(x.dist_ema200_atr.to_numpy(float)>-3.0)
    distribution=np.isfinite(loc)&(loc>0.55)&(x.dist_ema200_atr.to_numpy(float)<3.0)
    wy_long=spring.astype(int)*45+bull_absorb.astype(int)*20+accumulation.astype(int)*15+(x.m1_efficiency.to_numpy(float)>0.35).astype(int)*10+(x.h1_ret4.to_numpy(float)>0).astype(int)*10
    wy_short=upthrust.astype(int)*45+bear_absorb.astype(int)*20+distribution.astype(int)*15+(x.m1_efficiency.to_numpy(float)>0.35).astype(int)*10+(x.h1_ret4.to_numpy(float)<0).astype(int)*10
    wy_dir=np.where((wy_long>=45)&(wy_long>wy_short),1,np.where((wy_short>=45)&(wy_short>wy_long),-1,0))
    wy_score=np.maximum(wy_long,wy_short).clip(0,100)

    # ---------- Tick/microstructure proxy; NOT true L2/L3 order flow ----------
    imb=x.tick_direction_imbalance.to_numpy(float)
    net=x.tick_mid_net_move_atr.to_numpy(float); path=x.tick_mid_abs_path_atr.to_numpy(float)
    eff=np.divide(net,np.maximum(path,1e-9))
    m1up=x.m1_up_fraction.to_numpy(float); m1eff=x.m1_efficiency.to_numpy(float)
    spread_mean=x.tick_spread_mean_points.to_numpy(float); spread_std=x.tick_spread_std_points.to_numpy(float)
    spread_stable=(spread_std<=pd.Series(spread_std).rolling(64,min_periods=32).median().shift(1).fillna(np.inf).to_numpy())
    micro_long=(imb>=0.12).astype(int)*30+(eff>=0.18).astype(int)*25+(m1up>=0.58).astype(int)*20+(m1eff>=0.35).astype(int)*15+spread_stable.astype(int)*10
    micro_short=(imb<=-0.12).astype(int)*30+(eff<=-0.18).astype(int)*25+(m1up<=0.42).astype(int)*20+(m1eff>=0.35).astype(int)*15+spread_stable.astype(int)*10
    micro_dir=np.where((micro_long>=50)&(micro_long>micro_short),1,np.where((micro_short>=50)&(micro_short>micro_long),-1,0))
    micro_score=np.maximum(micro_long,micro_short).clip(0,100)

    # ---------- Deterministic confluence specialist ----------
    dirs=np.vstack([smc_dir,pa_dir,wy_dir,micro_dir]).T
    scores=np.vstack([smc_score,pa_score,wy_score,micro_score]).T
    con_dir=np.zeros(n,int); con_score=np.zeros(n,float)
    for i in range(n):
        pos=dirs[i]>0; neg=dirs[i]<0
        if pos.sum()>=2 and pos.sum()>neg.sum():
            con_dir[i]=1; con_score[i]=scores[i,pos].mean()+5*(pos.sum()-2)
        elif neg.sum()>=2 and neg.sum()>pos.sum():
            con_dir[i]=-1; con_score[i]=scores[i,neg].mean()+5*(neg.sum()-2)
    con_score=np.clip(con_score,0,100)

    out=pd.DataFrame({
        'feature_time':x.time,
        'feature_available_time':x.feature_available_time,
        'smc_ict_dir':smc_dir,'smc_ict_score':smc_score,
        'price_action_dir':pa_dir,'price_action_score':pa_score,
        'wyckoff_dir':wy_dir,'wyckoff_score':wy_score,
        'microstructure_dir':micro_dir,'microstructure_score':micro_score,
        'confluence_dir':con_dir,'confluence_score':con_score,
        'smc_bull_bos':bull_bos.astype(int),'smc_bear_bos':bear_bos.astype(int),
        'smc_bull_sweep':bull_sweep.astype(int),'smc_bear_sweep':bear_sweep.astype(int),
        'smc_bull_fvg_recent':bull_fvg_recent.astype(int),'smc_bear_fvg_recent':bear_fvg_recent.astype(int),
        'wyckoff_spring':spring.astype(int),'wyckoff_upthrust':upthrust.astype(int),
    })
    return out

def asof_decision_tape(x: pd.DataFrame, f: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    decisions=pd.DataFrame({'time':x['time'].drop_duplicates().sort_values()})
    start=pd.Timestamp(start); end=pd.Timestamp(end)
    decisions=decisions[(decisions.time>=start)&(decisions.time<end)].copy()
    # A specialist state is usable only when its source closed-bar feature row is available.
    src=f.sort_values('feature_available_time')
    tape=pd.merge_asof(decisions.sort_values('time'),src,left_on='time',right_on='feature_available_time',direction='backward',allow_exact_matches=True)
    if tape['feature_time'].isna().any():
        raise RuntimeError('missing causal specialist state for some decision bars')
    if (tape.feature_available_time>tape.time).any():
        raise RuntimeError('lookahead detected: feature availability after decision time')
    # Keep the MT5-facing schema compact and deterministic.
    cols=['time']
    for s in SPECIALISTS: cols += [f'{s}_dir',f'{s}_score']
    tape=tape[cols].copy()
    tape['time']=tape.time.dt.strftime('%Y.%m.%d %H:%M:%S')
    for c in tape.columns[1:]:
        if c.endswith('_dir'): tape[c]=tape[c].astype(int)
        else: tape[c]=tape[c].round(6)
    return tape

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--common-files',required=True)
    ap.add_argument('--output',required=True)
    ap.add_argument('--metadata',required=True)
    ap.add_argument('--start',default='2025-08-01')
    ap.add_argument('--end',default='2026-08-01')
    a=ap.parse_args()
    common=Path(a.common_files); out=Path(a.output); meta=Path(a.metadata)
    x=load_lake(common); f=build_closed_bar_specialists(x); tape=asof_decision_tape(x,f,a.start,a.end)
    out.parent.mkdir(parents=True,exist_ok=True); tape.to_csv(out,index=False,lineterminator='\n')
    counts={s:{'long':int((tape[f'{s}_dir']==1).sum()),'short':int((tape[f'{s}_dir']==-1).sum()),'flat':int((tape[f'{s}_dir']==0).sum())} for s in SPECIALISTS}
    m={'schema':'v34_parallel_alpha_tape_v1','causal_rule':'feature_available_time <= decision_bar_time','start':a.start,'end':a.end,'rows':len(tape),'sha256':sha256(out),'specialists':SPECIALISTS,'signal_counts':counts,'notes':['SMC pivots confirmed only after right-side bars close','microstructure is L1/tick-path proxy, not true L2/L3 order flow','no future mitigation/fill information used in entry signals']}
    meta.write_text(json.dumps(m,indent=2),encoding='utf-8')
    print(f"V34 alpha tape PASS rows={len(tape)} sha256={m['sha256']}")
    print(json.dumps(counts,indent=2))
if __name__=='__main__': main()
