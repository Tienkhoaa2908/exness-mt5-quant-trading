#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_v47_forward_regime_shadow_source.py"
AN = ROOT / "scripts" / "analyze_v47_shadow_regime_gates.py"
PLAN = ROOT / "docs" / "research" / "v47_forward_regime_shadow_plan.md"


def rt(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_v47_source_identity_is_frozen():
    t = rt(BUILD)
    assert 'EXPECTED_PARENT_SHA = "6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3"' in t
    assert 'EXPECTED_OUTPUT_SHA = "7685dd83f576841532970d43e21fda80c896c407f313edae1fb12b0b39387e44"' in t


def test_v47_only_repairs_observability_identity():
    t = rt(BUILD)
    assert 'candidate_count="+IntegerToString(CANDIDATE_COUNT)' in t
    assert 'source_file=V47ForwardRegimeShadowLab.mq5' in t
    assert 'v47_primary_logic_changed=0' in t
    assert 'v47_shadow_adx_di_only=1' in t
    assert 'v47_live_authorized=0' in t
    assert 'SetupAdaptiveBreadthRouter' not in t
    assert 'AdaptiveExpertScore' not in t


def test_shadow_analyzer_never_promotes():
    t = rt(AN)
    assert '"shadow_only": True' in t
    assert '"eligible_to_promote_from_this_analysis": False' in t
    assert 'entry_adx <= 30' in t
    assert 'entry_plus_di > entry_minus_di' in t
    assert 'entry_minus_di > entry_plus_di' in t


def test_plan_freezes_v46_breadth4_and_forbids_grid_search():
    t = rt(PLAN)
    assert 'require >=4 of 5 shadow experts healthy' in t
    assert 'Do not run a grid over:' in t
    assert 'No single short period can authorize promotion by itself.' in t
    assert 'REAL-MONEY' not in t or 'does not authorize real-money trading' in t


def _run_without_pytest():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn(); print("PASS", fn.__name__)
    print(f"V47 static tests PASS count={len(tests)}")


if __name__ == "__main__":
    _run_without_pytest()
