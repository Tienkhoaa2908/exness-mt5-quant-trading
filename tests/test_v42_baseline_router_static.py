#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'scripts'/'build_v42_baseline_router_source.py'
AN=ROOT/'scripts'/'analyze_v42_baseline_router_mt5.py'
RUN=ROOT/'runtime'/'v42_baseline_router_exact_mt5'/'RUN_V42_BASELINE_ROUTER_EXACT_MT5_GIT_BASH.sh'
BOOT=ROOT/'runtime'/'v42_baseline_router_exact_mt5'/'BOOTSTRAP_V42_BASELINE_ROUTER_ONE_SHOT_GIT_BASH.sh'
RESUME=ROOT/'runtime'/'v42_baseline_router_exact_mt5'/'RESUME_V42_FROM_COMPILED_EA_GIT_BASH.sh'
V32_RUN=ROOT/'runtime'/'v32_mlp_keep_sweep'/'RUN_V32_DEEP_MLP_KEEP_SWEEP_GIT_BASH.sh'
V34_RUN=ROOT/'runtime'/'v34_parallel_alpha'/'RUN_V34_V35_PARALLEL_ALPHA_GIT_BASH.sh'
V38_RUN=ROOT/'runtime'/'v38_fast_harvest'/'RUN_V38_FAST_HARVEST_EXACT_MT5_GIT_BASH.sh'
ACCEPTED_V38_ZIP='224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b'
FROZEN_V42_SOURCE='142bb4fdb066de712395f32942e8ff24cbc3af0a4c9d82c88f96317d8acc248e'


def rt(path:Path)->str:
    return path.read_text(encoding='utf-8')


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def synthetic_parent():
    setups='\n'.join([
      '   SetupAdaptiveRouter(7,"adaptive_ewma_hl8_thr0",0,0.00,0.00);',
      '   SetupAdaptiveRouter(8,"adaptive_ewma_hl8_thr0p05",0,0.05,0.00);',
      '   SetupAdaptiveRouter(9,"adaptive_ewma_hl10_thr0p05",1,0.05,0.00);',
      '   SetupAdaptiveRouter(10,"adaptive_ewma_hl12_thr0p05",2,0.05,0.00);',
      '   SetupAdaptiveRouter(11,"adaptive_cp_fast5_slow20_thr0p30",4,0.05,0.00);',
    ])
    return f'''#define MT5Q_RELEASE_ID "v38_fast_harvest_lab_v1"\n#define CANDIDATE_COUNT 23\ninput string InpOutputTag = "v38_fast_harvest_lab_v1";\ninput bool   InpV34WriteIntraTradeTelemetry = true;\ninput bool   InpV38WriteM1FastTelemetry = true;\nint MQLInfoInteger(int x){{return 1;}}\n#define MQL_TESTER 1\nvoid BuildCatalog()\n{{\n{setups}\n   SetupV38FastClone(22,"v38_adaptive_timebox30m",4,0.0,0.0,0.0,30*60);\n}}\nvoid x(){{\nif(InpUseTradeSessionPreflight && !TradeSessionOpenAt(tick.time)){{ C[ci].session_reject++; continue; }}\n\n      C[ci].selected_signals++;\n   x+="v34_specialists=smc_ict_causal,price_action_causal,wyckoff_proxy_causal,tick_microstructure_proxy,parallel_specialist_confluence\\r\\n";\n}}\n// MQLInfoInteger(MQL_TESTER)\nV38_FAST_HARVEST_LAB START\nV38_FAST_HARVEST_LAB DONE\n'''


def test_builder_clones_frozen_router_args_and_adds_only_switch_hysteresis(tmp_path=None):
    b=load(BUILD,'b42')
    td=Path(tempfile.mkdtemp()) if tmp_path is None else tmp_path
    src=td/'p.mq5'; out=td/'o.mq5'
    src.write_text(synthetic_parent(),encoding='utf-8')
    b.build(src,out)
    s=rt(out)
    assert '#define CANDIDATE_COUNT 29' in s
    assert 'SetupAdaptiveRouter(23,"v42_hl8_switch15m",0,0.00,0.00);' in s
    assert 'SetupAdaptiveRouter(26,"v42_hl10_thr0p05_switch15m",1,0.05,0.00);' in s
    assert 'V42DirectionSwitchAllows(r[0].time,ci,dir)' in s
    assert 'InpV34WriteIntraTradeTelemetry = false' in s
    assert 'InpV38WriteM1FastTelemetry = false' in s
    assert 'v42_risk_changed=0' in s
    assert 'v42_entry_exit_geometry_changed=0' in s


