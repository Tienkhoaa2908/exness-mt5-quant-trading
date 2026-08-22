#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Build the legacy phrases from fragments so this scanner does not match itself.
FORBIDDEN_PATTERNS = [
    re.compile(r"real[- ]money\s+live\s+trading\s*(?:=|is|remains|still)?\s*forbidden", re.I),
    re.compile(r"\blive\s+(?:trading\s+)?(?:remains|is|still)\s+forbidden\b", re.I),
    re.compile(r"\blive\s+forbidden\b", re.I),
    re.compile(r"real[- ]money\s+live\s+trading\s+vẫn\s+cấm", re.I),
    re.compile(r"real[- ]money\s+order\s+execution\s+remains\s+outside\s+the\s+authorized\s+scope\s+of\s+this\s+project", re.I),
]


def tracked_markdown() -> list[Path]:
    raw = subprocess.check_output(
        ["git", "ls-files", "-z", "*.md", "**/*.md"], cwd=ROOT
    )
    return [ROOT / p.decode("utf-8") for p in raw.split(b"\0") if p]


def main() -> int:
    hits: list[str] = []
    files = tracked_markdown()
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            for rx in FORBIDDEN_PATTERNS:
                if rx.search(line):
                    hits.append(f"{path.relative_to(ROOT)}:{lineno}: {line.strip()}")
                    break

    if hits:
        print("LIVE_POLICY_WORDING_SCAN_FAIL")
        for hit in hits:
            print(hit)
        return 1

    print(f"LIVE_POLICY_WORDING_SCAN_PASS markdown_files={len(files)}")
    print("LIVE_RESEARCH_ALLOWED=1")
    print("LIVE_DEPLOYMENT_TARGET=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
