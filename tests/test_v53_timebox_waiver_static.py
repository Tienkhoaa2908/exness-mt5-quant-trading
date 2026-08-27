#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "runtime" / "v53_trend_bos_demo" / "CLOSE_V53_TIMEBOX_WAIVER.py"


def main() -> int:
    text = SCRIPT.read_text(encoding="utf-8")
    required = (
        "WAIVER_DATE = date(2026, 8, 28)",
        '"round_trips"',
        '"requests"',
        '"rejects"',
        '"duplicate_events"',
        '"direction_mismatches"',
        '"open_pending"',
        '"close_pending"',
        '"halted"',
        '"owned_positions"',
        '"account_mode": "DEMO"',
        '"real_money_authorized": "0"',
        "V53_NO_SIGNAL_TIMEBOX_WAIVER",
        "NOT DEMO_CONFIRMATION_PASS",
    )
    for token in required:
        assert token in text, token
    assert 'V53_TIMEBOX_LABEL=DEMO_CONFIRMATION_PASS' not in text
    assert "sup.package(common, reason)" in text
    print("V53 timebox waiver static PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
