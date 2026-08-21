#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'scripts'/'build_v43_confidence_router_source.py'
AN=ROOT/'scripts'/'analyze_v43_confidence_router_mt5.py'
PACKAGER=ROOT/'scripts'/'package_research_bundle_portable.py'
RUN=ROOT/'runtime'/'v43_confidence_router_exact_mt5'/'RUN_V43_CONFIDENCE_ROUTER_EXACT_MT5_GIT_BASH.sh'
BOOT=ROOT/'runtime'/'v43_confidence_router_exact_mt5'/'BOOTSTRAP_V43_CONFIDENCE_ROUTER_ONE_SHOT_GIT_BASH.sh'
PACKAGE_ONLY=ROOT/'runtime'/'v43_confidence_router_exact_mt5'/'PACKAGE_V43_EXISTING_OUTPUT_GIT_BASH.sh'
CURRENT=ROOT/'docs'/'handover'/'CURRENT_STATE.md'
RECOVERY=ROOT/'docs'/'handover'/'RECOVERY_PROMPT.md'
PLAYBOOK=ROOT/'docs'/'handover'/'WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md'
EXPECTED_V43_SHA='487f2fffdfb7a348bd697fc0a8e6682d39a83f06b1a09453f7a194d5f5000c8a'
ACCEPTED_V38_ZIP='224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b'


def rt(path:Path)->str:
    return path.read_text(encoding='utf-8')


def load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def synthetic_parent()->str:
    setups='\n'.join([
        '   SetupAdaptiveRouter(7,"adaptive_ewma_hl8_thr0",0,0.00,0.00);',
        '   SetupAdaptiveRouter(8,"adaptive_ewma_hl8_thr0p05",1,0.05,0.00);',
        '   SetupAdaptiveRouter(9,"adaptive_ewma_hl10_thr0p05",2,0.05,0.00);',
        '   SetupAdaptiveRouter(10,"adaptive_ewma_hl12_thr0p05",3,0.05,0.00);',
        '   SetupAdaptiveRouter(11,"adaptive_cp_fast5_slow20_thr0p30",4,0.05,0.00);',
    ])
    return f'''#define MT5Q_RELEASE_ID "v38_fast_harvest_lab_v1"\n#define CANDIDATE_COUNT 23\ninput string InpOutputTag = "v38_fast_harvest_lab_v1";\ninput bool   InpV34WriteIntraTradeTelemetry = true;\ninput bool   InpV38WriteM1FastTelemetry = true;\n#define ADAPT_VARIANT_COUNT 5\n#define EXPERT_COUNT 5\n#define DBL_MAX 1.0e308\nstruct CandidateState{{double adaptive_switch_penalty; bool slow_mom_timebox; int adaptive_variant; double adaptive_min_score; string family;}};\nCandidateState C[CANDIDATE_COUNT];\nint g_last_selected_expert[ADAPT_VARIANT_COUNT];\nint g_v34_tape_handle=0;\nvoid ResetCandidate(int i){{C[i].adaptive_switch_penalty=0.0; C[i].slow_mom_timebox=false;}}\nvoid SetupAdaptiveRouter(int i,string n,int v,double m,double p){{}}\nvoid SetupV38FastClone(const int i,const string name,const int mode,const double targetR, const double armR,const double givebackR,const int timeboxSeconds){{}}\nvoid BuildCatalog(){{\n{setups}\n   SetupV38FastClone(22,"v38_adaptive_timebox30m",4,0.0,0.0,0.0,30*60);\n}}\nbool ExpertSignalInfo(int e,double a,int w,int ed,int td,int md,int bd,int sd,int &d,int &m){{return true;}}\ndouble AdaptiveExpertScore(int v,int e){{return 0;}}\nbool ResolveAdaptiveSignal(const CandidateState &st,const double atr,const datetime when, const int emaDir,const int trendDir,const int macdDir,const int bosDir,const int slowDir, int &direction,int &activeMask)\n{{\n   direction=0; activeMask=0;\n   double best=-DBL_MAX,second=-DBL_MAX; int bestExpert=-1,bestDir=0,bestMask=0;\n   return true;\n}}\nlong MQLInfoInteger(int x){{return 1;}}\n#define MQL_TESTER 1\nvoid manifest(){{string x=""; x+="v38_m1_fast_telemetry="+(InpV38WriteM1FastTelemetry?"1":"0")+"\\r\\n";}}\n// MQLInfoInteger(MQL_TESTER)\nV38_FAST_HARVEST_LAB START\nV38_FAST_HARVEST_LAB DONE\n'''


def test_builder_is_bounded_confidence_mechanism_not_time_hysteresis():
    b=load(BUILD,'v43b')
    assert len(b.NEW_SPECS)==4
    assert {x[4] for x in b.NEW_SPECS}=={0.05,0.10}
    assert {x[1] for x in b.NEW_SPECS}=={'adaptive_ewma_hl8_thr0p05','adaptive_ewma_hl10_thr0p05'}
    td=Path(tempfile.mkdtemp());src=td/'p.mq5';out=td/'o.mq5'
    src.write_text(synthetic_parent(),encoding='utf-8')
    b.build(src,out);text=rt(out)
    for token in ['#define CANDIDATE_COUNT 27','ResolveV43ConfidenceSignal','v43_hl8_thr0p05_conf0p05','v43_hl10_thr0p05_conf0p10','v43_global_time_hysteresis=0']:
        assert token in text
    assert 'g_v42_switch_delay_seconds' not in text
    assert '15*60' not in text and '30*60' not in text.split('SetupV38FastClone(22',1)[-1]


