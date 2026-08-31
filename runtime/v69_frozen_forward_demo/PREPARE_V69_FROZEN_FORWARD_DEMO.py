#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_BRANCH = "agent/v69-frozen-forward-demo-validation"
BASE_V69_RESEARCH_HEAD = "0569701be7846605ac01f94d8b5fc4ec2a6f8dd1"
V69_ACCEPTED_ZIP_SHA256 = "e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb"
EXPERT_NAME = "V69FrozenForwardDemoLong"
COMMON_DIR = "v69_frozen_forward_demo"
SYMBOL = "XAUUSDm"
PERIOD = "M15"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V69_FORWARD_PREP"
BUILDER = REPO / "scripts" / "build_v69_frozen_forward_demo_source.py"
STATIC_TEST = REPO / "tests" / "test_v69_frozen_forward_demo_static.py"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"
V69_RUNNER = REPO / "runtime" / "v69_confirm_separation_retest" / "RUN_V69_CONFIRM_SEPARATION_RETEST.py"
ADR = REPO / "docs" / "adr" / "ADR-072-v69-frozen-forward-demo-validation.md"
HANDOFF = REPO / "docs" / "handoff" / "V69_FORWARD_RECOVERY_STATE.md"
ZIP_OUT = OUT / "v69_frozen_forward_demo_preparation.zip"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def capture(cmd, *, cwd=None) -> str:
    return subprocess.check_output(
        [str(x) for x in cmd], cwd=cwd, text=True, encoding="utf-8", errors="replace"
    ).strip()


def run(cmd, *, cwd=None, timeout=None) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run([str(x) for x in cmd], cwd=cwd, check=True, timeout=timeout)


def ensure_repo() -> tuple[str, str, str]:
    expected_head = os.environ.get("V69_FORWARD_EXPECTED_HEAD", "").strip()
    if not expected_head:
        raise RuntimeError("V69_FORWARD_EXPECTED_HEAD is required; refusing unpinned preparation")

    origin = capture(["git", "remote", "get-url", "origin"], cwd=REPO)
    branch = capture(["git", "branch", "--show-current"], cwd=REPO)
    head = capture(["git", "rev-parse", "HEAD"], cwd=REPO)
    dirty = capture(["git", "status", "--porcelain"], cwd=REPO)

    print(f"ORIGIN={origin}")
    print(f"BRANCH={branch}")
    print(f"HEAD={head}")
    print(f"EXPECTED_HEAD={expected_head}")

    if "Tienkhoaa2908/exness-mt5-quant-trading" not in origin:
        raise RuntimeError(f"wrong repository origin={origin}")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")
    if head != expected_head:
        raise RuntimeError(f"wrong HEAD expected={expected_head} actual={head}")
    if dirty:
        raise RuntimeError("working tree must be clean; do not git clean or stash pop")
    return origin, branch, head


def configure_compile_runtime():
    v69 = load(V69_RUNNER, "v69_compile_helpers_for_forward")
    runner = v69.configure_runtime()
    runner.OUT = OUT
    return runner


def reset_forward_common(common: Path) -> tuple[Path, Path | None]:
    parent = common / "mt5_quant"
    parent.mkdir(parents=True, exist_ok=True)
    root = parent / COMMON_DIR
    archived = None
    if root.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%fZ")
        archived = parent / f"_v69_forward_previous_{stamp}"
        root.rename(archived)
        print(f"V69_FORWARD_PREVIOUS_COMMON_ARCHIVED={archived}")
    root.mkdir(parents=True, exist_ok=True)
    print(f"V69_FORWARD_COMMON_ROOT={root}")
    return root, archived


def package(runner, provenance: Path, source: Path, compile_log: Path) -> None:
    include = [source, compile_log, provenance, ADR, HANDOFF]
    include = [p for p in include if p.is_file()]

    manifest = OUT / "V69_FORWARD_PREP_MANIFEST_SHA256.txt"
    rows: list[str] = []
    for p in include:
        try:
            rel = p.relative_to(REPO)
        except ValueError:
            rel = Path("external") / p.name
        rows.append(f"{runner.sha(p)}  {rel.as_posix()}")
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")
    include.append(manifest)

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in include:
            try:
                arc = p.relative_to(REPO).as_posix()
            except ValueError:
                arc = f"external/{p.name}"
            zf.write(p, arc)
    with zipfile.ZipFile(ZIP_OUT) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"preparation ZIP CRC failure first_bad={bad}")

    print(f"V69_FORWARD_PREP_ZIP={ZIP_OUT}")
    print(f"V69_FORWARD_PREP_ZIP_SHA256={runner.sha(ZIP_OUT)}")


