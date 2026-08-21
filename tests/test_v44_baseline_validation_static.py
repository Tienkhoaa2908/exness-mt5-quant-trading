#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'scripts'/'build_v44_baseline_validation_source.py'
AN=ROOT/'scripts'/'analyze_v44_baseline_validation.py'
RUN=ROOT/'runtime'/'v44_baseline_validation'/'RUN_V44_BASELINE_VALIDATION_EXACT_MT5_GIT_BASH.sh'
BOOT=ROOT/'runtime'/'v44_baseline_validation'/'BOOTSTRAP_V44_BASELINE_VALIDATION_ONE_SHOT_GIT_BASH.sh'
PKG=ROOT/'runtime'/'v44_baseline_validation'/'PACKAGE_V44_EXISTING_OUTPUT_GIT_BASH.sh'
PACKAGER=ROOT/'scripts'/'package_research_bundle_portable.py'
CURRENT=ROOT/'docs'/'handover'/'CURRENT_STATE.md'
RECOVERY=ROOT/'docs'/'handover'/'RECOVERY_PROMPT.md'
PLAYBOOK=ROOT/'docs'/'handover'/'WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md'
EXPECTED_V44_SHA='cfde6716916cd6adcf89cec2c7c2795ff762ea845795a9108e0247ee84e311d3'
V38_ZIP_SHA='224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b'

def rt(p:Path)->str: return p.read_text(encoding='utf-8')

