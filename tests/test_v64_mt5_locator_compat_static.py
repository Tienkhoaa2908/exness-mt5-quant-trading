from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXED = ROOT / "runtime" / "v64_microstructure_trigger_shadow" / "RUN_V64_MICROSTRUCTURE_TRIGGER_SHADOW_FIXED.py"
LAUNCHER = ROOT / "runtime" / "v64_microstructure_trigger_shadow" / "START_V64_MICROSTRUCTURE_TRIGGER_SHADOW_GIT_BASH.sh"


def load_fixed():
    spec = importlib.util.spec_from_file_location("v64_locator_fixed", FIXED)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_v64_locator_compat_maps_to_canonical_locate_mt5_once():
    mod = load_fixed()

    class FakeBase:
        def __init__(self):
            self.calls = 0

        def locate_mt5(self):
            self.calls += 1
            return (
                Path("C:/mt5/data"),
                Path("C:/mt5/common/Files"),
                Path("C:/mt5/data/MQL5/Experts/mt5_quant"),
                Path("C:/mt5/common/Files/mt5_quant/inputs"),
            )

    base = FakeBase()
    mod.install_mt5_locator_compat(base)
    data = base.find_mt5_data_dir()
    common = base.find_common_files_dir(data)
    assert data == Path("C:/mt5/data")
    assert common == Path("C:/mt5/common/Files")
    assert base.calls == 1


def test_v64_locator_compat_rejects_wrong_data_pairing():
    mod = load_fixed()

    class FakeBase:
        def locate_mt5(self):
            return (
                Path("C:/mt5/data"),
                Path("C:/mt5/common/Files"),
                Path("C:/mt5/data/MQL5/Experts/mt5_quant"),
                Path("C:/mt5/common/Files/mt5_quant/inputs"),
            )

    base = FakeBase()
    mod.install_mt5_locator_compat(base)
    try:
        base.find_common_files_dir(Path("D:/wrong"))
    except RuntimeError as exc:
        assert "data/common locator mismatch" in str(exc)
    else:
        raise AssertionError("expected V64 locator mismatch to fail")


def test_v64_launcher_uses_fixed_runner():
    text = LAUNCHER.read_text(encoding="utf-8")
    assert "RUN_V64_MICROSTRUCTURE_TRIGGER_SHADOW_FIXED.py" in text
    assert 'exec "$PY" "$RUNNER"' in text


def test_v64_fixed_runner_requires_canonical_api():
    text = FIXED.read_text(encoding="utf-8")
    assert 'getattr(base, "locate_mt5", None)' in text
    assert "base.find_mt5_data_dir = find_mt5_data_dir" in text
    assert "base.find_common_files_dir = find_common_files_dir" in text
    assert "V64_MT5_LOCATOR_COMPAT=PASS" in text
