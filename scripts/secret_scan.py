#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SUFFIXES={'.py','.ps1','.cmd','.bat','.ini','.mq5','.mqh','.json','.yaml','.yml','.toml','.cfg','.conf'}
SKIP={'secret_scan.py'}
SKIP_DIRS={'.git','__pycache__','.pytest_cache','.venv','venv','site-packages','node_modules'}
PATTERNS={
 'tracked_login_ini':re.compile(r'(?im)^\s*Login\s*=\s*\d{5,}\s*$'),
 'tracked_login_ps':re.compile(r'''(?im)\$Login\s*=\s*["']?\d{5,}["']?'''),
 'tracked_login_arg':re.compile(r'(?i)(?:^|\s)-Login\s+\d{5,}(?:\s|$)'),
 'password_assignment':re.compile(r'''(?im)^\s*(?:password|passwd)\s*[:=]\s*["']?[^"'\s#;]{6,}'''),
 'token_assignment':re.compile(r'''(?im)^\s*(?:api[_-]?key|access[_-]?token|refresh[_-]?token|secret)\s*[:=]\s*["']?[^"'\s#;]{8,}'''),
}


def tracked_files(root: Path) -> list[Path] | None:
    """Return tracked working-tree files when root is a Git checkout.

    We intentionally read the working-tree copy of each tracked path so local
    edits are still scanned, while untracked runtime evidence, virtualenvs,
    package caches and generated outputs are not mistaken for repository
    secrets.
    """
    try:
        cp=subprocess.run(
            ['git','-C',str(root),'ls-files','-z'],
            check=True,capture_output=True,
        )
    except (FileNotFoundError,subprocess.CalledProcessError):
        return None
    rels=[x for x in cp.stdout.decode('utf-8','surrogateescape').split('\0') if x]
    return [root / rel for rel in rels]


def candidate_files(root: Path):
    tracked=tracked_files(root)
    if tracked is not None:
        for p in tracked:
            if p.is_file():
                yield p
        return
    for p in root.rglob('*'):
        if not p.is_file():
            continue
        try:
            rel=p.relative_to(root)
        except ValueError:
            continue
        if any(part in SKIP_DIRS or part.upper().startswith('OUTPUT_') for part in rel.parts[:-1]):
            continue
        yield p


def main():
    root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
    findings=[]
    scanned=0
    for p in candidate_files(root):
        if p.name in SKIP or p.suffix.lower() not in SUFFIXES:
            continue
        try:
            rel=p.relative_to(root)
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        try:
            text=p.read_text(encoding='utf-8-sig')
        except (UnicodeDecodeError,OSError):
            continue
        scanned += 1
        for name,pat in PATTERNS.items():
            for m in pat.finditer(text):
                findings.append((p,text.count('\n',0,m.start())+1,name))
    for p,line,name in findings:
        print(f'SECRET_SCAN_FAIL {name} {p}:{line}',file=sys.stderr)
    if findings:
        return 2
    print(f'SECRET_SCAN_PASS files={scanned} mode={"git-tracked" if tracked_files(root) is not None else "fallback"}')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
