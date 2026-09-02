#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
from collections import Counter
from pathlib import Path

EVAL_FILE = "V64_ENTRY_EVAL.csv"
DIRECTION_COMPONENTS = (
    "structure_dir",
    "bos_choch_dir",
    "fvg_dir",
    "liquidity_sweep_dir",
    "order_block_retest_dir",
    "pullback_dir",
    "di_dir",
    "macd_dir",
    "location_dir",
)


def read_csv_snapshot(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a live CSV defensively and ignore a partial final record."""
    if not path.is_file() or path.stat().st_size <= 0:
        return [], []
    raw = path.read_bytes()
    if not raw:
        return [], []
    if not raw.endswith((b"\n", b"\r")):
        cut = max(raw.rfind(b"\n"), raw.rfind(b"\r"))
        if cut < 0:
            return [], []
        raw = raw[: cut + 1]
    text = raw.decode("utf-8-sig", errors="replace")
    if not text.strip():
        return [], []
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = list(reader)
    return list(reader.fieldnames or []), rows


def int_value(row: dict[str, str], key: str) -> int:
    try:
        return int(float((row.get(key) or "0").strip() or 0))
    except (TypeError, ValueError):
        return 0


def mean_or_none(values: list[int]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def selector_htf_regime(row: dict[str, str]) -> str:
    """Mirror the V59 selector's HTF regime predicates exactly."""
    h4 = int_value(row, "h4_trend")
    h1 = int_value(row, "h1_trend")
    long_regime = h1 == 1 and h4 != -1
    short_regime = h1 == -1 and h4 != 1
    if long_regime and not short_regime:
        return "LONG_HTF_REGIME"
    if short_regime and not long_regime:
        return "SHORT_HTF_REGIME"
    return "NO_DIRECTIONAL_HTF_REGIME"


def selector_trigger_state(row: dict[str, str]) -> str:
    """Mirror the V59 selector's trigger predicates from logged feature columns."""
    bos = int_value(row, "bos_choch_dir")
    fvg = int_value(row, "fvg_dir")
    sweep = int_value(row, "liquidity_sweep_dir")
    ob = int_value(row, "order_block_retest_dir")
    pullback = int_value(row, "pullback_dir")
    m15 = int_value(row, "m15_trend")
    long_trigger = bos == 1 or fvg == 1 or sweep == 1 or ob == 1 or (pullback == 1 and m15 == 1)
    short_trigger = bos == -1 or fvg == -1 or sweep == -1 or ob == -1 or (pullback == -1 and m15 == -1)
    if long_trigger and short_trigger:
        return "BOTH_TRIGGERS"
    if long_trigger:
        return "LONG_TRIGGER_ONLY"
    if short_trigger:
        return "SHORT_TRIGGER_ONLY"
    return "NO_SELECTOR_TRIGGER"


def score_relation(row: dict[str, str]) -> str:
    long_score = int_value(row, "long_score")
    short_score = int_value(row, "short_score")
    if long_score > short_score:
        return "LONG_SCORE_HIGHER"
    if short_score > long_score:
        return "SHORT_SCORE_HIGHER"
    return "SCORES_TIED"


def row_identity(row: dict[str, str]) -> tuple[tuple[str, str], ...]:
    """Stable identity used only to remove copies of the same eval row across rotated roots."""
    items: list[tuple[str, str]] = []
    for key, value in row.items():
        if key is None:
            continue
        items.append((str(key), "" if value is None else str(value).strip()))
    return tuple(sorted(items))


def classify_rows(rows: list[dict[str, str]], reject: Counter[str]) -> tuple[str, str, str]:
    no_arch = reject.get("no_complete_archetype", 0)
    bad_stop = reject.get("invalid_arm_structural_stop", 0)
    isolated = reject.get("direction_isolated_out", 0)
    pending = sum(v for k, v in reject.items() if k.startswith("pending_"))

    if rows and no_arch > 0 and no_arch >= max(bad_stop, isolated, pending):
        return (
            "ARCHETYPE_COMPLETION_BLOCK_BEFORE_PENDING_ARM",
            "no_complete_archetype",
            "inspect pullback-sweep and breakout-retest component availability on M15",
        )
    if rows and bad_stop > 0 and bad_stop >= max(no_arch, isolated, pending):
        return (
            "STRUCTURAL_STOP_BLOCK_BEFORE_PENDING_ARM",
            "invalid_arm_structural_stop",
            "inspect raw M15 swing stop geometry versus current entry",
        )
    if rows and isolated > 0 and isolated >= max(no_arch, bad_stop, pending):
        return (
            "DIRECTION_ISOLATION_BLOCK_BEFORE_PENDING_ARM",
            "direction_isolated_out",
            "inspect deduplicated all-source selector direction, HTF regime, trigger state and score relation; keep SHORT disabled",
        )
    if rows and pending > 0:
        return (
            "PENDING_EVAL_LOGGED_BUT_PENDING_EVENT_MISSING_REVIEW_TELEMETRY",
            "pending_eval_without_pending_event",
            "compare ENTRY_EVAL timestamps with V64_EVENTS writer and pending-state mutation",
        )
    if rows:
        blocker = reject.most_common(1)[0][0] if reject else "directional_eval_without_reject_reason"
        return (
            "PRE_PENDING_DIRECTIONAL_EVAL_OBSERVED",
            blocker,
            "review decision/reject distributions before adding new live instrumentation",
        )
    return (
        "NO_PRE_PENDING_DIRECTIONAL_EVAL_ROWS",
        "selector_or_feature_gate_unobserved",
        "instrument V69 EvaluateBar before d==0 return to distinguish feature readiness, HTF regime, trigger, score and edge gates",
    )


def direction_context(summary: dict) -> tuple[str, str]:
    rows = int(summary.get("rows", 0))
    selected = summary.get("selected_direction_counts", {})
    decision = summary.get("decision_reason_counts", {})
    regimes = summary.get("htf_regime_counts", {})
    short_rows = int(selected.get("-1", 0))
    long_rows = int(selected.get("1", 0))
    if rows <= 0:
        return (
            "NO_UNIQUE_PRE_PENDING_EVAL_ROWS",
            "add observability before selector d==0; do not alter strategy thresholds",
        )
    if (
        short_rows == rows
        and int(decision.get("short_edge", 0)) == rows
        and int(regimes.get("SHORT_HTF_REGIME", 0)) == rows
    ):
        return (
            "ALL_UNIQUE_EVALS_SHORT_EDGE_IN_SHORT_HTF_REGIME",
            "frozen LONG-only abstention is consistent with selector state; do not enable SHORT without separate research",
        )
    if long_rows > 0:
        return (
            "LONG_SELECTOR_CANDIDATES_EXIST_ACROSS_PRESERVED_EVALS",
            "localize which roots/times produced LONG and why they did or did not progress to PENDING_ARM",
        )
    if short_rows == rows:
        return (
            "ALL_UNIQUE_EVALS_SELECTED_SHORT",
            "verify HTF/trigger/score consistency before deciding whether this is regime abstention or selector asymmetry",
        )
    return (
        "MIXED_SELECTOR_DIRECTION_EVIDENCE",
        "compare LONG and SHORT rows by HTF regime, trigger state and score relation before strategy research changes",
    )


def summarize_rows(rows: list[dict[str, str]]) -> dict:
    decision = Counter((r.get("decision_reason") or "").strip() for r in rows if (r.get("decision_reason") or "").strip())
    reject = Counter((r.get("reject_reason") or "").strip() for r in rows if (r.get("reject_reason") or "").strip())
    selected = Counter(str(int_value(r, "selected_direction")) for r in rows)
    htf_regimes = Counter(selector_htf_regime(r) for r in rows)
    trigger_states = Counter(selector_trigger_state(r) for r in rows)
    score_relations = Counter(score_relation(r) for r in rows)
    h1_trends = Counter(str(int_value(r, "h1_trend")) for r in rows)
    h4_trends = Counter(str(int_value(r, "h4_trend")) for r in rows)
    long_scores = [int_value(r, "long_score") for r in rows]
    short_scores = [int_value(r, "short_score") for r in rows]
    score_margins = [int_value(r, "long_score") - int_value(r, "short_score") for r in rows]
    times = sorted((r.get("time") or "").strip() for r in rows if (r.get("time") or "").strip())

    selected_by_htf: dict[str, Counter[str]] = {}
    selected_by_trigger: dict[str, Counter[str]] = {}
    for row in rows:
        d = str(int_value(row, "selected_direction"))
        regime = selector_htf_regime(row)
        trigger = selector_trigger_state(row)
        selected_by_htf.setdefault(regime, Counter())[d] += 1
        selected_by_trigger.setdefault(trigger, Counter())[d] += 1

    component_counts: dict[str, dict[str, int]] = {}
    for field in DIRECTION_COMPONENTS:
        counts = Counter(str(int_value(r, field)) for r in rows)
        component_counts[field] = dict(counts.most_common())

    classification, blocker, next_action = classify_rows(rows, reject)
    summary = {
        "rows": len(rows),
        "classification": classification,
        "dominant_blocker": blocker,
        "next_action": next_action,
        "decision_reason_counts": dict(decision.most_common(30)),
        "reject_reason_counts": dict(reject.most_common(30)),
        "selected_direction_counts": dict(selected.most_common()),
        "htf_regime_counts": dict(htf_regimes.most_common()),
        "trigger_state_counts": dict(trigger_states.most_common()),
        "score_relation_counts": dict(score_relations.most_common()),
        "h1_trend_counts": dict(h1_trends.most_common()),
        "h4_trend_counts": dict(h4_trends.most_common()),
        "selected_by_htf_regime": {k: dict(v.most_common()) for k, v in selected_by_htf.items()},
        "selected_by_trigger_state": {k: dict(v.most_common()) for k, v in selected_by_trigger.items()},
        "component_direction_counts": component_counts,
        "rejection_rows": sum(reject.values()),
        "first_time": times[0] if times else None,
        "last_time": times[-1] if times else None,
        "long_score_min": min(long_scores) if long_scores else None,
        "long_score_max": max(long_scores) if long_scores else None,
        "long_score_mean": mean_or_none(long_scores),
        "short_score_min": min(short_scores) if short_scores else None,
        "short_score_max": max(short_scores) if short_scores else None,
        "short_score_mean": mean_or_none(short_scores),
        "long_minus_short_score_min": min(score_margins) if score_margins else None,
        "long_minus_short_score_max": max(score_margins) if score_margins else None,
        "long_minus_short_score_mean": mean_or_none(score_margins),
    }
    context, context_next = direction_context(summary)
    summary["direction_context_classification"] = context
    summary["direction_context_next_action"] = context_next
    return summary


def analyze(root: Path) -> dict:
    path = root / EVAL_FILE
    fields, rows = read_csv_snapshot(path)
    result = summarize_rows(rows)
    result.update(
        {
            "root": str(root),
            "eval_path": str(path),
            "eval_file_present": path.is_file(),
            "header": fields,
        }
    )
    return result


def source_brief(result: dict) -> dict:
    return {
        "root": result.get("root"),
        "rows": int(result.get("rows", 0)),
        "first_time": result.get("first_time"),
        "last_time": result.get("last_time"),
        "decision_reason_counts": result.get("decision_reason_counts", {}),
        "reject_reason_counts": result.get("reject_reason_counts", {}),
        "selected_direction_counts": result.get("selected_direction_counts", {}),
        "htf_regime_counts": result.get("htf_regime_counts", {}),
        "trigger_state_counts": result.get("trigger_state_counts", {}),
        "score_relation_counts": result.get("score_relation_counts", {}),
        "long_score_mean": result.get("long_score_mean"),
        "short_score_mean": result.get("short_score_mean"),
        "long_minus_short_score_mean": result.get("long_minus_short_score_mean"),
    }


def aggregate(roots: list[Path]) -> dict:
    """Aggregate all roots and deduplicate copied rows created by FILE_COMMON rotations."""
    source_analyses: list[dict] = []
    unique_rows: list[dict[str, str]] = []
    seen: set[tuple[tuple[str, str], ...]] = set()
    raw_rows = 0
    duplicate_rows = 0

    for root in roots:
        path = root / EVAL_FILE
        fields, rows = read_csv_snapshot(path)
        result = summarize_rows(rows)
        result.update(
            {
                "root": str(root),
                "eval_path": str(path),
                "eval_file_present": path.is_file(),
                "header": fields,
            }
        )
        source_analyses.append(result)
        raw_rows += len(rows)
        for row in rows:
            identity = row_identity(row)
            if identity in seen:
                duplicate_rows += 1
                continue
            seen.add(identity)
            unique_rows.append(row)

    unique_summary = summarize_rows(unique_rows)
    return {
        "raw_rows_across_sources": raw_rows,
        "unique_rows_across_sources": len(unique_rows),
        "duplicate_rows_removed": duplicate_rows,
        "sources": len(source_analyses),
        "sources_with_rows": sum(1 for item in source_analyses if int(item.get("rows", 0)) > 0),
        "unique_summary": unique_summary,
        "source_analyses": source_analyses,
        "source_summaries": [source_brief(item) for item in source_analyses],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    result = analyze(args.root)
    print(f"V69_PRE_PENDING_EVAL_ROWS={result['rows']}")
    print("V69_PRE_PENDING_CLASSIFICATION=" + result["classification"])
    print("V69_PRE_PENDING_TOP_BLOCKER=" + result["dominant_blocker"])
    print("V69_PRE_PENDING_NEXT_ACTION=" + result["next_action"])
    print("V69_PRE_PENDING_DECISION_REASONS=" + json.dumps(result["decision_reason_counts"], sort_keys=True))
    print("V69_PRE_PENDING_REJECT_REASONS=" + json.dumps(result["reject_reason_counts"], sort_keys=True))
    print("V69_PRE_PENDING_SELECTED_DIRECTIONS=" + json.dumps(result["selected_direction_counts"], sort_keys=True))
    print("V69_PRE_PENDING_HTF_REGIMES=" + json.dumps(result["htf_regime_counts"], sort_keys=True))
    print("V69_PRE_PENDING_TRIGGER_STATES=" + json.dumps(result["trigger_state_counts"], sort_keys=True))
    print("V69_PRE_PENDING_SCORE_RELATIONS=" + json.dumps(result["score_relation_counts"], sort_keys=True))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"V69_PRE_PENDING_JSON={args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
