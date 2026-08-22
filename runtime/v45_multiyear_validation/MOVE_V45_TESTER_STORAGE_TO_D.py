#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

V30_SHA = "4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05"
TARGET_ROOT = Path(os.environ.get("V45_TESTER_STORAGE_ROOT", r"D:\MT5TesterCache"))
MIN_TARGET_FREE_GIB = 12.0
GIB = 1024 ** 3


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def task_running(image: str) -> bool:
    cp = subprocess.run(
        ["tasklist.exe", "/FI", f"IMAGENAME eq {image}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return image.lower() in cp.stdout.lower()


def gib(n: int) -> float:
    return n / GIB


def locate_terminal_data() -> Path:
    root = Path(os.environ["APPDATA"]) / "MetaQuotes" / "Terminal"
    matches = []
    for src in root.glob("*/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5"):
        try:
            if src.is_file() and sha256(src) == V30_SHA:
                matches.append(src)
        except OSError:
            pass
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one accepted V30 terminal data folder; matches={len(matches)}")
    return matches[0].parents[3]


def is_junction(path: Path) -> bool:
    fn = getattr(path, "is_junction", None)
    return bool(fn and fn())


def tree_signature(root: Path) -> tuple[int, int]:
    count = 0
    total = 0
    if not root.exists():
        return count, total
    for p in root.rglob("*"):
        try:
            if p.is_file():
                count += 1
                total += p.stat().st_size
        except OSError:
            pass
    return count, total


def copy_tree_with_robocopy(source: Path, target: Path) -> None:
    cp = subprocess.run(
        [
            "robocopy.exe",
            str(source),
            str(target),
            "/E",
            "/COPY:DAT",
            "/DCOPY:DAT",
            "/R:1",
            "/W:1",
            "/XJ",
            "/NFL",
            "/NDL",
            "/NP",
        ]
    )
    # Robocopy return codes 0..7 mean success / copied / differences handled.
    if cp.returncode > 7:
        raise RuntimeError(f"robocopy failed rc={cp.returncode}")


def make_junction(link: Path, target: Path) -> None:
    cp = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if cp.returncode != 0:
        raise RuntimeError(f"mklink /J failed rc={cp.returncode}: {cp.stdout} {cp.stderr}")


def main() -> int:
    print("=== V45 MOVE METATESTER STORAGE TO D ===")
    print("This does NOT launch MT5, MetaEditor, or Strategy Tester.")
    print("Only the local MetaTester storage is moved; terminal broker history/state/repo remain unchanged.")

    for image in ("terminal64.exe", "metaeditor64.exe", "metatester64.exe"):
        if task_running(image):
            raise RuntimeError(f"{image} is running. Close MT5/MetaEditor/MetaTester before migration.")

    data = locate_terminal_data()
    terminal_id = data.name
    appdata = Path(os.environ["APPDATA"])
    source = appdata / "MetaQuotes" / "Tester" / terminal_id
    target = TARGET_ROOT / terminal_id
    backup = source.with_name(source.name + ".v45_c_backup")

    target_drive = Path(TARGET_ROOT.drive + "\\") if TARGET_ROOT.drive else TARGET_ROOT
    if not target_drive.exists():
        raise RuntimeError(f"target drive/path does not exist: {target_drive}")

    free_target = shutil.disk_usage(target_drive).free
    print(f"SOURCE={source}")
    print(f"TARGET={target}")
    print(f"TARGET_FREE_GIB={gib(free_target):.2f}")
    if gib(free_target) < MIN_TARGET_FREE_GIB:
        raise RuntimeError(
            f"target volume needs at least {MIN_TARGET_FREE_GIB:.1f} GiB free; actual={gib(free_target):.2f} GiB"
        )

    if is_junction(source):
        resolved = source.resolve()
        if resolved != target.resolve():
            raise RuntimeError(f"tester storage is already a junction to another target: {resolved}")
        print("V45_TESTER_STORAGE_ON_D=1 already_migrated=1")
        print(f"TESTER_STORAGE_PHYSICAL={resolved}")
        return 0

    if backup.exists():
        raise RuntimeError(f"migration backup already exists; inspect before retrying: {backup}")

    if target.exists():
        marker = target / ".v45_managed_tester_storage"
        if not marker.is_file():
            if any(target.iterdir()):
                raise RuntimeError(f"target exists and is not V45-managed: {target}")
        else:
            shutil.rmtree(target)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir(parents=True, exist_ok=True)

    if source.exists():
        source_count, source_bytes = tree_signature(source)
        print(f"SOURCE_FILES={source_count}")
        print(f"SOURCE_GIB={gib(source_bytes):.3f}")
        copy_tree_with_robocopy(source, target)
        target_count, target_bytes = tree_signature(target)
        if target_count != source_count or target_bytes != source_bytes:
            raise RuntimeError(
                f"copy verification failed source=({source_count},{source_bytes}) target=({target_count},{target_bytes})"
            )
    else:
        source_count = source_bytes = 0

    (target / ".v45_managed_tester_storage").write_text(
        f"terminal_id={terminal_id}\nsource={source}\ntarget={target}\n",
        encoding="utf-8",
    )

    renamed = False
    try:
        if source.exists():
            source.rename(backup)
            renamed = True
        make_junction(source, target)
        if not is_junction(source):
            raise RuntimeError("junction verification failed: source is not a junction")
        if source.resolve() != target.resolve():
            raise RuntimeError(f"junction resolves to unexpected target: {source.resolve()}")
        if renamed:
            shutil.rmtree(backup)
    except Exception:
        try:
            if is_junction(source):
                source.rmdir()
        except Exception:
            pass
        if renamed and backup.exists() and not source.exists():
            backup.rename(source)
        raise

    free_c_after = shutil.disk_usage(data).free
    free_d_after = shutil.disk_usage(target).free
    print("V45_TESTER_STORAGE_ON_D=1 already_migrated=0")
    print(f"TESTER_STORAGE_PHYSICAL={target.resolve()}")
    print(f"C_FREE_AFTER_GIB={gib(free_c_after):.2f}")
    print(f"D_FREE_AFTER_GIB={gib(free_d_after):.2f}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