def load(p:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(spec); assert spec.loader
    spec.loader.exec_module(m); return m

def synthetic_parent()->str:
    return '''#property strict
#define MT5Q_RELEASE_ID "v38_fast_harvest_lab_v1"
#define CANDIDATE_COUNT 23
input string InpOutputTag = "v38_fast_harvest_lab_v1";
input bool   InpV34WriteIntraTradeTelemetry = true;
input bool   InpV38WriteM1FastTelemetry = true;
// adaptive_ewma_hl8_thr0
// adaptive_ewma_hl8_thr0p05
// adaptive_ewma_hl10_thr0p05
// MQLInfoInteger(MQL_TESTER)
void Manifest(){
   string x="";
   x+="v38_m1_fast_telemetry="+(InpV38WriteM1FastTelemetry?"1":"0")+"\\r\\n";
}
V38_FAST_HARVEST_LAB START
V38_FAST_HARVEST_LAB DONE
'''

def test_builder_changes_only_validation_telemetry_and_markers():
    b=load(BUILD,'v44b')
    td=Path(tempfile.mkdtemp()); src=td/'p.mq5'; out=td/'o.mq5'
    src.write_text(synthetic_parent(),encoding='utf-8')
    b.build(src,out); text=rt(out)
    assert '#define CANDIDATE_COUNT 23' in text
    assert 'InpV34WriteIntraTradeTelemetry = false;' in text
    assert 'InpV38WriteM1FastTelemetry = false;' in text
    for tok in ['v44_baseline_validation=1','v44_strategy_logic_changed=0','v44_risk_changed=0','v44_live_authorized=0']:
        assert tok in text
    assert 'adaptive_ewma_hl8_thr0' in text
    assert 'adaptive_ewma_hl8_thr0p05' in text
    assert 'adaptive_ewma_hl10_thr0p05' in text

def test_analyzer_window_protocol_is_exactly_19():
    a=load(AN,'v44a')
    assert len(a.WINDOWS)==19
    assert sum(w[1]=='month' for w in a.WINDOWS)==12
    assert sum(w[1]=='quarter' for w in a.WINDOWS)==4
    assert sum(w[1]=='halfyear' for w in a.WINDOWS)==2
    assert sum(w[1]=='annual' for w in a.WINDOWS)==1
    assert a.CANDIDATES==['adaptive_ewma_hl8_thr0','adaptive_ewma_hl8_thr0p05','adaptive_ewma_hl10_thr0p05']

def test_analyzer_hard_reproduces_accepted_annual_control():
    text=rt(AN)
    for tok in ['EXPECTED_CONTROL_FINAL = 107.432645','EXPECTED_CONTROL_TRADES = 563','EXPECTED_MONTHLY_TRADES','EXPECTED_MONTHLY_FINAL','V44 annual control reproduction failed']:
        assert tok in text

def test_readiness_is_paper_demo_only_never_live():
    text=rt(AN)+'\n'+rt(RUN)+'\n'+rt(BOOT)
    assert '"live_authorized":False' in rt(AN)
    assert 'PAPER_DEMO_READY' in rt(AN)
    assert 'REAL-MONEY LIVE TRADING remains FORBIDDEN' in text
    assert 'LIVE_AUTHORIZED=0' in rt(RUN)
    assert 'AllowLiveTrading=0' in rt(RUN)
    assert 'AllowDllImport=0' in rt(RUN)

def test_annual_gate_runs_before_other_18_windows():
    text=rt(RUN)
    assert 'ANNUAL HARD REPRODUCTION GATE FIRST' in text
    assert '--verify-annual-only' in text
    assert 'Annual accepted-control reproduction PASS; running remaining 18 restart windows' in text
    assert 'for ((wi=1; wi<${#WINDOWS[@]}; wi++))' in text

def test_runner_uses_immutable_v38_and_frozen_v44_source():
    text=rt(RUN)
    assert V38_ZIP_SHA in text
    assert EXPECTED_V44_SHA in text
    assert 'V38FastHarvestLab.base.a.mq5' in text
    assert 'build_v34_parallel_alpha_source.py' not in text
    assert 'build_v38_fast_harvest_source.py' not in text
    assert 'V44 frozen source hash mismatch' in text

def test_runner_has_compile_and_mt5_artifact_checkpoints():
    text=rt(RUN)
    for tok in ['compile_checkpoint_valid','Result:[[:space:]]*0','REUSE COMPLETE','RECOVER COLLECTION-ONLY','LATEST did not refresh after MT5','collect_ready','MT5_DONE.txt','SOURCE_RUN_FOLDER.txt']:
        assert tok in text
    assert 'set +e' not in text
    assert "if MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'" in text

def test_each_window_restarts_from_frozen_state():
    text=rt(RUN)
    assert 'cp -f "$STATE1" "$state_target"' in text
    assert 'window_state_semantics=accepted_2025_08_state_restart_each_window' in text
    assert 'restart_state_sha=%s' in text

def test_portable_packaging_and_package_only_recovery():
    run=rt(RUN); boot=rt(BOOT); pkg=rt(PKG)
    assert 'package_research_bundle_portable.py' in run
    assert 'package_research_bundle_portable.py' in pkg
    assert "line.split('  ',1)" not in run
    assert 'MT5 WILL NOT RERUN' in boot
    assert 'MT5 WAS NOT RERUN' in pkg
    assert 'PACKAGE-ONLY RECOVERY DONE' in pkg

def test_windows_utf8_no_runtime_patcher_no_git_clean():
    text='\n'.join(rt(p) for p in [RUN,BOOT,PKG,BUILD,AN])
    assert 'export PYTHONUTF8=1' in rt(RUN)
    assert 'export PYTHONIOENCODING=utf-8' in rt(RUN)
    assert 'export PYTHONUTF8=1' in rt(BOOT)
    assert '.generated.sh' not in text
    assert 'patch_v44' not in text.lower()
    assert 'git clean' not in text

def test_shell_entrypoints_bash_n():
    for p in [RUN,BOOT,PKG]:
        cp=subprocess.run(['bash','-n',str(p)],capture_output=True,text=True)
        assert cp.returncode==0, f'{p}: {cp.stderr}'

def test_package_recovery_requires_all_19_completed_checkpoints():
    text=rt(BOOT)
    for tag in [
        'y01_2025_08_2026_08','h01_2025_08_2026_02','h02_2026_02_2026_08',
        'q01_2025_08_11','q04_2026_05_08','m01_2025_08','m12_2026_07'
    ]:
        assert tag in text
    assert 'after completed exact evidence; attempting package-only recovery' in text

def test_recovery_docs_preserve_v42_incidents_and_v44_ladder():
    text='\n'.join(rt(p) for p in [CURRENT,RECOVERY,PLAYBOOK]).lower()
    for tok in ['immutable v38','cp1252','err trap','runtime shell patcher','compile artifact','msys','package-only','do not rerun mt5','recovery ladder','v44']:
        assert tok in text, tok

def test_no_validation_window_retuning():
    text=rt(AN)+'\n'+rt(RUN)
    assert 'does not retune the three frozen routers' in text
    assert 'same_window_retuning=FORBIDDEN' in rt(RUN)

def _run_without_pytest():
    funcs=[v for k,v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    for fn in funcs:
        fn(); print('PASS',fn.__name__)
    print(f'V44 static tests PASS count={len(funcs)}')

if __name__=='__main__':
    _run_without_pytest()
