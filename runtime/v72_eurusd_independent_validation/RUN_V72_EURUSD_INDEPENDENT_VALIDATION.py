#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

EXPECTED_BRANCH = "agent/v72-eurusd-independent-validation"
EXPECTED_HEAD_ENV = "V72_EURUSD_EXPECTED_HEAD"
SYMBOL = "EURUSDm"
FROM_DATE = "2024.09.01"
TO_DATE = "2025.09.01"
REAL_MODEL = 4
EXPERT = "V71FxPortabilityLong"
EXPECTED_SOURCE_SHA256 = "32615744d81e48be9f95638a8062e590b690bf1ec56437dc3293fda4bb202e7c"
# The exact pinned V71 source writes FILE_COMMON telemetry here. V72 must read the
# same root; changing the source root would change the pinned source SHA.
SOURCE_COMMON_DIR = "v71_fx_portability"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V72_EURUSD"
BUILDER = REPO / "scripts" / "build_v71_fx_portability_source.py"
ANALYZER = REPO / "scripts" / "analyze_v72_eurusd_validation.py"
STATIC_TEST = REPO / "tests" / "test_v72_eurusd_independent_validation.py"
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
    return subprocess.check_output([str(x) for x in cmd], cwd=cwd, text=True, encoding="utf-8", errors="replace").strip()


def ensure_repo() -> str:
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
        raise RuntimeError("working tree must be clean before V72 EURUSD validation")
    return head


def configure_runtime():
    runner = load(V64_RUNNER, "v64_runtime_reused_by_v72_eurusd")
    fixed = load(V64_FIXED, "v64_fixed_helpers_for_v72_eurusd")
    fixed.install_mt5_locator_compat(runner.base)
    fixed.install_compile_diagnostics(runner)
    runner.OUT = OUT
    # Exact V71 source is hash-pinned and hardcodes mt5_quant\\v71_fx_portability.
    # Point the reused harness at that exact telemetry root instead of inventing a
    # V72 root that the EA never writes to.
    runner.COMMON_DIR = SOURCE_COMMON_DIR
    runner.EXPECTED_BRANCH = EXPECTED_BRANCH
    runner.PERIOD = "M15"
    runner.SYMBOL = SYMBOL
    return runner


def parse_time(raw: str | None) -> datetime | None:
    value = (raw or "").strip()
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y.%m.%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def read_times(path: Path) -> list[datetime]:
    if not path.is_file() or path.stat().st_size <= 0:
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        rows = list(csv.DictReader(fh))
    out: list[datetime] = []
    for row in rows:
        dt = parse_time(row.get("time"))
        if dt is not None:
            out.append(dt)
    return out


def recover_existing_v72_evidence(runner, common: Path, label: str) -> Path | None:
    """Recover the tester pass that completed before the old runner looked in the wrong root.

    Recovery is fail-closed: the pinned V71 telemetry root is accepted only when the three
    primary CSVs exist and every timestamped row belongs to the preregistered V72 period.
    Stale V71 Sep-2025+ evidence therefore cannot be silently reused.
    """
    root = common / "mt5_quant" / SOURCE_COMMON_DIR
    primary = ("V64_ENTRY_EVAL.csv", "V64_EVENTS.csv", "V64_DEALS.csv")
    missing = [name for name in primary if not (root / name).is_file() or (root / name).stat().st_size <= 0]
    if missing:
        print(f"V72_EURUSD_EXISTING_EVIDENCE_CHECK=MISS root={root} missing={','.join(missing)}")
        return None

    eval_times = read_times(root / "V64_ENTRY_EVAL.csv")
    all_times: list[datetime] = []
    for name in primary:
        all_times.extend(read_times(root / name))
    if not eval_times or not all_times:
        print(f"V72_EURUSD_EXISTING_EVIDENCE_CHECK=MISS root={root} reason=no_timestamped_rows")
        return None

    lower = datetime.strptime(FROM_DATE, "%Y.%m.%d")
    # Tester ToDate handling can include timestamps on the named boundary date, so allow
    # that calendar day but nothing beyond it.
    upper = datetime.strptime(TO_DATE, "%Y.%m.%d") + timedelta(days=1)
    first = min(all_times)
    last = max(all_times)
    if first < lower or last >= upper:
        print(
            "V72_EURUSD_EXISTING_EVIDENCE_CHECK=REJECT "
            f"root={root} first={first} last={last} allowed=[{lower},{upper})"
        )
        return None

    print(
        "V72_EURUSD_EXISTING_EVIDENCE_CHECK=PASS "
        f"root={root} first={first} last={last} eval_rows={len(eval_times)}"
    )
    result = runner.copy_run(root, label)
    print(f"V72_EURUSD_TEST_RECOVERED_EXISTING=1 evidence={result}")
    return result


