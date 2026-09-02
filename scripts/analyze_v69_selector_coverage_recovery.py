#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

DIRECTIONAL_CORE_FUNCTIONS = (
    "V64EMA",
    "V64ATR",
    "V64RSI",
    "V64PivotHigh",
    "V64PivotLow",
    "V64ConfirmedSwings",
    "V64RecentFvgDir",
    "V64DIADX",
    "V64OrderBlockRetestDir",
    "V64ScoreDirection",
    "V64BuildFeatures",
    "V64SelectDirection",
)
THRESHOLD_INPUTS = (
    "InpV64MinDirectionalScore",
    "InpV64MinScoreEdge",
)


def parse_time(value: str) -> datetime | None:
    value = (value or "").strip()
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y.%m.%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def as_int(row: dict[str, str], key: str) -> int:
    try:
        return int(float((row.get(key) or "0").strip()))
    except (TypeError, ValueError):
        return 0


def as_float(row: dict[str, str], key: str) -> float | None:
    try:
        return float((row.get(key) or "").strip())
    except (TypeError, ValueError):
        return None


def re_search_function(text: str, name: str):
    import re

    pattern = re.compile(r"(?m)^[A-Za-z_][A-Za-z0-9_<>&\s\*]*\b" + re.escape(name) + r"\s*\(")
    match = pattern.search(text)
    if match is None:
        raise ValueError(f"function {name} missing")
    return match


def extract_function(text: str, name: str) -> str:
    match = re_search_function(text, name)
    start = match.start()
    brace = text.find("{", match.end())
    if brace < 0:
        raise ValueError(f"function {name} opening brace missing")
    depth = 0
    for idx in range(brace, len(text)):
        ch = text[idx]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]
    raise ValueError(f"function {name} closing brace missing")


def normalize_code(text: str) -> str:
    return "".join(text.split())


def extract_input(text: str, name: str) -> str:
    import re

    pattern = re.compile(r"(?m)^\s*input\s+[^;\n]*\b" + re.escape(name) + r"\s*=\s*[^;]+;")
    match = pattern.search(text)
    if match is None:
        raise ValueError(f"input {name} missing")
    return normalize_code(match.group(0))


def compare_directional_core(screen_source: str, v69_source: str) -> dict:
    mismatches: list[str] = []
    for name in DIRECTIONAL_CORE_FUNCTIONS:
        left = normalize_code(extract_function(screen_source, name))
        right = normalize_code(extract_function(v69_source, name))
        if left != right:
            mismatches.append(name)
    threshold_mismatches: list[str] = []
    for name in THRESHOLD_INPUTS:
        if extract_input(screen_source, name) != extract_input(v69_source, name):
            threshold_mismatches.append(name)
    return {
        "exact_directional_core_match": not mismatches and not threshold_mismatches,
        "function_mismatches": mismatches,
        "threshold_mismatches": threshold_mismatches,
        "functions_checked": list(DIRECTIONAL_CORE_FUNCTIONS),
        "thresholds_checked": list(THRESHOLD_INPUTS),
    }


def htf_regime(row: dict[str, str]) -> str:
    h1 = as_int(row, "h1_trend")
    h4 = as_int(row, "h4_trend")
    if h1 == 1 and h4 != -1:
        return "LONG_HTF_REGIME"
    if h1 == -1 and h4 != 1:
        return "SHORT_HTF_REGIME"
    return "NEUTRAL_HTF_REGIME"


def trigger_state(row: dict[str, str]) -> str:
    m15 = as_int(row, "m15_trend")
    long_trigger = (
        as_int(row, "bos_choch_dir") == 1
        or as_int(row, "fvg_dir") == 1
        or as_int(row, "liquidity_sweep_dir") == 1
        or as_int(row, "order_block_retest_dir") == 1
        or (as_int(row, "pullback_dir") == 1 and m15 == 1)
    )
    short_trigger = (
        as_int(row, "bos_choch_dir") == -1
        or as_int(row, "fvg_dir") == -1
        or as_int(row, "liquidity_sweep_dir") == -1
        or as_int(row, "order_block_retest_dir") == -1
        or (as_int(row, "pullback_dir") == -1 and m15 == -1)
    )
    if long_trigger and short_trigger:
        return "BOTH_TRIGGERS"
    if long_trigger:
        return "LONG_TRIGGER_ONLY"
    if short_trigger:
        return "SHORT_TRIGGER_ONLY"
    return "NO_TRIGGER"


def pct(n: int, d: int) -> float:
    return round(100.0 * n / d, 4) if d else 0.0


def score_stats(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"min": None, "mean": None, "max": None}
    return {
        "min": round(min(values), 4),
        "mean": round(sum(values) / len(values), 4),
        "max": round(max(values), 4),
    }


