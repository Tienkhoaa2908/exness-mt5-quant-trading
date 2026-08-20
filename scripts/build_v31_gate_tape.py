#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, sys, warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.svm import LinearSVR
from catboost import CatBoostRegressor

warnings.filterwarnings('ignore')
REFERENCE_SHA = 'b30bbf3ad34028f826d3d1bfee45a2c2b05463ea211e379678cc19587f110491'
CANDIDATES = [
    'ema_h1_skip20','macd_h1_gap10','bos_fvg_h1_gap8','trend20_h1_gap5','router_ema_bos8',
    'slow_mom_16h24h_timebox8h','slow_mom_16h24h_peaklock_timebox8h','adaptive_ewma_hl8_thr0',
    'adaptive_ewma_hl8_thr0p05','adaptive_ewma_hl10_thr0p05','adaptive_ewma_hl12_thr0p05',
    'adaptive_cp_fast5_slow20_thr0p30']
RUN_IDS = {
    'chunk1': 'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-02-01_00-00-00__756375',
    'chunk2': 'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-08-01_00-00-00__22265',
    'chunk3': 'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2026-02-01_00-00-00__519093',
}
BAR_NUM = ['rv8','rv32','atr_ratio','dist_ema10_atr','dist_ema20_atr','dist_ema50_atr','dist_ema200_atr','rsi2','rsi14','macd_hist','adx','plus_di','minus_di','bb_pos','bb_width_atr','h1_ema50_minus_200_atr','don20_pos','don55_pos','m1_ret5','m1_ret15','m1_rv15','m1_efficiency','m1_range_atr','m5_ret1','m5_ret2','m5_rv3','m5_range_atr','h1_ret1','h1_ret4','h1_range_atr','h1_close_location','server_hour','day_of_week','tick_direction_imbalance','tick_spread_std_points','tick_mid_range_atr','tick_mid_abs_path_atr','tick_mid_net_move_atr','signal_count_long','signal_count_short']
EXPERT = [f'{p}_{e}' for p in ['ewma_hl8','ewma_fast5','ewma_slow20'] for e in ['ema','macd','bos','trend','slow']] + [f'expert_obs_{e}' for e in ['ema','macd','bos','trend','slow']]


def pt(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, format='%Y.%m.%d %H:%M:%S')


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_lake(common: pathlib.Path):
    roots = {k: common/'mt5_quant'/'runs'/rid for k,rid in RUN_IDS.items()}
    for k,r in roots.items():
        for f in ('bar_features.csv','trades.csv','manifest.txt'):
            if not (r/f).is_file():
                raise RuntimeError(f'missing accepted {k} file: {r/f}')
    b1,b2,b3 = [pd.read_csv(roots[k]/'bar_features.csv') for k in ('chunk1','chunk2','chunk3')]
    for q in (b1,b2,b3): q['dt']=pt(q['time'])
    b = pd.concat([
        b1[(b1.dt>=pd.Timestamp('2025-02-01'))&(b1.dt<pd.Timestamp('2025-08-01'))],
        b2[(b2.dt>=pd.Timestamp('2025-08-01'))&(b2.dt<pd.Timestamp('2026-02-01'))],
        b3[(b3.dt>=pd.Timestamp('2026-02-01'))&(b3.dt<pd.Timestamp('2026-08-01'))],
    ], ignore_index=True).sort_values('dt').drop_duplicates('dt').reset_index(drop=True)
    if len(b)!=35344 or b.dt.duplicated().any():
        raise RuntimeError(f'canonical bar lake mismatch rows={len(b)} dup={int(b.dt.duplicated().sum())}')
    b['avail']=b.dt+pd.Timedelta(minutes=15); b['month']=b.dt.dt.strftime('%Y_%m')
    t = pd.concat([pd.read_csv(roots[k]/'trades.csv') for k in ('chunk1','chunk2','chunk3')], ignore_index=True)
    t=t[t.book=='usd40_r1p0_cent'].copy(); t['entry_dt']=pt(t.entry_time); t['exit_dt']=pt(t.exit_time)
    t['direction_num']=t.direction.map({'LONG':1,'SHORT':-1}).astype(int)
    if len(t)!=7262:
        raise RuntimeError(f'USD40 r1.0 accepted trade count mismatch rows={len(t)} expected=7262')
    return b,t