def test_analyzer_requires_both_control_and_parent_incremental_gates():
    a=load(AN,'v43a')
    assert a.EXPECTED_CONTROL_FINAL==107.432645
    assert a.EXPECTED_CONTROL_TRADES==563
    assert len(a.CHALLENGERS)==4
    assert set(a.PARENT.values())=={'adaptive_ewma_hl8_thr0p05','adaptive_ewma_hl10_thr0p05'}
    text=rt(AN)
    for token in ['ending_usd_at_least_5pct_above_control','ending_usd_above_frozen_parent','beats_parent_in_at_least_7_months','trade_breadth_at_least_90pct_parent']:
        assert token in text
    assert "cg['pass'] and pg['pass']" in text


def test_runner_anchors_immutable_v38_and_frozen_v43_source():
    text=rt(RUN)
    assert ACCEPTED_V38_ZIP in text
    assert EXPECTED_V43_SHA in text
    assert 'V38FastHarvestLab.base.a.mq5' in text
    assert 'build_v34_parallel_alpha_source.py' not in text
    assert 'build_v38_fast_harvest_source.py' not in text
    assert 'V43 source hash mismatch' in text


def test_runner_compile_and_mt5_are_artifact_gated():
    text=rt(RUN)
    for token in ['compile_checkpoint_valid','Result:[[:space:]]*0','METAEDITOR_LAUNCH_RC','LATEST did not refresh after MT5','collect_ready','monthly_summary.csv','trades.csv','manifest.txt']:
        assert token in text
    assert 'set +e' not in text
    assert 'if MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL=' in text


def test_runner_uses_portable_packaging_and_package_only_recovery():
    run=rt(RUN);boot=rt(BOOT);pkg=rt(PACKAGE_ONLY)
    assert 'package_research_bundle_portable.py' in run
    assert "line.split('  ',1)" not in run
    assert 'PACKAGE_V43_EXISTING_OUTPUT_GIT_BASH.sh' in boot
    assert 'MT5 WILL NOT RERUN' in boot
    assert 'PACKAGE-ONLY RECOVERY DONE' in pkg and 'MT5 WAS NOT RERUN' in pkg
    assert 'package_research_bundle_portable.py' in pkg


def test_portable_packager_never_parses_sha256sum_rendering():
    text=rt(PACKAGER)
    assert 'sha256_file' in text and 'write_manifest' in text and 'testzip' in text
    assert "split('  ',1)" not in text
    assert 'sha256sum' not in text


def test_windows_utf8_and_no_runtime_patcher_or_git_clean():
    texts='\n'.join(rt(p) for p in [RUN,BOOT,PACKAGE_ONLY,BUILD,AN])
    assert 'export PYTHONUTF8=1' in rt(RUN) and 'export PYTHONIOENCODING=utf-8' in rt(RUN)
    assert 'export PYTHONUTF8=1' in rt(BOOT) and 'export PYTHONIOENCODING=utf-8' in rt(BOOT)
    assert 'patch_v43' not in texts.lower() and '.generated.sh' not in texts
    assert 'git clean' not in texts


def test_safety_no_native_order_path_and_risk_unchanged():
    texts='\n'.join(rt(p) for p in [BUILD,RUN])
    assert 'AllowLiveTrading=0' in rt(RUN) and 'AllowDllImport=0' in rt(RUN)
    assert 'v43_risk_changed=0' in texts and 'risk_ceiling_per_trade=1.00%' in rt(RUN)
    for bad in ['OrderSend(', 'OrderSendAsync(', 'trade.Buy(', 'trade.Sell(']:
        assert bad not in rt(BUILD)


def test_shell_entrypoints_are_syntax_checked():
    for p in [RUN,BOOT,PACKAGE_ONLY]:
        cp=subprocess.run(['bash','-n',str(p)],capture_output=True,text=True)
        assert cp.returncode==0, f'{p}: {cp.stderr}'


def test_bootstrap_uses_explicit_refspec_and_no_whole_rerun_after_packaging_failure():
    text=rt(BOOT)
    assert '+refs/heads/$BRANCH:$REMOTE_REF' in text
    assert 'attempting package-only recovery' in text
    assert 'monthly_summary.csv' in text and 'v43_confidence_router_analysis.json' in text


def test_recovery_docs_capture_v42_failure_playbook_and_recovery_ladder():
    text='\n'.join(rt(p) for p in [CURRENT,RECOVERY,PLAYBOOK]).lower()
    for token in ['immutable v38','cp1252','err trap','runtime patcher','compile artifact','package-only','msys','do not rerun mt5','recovery ladder']:
        assert token in text, token


def test_recovery_docs_record_v42_hold_and_v43_contract():
    text='\n'.join(rt(p) for p in [CURRENT,RECOVERY]).lower()
    for token in ['v42 = hold','107.432645','8.58163','v43','confidence-aware','487f2fffdfb7a348bd697fc0a8e6682d39a83f06b1a09453f7a194d5f5000c8a']:
        assert token in text, token


def test_no_same_window_margin_rescue_sweep():
    b=load(BUILD,'v43m')
    assert len(b.NEW_SPECS)==4
    assert sorted({x[4] for x in b.NEW_SPECS})==[0.05,0.10]
    plan=rt(ROOT/'docs'/'research'/'v43_confidence_aware_router_exact_mt5_plan.md').lower()
    assert 'no same-window margin retuning' in plan


def _run_without_pytest():
    tests=[v for k,v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    for fn in tests:
        fn(); print('PASS',fn.__name__)
    print(f'V43 static tests PASS count={len(tests)}')


if __name__=='__main__':
    _run_without_pytest()
