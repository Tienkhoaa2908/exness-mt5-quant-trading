#!/usr/bin/env python3
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
BUILDER=REPO/"scripts"/"build_v53_trend_bos_demo_confirmation_source.py"
RUNNER=REPO/"runtime"/"v53_trend_bos_demo"/"RUN_V53_TREND_BOS_DEMO.py"
SUP=REPO/"runtime"/"v53_trend_bos_demo"/"SUPERVISE_V53_TREND_BOS_DEMO.py"


def need(text:str,*tokens:str):
    for t in tokens:
        assert t in text, t


def main()->int:
    b=BUILDER.read_text(encoding="utf-8")
    r=RUNNER.read_text(encoding="utf-8")
    s=SUP.read_text(encoding="utf-8")

    need(b,
        'V48_SHA = "ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa"',
        'v52_b4_or_b3_trend_bos',
        'SIG_TREND_H1|SIG_BOS_FVG_H1',
        'v53_healthy==3',
        'const int ci=26,bi=3,ix=BI(ci,bi);',
        'InpV53Magic = 530053',
        'InpV53MinMarketDays = 2',
        'InpV53MinRoundTrips = 1',
        'InpV53HardCalendarDays = 7',
        'DEMO_CONFIRMATION_PASS',
        'ACCOUNT_TRADE_MODE_DEMO',
        'real_money_authorized=0',
        'SendNotification')
    assert 'LIVE_CANDIDATE_READY' in b  # builder explicitly replaces and then forbids residue
    need(r,
        'EXPECTED_BRANCH="agent/v53-trend-bos-demo-confirmation"',
        'v50_execution_probe_state.csv',
        'v53_demo_rehearsal_state.csv',
        'V53_DEMO_REHEARSAL_STATUS.txt',
        'account_mode")=="DEMO"',
        'real_money_authorized")=="0"',
        'TARGET=2_market_days_and_1_natural_round_trip')
    need(s,'V53_DEMO_REHEARSAL_FINAL.txt','bundle_manifest_sha256.txt','LATEST_V53_ZIP.txt')

    # No execution-probe logic: V53 broker orders must be driven only by natural selected virtual intent.
    for forbidden in ('PROBE_TARGET','probe_round_trips','V50 probe'):
        assert forbidden not in b
        assert forbidden not in r

    print("PASS selected_trend_bos_frozen")
    print("PASS demo_only_guard_contract")
    print("PASS one_natural_roundtrip_short_gate")
    print("PASS no_execution_probe_reuse")
    print("PASS detached_zip_supervisor")
    print("V53 trend+bos DEMO static tests PASS count=5")
    return 0

if __name__=="__main__":raise SystemExit(main())
