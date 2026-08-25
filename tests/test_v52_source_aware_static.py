#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
B=(ROOT/"scripts"/"build_v52_source_aware_source.py").read_text(encoding="utf-8")
A=(ROOT/"scripts"/"analyze_v52_source_aware.py").read_text(encoding="utf-8")
R=(ROOT/"runtime"/"v52_source_aware"/"RUN_V52_SOURCE_AWARE_ONE_SHOT.py").read_text(encoding="utf-8")
S=(ROOT/"runtime"/"v52_source_aware"/"START_V52_SOURCE_AWARE_GIT_BASH.sh").read_text(encoding="utf-8")


def test_parent_is_accepted_v51_source():
    assert '927611f7313793505d23c4c3d205a8ce0282869ad3ab8e4b49efe2ecc7ec79f6' in B
    assert 'V52 requires accepted V51 source' in B


def test_exact_source_aware_candidates_only():
    for name in ('v52_b4_or_b3_trend','v52_b4_or_b3_bos','v52_b4_or_b3_trend_bos'):
        assert name in B and name in A
    assert 'SIG_TREND_H1|SIG_BOS_FVG_H1' in B


def test_source_filter_applies_only_at_breadth3():
    assert 'v52_healthy==3' in B
    assert 'adaptive_b3_allowed_mask' in B
    assert '(bestMask & st.adaptive_b3_allowed_mask)==0' in B


def test_no_new_risk_or_execution_path():
    assert 'v52_risk_changed=0' in B
    assert 'SetupAdaptiveBreadthRouter(i,name,2,0.05,0.00,3,0.05)' in B
    assert 'FORBIDDEN' in B and 'OrderSend(' in B and 'CTrade' in B


def test_guardrails_are_small_gain_but_strict_quality():
    assert '"min_frequency_ratio":1.05' in A
    assert '"max_dd_absolute_pct":20.0' in A
    assert '"max_dd_increase_points":3.0' in A
    assert '"min_pf_absolute":1.20' in A
    assert '"min_pf_ratio_vs_baseline":0.95' in A
    assert '"min_avgr_absolute":0.10' in A
    assert '"min_avgr_ratio_vs_baseline":0.75' in A


def test_runner_rebuilds_accepted_v51_before_v52():
    assert 'V51_ACCEPTED_SHA="927611f7313793505d23c4c3d205a8ce0282869ad3ab8e4b49efe2ecc7ec79f6"' in R
    assert R.index('V51_BUILDER=') < R.index('V52_BUILDER=')
    assert 'if v51_sha!=V51_ACCEPTED_SHA' in R


def test_one_exact_mt5_run_one_zip():
    assert 'v52_source_aware_tournament.zip' in R
    assert 'v46.run_mt5_once' in R
    assert 'bundle_manifest_sha256.txt' in R
    assert 'One exact historical MT5 run; one final ZIP.' in S


def run_all():
    fs=[v for k,v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for f in fs:
        f(); print("PASS",f.__name__)
    print(f"V52 source-aware static tests PASS count={len(fs)}")


if __name__=="__main__": run_all()
