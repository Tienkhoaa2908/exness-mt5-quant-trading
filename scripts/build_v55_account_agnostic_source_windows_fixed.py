#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEGACY_BUILDER = HERE / "build_v55_account_agnostic_source.py"

# V49/V53/V54 intentionally inherited V48's DEMO-only OnInit guard. V55 is the
# first same-binary DEMO/REAL layer, so that historical guard must be relaxed
# before the existing V55 transform runs. Match the structural prefix rather
# than the milestone label inside Print(...), because that label is renamed by
# V49 -> V53 -> V54 generation.
INHERITED_DEMO_GUARD_PREFIX = (
    '   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO)'
    '{ V48WriteInitDiagnostic("REFUSED","real_or_non_demo_account"); '
)

V55_ACCOUNT_MODE_GUARD_PREFIX = (
    '   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO '
    '&& (ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_REAL)'
    '{ V48WriteInitDiagnostic("REFUSED","unsupported_account_mode"); '
)

V54_DEMO_ONLY_PRINT = 'Print("V54 PRODUCTION READINESS REFUSED: DEMO ACCOUNT REQUIRED");'
V55_SUPPORTED_MODE_PRINT = 'Print("V55 ACCOUNT-AGNOSTIC REFUSED: DEMO OR REAL ACCOUNT REQUIRED");'


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def replace_exactly_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"V55 {label} drifted expected=1 actual={count}")
    return text.replace(old, new, 1)


def sanitize_inherited_demo_guard(text: str) -> str:
    out = replace_exactly_once(
        text,
        INHERITED_DEMO_GUARD_PREFIX,
        V55_ACCOUNT_MODE_GUARD_PREFIX,
        "inherited V48 DEMO-only OnInit guard prefix",
    )
    out = replace_exactly_once(
        out,
        V54_DEMO_ONLY_PRINT,
        V55_SUPPORTED_MODE_PRINT,
        "V54 DEMO-only OnInit diagnostic",
    )
    if "real_or_non_demo_account" in out:
        raise RuntimeError("V55 inherited non-DEMO refusal token remains after sanitation")
    return out


def main() -> int:
    legacy = load(LEGACY_BUILDER, "v55_legacy_builder_for_windows_fix")
    original_transform = legacy.transform

    def fixed_transform(text: str) -> str:
        prepared = sanitize_inherited_demo_guard(text)
        final = original_transform(prepared)
        required = (
            "V55 ACCOUNT-AGNOSTIC REFUSED: DEMO OR REAL ACCOUNT REQUIRED",
            "unsupported_account_mode",
            "ACCOUNT_TRADE_MODE_DEMO",
            "ACCOUNT_TRADE_MODE_REAL",
            "V55SupportedAccountMode",
            "V55RealExecutionAuthorized",
            "V55NewRiskAuthorized",
        )
        for token in required:
            if token not in final:
                raise RuntimeError(f"V55 fixed builder required token missing: {token}")
        for forbidden in (
            "real_or_non_demo_account",
            'V55Halt("non_demo_account")',
            "V55 PRODUCTION READINESS REFUSED: DEMO ACCOUNT REQUIRED",
        ):
            if forbidden in final:
                raise RuntimeError(f"V55 fixed builder forbidden token remains: {forbidden}")
        return final

    legacy.transform = fixed_transform
    return legacy.main()


if __name__ == "__main__":
    raise SystemExit(main())
