from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_v67_post_zone_reclaim_quality_source.py"
ANALYZER = ROOT / "scripts" / "analyze_v67_post_zone_reclaim_quality.py"
RUNNER = ROOT / "runtime" / "v67_post_zone_reclaim_quality" / "RUN_V67_POST_ZONE_RECLAIM_QUALITY.py"
LAUNCHER = ROOT / "runtime" / "v67_post_zone_reclaim_quality" / "START_V67_POST_ZONE_RECLAIM_QUALITY_GIT_BASH.sh"
ADR = ROOT / "docs" / "adr" / "ADR-069-v67-post-zone-reclaim-quality-research.md"
HANDOFF = ROOT / "docs" / "handoff" / "V67_RECOVERY_STATE.md"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def source(direction: int) -> str:
    return load(BUILDER, f"v67_builder_{direction}").transform(direction)


def test_v67_first_zone_touch_can_never_send_order():
    for d in (-1, 1):
        s = source(d)
        stage = s[s.index("void V66TryMicroEntry"):s.index("void V64ManagePendingEntry")]
        touch = stage.index('V64PendingEvent("MICRO_ENTRY_ZONE_TOUCH"')
        first_return = stage.index("return;", touch)
        confirm = stage.index("V67PostZoneReversalConfirmed")
        preflight = stage.index("V64OrderPreflight")
        assert touch < first_return < confirm < preflight
        between = stage[touch:first_return]
        assert "g_trade.Buy" not in between
        assert "g_trade.Sell" not in between


def test_v67_requires_penetration_then_closed_m1_reclaim():
    for d in (-1, 1):
        s = source(d)
        assert "InpV67PenetrationRiskCash = 0.92" in s
        assert "MICRO_ENTRY_PENETRATION" in s
        assert "POST_ZONE_CONFIRM_WAIT" in s
        assert "POST_ZONE_REVERSAL_CONFIRM" in s
        assert "POST_ZONE_CONFIRM_RESET" in s
        assert "POST_ZONE_ENTRY_READY" in s
        assert "CopyRates(_Symbol,PERIOD_M1,1,40,m1)" in s
        assert "m1[0].time<g_v67_zone_touch_bar" in s
        assert "post_zone_rejection_reclaim" in s
        assert "reclaim_body_too_small" in s
        assert "reclaim_distance_from_extreme_weak" in s


def test_v67_reclaim_confirmation_is_invalidated_by_new_adverse_extreme():
    s = source(1)
    stage = s[s.index("void V66TryMicroEntry"):s.index("void V64ManagePendingEntry")]
    assert "new_adverse_extreme_requires_fresh_reclaim" in stage
    assert "reclaim_confirmation_expired" in stage
    assert "InpV67ConfirmValidityMinutes = 5" in s
    assert "g_v67_reversal_confirmed=false" in stage


def test_v67_loss_headroom_and_structural_stop_contract():
    for d in (-1, 1):
        s = source(d)
        assert "InpV64FixedLot = 0.01" in s
        assert "InpV64MinStopRiskCash = 0.85" in s
        assert "InpV64MaxStopRiskCash = 1.10" in s
        assert "InpV64EmergencyLossCash = 1.20" in s
        assert "InpV64PrimaryTargetCash = 3.50" in s
        assert "InpV64MinRiskSpreadRatio = 4.0" in s
        assert 'V64BuildMicroStopTarget(d,entry,g_v66_micro_stop' in s
        stage = s[s.index("void V66TryMicroEntry"):s.index("void V64ManagePendingEntry")]
        assert "MathMax(g_v66_micro_stop" not in stage
        assert "MathMin(g_v66_micro_stop" not in stage
        assert '"m1_micro_reclaim"' in stage


def test_v67_long_short_execution_mechanics_are_symmetric():
    long = source(1)
    short = source(-1)
    for token in (
        "MICRO_ENTRY_PENETRATION",
        "POST_ZONE_REVERSAL_CONFIRM",
        "POST_ZONE_ENTRY_READY",
        "V64EntryQualityPass",
        "V64TrendQualityPass",
        "V64M5RefinedStop",
        "V64OrderPreflight",
        "V64NoiseStart(d,shadow_entry)",
    ):
        assert token in long
        assert token in short
    assert "InpV64AllowedDirection = 1" in long
    assert "InpV64AllowedDirection = -1" in short


def test_v67_runner_freezes_samples_and_removes_fixed_weekly_promotion_quota():
    text = RUNNER.read_text(encoding="utf-8")
    assert 'EXPECTED_BRANCH = "agent/v67-post-zone-reclaim-quality-research"' in text
    assert '("week1", "2026.08.03", "2026.08.08")' in text
    assert '("week4", "2026.08.24", "2026.08.29")' in text
    assert '("bearish1", "2026.07.13", "2026.07.18")' in text
    assert '("bearish4", "2026.06.15", "2026.06.20")' in text
    assert '"real_tick_passes": 12' in text
    assert '"selection_uses_pnl": False' in text
    assert '"fixed_trades_per_week_promotion_quota": False' in text
    assert '"fixed_weekly_profit_promotion_quota": False' in text
    assert '"long_short_lanes_evaluated_independently": True' in text


def test_v67_analyzer_measures_fast_losses_directly():
    mod = load(ANALYZER, "v67_analyzer_test")
    with tempfile.TemporaryDirectory() as td:
        rd = Path(td)
        (rd / "V64_DEALS.csv").write_text(
            "time,deal,entry,deal_type,reason,price,volume,profit,commission,swap,fee\n"
            "2026.08.05 07:05:06,2,0,0,3,4171.353,0.01,0,0,0,0\n"
            "2026.08.05 07:05:29,3,1,1,4,4170.044,0.01,-1.10,0,0,0\n"
            "2026.08.05 08:14:43,4,0,0,3,4166.066,0.01,0,0,0,0\n"
            "2026.08.05 08:19:43,5,1,1,3,4169.566,0.01,3.50,0,0,0\n",
            encoding="utf-8",
        )
        out = mod.duration_summary(rd)
        assert out["trades"] == 2
        assert out["losses"] == 1
        assert out["wins"] == 1
        assert out["losses_le_30s"] == 1
        assert out["losses_le_60s"] == 1
        assert out["loss_median_seconds"] == 23.0
        assert out["win_median_seconds"] == 300.0


def test_v67_paths_docs_and_launcher_are_safe():
    for path in (BUILDER, ANALYZER, RUNNER, LAUNCHER, ADR, HANDOFF):
        assert path.is_file(), path
    launcher = LAUNCHER.read_text(encoding="utf-8")
    assert "set -Eeuo pipefail" in launcher
    assert "agent/v67-post-zone-reclaim-quality-research" in launcher
    assert "RUN_V67_POST_ZONE_RECLAIM_QUALITY.py" in launcher
    docs = ADR.read_text(encoding="utf-8") + HANDOFF.read_text(encoding="utf-8")
    assert "REAL-money authorization is false" in docs
    assert "0.01" in docs
    assert "stable" in docs.lower()
    assert "3 trades" not in docs.lower()
    assert "$6" not in docs


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V67 static tests PASS count={len(tests)}")