def analyze_rows(rows: list[dict[str, str]]) -> dict:
    parsed = [(parse_time(row.get("time", "")), row) for row in rows]
    parsed = [(time, row) for time, row in parsed if time is not None]
    parsed.sort(key=lambda item: item[0])
    unique_by_time: dict[datetime, dict[str, str]] = {}
    for time, row in parsed:
        unique_by_time[time] = row
    ordered = sorted(unique_by_time.items())
    data = [row for _, row in ordered]
    times = [time for time, _ in ordered]

    directions = Counter(str(as_int(row, "selected_direction")) for row in data)
    reasons = Counter((row.get("decision_reason") or "").strip() or "EMPTY" for row in data)
    regimes = Counter(htf_regime(row) for row in data)
    triggers = Counter(trigger_state(row) for row in data)
    feature_not_ready = reasons.get("feature_not_ready", 0)
    feature_ready = len(data) - feature_not_ready
    long_n = directions.get("1", 0)
    short_n = directions.get("-1", 0)
    neutral_n = directions.get("0", 0)
    directional_n = long_n + short_n

    by_month: defaultdict[str, Counter] = defaultdict(Counter)
    for time, row in ordered:
        key = time.strftime("%Y-%m")
        by_month[key][str(as_int(row, "selected_direction"))] += 1
        by_month[key][htf_regime(row)] += 1
        by_month[key]["rows"] += 1

    long_scores = [value for value in (as_float(row, "long_score") for row in data) if value is not None]
    short_scores = [value for value in (as_float(row, "short_score") for row in data) if value is not None]
    edge: list[float] = []
    for row in data:
        long_score = as_float(row, "long_score")
        short_score = as_float(row, "short_score")
        if long_score is not None and short_score is not None:
            edge.append(long_score - short_score)

    return {
        "raw_rows": len(rows),
        "parsed_rows": len(parsed),
        "unique_m15_rows": len(data),
        "duplicate_times_removed": len(parsed) - len(data),
        "first_time": times[0].strftime("%Y.%m.%d %H:%M:%S") if times else None,
        "last_time": times[-1].strftime("%Y.%m.%d %H:%M:%S") if times else None,
        "span_days": (times[-1] - times[0]).days if len(times) >= 2 else 0,
        "feature_ready_rows": feature_ready,
        "feature_not_ready_rows": feature_not_ready,
        "feature_ready_pct": pct(feature_ready, len(data)),
        "selected_direction_counts": dict(sorted(directions.items())),
        "decision_reason_counts": dict(sorted(reasons.items())),
        "htf_regime_counts": dict(sorted(regimes.items())),
        "trigger_state_counts": dict(sorted(triggers.items())),
        "long_selected_rows": long_n,
        "short_selected_rows": short_n,
        "neutral_selected_rows": neutral_n,
        "directional_selected_rows": directional_n,
        "long_selected_pct_all_bars": pct(long_n, len(data)),
        "short_selected_pct_all_bars": pct(short_n, len(data)),
        "neutral_selected_pct_all_bars": pct(neutral_n, len(data)),
        "directional_selected_pct_all_bars": pct(directional_n, len(data)),
        "long_share_of_directional_pct": pct(long_n, directional_n),
        "short_share_of_directional_pct": pct(short_n, directional_n),
        "long_score": score_stats(long_scores),
        "short_score": score_stats(short_scores),
        "long_minus_short_score": score_stats(edge),
        "by_month": {month: dict(sorted(counts.items())) for month, counts in sorted(by_month.items())},
        "classification": (
            "NO_COVERAGE_ROWS"
            if not data
            else "LONG_SELECTOR_COVERAGE_PRESENT"
            if long_n > 0
            else "NO_LONG_SELECTOR_SELECTION_IN_SCREEN"
        ),
    }


def analyze_csv(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        rows = list(csv.DictReader(handle))
    result = analyze_rows(rows)
    result["source_csv"] = str(path)
    return result


def write_outputs(result: dict, output: Path | None, summary: Path | None) -> None:
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if summary is not None:
        summary.parent.mkdir(parents=True, exist_ok=True)
        coverage = result.get("coverage", {})
        identity = result.get("selector_identity", {})
        lines = [
            "V69_SELECTOR_COVERAGE_RECOVERY=1",
            f"SELECTOR_IDENTITY={'PASS' if identity.get('exact_directional_core_match') else 'FAIL'}",
            f"UNIQUE_M15_ROWS={coverage.get('unique_m15_rows', 0)}",
            f"FIRST_TIME={coverage.get('first_time')}",
            f"LAST_TIME={coverage.get('last_time')}",
            f"FEATURE_READY_PCT={coverage.get('feature_ready_pct', 0.0)}",
            f"LONG_SELECTED_PCT_ALL_BARS={coverage.get('long_selected_pct_all_bars', 0.0)}",
            f"SHORT_SELECTED_PCT_ALL_BARS={coverage.get('short_selected_pct_all_bars', 0.0)}",
            f"NEUTRAL_SELECTED_PCT_ALL_BARS={coverage.get('neutral_selected_pct_all_bars', 0.0)}",
            f"LONG_SHARE_OF_DIRECTIONAL_PCT={coverage.get('long_share_of_directional_pct', 0.0)}",
            f"SHORT_SHARE_OF_DIRECTIONAL_PCT={coverage.get('short_share_of_directional_pct', 0.0)}",
            f"COVERAGE_CLASSIFICATION={coverage.get('classification')}",
            "DEVELOPMENT_COVERAGE_ONLY=1",
            "INDEPENDENT_EDGE_EVIDENCE=0",
            "STRATEGY_CHANGED=0",
            "ORDERS_SENT=0",
            "REAL_MONEY_AUTHORIZED=0",
        ]
        summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
