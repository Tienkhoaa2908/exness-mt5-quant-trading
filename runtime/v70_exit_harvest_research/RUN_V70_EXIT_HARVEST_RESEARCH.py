#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

EXPECTED_BRANCH = "agent/v70-exit-harvest-research"
EXPECTED_HEAD_ENV = "V70_EXIT_HARVEST_EXPECTED_HEAD"
REANALYZE_ENV = "V70_REANALYZE_EXISTING"
EXPECTED_BASELINE_TRADES = 24
EXPECTED_BASELINE_WINS = 10
EXPECTED_BASELINE_LOSSES = 14
EXPECTED_BASELINE_NET_USD = 7.14
EXPECTED_BASELINE_NET_TOLERANCE_USD = 0.05
SYMBOL = "XAUUSDm"
PERIOD = "M15"
REAL_MODEL = 4
EXPERT = "V70ExitHarvestShadowLong"
REPLAY_MONTHS = [
    ("2025_09", "2025.09.01", "2025.10.01"),
    ("2025_10", "2025.10.01", "2025.11.01"),
    ("2025_11", "2025.11.01", "2025.12.01"),
    ("2025_12", "2025.12.01", "2026.01.01"),
    ("2026_01", "2026.01.01", "2026.02.01"),
    ("2026_02", "2026.02.01", "2026.03.01"),
    ("2026_03", "2026.03.01", "2026.04.01"),
    ("2026_04", "2026.04.01", "2026.05.01"),
    ("2026_05", "2026.05.01", "2026.06.01"),
]

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V70"
BUILDER = REPO / "scripts" / "build_v70_exit_harvest_shadow_source.py"
ANALYZER = REPO / "scripts" / "analyze_v70_exit_harvest_shadow.py"
STATIC_TEST = REPO / "tests" / "test_v70_exit_harvest_research.py"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"
V64_RUNNER = REPO / "runtime" / "v64_microstructure_trigger_shadow" / "RUN_V64_MICROSTRUCTURE_TRIGGER_SHADOW.py"
V64_FIXED = REPO / "runtime" / "v64_microstructure_trigger_shadow" / "RUN_V64_MICROSTRUCTURE_TRIGGER_SHADOW_FIXED.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(cmd, *, cwd=None, timeout=None) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run([str(x) for x in cmd], cwd=cwd, check=True, timeout=timeout)


def capture(cmd, *, cwd=None) -> str:
    return subprocess.check_output(
        [str(x) for x in cmd], cwd=cwd, text=True, encoding="utf-8", errors="replace"
    ).strip()


def ensure_repo() -> tuple[str, str]:
    branch = capture(["git", "branch", "--show-current"], cwd=REPO)
    head = capture(["git", "rev-parse", "HEAD"], cwd=REPO)
    dirty = capture(["git", "status", "--porcelain"], cwd=REPO)
    expected = (os.environ.get(EXPECTED_HEAD_ENV) or "").strip()
    print(f"BRANCH={branch}")
    print(f"HEAD={head}")
    print(f"EXPECTED_HEAD={expected}")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")
    if not expected:
        raise RuntimeError(f"{EXPECTED_HEAD_ENV} is required")
    if head != expected:
        raise RuntimeError(f"exact HEAD mismatch expected={expected} actual={head}")
    if dirty:
        raise RuntimeError("working tree must be clean before V70 research")
    return branch, head


def configure_runtime():
    runner = load(V64_RUNNER, "v64_runtime_reused_by_v70")
    fixed = load(V64_FIXED, "v64_fixed_helpers_for_v70")
    fixed.install_mt5_locator_compat(runner.base)
    fixed.install_compile_diagnostics(runner)
    runner.OUT = OUT
    runner.COMMON_DIR = "v70_exit_harvest_research"
    runner.DIRECTIONS = (("long", 1, EXPERT),)
    runner.EXPECTED_BRANCH = EXPECTED_BRANCH
    return runner


def build_source(runner) -> tuple[Path, str]:
    OUT.mkdir(parents=True, exist_ok=True)
    source = OUT / f"{EXPERT}.mq5"
    run([sys.executable, BUILDER, "--output", source])
    digest = runner.sha(source)
    print(f"V70_SOURCE_PASS expert={EXPERT} sha256={digest}")
    return source, digest


