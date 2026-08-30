#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v64_microstructure_trigger_shadow_source.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parent = load(PARENT, "v64_parent_fixed")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V64 fixed {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


def transform(allowed_direction: int) -> str:
    text = parent.transform(allowed_direction)

    # MQL5 has IntegerToString(long), but no LongToString(). Keep the 64-bit
    # shadow sequence id intact and make the generated source MetaEditor-valid.
    text = replace_once(
        text,
        "LongToString(g_v64_noise[k].id)",
        "IntegerToString(g_v64_noise[k].id)",
        "long id string conversion",
    )

    # First-hit stop/target states are frozen when hit, but the path remains
    # alive until the fixed horizon so we can distinguish genuine invalidation
    # from stop-then-recovery micro-noise.
    text = replace_once(
        text,
        'if(unresolved==0){V64NoiseFinish(k,"all_resolved");continue;}\n      if(TimeCurrent()-g_v64_noise[k].started>=InpV64NoiseShadowMaxMinutes*60)',
        'if(unresolved==0){ /* first-hit matrix resolved; continue path telemetry */ }\n      if(TimeCurrent()-g_v64_noise[k].started>=InpV64NoiseShadowMaxMinutes*60)',
        "noise shadow persistence",
    )

    text = replace_once(
        text,
        "   V64EnsureHeaders();\n   V64WriteStatus(\"READY\",\"profit_ratchet_m5_refinement\");",
        "   V64EnsureHeaders();\n"
        "   if(!FileIsExist(V64_NOISE_FILE,FILE_COMMON))\n"
        "      V64Append(V64_NOISE_FILE,\"id,start,end,direction,entry,max_pnl,min_pnl,s110_t300,s110_t350,s110_t400,s135_t300,s135_t350,s135_t400,s160_t300,s160_t350,s160_t400,reason\");\n"
        "   V64WriteStatus(\"READY\",\"microstructure_trigger_shadow\");",
        "noise header",
    )

    text = replace_once(
        text,
        'void OnDeinit(const int reason)\n{\n   if(g_shadow_open) V64FinishShadow("tester_end");\n   V64WriteStatus("STOPPED",IntegerToString(reason));\n}',
        'void OnDeinit(const int reason)\n{\n'
        '   if(g_shadow_open) V64FinishShadow("tester_end");\n'
        '   for(int k=0;k<V64_NOISE_MAX;k++) if(g_v64_noise[k].active) V64NoiseFinish(k,"tester_end");\n'
        '   V64WriteStatus("STOPPED",IntegerToString(reason));\n'
        '}',
        "noise deinit flush",
    )

    validate(text)
    return text


def validate(text: str) -> None:
    required = (
        "IntegerToString(g_v64_noise[k].id)",
        "first-hit matrix resolved; continue path telemetry",
        "id,start,end,direction,entry,max_pnl,min_pnl,s110_t300",
        'V64NoiseFinish(k,"tester_end")',
        'V64WriteStatus("READY","microstructure_trigger_shadow")',
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V64 fixed required token missing: {token}")
    if "LongToString(" in text:
        raise RuntimeError("V64 generated MQL still uses nonexistent LongToString")
    if 'V64NoiseFinish(k,"all_resolved")' in text:
        raise RuntimeError("V64 noise path still terminates when first-hit matrix resolves")


def build(output: Path, allowed_direction: int) -> str:
    text = transform(allowed_direction).replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = sha256(output)
    print(f"V64_FIXED_SOURCE_SHA256={digest}")
    print(f"V64_FIXED_SOURCE_PATH={output}")
    print(f"V64_ALLOWED_DIRECTION={allowed_direction}")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--allowed-direction", required=True, type=int, choices=(-1, 1))
    args = ap.parse_args()
    build(args.output, args.allowed_direction)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
