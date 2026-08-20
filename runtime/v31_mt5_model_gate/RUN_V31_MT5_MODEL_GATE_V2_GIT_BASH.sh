#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
BASE="$ROOT/RUN_V31_MT5_MODEL_GATE_GIT_BASH.sh"
TMP="$ROOT/.RUN_V31_MT5_MODEL_GATE_CORRECTED.sh"
OUT="$ROOT/OUTPUT_V31_MT5"
CORRECT_TAPE_SHA="b30bbf3ad34028f826d3d1bfee45a2c2b05463ea211e379678cc19587f110491"
OLD_TAPE_SHA="44c11a98b75c7764e7a07eff245e1864d9dc85acc4a116a5cd162acb241539fc"

[[ -s "$BASE" ]] || { echo "FATAL: base runner missing: $BASE" >&2; exit 1; }
cp -f "$BASE" "$TMP"
sed -i "s/$OLD_TAPE_SHA/$CORRECT_TAPE_SHA/g" "$TMP"
grep -Fq "$CORRECT_TAPE_SHA" "$TMP" || { echo "FATAL: corrected causal reference SHA not installed" >&2; exit 1; }

bash "$TMP"
rc=$?
[[ $rc -eq 0 ]] || exit $rc

VENV_PY="$OUT/.venv/Scripts/python.exe"
ANALYZER="$REPO_ROOT/scripts/analyze_v31_mt5_model_gate.py"
PKG="$OUT/package"
[[ -x "$VENV_PY" ]] || { echo "FATAL: V31 venv Python missing after runner" >&2; exit 2; }
[[ -s "$ANALYZER" ]] || { echo "FATAL: exact-MT5 analyzer missing: $ANALYZER" >&2; exit 3; }

"$VENV_PY" "$ANALYZER" --package-root "$(cygpath -w "$PKG")" --output "$(cygpath -w "$PKG/analysis")"

STAMP="$(date '+%Y%m%d_%H%M%S')"
FINAL="$OUT/v31_mt5_model_gate_40usd_ANALYZED_${STAMP}.zip"
"$VENV_PY" - "$PKG" "$FINAL" <<'PY'
import os,sys,zipfile
root,out=sys.argv[1:]
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for base,dirs,files in os.walk(root):
        dirs.sort(); files.sort()
        for f in files:
            p=os.path.join(base,f)
            z.write(p,os.path.relpath(p,root).replace('\\','/'))
PY
[[ -s "$FINAL" ]] || { echo "FATAL: analyzed final ZIP missing" >&2; exit 4; }
SHA="$(sha256sum "$FINAL" | awk '{print $1}')"
echo
echo "============================================================"
echo "V31 EXACT MT5 + ANALYSIS DONE"
echo "UPLOAD THIS ONE ZIP:"
echo "$(cygpath -w "$FINAL")"
echo "SHA256=$SHA"
echo "Exact report inside ZIP: analysis/V31_EXACT_MT5_REPORT.txt"
echo "============================================================"
