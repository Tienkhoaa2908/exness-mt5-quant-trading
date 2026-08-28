#!/usr/bin/env python3
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
V54_BUILDER = REPO / "scripts" / "build_v54_production_readiness_source.py"
BUILDER = REPO / "scripts" / "build_v55_account_agnostic_source.py"
RUNNER = REPO / "runtime" / "v55_account_agnostic" / "RUN_V55_ACCOUNT_AGNOSTIC.py"
WINDOWS_GATE = REPO / "runtime" / "v55_account_agnostic" / "RUN_V55_WINDOWS_GATE.py"
PACKAGER = REPO / "runtime" / "v55_account_agnostic" / "PACKAGE_V55_EVIDENCE.py"
START = REPO / "runtime" / "v55_account_agnostic" / "START_V55_ACCOUNT_AGNOSTIC_GIT_BASH.sh"


def rt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def need(text: str, *tokens: str) -> None:
    for token in tokens:
        assert token in text, token


def test_same_binary_demo_real_with_explicit_real_arm():
    b = rt(BUILDER)
    need(
        b,
        'V54_BUILDER = HERE / "build_v54_production_readiness_source.py"',
        'CANDIDATE = "v52_b4_or_b3_trend_bos"',
        'InpV55Magic = 550055',
        'InpV55AllowRealAccount = false',
        'InpV55RealArmCode = ""',
        'InpV55RealArmCode=="V55_REAL_ARMED"',
        'ACCOUNT_TRADE_MODE_DEMO',
        'ACCOUNT_TRADE_MODE_REAL',
        'DEMO_AND_REAL_SAME_BINARY',
        'REAL_OBSERVE_ONLY',
        'REAL_ARMED',
        'V55NewRiskAuthorized',
    )
    assert 'non_demo_account' in b
    need(b, 'forbidden = (', '"non_demo_account"')


def test_account_change_requires_restart_and_risk_state_is_account_scoped():
    v54 = rt(V54_BUILDER)
    b = rt(BUILDER)
    need(
        b,
        'g_v55_init_login',
        'g_v55_init_account_mode',
        'V55AccountIdentityStable',
        'account_identity_changed_restart_required',
        'AccountInfoInteger(ACCOUNT_LOGIN)',
        'V55RiskGlobal',
        'V55RiskGlobal("peak_equity",0)',
    )
    assert 'V54RiskGlobal("day_start_equity",key)' in v54


def test_first_real_entry_requires_post_start_flat_epoch():
    b = rt(BUILDER)
    need(
        b,
        'bool g_v55_real_entry_epoch_ready=false;',
        'g_v55_real_entry_epoch_ready=(g_v55_init_account_mode==ACCOUNT_TRADE_MODE_DEMO);',
        'g_v55_init_account_mode==ACCOUNT_TRADE_MODE_REAL && !g_v55_real_entry_epoch_ready',
        'if(owned==0 && !B[ix].open)',
        'else if(owned==0 && B[ix].open)',
        'real_activation_waiting_for_flat',
        'REAL_ENTRY_EPOCH_READY',
        'real_entry_epoch_ready=',
    )
    # Existing owned REAL positions are not rejected by the latch: only owned==0
    # legacy virtual-open state is blocked from becoming a new real broker entry.
    assert 'else if(owned==0 && B[ix].open)' in b


def test_broker_specific_constraints_are_runtime_derived():
    b = rt(BUILDER)
    need(
        b,
        'SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN)',
        'SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX)',
        'SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP)',
        'SYMBOL_TRADE_STOPS_LEVEL',
        'SYMBOL_TRADE_FREEZE_LEVEL',
        'V55StopsGeometryOk',
        'OrderCalcMargin',
        'ACCOUNT_MARGIN_FREE',
        'InpV55MaxMarginUsagePct = 80.0',
    )


def test_runner_defaults_demo_but_supports_explicit_real_mode_without_credentials():
    r = rt(RUNNER)
    need(
        r,
        'choices=("demo", "real")',
        'default="demo"',
        'REAL_ARM_CODE = "V55_REAL_ARMED"',
        'ExpertParameters={preset.name}',
        'expected_account = "REAL" if execution_mode == "real" else "DEMO"',
        'expected_activation = "REAL_ARMED" if execution_mode == "real" else "DEMO_ACTIVE"',
        'OWNED_MAGIC=550055',
        'MAX_OWNED_STRATEGY_POSITIONS=1',
    )
    low = r.lower()
    for forbidden in ('password=', 'login=', 'server='):
        assert forbidden not in low, forbidden


def test_runner_emits_native_mt5_set_format():
    r = rt(RUNNER)
    need(
        r,
        'def set_scalar(value: str, start: str, step: str, stop: str)',
        'return f"{value}||{start}||{step}||{stop}||N"',
        'def set_bool(value: bool)',
        'InpV55AllowRealAccount=true||',
        'InpV55AllowRealAccount=false||',
        'InpV55Magic=550055||',
        'InpV55MaxRiskPct=0.50||',
        'RealArmCode" not in line and "||" not in line',
    )


def test_windows_gate_is_fail_fast_and_prints_attach_diagnostics():
    g = rt(WINDOWS_GATE)
    need(
        g,
        'READY_TIMEOUT_SECONDS = 60',
        'DIAG_AFTER_SECONDS = 15',
        'V55 WINDOWS STARTUP DIAGNOSTICS',
        'terminal_trade_allowed',
        'mql_trade_allowed',
        'terminal_dlls_allowed',
        'latest_mt5_logs',
        'recent_common_diagnostics',
        'MetaTrader 5 is already open. Close the existing terminal first',
        'v55.wait_ready = fast_wait_ready',
    )


def test_runtime_preserves_inherited_v54_safety_and_v55_evidence_contracts():
    v54 = rt(V54_BUILDER)
    b = rt(BUILDER)
    p = rt(PACKAGER)

    need(b, 'v54.build(source, staged)', 'final = transform(text)')
    need(
        v54,
        'InpV54MaxRiskPct',
        'InpV54DailyLossPct',
        'InpV54MaxDrawdownPct',
        'InpV54MaxSpreadPoints',
        'stale_strategy_state',
        'stale_tick',
        'broker_reject_limit',
        'owned_position_missing_sltp',
        'duplicate_owned_positions',
        'OrderCalcProfit',
        'OnTradeTransaction',
        'SendNotification',
    )
    need(
        b,
        'OrderCalcMargin',
        'V55NewRiskAuthorized',
        'V55AccountIdentityStable',
        'V55StopsGeometryOk',
        'V55RiskGlobal("peak_equity",0)',
        'real_activation_waiting_for_flat',
    )
    need(
        p,
        '"schema": "v55_immutable_evidence_v1"',
        'ZIP CRC failure',
        'manifest mismatch',
        'V52R_ACCEPTED_ZIP_SHA256',
        'V53_ACCEPTED_ZIP_SHA256',
        'DEMO_AND_REAL_SAME_BINARY',
    )


def test_one_command_launcher_passes_mode_through_windows_gate():
    s = rt(START)
    need(s, 'set -euo pipefail', 'RUN_V55_WINDOWS_GATE.py "$@"')


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print(f"V55 account-agnostic static tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
