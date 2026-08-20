#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, pathlib, warnings
import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

CANDIDATES=[
'ema_h1_skip20','macd_h1_gap10','bos_fvg_h1_gap8','trend20_h1_gap5','router_ema_bos8',
'slow_mom_16h24h_timebox8h','slow_mom_16h24h_peaklock_timebox8h','adaptive_ewma_hl8_thr0',
'adaptive_ewma_hl8_thr0p05','adaptive_ewma_hl10_thr0p05','adaptive_ewma_hl12_thr0p05',
'adaptive_cp_fast5_slow20_thr0p30']
RUN_IDS={
'chunk1':'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-02-01_00-00-00__756375',
'chunk2':'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-08-01_00-00-00__22265',
'chunk3':'ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2026-02-01_00-00-00__519093'}
BAR_NUM=['rv8','rv32','atr_ratio','dist_ema10_atr','dist_ema20_atr','dist_ema50_atr','dist_ema200_atr',
'rsi2','rsi14','macd_hist','adx','plus_di','minus_di','bb_pos','bb_width_atr','h1_ema50_minus_200_atr',
'don20_pos','don55_pos','m1_ret5','m1_ret15','m1_rv15','m1_efficiency','m1_range_atr','m5_ret1',
'm5_ret2','m5_rv3','m5_range_atr','h1_ret1','h1_ret4','h1_range_atr','h1_close_location','server_hour',
'day_of_week','tick_direction_imbalance','tick_spread_std_points','tick_mid_range_atr',
'tick_mid_abs_path_atr','tick_mid_net_move_atr','signal_count_long','signal_count_short']
EXPERT=[f'{p}_{e}' for p in ['ewma_hl8','ewma_fast5','ewma_slow20'] for e in ['ema','macd','bos','trend','slow']]
EXPERT += [f'expert_obs_{e}' for e in ['ema','macd','bos','trend','slow']]
TARGETS=['r_multiple','mfe_r','adverse_r','giveback_r']

def pt(s): return pd.to_datetime(s,format='%Y.%m.%d %H:%M:%S')

def engineer_bar(df):
    out=[]
    for e in ['ema','macd','bos','trend','slow']:
        for name,expr in [
            (f'fastslow_{e}',df[f'ewma_fast5_{e}']-df[f'ewma_slow20_{e}']),
            (f'hl8slow_{e}',df[f'ewma_hl8_{e}']-df[f'ewma_slow20_{e}']),
            (f'conf_{e}',np.log1p(df[f'expert_obs_{e}']))]:
            df[name]=expr; out.append(name)
    df['vol_ratio']=df.rv8/(df.rv32.abs()+1e-9); out.append('vol_ratio')
    df['di_spread']=df.plus_di-df.minus_di; out.append('di_spread')
    df['signal_imbalance']=df.signal_count_long-df.signal_count_short; out.append('signal_imbalance')
    return out

def load(common:pathlib.Path):
    roots={k:common/'mt5_quant'/'runs'/rid for k,rid in RUN_IDS.items()}
    for k,r in roots.items():
        for f in ('bar_features.csv','trades.csv','manifest.txt'):
            if not (r/f).is_file(): raise RuntimeError(f'missing accepted {k} file: {r/f}')
    bars=[]
    bounds=[('chunk1','2025-02-01','2025-08-01'),('chunk2','2025-08-01','2026-02-01'),('chunk3','2026-02-01','2026-08-01')]
    for k,a,b in bounds:
        q=pd.read_csv(roots[k]/'bar_features.csv'); q['dt']=pt(q.time)
        bars.append(q[(q.dt>=pd.Timestamp(a))&(q.dt<pd.Timestamp(b))])
    b=pd.concat(bars,ignore_index=True).sort_values('dt').drop_duplicates('dt').reset_index(drop=True)
    if len(b)!=35344 or b.dt.duplicated().any(): raise RuntimeError(f'canonical bar mismatch rows={len(b)}')
    b['avail']=b.dt+pd.Timedelta(minutes=15)
    t=pd.concat([pd.read_csv(roots[k]/'trades.csv') for k in ('chunk1','chunk2','chunk3')],ignore_index=True)
    t=t[t.book=='usd40_r1p0_cent'].copy()
    if len(t)!=7262: raise RuntimeError(f'accepted USD40 trade count mismatch={len(t)}')
    t['entry_dt']=pt(t.entry_time); t['exit_dt']=pt(t.exit_time); t['month']=t.entry_dt.dt.strftime('%Y_%m')
    t['direction_num']=t.direction.map({'LONG':1,'SHORT':-1}).astype(int)
    t['adverse_r']=-pd.to_numeric(t.mae_r,errors='coerce')
    return b,t

