from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_v64_microstructure_trigger_shadow_source_fixed.py"
SCREEN = ROOT / "scripts" / "build_v64_microstructure_trigger_shadow_screen_source.py"
ANALYZER = ROOT / "scripts" / "analyze_v64_microstructure_trigger_shadow.py"
RUNNER = ROOT / "runtime" / "v64_microstructure_trigger_shadow" / "RUN_V64_MICROSTRUCTURE_TRIGGER_SHADOW.py"
LAUNCHER = ROOT / "runtime" / "v64_microstructure_trigger_shadow" / "START_V64_MICROSTRUCTURE_TRIGGER_SHADOW_GIT_BASH.sh"
ADR = ROOT / "docs" / "adr" / "ADR-066-v64-microstructure-trigger-shadow-research.md"
HANDOFF = ROOT / "docs" / "handoff" / "V64_RECOVERY_STATE.md"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def source(direction: int) -> str:
    return load(BUILDER, f"v64_builder_{direction}").transform(direction)


def test_v64_cash_and_direction_contract():
    for d in (-1, 1):
        s = source(d)
        assert "InpV64FixedLot = 0.01" in s
        assert "InpV64PrimaryTargetCash = 3.50" in s
        assert "InpV64MinStopRiskCash = 0.85" in s
        assert "InpV64MaxStopRiskCash = 1.20" in s
        assert "InpV64EmergencyLossCash = 1.15" in s
        assert "InpV64MinRiskSpreadRatio = 4.0" in s
        assert f"InpV64AllowedDirection = {d}" in s
        assert 'g_trade.Buy(InpV64FixedLot' in s
        assert 'g_trade.Sell(InpV64FixedLot' in s


def test_v64_uses_two_nonfungible_archetypes():
    s = source(1)
    assert "PULLBACK_SWEEP_BOS" in s
    assert "BREAKOUT_RETEST_BOS" in s
    assert "V64ClassifyArchetype" in s
    assert "f.pullback_dir==d" in s
    assert "f.bos_choch_dir==d && f.structure_dir==d" in s
    assert 'detail="no_complete_archetype"' in s
    assert "V64MicroSweepBos" in s
    assert "V64MicroBreakRetestBos" in s


def test_v64_micro_trigger_is_closed_bar_sweep_reclaim_displacement_bos():
    s = source(1)
    assert "CopyRates(_Symbol,PERIOD_M1,1,80,m1)" in s
    assert "liquidity_sweep_reclaim_missing" in s
    assert "micro_bos_missing" in s
    assert "m1_displacement_too_weak" in s
    assert "InpV64MinM1BodyAtr = 0.25" in s
    assert "InpV64MinM1BodyFraction = 0.45" in s
    assert "InpV64MinSweepAtr = 0.05" in s
    assert "InpV64MicroBosBufferAtr = 0.02" in s
    # No future/current incomplete bar input for micro confirmation.
    micro = s[s.index("bool V64MicroSweepBos"):s.index("int V64NoiseSlot")]
    assert "CopyRates(_Symbol,PERIOD_M1,0," not in micro
    assert ".shift(-1)" not in micro


def test_v64_htf_trend_quality_is_normalized_and_causal():
    s = source(1)
    assert "CopyRates(_Symbol,PERIOD_H1,1,90,h1)" in s
    assert "CopyRates(_Symbol,PERIOD_H4,1,90,h4)" in s
    assert "InpV64MinH1EmaSepAtr = 0.12" in s
    assert "InpV64MinH4EmaSepAtr = 0.08" in s
    assert "InpV64MinH1SlopeAtr = 0.02" in s
    assert "InpV64MinH4SlopeAtr = 0.01" in s
    assert "InpV64MinPullbackEfficiency = 0.12" in s
    assert "InpV64MinBreakoutEfficiency = 0.18" in s
    assert 'detail="m15_efficiency_weak"' in s


def test_v64_spread_geometry_blocks_too_tight_stop():
    s = source(1)
    assert "risk_cash/spread_cash<InpV64MinRiskSpreadRatio" in s
    assert '"risk_spread_ratio_low"' in s
    assert "spread_cash<=0.0" in s


def test_v64_noise_shadow_survives_actual_stop_and_has_3x3_matrix():
    s = source(1)
    assert "V64_NOISE_SHADOW.csv" in s
    assert "const double stops[3]={1.10,1.35,1.60};" in s
    assert "const double targets[3]={3.00,3.50,4.00};" in s
    assert "state[9]" in s
    assert "first-hit matrix resolved; continue path telemetry" in s
    assert 'V64NoiseFinish(k,"all_resolved")' not in s
    assert 'V64NoiseFinish(k,"tester_end")' in s
    assert "InpV64NoiseShadowMaxMinutes = 480" in s
    assert "OrderCalcProfit" in s


