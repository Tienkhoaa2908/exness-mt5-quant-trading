#!/usr/bin/env python3
from __future__ import annotations
import pathlib
import sys

REPLACEMENTS = {
    '  local src="$1" log="${src%.mq5}.log" ex5="${src%.mq5}.ex5"; rm -f "$log" "$ex5"':
        '  local src="$1"\n  local log="${src%.mq5}.log"\n  local ex5="${src%.mq5}.ex5"\n  rm -f "$log" "$ex5"',
    '  local expert="$1" tag="$2" ini="$DATA/config/v31_1_${tag}.ini" tmp="$OUT/.ini_utf8"':
        '  local expert="$1"\n  local tag="$2"\n  local ini="$DATA/config/v31_1_${tag}.ini"\n  local tmp="$OUT/.ini_utf8"',
    '  local tag="$1" dest="$CP/$tag"; [[ -s "$LATEST" ]] || die "LATEST locator missing after $tag"':
        '  local tag="$1"\n  local dest="$CP/$tag"\n  [[ -s "$LATEST" ]] || die "LATEST locator missing after $tag"',
    '  local tag="$1" bit="$2" dest="$CP/$tag"':
        '  local tag="$1"\n  local bit="$2"\n  local dest="$CP/$tag"',
    '  local ea="V31_1_ModelGateUsd40_${tag}" src="$EXPERT_DIR/${ea}.mq5"; cp -f "$BASE_SRC" "$src"':
        '  local ea="V31_1_ModelGateUsd40_${tag}"\n  local src="$EXPERT_DIR/${ea}.mq5"\n  cp -f "$BASE_SRC" "$src"',
}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch_v31_1_runner_locals.py RUNNER", file=sys.stderr)
        return 2
    p = pathlib.Path(sys.argv[1])
    s = p.read_text(encoding="utf-8")
    for old, new in REPLACEMENTS.items():
        n = s.count(old)
        if n != 1:
            raise RuntimeError(f"expected exactly one runner pattern, found {n}: {old}")
        s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8", newline="\n")
    # Fail closed if the known unsafe forms somehow remain.
    forbidden = [
        'local src="$1" log="${src%.mq5}.log"',
        'local expert="$1" tag="$2" ini=',
        'local tag="$1" dest="$CP/$tag"',
        'local tag="$1" bit="$2" dest="$CP/$tag"',
        'local ea="V31_1_ModelGateUsd40_${tag}" src=',
    ]
    bad = [x for x in forbidden if x in s]
    if bad:
        raise RuntimeError(f"unsafe local declaration(s) remain: {bad}")
    print(f"V31.1 runner local-declaration hotfix PASS: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