def test_v42_catalog_is_bounded_not_parameter_sweep():
    b=load(BUILD,'b42c')
    assert len(b.NEW_SPECS)==6
    assert sum(1 for x in b.NEW_SPECS if x[3]==30*60)==1
    assert sum(1 for x in b.NEW_SPECS if x[3]==15*60)==5
    assert {x[1] for x in b.NEW_SPECS}==set(b.OLD_ROUTERS)


def test_analyzer_hard_verifies_accepted_control_and_15pct_target():
    a=load(AN,'a42')
    assert a.EXPECTED_CONTROL_FINAL==107.432645
    assert a.EXPECTED_CONTROL_TRADES==563
    assert len(a.EXPECTED_MONTHLY_FINAL)==12
    assert a.TARGET_GEO_MONTH_PCT==15.0
    assert len(a.CHALLENGERS)==6


def test_promotion_gate_requires_material_return_and_risk_quality():
    text=rt(AN)
    for token in [
        'ending_usd_at_least_5pct_above_control',
        'geo_uplift_at_least_0p50pp',
        'return_to_dd_improved',
        'beats_control_in_at_least_7_months',
        'turnover_not_more_than_10pct_above_control',
        'trade_breadth_at_least_75pct_control',
    ]:
        assert token in text


def test_shell_scripts_parse_with_bash_n():
    for path in [BOOT,RUN,RESUME]:
        cp=subprocess.run(['bash','-n',str(path)],capture_output=True,text=True,encoding='utf-8')
        assert cp.returncode==0, f'{path}: {cp.stderr}'


def test_runner_is_exact_mt5_not_offline_shadow():
    text=rt(RUN)
    for token in ['terminal64.exe','metaeditor64.exe','Model=0','Deposit=40','2025.08.01','2026.08.01','RUN v42_baseline_router']:
        assert token in text
    assert 'AllowLiveTrading=0' in text
    assert 'AllowDllImport=0' in text
    assert 'git clean' not in text


def test_runner_anchors_to_accepted_v38_zip_not_rebuilt_v34_source():
    text=rt(RUN)
    assert ACCEPTED_V38_ZIP in text
    assert 'v38_fast_harvest_exact_mt5.zip' in text
    assert 'V38FastHarvestLab.base.a.mq5' in text
    assert 'accepted V38 ZIP CRC failure' in text
    assert 'scripts/build_v34_parallel_alpha_source.py' not in text
    assert 'scripts/build_v38_fast_harvest_source.py' not in text
    assert 'V34_ACCEPTED_SHA' not in text
    assert 'V38_PARENT_ZIP_SHA=' in text


def test_runner_matches_successful_v32_v34_v38_direct_compile_shape():
    current=rt(RUN)
    for old in [V32_RUN,V34_RUN,V38_RUN]:
        text=rt(old)
        assert 'compile_ea' in text
        assert 'METAEDITOR_EXE' in text
        assert '/compile:' in text
        assert 'TERMINAL_EXE' in text
    assert 'compile_ea' in current
    assert 'METAEDITOR_EXE' in current
    assert '/compile:' in current
    assert 'TERMINAL_EXE' in current
    assert 'patch_v42_metaeditor_runner.py' not in current


def test_runner_is_direct_not_runtime_patched():
    run=rt(RUN); boot=rt(BOOT)
    assert 'patch_v42_metaeditor_runner.py' not in run
    assert 'patch_v42_metaeditor_runner.py' not in boot
    assert '.RUN_V42_BASELINE_ROUTER_HARDENED.generated.sh' not in boot
    assert 'bash -n "$RUNNER"' in boot
    assert 'bash "$RUNNER"' in boot
    assert 'runner_architecture=direct_v32_v34_v38_style_with_compile_checkpoint_v1' in run


def test_compile_checkpoint_reuses_existing_valid_ex5_and_log():
    text=rt(RUN)
    for token in [
        'compile_checkpoint_valid',
        'REUSE COMPILE CHECKPOINT',
        'compile_source_sha256',
        'Result:[[:space:]]*0',
        'st_mtime_ns',
        'REUSE installed V42 source bytes',
    ]:
        assert token in text
    assert 'compile_ea "$EA42" "$SHA42A"' in text
    assert 'cp -f "$BASE42A" "$EA42"' in text


def test_compile_waits_for_log_result_and_ex5_as_one_postcondition():
    text=rt(RUN)
    assert 'for ((i=0;i<1200;i++))' in text
    assert 'if [[ -s "$log" ]]' in text
    assert 'if [[ -n "$sum" ]]' in text
    assert 'if [[ -s "$ex5" ]]' in text
    assert 'compile artifacts did not reach log+Result+EX5 postcondition' in text
    assert '[[ -s "$log" ]] || die "compile log missing' not in text