def test_v64_actual_execution_no_longer_gated_by_legacy_single_shadow():
    s = source(1)
    tick_start = s.index("void OnTick()")
    tick_end = s.index("void OnTradeTransaction", tick_start)
    tick = s[tick_start:tick_end]
    assert "V64UpdateNoiseShadows();" in tick
    assert "V64UpdateShadow();" not in tick
    assert "if(g_shadow_open) return;" not in tick
    manage = s[s.index("void V64ManagePendingEntry"):s.index("void V64EvaluateBar")]
    assert "V64NoiseStart(d,entry);" in manage
    assert "V64StartShadow(" not in manage


def test_v64_screen_remains_dedicated_directional_nonexecution():
    mod = load(SCREEN, "v64_screen")
    s = mod.transform()
    assert "V64_DIRECTIONAL_SCREEN_ONLY" in s
    assert "InpV64ScreenOnly = true" in s
    ev = s[s.index("void V64EvaluateBar()"):s.index("int OnInit()")]
    for token in ("V64BuildStopTarget(", "V64OrderPreflight(", "g_trade.Buy(", "g_trade.Sell("):
        assert token not in ev


def test_v64_runner_protocol_is_fixed_and_pnl_independent():
    text = RUNNER.read_text(encoding="utf-8")
    assert 'EXPECTED_BRANCH = "agent/v64-microstructure-trigger-shadow-research"' in text
    assert 'REAL_MODEL = 4' in text
    assert '("week1", "2026.08.03", "2026.08.08")' in text
    assert '("week4", "2026.08.24", "2026.08.29")' in text
    assert 'MIN_BEARISH_SHORT_SIGNALS = 8' in text
    assert 'MIN_BEARISH_SHORT_SHARE = 0.60' in text
    assert 'BEARISH_WEEK_COUNT = 4' in text
    assert '"real_tick_passes": 12' in text
    assert '"selection_uses_pnl": False' in text
    assert 'build_v64_microstructure_trigger_shadow_source_fixed.py' in text
    assert 'V64_NOISE_SHADOW.csv' in text


def test_v64_launcher_is_safe_and_branch_pinned():
    text = LAUNCHER.read_text(encoding="utf-8")
    assert 'set -Eeuo pipefail' in text
    assert 'agent/v64-microstructure-trigger-shadow-research' in text
    assert 'RUN_V64_MICROSTRUCTURE_TRIGGER_SHADOW.py' in text
    assert "'fixed 0.01 | planned risk $0.85-$1.20 | TP $3.50'" in text
    assert "'risk/spread >= 4 | sweep/reclaim/BOS | two archetypes'" in text


def test_v64_noise_analyzer_detects_stop_then_later_target():
    mod = load(ANALYZER, "v64_analyzer")
    rows = [
        {
            "s110_t300": "-1", "s110_t350": "-1", "s110_t400": "-1",
            "s135_t300": "1", "s135_t350": "1", "s135_t400": "0",
            "s160_t300": "1", "s160_t350": "1", "s160_t400": "0",
            "max_pnl": "3.7", "min_pnl": "-1.2",
        },
        {
            "s110_t300": "1", "s110_t350": "0", "s110_t400": "0",
            "s135_t300": "1", "s135_t350": "0", "s135_t400": "0",
            "s160_t300": "1", "s160_t350": "0", "s160_t400": "0",
            "max_pnl": "3.1", "min_pnl": "-0.4",
        },
    ]
    out = mod.noise_summary(rows)
    assert out["s110_t300"]["trades"] == 2
    assert out["s110_t300"]["wins"] == 1
    assert out["s110_t300"]["losses"] == 1
    assert out["s110_t300"]["stop_then_later_target"] == 1
    assert out["s110_t350"]["stop_then_later_target"] == 1
    assert out["s110_t400"]["stop_then_later_target"] == 0


def test_v64_docs_record_external_research_as_patterns_not_evidence():
    adr = ADR.read_text(encoding="utf-8")
    handoff = HANDOFF.read_text(encoding="utf-8")
    for text in (adr, handoff):
        assert "MunchonGithub/thragg-ea" in text
        assert "smtlab/smartmoneyconcepts" in text
        assert "foeed/FvgGold-EA" in text
        assert "unverified" in text.lower()
        assert "REAL" in text
        assert "0.01" in text
    assert "stop-then-recovery" in adr
    assert "12 Model=4" in handoff


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V64 static tests PASS count={len(tests)}")
