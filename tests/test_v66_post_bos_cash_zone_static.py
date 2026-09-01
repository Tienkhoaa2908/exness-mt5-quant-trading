from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_v66_post_bos_cash_zone_source_fixed.py"
ANALYZER = ROOT / "scripts" / "analyze_v66_post_bos_cash_zone.py"
RUNNER = ROOT / "runtime" / "v66_post_bos_cash_zone" / "RUN_V66_POST_BOS_CASH_ZONE.py"
FIXED_RUNNER = ROOT / "runtime" / "v66_post_bos_cash_zone" / "RUN_V66_POST_BOS_CASH_ZONE_FIXED.py"
LAUNCHER = ROOT / "runtime" / "v66_post_bos_cash_zone" / "START_V66_POST_BOS_CASH_ZONE_GIT_BASH.sh"
ADR = ROOT / "docs" / "adr" / "ADR-068-v66-post-bos-cash-zone-research.md"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def source(direction: int) -> str:
    return load(BUILDER, f"v66_builder_{direction}").transform(direction)


def test_v66_contract_and_direction_isolation():
    for d in (-1, 1):
        s = source(d)
        assert '#property version   "66.00"' in s
        assert "InpV64Magic = 660066" in s
        assert "InpV64FixedLot = 0.01" in s
        assert "InpV64MinStopRiskCash = 0.85" in s
        assert "InpV64MaxStopRiskCash = 1.25" in s
        assert "InpV64EmergencyLossCash = 1.20" in s
        assert "InpV64PrimaryTargetCash = 3.50" in s
        assert "InpV64MinRiskSpreadRatio = 4.0" in s
        assert "InpV66MicroEntryTTLMinutes = 30" in s
        assert f"InpV64AllowedDirection = {d}" in s
        assert r"mt5_quant\\v66_post_bos_cash_zone" in s
        assert r"mt5_quant\\v65_micro_stop_calibration" not in s


def test_v66_bos_arms_stage_two_instead_of_forcing_market_entry():
    for d in (-1, 1):
        s = source(d)
        manage = s[s.index("void V64ManagePendingEntry"):s.index("void V64EvaluateBar")]
        assert manage.index("V64MicroTriggerConfirmed") < manage.index("V66ArmMicroPending")
        assert "V66TryMicroEntry();" in manage
        assert "V64BuildMicroStopTarget" in manage
        assert "MICRO_CANDIDATE" in manage
        assert "V66 CASHZONE" not in manage


def test_v66_real_tick_stage_waits_without_widening_structural_stop():
    s = source(1)
    stage = s[s.index("void V66TryMicroEntry"):s.index("void V64ManagePendingEntry")]
    assert "V64BuildMicroStopTarget(d,entry,g_v66_micro_stop" in stage
    assert 'reject=="micro_risk_cash_cap"' in stage
    assert '"above_cash_zone"' in stage
    assert '"near_stop_wait_rebound"' in stage
    assert '"spread_geometry_wait"' in stage
    assert "MICRO_ENTRY_ZONE_TOUCH" in stage
    assert "MICRO_ENTRY_INVALIDATE" in stage
    assert "MICRO_ENTRY_EXPIRE" in stage
    assert "expired_first_micro_arm_ttl" in stage
    assert "MathMax(g_v66_micro_stop" not in stage
    assert "MathMin(g_v66_micro_stop" not in stage
    assert "V64BuildStopTarget(d,cur,entry" not in stage


def test_v66_on_tick_checks_cash_zone_before_new_stage_one_work():
    s = source(1)
    tick = s[s.index("void OnTick"):s.index("void OnTradeTransaction")]
    assert tick.index("V66TryMicroEntry") < tick.index("V64ManagePendingEntry")
    assert "V64UpdateNoiseShadows" in tick


def test_v66_actual_entry_revalidates_context_and_uses_actual_fill_shadow():
    s = source(1)
    stage = s[s.index("void V66TryMicroEntry"):s.index("void V64ManagePendingEntry")]
    assert "cur.h4_trend!=d || cur.h1_trend!=d" in stage
    assert "V64EntryQualityPass" in stage
    assert "V64TrendQualityPass" in stage
    assert "V64M5RefinedStop" in stage
    assert '"m1_micro_zone"' in stage
    assert "g_trade.ResultPrice()" in stage
    assert "V64NoiseStart(d,shadow_entry)" in stage
    assert "LongToString(" not in s


def test_v66_runner_freezes_v65_samples_and_never_reselects_by_pnl():
    text = RUNNER.read_text(encoding="utf-8")
    assert 'EXPECTED_BRANCH = "agent/v66-post-bos-cash-zone-research"' in text
    assert '("week1", "2026.08.03", "2026.08.08")' in text
    assert '("week4", "2026.08.24", "2026.08.29")' in text
    assert '("bearish1", "2026.07.13", "2026.07.18")' in text
    assert '("bearish4", "2026.06.15", "2026.06.20")' in text
    assert '"real_tick_passes": 12' in text
    assert '"selection_uses_pnl": False' in text
    assert "screen" not in text.lower()


def test_v66_analyzer_repairs_v65_contract_labels_and_counts_stage_two():
    text = ANALYZER.read_text(encoding="utf-8")
    assert '"PLANNED_RISK_BAND_CASH=0.85,1.20"' in text
    assert '"PLANNED_RISK_BAND_CASH=0.85,1.25"' in text
    assert '"EMERGENCY_LOSS_CASH=1.15"' in text
    assert '"EMERGENCY_LOSS_CASH=1.20"' in text
    for token in ("MICRO_ENTRY_ARM", "MICRO_ENTRY_ZONE_TOUCH", "MICRO_ENTRY_INVALIDATE", "MICRO_ENTRY_EXPIRE"):
        assert token in text


def test_v66_launcher_uses_fixed_runtime_without_local_pytest_dependency():
    text = LAUNCHER.read_text(encoding="utf-8")
    assert "set -Eeuo pipefail" in text
    assert "agent/v66-post-bos-cash-zone-research" in text
    assert "RUN_V66_POST_BOS_CASH_ZONE_FIXED.py" in text
    assert "-m pytest" not in text
    fixed = FIXED_RUNNER.read_text(encoding="utf-8")
    assert "build_v66_post_bos_cash_zone_source_fixed.py" in fixed


def test_v66_adr_exists_and_preserves_tester_only_safety():
    assert ADR.is_file()
    text = ADR.read_text(encoding="utf-8")
    assert "V66" in text
    assert "0.01" in text
    assert "REAL" in text
    assert "cash-zone" in text.lower() or "cash zone" in text.lower()


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V66 static tests PASS count={len(tests)}")
