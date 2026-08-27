#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import time
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUPERVISOR = HERE / "SUPERVISE_V53_TREND_BOS_DEMO.py"
WAIVER_DATE = date(2026, 8, 28)
MAX_STATUS_AGE_SECONDS = 180


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sup = load(SUPERVISOR, "v53_supervisor_for_timebox_waiver")


def as_int(s: dict[str, str], key: str) -> int:
    try:
        return int(s.get(key, "0") or 0)
    except ValueError as exc:
        raise RuntimeError(f"invalid integer status field {key}={s.get(key)!r}") from exc


def main() -> int:
    now = datetime.now()
    if now.date() < WAIVER_DATE:
        raise RuntimeError(
            f"V53 timebox waiver is not available before {WAIVER_DATE.isoformat()} local date; now={now.isoformat(timespec='seconds')}"
        )

    _, common, _, _ = sup.base.locate_mt5()
    v53 = common / "mt5_quant" / "v53"
    status = v53 / "V53_DEMO_REHEARSAL_STATUS.txt"
    final = v53 / "V53_DEMO_REHEARSAL_FINAL.txt"

    if final.is_file() and final.stat().st_size > 0:
        verdict = sup.kv(final).get("verdict", "FINAL")
        raise RuntimeError(f"EA FINAL already exists verdict={verdict}; do not apply a coordinator waiver")
    if not status.is_file():
        raise RuntimeError("V53 status file missing")

    age = time.time() - status.stat().st_mtime
    if age > MAX_STATUS_AGE_SECONDS:
        raise RuntimeError(f"V53 status is stale age_seconds={age:.1f} > {MAX_STATUS_AGE_SECONDS}")

    s = sup.kv(status)
    required_strings = {
        "account_mode": "DEMO",
        "real_money_authorized": "0",
    }
    for key, expected in required_strings.items():
        actual = s.get(key, "")
        if actual != expected:
            raise RuntimeError(f"waiver precondition failed {key} expected={expected} actual={actual}")

    checks_zero = (
        "round_trips",
        "requests",
        "rejects",
        "duplicate_events",
        "direction_mismatches",
        "open_pending",
        "close_pending",
        "halted",
        "owned_positions",
    )
    for key in checks_zero:
        if as_int(s, key) != 0:
            raise RuntimeError(f"waiver precondition failed {key}={s.get(key)}; expected 0")

    if as_int(s, "market_days") < 2:
        raise RuntimeError(f"waiver requires at least 2 market days; actual={s.get('market_days','0')}")
    if s.get("halt_reason", "").strip():
        raise RuntimeError(f"waiver precondition failed halt_reason={s.get('halt_reason')}")

    reason = "COORDINATOR_V53_NO_SIGNAL_TIMEBOX_WAIVER"
    zpath = sup.package(common, reason)
    print("V53_TIMEBOX_WAIVER_PASS=1")
    print(f"V53_TIMEBOX_LABEL=V53_NO_SIGNAL_TIMEBOX_WAIVER")
    print(f"STATUS_AGE_SECONDS={age:.1f}")
    print(f"MARKET_DAYS={s.get('market_days','0')}")
    print(f"ROUND_TRIPS={s.get('round_trips','0')}")
    print(f"REQUESTS={s.get('requests','0')}")
    print(f"V53_WAIVER_ZIP={zpath}")
    print(f"V53_WAIVER_ZIP_SHA256={sup.sha(zpath)}")
    print("NOTE=This closes the waiting gate; it is NOT DEMO_CONFIRMATION_PASS.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
