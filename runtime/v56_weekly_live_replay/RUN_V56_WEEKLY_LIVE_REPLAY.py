#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

EXPECTED_BRANCH = "agent/v54-production-readiness-hardening"
V48_SOURCE_SHA = "ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa"
ACCEPTED_V52R_ZIP_SHA256 = "4eddfce34c25b915e921a35e993f68f0a78644f3d6055bfa26180ba60ec9762c"
REPLAY_FROM = "2026.08.02"
REPLAY_TO = "2026.08.29"
WEEK_START = "2026.08.24"
WEEK_END_EXCLUSIVE = "2026.08.29"
EXPERT_NAME = "V56WeeklyLiveReplay"
CANDIDATE = "v52_b4_or_b3_trend_bos"
BOOK = "usd40_r1p0_cent_continuous"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "OUTPUT_V56"
CP = OUT / "checkpoint"
RUN_CP = CP / "run"
ZIP_OUT = OUT / "v56_weekly_real_tick_live_replay.zip"

V55_RUNNER = REPO / "runtime" / "v55_account_agnostic" / "RUN_V55_ACCOUNT_AGNOSTIC.py"
BUILDER = REPO / "scripts" / "build_v56_weekly_live_replay_source.py"
ANALYZER = REPO / "scripts" / "analyze_v56_weekly_live_replay.py"
STATIC_TEST = REPO / "tests" / "test_v56_weekly_live_replay_static.py"
SECRET_SCAN = REPO / "scripts" / "secret_scan.py"

V52R_STATE_PATH = "runtime/v52r_real_tick/OUTPUT_V52R/checkpoint/data/state_after_v52r.csv"
V52R_ZIP_PATH = "runtime/v52r_real_tick/OUTPUT_V52R/v52r_real_tick_repro.zip"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v55 = load(V55_RUNNER, "v55_base_for_v56_weekly_replay")
base = v55.base


def run(cmd, *, cwd=None):
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run([str(x) for x in cmd], cwd=cwd, check=True)


def capture(cmd, *, cwd=None) -> str:
    return subprocess.check_output(
        [str(x) for x in cmd], cwd=cwd, text=True, encoding="utf-8", errors="replace"
    ).strip()


def capture_bytes(cmd, *, cwd=None) -> bytes:
    return subprocess.check_output([str(x) for x in cmd], cwd=cwd)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return base.sha256(path)


def ensure_clean_repo() -> tuple[str, str]:
    branch = capture(["git", "branch", "--show-current"], cwd=REPO)
    head = capture(["git", "rev-parse", "HEAD"], cwd=REPO)
    dirty = capture(["git", "status", "--porcelain"], cwd=REPO)
    print(f"BRANCH={branch}")
    print(f"HEAD={head}")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"wrong branch expected={EXPECTED_BRANCH} actual={branch}")
    if dirty:
        raise RuntimeError("working tree must be clean before V56 replay")
    return branch, head


