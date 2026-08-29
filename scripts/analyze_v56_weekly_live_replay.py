#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

CANDIDATE = "v52_b4_or_b3_trend_bos"
BOOK = "usd40_r1p0_cent_continuous"
WEEK_START = datetime(2026, 8, 24)
WEEK_END = datetime(2026, 8, 29)
OK_RETCODES = {10008, 10009, 10010}  # PLACED, DONE, DONE_PARTIAL


def parse_event_time(value: str) -> datetime | None:
    value = value.strip()
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def in_week(ts: datetime | None) -> bool:
    return ts is not None and WEEK_START <= ts < WEEK_END


def parse_kv(path: Path | None) -> dict[str, str]:
    if path is None or not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8-sig", errors="replace").replace("\\r\\n", "\n")
    out: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def analyze_events(path: Path) -> dict:
    virtual_open = 0
    virtual_close = 0
    broker_open = 0
    broker_close = 0
    rejected_open = 0
    rejected_close = 0
    guards: Counter[str] = Counter()
    rows_in_week = 0
    first_virtual_open = None
    first_broker_open = None

    if not path.is_file():
        raise RuntimeError(f"V56 events file missing: {path}")

    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        for raw in csv.reader(fh):
            if len(raw) < 2:
                continue
            ts = parse_event_time(raw[0])
            if not in_week(ts):
                continue
            rows_in_week += 1
            kind = raw[1].strip()
            if kind == "V56_VIRTUAL_OPEN":
                virtual_open += 1
                if first_virtual_open is None:
                    first_virtual_open = raw[0].strip()
            elif kind == "V56_VIRTUAL_CLOSE":
                virtual_close += 1
            elif kind == "GUARD":
                guards[raw[2].strip() if len(raw) >= 3 else "<missing>"] += 1
            elif kind in ("OPEN", "CLOSE"):
                call_ok = None
                retcode = None
                if len(raw) >= 11:
                    try:
                        call_ok = int(raw[9].strip())
                    except ValueError:
                        pass
                    try:
                        retcode = int(raw[10].strip())
                    except ValueError:
                        pass
                rejected = call_ok != 1 or retcode not in OK_RETCODES
                if kind == "OPEN":
                    broker_open += 1
                    if first_broker_open is None:
                        first_broker_open = raw[0].strip()
                    if rejected:
                        rejected_open += 1
                else:
                    broker_close += 1
                    if rejected:
                        rejected_close += 1

    return {
        "rows_in_week": rows_in_week,
        "virtual_open_transitions": virtual_open,
        "virtual_close_transitions": virtual_close,
        "broker_open_requests": broker_open,
        "broker_close_requests": broker_close,
        "rejected_open_requests": rejected_open,
        "rejected_close_requests": rejected_close,
        "first_virtual_open": first_virtual_open,
        "first_broker_open": first_broker_open,
        "guard_reason_counts": dict(sorted(guards.items())),
    }


