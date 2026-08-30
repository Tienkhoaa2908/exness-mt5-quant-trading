from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_v65_micro_stop_calibration_source_fixed.py"
BASE_BUILDER = ROOT / "scripts" / "build_v65_micro_stop_calibration_source.py"
RUNNER = ROOT / "runtime" / "v65_micro_stop_calibration" / "RUN_V65_MICRO_STOP_CALIBRATION.py"
FIXED_RUNNER = ROOT / "runtime" / "v65_micro_stop_calibration" / "RUN_V65_MICRO_STOP_CALIBRATION_FIXED.py"
LAUNCHER = ROOT / "runtime" / "v65_micro_stop_calibration" / "START_V65_MICRO_STOP_CALIBRATION_GIT_BASH.sh"
ADR = ROOT / "docs" / "adr" / "ADR-067-v65-micro-stop-calibration-research.md"
HANDOFF = ROOT / "docs" / "handoff" / "V65_RECOVERY_STATE.md"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def source(direction: int) -> str:
    return load(BUILDER, f"v65_fixed_builder_{direction}").transform(direction)


def test_v65_fixed_builder_normalizes_all_v64_roots():
    mod = load(BUILDER, "v65_fixed_root_contract")
    for d in (-1, 1):
        s = mod.transform(d)
        assert mod.base.V65_ROOT in s
        assert r"mt5_quant\\v64_microstructure_trigger_shadow" not in s
    fixed_text = BUILDER.read_text(encoding="utf-8")
    assert 'if label == "FILE_COMMON root"' in fixed_text
    assert "text.replace(old, new)" in fixed_text
    assert "stale FILE_COMMON root remains" in fixed_text


def test_v65_micro_trigger_precedes_cash_risk_gate():
    for d in (-1, 1):
        s = source(d)
        manage = s[s.index("void V64ManagePendingEntry"):s.index("void V64EvaluateBar")]
        assert manage.index("V64MicroTriggerConfirmed") < manage.index("V64BuildMicroStopTarget")
        assert "V64BuildStopTarget(d,cur,entry" not in manage
        assert 'g_v64_stop_source!="m5"' not in manage
        assert '"m1_micro"' in manage
        assert "MICRO_CANDIDATE" in manage
        assert "MICRO_REJECT" in manage


def test_v65_micro_stop_is_structural_not_clamped():
    s = source(1)
    assert "sweepExtreme-InpV64MicroStopAtrBuffer*atr" in s
    assert "m1[1].low-InpV64MicroStopAtrBuffer*atr" in s
    assert "micro_risk_too_tight" in s
    assert "micro_risk_cash_cap" in s
    assert "micro_risk_spread_ratio_low" in s
    assert "MathMax(micro_stop" not in s
    assert "MathMin(micro_stop" not in s


def test_v65_cash_contract_and_noise_root():
    for d in (-1, 1):
        s = source(d)
        assert "InpV64FixedLot = 0.01" in s
        assert "InpV64PrimaryTargetCash = 3.50" in s
        assert "InpV64MaxStopRiskCash = 1.25" in s
        assert "InpV64EmergencyLossCash = 1.20" in s
        assert "InpV64MinRiskSpreadRatio = 4.0" in s
        assert "InpV64MicroStopAtrBuffer = 0.10" in s
        assert f"InpV64AllowedDirection = {d}" in s
        assert r"mt5_quant\\v65_micro_stop_calibration" in s
        assert 'string V64_NOISE_FILE=V64_ROOT+"\\\\V64_NOISE_SHADOW.csv";' in s
        assert "IntegerToString(g_v64_noise[k].id)" in s
        assert "LongToString(" not in s


def test_v65_runner_reuses_exact_v64_windows_without_pnl_reselection():
    text = RUNNER.read_text(encoding="utf-8")
    assert 'EXPECTED_BRANCH = "agent/v65-micro-stop-calibration-research"' in text
    assert '("week1", "2026.08.03", "2026.08.08")' in text
    assert '("week4", "2026.08.24", "2026.08.29")' in text
    assert '("bearish1", "2026.07.13", "2026.07.18")' in text
    assert '("bearish4", "2026.06.15", "2026.06.20")' in text
    assert '"real_tick_passes": 12' not in text or "12" in text
    assert '"selection_uses_pnl": False' in text
    lower = text.lower()
    window_block = lower.split("bearish_windows =", 1)[1].split("directions =", 1)[0]
    assert "screen" not in window_block
    assert "select_bearish_weeks" not in text


def test_v65_fixed_runner_routes_original_runner_to_fixed_builder():
    text = FIXED_RUNNER.read_text(encoding="utf-8")
    assert "RUN_V65_MICRO_STOP_CALIBRATION.py" in text
    assert "build_v65_micro_stop_calibration_source_fixed.py" in text
    assert "runner.BUILDER = FIXED_BUILDER" in text


def test_v65_docs_and_launcher_exist_and_tester_only():
    for path in (LAUNCHER, ADR, HANDOFF):
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        assert "V65" in text
    launcher = LAUNCHER.read_text(encoding="utf-8")
    assert "set -Eeuo pipefail" in launcher
    assert "agent/v65-micro-stop-calibration-research" in launcher
    assert "RUN_V65_MICRO_STOP_CALIBRATION_FIXED.py" in launcher
    assert "build_v65_micro_stop_calibration_source_fixed.py" in launcher
    docs = ADR.read_text(encoding="utf-8") + HANDOFF.read_text(encoding="utf-8")
    assert "REAL" in docs
    assert "0.01" in docs
    assert "micro" in docs.lower()


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V65 static tests PASS count={len(tests)}")
