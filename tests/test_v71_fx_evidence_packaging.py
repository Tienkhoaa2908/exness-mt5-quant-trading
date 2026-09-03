#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKER = ROOT / "scripts" / "package_v71_fx_evidence.py"
BUILDER = ROOT / "scripts" / "build_v71_fx_portability_source.py"
LAUNCHER = ROOT / "runtime" / "v71_fx_portability_research" / "PACK_V71_FX_EVIDENCE_GIT_BASH.sh"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_run(root: Path, label: str, trades: int) -> None:
    d = root / label
    d.mkdir(parents=True)
    rows = ["time,entry,price,profit,commission,swap,fee,reason"]
    for i in range(trades):
        rows.append(f"2025.09.{10+i:02d} 10:00:00,0,1.1000,0,0,0,0,0")
        rows.append(f"2025.09.{10+i:02d} 10:02:00,1,1.1010,1.00,0,0,0,5")
    (d / "V64_DEALS.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    (d / "V64_EVENTS.csv").write_text("time,event,detail,value1,value2,value3\n", encoding="utf-8")
    (d / "V64_ENTRY_EVAL.csv").write_text("time,reject_reason\n", encoding="utf-8")
    (d / "V64_STATUS.txt").write_text("PASS\n", encoding="utf-8")
    (d / "V64_NOISE_SHADOW.csv").write_text("id,max_pnl,min_pnl\n", encoding="utf-8")


def build_fixture(root: Path) -> None:
    builder = load(BUILDER, "v71_builder_for_packaging_fixture")
    (root / "V71FxPortabilityLong.mq5").write_text(builder.transform(), encoding="utf-8")
    (root / "V71FxPortabilityLong.compile.txt").write_text("Result: 0 errors, 0 warnings\n", encoding="utf-8")
    (root / "V71_FX_PORTABILITY_SUMMARY.txt").write_text("V71_FX_PORTABILITY_ANALYSIS=PASS\n", encoding="utf-8")
    payload = {
        "protocol": "v71_fx_portability_v1",
        "development_only_not_independent": True,
        "strategy_semantics": "V69 LONG exact after metadata normalization",
        "control_symbol": "XAUUSDm",
        "results": {
            "XAUUSDm": {"trades": 1},
            "EURUSDm": {"trades": 0},
            "GBPUSDm": {"trades": 1},
        },
        "short_enabled": False,
        "real_money_authorized": False,
    }
    (root / "v71_fx_portability_analysis.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    write_run(root, "fx_xauusdm_long", 1)
    write_run(root, "fx_eurusdm_long", 0)
    write_run(root, "fx_gbpusdm_long", 1)


def test_package_exports_full_core_and_per_symbol_archives() -> None:
    packer = load(PACKER, "v71_packer_test")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        build_fixture(out)
        result = packer.package_evidence(
            repo=ROOT,
            output_root=out,
            packaging_head="1" * 40,
            evidence_head="2" * 40,
        )
        assert set(result["symbols"]) == {"XAUUSDm", "EURUSDm", "GBPUSDm"}
        full = Path(result["full"]["path"])
        core = Path(result["core"]["path"])
        assert full.is_file() and core.is_file()
        assert len(result["symbol_packages"]) == 3
        with zipfile.ZipFile(full) as zf:
            names = set(zf.namelist())
            assert "V71_FX_EVIDENCE_MANIFEST.json" in names
            assert "fx_xauusdm_long/V64_ENTRY_EVAL.csv" in names
            assert "fx_eurusdm_long/V64_DEALS.csv" in names
            manifest = json.loads(zf.read("V71_FX_EVIDENCE_MANIFEST.json"))
            assert manifest["evidence_head"] == "2" * 40
            assert manifest["short_enabled"] is False
            assert manifest["real_money_authorized"] is False
        with zipfile.ZipFile(core) as zf:
            names = set(zf.namelist())
            assert "fx_xauusdm_long/V64_DEALS.csv" in names
            assert "fx_xauusdm_long/V64_EVENTS.csv" in names
            assert "fx_xauusdm_long/V64_ENTRY_EVAL.csv" not in names
        xau = Path(result["symbol_packages"]["XAUUSDm"]["path"])
        with zipfile.ZipFile(xau) as zf:
            names = set(zf.namelist())
            assert "fx_xauusdm_long/V64_DEALS.csv" in names
            assert not any(name.startswith("fx_gbpusdm_long/") for name in names)


def test_package_rejects_tampered_strategy_source() -> None:
    packer = load(PACKER, "v71_packer_tamper_test")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        build_fixture(out)
        source = out / "V71FxPortabilityLong.mq5"
        source.write_text(source.read_text(encoding="utf-8") + "// drift\n", encoding="utf-8")
        try:
            packer.package_evidence(
                repo=ROOT,
                output_root=out,
                packaging_head="1" * 40,
                evidence_head="2" * 40,
            )
        except RuntimeError as exc:
            assert "does not match current V71 builder" in str(exc)
        else:
            raise AssertionError("tampered V71 source unexpectedly packaged")


def test_pack_launcher_is_packaging_only_and_exact_head_pinned() -> None:
    src = LAUNCHER.read_text(encoding="utf-8")
    assert "V71_FX_EXPECTED_HEAD is required" in src
    assert "V71_FX_EVIDENCE_HEAD is required" in src
    assert "V71_FX_EVIDENCE_TESTER_RERUN=0" in src
    assert "V71_FX_EVIDENCE_MT5_CLOSE_REQUIRED=0" in src
    assert "RUN_V71_FX_PORTABILITY_RESEARCH.py" not in src
    assert "terminal64.exe" not in src
    assert "metaeditor64.exe" not in src


def main() -> int:
    tests = [obj for name, obj in sorted(globals().items()) if name.startswith("test_") and callable(obj)]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V71 FX evidence packaging tests PASS count={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