def analyze_trades(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"V56 trades file missing/empty: {path}")
    df = pd.read_csv(path)
    required = {"candidate", "book", "entry_time", "exit_time", "r_multiple"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise RuntimeError(f"V56 trades.csv missing columns: {missing}")

    selected = df[(df["candidate"].astype(str) == CANDIDATE) & (df["book"].astype(str) == BOOK)].copy()
    selected["entry_dt"] = pd.to_datetime(selected["entry_time"], errors="coerce")
    selected["exit_dt"] = pd.to_datetime(selected["exit_time"], errors="coerce")
    selected["r_num"] = pd.to_numeric(selected["r_multiple"], errors="coerce")

    entered = selected[(selected["entry_dt"] >= WEEK_START) & (selected["entry_dt"] < WEEK_END)]
    exited = selected[(selected["exit_dt"] >= WEEK_START) & (selected["exit_dt"] < WEEK_END)]
    r = entered["r_num"].dropna()

    return {
        "selected_candidate_rows_all_replay": int(len(selected)),
        "selected_closed_trades_entered_in_week": int(len(entered)),
        "selected_closed_trades_exited_in_week": int(len(exited)),
        "selected_week_sum_r": float(r.sum()) if len(r) else 0.0,
        "selected_week_avg_r": float(r.mean()) if len(r) else None,
        "selected_week_wins": int((r > 0).sum()) if len(r) else 0,
        "selected_week_losses": int((r <= 0).sum()) if len(r) else 0,
        "books_seen_for_candidate": sorted(set(df.loc[df["candidate"].astype(str) == CANDIDATE, "book"].astype(str))),
    }


def determine_verdict(events: dict, status: dict[str, str]) -> str:
    if status.get("halted") == "1":
        return "V56_WEEK_RUNTIME_HALTED"
    virtual_open = int(events.get("virtual_open_transitions", 0))
    broker_open = int(events.get("broker_open_requests", 0))
    rejected_open = int(events.get("rejected_open_requests", 0))
    if virtual_open == 0:
        return "V56_WEEK_NO_SELECTED_CANDIDATE_ENTRY"
    if broker_open == 0:
        return "V56_WEEK_EXECUTION_MAPPING_BLOCKED"
    if broker_open < virtual_open:
        return "V56_WEEK_PARTIAL_MAPPING"
    if rejected_open > 0:
        return "V56_WEEK_BROKER_REJECTION_OBSERVED"
    return "V56_WEEK_MAPPING_OBSERVED"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--status")
    ap.add_argument("--output", required=True)
    ap.add_argument("--summary", required=True)
    ns = ap.parse_args()

    trades = analyze_trades(Path(ns.trades))
    events = analyze_events(Path(ns.events))
    status = parse_kv(Path(ns.status) if ns.status else None)
    verdict = determine_verdict(events, status)

    payload = {
        "schema": "v56_weekly_real_tick_live_replay_v1",
        "verdict": verdict,
        "candidate": CANDIDATE,
        "book": BOOK,
        "week_start_broker_time": WEEK_START.isoformat(sep=" "),
        "week_end_exclusive_broker_time": WEEK_END.isoformat(sep=" "),
        "tester_model": 4,
        "real_ticks": True,
        "alpha_changed_from_v55": False,
        "execution_mapping_changed_from_v55": False,
        "trades": trades,
        "events": events,
        "final_status": {
            "account_mode": status.get("account_mode"),
            "halted": status.get("halted"),
            "halt_reason": status.get("halt_reason"),
            "requests": status.get("requests"),
            "rejects": status.get("rejects"),
            "candidate": status.get("candidate"),
        },
        "interpretation": {
            "V56_WEEK_NO_SELECTED_CANDIDATE_ENTRY": "The selected virtual strategy produced no entry transition during 24-28 Aug; zero live orders is consistent with alpha opportunity frequency for this replay.",
            "V56_WEEK_EXECUTION_MAPPING_BLOCKED": "The selected virtual strategy opened, but V55 emitted no broker OPEN request; inspect production guards/mapping.",
            "V56_WEEK_PARTIAL_MAPPING": "Some selected virtual entries did not map to broker OPEN requests; inspect guard chronology.",
            "V56_WEEK_BROKER_REJECTION_OBSERVED": "Selected entries mapped to broker requests, but at least one simulated broker OPEN was rejected.",
            "V56_WEEK_MAPPING_OBSERVED": "Selected virtual entries mapped to simulated broker OPEN requests under V55 execution logic.",
            "V56_WEEK_RUNTIME_HALTED": "The replay ended halted; halt_reason is authoritative and must be fixed before drawing an alpha conclusion.",
        }.get(verdict, ""),
    }

    out = Path(ns.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    summary = Path(ns.summary)
    lines = [
        f"V56_WEEKLY_REPLAY_VERDICT={verdict}",
        f"CANDIDATE={CANDIDATE}",
        f"BOOK={BOOK}",
        "WEEK=2026-08-24..2026-08-28",
        "TESTER_MODEL=4",
        "REAL_TICKS=1",
        f"VIRTUAL_OPENS={events['virtual_open_transitions']}",
        f"VIRTUAL_CLOSES={events['virtual_close_transitions']}",
        f"BROKER_OPEN_REQUESTS={events['broker_open_requests']}",
        f"BROKER_CLOSE_REQUESTS={events['broker_close_requests']}",
        f"REJECTED_OPEN_REQUESTS={events['rejected_open_requests']}",
        f"SELECTED_CLOSED_TRADES_ENTERED_IN_WEEK={trades['selected_closed_trades_entered_in_week']}",
        f"SELECTED_WEEK_SUM_R={trades['selected_week_sum_r']}",
        f"HALTED={status.get('halted','')}",
        f"HALT_REASON={status.get('halt_reason','')}",
        "GUARD_REASON_COUNTS=" + json.dumps(events["guard_reason_counts"], sort_keys=True),
        "",
    ]
    summary.write_text("\n".join(lines), encoding="utf-8")

    print(lines[0])
    print(f"VIRTUAL_OPENS={events['virtual_open_transitions']}")
    print(f"BROKER_OPEN_REQUESTS={events['broker_open_requests']}")
    print(f"REJECTED_OPEN_REQUESTS={events['rejected_open_requests']}")
    print(f"SELECTED_CLOSED_TRADES_ENTERED_IN_WEEK={trades['selected_closed_trades_entered_in_week']}")
    print("GUARD_REASON_COUNTS=" + json.dumps(events["guard_reason_counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
