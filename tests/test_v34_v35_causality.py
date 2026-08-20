import importlib.util
from pathlib import Path
import pandas as pd, numpy as np

ROOT=Path(__file__).resolve().parents[1]
def load(rel,name):
 p=ROOT/rel;spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_confirmed_swing_not_available_until_right_bars_close():
 m=load('scripts/v34_parallel_alpha_features.py','v34')
 x=pd.DataFrame({'high':[1,2,5,2,1,1,1],'low':[0,0,0,0,0,0,0]})
 last_hi,_,confirm_hi,_=m.confirmed_swings(x,left=2,right=2)
 assert np.isnan(confirm_hi[2])
 assert confirm_hi[4]==5
 assert np.isnan(last_hi[3])
 assert last_hi[4]==5

def test_asof_decision_tape_never_uses_future_availability():
 m=load('scripts/v34_parallel_alpha_features.py','v34')
 times=pd.to_datetime(['2026-01-01 00:00','2026-01-01 00:15','2026-01-01 03:00'])
 x=pd.DataFrame({'time':times})
 ft=pd.to_datetime(['2025-12-31 23:45','2026-01-01 00:00','2026-01-01 00:15','2026-01-01 03:00'])
 f=pd.DataFrame({'feature_time':ft,'feature_available_time':ft+pd.Timedelta(minutes=15)})
 for s in m.SPECIALISTS:
  f[s+'_dir']=[1,1,-1,1];f[s+'_score']=[5,10,20,30]
 t=m.asof_decision_tape(x,f,'2026-01-01','2026-01-02')
 r=t[t.time=='2026.01.01 03:00:00'].iloc[0]
 assert r.smc_ict_score==20

def test_v35_contains_existing_and_new_expert_sources():
 m=load('scripts/v35_train_specialist_router.py','v35')
 assert len(m.BASE_EXPERTS)==5
 assert len(m.NEW_SPECIALISTS)==5
 assert len(m.SPECIALISTS)==10
 assert set(m.BASE_EXPERTS).isdisjoint(m.NEW_SPECIALISTS)
