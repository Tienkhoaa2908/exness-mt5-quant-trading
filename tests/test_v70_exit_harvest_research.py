#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_v70_exit_harvest_shadow_source.py"
ANALYZER = ROOT / "scripts" / "analyze_v70_exit_harvest_shadow.py"
RUNTIME = ROOT / "runtime" / "v70_exit_harvest_research" / "RUN_V70_EXIT_HARVEST_RESEARCH.py"
LAUNCHER = ROOT / "runtime" / "v70_exit_harvest_research" / "RUN_V70_EXIT_HARVEST_RESEARCH_GIT_BASH.sh"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_builder_preserves_frozen_v69_entry_and_real_exit_contract() -> None:
    m = load(BUILDER, "v70_exit_builder_test")
    s = m.transform()
    assert '#property version   "70.00"' in s
    assert "InpV64Magic = 700070" in s
    assert "InpV64AllowedDirection = 1" in s
    assert "InpV64AllowedDirection = -1" not in s
    assert "InpV64FixedLot = 0.01" in s
    assert "InpV64PrimaryTargetCash = 3.50" in s
    assert "InpV64ProfitArmCash = 2.00" in s
    assert "InpV64ProfitLockCash = 1.00" in s
    assert "InpV69MinConfirmSeparationRiskCash = 1.30" in s
    assert "InpV69MinConfirmAgeSeconds = 30" in s
    assert m.V70_ROOT in s
    assert m.V69_ROOT not in s


def test_exit_shadow_is_observability_only_and_cannot_trade() -> None:
    m = load(BUILDER, "v70_exit_shadow_safety_test")
    helper = m.EXIT_SHADOW
    assert "V70_EXIT_POLICY_TRIGGER" in helper
    assert "BASELINE_200_100" in helper
    assert "EARLY_100_025" in helper
    assert "MID_150_050" in helper
    assert "TIERED_100_025_200_100" in helper
    assert "PositionClose" not in helper
    assert "PositionModify" not in helper
    assert ".Buy(" not in helper
    assert ".Sell(" not in helper


def test_analyzer_reads_real_v64_event_value_schema() -> None:
    m = load(ANALYZER, "v70_exit_analyzer_schema_test")
    events = [
        {
            "time": "2025.09.01 00:00:01",
            "event": "V70_EXIT_SHADOW_START",
            "detail": "actual_position_lifetime",
            "value1": "3500",
            "value2": "1",
            "value3": "0",
        },
        {
            "time": "2025.09.01 00:00:03",
            "event": "V70_EXIT_POLICY_ARM",
            "detail": "EARLY_100_025",
            "value1": "1.10",
            "value2": "0.25",
            "value3": "1.10",
        },
        {
            "time": "2025.09.01 00:00:05",
            "event": "V70_EXIT_POLICY_TRIGGER",
            "detail": "EARLY_100_025",
            "value1": "0.20",
            "value2": "0.25",
            "value3": "1.20",
        },
        {
            "time": "2025.09.01 00:00:08",
            "event": "V70_EXIT_SHADOW_END",
            "detail": "actual_position_closed",
            "value1": "1.20",
            "value2": "-0.40",
            "value3": "7",
        },
    ]
    blocks = m.parse_shadow_blocks(events)
    assert len(blocks) == 1
    assert blocks[0]["entry_price"] == 3500.0
    assert blocks[0]["true_mfe_usd"] == 1.2
    assert blocks[0]["true_mae_usd"] == -0.4
    assert blocks[0]["shadow_duration_seconds"] == 7.0
    assert blocks[0]["triggers"]["EARLY_100_025"]["pnl"] == 0.2
    src = ANALYZER.read_text(encoding="utf-8")
    assert "V64_NOISE_SHADOW" not in src