def main() -> int:
    origin, branch, head = ensure_repo()

    v69 = load(V69_RUNNER, "v69_process_helpers_for_forward")
    runner = v69.configure_runtime()
    if runner.base.task_running("terminal64.exe"):
        raise RuntimeError("MetaTrader 5 must be closed during forward preparation")
    if runner.base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor must be closed during forward preparation")

    OUT.mkdir(parents=True, exist_ok=True)
    run([sys.executable, "-m", "py_compile", BUILDER, STATIC_TEST, Path(__file__)])
    run([sys.executable, STATIC_TEST])
    run([sys.executable, SECRET_SCAN, REPO])

    runner.OUT = OUT
    data = runner.base.find_mt5_data_dir()
    common = runner.base.find_common_files_dir(data)
    expert_dir = Path(data) / "MQL5" / "Experts" / "mt5_quant"
    print(f"V69_FORWARD_MT5_DATA={data}")
    print(f"V69_FORWARD_MT5_COMMON={common}")
    print(f"V69_FORWARD_EXPERT_DIR={expert_dir}")

    source = OUT / f"{EXPERT_NAME}.mq5"
    run([sys.executable, BUILDER, "--output", source])
    source_sha = runner.sha(source)
    print(f"V69_FORWARD_SOURCE_SHA256={source_sha}")

    compile_log = runner.compile_source(source, source_sha, data, expert_dir, EXPERT_NAME)
    installed_source = expert_dir / f"{EXPERT_NAME}.mq5"
    installed_ex5 = expert_dir / f"{EXPERT_NAME}.ex5"
    if not installed_source.is_file() or runner.sha(installed_source) != source_sha:
        raise RuntimeError("installed MQ5 does not match generated source")
    if not installed_ex5.is_file() or installed_ex5.stat().st_size <= 0:
        raise RuntimeError("compiled EX5 missing or empty")
    ex5_sha = runner.sha(installed_ex5)

    common_root, archived = reset_forward_common(common)
    prepared_at = datetime.now(timezone.utc).isoformat()
    provenance = OUT / "V69_FORWARD_PREPARATION.json"
    provenance.write_text(json.dumps({
        "prepared_at_utc": prepared_at,
        "repository_origin": origin,
        "branch": branch,
        "head": head,
        "base_v69_research_head": BASE_V69_RESEARCH_HEAD,
        "accepted_v69_evidence_zip_sha256": V69_ACCEPTED_ZIP_SHA256,
        "expert_name": EXPERT_NAME,
        "symbol": SYMBOL,
        "period": PERIOD,
        "direction": "LONG_ONLY",
        "fixed_lot": 0.01,
        "planned_risk_band_cash": [0.85, 1.10],
        "emergency_loss_cash": 1.20,
        "target_cash": 3.50,
        "min_risk_spread_ratio": 4.0,
        "min_confirm_separation_risk_cash": 1.30,
        "min_confirm_age_seconds": 30,
        "demo_only": True,
        "real_money_authorized": False,
        "short_enabled": False,
        "source_sha256": source_sha,
        "ex5_sha256": ex5_sha,
        "installed_source": str(installed_source),
        "installed_ex5": str(installed_ex5),
        "file_common_root": str(common_root),
        "previous_common_archived": str(archived) if archived else None,
        "prospective_evidence_started": False,
        "prospective_evidence_start_rule": "starts only after this exact EA successfully initializes on an Exness DEMO XAUUSDm M15 chart",
        "strategy_threshold_tuning_allowed": False,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    package(runner, provenance, source, compile_log)

    print(f"V69_FORWARD_EX5_SHA256={ex5_sha}")
    print("V69_FORWARD_DIRECTION=LONG_ONLY")
    print("V69_FORWARD_DEMO_ONLY=1")
    print("V69_FORWARD_REAL_MONEY_AUTHORIZED=0")
    print("V69_FORWARD_SHORT_ENABLED=0")
    print("V69_FORWARD_PREPARED=1")
    print("V69_FORWARD_EVIDENCE_STARTED=0")
    print(f"V69_FORWARD_ATTACH_EXPERT={EXPERT_NAME}")
    print(f"V69_FORWARD_ATTACH_CHART={SYMBOL} {PERIOD}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}")
        raise
