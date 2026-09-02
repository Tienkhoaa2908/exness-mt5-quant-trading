#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ANALYZER = REPO / "scripts" / "analyze_v69_upstream_signal_funnel.py"
PRE_PENDING_ANALYZER = REPO / "scripts" / "analyze_v69_pre_pending_eval.py"
OUT = HERE / "OUTPUT_V69_REAL_READINESS_PROBE"
PRE_PROBE_SIGNAL_PATH = OUT / "V69_PRE_PROBE_SIGNAL_PATH.json"
EXPECTED_BRANCH = "agent/v69-one-shot-prospective-demo"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def capture(cmd) -> str:
    return subprocess.check_output(
        [str(x) for x in cmd], cwd=REPO, text=True, encoding="utf-8", errors="replace"
    ).strip()


def ensure_repo() -> tuple[str, str]:
    expected = os.environ.get("V69_UPSTREAM_DIAG_EXPECTED_HEAD", "").strip()
    if not expected:
        raise RuntimeError("V69_UPSTREAM_DIAG_EXPECTED_HEAD is required")
    branch = capture(["git", "branch", "--show-current"])
    head = capture(["git", "rev-parse", "HEAD"])
    dirty = capture(["git", "status", "--porcelain"])
    origin = capture(["git", "remote", "get-url", "origin"])
    print(f"ORIGIN={origin}")
    print(f"BRANCH={branch}")
    print(f"HEAD={head}")
    print(f"EXPECTED_HEAD={expected}")
    if "Tienkhoaa2908/exness-mt5-quant-trading" not in origin:
        raise RuntimeError("wrong repository")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")
    if head != expected:
        raise RuntimeError(f"wrong HEAD expected={expected} actual={head}")
    if dirty:
        raise RuntimeError("working tree must be clean; do not git clean or stash pop")
    return branch, head


def common_mt5_quant_root() -> Path:
    appdata = os.environ.get("APPDATA", "").strip()
    if not appdata:
        raise RuntimeError("APPDATA is not set; cannot locate MetaQuotes Common Files")
    return Path(appdata) / "MetaQuotes" / "Terminal" / "Common" / "Files" / "mt5_quant"


def candidate_roots(parent: Path) -> list[Path]:
    roots: list[Path] = []
    current = parent / "v69_frozen_forward_demo"
    if current.is_dir():
        roots.append(current)
    roots.extend(sorted((p for p in parent.glob("_v69_forward_previous_*") if p.is_dir()), reverse=True))
    return roots


def snapshot_analysis(path: Path, analyzer) -> dict | None:
    """Reconstruct the funnel from the pre-probe JSON saved before V69 relaunch."""
    if not path.is_file() or path.stat().st_size <= 0:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None
    raw_counts = payload.get("top_event_counts", {})
    if not isinstance(raw_counts, dict):
        raw_counts = {}
    event_counts: Counter[str] = Counter()
    for name, value in raw_counts.items():
        try:
            event_counts[str(name)] = int(value)
        except (TypeError, ValueError):
            continue

    stage_counts = {name: int(event_counts.get(name, 0)) for name in analyzer.FUNNEL_STAGES}
    aux_counts = {name: int(event_counts.get(name, 0)) for name in analyzer.AUX_EVENTS}
    closed = int(payload.get("closed_deals", 0) or 0)
    wait_reasons: Counter[str] = Counter()
    classification, blocker, next_action = analyzer.classify(stage_counts, wait_reasons, closed)
    try:
        events_rows = int(payload.get("events_rows", 0) or 0)
    except (TypeError, ValueError):
        events_rows = 0
    return {
        "root": f"snapshot:{path}",
        "source_kind": "PRE_PROBE_SIGNAL_PATH_JSON",
        "events_file_present": bool(payload.get("events_file_present", False)),
        "deals_file_present": bool(payload.get("deals_file_present", False)),
        "events_rows": events_rows,
        "closed_deals": closed,
        "stage_counts": stage_counts,
        "aux_event_counts": aux_counts,
        "classification": classification,
        "dominant_blocker": blocker,
        "next_action": next_action,
        "confirm_wait_reason_counts": {},
        "top_event_counts": dict(event_counts.most_common(60)),
        "top_detail_counts": payload.get("diagnostic_detail_counts", {}),
    }


def richness(result: dict) -> tuple[int, int, int, int]:
    stage_total = sum(int(v) for v in result.get("stage_counts", {}).values())
    source_bonus = 1 if result.get("source_kind") == "PRE_PROBE_SIGNAL_PATH_JSON" else 0
    file_bonus = int(bool(result.get("events_file_present")))
    return (int(result.get("events_rows", 0)), stage_total, source_bonus, file_bonus)


def eval_richness(result: dict) -> tuple[int, int]:
    return (int(result.get("rows", 0)), int(bool(result.get("eval_file_present"))))


def print_json_marker(name: str, value) -> None:
    print(name + "=" + json.dumps(value, ensure_ascii=False, sort_keys=True))