def test_dual_accounting_separates_legacy_identity_from_roundtrip_economics() -> None:
    m = load(ANALYZER, "v70_exit_dual_accounting_test")
    deals = [
        {
            "time": "2025.09.01 00:00:01",
            "entry": "0",
            "profit": "0",
            "commission": "-0.10",
            "swap": "0",
            "fee": "0",
            "price": "3500",
        },
        {
            "time": "2025.09.01 00:01:01",
            "entry": "1",
            "profit": "1.00",
            "commission": "-0.05",
            "swap": "0",
            "fee": "0",
            "price": "3501",
        },
    ]
    legacy = m.legacy_accepted_summary(deals)
    economic = m.trade_quality.parse_deals(deals)
    assert legacy["trades"] == 1
    assert abs(legacy["net_usd"] - 0.95) < 1e-9
    assert len(economic) == 1
    assert abs(economic[0]["realized_pnl_usd"] - 0.85) < 1e-9
    assert abs(economic[0]["explicit_cost_usd"] + 0.15) < 1e-9


def test_runtime_gates_on_legacy_identity_not_economic_roundtrip_net() -> None:
    m = load(RUNTIME, "v70_exit_runtime_identity_test")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "analysis.json"
        good = {
            "legacy_accepted_identity": {"trades": 24, "wins": 10, "losses": 14, "net_usd": 7.14},
            "economic_roundtrip_actual": {"trades": 24, "wins": 10, "losses": 14, "net_usd": 6.44},
            "true_in_position_excursion": {
                "trades": 24,
                "median_true_mfe_all_usd": 0.5,
                "median_true_mfe_winners_usd": 1.5,
                "true_mfe_ge_1_count": 10,
            },
            "policies": {
                "BASELINE_200_100": {"changed_trade_count": 1},
                "EARLY_100_025": {"changed_trade_count": 2},
                "MID_150_050": {"changed_trade_count": 0},
                "TIERED_100_025_200_100": {"changed_trade_count": 2},
            },
        }
        p.write_text(json.dumps(good), encoding="utf-8")
        result = m.require_accepted_baseline(p, emit=False)
        assert result["legacy_accepted_identity"]["net_usd"] == 7.14
        assert result["economic_roundtrip_actual"]["net_usd"] == 6.44
        m.require_shadow_integrity(result, emit=False)

        bad_identity = dict(good)
        bad_identity["legacy_accepted_identity"] = {
            "trades": 24,
            "wins": 10,
            "losses": 14,
            "net_usd": 6.44,
        }
        p.write_text(json.dumps(bad_identity), encoding="utf-8")
        try:
            m.require_accepted_baseline(p, emit=False)
        except RuntimeError as exc:
            assert "legacy baseline net identity mismatch" in str(exc)
        else:
            raise AssertionError("legacy baseline identity guard must fail closed")

        zero_shadow = dict(good)
        zero_shadow["true_in_position_excursion"] = {
            "trades": 24,
            "median_true_mfe_all_usd": 0.0,
            "median_true_mfe_winners_usd": 0.0,
            "true_mfe_ge_1_count": 0,
        }
        zero_shadow["policies"] = {
            "BASELINE_200_100": {"changed_trade_count": 0},
            "EARLY_100_025": {"changed_trade_count": 0},
            "MID_150_050": {"changed_trade_count": 0},
            "TIERED_100_025_200_100": {"changed_trade_count": 0},
        }
        try:
            m.require_shadow_integrity(zero_shadow, emit=False)
        except RuntimeError as exc:
            assert "all-zero excursion/policy path" in str(exc)
        else:
            raise AssertionError("all-zero shadow telemetry must fail closed")


def test_existing_evidence_reanalysis_is_source_pinned_and_skips_tester() -> None:
    src = RUNTIME.read_text(encoding="utf-8")
    assert 'REANALYZE_ENV = "V70_REANALYZE_EXISTING"' in src
    assert "V70_EXISTING_EVIDENCE_SOURCE_IDENTITY=PASS" in src
    assert "V70_EXISTING_EVIDENCE_MONTHS=PASS" in src
    assert "V70_EXISTING_EVIDENCE_LIFECYCLE=PASS" in src
    assert "V70_EXISTING_EVIDENCE_REANALYSIS" in src
    assert "builder.transform()" in src
    assert '"V64_DEALS.csv", "V64_EVENTS.csv"' in src
    assert "analyzer.analyze_run(run_dir)" in src
    assert "events_text" not in src
    assert src.index("if reanalyze_existing:") < src.index("data = runner.base.find_mt5_data_dir()")


