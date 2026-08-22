#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import shutil
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
V1_PATH = HERE / "RUN_V48_DEMO_PAPER_START_HARDENED.py"
EXPECTED_SEED_SHA = "36f68c8ce14ee657e1091d71e4c1702da907fcbd70c445b40f97852bf7288ee3"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v1 = load_module(V1_PATH, "v48_hardened_v1")
legacy = v1.legacy
_original_seed_paper_state = legacy.seed_paper_state
_original_launch_and_verify = v1.launch_and_verify


def _archive_paths(common: Path, label: str, paths: list[Path]) -> Path:
    root = common / "mt5_quant" / "paper"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive = root / f"_v48_{label}_{stamp}"
    archive.mkdir(parents=True, exist_ok=False)
    for src in paths:
        if src.exists():
            shutil.move(str(src), str(archive / src.name))
    return archive


def _kv(path: Path) -> dict[str, str]:
    return legacy.parse_kv(path)


def _is_failed_init_debris(common: Path) -> tuple[bool, str]:
    p = v1.paper_paths(common)
    latest = _kv(p["latest"])
    status = _kv(p["status"])
    init = _kv(p["init"])

    if latest.get("run_id", "").strip() or status.get("run_id", "").strip():
        return False, "non_empty_run_id"

    if not p["state"].is_file():
        return False, "state_missing"

    state_sha = v1.sha256(p["state"])
    if state_sha == EXPECTED_SEED_SHA:
        return False, "state_is_seed"

    # MQL5 calls OnDeinit(REASON_INITFAILED=8) after OnInit returns INIT_FAILED.
    # The V48 v2 MQL OnDeinit writes state/status/latest even though READY was
    # never reached. We only auto-recover that exact, fully evidenced pattern.
    recoverable = (
        init.get("stage") == "STOPPED"
        and init.get("reason") == "8"
        and init.get("broker_orders") == "0"
        and init.get("live_authorized") == "0"
        and init.get("symbol") == "XAUUSDm"
        and init.get("period") in {"PERIOD_M15", "M15"}
    )
    return recoverable, f"state_sha={state_sha} init_stage={init.get('stage','')} reason={init.get('reason','')}"


def seed_paper_state_v2(common: Path) -> Path:
    p = v1.paper_paths(common)
    p["root"].mkdir(parents=True, exist_ok=True)

    recoverable, detail = _is_failed_init_debris(common)
    if recoverable:
        archive = _archive_paths(
            common,
            "failed_init_reason8",
            [p["latest"], p["status"], p["init"], p["state"], p["seed_meta"]],
        )
        print(f"V48_FAILED_INIT_DEBRIS_QUARANTINED={archive}")
        print(f"V48_FAILED_INIT_DEBRIS_EVIDENCE={detail}")
        print("V48_FAILED_INIT_RECOVERY_ALLOWED=1")

    elif p["state"].is_file() and v1.sha256(p["state"]) != EXPECTED_SEED_SHA:
        latest = _kv(p["latest"])
        status = _kv(p["status"])
        if not latest.get("run_id", "").strip() and not status.get("run_id", "").strip():
            raise RuntimeError(
                "non-seed V48 state without valid run_id is not a proven REASON_INITFAILED=8 artifact; "
                f"refusing automatic reset ({detail})"
            )

    state = _original_seed_paper_state(common)
    if v1.sha256(state) != EXPECTED_SEED_SHA:
        raise RuntimeError(
            "V48 fresh-session state must equal accepted V46 seed before launch; "
            f"actual={v1.sha256(state)} expected={EXPECTED_SEED_SHA}"
        )
    print("V48_FRESH_SESSION_SEED_PASS=1")
    return state


def write_startup_ini_v2(data: Path) -> Path:
    ini = data / "config" / "v48_demo_paper_forward_hardened_v2.ini"
    # Empirical 2026-08-22 evidence showed Enabled=1 left
    # TERMINAL_TRADE_ALLOWED=1 even with AllowLiveTrading=0. The platform docs
    # state that disabling Auto Trading prevents trading while Expert Advisors
    # can continue to run. Therefore V48 v2 starts with BOTH trading controls
    # disabled and proves the result inside OnInit.
    text = """[Common]\nKeepPrivate=1\nNewsEnable=0\n[Experts]\nAllowLiveTrading=0\nAllowDllImport=0\nEnabled=0\nAccount=0\nProfile=0\n[StartUp]\nExpert=V48DemoPaperObserver\nSymbol=XAUUSDm\nPeriod=M15\n"""
    legacy.base.write_utf16_ini(ini, text)
    decoded = ini.read_bytes().decode("utf-16")
    required = (
        "AllowLiveTrading=0",
        "AllowDllImport=0",
        "Enabled=0",
        "Expert=V48DemoPaperObserver",
        "Symbol=XAUUSDm",
        "Period=M15",
    )
    missing = [x for x in required if x not in decoded]
    if missing:
        raise RuntimeError(f"V48 v2 startup INI self-check failed missing={missing}")
    print(f"V48_V2_CONFIG_SHA256={v1.sha256(ini)}")
    print("V48_V2_CONFIG_SELF_CHECK_PASS=1")
    print("V48_V2_TERMINAL_AUTOTRADING_REQUESTED_OFF=1")
    return ini


def _rollback_failed_start(common: Path) -> None:
    p = v1.paper_paths(common)
    latest = _kv(p["latest"])
    status = _kv(p["status"])
    if latest.get("run_id", "").strip() or status.get("run_id", "").strip():
        print("V48_FAILED_START_ROLLBACK_SKIPPED_VALID_RUN_ID=1")
        return

    # Preserve every failed-start artifact, then restore the exact accepted seed.
    debris = [x for x in (p["latest"], p["status"], p["init"], p["state"], p["seed_meta"]) if x.exists()]
    if debris:
        archive = _archive_paths(common, "failed_start_rollback", debris)
        print(f"V48_FAILED_START_ARCHIVE={archive}")

    seed = legacy.accepted_v46_state()
    shutil.copy2(seed, p["state"])
    if v1.sha256(p["state"]) != EXPECTED_SEED_SHA:
        raise RuntimeError("failed-start rollback could not restore accepted V46 seed")
    print("V48_FAILED_START_STATE_ROLLBACK_PASS=1")
    print("V48_FAILED_START_ACCEPTED_SESSION_CREATED=0")


def launch_and_verify_v2(data: Path, common: Path) -> None:
    try:
        _original_launch_and_verify(data, common)
    except Exception:
        _rollback_failed_start(common)
        raise


def main() -> int:
    legacy.seed_paper_state = seed_paper_state_v2
    v1.write_startup_ini = write_startup_ini_v2
    v1.launch_and_verify = launch_and_verify_v2
    return v1.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
