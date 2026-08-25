#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
B=(ROOT/"scripts"/"build_v50_execution_probe_source.py").read_text(encoding="utf-8")
R=(ROOT/"runtime"/"v50_execution_probe"/"RUN_V50_EXECUTION_PROBE.py").read_text(encoding="utf-8")
S=(ROOT/"runtime"/"v50_execution_probe"/"SUPERVISE_V50_EXECUTION_PROBE.py").read_text(encoding="utf-8")
REC=(ROOT/"runtime"/"v50_execution_probe"/"RECOVER_V50_EXECUTION_PROBE.py").read_text(encoding="utf-8")
START=(ROOT/"runtime"/"v50_execution_probe"/"START_V50_EXECUTION_PROBE_GIT_BASH.sh").read_text(encoding="utf-8")
def test_alpha_not_relaxed():assert "Frozen breadth4 stays unchanged" in START and "breadth3" not in B
def test_demo_probe_separate_magic():assert "ACCOUNT_TRADE_MODE_DEMO" in B and "InpV50ProbeMagic = 500050" in B
def test_min_volume_margin_precheck():assert "SYMBOL_VOLUME_MIN" in B and "OrderCalcMargin" in B and "InpV50MaxMarginFraction = 0.80" in B
def test_protective_exit():assert "InpV50ProbeHoldSeconds = 45" in B and "InpV50ProtectiveDistancePoints = 1500" in B and "PositionClose" in B
def test_three_roundtrips():assert "InpV50ProbeTargetRoundTrips = 3" in B and "EXECUTION_PIPELINE_PASS" in B
def test_no_probe_strategy_overlap():assert "if(V50ProbeBusy()) return;" in B and "V49OwnedPositionCount" in B
def test_compile_before_transition():assert R.index("compile_v50(source,source_sha,data)")<R.index("close_v49_if_flat(common)")
def test_zip_manifest():assert "bundle_manifest_sha256.txt" in S and "LATEST_V50_ZIP.txt" in S and "bundle_manifest_sha256.txt" in REC
def test_status_reader_retries_windows_share_locks():assert "except (PermissionError,OSError)" in R and "except (PermissionError,OSError)" in S and "read_bytes_retry" in REC
def test_recovery_does_not_start_or_trade():assert "TERMINAL_EXE" not in REC and "CTrade" not in REC and "V50_RECOVERY_PACKAGE_PASS=1" in REC
def run_all():
    fs=[v for k,v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for f in fs:f();print("PASS",f.__name__)
    print(f"V50 execution probe static tests PASS count={len(fs)}")
if __name__=="__main__":run_all()