def analyze(run_dirs: list[Path]) -> tuple[Path, Path]:
    output = OUT / "v70_exit_harvest_analysis.json"
    summary = OUT / "V70_EXIT_HARVEST_SUMMARY.txt"
    cmd = [sys.executable, ANALYZER]
    for run_dir in run_dirs:
        cmd += ["--run-dir", run_dir]
    cmd += ["--output", output, "--summary", summary]
    run(cmd)
    return output, summary


def require_accepted_baseline(output: Path, *, emit: bool = True) -> dict:
    result = json.loads(output.read_text(encoding="utf-8"))
    legacy = result.get("legacy_accepted_identity") or {}
    economic = result.get("economic_roundtrip_actual") or result.get("actual") or {}
    trades = int(legacy.get("trades") or 0)
    wins = int(legacy.get("wins") or 0)
    losses = int(legacy.get("losses") or 0)
    legacy_net = float(legacy.get("net_usd") or 0.0)
    economic_net = float(economic.get("net_usd") or 0.0)
    if trades != EXPECTED_BASELINE_TRADES:
        raise RuntimeError(
            f"V70 baseline trade identity mismatch expected={EXPECTED_BASELINE_TRADES} actual={trades}"
        )
    if wins != EXPECTED_BASELINE_WINS or losses != EXPECTED_BASELINE_LOSSES:
        raise RuntimeError(
            "V70 baseline win/loss identity mismatch "
            f"expected={EXPECTED_BASELINE_WINS}W/{EXPECTED_BASELINE_LOSSES}L actual={wins}W/{losses}L"
        )
    if abs(legacy_net - EXPECTED_BASELINE_NET_USD) > EXPECTED_BASELINE_NET_TOLERANCE_USD:
        raise RuntimeError(
            "V70 legacy baseline net identity mismatch "
            f"expected={EXPECTED_BASELINE_NET_USD:.2f}+/-{EXPECTED_BASELINE_NET_TOLERANCE_USD:.2f} "
            f"actual={legacy_net:.8f}"
        )
    if emit:
        print(
            "V70_BASELINE_ACCEPTED_V69_IDENTITY=PASS "
            f"trades={trades} wins={wins} losses={losses} "
            f"legacy_net_usd={legacy_net:.8f} economic_roundtrip_net_usd={economic_net:.8f}"
        )
    return result


def require_shadow_integrity(result: dict, *, emit: bool = True) -> None:
    excursion = result.get("true_in_position_excursion") or {}
    trades = int(excursion.get("trades") or 0)
    mfe_all = float(excursion.get("median_true_mfe_all_usd") or 0.0)
    mfe_winners = float(excursion.get("median_true_mfe_winners_usd") or 0.0)
    mfe_ge_1 = int(excursion.get("true_mfe_ge_1_count") or 0)
    policy_changes = sum(
        int((result.get("policies") or {}).get(name, {}).get("changed_trade_count") or 0)
        for name in (
            "BASELINE_200_100",
            "EARLY_100_025",
            "MID_150_050",
            "TIERED_100_025_200_100",
        )
    )
    if trades <= 0:
        raise RuntimeError("V70 true excursion telemetry invalid: no matched trades")
    if mfe_all <= 1e-12 and mfe_winners <= 1e-12 and mfe_ge_1 == 0 and policy_changes == 0:
        raise RuntimeError(
            "V70 true excursion telemetry invalid: all-zero excursion/policy path; "
            "do not interpret POLICY_* economics"
        )
    if emit:
        print(
            "V70_TRUE_POSITION_LIFETIME_TELEMETRY=PASS "
            f"trades={trades} median_mfe_all={mfe_all:.8f} "
            f"median_mfe_winners={mfe_winners:.8f} mfe_ge_1={mfe_ge_1} "
            f"policy_changed_sum={policy_changes}"
        )


