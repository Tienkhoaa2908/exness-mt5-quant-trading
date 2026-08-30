from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXED = ROOT / "runtime" / "v64_microstructure_trigger_shadow" / "RUN_V64_MICROSTRUCTURE_TRIGGER_SHADOW_FIXED.py"
LAUNCHER = ROOT / "runtime" / "v64_microstructure_trigger_shadow" / "START_V64_MICROSTRUCTURE_TRIGGER_SHADOW_GIT_BASH.sh"
BUILDER = ROOT / "scripts" / "build_v64_microstructure_trigger_shadow_source_fixed.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_fixed():
    return load(FIXED, "v64_locator_fixed")


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
    assert '"$PY" "$LOCATOR_TEST"' in text
    assert '-m pytest' not in text


def test_v64_fixed_runner_requires_canonical_api():
    text = FIXED.read_text(encoding="utf-8")
    assert 'getattr(base, "locate_mt5", None)' in text
    assert "base.find_mt5_data_dir = find_mt5_data_dir" in text
    assert "base.find_common_files_dir = find_common_files_dir" in text
    assert "V64_MT5_LOCATOR_COMPAT=PASS" in text


def test_v64_generated_mql_uses_supported_long_conversion():
    mod = load(BUILDER, "v64_builder_compile_portability")
    for direction in (-1, 1):
        text = mod.transform(direction)
        assert "IntegerToString(g_v64_noise[k].id)" in text
        assert "LongToString(" not in text


def test_v64_fixed_runner_fails_fast_with_compile_log():
    text = FIXED.read_text(encoding="utf-8")
    assert "install_compile_diagnostics" in text
    assert "V64_COMPILE_DIAGNOSTICS=ENABLED" in text
    assert "V64_COMPILE_FAIL expert=" in text
    assert "V64 METAEDITOR COMPILE LOG" in text
    assert "errors == 0 and warnings == 0" in text
    assert "runner.compile_source = compile_source" in text


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V64 locator/compile static tests PASS count={len(tests)}")
