#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v69_confirm_separation_retest_source.py"
V69_RESEARCH_ROOT = r"mt5_quant\\v69_confirm_separation_retest"
V69_FORWARD_ROOT = r"mt5_quant\\v69_frozen_forward_demo"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parent = load(PARENT, "v69_parent_for_frozen_forward_demo")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V69 forward {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


def replace_tester_guard_with_demo_guard(text: str) -> str:
    token_re = re.compile(r"MQLInfoInteger\s*\(\s*MQL_TESTER\s*\)")
    hits = list(token_re.finditer(text))
    if len(hits) != 1:
        raise RuntimeError(f"V69 forward tester token drifted expected=1 actual={len(hits)}")

    hit = hits[0]
    search_start = max(0, hit.start() - 300)
    prefix = text[search_start:hit.start()]
    if_matches = list(re.finditer(r"\bif\s*\(", prefix))
    if not if_matches:
        raise RuntimeError("V69 forward cannot locate tester if before MQL_TESTER")
    if_start = search_start + if_matches[-1].start()

    brace_open = text.find("{", hit.end())
    if brace_open < 0:
        raise RuntimeError("V69 forward tester guard opening brace missing")

    depth = 0
    brace_close = -1
    for pos in range(brace_open, len(text)):
        ch = text[pos]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                brace_close = pos
                break
    if brace_close < 0:
        raise RuntimeError("V69 forward tester guard closing brace missing")

    block = text[if_start:brace_close + 1]
    if "return INIT_FAILED;" not in block:
        raise RuntimeError("V69 forward tester guard is not an INIT_FAILED refusal")
    if "MQL_TESTER" not in block:
        raise RuntimeError("V69 forward parsed wrong guard block")

    line_start = text.rfind("\n", 0, if_start) + 1
    indent = text[line_start:if_start]
    if indent.strip():
        indent = "   "

    # Keep the forward adapter self-contained: do not call milestone-specific
    # diagnostics helpers that are not guaranteed to exist in the frozen V69 source.
    demo_guard = (
        f'{indent}if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO)'
        '{ Print("V69 FROZEN FORWARD REFUSED: DEMO ACCOUNT REQUIRED reason=v69_forward_demo_only"); '
        'return INIT_FAILED; }'
    )
    return text[:if_start] + demo_guard + text[brace_close + 1:]


def transform() -> str:
    # Strategy semantics come directly from the frozen V69 LONG builder.
    text = parent.transform(1)

    version_old = '#property version   "69.00"'
    version_new = (
        '#property version   "69.10"\n'
        '// Forward validation authorization is deliberately immutable and false.\n'
        'const bool V69ForwardRealMoneyAuthorized=false;'
    )
    text = replace_once(text, version_old, version_new, "version and authorization marker")
    text = replace_once(text, "input long   InpV64Magic = 690069;", "input long   InpV64Magic = 690169;", "magic")

    if V69_RESEARCH_ROOT not in text:
        raise RuntimeError("V69 forward inherited research FILE_COMMON root missing")
    text = text.replace(V69_RESEARCH_ROOT, V69_FORWARD_ROOT)
    text = text.replace("V69 SEP RETEST L", "V69 FORWARD DEMO L")

    # V57+ is tester-only. Change only that runtime refusal, by parsing the actual
    # guard structurally rather than depending on milestone-specific text/layout.
    text = replace_tester_guard_with_demo_guard(text)

    # Fail closed on every tick as well, so an account-mode change cannot reach an order path.
    on_tick = "void OnTick()\n{"
    guarded_tick = (
        "void OnTick()\n{\n"
        "   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO)\n"
        "   {\n"
        "      Print(\"V69 FROZEN FORWARD HALT: DEMO ACCOUNT REQUIRED\");\n"
        "      ExpertRemove();\n"
        "      return;\n"
        "   }"
    )
    text = replace_once(text, on_tick, guarded_tick, "per-tick demo guard")

    validate(text)
    return text


def validate(text: str) -> None:
    required = (
        '#property version   "69.10"',
        "const bool V69ForwardRealMoneyAuthorized=false;",
        V69_FORWARD_ROOT,
        "InpV64Magic = 690169",
        "InpV64AllowedDirection = 1",
        "InpV64FixedLot = 0.01",
        "InpV64MinStopRiskCash = 0.85",
        "InpV64MaxStopRiskCash = 1.10",
        "InpV64EmergencyLossCash = 1.20",
        "InpV64PrimaryTargetCash = 3.50",
        "InpV69MinConfirmSeparationRiskCash = 1.30",
        "InpV69MinConfirmAgeSeconds = 30",
        "POST_CONFIRM_SEPARATION",
        "POST_CONFIRM_RETEST_READY",
        "POST_CONFIRM_ENTRY_READY",
        "ACCOUNT_TRADE_MODE_DEMO",
        "v69_forward_demo_only",
        "V69 FROZEN FORWARD HALT: DEMO ACCOUNT REQUIRED",
        "g_trade.Buy",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V69 forward generated source missing token: {token}")

    forbidden = (
        V69_RESEARCH_ROOT,
        "MQL_TESTER",
        "InpV64AllowedDirection = -1",
        "V69ForwardRealMoneyAuthorized=true",
        "V48WriteInitDiagnostic",
    )
    for token in forbidden:
        if token in text:
            raise RuntimeError(f"V69 forward forbidden token remains: {token}")

    stage = text[text.index("void V66TryMicroEntry"):text.index("void V64ManagePendingEntry")]
    confirm = stage.index('V64PendingEvent("POST_ZONE_REVERSAL_CONFIRM"')
    first_return = stage.index("return;", confirm)
    separation = stage.index('V64PendingEvent("POST_CONFIRM_SEPARATION"')
    retest = stage.index('V64PendingEvent("POST_CONFIRM_RETEST_READY"')
    ready = stage.index('V64PendingEvent("POST_CONFIRM_ENTRY_READY"')
    preflight = stage.index("V64OrderPreflight")
    if not (confirm < first_return < separation < retest < ready < preflight):
        raise RuntimeError("V69 forward changed frozen entry-state ordering")


def build(output: Path) -> str:
    text = transform().replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = sha256(output)
    print(f"V69_FORWARD_SOURCE_SHA256={digest}")
    print(f"V69_FORWARD_SOURCE_PATH={output}")
    print("V69_FORWARD_DIRECTION=LONG_ONLY")
    print("V69_FORWARD_DEMO_ONLY=1")
    print("V69_FORWARD_REAL_MONEY_AUTHORIZED=0")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
