#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'scripts'/'build_v45_multiyear_validation_source.py'
AN=ROOT/'scripts'/'analyze_v45_multiyear_validation.py'
BUNDLE_AN=ROOT/'scripts'/'analyze_mt5_research_bundle.py'
RUN=ROOT/'runtime'/'v45_multiyear_validation'/'RUN_V45_MULTIYEAR_ONE_SHOT.py'
BOOT=ROOT/'runtime'/'v45_multiyear_validation'/'BOOTSTRAP_V45_MULTIYEAR_ONE_SHOT_GIT_BASH.sh'
PKG=ROOT/'runtime'/'v45_multiyear_validation'/'PACKAGE_V45_EXISTING_OUTPUT_GIT_BASH.sh'
CURRENT=ROOT/'docs'/'handover'/'CURRENT_STATE.md'
RECOVERY=ROOT/'docs'/'handover'/'RECOVERY_PROMPT.md'
PLAYBOOK=ROOT/'docs'/'handover'/'WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md'

def rt(p:Path)->str:return p.read_text(encoding='utf-8')
def load(p:Path,n:str):
    spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);assert spec.loader;spec.loader.exec_module(m);return m

def synthetic_parent()->str:
    return '''#define MT5Q_RELEASE_ID "v38_fast_harvest_lab_v1"\n#define CANDIDATE_COUNT 23\ninput string InpOutputTag = "v38_fast_harvest_lab_v1";\ninput bool   InpV34WriteIntraTradeTelemetry = true;\ninput bool   InpV38WriteM1FastTelemetry = true;\n// adaptive_ewma_hl8_thr0\n// adaptive_ewma_hl8_thr0p05\n// adaptive_ewma_hl10_thr0p05\nlong MQLInfoInteger(int x){return 1;}\n#define MQL_TESTER 1\nvoid manifest(){string x="";\n   x+="v38_m1_fast_telemetry="+(InpV38WriteM1FastTelemetry?"1":"0")+"\\r\\n";\n}\n// MQLInfoInteger(MQL_TESTER)\nV38_FAST_HARVEST_LAB START\nV38_FAST_HARVEST_LAB DONE\n'''

def test_builder_changes_only_validation_markers_and_telemetry():
    b=load(BUILD,'v45b');td=Path(tempfile.mkdtemp());src=td/'p.mq5';out=td/'o.mq5';src.write_text(synthetic_parent(),encoding='utf-8');b.build(src,out);text=rt(out)
    for tok in ['#define CANDIDATE_COUNT 23','v45_multiyear_validation=1','v45_strategy_logic_changed=0','v45_risk_changed=0','v45_state_protocol=cold_start_no_2025_state','v45_single_tester_run=1','v45_live_authorized=0']:
        assert tok in text
    assert 'InpV34WriteIntraTradeTelemetry = false' in text and 'InpV38WriteM1FastTelemetry = false' in text

def test_protocol_is_one_long_run_with_monthly_logging():
    text=rt(RUN)
    assert 'FROM_DATE = "2022.01.01"' in text and 'TO_DATE = "2026.08.01"' in text and 'WARMUP_MONTHS = 6' in text
    assert '36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2' in text
    assert text.count('subprocess.run([str(TERMINAL_EXE)')==1
    assert 'monthly_summary.csv' in text and 'v45_monthly_analysis.csv' in text

def test_cold_start_has_no_2025_state_injection():
    text=rt(RUN)
    assert 'state.unlink()' in text and 'cold-start state removal failed' in text
    assert 'state_after_chunk1' not in text and 'STATE1_SHA' not in text

def test_mt5_resume_checkpoint_prevents_rerun():
    text=rt(RUN)
    assert 'REUSE V45 COMPLETE CHECKPOINT — MT5 NOT RERUN' in text
    assert 'RECOVER COLLECTION-ONLY — MT5 NOT RERUN' in text
    assert 'MT5_DONE.json' in text and 'DONE.txt' in text

def test_compile_reuse_requires_artifact_freshness_or_marker():
    text=rt(RUN)
    assert 'log.stat().st_mtime_ns < src_mtime' in text
    assert 'compile_source_sha256' in text
    assert 'MetaEditor log 0/0 + EX5' in text

def test_analyzer_has_multiyear_yearly_and_rolling_gates():
    text=rt(AN)
    for tok in ['MIN_TOTAL_MONTHS = 48','MIN_EVAL_MONTHS = 42','rolling_12m_positive_ratio_at_least_75pct','at_least_3_full_calendar_years','sum_r_after_extra_0p05r_per_trade_positive']:
        assert tok in text
    assert 'for window in (3, 6, 12)' in text and 'yearly-csv' in text and 'rolling-csv' in text

def test_primary_candidate_is_v44_robustness_choice():
    text=rt(AN)
    assert 'PRIMARY = "adaptive_ewma_hl10_thr0p05"' in text
    assert 'adaptive_ewma_hl8_thr0p05' in text and 'adaptive_ewma_hl8_thr0' in text

def test_live_trading_remains_forbidden():
    text=rt(RUN)+'\n'+rt(AN)
    assert 'AllowLiveTrading=0' in text and 'AllowDllImport=0' in text
    assert 'LIVE_AUTHORIZED=0' in text and 'live_authorized' in text.lower()

def test_portable_package_only_recovery_exists():
    text=rt(PKG)
    assert 'package_research_bundle_portable.py' in text and 'MT5 WAS NOT RERUN' in text
    assert 'v45_multiyear_single_run_validation.zip' in text

def test_bootstrap_explicit_refspec_and_no_git_clean():
    text=rt(BOOT)
    assert '+refs/heads/$BRANCH:$REMOTE_REF' in text and 'git clean' not in text
    assert 'package-only recovery' in text

def test_no_runtime_shell_patcher():
    texts='\n'.join(rt(p) for p in [RUN,BOOT,PKG])
    assert '.generated.sh' not in texts and 'patch_v45' not in texts.lower()

def test_shell_entrypoints_syntax():
    for p in [BOOT,PKG]:
        cp=subprocess.run(['bash','-n',str(p)],capture_output=True,text=True);assert cp.returncode==0,cp.stderr

def test_windows_utf8_contract():
    assert 'PYTHONUTF8=1' in rt(BOOT) and 'PYTHONIOENCODING=utf-8' in rt(BOOT)
    assert 'PYTHONUTF8=1' in rt(PKG) and 'PYTHONIOENCODING=utf-8' in rt(PKG)

def test_recovery_docs_lock_historical_state_and_no_rerun_contract():
    text='\n'.join(rt(p) for p in [CURRENT,RECOVERY,PLAYBOOK]).lower()
    for tok in ['cold-start','look-ahead','2025','2022','mt5_done.json','done.txt','mt5 must not rerun','package-only']:
        assert tok in text,tok

def test_generic_bundle_analyzer_recognizes_v45_first():
    text=rt(BUNDLE_AN)
    assert '("V45_EVIDENCE.txt","V44_EVIDENCE.txt"' in text
    assert '("v45","v45_multiyear_analysis.json")' in text

def _run_without_pytest():
    tests=[v for k,v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    for fn in tests:
        fn();print('PASS',fn.__name__)
    print(f'V45 static tests PASS count={len(tests)}')

if __name__=='__main__':_run_without_pytest()
