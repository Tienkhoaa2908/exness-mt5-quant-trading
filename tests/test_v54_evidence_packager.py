from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path


def load(path: Path):
    spec = importlib.util.spec_from_file_location("v54_packager_tested", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_v54_packager_immutable_manifest(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    common = tmp_path / "common"
    out = tmp_path / "out"
    (repo / "runtime/v54_production_readiness/OUTPUT_V54").mkdir(parents=True)
    (repo / "scripts").mkdir(parents=True)
    (repo / "runtime/v54_production_readiness").mkdir(parents=True, exist_ok=True)
    (repo / "docs/adr").mkdir(parents=True)
    (repo / "docs/runbooks").mkdir(parents=True)
    (common / "mt5_quant/v54").mkdir(parents=True)

    required = {
        common / "mt5_quant/v54/V54_PRODUCTION_READINESS_STATUS.txt": "schema=v54\n",
        repo / "runtime/v54_production_readiness/OUTPUT_V54/V54ProductionReadiness.mq5": "// source\n",
        repo / "runtime/v54_production_readiness/OUTPUT_V54/V54ProductionReadiness.compile.txt": "0 errors, 0 warnings\n",
        repo / "scripts/build_v54_production_readiness_source.py": "# builder\n",
        repo / "runtime/v54_production_readiness/RUN_V54_PRODUCTION_READINESS.py": "# runner\n",
        repo / "runtime/v54_production_readiness/PACKAGE_V54_EVIDENCE.py": "# placeholder\n",
        repo / "docs/adr/ADR-056-v54-production-readiness-safety-envelope.md": "# adr\n",
        repo / "docs/runbooks/V54_PRODUCTION_READINESS_RUNBOOK.md": "# runbook\n",
    }
    for path, text in required.items():
        path.write_text(text, encoding="utf-8")

    module_path = Path(__file__).resolve().parents[1] / "runtime/v54_production_readiness/PACKAGE_V54_EVIDENCE.py"
    mod = load(module_path)
    z = mod.package(repo, common, out, "unit")
    assert z.is_file()
    with zipfile.ZipFile(z) as fh:
        assert fh.testzip() is None
        assert "SHA256SUMS.txt" in fh.namelist()
        assert "PROVENANCE.json" in fh.namelist()
        assert "runtime/V54_PRODUCTION_READINESS_STATUS.txt" in fh.namelist()
