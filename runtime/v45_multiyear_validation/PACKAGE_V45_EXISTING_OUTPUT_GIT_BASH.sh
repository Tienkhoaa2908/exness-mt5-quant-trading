#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
OUT="$ROOT/OUTPUT_V45"
BUNDLE="$OUT/bundle"
ZIP="$OUT/v45_multiyear_single_run_validation.zip"
PACKAGER="$REPO_ROOT/scripts/package_research_bundle_portable.py"
PY="$REPO_ROOT/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"

[[ -x "$PY" ]] || { echo "FATAL: pinned Python missing" >&2; exit 1; }
[[ -s "$PACKAGER" ]] || { echo "FATAL: portable packager missing" >&2; exit 1; }
[[ -d "$BUNDLE" ]] || { echo "FATAL: V45 completed bundle missing" >&2; exit 1; }
for f in V45_EVIDENCE.txt v45_multiyear_analysis.json v45_monthly_analysis.csv v45_yearly_analysis.csv v45_rolling_analysis.csv monthly_summary.csv trades.csv manifest.txt; do
  [[ -s "$BUNDLE/$f" ]] || { echo "FATAL: completed V45 bundle missing $f" >&2; exit 1; }
done
grep -Fq 'tester_only=1' "$BUNDLE/manifest.txt"
grep -Fq 'native_broker_orders=0' "$BUNDLE/manifest.txt"
grep -Fq 'external_broker_orders=0' "$BUNDLE/manifest.txt"
grep -Fq 'v45_multiyear_validation=1' "$BUNDLE/manifest.txt"

"$PY" -m py_compile "$(cygpath -w "$PACKAGER")"
"$PY" "$(cygpath -w "$PACKAGER")" --bundle "$(cygpath -w "$BUNDLE")" --output "$(cygpath -w "$ZIP")"
echo "V45 PACKAGE-ONLY RECOVERY DONE — MT5 WAS NOT RERUN"
echo "UPLOAD THIS ONE ZIP:"
cygpath -w "$ZIP"
sha256sum "$ZIP"
