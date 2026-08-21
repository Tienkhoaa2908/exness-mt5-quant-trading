#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
OUT="$ROOT/OUTPUT_V43"
BUNDLE="$OUT/bundle"
ZIP="$OUT/v43_confidence_router_exact_mt5.zip"
PACKAGER="$REPO_ROOT/scripts/package_research_bundle_portable.py"
PY="$REPO_ROOT/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"

[[ -x "$PY" ]] || { echo "FATAL: pinned Python missing: $PY" >&2; exit 1; }
[[ -s "$PACKAGER" ]] || { echo "FATAL: portable packager missing: $PACKAGER" >&2; exit 1; }
[[ -d "$BUNDLE" ]] || { echo "FATAL: V43 bundle directory missing: $BUNDLE" >&2; exit 1; }

for f in V43_EVIDENCE.txt v43_confidence_router_analysis.json v43_confidence_router_comparison.csv monthly_summary.csv trades.csv manifest.txt; do
  [[ -s "$BUNDLE/$f" ]] || { echo "FATAL: existing completed V43 bundle missing $f" >&2; exit 1; }
done

grep -Fq 'v43_confidence_aware_router=1' "$BUNDLE/manifest.txt" || { echo "FATAL: V43 manifest marker missing" >&2; exit 1; }
grep -Fq 'tester_only=1' "$BUNDLE/manifest.txt" || { echo "FATAL: tester_only marker missing" >&2; exit 1; }
grep -Fq 'native_broker_orders=0' "$BUNDLE/manifest.txt" || { echo "FATAL: native order marker mismatch" >&2; exit 1; }
grep -Fq 'external_broker_orders=0' "$BUNDLE/manifest.txt" || { echo "FATAL: external order marker mismatch" >&2; exit 1; }

"$PY" -m py_compile "$PACKAGER"
"$PY" "$PACKAGER" --bundle "$(cygpath -w "$BUNDLE")" --output "$(cygpath -w "$ZIP")"

"$PY" - "$BUNDLE/v43_confidence_router_analysis.json" <<'PYPRINT'
import json,sys
with open(sys.argv[1],encoding='utf-8') as f:
    d=json.load(f)
c=d['exact_control']
w=next(x for x in d['v43_challengers'] if x['candidate']==d['development_v43_return_winner'])
print(f"EXACT_CONTROL_END_USD={c['ending_usd']:.6f}")
print(f"EXACT_CONTROL_GEO_MONTH={c['geo_month_pct']:.4f}%")
print(f"EXACT_CONTROL_MAX_DD={c['max_mtm_dd_pct']:.4f}%")
print(f"V43_WINNER={w['candidate']}")
print(f"V43_WINNER_END_USD={w['ending_usd']:.6f}")
print(f"V43_WINNER_GEO_MONTH={w['geo_month_pct']:.4f}%")
print(f"V43_WINNER_MAX_DD={w['max_mtm_dd_pct']:.4f}%")
print('ELIGIBLE_TO_FREEZE='+(','.join(d['eligible_to_freeze_for_fresh_holdout']) or 'NONE'))
print(f"TARGET_GEO_MONTH={d['aspirational_target']['geo_month_pct']:.2f}%")
PYPRINT

echo "PACKAGE-ONLY RECOVERY DONE — MT5 WAS NOT RERUN"
echo "UPLOAD THIS ONE ZIP:"
cygpath -w "$ZIP"
sha256sum "$ZIP"
