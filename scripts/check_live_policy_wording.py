#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ADR/research documents are immutable historical evidence and may quote superseded policy.
# Operational policy wording is enforced only on active operator-facing documents.
ACTIVE_MARKDOWN = (
    Path("README.md"),
    Path("RECOVERY_CHECKPOINT.md"),
    Path("docs/handover/CURRENT_STATE.md"),
    Path("docs/handover/RECOVERY_PROMPT.md"),
    Path("docs/windows_mt5_exness_setup.md"),
)

FORBIDDEN_PATTERNS = [
    re.compile(r"real[- ]money\s+live\s+trading\s*(?:=|is|remains|still)?\s*forbidden", re.I),
    re.compile(r"\blive\s+(?:trading\s+)?(?:remains|is|still)\s+forbidden\b", re.I),
    re.compile(r"\blive\s+forbidden\b", re.I),
    re.compile(r"real[- ]money\s+live\s+trading\s+vẫn\s+cấm", re.I),
    re.compile(
        r"real[- ]money\s+order\s+execution\s+remains\s+outside\s+the\s+authorized\s+scope\s+of\s+this\s+project",
        re.I,
    ),
]


def main() -> int:
    hits: list[str] = []
    checked = 0
    for rel in ACTIVE_MARKDOWN:
        path = ROOT / rel
        if not path.is_file():
            continue
        checked += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            for rx in FORBIDDEN_PATTERNS:
                if rx.search(line):
                    hits.append(f"{rel}:{lineno}: {line.strip()}")
                    break

    if hits:
        print("LIVE_POLICY_WORDING_SCAN_FAIL")
        for hit in hits:
            print(hit)
        return 1

    print(f"LIVE_POLICY_WORDING_SCAN_PASS active_markdown_files={checked}")
    print("HISTORICAL_ADR_RESEARCH_EXEMPT=1")
    print("LIVE_RESEARCH_ALLOWED=1")
    print("LIVE_DEPLOYMENT_TARGET=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
