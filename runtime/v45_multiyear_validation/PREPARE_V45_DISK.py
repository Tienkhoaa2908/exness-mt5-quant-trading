#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

V30_SHA = "4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05"
MIN_TERMINAL_FREE_GIB = 2.0
MIN_TESTER_FREE_GIB = 12.0
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


def dir_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for p in path.rglob("*"):
        try:
            if p.is_file():
                total += p.stat().st_size
        except OSError:
            pass
    return total


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


def remove_tree(path: Path) -> int:
    before = dir_size(path)
    if path.exists():
        shutil.rmtree(path)
    return before


def main() -> int:
    print("=== V45 DISK PREFLIGHT ===")
    print("This does NOT launch MT5 or MetaEditor.")
    print("It preserves terminal broker history, V45/V44 evidence, state, repo files, and compiled EAs.")
    for image in ("terminal64.exe", "metaeditor64.exe", "metatester64.exe"):
        if task_running(image):
            raise RuntimeError(f"{image} is running. Close MT5/MetaEditor/MetaTester before disk preflight.")

    data = locate_terminal_data()
    appdata = Path(os.environ["APPDATA"])
    terminal_id = data.name
    tester_root = appdata / "MetaQuotes" / "Tester" / terminal_id
    tester_physical = tester_root.resolve() if tester_root.exists() else tester_root

    terminal_free = shutil.disk_usage(data).free
    tester_free = shutil.disk_usage(tester_physical if tester_physical.exists() else data).free

    print(f"TERMINAL_DATA={data}")
    print(f"TESTER_ROOT={tester_root}")
    print(f"TESTER_STORAGE_PHYSICAL={tester_physical}")
    print(f"TERMINAL_FREE_GIB={gib(terminal_free):.2f}")
    print(f"TESTER_FREE_GIB={gib(tester_free):.2f}")
    print(f"MIN_TERMINAL_FREE_GIB={MIN_TERMINAL_FREE_GIB:.2f}")
    print(f"MIN_TESTER_FREE_GIB={MIN_TESTER_FREE_GIB:.2f}")

    # Clean only small terminal-side tester temp/cache when C: is critically low.
    reclaimed_estimate = 0
    if gib(terminal_free) < MIN_TERMINAL_FREE_GIB:
        terminal_tester_temp = data / "Tester" / "temp"
        if terminal_tester_temp.exists():
            sz = dir_size(terminal_tester_temp)
            print(f"TERMINAL_CACHE_TARGET size_gib={gib(sz):.3f} path={terminal_tester_temp}")
            reclaimed_estimate += remove_tree(terminal_tester_temp)

        cache_dir = data / "Tester" / "cache"
        if cache_dir.is_dir():
            for p in sorted(set(cache_dir.glob("*.tst")) | set(cache_dir.glob("*.opt"))):
                try:
                    sz = p.stat().st_size
                    print(f"TERMINAL_CACHE_FILE size_gib={gib(sz):.3f} path={p}")
                    p.unlink()
                    reclaimed_estimate += sz
                except FileNotFoundError:
                    pass
        terminal_free = shutil.disk_usage(data).free

    # If tester storage is still on the same full volume, safe-delete only its
    # recomputable agent history copies. Once storage is junctioned to D:, this
    # branch normally does nothing because D: has sufficient free space.
    same_volume = data.drive.lower() == tester_physical.drive.lower()
    if gib(tester_free) < MIN_TESTER_FREE_GIB and same_volume and tester_root.is_dir():
        for p in sorted(tester_root.glob("Agent-127.0.0.1-*/bases")):
            sz = dir_size(p)
            print(f"TESTER_CACHE_TARGET size_gib={gib(sz):.3f} path={p}")
            reclaimed_estimate += remove_tree(p)
        manager_temp = tester_root / "Manager" / "temp"
        if manager_temp.exists():
            sz = dir_size(manager_temp)
            print(f"TESTER_CACHE_TARGET size_gib={gib(sz):.3f} path={manager_temp}")
            reclaimed_estimate += remove_tree(manager_temp)
        tester_free = shutil.disk_usage(tester_physical if tester_physical.exists() else data).free
        terminal_free = shutil.disk_usage(data).free

    print(f"SAFE_CACHE_REMOVED_GIB={gib(reclaimed_estimate):.2f}")
    print(f"TERMINAL_FREE_AFTER_GIB={gib(terminal_free):.2f}")
    print(f"TESTER_FREE_AFTER_GIB={gib(tester_free):.2f}")

    if gib(terminal_free) < MIN_TERMINAL_FREE_GIB:
        need = MIN_TERMINAL_FREE_GIB - gib(terminal_free)
        raise RuntimeError(
            f"terminal volume needs {MIN_TERMINAL_FREE_GIB:.1f} GiB free for logs/config/temp; "
            f"actual={gib(terminal_free):.2f} GiB, free at least {need:.2f} GiB more on {data.drive}."
        )

    if gib(tester_free) < MIN_TESTER_FREE_GIB:
        need = MIN_TESTER_FREE_GIB - gib(tester_free)
        raise RuntimeError(
            f"MetaTester storage volume needs {MIN_TESTER_FREE_GIB:.1f} GiB free for the 2022-2026 tick run; "
            f"actual={gib(tester_free):.2f} GiB, free at least {need:.2f} GiB more on {tester_physical.drive or 'that volume'}."
        )

    print("V45_DISK_PREFLIGHT_PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
