import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import v30_causal_research_v2 as c
import v30_trade_tournament_v2 as t
import v30_sequence_tournament_v2 as s


def synthetic_bars(n=40):
    tm=pd.date_range('2025-01-01 00:00',periods=n,freq='15min')
    d={col:np.zeros(n) for col in [
        'open','high','low','close','atr14','server_hour','day_of_week','rv8','rv32','m1_range_atr','m5_range_atr','h1_range_atr',
        'tick_mid_net_move_atr','tick_mid_abs_path_atr','bid_change_count','ask_change_count','tick_count','tick_spread_std_points','tick_spread_mean_points',
        'plus_di','minus_di','signal_count_long','signal_count_short','macd_hist'
    ]}
    d['time']=tm; d['close']=np.arange(n,dtype=float)+100; d['high']=d['close']+1; d['low']=d['close']-1; d['atr14']=np.ones(n)
    for e in c.EXPERTS:
        d[f'ewma_fast5_{e}']=np.zeros(n); d[f'ewma_slow20_{e}']=np.zeros(n); d[f'ewma_hl8_{e}']=np.zeros(n); d[f'ewma_hl12_{e}']=np.zeros(n); d[f'expert_obs_{e}']=np.zeros(n)
    return pd.DataFrame(d)


def test_bar_labels_keep_tail_nan():
    b=synthetic_bars(8)
    out=c.add_bar_labels(b,horizons=(2,))
    assert out['target_up_2'].iloc[-2:].isna().all()
    assert out['target_mfe_atr_2'].iloc[-2:].isna().all()
    assert out['target_mae_atr_2'].iloc[-2:].isna().all()


def test_causal_join_uses_closed_bar_not_current_bar():
    bars=pd.DataFrame({'time':pd.to_datetime(['2025-01-01 10:30','2025-01-01 10:45','2025-01-01 11:00'])})
    bars['feature_available_time']=bars['time']+pd.Timedelta(minutes=15)
    trades=pd.DataFrame({'entry_time':pd.to_datetime(['2025-01-01 10:45','2025-01-01 10:46','2025-01-01 11:00'])})
    out=c.join_trades_to_causal_bars(trades,bars,seq_len=1)
    assert out['feature_time'].tolist()==pd.to_datetime(['2025-01-01 10:30','2025-01-01 10:30','2025-01-01 10:45']).tolist()
    assert (out['feature_available_time']<=out['entry_time']).all()


def test_bar_labeler_does_not_add_future_to_model_features():
    b=synthetic_bars(40)
    lab=c.add_bar_labels(b,horizons=(1,))
    assert all(not x.startswith('target_') for x in c.bar_model_features(lab))


def test_fold_cutoff_is_previous_calibration_month():
    months=[f'2025_{m:02d}' for m in range(2,10)]
    rows=[]
    for m in months:
        start=t.month_start(m)
        for i in range(200):
            rows.append({'month':m,'entry_time':start+pd.Timedelta(hours=i),'exit_time':start+pd.Timedelta(hours=i+1)})
    df=pd.DataFrame(rows)
    cal,test=next(t.fold_months(df,warmup_months=6))
    assert cal=='2025_07' and test=='2025_08'
    train=df[df.exit_time<t.month_start(cal)]
    assert (train.exit_time<t.month_start('2025_07')).all()


def test_sequence_models_forward_shapes():
    b,tim,nf,ns=4,64,12,7
    x=torch.randn(b,tim,nf); st=torch.randn(b,ns)
    for name in ('gru','tcn','patch_transformer'):
        model=s.make_model(name,nf,ns)
        y=model(x,st)
        assert tuple(y.shape)==(b,)
