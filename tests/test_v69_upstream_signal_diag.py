#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ANALYZER = REPO / "scripts" / "analyze_v69_upstream_signal_funnel.py"
PRE_PENDING_ANALYZER = REPO / "scripts" / "analyze_v69_pre_pending_eval.py"
RUNNER = REPO / "runtime" / "v69_real_readiness_probe" / "RUN_V69_UPSTREAM_SIGNAL_DIAG.py"
LAUNCHER = REPO / "runtime" / "v69_real_readiness_probe" / "RUN_V69_UPSTREAM_SIGNAL_DIAG_GIT_BASH.sh"

EVAL_HEADER = [
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


def write_events(root: Path, events: list[tuple[str, str]], *, partial_tail: bool = False) -> None:
    root.mkdir(parents=True, exist_ok=True)
    events_path = root / "V64_EVENTS.csv"
    with events_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["time", "event", "detail"])
        for event, detail in events:
            w.writerow(["2026.09.02 12:00:00", event, detail])
    if partial_tail:
        with events_path.open("ab") as fh:
            fh.write(b"2026.09.02 12:00:01,POST_ZONE_REVERSAL_CONFIRM")
    with (root / "V64_DEALS.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["time", "entry", "price"])


def make_eval_row(
    *,
    time: str = "2026.09.02 12:00:00",
    reject_reason: str = "no_complete_archetype",
    decision_reason: str = "long_edge",
    selected_direction: int = 1,
    h4_trend: int = 0,
    h1_trend: int = 1,
    m15_trend: int = 1,
    bos_choch_dir: int = 1,
    long_score: int = 10,
    short_score: int = 2,
) -> dict[str, str]:
    row = {name: "0" for name in EVAL_HEADER}
    row.update({
        "time": time,
        "h4_trend": str(h4_trend),
        "h1_trend": str(h1_trend),
        "m15_trend": str(m15_trend),
        "bos_choch_dir": str(bos_choch_dir),
        "long_score": str(long_score),
        "short_score": str(short_score),
        "selected_direction": str(selected_direction),
        "decision_reason": decision_reason,
        "reject_reason": reject_reason,
        "stop_source": "none",
    })
    return row


def write_eval_rows(root: Path, rows: list[dict[str, str]]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    with (root / "V64_ENTRY_EVAL.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=EVAL_HEADER)
        w.writeheader()
        w.writerows(rows)


def write_eval(root: Path, reject_reason: str, *, decision_reason: str = "long_edge", selected_direction: int = 1) -> None:
    write_eval_rows(
        root,
        [make_eval_row(reject_reason=reject_reason, decision_reason=decision_reason, selected_direction=selected_direction)],
    )


def test_confirm_wait_reason_localizes_upstream_block() -> None:
    mod = load(ANALYZER, "v69_upstream_reason")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_events(
            root,
            [
                ("PENDING_ARM", "ok"),
                ("MICRO_ENTRY_ARM", "ok"),
                ("MICRO_ENTRY_ZONE_TOUCH", "ok"),
                ("MICRO_ENTRY_PENETRATION", "ok"),
                ("POST_ZONE_CONFIRM_WAIT", "reclaim_body_too_small"),
                ("POST_ZONE_CONFIRM_WAIT", "reason=reclaim_body_too_small body=0.2"),
                ("POST_ZONE_CONFIRM_WAIT", "reclaim_candle_wrong_direction"),
            ],
        )
        out = mod.analyze(root)
        assert out["classification"] == "RECLAIM_CONFIRM_QUALITY_BLOCK"
        assert out["dominant_blocker"] == "reclaim_body_too_small"
        assert out["confirm_wait_reason_counts"]["reclaim_body_too_small"] == 2
        assert out["stage_counts"]["POST_ZONE_REVERSAL_CONFIRM"] == 0


def test_funnel_classifies_each_pre_reclaim_transition() -> None:
    mod = load(ANALYZER, "v69_upstream_transitions")
    cases = [
        ([], "INITIAL_SETUP_OR_PENDING_ARM_BLOCK"),
        (["PENDING_ARM"], "PENDING_ARM_REACHED_MICRO_ENTRY_NOT_ARMED"),
        (["PENDING_ARM", "MICRO_ENTRY_ARM"], "MICRO_ENTRY_ARMED_ZONE_NOT_TOUCHED"),
        (["PENDING_ARM", "MICRO_ENTRY_ARM", "MICRO_ENTRY_ZONE_TOUCH"], "ZONE_TOUCH_REACHED_PENETRATION_NOT_REACHED"),
        (["PENDING_ARM", "MICRO_ENTRY_ARM", "MICRO_ENTRY_ZONE_TOUCH", "MICRO_ENTRY_PENETRATION"], "PENETRATION_REACHED_CONFIRM_EVALUATION_NOT_OBSERVED"),
    ]
    for idx, (events, expected) in enumerate(cases):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_events(root, [(event, "ok") for event in events])
            out = mod.analyze(root)
            assert out["classification"] == expected, (idx, out)


def test_partial_live_tail_is_ignored_not_invented() -> None:
    mod = load(ANALYZER, "v69_upstream_partial")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_events(root, [("PENDING_ARM", "ok")], partial_tail=True)
        out = mod.analyze(root)
        assert out["events_rows"] == 1
        assert out["stage_counts"]["PENDING_ARM"] == 1
        assert out["stage_counts"]["POST_ZONE_REVERSAL_CONFIRM"] == 0


def test_header_only_event_file_is_valid_upstream_evidence() -> None:
    mod = load(ANALYZER, "v69_upstream_header_only")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_events(root, [])
        out = mod.analyze(root)
        assert out["events_file_present"] is True
        assert out["events_rows"] == 0
        assert out["stage_counts"]["PENDING_ARM"] == 0
        assert out["classification"] == "INITIAL_SETUP_OR_PENDING_ARM_BLOCK"
        assert out["dominant_blocker"] == "PENDING_ARM"


def test_pre_pending_eval_localizes_no_complete_archetype() -> None:
    mod = load(PRE_PENDING_ANALYZER, "v69_pre_pending_arch")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_eval(root, "no_complete_archetype")
        out = mod.analyze(root)
        assert out["rows"] == 1
        assert out["classification"] == "ARCHETYPE_COMPLETION_BLOCK_BEFORE_PENDING_ARM"
        assert out["dominant_blocker"] == "no_complete_archetype"
        assert out["decision_reason_counts"]["long_edge"] == 1
        assert out["htf_regime_counts"]["LONG_HTF_REGIME"] == 1
        assert out["trigger_state_counts"]["LONG_TRIGGER_ONLY"] == 1
        assert out["score_relation_counts"]["LONG_SCORE_HIGHER"] == 1


def test_pre_pending_zero_eval_requires_evaluatebar_observability() -> None:
    mod = load(PRE_PENDING_ANALYZER, "v69_pre_pending_zero")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        root.mkdir(parents=True, exist_ok=True)
        with (root / "V64_ENTRY_EVAL.csv").open("w", encoding="utf-8", newline="") as fh:
            csv.writer(fh).writerow(EVAL_HEADER)
        out = mod.analyze(root)
        assert out["rows"] == 0
        assert out["classification"] == "NO_PRE_PENDING_DIRECTIONAL_EVAL_ROWS"
        assert out["dominant_blocker"] == "selector_or_feature_gate_unobserved"
        assert "EvaluateBar" in out["next_action"]


def test_pre_pending_aggregate_deduplicates_rotated_roots() -> None:
    mod = load(PRE_PENDING_ANALYZER, "v69_pre_pending_aggregate")
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        root_a = base / "a"
        root_b = base / "b"
        short_a = make_eval_row(
            time="2026.09.02 12:00:00",
            reject_reason="direction_isolated_out",
            decision_reason="short_edge",
            selected_direction=-1,
            h4_trend=0,
            h1_trend=-1,
            m15_trend=-1,
            bos_choch_dir=-1,
            long_score=2,
            short_score=10,
        )
        long_b = make_eval_row(
            time="2026.09.02 12:15:00",
            reject_reason="no_complete_archetype",
            decision_reason="long_edge",
            selected_direction=1,
            h4_trend=0,
            h1_trend=1,
            m15_trend=1,
            bos_choch_dir=1,
            long_score=11,
            short_score=3,
        )
        short_c = make_eval_row(
            time="2026.09.02 12:30:00",
            reject_reason="direction_isolated_out",
            decision_reason="short_edge",
            selected_direction=-1,
            h4_trend=-1,
            h1_trend=-1,
            m15_trend=-1,
            bos_choch_dir=-1,
            long_score=1,
            short_score=12,
        )
        write_eval_rows(root_a, [short_a, long_b])
        write_eval_rows(root_b, [short_a, short_c])

        out = mod.aggregate([root_a, root_b])
        unique = out["unique_summary"]
        assert out["raw_rows_across_sources"] == 4
        assert out["unique_rows_across_sources"] == 3
        assert out["duplicate_rows_removed"] == 1
        assert unique["selected_direction_counts"] == {"-1": 2, "1": 1}
        assert unique["htf_regime_counts"] == {"SHORT_HTF_REGIME": 2, "LONG_HTF_REGIME": 1}
        assert unique["trigger_state_counts"] == {"SHORT_TRIGGER_ONLY": 2, "LONG_TRIGGER_ONLY": 1}
        assert unique["direction_context_classification"] == "LONG_SELECTOR_CANDIDATES_EXIST_ACROSS_PRESERVED_EVALS"
        assert len(out["source_summaries"]) == 2


def test_all_unique_short_edges_are_classified_as_regime_abstention() -> None:
    mod = load(PRE_PENDING_ANALYZER, "v69_pre_pending_short_context")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        rows = [
            make_eval_row(
                time=f"2026.09.02 12:{minute}:00",
                reject_reason="direction_isolated_out",
                decision_reason="short_edge",
                selected_direction=-1,
                h4_trend=0 if minute == "00" else -1,
                h1_trend=-1,
                m15_trend=-1,
                bos_choch_dir=-1,
                long_score=2,
                short_score=10,
            )
            for minute in ("00", "15")
        ]
        write_eval_rows(root, rows)
        out = mod.aggregate([root])["unique_summary"]
        assert out["rows"] == 2
        assert out["decision_reason_counts"] == {"short_edge": 2}
        assert out["selected_direction_counts"] == {"-1": 2}
        assert out["htf_regime_counts"] == {"SHORT_HTF_REGIME": 2}
        assert out["score_relation_counts"] == {"SHORT_SCORE_HIGHER": 2}
        assert out["direction_context_classification"] == "ALL_UNIQUE_EVALS_SHORT_EDGE_IN_SHORT_HTF_REGIME"
        assert "do not enable SHORT" in out["direction_context_next_action"]


def test_runner_accepts_zero_event_rows_and_reads_pre_pending_eval() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    assert "V69_PRE_PROBE_SIGNAL_PATH.json" in runner
    assert "V69_UPSTREAM_ZERO_EVENT_ROWS_VALID=1" in runner
    assert "none contain readable V64_EVENTS.csv rows" not in runner
    assert "PRE_PROBE_SIGNAL_PATH_JSON" in runner
    assert "analyze_v69_pre_pending_eval.py" in runner
    assert "v69_upstream_signal_diagnostic_v4" in runner
    assert "V69_PRE_PENDING_EVAL_ROWS=" in runner
    assert "V69_PRE_PENDING_REJECT_REASONS=" in runner
    assert "V69_PRE_PENDING_ALL_UNIQUE_ROWS=" in runner
    assert "V69_PRE_PENDING_ALL_HTF_REGIMES" in runner
    assert "V69_PRE_PENDING_ALL_TRIGGER_STATES" in runner
    assert "V69_PRE_PENDING_ALL_SCORE_SUMMARY" in runner
    assert "V69_PRE_PENDING_ALL_SOURCE_SUMMARY" in runner
    assert "INITIAL_SETUP_OR_PENDING_ARM_BLOCK" in ANALYZER.read_text(encoding="utf-8")


def test_runner_and_launcher_are_strictly_read_only() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    launcher = LAUNCHER.read_text(encoding="utf-8")
    assert "V69_UPSTREAM_MT5_CAN_REMAIN_RUNNING=1" in runner
    assert "V69_UPSTREAM_ORDERS_SENT=0" in runner
    assert "_v69_forward_previous_*" in runner
    assert "v69_frozen_forward_demo" in runner
    assert "V69_UPSTREAM_DIAG_EXPECTED_HEAD is required" in runner
    assert "V69_UPSTREAM_DIAG_EXPECTED_HEAD is required" in launcher
    assert "PYTHON_REJECTED=" in launcher
    assert "DO NOT git clean" in launcher
    assert "DO NOT stash pop" in launcher
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
        assert forbidden not in runner, forbidden
        assert forbidden not in launcher, forbidden


def main() -> int:
    tests = [value for name, value in globals().items() if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"V69 upstream signal diagnostic tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
