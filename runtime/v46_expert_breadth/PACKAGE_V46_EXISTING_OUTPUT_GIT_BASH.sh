#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO="$(cd -- "$ROOT/../.." && pwd -P)"
OUT="$ROOT/OUTPUT_V46"
BUNDLE="$OUT/bundle"
ZIP="$OUT/v46_expert_breadth_walkforward.zip"
PY="$REPO/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
PACKAGER="$REPO/scripts/package_research_bundle_portable.py"

[[ -x "$PY" ]] || { echo "FATAL: pinned Python missing: $PY" >&2; exit 1; }
[[ -s "$BUNDLE/V46_EVIDENCE.txt" && -s "$BUNDLE/v46_expert_breadth_analysis.json" && -s "$BUNDLE/monthly_summary.csv" && -s "$BUNDLE/trades.csv" && -s "$BUNDLE/manifest.txt" ]] || {
  echo "FATAL: completed V46 bundle evidence missing; package-only is not applicable" >&2
  exit 1
}

"$PY" "$(cygpath -w "$PACKAGER")" --bundle "$(cygpath -w "$BUNDLE")" --output "$(cygpath -w "$ZIP")"
echo "V46 PACKAGE-ONLY COMPLETE — MT5 WAS NOT RERUN"
echo "UPLOAD THIS ONE ZIP:"
echo "$(cygpath -w "$ZIP")"
"$PY" - "$ZIP" <<'PY'
from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1])
h=hashlib.sha256(p.read_bytes()).hexdigest()
print('SHA256='+h)
PY
