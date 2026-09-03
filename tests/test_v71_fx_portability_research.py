#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_v71_fx_portability_source.py"
ANALYZER = ROOT / "scripts" / "analyze_v71_fx_portability.py"
RUNTIME = ROOT / "runtime" / "v71_fx_portability_research" / "RUN_V71_FX_PORTABILITY_RESEARCH.py"
LAUNCHER = ROOT / "runtime" / "v71_fx_portability_research" / "RUN_V71_FX_PORTABILITY_RESEARCH_GIT_BASH.sh"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_builder_is_exact_v69_long_after_metadata_normalization() -> None:
    m = load(BUILDER, "v71_builder_test")
    text = m.transform()
    assert '#property version   "71.00"' in text
    assert "InpV64Magic = 710071" in text
    assert "InpV64AllowedDirection = 1" in text
    assert "InpV64AllowedDirection = -1" not in text
    assert "InpV64FixedLot = 0.01" in text
    assert "InpV64MinStopRiskCash = 0.85" in text
    assert "InpV64MaxStopRiskCash = 1.10" in text
    assert "InpV64PrimaryTargetCash = 3.50" in text
    assert "InpV69MinConfirmSeparationRiskCash = 1.30" in text
    assert m.normalize_to_v69(text) == m.parent.transform(1)


def test_runtime_uses_one_full_period_per_symbol_and_no_retune() -> None:
    src = RUNTIME.read_text(encoding="utf-8")
    assert 'EXPECTED_BRANCH = "agent/v71-fx-portability-research"' in src
    assert 'EXPECTED_HEAD_ENV = "V71_FX_EXPECTED_HEAD"' in src
    assert 'DEFAULT_SYMBOLS = ("XAUUSDm", "EURUSDm", "GBPUSDm", "USDJPYm", "AUDUSDm")' in src
    assert 'FROM_DATE = "2025.09.01"' in src
    assert 'TO_DATE = "2026.06.01"' in src
    assert 'EXPERT = "V71FxPortabilityLong"' in src
    assert 'REAL_MODEL = 4' in src
    assert "V71_FX_DIRECT_PORTABILITY_NO_RETUNE=1" in src
    assert "V71_FX_CASH_RISK_BAND_USD=0.85,1.10" in src
    assert "V71_FX_TARGET_CASH_USD=3.50" in src
    assert "V71_FX_SEPARATION_CASH_USD=1.30" in src
    assert "V71_SHORT_ENABLED=0" in src
    assert "REAL_MONEY_AUTHORIZED=0" in src
    assert "MetaTrader 5 must be closed for V71 cross-symbol tester research" in src
    assert 'V71_FX_EXPECTED_HEAD' in LAUNCHER.read_text(encoding="utf-8")


def test_analyzer_pairs_real_deal_schema_and_months() -> None:
    m = load(ANALYZER, "v71_analyzer_test")
    deals = [
        {"time": "2025.09.10 10:00:00", "entry": "0", "price": "1.1000", "profit": "0", "commission": "-0.02", "swap": "0", "fee": "0", "reason": "0"},
        {"time": "2025.09.10 10:00:45", "entry": "1", "price": "1.0990", "profit": "-1.00", "commission": "-0.02", "swap": "0", "fee": "0", "reason": "4"},
        {"time": "2025.10.12 11:00:00", "entry": "0", "price": "1.1100", "profit": "0", "commission": "0", "swap": "0", "fee": "0", "reason": "0"},
        {"time": "2025.10.12 11:03:00", "entry": "1", "price": "1.1130", "profit": "3.00", "commission": "0", "swap": "0", "fee": "0", "reason": "5"},
    ]
    trades = m.parse_trades(deals)
    assert len(trades) == 2
    assert abs(trades[0]["realized_pnl_usd"] + 1.04) < 1e-9
    assert trades[0]["duration_seconds"] == 45.0
    assert trades[0]["month"] == "2025-09"
    assert trades[1]["month"] == "2025-10"
    s = m.summarize([t["realized_pnl_usd"] for t in trades])
    assert s["trades"] == 2
    assert s["wins"] == 1
    assert s["losses"] == 1
    assert abs(s["net_usd"] - 1.96) < 1e-9


def test_analyzer_accepts_zero_trade_symbol_without_faking_edge() -> None:
    m = load(ANALYZER, "v71_zero_trade_test")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        (p / "V64_DEALS.csv").write_text("time,entry,price,profit,commission,swap,fee,reason\n", encoding="utf-8")
        (p / "V64_EVENTS.csv").write_text("time,event,detail,value1,value2,value3\n", encoding="utf-8")
        (p / "V64_ENTRY_EVAL.csv").write_text("time,reject_reason\n", encoding="utf-8")
        result = m.analyze_symbol("EURUSDm", p)
        assert result["trades"] == 0
        assert result["net_usd"] == 0.0
        assert result["profit_factor"] == 0.0
        assert result["fast_loss_share"] == 0.0


def test_no_short_or_real_activation_paths_added() -> None:
    for path in (BUILDER, ANALYZER, RUNTIME):
        src = path.read_text(encoding="utf-8")
        assert "REAL_MONEY_AUTHORIZED=1" not in src
    builder = BUILDER.read_text(encoding="utf-8")
    assert "parent.transform(1)" in builder
    assert "parent.transform(-1)" not in builder
    runtime = RUNTIME.read_text(encoding="utf-8")
    assert '.Sell(' not in runtime
    assert '.Buy(' not in runtime


def main() -> int:
    tests = [obj for name, obj in sorted(globals().items()) if name.startswith("test_") and callable(obj)]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V71 FX portability tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