def rank_corr(a,b):
    x=pd.Series(a); y=pd.Series(b)
    if x.nunique()<2 or y.nunique()<2: return float('nan')
    return float(x.rank().corr(y.rank()))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--common-files',required=True)
    ap.add_argument('--output',required=True)
    ap.add_argument('--summary',required=True)
    a=ap.parse_args()
    common=pathlib.Path(a.common_files); output=pathlib.Path(a.output); summary=pathlib.Path(a.summary)
    b,t=load(common); eng=engineer_bar(b); base=BAR_NUM+EXPERT+eng
    state=b[['avail']+base].sort_values('avail')
    j=pd.merge_asof(t.sort_values('entry_dt'),state,left_on='entry_dt',right_on='avail',direction='backward',allow_exact_matches=True)
    if j[base].isna().any().any(): raise RuntimeError('causal feature join contains NaN')
    X=j[base].replace([np.inf,-np.inf],np.nan).fillna(0).astype(float).reset_index(drop=True)
    X['direction_num']=j.direction_num.to_numpy()
    for c in CANDIDATES: X['cand_'+c]=(j.candidate.astype(str).to_numpy()==c).astype(float)
    y=j[TARGETS].astype(float).to_numpy()
    keys=j.entry_dt.astype(str)+'|'+j.direction_num.astype(str)
    mult=keys.map(keys.value_counts()).to_numpy(); w=1.0/mult
    months=sorted(j.month.unique()); tests=months[6:]; recs=[]; preds=[]
    for tm in tests:
        cal=months[months.index(tm)-1]; cstart=pd.Timestamp(cal.replace('_','-')+'-01')
        train=(j.exit_dt<cstart).to_numpy(); calmask=(j.month==cal).to_numpy(); test=(j.month==tm).to_numpy()
        if train.sum()<1000 or calmask.sum()<100 or test.sum()<100: raise RuntimeError(f'insufficient fold {tm}')
        ym=y[train].mean(axis=0); ys=y[train].std(axis=0); ys=np.where(ys>1e-8,ys,1.0)
        yz=(y-ym)/ys
        model=Pipeline([('sc',StandardScaler()),('m',MLPRegressor(hidden_layer_sizes=(64,32,16),alpha=.01,max_iter=100,early_stopping=True,n_iter_no_change=12,random_state=33))])
        try: model.fit(X.loc[train],yz[train],m__sample_weight=w[train])
        except TypeError: model.fit(X.loc[train],yz[train])
        pz=model.predict(X.loc[test]); p=pz*ys+ym
        idx=np.flatnonzero(test)
        for q,rowidx in enumerate(idx):
            preds.append({'test_month':tm,'calibration_month':cal,'entry_time':j.iloc[rowidx].entry_time,'candidate':j.iloc[rowidx].candidate,'direction':j.iloc[rowidx].direction,**{f'actual_{name}':float(y[rowidx,k]) for k,name in enumerate(TARGETS)},**{f'pred_{name}':float(p[q,k]) for k,name in enumerate(TARGETS)}})
        rec={'test_month':tm,'calibration_month':cal,'train_rows':int(train.sum()),'cal_rows':int(calmask.sum()),'test_rows':int(test.sum())}
        for k,name in enumerate(TARGETS):
            rec[f'{name}_spearman']=rank_corr(y[test,k],p[:,k]); rec[f'{name}_mae']=float(np.mean(np.abs(y[test,k]-p[:,k])))
        rec['pred_r_top40_actual_mean_r']=float(y[test,0][p[:,0]>=np.quantile(p[:,0],.60)].mean())
        rec['pred_r_bottom20_actual_mean_r']=float(y[test,0][p[:,0]<=np.quantile(p[:,0],.20)].mean())
        rec['pred_giveback_top20_actual_giveback']=float(y[test,3][p[:,3]>=np.quantile(p[:,3],.80)].mean())
        recs.append(rec)
        print(f'V33 multitask fold PASS test={tm} train={int(train.sum())} test_rows={int(test.sum())}',flush=True)
    rdf=pd.DataFrame(recs); pdf=pd.DataFrame(preds)
    output.parent.mkdir(parents=True,exist_ok=True); summary.parent.mkdir(parents=True,exist_ok=True)
    pdf.to_csv(output,index=False)
    agg={'protocol':'causal expanding monthly; labels only exits before calibration-month start; no reconstructed PnL','targets':TARGETS,'months':len(rdf),'rows':len(pdf),'mean_metrics':{c:float(rdf[c].mean()) for c in rdf.columns if c.endswith('_spearman') or c.endswith('_mae') or c.startswith('pred_')},'folds':rdf.to_dict('records')}
    summary.write_text(json.dumps(agg,indent=2),encoding='utf-8')
    print(json.dumps(agg['mean_metrics'],indent=2))

if __name__=='__main__': main()
