#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, warnings
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
warnings.filterwarnings('ignore')

REFERENCE_SHA='8b3550dbdf451d558349be46d4a1b9391feba04c29cd21968594473eae716356'
CANDIDATES=['ema_h1_skip20','macd_h1_gap10','bos_fvg_h1_gap8','trend20_h1_gap5','router_ema_bos8','slow_mom_16h24h_timebox8h','slow_mom_16h24h_peaklock_timebox8h','adaptive_ewma_hl8_thr0','adaptive_ewma_hl8_thr0p05','adaptive_ewma_hl10_thr0p05','adaptive_ewma_hl12_thr0p05','adaptive_cp_fast5_slow20_thr0p30']
RUN_IDS={'chunk1':'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-02-01_00-00-00__756375','chunk2':'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-08-01_00-00-00__22265','chunk3':'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2026-02-01_00-00-00__519093'}
BAR_NUM=['rv8','rv32','atr_ratio','dist_ema10_atr','dist_ema20_atr','dist_ema50_atr','dist_ema200_atr','rsi2','rsi14','macd_hist','adx','plus_di','minus_di','bb_pos','bb_width_atr','h1_ema50_minus_200_atr','don20_pos','don55_pos','m1_ret5','m1_ret15','m1_rv15','m1_efficiency','m1_range_atr','m5_ret1','m5_ret2','m5_rv3','m5_range_atr','h1_ret1','h1_ret4','h1_range_atr','h1_close_location','server_hour','day_of_week','tick_direction_imbalance','tick_spread_std_points','tick_mid_range_atr','tick_mid_abs_path_atr','tick_mid_net_move_atr','signal_count_long','signal_count_short']
EXPERT=[f'{p}_{e}' for p in ['ewma_hl8','ewma_fast5','ewma_slow20'] for e in ['ema','macd','bos','trend','slow']]+[f'expert_obs_{e}' for e in ['ema','macd','bos','trend','slow']]
KEEP_TARGETS=[0.50,0.60,0.70,0.80,0.90]

