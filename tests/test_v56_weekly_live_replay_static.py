from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILDER = REPO / "scripts" / "build_v56_weekly_live_replay_source.py"
ANALYZER = REPO / "scripts" / "analyze_v56_weekly_live_replay.py"
RUNNER = REPO / "runtime" / "v56_weekly_live_replay" / "RUN_V56_WEEKLY_LIVE_REPLAY.py"
LAUNCHER = REPO / "runtime" / "v56_weekly_live_replay" / "START_V56_WEEKLY_LIVE_REPLAY_GIT_BASH.sh"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def synthetic_v55() -> str:
    return r'''input bool InpV55PushNotifications = true;
input string InpAdaptiveStateFile = "mt5_quant\\paper\\v55_demo_rehearsal_state.csv";
input long InpV55Magic = 550055;
bool g_v55_real_entry_epoch_ready=false;
// v52_b4_or_b3_trend_bos V55NewRiskAuthorized V55StopsGeometryOk OrderCalcProfit OrderCalcMargin
string a="mt5_quant\\v55\\V55_PRODUCTION_READINESS_STATUS.txt";
string b="mt5_quant\\paper\\V48_DEMO_PAPER_STATUS.txt";
string c="mt5_quant\\runs\\";
void V55SyncBrokerWithVirtual()
{
   const int ci=26,bi=3,ix=BI(ci,bi);
   ulong ticket=0; int broker_dir=0; double broker_vol=0.0;
   int owned=V55OwnedPositionCount(ticket,broker_dir,broker_vol);
}
void V55WriteStatus()
{
   ulong ticket=0; int broker_dir=0; double broker_vol=0.0;
   int owned=V55OwnedPositionCount(ticket,broker_dir,broker_vol);
}
int OnInit()
{
   if(MQLInfoInteger(MQL_TESTER)){ V48WriteInitDiagnostic("REFUSED","tester_mode"); Print("V48 DEMO-PAPER refuses tester mode; use frozen V46 for historical tests"); return INIT_FAILED; }
   return INIT_SUCCEEDED;
}
'''


def test_v56_transform_is_tester_only_and_isolates_outputs():
    mod = load(BUILDER, "v56_builder_test")
    out = mod.transform_v55_to_v56(synthetic_v55())
    assert "if(!MQLInfoInteger(MQL_TESTER))" in out
    assert "v56_tester_only" in out
    assert "tester_mode" not in out
    assert 'input bool InpV55PushNotifications = false;' in out
    assert mod.V56_STATE_FILE in out
    assert r"mt5_quant\\v55\\" not in out
    assert r"mt5_quant\\v56_weekly_live_replay\\" in out
    assert "V56_VIRTUAL_OPEN" in out
    assert "V56_VIRTUAL_CLOSE" in out


def test_v56_instrumentation_only_changes_sync_function():
    mod = load(BUILDER, "v56_builder_scope_test")
    out = mod.transform_v55_to_v56(synthetic_v55())
    sync = out.split("void V55SyncBrokerWithVirtual()", 1)[1].split("void V55WriteStatus()", 1)[0]
    status = out.split("void V55WriteStatus()", 1)[1]
    assert "V56_VIRTUAL_OPEN" in sync
    assert "V56_VIRTUAL_OPEN" not in status
    assert status.count("int owned=V55OwnedPositionCount(ticket,broker_dir,broker_vol);") == 1


def test_v56_runner_uses_accepted_preweek_state_and_real_ticks():
    text = RUNNER.read_text(encoding="utf-8")
    assert 'ACCEPTED_V52R_ZIP_SHA256 = "4eddfce34c25b915e921a35e993f68f0a78644f3d6055bfa26180ba60ec9762c"' in text
    assert 'REPLAY_FROM = "2026.08.02"' in text
    assert 'REPLAY_TO = "2026.08.29"' in text
    assert 'WEEK_START = "2026.08.24"' in text
    assert "Model=4" in text
    assert "V56_REAL_TICKS=1" in text
    assert "state_after_v52r.csv" in text
    assert "look-ahead" in text
    assert "current/end-of-week state" in text
    assert "AllowLiveTrading=1" in text
    assert "AllowDllImport=0" in text


def test_v56_analyzer_classifies_alpha_vs_mapping():
    mod = load(ANALYZER, "v56_analyzer_test")
    assert mod.determine_verdict({"virtual_open_transitions": 0, "broker_open_requests": 0, "rejected_open_requests": 0}, {}) == "V56_WEEK_NO_SELECTED_CANDIDATE_ENTRY"
    assert mod.determine_verdict({"virtual_open_transitions": 2, "broker_open_requests": 0, "rejected_open_requests": 0}, {}) == "V56_WEEK_EXECUTION_MAPPING_BLOCKED"
    assert mod.determine_verdict({"virtual_open_transitions": 2, "broker_open_requests": 1, "rejected_open_requests": 0}, {}) == "V56_WEEK_PARTIAL_MAPPING"
    assert mod.determine_verdict({"virtual_open_transitions": 1, "broker_open_requests": 1, "rejected_open_requests": 1}, {}) == "V56_WEEK_BROKER_REJECTION_OBSERVED"
    assert mod.determine_verdict({"virtual_open_transitions": 1, "broker_open_requests": 1, "rejected_open_requests": 0}, {}) == "V56_WEEK_MAPPING_OBSERVED"
    assert mod.determine_verdict({"virtual_open_transitions": 0, "broker_open_requests": 0, "rejected_open_requests": 0}, {"halted": "1"}) == "V56_WEEK_RUNTIME_HALTED"


def test_v56_launcher_is_branch_locked():
    text = LAUNCHER.read_text(encoding="utf-8")
    assert 'EXPECTED_BRANCH="agent/v54-production-readiness-hardening"' in text
    assert "RUN_V56_WEEKLY_LIVE_REPLAY.py" in text
