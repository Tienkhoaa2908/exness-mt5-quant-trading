#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "RUN_V45_MULTIYEAR_ONE_SHOT.py"


def load_base():
    spec = importlib.util.spec_from_file_location("v45_base_runner", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load base V45 runner: {BASE_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def replace_once(text: str, old: str, new: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V45 parent recovery expected exactly one marker, found={n}: {old[:120]!r}")
    return text.replace(old, new, 1)


def recover_parent_from_installed_v45(base, expert_dir: Path) -> Path:
    installed = expert_dir / f"{base.EXPERT_NAME}.mq5"
    if not installed.is_file():
        raise RuntimeError(
            "accepted V38 ZIP is missing and installed V45 source is also missing; "
            f"expected installed source: {installed}"
        )
    installed_sha = base.sha256(installed)
    if installed_sha != base.V45_SOURCE_SHA:
        raise RuntimeError(
            "accepted V38 ZIP is missing and installed V45 source has wrong SHA: "
            f"expected={base.V45_SOURCE_SHA} actual={installed_sha} path={installed}"
        )

    text = installed.read_text(encoding="utf-8-sig")
    text = replace_once(
        text,
        '#define MT5Q_RELEASE_ID "v45_multiyear_single_run_validation_v1"',
        '#define MT5Q_RELEASE_ID "v38_fast_harvest_lab_v1"',
    )
    text = replace_once(
        text,
        'input string InpOutputTag = "v45_multiyear_single_run_validation_v1";',
        'input string InpOutputTag = "v38_fast_harvest_lab_v1";',
    )
    text = replace_once(
        text,
        'input bool   InpV34WriteIntraTradeTelemetry = false;',
        'input bool   InpV34WriteIntraTradeTelemetry = true;',
    )
    text = replace_once(
        text,
        'input bool   InpV38WriteM1FastTelemetry = false;',
        'input bool   InpV38WriteM1FastTelemetry = true;',
    )

    marker = '   x+="v38_m1_fast_telemetry="+(InpV38WriteM1FastTelemetry?"1":"0")+"\\r\\n";'
    extra = (
        '   x+="v45_multiyear_validation=1\\r\\n";\n'
        '   x+="v45_strategy_logic_changed=0\\r\\n";\n'
        '   x+="v45_risk_changed=0\\r\\n";\n'
        '   x+="v45_candidate_focus=adaptive_ewma_hl8_thr0,adaptive_ewma_hl8_thr0p05,adaptive_ewma_hl10_thr0p05\\r\\n";\n'
        '   x+="v45_state_protocol=cold_start_no_2025_state\\r\\n";\n'
        '   x+="v45_default_from=2022.01.01\\r\\n";\n'
        '   x+="v45_default_to=2026.08.01\\r\\n";\n'
        '   x+="v45_warmup_months=6\\r\\n";\n'
        '   x+="v45_single_tester_run=1\\r\\n";\n'
        '   x+="v45_monthly_logging=1\\r\\n";\n'
        '   x+="v45_live_authorized=0\\r\\n";'
    )
    text = replace_once(text, marker + "\n" + extra, marker)
    text = text.replace("V45_MULTIYEAR_VALIDATION START", "V38_FAST_HARVEST_LAB START")
    text = text.replace("V45_MULTIYEAR_VALIDATION DONE", "V38_FAST_HARVEST_LAB DONE")

    out = base.OUT / "V38FastHarvestLab.accepted_parent.mq5"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8", newline="\r\n")
    recovered_sha = base.sha256(out)
    if recovered_sha != base.V38_PARENT_SOURCE_SHA:
        raise RuntimeError(
            "reverse recovery did not reproduce accepted V38 parent exactly: "
            f"expected={base.V38_PARENT_SOURCE_SHA} actual={recovered_sha}"
        )
    print(
        "Accepted V38 immutable parent RECOVERED FROM INSTALLED V45 PASS "
        f"sha256={recovered_sha}"
    )
    return out


def get_accepted_parent(base, expert_dir: Path) -> Path:
    if base.V38_ZIP.is_file():
        return base.extract_parent()
    print(f"Accepted V38 ZIP missing after clean clone: {base.V38_ZIP}")
    print("Using reversible installed-V45 recovery with exact parent SHA hard gate.")
    return recover_parent_from_installed_v45(base, expert_dir)


def main() -> int:
    base = load_base()
    base.OUT.mkdir(parents=True, exist_ok=True)
    base.CP.mkdir(parents=True, exist_ok=True)
    logf = base.LOG.open("a", encoding="utf-8", buffering=1)
    sys.stdout = base.Tee(sys.__stdout__, logf)
    sys.stderr = base.Tee(sys.__stderr__, logf)

    base.say("V45 MULTIYEAR SINGLE-RUN VALIDATION — EXACT MT5 / CLEAN-CLONE RECOVERY")
    print("One Strategy Tester invocation; monthly outputs are retained for later analysis.")
    print("REAL-MONEY LIVE TRADING remains FORBIDDEN. LIVE_AUTHORIZED=0.")

    required = (
        base.TERMINAL_EXE,
        base.METAEDITOR_EXE,
        base.BUILDER,
        base.ANALYZER,
        base.TEST,
        base.SECRET_SCAN,
        base.PACKAGER,
        base.BOOTSTRAP,
        base.PACKAGE_ONLY,
        BASE_PATH,
    )
    for p in required:
        if not p.is_file():
            raise RuntimeError(f"required file missing: {p}")

    head = base.capture(["git", "rev-parse", "HEAD"], cwd=base.REPO)
    branch = base.capture(["git", "branch", "--show-current"], cwd=base.REPO)
    print(f"HEAD={head}\nBRANCH={branch}")
    if branch != base.EXPECTED_BRANCH:
        raise RuntimeError(f"wrong branch expected={base.EXPECTED_BRANCH} actual={branch}")

    import numpy
    import pandas
    import sklearn

    assert numpy.__version__ == "2.3.5"
    assert pandas.__version__ == "2.2.3"
    assert sklearn.__version__ == "1.8.0"

    base.say("Static/recovery/secret gates before MetaEditor or MT5")
    base.run([
        sys.executable,
        "-m",
        "py_compile",
        base.BUILDER,
        base.ANALYZER,
        base.TEST,
        base.SECRET_SCAN,
        base.PACKAGER,
        BASE_PATH,
        Path(__file__).resolve(),
    ])
    base.run([sys.executable, base.TEST])
    base.run([sys.executable, base.SECRET_SCAN, base.REPO])

    data, common, expert_dir, inputs = base.locate_mt5()
    print(f"MT5_DATA={data}")
    base.verify_tape(inputs)
    parent = get_accepted_parent(base, expert_dir)
    source, source_sha = base.build_source(parent)
    installed, ex5, compile_txt = base.install_and_compile(source, source_sha, data, expert_dir)
    if not ex5.is_file() or ex5.stat().st_size == 0:
        raise RuntimeError("compiled EX5 missing")
    base.run_mt5_once(data, common, inputs)
    base.analyze_and_package(head, branch, source_sha, compile_txt)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
