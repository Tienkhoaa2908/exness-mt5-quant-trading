from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]

def load(rel, name):
    p = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_v38_has_bounded_preregistered_fast_arms():
    a = load("scripts/analyze_v38_fast_harvest_mt5.py", "a38")
    assert a.CONTROL == "adaptive_ewma_hl8_thr0"
    assert a.FAST == [
        "v38_adaptive_fast_tp0p50",
        "v38_adaptive_fast_tp0p75",
        "v38_adaptive_fast_tp1p00",
        "v38_adaptive_fast_gb0p25_after0p75",
        "v38_adaptive_velocity_decay_after0p50",
        "v38_adaptive_timebox30m",
    ]
    assert len(a.FAST) == len(set(a.FAST)) == 6

def test_v38_builder_preserves_v34_and_tester_only_contract():
    text = (ROOT / "scripts/build_v38_fast_harvest_source.py").read_text(encoding="utf-8")
    assert "8bae2c56d43d11809ae96b5ee2f4bfe59007231ed5642bebe73dfbe2db7a7f10" in text
    assert '#define CANDIDATE_COUNT 23' in text
    assert "MQLInfoInteger(MQL_TESTER)" in text
    assert "V38FastExitTriggered" in text
    assert "intra_trade_m1_fast.csv" in text
    assert "BookRiskFraction" not in text
    assert "target=B[ix].balance" not in text

def test_v38_hard_stop_precedes_fast_exit():
    text = (ROOT / "scripts/build_v38_fast_harvest_source.py").read_text(encoding="utf-8")
    anchor = 'if(stopHit){ string rsn=MathAbs(B[ix].stop-B[ix].initial_stop)'
    fast = 'if(V38FastExitTriggered(ci,B[ix],tick,px,v38Reason))'
    assert anchor in text and fast in text
    assert text.index(anchor) < text.index(fast)

def _run_without_pytest():
    tests = [
        test_v38_has_bounded_preregistered_fast_arms,
        test_v38_builder_preserves_v34_and_tester_only_contract,
        test_v38_hard_stop_precedes_fast_exit,
    ]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V38 static tests PASS count={len(tests)}")

if __name__ == "__main__":
    _run_without_pytest()
