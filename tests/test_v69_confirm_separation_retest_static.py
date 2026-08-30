#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_v69_confirm_separation_retest_source.py"
RUNNER = ROOT / "runtime" / "v69_confirm_separation_retest" / "RUN_V69_CONFIRM_SEPARATION_RETEST.py"
LAUNCHER = ROOT / "runtime" / "v69_confirm_separation_retest" / "START_V69_CONFIRM_SEPARATION_RETEST_GIT_BASH.sh"
ANALYZER = ROOT / "scripts" / "analyze_v69_confirm_separation_retest.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def generated(direction: int) -> str:
    return load(BUILDER, f"v69_builder_{direction}").transform(direction)


def test_v69_cash_contract_and_identity() -> None:
    for d in (-1, 1):
        s = generated(d)
        assert '#property version   "69.00"' in s
        assert "InpV64Magic = 690069" in s
        assert "InpV64FixedLot = 0.01" in s
        assert "InpV64MinStopRiskCash = 0.85" in s
        assert "InpV64MaxStopRiskCash = 1.10" in s
        assert "InpV64EmergencyLossCash = 1.20" in s
        assert "InpV64PrimaryTargetCash = 3.50" in s
        assert f"InpV64AllowedDirection = {d}" in s
        assert r"mt5_quant\v69_confirm_separation_retest" in s
        assert r"mt5_quant\v68_v67_holdout_stability" not in s
        assert "LongToString(" not in s


def test_v69_confirmation_cannot_order_without_separation_and_retest() -> None:
    for d in (-1, 1):
        s = generated(d)
        stage = s[s.index("void V66TryMicroEntry"):s.index("void V64ManagePendingEntry")]
        confirm = stage.index('V64PendingEvent("POST_ZONE_REVERSAL_CONFIRM"')
        first_return = stage.index("return;", confirm)
        separation = stage.index('V64PendingEvent("POST_CONFIRM_SEPARATION"')
        retest = stage.index('V64PendingEvent("POST_CONFIRM_RETEST_READY"')
        entry_ready = stage.index('V64PendingEvent("POST_CONFIRM_ENTRY_READY"')
        preflight = stage.index("V64OrderPreflight")
        assert confirm < first_return < separation < retest < entry_ready < preflight
        assert "g_trade.Buy" not in stage[confirm:first_return]
        assert "g_trade.Sell" not in stage[confirm:first_return]


def test_v69_requires_real_favorable_separation_then_later_retest() -> None:
    for d in (-1, 1):
        s = generated(d)
        assert "InpV69MinConfirmSeparationRiskCash = 1.30" in s
        assert "InpV69MinConfirmAgeSeconds = 30" in s
        assert "waiting_post_confirm_separation" in s
        assert "post_confirm_age_wait" in s
        assert "separated_waiting_cash_zone_retest" in s
        assert "// The separation tick itself is not a retest." in s
        assert "g_v69_max_post_confirm_risk<InpV69MinConfirmSeparationRiskCash" in s
        assert "risk_cash>InpV64MaxStopRiskCash" in s


def test_v69_preserves_structural_stop_and_does_not_clamp() -> None:
    for d in (-1, 1):
        s = generated(d)
        stage = s[s.index("void V66TryMicroEntry"):s.index("void V64ManagePendingEntry")]
        assert "V64BuildMicroStopTarget(d,entry,g_v66_micro_stop" in stage
        assert "MathMax(g_v66_micro_stop" not in stage
        assert "MathMin(g_v66_micro_stop" not in stage
        assert "g_v66_micro_stop=" not in stage[stage.index('POST_ZONE_REVERSAL_CONFIRM'):]


def test_v69_resets_separation_when_confirmation_is_invalidated() -> None:
    s = generated(1)
    assert s.count("g_v69_post_confirm_separated=false;") >= 4
    assert "new_adverse_extreme_requires_fresh_reclaim" in s
    assert "reclaim_confirmation_expired" in s


def test_v69_runner_is_18_pass_replay_not_fresh_holdout() -> None:
    t = RUNNER.read_text(encoding="utf-8")
    assert 'EXPECTED_BRANCH = "agent/v69-confirm-separation-retest-research"' in t
    assert 'V68_ACCEPTED_HEAD = "e1684df89078c9a8c0320df2370bbee19d00ff42"' in t
    assert 'V68_ACCEPTED_ZIP_SHA256 = "bb7b54f2ef0b30b83b2ee130c460ef2d0a50c9dfd9d78cdb89a88f084e35addb"' in t
    assert '"replay_is_independent_holdout": False' in t
    assert '"v68_is_development_evidence_for_v69": True' in t
    assert "len(REPLAY_MONTHS) * len(DIRECTIONS)" in t
    assert len(load(RUNNER, "v69_runner_static").REPLAY_MONTHS) == 9


def test_v69_analyzer_tracks_fast_losses_and_new_state() -> None:
    t = ANALYZER.read_text(encoding="utf-8")
    assert "POST_CONFIRM_SEPARATION" in t
    assert "POST_CONFIRM_RETEST_READY" in t
    assert "POST_CONFIRM_ENTRY_READY" in t
    assert "losses_le_60s" in t or "fmt_lane" in t
    assert "this_is_not_an_independent_holdout" in t


def test_v69_launcher_is_branch_pinned() -> None:
    t = LAUNCHER.read_text(encoding="utf-8")
    assert "agent/v69-confirm-separation-retest-research" in t
    assert "RUN_V69_CONFIRM_SEPARATION_RETEST.py" in t
    assert "git clean" not in t.lower()
    assert "stash pop" not in t.lower()


def main() -> int:
    tests = [
        obj for name, obj in sorted(globals().items())
        if name.startswith("test_v69_") and callable(obj)
    ]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V69 static tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