def existing_run_dirs() -> list[Path]:
    run_dirs: list[Path] = []
    for month, _, _ in REPLAY_MONTHS:
        run_dir = OUT / f"holdout_{month}_long"
        for filename in ("V64_DEALS.csv", "V64_EVENTS.csv"):
            path = run_dir / filename
            if not path.is_file() or path.stat().st_size <= 0:
                raise RuntimeError(f"V70 existing evidence missing or empty: {path}")
        events_text = (run_dir / "V64_EVENTS.csv").read_text(
            encoding="utf-8-sig", errors="replace"
        )
        if "V70_EXIT_SHADOW_START" not in events_text or "V70_EXIT_SHADOW_END" not in events_text:
            raise RuntimeError(f"V70 existing evidence lacks exit-shadow lifecycle: {run_dir}")
        run_dirs.append(run_dir)
    return run_dirs


def require_existing_source_identity() -> str:
    source = OUT / f"{EXPERT}.mq5"
    if not source.is_file() or source.stat().st_size <= 0:
        raise RuntimeError(f"V70 existing generated source missing: {source}")
    builder = load(BUILDER, "v70_builder_for_existing_evidence_identity")
    expected_bytes = builder.transform().encode("utf-8")
    expected_sha = hashlib.sha256(expected_bytes).hexdigest()
    actual_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual_sha != expected_sha:
        raise RuntimeError(
            "V70 existing evidence source identity mismatch "
            f"expected={expected_sha} actual={actual_sha}"
        )
    print(f"V70_EXISTING_EVIDENCE_SOURCE_IDENTITY=PASS sha256={actual_sha}")
    return actual_sha


def emit_final(head: str, output: Path, summary: Path, *, reanalyzed: bool) -> None:
    print(f"V70_EXIT_HARVEST_HEAD={head}")
    print(f"V70_EXIT_HARVEST_RESULT_JSON={output}")
    print(f"V70_EXIT_HARVEST_SUMMARY={summary}")
    print(f"V70_EXISTING_EVIDENCE_REANALYSIS={1 if reanalyzed else 0}")
    print("V70_BASELINE_ENTRY_SEMANTICS_CHANGED=0")
    print("V70_BASELINE_REAL_EXIT_SEMANTICS_CHANGED=0")
    print("V70_COUNTERFACTUAL_EXIT_SHADOW_ONLY=1")
    print("V70_DEVELOPMENT_ONLY=1")
    print("V70_SHORT_ENABLED=0")
    print("REAL_MONEY_AUTHORIZED=0")
    print("V70_EXIT_HARVEST_RESEARCH=PASS")


def main() -> int:
    _, head = ensure_repo()
    run([sys.executable, "-m", "py_compile", BUILDER, ANALYZER, STATIC_TEST, Path(__file__)])
    run([sys.executable, STATIC_TEST])
    run([sys.executable, SECRET_SCAN, REPO])

    reanalyze_existing = (os.environ.get(REANALYZE_ENV) or "").strip() == "1"
    if reanalyze_existing:
        require_existing_source_identity()
        run_dirs = existing_run_dirs()
        print(f"V70_EXISTING_EVIDENCE_MONTHS=PASS count={len(run_dirs)}")
        output, summary = analyze(run_dirs)
        result = require_accepted_baseline(output)
        require_shadow_integrity(result)
        emit_final(head, output, summary, reanalyzed=True)
        return 0

    runner = configure_runtime()
    data = runner.base.find_mt5_data_dir()
    common = runner.base.find_common_files_dir(data)
    expert_dir = Path(data) / "MQL5" / "Experts" / "mt5_quant"
    print(f"V70_MT5_LOCATOR_PASS data={data} common={common} expert_dir={expert_dir}")

    if runner.base.task_running("terminal64.exe"):
        raise RuntimeError("MetaTrader 5 must be closed for the one-pass V70 tester replay")
    if runner.base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor must be closed for the one-pass V70 tester replay")

    source, digest = build_source(runner)
    runner.compile_source(source, digest, data, expert_dir, EXPERT)

    run_dirs: list[Path] = []
    for month, from_date, to_date in REPLAY_MONTHS:
        label = f"holdout_{month}_long"
        root = runner.reset_common(common, label)
        ini = runner.write_config(data, EXPERT, from_date, to_date, label, REAL_MODEL)
        run_dirs.append(runner.run_terminal(root, ini, label, REAL_MODEL))

    output, summary = analyze(run_dirs)
    result = require_accepted_baseline(output)
    require_shadow_integrity(result)
    emit_final(head, output, summary, reanalyzed=False)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}")
        raise
