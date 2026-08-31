#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "runtime" / "v69_trade_quality_diagnostics" / "RUN_V69_TRADE_QUALITY_DIAGNOSTICS.py"


def load():
    spec = importlib.util.spec_from_file_location("v69_trade_quality_runtime", RUNNER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_live_snapshot_drops_partial_final_record() -> None:
    m = load()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        src = root / "live.csv"
        dst = root / "snapshot.csv"
        src.write_bytes(b"a,b\n1,2\n3,4\n5,")
        copied = m.snapshot_complete_lines(src, dst)
        assert copied > 0
        assert dst.read_bytes() == b"a,b\n1,2\n3,4\n"


def test_historical_discovery_is_long_only() -> None:
    m = load()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for name in (
            "holdout_2025_09_long",
            "holdout_2025_09_short",
            "holdout_2025_10_long",
            "random_long",
        ):
            p = root / name
            p.mkdir()
            (p / "V64_DEALS.csv").write_text("time,entry\n", encoding="utf-8")
        found = [p.name for p in m.discover_historical_long_runs(root)]
        assert found == ["holdout_2025_09_long", "holdout_2025_10_long"]


def test_runtime_is_read_only_and_never_launches_mt5() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert 'EXPECTED_BRANCH = "agent/v69-trade-quality-diagnostics"' in text
    assert 'OUTPUT_V69_TRADE_QUALITY' in text
    assert 'MT5_DEMO_CAN_REMAIN_RUNNING=1' in text
    forbidden = (
        "terminal64.exe",
        "metaeditor64.exe",
        "build_v69_frozen_forward_demo_source",
        "g_trade.Buy",
        "g_trade.Sell",
        "git clean",
        "stash pop",
    )
    for token in forbidden:
        assert token not in text


def test_empty_forward_snapshot_is_not_a_runtime_failure() -> None:
    m = load()
    analyzer = m.load(m.ANALYZER, "v69_trade_quality_test_analyzer")
    with tempfile.TemporaryDirectory() as td:
        result = analyzer.analyze(Path(td))
    assert result["summary"]["trades"] == 0
    assert result["diagnosis"]["priority"] == "INSUFFICIENT_SAMPLE"


def main() -> int:
    tests = [
        obj
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V69 trade-quality runtime tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
