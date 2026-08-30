#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL_RUNNER = HERE / "RUN_V64_MICROSTRUCTURE_TRIGGER_SHADOW.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def install_mt5_locator_compat(base) -> None:
    """Bridge V64's stale locator names to the canonical V45 locate_mt5 API.

    The canonical helper returns (data, common, expert_dir, inputs). Cache the
    tuple so every compatibility lookup resolves the same MT5 installation.
    """
    locate = getattr(base, "locate_mt5", None)
    if not callable(locate):
        raise RuntimeError("V64 canonical MT5 locator missing: base.locate_mt5")

    cache: dict[str, tuple] = {}

    def located():
        if "value" not in cache:
            value = locate()
            if not isinstance(value, tuple) or len(value) != 4:
                raise RuntimeError(f"V64 locate_mt5 contract mismatch: {value!r}")
            cache["value"] = value
        return cache["value"]

    def find_mt5_data_dir():
        return located()[0]

    def find_common_files_dir(data):
        value = located()
        if Path(data) != Path(value[0]):
            raise RuntimeError(
                f"V64 MT5 data/common locator mismatch requested={data} canonical={value[0]}"
            )
        return value[1]

    base.find_mt5_data_dir = find_mt5_data_dir
    base.find_common_files_dir = find_common_files_dir


def install_compile_diagnostics(runner) -> None:
    """Replace V64 compile with a diagnostic 0/0 gate.

    MetaEditor commonly returns process rc=0 even when MQL compilation fails.
    Treat the compile log Result line as authoritative. If errors or warnings
    are reported, copy and print the log immediately instead of waiting for the
    EX5+0/0 timeout to expire.
    """

    base = runner.base

    def compile_source(source: Path, source_sha: str, data: Path, expert_dir: Path, expert_name: str) -> Path:
        expert_dir.mkdir(parents=True, exist_ok=True)
        installed = expert_dir / f"{expert_name}.mq5"
        ex5 = installed.with_suffix(".ex5")
        log = installed.with_suffix(".log")
        shutil.copy2(source, installed)
        for p in (ex5, log):
            try:
                p.unlink()
            except FileNotFoundError:
                pass

        if base.task_running("metaeditor64.exe"):
            raise RuntimeError("MetaEditor is open before V64 compile")

        cp = subprocess.run(
            [str(base.METAEDITOR_EXE), f"/compile:{installed}", f"/include:{data/'MQL5'}", "/log"]
        )
        print(f"V64_METAEDITOR_LAUNCH_RC expert={expert_name} rc={cp.returncode}")

        deadline = time.time() + 120.0
        last_summary = None
        compile_copy = runner.OUT / f"{expert_name}.compile.txt"

        while time.time() < deadline:
            if log.is_file() and log.stat().st_size > 0:
                summary = base.compile_summary(log)
                if summary:
                    last_summary = summary
                    m = re.search(
                        r"Result:\s*(\d+)\s+errors?,\s*(\d+)\s+warnings?",
                        summary,
                        flags=re.I,
                    )
                    if m:
                        errors = int(m.group(1))
                        warnings = int(m.group(2))
                        if errors == 0 and warnings == 0:
                            if ex5.is_file() and ex5.stat().st_size > 0:
                                compile_copy.write_text(base.decode_compile_log(log), encoding="utf-8")
                                print(
                                    f"V64_COMPILE_PASS expert={expert_name} summary={summary} "
                                    f"ex5_sha256={runner.sha(ex5)} source_sha256={source_sha}"
                                )
                                return compile_copy
                        else:
                            decoded = base.decode_compile_log(log)
                            compile_copy.write_text(decoded, encoding="utf-8")
                            print(
                                f"V64_COMPILE_FAIL expert={expert_name} summary={summary} "
                                f"diagnostics={compile_copy}"
                            )
                            print("===== V64 METAEDITOR COMPILE LOG =====")
                            print(decoded)
                            print("===== END V64 METAEDITOR COMPILE LOG =====")
                            raise RuntimeError(
                                f"V64 MetaEditor compile failed expert={expert_name} summary={summary}"
                            )
            time.sleep(0.25)

        if log.is_file() and log.stat().st_size > 0:
            decoded = base.decode_compile_log(log)
            compile_copy.write_text(decoded, encoding="utf-8")
            print(f"V64_COMPILE_TIMEOUT_LOG={compile_copy}")
            print("===== V64 METAEDITOR TIMEOUT LOG =====")
            print(decoded)
            print("===== END V64 METAEDITOR TIMEOUT LOG =====")

        raise RuntimeError(
            f"V64 compile timeout expert={expert_name} last_summary={last_summary!r} "
            f"ex5_exists={ex5.is_file()} log_exists={log.is_file()}"
        )

    runner.compile_source = compile_source


def main() -> int:
    runner = load(ORIGINAL_RUNNER, "v64_original_runner_fixed_locator")
    install_mt5_locator_compat(runner.base)
    install_compile_diagnostics(runner)

    # Warm the adapter once. The original V64 main then reuses this exact cached
    # installation through its stale helper names without rescanning APPDATA.
    data = runner.base.find_mt5_data_dir()
    common = runner.base.find_common_files_dir(data)
    expert_dir = Path(data) / "MQL5" / "Experts" / "mt5_quant"
    print(f"V64_MT5_LOCATOR_COMPAT=PASS data={data} common={common} expert_dir={expert_dir}")
    print("V64_COMPILE_DIAGNOSTICS=ENABLED")
    return runner.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}")
        raise
