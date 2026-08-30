from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILDER = REPO / "scripts" / "build_v62_direction_isolated_entry_refinement_source.py"
ANALYZER = REPO / "scripts" / "analyze_v62_direction_isolated_entry_refinement.py"
RUNNER = REPO / "runtime" / "v62_direction_isolated_entry_refinement" / "RUN_V62_DIRECTION_ISOLATED_ENTRY_REFINEMENT.py"
LAUNCHER = REPO / "runtime" / "v62_direction_isolated_entry_refinement" / "START_V62_DIRECTION_ISOLATED_ENTRY_REFINEMENT_GIT_BASH.sh"
ADR = REPO / "docs" / "adr" / "ADR-064-v62-direction-isolated-entry-refinement-research.md"
HANDOFF = REPO / "docs" / "handoff" / "V62_RECOVERY_STATE.md"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_builder_preserves_loss_first_contract_and_direction_isolation():
    mod = load(BUILDER, "v62_builder_contract_test")
    long_src = mod.transform(1)
    short_src = mod.transform(-1)
    for text in (long_src, short_src):
        for token in (
            "InpV62FixedLot = 0.01",
            "InpV62PrimaryTargetCash = 3.00",
            "InpV62ProfitArmCash = 2.00",
            "InpV62ProfitLockCash = 1.00",
            "InpV62MinStopRiskCash = 0.75",
            "InpV62MaxStopRiskCash = 1.25",
            "V62OrderPreflight",
            "V62ManageProfitRatchet",
            "PENDING_ARM",
            "REFINE_WAIT",
            "REFINED_ENTRY",
        ):
            assert token in text, token
    assert "InpV62AllowedDirection = 1" in long_src
    assert "InpV62AllowedDirection = -1" in short_src


def test_entry_refinement_is_closed_bar_m5_and_m1_and_not_fake_stop():
    mod = load(BUILDER, "v62_builder_causality_test")
    text = mod.transform(1)
    assert "CopyRates(_Symbol,PERIOD_M5,1,120,m5)" in text
    assert "CopyRates(_Symbol,PERIOD_M1,1,40,m1)" in text
    assert "m5_retest_m1_turn" in text
    assert "V62BuildStopTarget(d,g_v62_pending_features,entry" in text
    assert "InpV62PendingMaxMinutes = 240" in text
    assert "invalidated_before_entry" in text
    assert "V62RawM15Stop" in text


def test_pending_feature_state_is_declared_after_feature_struct():
    mod = load(BUILDER, "v62_builder_declaration_test")
    text = mod.transform(1)
    struct_end = text.index("   int short_score;\n};")
    pending = text.index("V62Features g_v62_pending_features;")
    assert pending > struct_end


def test_evaluate_bar_arms_instead_of_immediate_market_entry():
    mod = load(BUILDER, "v62_builder_arm_test")
    text = mod.transform(1)
    start = text.index("void V62EvaluateBar()")
    end = text.index("int OnInit()", start)
    body = text[start:end]
    assert "V62ArmPending(d,f,why);" in body
    assert "V62BuildStopTarget(" not in body
    assert "g_trade.Buy(" not in body
    assert "g_trade.Sell(" not in body


def test_runner_preregisters_four_weeks_and_eight_model4_passes():
    text = RUNNER.read_text(encoding="utf-8")
    for token in (
        '("week1", "2026.08.03", "2026.08.08")',
        '("week2", "2026.08.10", "2026.08.15")',
        '("week3", "2026.08.17", "2026.08.22")',
        '("week4", "2026.08.24", "2026.08.29")',
        '("long", 1, "V62DirectionIsolatedEntryRefinementLong")',
        '("short", -1, "V62DirectionIsolatedEntryRefinementShort")',
        "MODEL = 4",
        "V62_REAL_TICK_PASS_START",
        "V62_REAL_TICK_PASS_DONE",
    ):
        assert token in text, token
    assert "SCREEN_MODEL" not in text
    assert "select_directional_windows" not in text


def test_analyzer_counts_exit_round_trips_not_entry_deals():
    mod = load(ANALYZER, "v62_analyzer_test")
    deals = [
        {"entry": "0", "profit": "0", "commission": "0", "swap": "0", "fee": "0", "reason": "0"},
        {"entry": "1", "profit": "2.10", "commission": "0", "swap": "0", "fee": "0", "reason": "4"},
        {"entry": "0", "profit": "0", "commission": "0", "swap": "0", "fee": "0", "reason": "0"},
        {"entry": "1", "profit": "-0.90", "commission": "0", "swap": "0", "fee": "0", "reason": "5"},
    ]
    result = mod.actual_summary(deals)
    assert result["trades"] == 2
    assert result["wins"] == 1
    assert result["losses"] == 1
    assert abs(result["all_deal_net_usd"] - 1.20) < 1e-9


def test_launcher_is_portable_and_branch_pinned():
    text = LAUNCHER.read_text(encoding="utf-8")
    assert 'EXPECTED_BRANCH="agent/v62-direction-isolated-entry-refinement-research"' in text
    assert "py.exe" in text
    assert "python.exe" in text
    assert "set -Eeuo pipefail" in text
    assert "RUN_V62_DIRECTION_ISOLATED_ENTRY_REFINEMENT.py" in text


def test_adr_and_handoff_record_nonproduction_and_isolated_sum_caveat():
    adr = ADR.read_text(encoding="utf-8")
    handoff = HANDOFF.read_text(encoding="utf-8")
    for text in (adr, handoff):
        assert "0.01" in text
        assert "$0.75-$1.25" in text
        assert "SHORT" in text
        assert "REAL" in text
    assert "isolated-pass sum" in adr
    assert "not a concurrent" in adr
    assert "8-pass V62 evidence bundle" in handoff
    assert "total 8 passes" in handoff


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print(f"V62 static tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
