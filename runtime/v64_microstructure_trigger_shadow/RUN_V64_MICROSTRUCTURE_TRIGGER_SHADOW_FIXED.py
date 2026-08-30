#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
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


def main() -> int:
    runner = load(ORIGINAL_RUNNER, "v64_original_runner_fixed_locator")
    install_mt5_locator_compat(runner.base)

    # Warm the adapter once. The original V64 main then reuses this exact cached
    # installation through its stale helper names without rescanning APPDATA.
    data = runner.base.find_mt5_data_dir()
    common = runner.base.find_common_files_dir(data)
    expert_dir = Path(data) / "MQL5" / "Experts" / "mt5_quant"
    print(f"V64_MT5_LOCATOR_COMPAT=PASS data={data} common={common} expert_dir={expert_dir}")
    return runner.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}")
        raise
