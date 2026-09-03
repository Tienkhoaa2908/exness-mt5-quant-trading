#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

EXPECTED_BRANCH = "agent/v71-fx-portability-research"
EXPECTED_HEAD_ENV = "V71_FX_EXPECTED_HEAD"
SYMBOLS_ENV = "V71_FX_SYMBOLS"
DEFAULT_SYMBOLS = ("XAUUSDm", "EURUSDm", "GBPUSDm", "USDJPYm", "AUDUSDm")
CONTROL_SYMBOL = "XAUUSDm"
FROM_DATE = "2025.09.01"
TO_DATE = "2026.06.01"
REAL_MODEL = 4
EXPERT = "V71FxPortabilityLong"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V71_FX"
BUILDER = REPO / "scripts" / "build_v71_fx_portability_source.py"
ANALYZER = REPO / "scripts" / "analyze_v71_fx_portability.py"
STATIC_TEST = REPO / "tests" / "test_v71_fx_portability_research.py"
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
        raise RuntimeError("working tree must be clean before V71 FX research")
    return branch, head


def requested_symbols() -> tuple[str, ...]:
    raw = (os.environ.get(SYMBOLS_ENV) or "").strip()
    values = tuple(x.strip() for x in raw.split(",") if x.strip()) if raw else DEFAULT_SYMBOLS
    if CONTROL_SYMBOL not in values:
        values = (CONTROL_SYMBOL,) + values
    if len(values) < 3:
        raise RuntimeError("V71 FX research requires XAU control plus at least two FX symbols")
    if len(set(values)) != len(values):
        raise RuntimeError(f"V71 duplicate symbols: {values}")
    for symbol in values:
        if not re.fullmatch(r"[A-Za-z0-9._-]{3,24}", symbol):
            raise RuntimeError(f"V71 unsafe symbol token: {symbol!r}")
    return values


def configure_runtime():
    runner = load(V64_RUNNER, "v64_runtime_reused_by_v71_fx")
    fixed = load(V64_FIXED, "v64_fixed_helpers_for_v71_fx")
    fixed.install_mt5_locator_compat(runner.base)
    fixed.install_compile_diagnostics(runner)
    runner.OUT = OUT
    runner.COMMON_DIR = "v71_fx_portability"
    runner.EXPECTED_BRANCH = EXPECTED_BRANCH
    runner.PERIOD = "M15"
    return runner


def label_for(symbol: str) -> str:
    return "fx_" + re.sub(r"[^a-z0-9]+", "_", symbol.lower()).strip("_") + "_long"


def main() -> int:
    _, head = ensure_repo()
    symbols = requested_symbols()
    print("V71_FX_SYMBOLS=" + ",".join(symbols))
    print("V71_FX_DIRECT_PORTABILITY_NO_RETUNE=1")
    print("V71_FX_FIXED_LOT=0.01")
    print("V71_FX_CASH_RISK_BAND_USD=0.85,1.10")
    print("V71_FX_TARGET_CASH_USD=3.50")
    print("V71_FX_SEPARATION_CASH_USD=1.30")

    run([sys.executable, "-m", "py_compile", BUILDER, ANALYZER, STATIC_TEST, Path(__file__)])
    run([sys.executable, STATIC_TEST])
    run([sys.executable, SECRET_SCAN, REPO])

    runner = configure_runtime()
    data = runner.base.find_mt5_data_dir()
    common = runner.base.find_common_files_dir(data)
    expert_dir = Path(data) / "MQL5" / "Experts" / "mt5_quant"
    print(f"V71_MT5_LOCATOR_PASS data={data} common={common} expert_dir={expert_dir}")
    if runner.base.task_running("terminal64.exe"):
        raise RuntimeError("MetaTrader 5 must be closed for V71 cross-symbol tester research")
    if runner.base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor must be closed for V71 cross-symbol tester research")

    OUT.mkdir(parents=True, exist_ok=True)
    source = OUT / f"{EXPERT}.mq5"
    run([sys.executable, BUILDER, "--output", source])
    digest = runner.sha(source)
    print(f"V71_SOURCE_PASS expert={EXPERT} sha256={digest}")
    runner.compile_source(source, digest, data, expert_dir, EXPERT)

    run_dirs: list[tuple[str, Path]] = []
    for symbol in symbols:
        label = label_for(symbol)
        runner.SYMBOL = symbol
        root = runner.reset_common(common, label)
        ini = runner.write_config(data, EXPERT, FROM_DATE, TO_DATE, label, REAL_MODEL)
        print(f"V71_FX_TEST_START symbol={symbol} label={label} from={FROM_DATE} to={TO_DATE}")
        try:
            result = runner.run_terminal(root, ini, label, REAL_MODEL, timeout=5400)
        except Exception as exc:
            raise RuntimeError(f"V71 FX tester failed symbol={symbol}: {exc}") from exc
        print(f"V71_FX_TEST_DONE symbol={symbol} evidence={result}")
        run_dirs.append((symbol, result))

    output = OUT / "v71_fx_portability_analysis.json"
    summary = OUT / "V71_FX_PORTABILITY_SUMMARY.txt"
    cmd = [sys.executable, ANALYZER, "--control-symbol", CONTROL_SYMBOL, "--output", output, "--summary", summary]
    for symbol, path in run_dirs:
        cmd += ["--run", f"{symbol}={path}"]
    run(cmd)

    print(f"V71_FX_PORTABILITY_HEAD={head}")
    print(f"V71_FX_RESULT_JSON={output}")
    print(f"V71_FX_SUMMARY={summary}")
    print("V71_FX_V69_LONG_STRATEGY_EQUIVALENT=1")
    print("V71_FX_ENTRY_RETUNE=0")
    print("V71_FX_EXIT_RETUNE=0")
    print("V71_SHORT_ENABLED=0")
    print("REAL_MONEY_AUTHORIZED=0")
    print("V71_FX_PORTABILITY_RESEARCH=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}")
        raise