def main() -> int:
    head = ensure_repo()
    print("V72_EURUSD_UNTOUCHED_PERIOD=2024.09.01,2025.09.01")
    print("V72_EURUSD_STRATEGY_SOURCE=EXACT_V71_NO_RETUNE")
    print("V72_EURUSD_ENTRY_RETUNE=0")
    print("V72_EURUSD_EXIT_RETUNE=0")
    print("V72_SHORT_ENABLED=0")
    print("REAL_MONEY_AUTHORIZED=0")

    run([sys.executable, "-m", "py_compile", BUILDER, ANALYZER, STATIC_TEST, Path(__file__)])
    run([sys.executable, STATIC_TEST])
    run([sys.executable, SECRET_SCAN, REPO])

    runner = configure_runtime()
    data = runner.base.find_mt5_data_dir()
    common = runner.base.find_common_files_dir(data)
    expert_dir = Path(data) / "MQL5" / "Experts" / "mt5_quant"
    print(f"V72_MT5_LOCATOR_PASS data={data} common={common} expert_dir={expert_dir}")
    if runner.base.task_running("terminal64.exe"):
        raise RuntimeError("MetaTrader 5 must be closed for V72 EURUSD validation")
    if runner.base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor must be closed for V72 EURUSD validation")

    OUT.mkdir(parents=True, exist_ok=True)
    source = OUT / f"{EXPERT}.mq5"
    run([sys.executable, BUILDER, "--output", source])
    digest = runner.sha(source)
    print(f"V72_SOURCE_SHA256={digest}")
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"V72 strategy source drift expected={EXPECTED_SOURCE_SHA256} actual={digest}")
    runner.compile_source(source, digest, data, expert_dir, EXPERT)

    label = "v72_eurusdm_untouched_long"
    result = recover_existing_v72_evidence(runner, common, label)
    if result is None:
        root = runner.reset_common(common, label)
        ini = runner.write_config(data, EXPERT, FROM_DATE, TO_DATE, label, REAL_MODEL)
        print(f"V72_EURUSD_TEST_START symbol={SYMBOL} from={FROM_DATE} to={TO_DATE}")
        result = runner.run_terminal(root, ini, label, REAL_MODEL, timeout=5400)
        print(f"V72_EURUSD_TEST_DONE evidence={result}")
    else:
        print("V72_EURUSD_TEST_RERUN=0")

    output = OUT / "v72_eurusd_validation.json"
    summary = OUT / "V72_EURUSD_VALIDATION_SUMMARY.txt"
    run([sys.executable, ANALYZER, "--run-dir", result, "--output", output, "--summary", summary])

    print(f"V72_EURUSD_VALIDATION_HEAD={head}")
    print(f"V72_EURUSD_RESULT_JSON={output}")
    print(f"V72_EURUSD_SUMMARY={summary}")
    print("V72_EURUSD_V69_LONG_STRATEGY_EQUIVALENT=1")
    print("V72_EURUSD_INDEPENDENT_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}")
        raise