def test_existing_evidence_zero_trade_month_needs_zero_shadows_not_fake_lifecycle() -> None:
    m = load(RUNTIME, "v70_exit_runtime_zero_trade_month_test")
    old_out = m.OUT
    old_months = m.REPLAY_MONTHS
    try:
        with tempfile.TemporaryDirectory() as td:
            m.OUT = Path(td)
            m.REPLAY_MONTHS = [("zero", "2026.02.01", "2026.03.01")]
            run_dir = m.OUT / "holdout_zero_long"
            run_dir.mkdir(parents=True)
            (run_dir / "V64_DEALS.csv").write_text(
                "time,entry,profit,commission,swap,fee,price,reason\n",
                encoding="utf-8",
            )
            (run_dir / "V64_EVENTS.csv").write_text(
                "time,event,detail,value1,value2,value3\n",
                encoding="utf-8",
            )
            dirs = m.existing_run_dirs()
            assert dirs == [run_dir]

            m.REPLAY_MONTHS = [("trade", "2025.09.01", "2025.10.01")]
            traded = m.OUT / "holdout_trade_long"
            traded.mkdir(parents=True)
            (traded / "V64_DEALS.csv").write_text(
                "time,entry,profit,commission,swap,fee,price,reason\n"
                "2025.09.01 00:00:01,0,0,-0.10,0,0,3500,0\n"
                "2025.09.01 00:01:01,1,1.00,-0.05,0,0,3501,0\n",
                encoding="utf-8",
            )
            (traded / "V64_EVENTS.csv").write_text(
                "time,event,detail,value1,value2,value3\n",
                encoding="utf-8",
            )
            try:
                m.existing_run_dirs()
            except RuntimeError as exc:
                assert "trade/shadow integrity failure" in str(exc)
                assert "trade/shadow count mismatch trades=1 shadows=0" in str(exc)
            else:
                raise AssertionError("traded month without V70 lifecycle must fail closed")
    finally:
        m.OUT = old_out
        m.REPLAY_MONTHS = old_months


def test_runtime_is_exact_head_tester_only_long_only() -> None:
    src = RUNTIME.read_text(encoding="utf-8")
    sh = LAUNCHER.read_text(encoding="utf-8")
    assert 'EXPECTED_BRANCH = "agent/v70-exit-harvest-research"' in src
    assert 'EXPECTED_HEAD_ENV = "V70_EXIT_HARVEST_EXPECTED_HEAD"' in src
    assert 'EXPERT = "V70ExitHarvestShadowLong"' in src
    assert "EXPECTED_BASELINE_TRADES = 24" in src
    assert "EXPECTED_BASELINE_WINS = 10" in src
    assert "EXPECTED_BASELINE_LOSSES = 14" in src
    assert "EXPECTED_BASELINE_NET_USD = 7.14" in src
    assert "legacy_accepted_identity" in src
    assert "V70_BASELINE_ACCEPTED_V69_IDENTITY=PASS" in src
    assert "V70_TRUE_POSITION_LIFETIME_TELEMETRY=PASS" in src
    assert "MetaTrader 5 must be closed for the one-pass V70 tester replay" in src
    assert "REAL_MONEY_AUTHORIZED=0" in src
    assert "V70_SHORT_ENABLED=0" in src
    assert "V70_EXIT_HARVEST_EXPECTED_HEAD" in sh
    assert "REAL_MONEY_AUTHORIZED=0" in sh


def main() -> int:
    tests = [
        obj for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V70 exit-harvest research tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