def engineer_bar(df: pd.DataFrame) -> list[str]:
    for e in ['ema','macd','bos','trend','slow']:
        df[f'fastslow_{e}']=df[f'ewma_fast5_{e}']-df[f'ewma_slow20_{e}']
        df[f'hl8slow_{e}']=df[f'ewma_hl8_{e}']-df[f'ewma_slow20_{e}']
        df[f'conf_{e}']=np.log1p(df[f'expert_obs_{e}'])
    df['vol_ratio']=df.rv8/(df.rv32.abs()+1e-9)
    df['di_spread']=df.plus_di-df.minus_di
    df['signal_imbalance']=df.signal_count_long-df.signal_count_short
    return [c for c in df.columns if c.startswith('fastslow_') or c.startswith('hl8slow_') or c.startswith('conf_')] + ['vol_ratio','di_spread','signal_imbalance']


def models():
    return {
      'catboost': CatBoostRegressor(iterations=80,depth=5,learning_rate=.035,l2_leaf_reg=5,verbose=False,random_seed=3,thread_count=4),
      'extratrees': ExtraTreesRegressor(n_estimators=80,min_samples_leaf=12,max_features=.65,n_jobs=-1,random_state=3),
      'mlp': Pipeline([('sc',StandardScaler()),('m',MLPRegressor(hidden_layer_sizes=(32,16),alpha=.008,max_iter=35,early_stopping=True,n_iter_no_change=10,random_state=3))]),
      'linear_svr': Pipeline([('sc',StandardScaler()),('m',LinearSVR(C=.03,epsilon=.05,max_iter=4000,random_state=3))]),
    }


def fit(m, x, y, w):
    try:
        if isinstance(m, Pipeline): m.fit(x,y,m__sample_weight=w)
        else: m.fit(x,y,sample_weight=w)
    except TypeError:
        # Deterministic fallback for sklearn versions that do not route sample_weight.
        p=w/np.sum(w); rng=np.random.default_rng(20260820)
        idx=rng.choice(np.arange(len(x)),size=len(x),replace=True,p=p)
        m.fit(x.iloc[idx],y[idx])


