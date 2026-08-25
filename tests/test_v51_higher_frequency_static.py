#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
B=(ROOT/"scripts"/"build_v51_higher_frequency_source.py").read_text(encoding="utf-8")
A=(ROOT/"scripts"/"analyze_v51_higher_frequency.py").read_text(encoding="utf-8")
R=(ROOT/"runtime"/"v51_higher_frequency"/"RUN_V51_HIGHER_FREQUENCY_ONE_SHOT.py").read_text(encoding="utf-8")

def test_baseline_preserved():
    assert 'v46_hl10_thr0p05_breadth4' in B and 'healthy==3' in B

def test_three_fixed_challengers():
    for t in ('v51_b4_or_b3_avg0p075','v51_b4_or_b3_avg0p10','v51_b4_or_b3_avg0p15'):
        assert t in B and t in A

def test_no_native_execution_in_historical_source():
    assert 'FORBIDDEN' in B and 'CTrade' in B and 'OrderSend(' in B

def test_single_run_and_cold_start_reuse():
    assert 'v46.run_mt5_once(data,common,inputs)' in R and 'cold_start=1' in R

def test_frequency_guardrail():
    assert 'min_frequency_ratio":1.20' in A and 'frequency_gain_at_least_20pct' in A

def test_risk_guardrails():
    assert 'max_dd_absolute_pct":20.0' in A and 'max_dd_increase_points":3.0' in A
    assert 'min_pf_ratio_vs_baseline":0.90' in A and 'friction_cost_r_per_trade":0.05' in A

def test_fail_safe_keep_baseline():
    assert 'V51_KEEP_BREADTH4' in A and 'V51_CHALLENGER_SELECTED' in A

def test_one_zip_manifest():
    assert 'bundle_manifest_sha256.txt' in R and 'v51_higher_frequency_tournament.zip' in R

def run_all():
    fs=[v for k,v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    for f in fs:
        f(); print('PASS',f.__name__)
    print(f'V51 higher-frequency static tests PASS count={len(fs)}')

if __name__=='__main__':run_all()