def main() -> int:
    branch, head = ensure_repo()
    analyzer = load(ANALYZER, "v69_upstream_signal_funnel")
    pre_pending = load(PRE_PENDING_ANALYZER, "v69_pre_pending_eval")
    parent = common_mt5_quant_root()
    print(f"V69_UPSTREAM_COMMON_PARENT={parent}")
    print("V69_UPSTREAM_READ_ONLY=1")
    print("V69_UPSTREAM_MT5_CAN_REMAIN_RUNNING=1")
    print("V69_UPSTREAM_METAEDITOR_REQUIRED=0")
    print("V69_UPSTREAM_ORDERS_SENT=0")

    roots = candidate_roots(parent)
    analyses = []
    for root in roots:
        result = analyzer.analyze(root)
        result["source_kind"] = "FILE_COMMON_ROOT"
        analyses.append(result)

    eval_aggregate = pre_pending.aggregate(roots)
    eval_analyses = list(eval_aggregate.get("source_analyses", []))

    snapshot = snapshot_analysis(PRE_PROBE_SIGNAL_PATH, analyzer)
    if snapshot is not None:
        analyses.append(snapshot)
        print(f"V69_UPSTREAM_PRE_PROBE_SNAPSHOT={PRE_PROBE_SIGNAL_PATH}")

    if not analyses:
        raise RuntimeError(
            f"no V69 forward telemetry roots or pre-probe snapshot found under {parent} / {PRE_PROBE_SIGNAL_PATH}"
        )

    analyses.sort(key=richness, reverse=True)
    selected = analyses[0]
    total_event_rows = sum(int(item.get("events_rows", 0)) for item in analyses)
    roots_with_rows = sum(1 for item in analyses if int(item.get("events_rows", 0)) > 0)
    if total_event_rows == 0:
        print("V69_UPSTREAM_ZERO_EVENT_ROWS_VALID=1")

    eval_analyses.sort(key=eval_richness, reverse=True)
    selected_eval = eval_analyses[0] if eval_analyses else {
        "root": "none",
        "rows": 0,
        "classification": "NO_PRE_PENDING_DIRECTIONAL_EVAL_ROWS",
        "dominant_blocker": "selector_or_feature_gate_unobserved",
        "next_action": "instrument V69 EvaluateBar before d==0 return to distinguish feature readiness, HTF regime, trigger, score and edge gates",
        "decision_reason_counts": {},
        "reject_reason_counts": {},
        "selected_direction_counts": {},
        "eval_file_present": False,
    }
    total_eval_rows = int(eval_aggregate.get("raw_rows_across_sources", 0))
    roots_with_eval_rows = int(eval_aggregate.get("sources_with_rows", 0))
    unique_eval_rows = int(eval_aggregate.get("unique_rows_across_sources", 0))
    duplicate_eval_rows = int(eval_aggregate.get("duplicate_rows_removed", 0))
    unique_eval = dict(eval_aggregate.get("unique_summary", {}))

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "protocol": "v69_upstream_signal_diagnostic_v4",
        "branch": branch,
        "head": head,
        "read_only": True,
        "mt5_can_remain_running": True,
        "orders_sent": False,
        "selected": selected,
        "all_sources": analyses,
        "total_event_rows_across_sources": total_event_rows,
        "sources_with_event_rows": roots_with_rows,
        "selected_pre_pending_eval": selected_eval,
        "all_pre_pending_eval_sources": eval_analyses,
        "aggregate_pre_pending_eval": eval_aggregate,
        "total_pre_pending_eval_rows": total_eval_rows,
        "unique_pre_pending_eval_rows": unique_eval_rows,
        "duplicate_pre_pending_eval_rows_removed": duplicate_eval_rows,
        "sources_with_pre_pending_eval_rows": roots_with_eval_rows,
    }
    out = OUT / "V69_UPSTREAM_SIGNAL_DIAGNOSTIC.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("V69_UPSTREAM_SOURCE_ROOT=" + selected["root"])
    print("V69_UPSTREAM_SOURCE_KIND=" + selected.get("source_kind", "UNKNOWN"))
    print(f"V69_UPSTREAM_EVENTS_ROWS={selected['events_rows']}")
    print(f"V69_UPSTREAM_TOTAL_EVENT_ROWS={total_event_rows}")
    print(f"V69_UPSTREAM_SOURCES_WITH_EVENT_ROWS={roots_with_rows}")
    for name, value in selected["stage_counts"].items():
        print(f"V69_UPSTREAM_{name}={value}")
    for name, value in selected.get("aux_event_counts", {}).items():
        print(f"V69_UPSTREAM_AUX_{name}={value}")
    print(f"V69_UPSTREAM_CLOSED_DEALS={selected['closed_deals']}")
    print("V69_UPSTREAM_CLASSIFICATION=" + selected["classification"])
    print("V69_UPSTREAM_TOP_BLOCKER=" + selected["dominant_blocker"])
    print("V69_UPSTREAM_NEXT_ACTION=" + selected["next_action"])
    print_json_marker("V69_UPSTREAM_CONFIRM_WAIT_REASONS", selected.get("confirm_wait_reason_counts", {}))
    print_json_marker("V69_UPSTREAM_TOP_EVENTS", selected.get("top_event_counts", {}))

    print("V69_PRE_PENDING_SOURCE_ROOT=" + str(selected_eval.get("root", "none")))
    print(f"V69_PRE_PENDING_EVAL_ROWS={int(selected_eval.get('rows', 0))}")
    print(f"V69_PRE_PENDING_TOTAL_EVAL_ROWS={total_eval_rows}")
    print(f"V69_PRE_PENDING_SOURCES_WITH_ROWS={roots_with_eval_rows}")
    print("V69_PRE_PENDING_CLASSIFICATION=" + str(selected_eval.get("classification", "UNKNOWN")))
    print("V69_PRE_PENDING_TOP_BLOCKER=" + str(selected_eval.get("dominant_blocker", "UNKNOWN")))
    print("V69_PRE_PENDING_NEXT_ACTION=" + str(selected_eval.get("next_action", "UNKNOWN")))
    print_json_marker("V69_PRE_PENDING_DECISION_REASONS", selected_eval.get("decision_reason_counts", {}))
    print_json_marker("V69_PRE_PENDING_REJECT_REASONS", selected_eval.get("reject_reason_counts", {}))
    print_json_marker("V69_PRE_PENDING_SELECTED_DIRECTIONS", selected_eval.get("selected_direction_counts", {}))

    print(f"V69_PRE_PENDING_ALL_RAW_ROWS={total_eval_rows}")
    print(f"V69_PRE_PENDING_ALL_UNIQUE_ROWS={unique_eval_rows}")
    print(f"V69_PRE_PENDING_ALL_DUPLICATE_ROWS_REMOVED={duplicate_eval_rows}")
    print("V69_PRE_PENDING_ALL_CONTEXT=" + str(unique_eval.get("direction_context_classification", "UNKNOWN")))
    print("V69_PRE_PENDING_ALL_CONTEXT_NEXT_ACTION=" + str(unique_eval.get("direction_context_next_action", "UNKNOWN")))
    print_json_marker("V69_PRE_PENDING_ALL_DECISION_REASONS", unique_eval.get("decision_reason_counts", {}))
    print_json_marker("V69_PRE_PENDING_ALL_REJECT_REASONS", unique_eval.get("reject_reason_counts", {}))
    print_json_marker("V69_PRE_PENDING_ALL_SELECTED_DIRECTIONS", unique_eval.get("selected_direction_counts", {}))
    print_json_marker("V69_PRE_PENDING_ALL_HTF_REGIMES", unique_eval.get("htf_regime_counts", {}))
    print_json_marker("V69_PRE_PENDING_ALL_TRIGGER_STATES", unique_eval.get("trigger_state_counts", {}))
    print_json_marker("V69_PRE_PENDING_ALL_SCORE_RELATIONS", unique_eval.get("score_relation_counts", {}))
    print_json_marker("V69_PRE_PENDING_ALL_H1_TRENDS", unique_eval.get("h1_trend_counts", {}))
    print_json_marker("V69_PRE_PENDING_ALL_H4_TRENDS", unique_eval.get("h4_trend_counts", {}))
    print_json_marker("V69_PRE_PENDING_ALL_SELECTED_BY_HTF", unique_eval.get("selected_by_htf_regime", {}))
    print_json_marker("V69_PRE_PENDING_ALL_SELECTED_BY_TRIGGER", unique_eval.get("selected_by_trigger_state", {}))
    print_json_marker("V69_PRE_PENDING_ALL_COMPONENT_DIRECTIONS", unique_eval.get("component_direction_counts", {}))
    print_json_marker(
        "V69_PRE_PENDING_ALL_SCORE_SUMMARY",
        {
            "long_min": unique_eval.get("long_score_min"),
            "long_max": unique_eval.get("long_score_max"),
            "long_mean": unique_eval.get("long_score_mean"),
            "short_min": unique_eval.get("short_score_min"),
            "short_max": unique_eval.get("short_score_max"),
            "short_mean": unique_eval.get("short_score_mean"),
            "long_minus_short_min": unique_eval.get("long_minus_short_score_min"),
            "long_minus_short_max": unique_eval.get("long_minus_short_score_max"),
            "long_minus_short_mean": unique_eval.get("long_minus_short_score_mean"),
        },
    )
    print_json_marker("V69_PRE_PENDING_ALL_SOURCE_SUMMARY", eval_aggregate.get("source_summaries", []))

    print(f"V69_UPSTREAM_ANALYZED_SOURCES={len(analyses)}")
    print(f"V69_UPSTREAM_RESULT_JSON={out}")
    print("V69_UPSTREAM_DIAGNOSTIC=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=os.sys.stderr)
        raise
