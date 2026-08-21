from pathlib import Path
import importlib.util,sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];S=ROOT/'scripts';sys.path.insert(0,str(S))
def read(rel):return (ROOT/rel).read_text(encoding='utf-8')
def mod():
 p=S/'v41_baseline_stack_action_value_stage_a.py';sp=importlib.util.spec_from_file_location('v41',p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m

def test_fixed_action_value_contract():
 c=read('scripts/v41_baseline_stack_common.py');a=read('scripts/v41_baseline_action_value.py')
 assert 'ENTRY_KEEP_TARGET=0.60' in c and 'ACTION_COVERAGE_TARGET=0.20' in c
 assert 'HistGradientBoostingRegressor' in c and 'HistGradientBoostingClassifier' in c
 assert 'pred_delta_r' in a and 'p_positive' in a and 'delta_r' in a.lower()

def test_baseline_is_causal_router_not_neural_net():
 s=read('scripts/v41_baseline_stack_action_value_stage_a.py')
 assert 'causal_performance_weighted_mixture_of_rule_based_experts' in s
 for x in ['EMA_skip20','MACD_gap10','BOS_FVG_gap8','Trend20_gap5','SlowMomentum_16h24h']:assert x in s
 assert "'ewma_half_life':8" in s and "'router_threshold':0.0" in s

def test_sequence_is_completed_trade_causal():
 m=mod();t=pd.DataFrame({'trade_key':['a','b','c'],'entry_time':pd.to_datetime(['2026-01-01 00:00','2026-01-01 01:00','2026-01-01 05:00']),'exit_time':pd.to_datetime(['2026-01-01 02:00','2026-01-01 03:00','2026-01-01 06:00']),'direction':['SHORT']*3,'source_family':['EMA']*3,'r_multiple':[1.,1.,-1.]});x=m.add_trade_sequence_features(t);assert x.loc[x.trade_key=='b','prev_win'].iloc[0]==0;assert x.loc[x.trade_key=='c','third_same_dir_after_2wins'].iloc[0]==1

def test_action_target_is_delta_vs_baseline():
 m=mod();g=pd.DataFrame({'trade_key':['x']*4,'time':pd.date_range('2026-01-01',periods=4,freq='min'),'unrealized_r':[1.,.7,1.2,1.1],'final_r':[1.1]*4});r=m.build_action_targets(g).iloc[0];assert r['STATIC_PROTECT_0.25R_delta_r']<0 and r['STATIC_PROTECT_0.25R_positive']==0

def test_v36_cutoff_blocks_future_rows():
 m=mod();v=pd.DataFrame({'exit_time':pd.to_datetime(['2026-01-01','2026-03-01','2026-01-02','2026-03-02']),'p_hold':[.1,.9,.2,.8],'actual_hold':[0,1,0,1],'p_protect':[.9,.1,.8,.2],'actual_protect':[1,0,1,0]});c=m.fit_v36_calibrators(v,pd.Timestamp('2026-02-01'));assert c['p_hold'] is None and c['p_protect'] is None

def test_frozen_positive_and_rejected_layers_are_explicit():
 s=read('scripts/v41_baseline_stack_action_value_stage_a.py');e=read('scripts/v41_baseline_stack_economics.py')
 assert 'V32_DeepMLP_keep60' in s and 'FROZEN_REFERENCE_NOT_RETUNED' in s and 'V36_Transformer' in s and 'V30_expected_R' in s
 for x in ['generic cooldown','hard conjunctive quality gate','broad signal fusion','fixed range-to-family router','universal fast exit']:assert x in s
 assert 'DIAGNOSTIC_ONLY_NOT_AUTO_INTEGRATED' in e

def test_profit_contract_shadow_not_exact():
 s=read('scripts/v41_baseline_stack_action_value_stage_a.py');c=read('scripts/v41_baseline_stack_common.py')
 assert 'NOT exact-MT5 PnL' in s and 'BASELINE_END_USD=107.43' in c and 'BASELINE_GEO_MONTH=0.0858' in c and 'TARGET_GEO_MONTH=0.15' in c
 assert "'risk_changed':False" in s and "'extra_entries':0" in s

def test_runner_offline_one_zip_and_packages_all_modules():
 r=read('runtime/v41_baseline_stack/RUN_V41_BASELINE_STACK_STAGE_A_GIT_BASH.sh');clean='\n'.join(x for x in r.splitlines() if 'grep -Eiq' not in x)
 for tok in ['terminal64.exe','metaeditor64.exe','OrderSend(','OrderSendAsync(','CTrade','trade.Buy(','trade.Sell(']:assert tok.lower() not in clean.lower()
 for f in ['v41_baseline_stack_common.py','v41_baseline_entry_value.py','v41_baseline_action_value.py','v41_baseline_stack_economics.py','v40_upgrade_campaign_stage_a.py','v40_upgrade_campaign_stage_a_core.py']:assert f in r
 assert 'v41_baseline_stack_action_value_stage_a.zip' in r and 'bundle_manifest_sha256.txt' in r and 'ZIP integrity PASS' in r and 'live_trading=FORBIDDEN' in r and 'risk_changed=0' in r

def test_bootstrap_explicit_refspec_no_clean():
 b=read('runtime/v41_baseline_stack/BOOTSTRAP_V41_BASELINE_STACK_ONE_SHOT_GIT_BASH.sh');assert 'agent/v41-baseline-stack-action-value' in b and '+refs/heads/$BRANCH:$REMOTE_REF' in b and 'checkout -B "$BRANCH" "$REMOTE_REF"' in b and 'reset --hard "$REMOTE_REF"' in b and 'no git clean' in b

def _run_without_pytest():
 tests=[v for k,v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
 for f in tests:f();print('PASS',f.__name__)
 print(f'V41 static tests PASS count={len(tests)}')
if __name__=='__main__':_run_without_pytest()
