#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYZER = ROOT / "scripts" / "analyze_v69_forward_trade_quality.py"


def load():
    spec = importlib.util.spec_from_file_location("v69_trade_quality", ANALYZER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def build_fixture(root: Path) -> None:
    deals = []
    specs = [
        ("2026.08.31 10:00:00", "2026.08.31 10:05:00", 1.20),
        ("2026.08.31 10:10:00", "2026.08.31 10:10:40", -1.00),
        ("2026.08.31 10:15:00", "2026.08.31 10:15:30", -0.90),
        ("2026.08.31 11:00:00", "2026.08.31 11:20:00", 2.50),
        ("2026.09.01 09:00:00", "2026.09.01 09:01:00", -1.00),
        ("2026.09.01 09:05:00", "2026.09.01 09:06:00", -0.80),
        ("2026.09.01 10:00:00", "2026.09.01 10:30:00", 3.20),
        ("2026.09.01 11:00:00", "2026.09.01 11:10:00", 1.10),
    ]
    for i, (start, end, pnl) in enumerate(specs):
        deals.append(
            {
                "time": start,
                "entry": 0,
                "profit": 0,
                "commission": -0.01,
                "swap": 0,
                "fee": 0,
                "reason": 0,
                "price": 3500 + i,
            }
        )
        deals.append(
            {
                "time": end,
                "entry": 1,
                "profit": pnl,
                "commission": -0.01,
                "swap": 0,
                "fee": 0,
                "reason": 4,
                "price": 3500 + i + 0.1,
            }
        )
    write_csv(
        root / "V64_DEALS.csv",
        ["time", "entry", "profit", "commission", "swap", "fee", "reason", "price"],
        deals,
    )

    noise_rows = []
    mfes = [2.5, 0.20, 0.10, 3.0, 0.15, 0.05, 3.5, 1.8]
    maes = [-0.3, -1.0, -0.9, -0.2, -1.0, -0.8, -0.2, -0.4]
    for i, (start, end, _) in enumerate(specs):
        noise_rows.append(
            {
                "id": i + 1,
                "started": start,
                "ended": end,
                "dir": 1,
                "entry": 3500 + i,
                "max_pnl": mfes[i],
                "min_pnl": maes[i],
                "reason": "time_expired",
            }
        )
    write_csv(
        root / "V64_NOISE_SHADOW.csv",
        ["id", "started", "ended", "dir", "entry", "max_pnl", "min_pnl", "reason"],
        noise_rows,
    )

    write_csv(
        root / "V64_EVENTS.csv",
        ["time", "event", "dir", "detail", "value1", "value2", "value3"],
        [
            {
                "time": "2026.08.31 10:02:00",
                "event": "PROFIT_LOCK",
                "dir": 1,
                "detail": "protected",
                "value1": 2.0,
                "value2": 1.0,
                "value3": 0,
            },
            {
                "time": "2026.08.31 10:00:00",
                "event": "POST_CONFIRM_ENTRY_READY",
                "dir": 1,
                "detail": "PULLBACK_SWEEP_BOS",
                "value1": 1,
                "value2": 30,
                "value3": 1.4,
            },
        ],
    )


def test_analyzer_reports_mfe_fast_loss_and_reentry_clusters() -> None:
    m = load()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        build_fixture(root)
        result = m.analyze(root)

    s = result["summary"]
    assert s["trades"] == 8
    assert s["wins"] == 4
    assert s["losses"] == 4
    assert s["noise_matched_trades"] == 8
    assert s["noise_match_rate"] == 1.0
    assert s["fast_losses"]["60"] == 4
    assert s["mfe_mae"]["median_mfe_losers_usd"] < 0.5
    assert s["reentry_clusters"]["15"]["loss_after_win"] >= 1
    assert s["reentry_clusters"]["15"]["loss_after_loss"] >= 1
    assert s["events"]["profit_lock_details"]["protected"] == 1
    assert result["diagnosis"]["priority"] == "ENTRY_STATE_AND_REENTRY_SUPPRESSION"
    assert result["read_only"] is True
    assert result["changes_strategy"] is False


def test_sub2_peak_roundtrip_loss_is_measured_not_tuned() -> None:
    m = load()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        build_fixture(root)
        result = m.analyze(root)

    q = result["summary"]["mfe_mae"]
    assert q["sub2_peak_roundtrip_loss_count"] == 4
    assert result["diagnosis"]["thresholds_are_diagnostic_not_strategy_parameters"] is True
    assert result["diagnosis"]["strategy_mutation_recommended_during_frozen_forward"] is False


def main() -> int:
    tests = [
        obj
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V69 forward trade-quality tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
