#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ANALYZER = REPO / "scripts" / "analyze_v69_selector_coverage_recovery.py"
RUNNER = REPO / "runtime" / "v69_selector_coverage_recovery" / "RUN_V69_SELECTOR_COVERAGE_RECOVERY.py"
LAUNCHER = REPO / "runtime" / "v69_selector_coverage_recovery" / "RUN_V69_SELECTOR_COVERAGE_RECOVERY_GIT_BASH.sh"
V64_SCREEN_BUILDER = REPO / "scripts" / "build_v64_microstructure_trigger_shadow_screen_source.py"
V69_BUILDER = REPO / "scripts" / "build_v69_confirm_separation_retest_source.py"

HEADER = [
    "time","h4_trend","h1_trend","m15_trend","structure_dir","bos_choch_dir","fvg_dir",
    "liquidity_sweep_dir","order_block_retest_dir","pullback_dir","di_dir","macd_dir","location_dir",
    "atr15","rsi2","rsi14","adx","plus_di","minus_di","macd","macd_slope","distance_ema_atr",
    "range_location","long_score","short_score","selected_direction","decision_reason","entry","stop","tp",
    "risk_cash","risk_pct","margin_cash","spread_points","spread_cash","feasible","reject_reason","stop_source","screen_only",
]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def row(time: str, d: int, reason: str, h1: int, h4: int, long_score: int, short_score: int) -> dict[str, str]:
    out = {key: "0" for key in HEADER}
    out.update({
        "time": time,
        "selected_direction": str(d),
        "decision_reason": reason,
        "h1_trend": str(h1),
        "h4_trend": str(h4),
        "long_score": str(long_score),
        "short_score": str(short_score),
        "bos_choch_dir": str(d if d else 0),
        "m15_trend": str(d if d else 0),
    })
    return out


def test_coverage_counts_every_bar_including_neutral_and_feature_not_ready() -> None:
    mod = load(ANALYZER, "v69_cov_counts")
    rows = [
        row("2026.08.01 00:00:00", 1, "long_edge", 1, 1, 10, 1),
        row("2026.08.01 00:15:00", -1, "short_edge", -1, -1, 1, 11),
        row("2026.08.01 00:30:00", 0, "score_below_threshold", 1, 0, 6, 4),
        row("2026.08.01 00:45:00", 0, "feature_not_ready", 0, 0, 0, 0),
    ]
    out = mod.analyze_rows(rows)
    assert out["unique_m15_rows"] == 4
    assert out["feature_ready_rows"] == 3
    assert out["selected_direction_counts"] == {"-1": 1, "0": 2, "1": 1}
    assert out["long_selected_pct_all_bars"] == 25.0
    assert out["short_selected_pct_all_bars"] == 25.0
    assert out["neutral_selected_pct_all_bars"] == 50.0
    assert out["long_share_of_directional_pct"] == 50.0


def test_duplicate_bar_times_are_removed() -> None:
    mod = load(ANALYZER, "v69_cov_dedup")
    sample = row("2026.08.01 00:00:00", -1, "short_edge", -1, -1, 1, 10)
    out = mod.analyze_rows([sample, dict(sample)])
    assert out["raw_rows"] == 2
    assert out["unique_m15_rows"] == 1
    assert out["duplicate_times_removed"] == 1


def test_directional_core_comparison_catches_function_and_threshold_drift() -> None:
    mod = load(ANALYZER, "v69_cov_identity")
    template = """
input int InpV64MinDirectionalScore = 8;
input int InpV64MinScoreEdge = 2;
double V64EMA(){return 1;}
double V64ATR(){return 1;}
double V64RSI(){return 1;}
bool V64PivotHigh(){return true;}
bool V64PivotLow(){return true;}
void V64ConfirmedSwings(){}
int V64RecentFvgDir(){return 0;}
void V64DIADX(){}
int V64OrderBlockRetestDir(){return 0;}
int V64ScoreDirection(){return 0;}
bool V64BuildFeatures(){return true;}
int V64SelectDirection(){return 0;}
"""
    same = mod.compare_directional_core(template, template)
    assert same["exact_directional_core_match"] is True
    drift = template.replace("return 0;}", "return 1;}", 1)
    diff = mod.compare_directional_core(template, drift)
    assert diff["exact_directional_core_match"] is False
    threshold = template.replace("InpV64MinScoreEdge = 2", "InpV64MinScoreEdge = 3")
    diff2 = mod.compare_directional_core(template, threshold)
    assert diff2["exact_directional_core_match"] is False
    assert "InpV64MinScoreEdge" in diff2["threshold_mismatches"]


def test_repo_v64_all_bar_screen_matches_frozen_v69_directional_core() -> None:
    analyzer = load(ANALYZER, "v69_cov_repo_identity")
    v64_screen = load(V64_SCREEN_BUILDER, "v64_screen_for_v69_coverage_identity")
    v69 = load(V69_BUILDER, "v69_for_coverage_identity")
    identity = analyzer.compare_directional_core(v64_screen.transform(), v69.transform(1))
    assert identity["exact_directional_core_match"] is True, identity
    assert identity["function_mismatches"] == []
    assert identity["threshold_mismatches"] == []


def test_runtime_is_read_only_and_reuses_existing_screen_evidence() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    launcher = LAUNCHER.read_text(encoding="utf-8")
    assert "OUTPUT_V64" in runner
    assert "V64MicrostructureTriggerShadowScreen.mq5" in runner
    assert "V64_ENTRY_EVAL.csv" in runner
    assert "exact_directional_core_match" in runner
    assert "mt5_can_remain_running" in runner
    assert "orders_sent" in runner
    assert "real_money_authorized" in runner
    assert "V69_SELECTOR_COVERAGE_EXPECTED_HEAD is required" in runner
    assert "V69_SELECTOR_COVERAGE_EXPECTED_HEAD is required" in launcher
    for forbidden in (
        "terminal64.exe",
        "metaeditor64.exe",
        "OrderSend(",
        ".Buy(",
        ".Sell(",
        "taskkill",
        ".terminate(",
        ".kill(",
    ):
        assert forbidden not in runner
        assert forbidden not in launcher


def main() -> int:
    tests = [value for name, value in globals().items() if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"V69 selector coverage recovery tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