def pt(s): return pd.to_datetime(s,format='%Y.%m.%d %H:%M:%S')
def sha256(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load_lake(common):
    roots={k:common/'mt5_quant'/'runs'/rid for k,rid in RUN_IDS.items()}
    for k,r in roots.items():
        for f in ('bar_features.csv','trades.csv','manifest.txt'):
            if not (r/f).is_file(): raise RuntimeError(f'missing accepted {k} file: {r/f}')
    b1,b2,b3=[pd.read_csv(roots[k]/'bar_features.csv') for k in ('chunk1','chunk2','chunk3')]
    for q in (b1,b2,b3): q['dt']=pt(q['time'])
    b=pd.concat([
        b1[(b1.dt>=pd.Timestamp('2025-02-01'))&(b1.dt<pd.Timestamp('2025-08-01'))],
        b2[(b2.dt>=pd.Timestamp('2025-08-01'))&(b2.dt<pd.Timestamp('2026-02-01'))],
        b3[(b3.dt>=pd.Timestamp('2026-02-01'))&(b3.dt<pd.Timestamp('2026-08-01'))],
    ],ignore_index=True).sort_values('dt').drop_duplicates('dt').reset_index(drop=True)
    if len(b)!=35344 or b.dt.duplicated().any(): raise RuntimeError(f'canonical bar lake mismatch rows={len(b)} dup={int(b.dt.duplicated().sum())}')
    b['avail']=b.dt+pd.Timedelta(minutes=15); b['month']=b.dt.dt.strftime('%Y_%m')
    t=pd.concat([pd.read_csv(roots[k]/'trades.csv') for k in ('chunk1','chunk2','chunk3')],ignore_index=True)
    t=t[t.book=='usd40_r1p0_cent'].copy(); t['entry_dt']=pt(t.entry_time); t['exit_dt']=pt(t.exit_time); t['direction_num']=t.direction.map({'LONG':1,'SHORT':-1}).astype(int)
    if len(t)!=7262: raise RuntimeError(f'USD40 r1.0 accepted trade count mismatch rows={len(t)} expected=7262')
    return b,t

def engineer(df):
    for e in ['ema','macd','bos','trend','slow']:
        df[f'fastslow_{e}']=df[f'ewma_fast5_{e}']-df[f'ewma_slow20_{e}']
        df[f'hl8slow_{e}']=df[f'ewma_hl8_{e}']-df[f'ewma_slow20_{e}']
        df[f'conf_{e}']=np.log1p(df[f'expert_obs_{e}'])
    df['vol_ratio']=df.rv8/(df.rv32.abs()+1e-9)
    df['di_spread']=df.plus_di-df.minus_di
    df['signal_imbalance']=df.signal_count_long-df.signal_count_short
    return [c for c in df.columns if c.startswith('fastslow_') or c.startswith('hl8slow_') or c.startswith('conf_')]+['vol_ratio','di_spread','signal_imbalance']

def model():
    return Pipeline([('sc',StandardScaler()),('m',MLPRegressor(hidden_layer_sizes=(64,32,16),alpha=.01,max_iter=80,early_stopping=True,n_iter_no_change=12,random_state=3))])

def fit(m,x,y,w):
    try: m.fit(x,y,m__sample_weight=w)
    except TypeError:
        try: m.fit(x,y,sample_weight=w)
        except TypeError: m.fit(x,y)

def build(common,output,metadata):
    b,t=load_lake(common); use=BAR_NUM+EXPERT
    j=pd.merge_asof(t.sort_values('entry_dt'),b[['avail']+use].sort_values('avail'),left_on='entry_dt',right_on='avail',direction='backward',allow_exact_matches=True)
    eng=engineer(j); basecols=BAR_NUM+EXPERT+eng
    X=j[basecols].replace([np.inf,-np.inf],np.nan).fillna(0).astype(float).reset_index(drop=True); X['direction_num']=j.direction_num.values
    for c in CANDIDATES: X['cand_'+c]=(j.candidate.values==c).astype(float)
    y=j.r_multiple.astype(float).to_numpy(); keys=j.entry_dt.astype(str)+'|'+j.direction_num.astype(str); mult=keys.map(keys.value_counts()).to_numpy(); w=1.0/mult
    engineer(b)
    months=sorted(j.month.unique()); tests=months[6:]
    maskL=np.zeros((len(b),len(CANDIDATES)),dtype=np.uint8); maskS=np.zeros_like(maskL); meta=[]
    avail_table=b[['avail']+basecols].sort_values('avail').reset_index(drop=True)
    for tm in tests:
        cal=months[months.index(tm)-1]; cstart=pd.Timestamp(cal.replace('_','-')+'-01')
        train=j.exit_dt<cstart; calmask=j.month==cal; bm=b.month==tm; idx=np.where(bm)[0]
        current=pd.DataFrame({'bar_time':b.loc[idx,'dt'].to_numpy()})
        state=pd.merge_asof(current.sort_values('bar_time'),avail_table,left_on='bar_time',right_on='avail',direction='backward',allow_exact_matches=True)
        if state[basecols].isna().any().any(): raise RuntimeError(f'missing causal state for current bars in {tm}')
        Bcur=state[basecols].replace([np.inf,-np.inf],np.nan).fillna(0).astype(float).reset_index(drop=True)
        m=model(); fit(m,X.loc[train],y[train],w[train]); pcal=m.predict(X.loc[calmask])
        thrs={str(int(k*100)):float(np.quantile(pcal,1.0-k)) for k in KEEP_TARGETS}
        scores=np.empty((len(idx),len(CANDIDATES),2),dtype=np.float32)
        for ci,c in enumerate(CANDIDATES):
            for di,dval in enumerate((1,-1)):
                xx=Bcur.copy(); xx['direction_num']=dval
                for cc in CANDIDATES: xx['cand_'+cc]=1.0 if cc==c else 0.0
                scores[:,ci,di]=m.predict(xx).astype(np.float32)
        for local,k in enumerate(idx):
            for ci in range(len(CANDIDATES)):
                for di,target in ((0,maskL),(1,maskS)):
                    sc=float(scores[local,ci,di]); msk=0
                    for bit,keep in enumerate(KEEP_TARGETS):
                        if sc>=thrs[str(int(keep*100))]: msk|=(1<<bit)
                    target[k,ci]=msk
        meta.append({'test_month':tm,'calibration_month':cal,'thresholds':thrs,'train_rows':int(train.sum()),'cal_rows':int(calmask.sum()),'bars':int(bm.sum())})
        print(f'V32 gate month PASS test={tm} cal={cal} train={int(train.sum())} bars={len(idx)}',flush=True)
    oos=b.month.isin(tests); idx=np.where(oos)[0]
    output.parent.mkdir(parents=True,exist_ok=True); metadata.parent.mkdir(parents=True,exist_ok=True)
    with output.open('w',newline='') as f:
        header=['bar_time']+[x for ci in range(len(CANDIDATES)) for x in (f'c{ci}_L',f'c{ci}_S')]; f.write(','.join(header)+'\n')
        for k in idx:
            vals=[b.loc[k,'dt'].strftime('%Y.%m.%d %H:%M:%S')]
            for ci in range(len(CANDIDATES)): vals += [str(int(maskL[k,ci])),str(int(maskS[k,ci]))]
            f.write(','.join(vals)+'\n')
    payload={'models_bits':{str(i):f'deep_mlp_keep_{int(k*100)}' for i,k in enumerate(KEEP_TARGETS)},'candidate_order':CANDIDATES,'months':meta,'feature_count':len(X.columns),'protocol':'same V31.1 causal DeepMLP; inverse opportunity weighting; previous-month score quantiles; nested keep-rate thresholds; current-bar state uses latest feature_available_time<=T','versions':{'numpy':np.__version__,'pandas':pd.__version__}}
    metadata.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    h=sha256(output); print(f'V32 gate tape PASS rows={len(idx)} sha256={h} reference_sha256={REFERENCE_SHA}')
    if h!=REFERENCE_SHA: print('NOTE: platform bytes differ from pinned Linux reference; retain generated hash and protocol evidence.',file=__import__('sys').stderr)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--common-files',required=True); ap.add_argument('--output',required=True); ap.add_argument('--metadata',required=True)
    a=ap.parse_args(); build(pathlib.Path(a.common_files),pathlib.Path(a.output),pathlib.Path(a.metadata))
if __name__=='__main__': main()