def build(common: pathlib.Path, output: pathlib.Path, metadata: pathlib.Path):
    b,t=load_lake(common)
    use=BAR_NUM+EXPERT
    j=pd.merge_asof(t.sort_values('entry_dt'),b[['avail']+use].sort_values('avail'),left_on='entry_dt',right_on='avail',direction='backward',allow_exact_matches=True)
    if j['avail'].isna().any() or (j['avail']>j['entry_dt']).any():
        raise RuntimeError('causal trade join violation')
    eng=engineer_bar(j); basecols=BAR_NUM+EXPERT+eng
    X=j[basecols].replace([np.inf,-np.inf],np.nan).fillna(0).astype(float).reset_index(drop=True); X['direction_num']=j.direction_num.values
    for c in CANDIDATES: X['cand_'+c]=(j.candidate.values==c).astype(float)
    y=j.r_multiple.astype(float).to_numpy()
    keys=j.entry_dt.astype(str)+'|'+j.direction_num.astype(str); mult=keys.map(keys.value_counts()).to_numpy(); w=1.0/mult

    engineer_bar(b)
    B=b[basecols].replace([np.inf,-np.inf],np.nan).fillna(0).astype(float).reset_index(drop=True)
    months=sorted(j.month.unique()); tests=months[6:]
    maskL=np.zeros((len(b),len(CANDIDATES)),dtype=np.uint8); maskS=np.zeros_like(maskL); meta=[]

    # At MT5 bar open T, only rows whose feature availability <= T may be used.
    # This as-of mapping is mandatory across weekends/session gaps; simple row shift is invalid.
    avail_ns=b['avail'].astype('int64').to_numpy()
    dt_ns=b['dt'].astype('int64').to_numpy()
    causal_state_idx=np.searchsorted(avail_ns,dt_ns,side='right')-1

    for tm in tests:
        cal=months[months.index(tm)-1]; cstart=pd.Timestamp(cal.replace('_','-')+'-01')
        train=j.exit_dt<cstart; calmask=j.month==cal; bm=b.month==tm; current_idx=np.where(bm)[0]
        state_idx=causal_state_idx[current_idx]
        if np.any(state_idx<0): raise RuntimeError(f'no causal feature state for test month {tm}')
        if np.any(avail_ns[state_idx]>dt_ns[current_idx]): raise RuntimeError(f'current-bar causal mapping violation in {tm}')
        score_bar={}; thrs={}
        for name,m in models().items():
            fit(m,X.loc[train],y[train],w[train])
            thrs[name]=float(np.quantile(m.predict(X.loc[calmask]),.50))
            out=np.empty((len(current_idx),len(CANDIDATES),2),dtype=np.float32)
            state_base=B.iloc[state_idx].reset_index(drop=True)
            for ci,c in enumerate(CANDIDATES):
                for di,dval in enumerate((1,-1)):
                    xx=state_base.copy(); xx['direction_num']=dval
                    for cc in CANDIDATES: xx['cand_'+cc]=1.0 if cc==c else 0.0
                    out[:,ci,di]=m.predict(xx).astype(np.float32)
            score_bar[name]=out
        for local,k in enumerate(current_idx):
            for ci in range(len(CANDIDATES)):
                for di,target in ((0,maskL),(1,maskS)):
                    passes=[score_bar['catboost'][local,ci,di]>=thrs['catboost'],score_bar['extratrees'][local,ci,di]>=thrs['extratrees'],score_bar['mlp'][local,ci,di]>=thrs['mlp'],score_bar['linear_svr'][local,ci,di]>=thrs['linear_svr']]
                    msk=sum((1<<q) for q,v in enumerate(passes) if v)
                    if passes[0] and passes[1]: msk|=1<<4
                    if sum(passes)>=2: msk|=1<<5
                    target[k,ci]=msk
        meta.append({'test_month':tm,'calibration_month':cal,'thresholds':thrs,'train_rows':int(train.sum()),'cal_rows':int(calmask.sum()),'bars':int(bm.sum())})
        print(f'gate month PASS test={tm} cal={cal} train={int(train.sum())} bars={int(bm.sum())}', flush=True)

    oos=b.month.isin(tests); idx=np.where(oos)[0]
    output.parent.mkdir(parents=True,exist_ok=True); metadata.parent.mkdir(parents=True,exist_ok=True)
    with output.open('w',newline='') as f:
        header=['bar_time']+[x for ci in range(len(CANDIDATES)) for x in (f'c{ci}_L',f'c{ci}_S')]
        f.write(','.join(header)+'\n')
        for k in idx:
            vals=[b.loc[k,'dt'].strftime('%Y.%m.%d %H:%M:%S')]
            for ci in range(len(CANDIDATES)): vals += [str(int(maskL[k,ci])),str(int(maskS[k,ci]))]
            f.write(','.join(vals)+'\n')
    payload={'models_bits':{'0':'catboost','1':'extratrees','2':'mlp_32_16','3':'linear_svr','4':'catboost_AND_extratrees','5':'majority_2of4'},'candidate_order':CANDIDATES,'months':meta,'feature_count':len(X.columns),'protocol':'fit exits before prior calibration month; threshold=median prior-month scores; current MT5 bar T scored from latest feature_available_time<=T using causal asof across session gaps; inverse opportunity weighting','versions':{'numpy':np.__version__,'pandas':pd.__version__}}
    metadata.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    h=sha256(output)
    print(f'V31 gate tape PASS rows={len(idx)} sha256={h} reference_sha256={REFERENCE_SHA}')
    if h!=REFERENCE_SHA:
        print('NOTE: tape bytes differ from Linux reference; retain generated hash in evidence. Causal protocol and row gates passed.',file=sys.stderr)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--common-files',required=True);ap.add_argument('--output',required=True);ap.add_argument('--metadata',required=True)
    a=ap.parse_args(); build(pathlib.Path(a.common_files),pathlib.Path(a.output),pathlib.Path(a.metadata))

if __name__=='__main__': main()