def test_windows_launchers_are_err_trap_safe_without_set_plus_e():
    text=rt(RUN)
    assert 'set +e' not in text
    assert "if MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' \"$METAEDITOR_EXE\"" in text
    assert "if MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' \"$TERMINAL_EXE\"" in text
    assert 'METAEDITOR_LAUNCH_RC=' in text
    assert 'MT5_LAUNCH_RC=' in text


def test_mt5_completion_is_artifact_driven_not_return_code_only():
    text=rt(RUN)
    assert 'after="$(read_kv run_id "$LATEST" || true)"' in text
    assert 'folder="$(read_kv run_folder "$LATEST" || true)"' in text
    assert 'LATEST did not refresh after MT5; launcher_rc=$rc' in text
    assert '[[ "$rc" -eq 0 ]] || die "MT5 failed' not in text


def test_bootstrap_forces_utf8_python_mode_on_windows():
    text=rt(BOOT)
    assert 'export PYTHONUTF8=1' in text
    assert 'export PYTHONIOENCODING=utf-8' in text


def test_resume_path_uses_existing_compiled_ea_and_never_launches_metaeditor():
    text=rt(RESUME)
    assert FROZEN_V42_SOURCE in text
    assert 'REUSE VERIFIED COMPILED V42 EA' in text
    assert 'V42BaselineRouterLab.log' in text
    assert 'V42BaselineRouterLab.ex5' in text
    assert 'Result:[[:space:]]*0' in text
    assert 'metaeditor64.exe' not in text
    assert 'METAEDITOR_EXE' not in text
    assert 'RUN v42_baseline_router — exact MT5 from verified compiled EA' in text


def test_resume_path_revalidates_v38_parent_tape_state_and_safety():
    text=rt(RESUME)
    assert ACCEPTED_V38_ZIP in text
    assert 'accepted V38 ZIP CRC failure' in text
    assert 'V34_TAPE_SHA=' in text
    assert 'STATE1_SHA=' in text
    assert 'AllowLiveTrading=0' in text
    assert 'AllowDllImport=0' in text
    assert 'native_broker_orders=0' in text
    assert 'external_broker_orders=0' in text


def test_resume_collection_waits_for_complete_manifested_outputs():
    text=rt(RESUME)
    assert 'collect_ready' in text
    assert 'for ((i=0;i<1200;i++))' in text
    assert 'monthly_summary.csv' in text
    assert 'trades.csv' in text
    assert 'manifest.txt' in text
    assert 'tester_only=1' in text
    assert 'MT5 run folder did not reach complete artifact/manifest postcondition' in text


def test_resume_mt5_completion_is_artifact_driven():
    text=rt(RESUME)
    assert 'for ((i=0;i<3600;i++))' in text
    assert 'MT5_LAUNCH_RC=' in text
    assert 'LATEST did not refresh after exact MT5; launcher_rc=$RC' in text
    assert '[[ "$RC" -eq 0 ]]' not in text
    assert 'set +e' not in text


def test_runner_reproduces_v38_control_before_acceptance():
    text=rt(RUN)
    assert 'EXPECTED_CONTROL_FINAL=107.432645' in text
    assert 'EXPECTED_CONTROL_TRADES=563' in text
    assert 'analyze_v42_baseline_router_mt5.py' in text


def test_one_run_one_zip_and_manifest():
    for text in [rt(RUN),rt(RESUME)]:
        assert 'bundle_manifest_sha256.txt' in text
        assert 'v42_baseline_router_exact_mt5.zip' in text
        assert 'testzip' in text


def test_bootstrap_explicit_refspec_and_no_clean():
    text=rt(BOOT)
    assert '+refs/heads/$BRANCH:$REMOTE_REF' in text
    assert 'git clean' not in text


def test_safety_no_native_order_path_in_v42_code():
    texts='\n'.join(rt(p) for p in [BUILD,AN,RUN,RESUME] if p.exists())
    assert 'AllowLiveTrading=1' not in texts
    assert 'risk_changed=0' in rt(BUILD)


def test_windows_text_io_is_explicit_utf8():
    text=rt(Path(__file__))
    bare='.'+'read_'+'text()'
    assert bare not in text
    assert "def rt(path:Path)->str:" in text
    assert "read_text(encoding='utf-8')" in text


def _run_without_pytest():
    tests=[v for k,v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    for fn in tests:
        fn()
        print('PASS',fn.__name__)
    print(f'V42 static tests PASS count={len(tests)}')


if __name__=='__main__':
    _run_without_pytest()