def recover_v52r_seed() -> tuple[Path, dict]:
    OUT.mkdir(parents=True, exist_ok=True)
    seed_out = OUT / "seed_state_from_accepted_v52r_20260801.csv"
    zip_probe = OUT / "accepted_v52r_zip_probe.zip"

    # First prefer a directly available historical output, but only if its companion ZIP
    # is the exact accepted V52R evidence package.
    direct_state = REPO / V52R_STATE_PATH
    direct_zip = REPO / V52R_ZIP_PATH
    if direct_state.is_file() and direct_zip.is_file() and sha(direct_zip) == ACCEPTED_V52R_ZIP_SHA256:
        shutil.copy2(direct_state, seed_out)
        provenance = {
            "source": "working_tree_ignored_output",
            "accepted_v52r_zip_sha256": ACCEPTED_V52R_ZIP_SHA256,
            "state_sha256": sha(seed_out),
            "state_path": V52R_STATE_PATH,
        }
        (OUT / "seed_provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
        print(f"V56_SEED_SOURCE=working_tree sha256={provenance['state_sha256']}")
        return seed_out, provenance

    # git stash --include-untracked stores untracked files in the third parent. The
    # previous safe-recovery step preserved V52R outputs there. Search every stash and
    # accept one only when the companion ZIP matches the frozen accepted V52R SHA.
    stash_lines = capture(["git", "stash", "list", "--format=%H"], cwd=REPO).splitlines()
    for stash_hash in stash_lines:
        stash_hash = stash_hash.strip()
        if not stash_hash:
            continue
        try:
            untracked = capture(["git", "rev-parse", f"{stash_hash}^3"], cwd=REPO)
            names = set(capture(["git", "ls-tree", "-r", "--name-only", untracked], cwd=REPO).splitlines())
        except subprocess.CalledProcessError:
            continue
        if V52R_STATE_PATH not in names or V52R_ZIP_PATH not in names:
            continue
        zip_bytes = capture_bytes(["git", "show", f"{untracked}:{V52R_ZIP_PATH}"], cwd=REPO)
        zip_sha = sha_bytes(zip_bytes)
        if zip_sha != ACCEPTED_V52R_ZIP_SHA256:
            print(f"V56_SKIP_STASH={stash_hash} v52r_zip_sha256={zip_sha}")
            continue
        state_bytes = capture_bytes(["git", "show", f"{untracked}:{V52R_STATE_PATH}"], cwd=REPO)
        if len(state_bytes) < 32:
            raise RuntimeError("accepted V52R stash state is unexpectedly empty")
        zip_probe.write_bytes(zip_bytes)
        seed_out.write_bytes(state_bytes)
        provenance = {
            "source": "git_stash_untracked_parent",
            "stash_commit": stash_hash,
            "untracked_parent": untracked,
            "accepted_v52r_zip_sha256": zip_sha,
            "state_sha256": sha(seed_out),
            "state_path": V52R_STATE_PATH,
        }
        (OUT / "seed_provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
        print(f"V56_SEED_SOURCE=stash stash={stash_hash} sha256={provenance['state_sha256']}")
        return seed_out, provenance

    raise RuntimeError(
        "cannot recover accepted V52R state_after_v52r.csv with matching accepted ZIP; "
        "refusing to replay with current/end-of-week state because that would introduce look-ahead"
    )


def build_source(expert_dir: Path) -> tuple[Path, str]:
    v46 = v55.v54.v48.accepted_v46_source(expert_dir)
    parent = v55.v54.v48.build_source(v46)
    parent_sha = sha(parent)
    if parent_sha != V48_SOURCE_SHA:
        raise RuntimeError(f"canonical V48 parent mismatch expected={V48_SOURCE_SHA} actual={parent_sha}")
    OUT.mkdir(parents=True, exist_ok=True)
    source = OUT / f"{EXPERT_NAME}.mq5"
    run([sys.executable, BUILDER, "--source", parent, "--output", source])
    source_sha = sha(source)
    print(f"V56_PARENT_V48_SHA256={parent_sha}")
    print(f"V56_SOURCE_SHA256={source_sha}")
    return source, source_sha


def compile_source(source: Path, source_sha: str, data: Path, expert_dir: Path) -> tuple[Path, Path, Path]:
    expert_dir.mkdir(parents=True, exist_ok=True)
    installed = expert_dir / f"{EXPERT_NAME}.mq5"
    ex5 = installed.with_suffix(".ex5")
    log = installed.with_suffix(".log")
    marker = installed.with_suffix(".compile_source_sha256")
    shutil.copy2(source, installed)
    for p in (ex5, log, marker):
        try:
            p.unlink()
        except FileNotFoundError:
            pass
    if base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor is open. Close it before V56 replay.")
    cp = subprocess.run(
        [str(base.METAEDITOR_EXE), f"/compile:{installed}", f"/include:{data/'MQL5'}", "/log"]
    )
    print(f"METAEDITOR_LAUNCH_RC={cp.returncode}")

    def ready() -> bool:
        if not ex5.is_file() or ex5.stat().st_size <= 0 or not log.is_file():
            return False
        summary = base.compile_summary(log)
        return bool(summary and "0 errors, 0 warnings" in summary.lower())

    base.wait_until(ready, 120, 0.5, "V56 MetaEditor 0/0 + EX5")
    marker.write_text(source_sha + "\n", encoding="utf-8")
    compile_copy = OUT / f"{EXPERT_NAME}.compile.txt"
    compile_copy.write_text(base.decode_compile_log(log), encoding="utf-8")
    print(f"V56_COMPILE_PASS summary={base.compile_summary(log)} ex5_sha256={sha(ex5)}")
    return installed, ex5, compile_copy


def prepare_common(common: Path, seed: Path) -> Path:
    root = common / "mt5_quant" / "v56_weekly_live_replay"
    root.parent.mkdir(parents=True, exist_ok=True)
    if root.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archived = root.parent / f"_v56_weekly_replay_previous_{stamp}"
        if archived.exists():
            shutil.rmtree(archived)
        root.rename(archived)
        print(f"V56_PREVIOUS_COMMON_ARCHIVED={archived}")
    root.mkdir(parents=True, exist_ok=True)
    dst = root / "seed_state.csv"
    shutil.copy2(seed, dst)
    if sha(dst) != sha(seed):
        raise RuntimeError("V56 seed copy mismatch")
    print(f"V56_COMMON_SEED_PASS sha256={sha(dst)} path={dst}")
    return root


def write_tester_config(data: Path) -> Path:
    ini = data / "config" / "v56_weekly_live_replay.ini"
    text = f"""[Common]\nKeepPrivate=1\nNewsEnable=0\n[Experts]\nAllowLiveTrading=1\nAllowDllImport=0\nEnabled=1\nAccount=0\nProfile=0\n[Tester]\nExpert=mt5_quant\\{EXPERT_NAME}.ex5\nSymbol=XAUUSDm\nPeriod=M15\nOptimization=0\nModel=4\nFromDate={REPLAY_FROM}\nToDate={REPLAY_TO}\nForwardMode=0\nDeposit=40\nCurrency=USD\nLeverage=1:200\nExecutionMode=0\nOptimizationCriterion=0\nUseCloud=0\nVisual=0\nShutdownTerminal=1\n"""
    base.write_utf16_ini(ini, text)
    decoded = ini.read_bytes().decode("utf-16")
    for token in (
        f"Expert=mt5_quant\\{EXPERT_NAME}.ex5",
        "Symbol=XAUUSDm",
        "Period=M15",
        "Optimization=0",
        "Model=4",
        f"FromDate={REPLAY_FROM}",
        f"ToDate={REPLAY_TO}",
        "Deposit=40",
        "Leverage=1:200",
        "AllowLiveTrading=1",
        "AllowDllImport=0",
        "ShutdownTerminal=1",
    ):
        if token not in decoded:
            raise RuntimeError(f"V56 tester config missing: {token}")
    shutil.copy2(ini, OUT / ini.name)
    print(f"V56_TESTER_CONFIG_PASS sha256={sha(ini)} path={ini}")
    print("V56_TESTER_MODEL=4")
    print("V56_REAL_TICKS=1")
    return ini


def newest_complete_run(runs_root: Path, started: float) -> Path | None:
    if not runs_root.is_dir():
        return None
    candidates: list[Path] = []
    for p in runs_root.iterdir():
        if not p.is_dir():
            continue
        req = [p / name for name in ("monthly_summary.csv", "trades.csv", "manifest.txt")]
        if not all(x.is_file() and x.stat().st_size > 0 for x in req):
            continue
        try:
            if max(x.stat().st_mtime for x in req) < started - 5:
                continue
        except OSError:
            continue
        candidates.append(p)
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def run_mt5(data: Path, common: Path, root: Path, ini: Path, head: str, source_sha: str) -> None:
    CP.mkdir(parents=True, exist_ok=True)
    mt5_done = CP / "MT5_DONE.json"
    if mt5_done.is_file() and RUN_CP.is_dir():
        info = json.loads(mt5_done.read_text(encoding="utf-8"))
        if (
            info.get("head") == head
            and info.get("source_sha256") == source_sha
            and info.get("model") == 4
            and info.get("from") == REPLAY_FROM
            and info.get("to") == REPLAY_TO
            and all((RUN_CP / n).is_file() for n in ("monthly_summary.csv", "trades.csv", "manifest.txt"))
        ):
            print("V56_REUSE_MT5_CHECKPOINT=1")
            return

    if base.task_running("terminal64.exe"):
        raise RuntimeError("MetaTrader 5 is open. Close the terminal before V56 Strategy Tester replay.")
    if base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor is open. Close it before V56 Strategy Tester replay.")

    if CP.exists():
        shutil.rmtree(CP)
    CP.mkdir(parents=True, exist_ok=True)

    started = time.time()
    print(f"RUN_V56_MT5_REAL_TICKS from={REPLAY_FROM} to={REPLAY_TO} analysis_week=2026.08.24..2026.08.28")
    cp = subprocess.run([str(base.TERMINAL_EXE), f"/config:{ini}"])
    print(f"MT5_LAUNCH_RC={cp.returncode}")

    runs_root = root / "runs"
    run_dir = newest_complete_run(runs_root, started)
    if run_dir is None:
        # Terminal can return before filesystem timestamps settle on Windows shares.
        def locate():
            return newest_complete_run(runs_root, started) or False
        run_dir = base.wait_until(locate, 120, 1.0, "V56 complete isolated run artifacts")

    RUN_CP.mkdir(parents=True, exist_ok=True)
    for name in ("monthly_summary.csv", "trades.csv", "manifest.txt"):
        shutil.copy2(run_dir / name, RUN_CP / name)

    artifact_map = {
        "V55_PRODUCTION_READINESS_EVENTS.csv": "events.csv",
        "V55_PRODUCTION_READINESS_TRANSACTIONS.csv": "transactions.csv",
        "V55_PRODUCTION_READINESS_STATUS.txt": "status.txt",
        "V55_PRODUCTION_READINESS_FINAL.txt": "final.txt",
        "seed_state.csv": "state_after_replay.csv",
    }
    for src_name, dst_name in artifact_map.items():
        src = root / src_name
        if src.is_file() and src.stat().st_size > 0:
            shutil.copy2(src, CP / dst_name)

    events = CP / "events.csv"
    status = CP / "status.txt"
    if not events.is_file() or events.stat().st_size <= 0:
        raise RuntimeError(f"V56 isolated broker/event evidence missing: {events}")
    if not status.is_file() or status.stat().st_size <= 0:
        raise RuntimeError(f"V56 isolated status missing: {status}")

    status_kv = v55.kv_retry(status)
    if status_kv.get("account_mode") != "DEMO":
        raise RuntimeError(
            f"V56 replay must mirror current trial environment expected account_mode=DEMO actual={status_kv.get('account_mode')}"
        )

    mt5_done.write_text(
        json.dumps(
            {
                "head": head,
                "source_sha256": source_sha,
                "terminal_rc": cp.returncode,
                "model": 4,
                "real_ticks": True,
                "from": REPLAY_FROM,
                "to": REPLAY_TO,
                "week_start": WEEK_START,
                "week_end_exclusive": WEEK_END_EXCLUSIVE,
                "run_dir": str(run_dir),
                "account_mode": status_kv.get("account_mode"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"V56_MT5_DONE=1 run_dir={run_dir}")


def analyze() -> dict:
    analysis = OUT / "v56_weekly_replay_analysis.json"
    summary = OUT / "V56_WEEKLY_REPLAY_SUMMARY.txt"
    run(
        [
            sys.executable,
            ANALYZER,
            "--trades",
            RUN_CP / "trades.csv",
            "--events",
            CP / "events.csv",
            "--status",
            CP / "status.txt",
            "--output",
            analysis,
            "--summary",
            summary,
        ]
    )
    return json.loads(analysis.read_text(encoding="utf-8"))


def package(branch: str, head: str, source_sha: str, compile_txt: Path, provenance: dict, result: dict) -> None:
    evidence = OUT / "V56_EVIDENCE.txt"
    evidence.write_text(
        "\n".join(
            [
                "V56_WEEKLY_REAL_TICK_LIVE_REPLAY=1",
                f"branch={branch}",
                f"head={head}",
                f"source_sha256={source_sha}",
                f"candidate={CANDIDATE}",
                f"book={BOOK}",
                f"replay_from={REPLAY_FROM}",
                f"replay_to={REPLAY_TO}",
                f"analysis_week_start={WEEK_START}",
                f"analysis_week_end_exclusive={WEEK_END_EXCLUSIVE}",
                "tester_model=4",
                "real_ticks=1",
                "deposit_usd=40",
                "leverage=1:200",
                "alpha_changed_from_v55=0",
                "execution_mapping_changed_from_v55=0",
                "tester_only=1",
                "live_orders_possible_from_v56=0",
                f"seed_source={provenance.get('source','')}",
                f"accepted_v52r_zip_sha256={provenance.get('accepted_v52r_zip_sha256','')}",
                f"seed_state_sha256={provenance.get('state_sha256','')}",
                f"verdict={result.get('verdict','')}",
                f"virtual_opens={result.get('events',{}).get('virtual_open_transitions')}",
                f"broker_open_requests={result.get('events',{}).get('broker_open_requests')}",
                f"rejected_open_requests={result.get('events',{}).get('rejected_open_requests')}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    bundle = OUT / "bundle"
    if bundle.exists():
        shutil.rmtree(bundle)
    bundle.mkdir(parents=True, exist_ok=True)

    files = [
        OUT / f"{EXPERT_NAME}.mq5",
        compile_txt,
        OUT / "v56_weekly_live_replay.ini",
        OUT / "seed_provenance.json",
        OUT / "v56_weekly_replay_analysis.json",
        OUT / "V56_WEEKLY_REPLAY_SUMMARY.txt",
        evidence,
        CP / "MT5_DONE.json",
        CP / "events.csv",
        CP / "transactions.csv",
        CP / "status.txt",
        CP / "final.txt",
        CP / "state_after_replay.csv",
        RUN_CP / "monthly_summary.csv",
        RUN_CP / "trades.csv",
        RUN_CP / "manifest.txt",
        BUILDER,
        ANALYZER,
        Path(__file__).resolve(),
        STATIC_TEST,
        REPO / "docs" / "adr" / "ADR-058-v56-weekly-real-tick-live-replay.md",
    ]
    used: set[str] = set()
    manifest_lines: list[str] = []
    for src in files:
        if not src.is_file():
            continue
        name = src.name
        if name in used:
            name = src.parent.name + "__" + name
        used.add(name)
        dst = bundle / name
        shutil.copy2(src, dst)
        manifest_lines.append(f"{sha(dst)}  {name}")

    manifest = bundle / "bundle_manifest_sha256.txt"
    manifest.write_text("\n".join(sorted(manifest_lines)) + "\n", encoding="utf-8")

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for p in sorted(bundle.iterdir()):
            if p.is_file():
                zf.write(p, p.name)
    with zipfile.ZipFile(ZIP_OUT) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"V56 ZIP CRC failure: {bad}")

    print(f"V56_WEEKLY_REPLAY_VERDICT={result.get('verdict','')}")
    print(f"V56_ZIP={ZIP_OUT}")
    print(f"V56_ZIP_SHA256={sha(ZIP_OUT)}")
    print("V56_PACKAGE_PASS=1")
    (CP / "DONE.txt").write_text(
        f"done=1\nhead={head}\nsource_sha256={source_sha}\nzip_sha256={sha(ZIP_OUT)}\n",
        encoding="utf-8",
    )


def main() -> int:
    branch, head = ensure_clean_repo()
    print("V56 PURPOSE: replay 24-28 Aug 2026 with MT5 Model=4 real ticks using V55 logic; no alpha retuning")
    run([sys.executable, "-m", "py_compile", BUILDER, ANALYZER, STATIC_TEST, Path(__file__).resolve()])
    run([sys.executable, STATIC_TEST])
    run([sys.executable, SECRET_SCAN, REPO])

    if base.task_running("terminal64.exe"):
        raise RuntimeError("MetaTrader 5 is open. Close it before V56 weekly Strategy Tester replay.")
    if base.task_running("metaeditor64.exe"):
        raise RuntimeError("MetaEditor is open. Close it before V56 weekly Strategy Tester replay.")

    data, common, expert_dir, _ = base.locate_mt5()
    print(f"MT5_DATA={data}")
    seed, provenance = recover_v52r_seed()
    source, source_sha = build_source(expert_dir)
    _, _, compile_txt = compile_source(source, source_sha, data, expert_dir)
    root = prepare_common(common, seed)
    ini = write_tester_config(data)
    run_mt5(data, common, root, ini, head, source_sha)
    result = analyze()
    package(branch, head, source_sha, compile_txt, provenance, result)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
