#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
WORK="${WORK:-$(cd -- "$SCRIPT_DIR/../.." && pwd -P)}"
BRANCH="${BRANCH:-agent/v46-expert-breadth-walkforward}"
REMOTE="${REMOTE:-origin}"
REMOTE_REF="refs/remotes/$REMOTE/$BRANCH"
RUNNER="$WORK/runtime/v46_expert_breadth/RUN_V46_EXPERT_BREADTH_ONE_SHOT_CANONICAL.py"
BUILDER="$WORK/scripts/build_v46_expert_breadth_source_canonical.py"
TEST_BASE="$WORK/tests/test_v46_expert_breadth_static.py"
TEST_SHA="$WORK/tests/test_v46_canonical_sha_fix_static.py"
MOVE="$WORK/runtime/v45_multiyear_validation/MOVE_V45_TESTER_STORAGE_TO_D.py"
PREP="$WORK/runtime/v45_multiyear_validation/PREPARE_V45_DISK.py"
PACKAGE_ONLY="$WORK/runtime/v46_expert_breadth/PACKAGE_V46_EXISTING_OUTPUT_GIT_BASH.sh"
VENV="$WORK/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv"
PY="$VENV/Scripts/python.exe"

[[ -d "$WORK/.git" ]] || { echo "FATAL: Git checkout missing: $WORK" >&2; exit 1; }

echo "=== V46 CANONICAL EXPERT-BREADTH EXACT-MT5 ==="
echo "WORK=$WORK"
echo "Primary stays breadth4. Crisis years are evaluated for capital preservation, not forced profitability."
echo "Canonical source SHA=6f09a8513f9446b415982fd3752c52d9bba7ff0bd1762135ef2e463f47daa1a3"
echo "One tester invocation only: 2021.01.03 -> 2026.08.01."
echo "REAL-MONEY LIVE TRADING remains FORBIDDEN. LIVE_AUTHORIZED=0."

git -C "$WORK" fetch --no-tags "$REMOTE" "+refs/heads/$BRANCH:$REMOTE_REF"
git -C "$WORK" show-ref --verify --quiet "$REMOTE_REF" || { echo "FATAL: remote ref missing $REMOTE_REF" >&2; exit 1; }
git -C "$WORK" checkout -B "$BRANCH" "$REMOTE_REF"
git -C "$WORK" reset --hard "$REMOTE_REF"

echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
echo "BRANCH=$(git -C "$WORK" branch --show-current)"

if [[ ! -x "$PY" ]]; then
  echo "=== Create pinned Python environment on current repo volume ==="
  SYS_PY=""
  if command -v python >/dev/null 2>&1; then SYS_PY="$(command -v python)";
  elif command -v python3 >/dev/null 2>&1; then SYS_PY="$(command -v python3)";
  elif command -v py.exe >/dev/null 2>&1; then SYS_PY="$(command -v py.exe)";
  fi
  [[ -n "$SYS_PY" ]] || { echo "FATAL: Python 3 not found" >&2; exit 64; }
  mkdir -p "$(dirname "$VENV")"
  VENV_WIN="$(cygpath -w "$VENV")"
  if [[ "$(basename "$SYS_PY")" == "py.exe" ]]; then
    MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' "$SYS_PY" -3 -m venv "$VENV_WIN"
  else
    "$SYS_PY" -m venv "$VENV_WIN"
  fi
fi
[[ -x "$PY" ]] || { echo "FATAL: venv Python missing: $PY" >&2; exit 65; }

"$PY" - <<'PYBASE'
import sys
from pathlib import Path
if sys.version_info < (3,12) or not hasattr(Path('.'),'is_junction'):
    raise SystemExit(f"FATAL: Python >=3.12 with Path.is_junction required; actual={sys.version}")
print(f"V46_PYTHON_RUNTIME_PASS version={sys.version.split()[0]}")
PYBASE

if ! "$PY" - <<'PYCHK' >/dev/null 2>&1
import numpy,pandas,sklearn
assert numpy.__version__=='2.3.5'
assert pandas.__version__=='2.2.3'
assert sklearn.__version__=='1.8.0'
PYCHK
then
  "$PY" -m pip install --disable-pip-version-check --upgrade pip
  "$PY" -m pip install --disable-pip-version-check "numpy==2.3.5" "pandas==2.2.3" "scikit-learn==1.8.0"
fi

for f in "$RUNNER" "$BUILDER" "$TEST_BASE" "$TEST_SHA" "$MOVE" "$PREP" "$PACKAGE_ONLY"; do
  [[ -s "$f" ]] || { echo "FATAL: required V46 file missing: $f" >&2; exit 1; }
done
bash -n "$0"
bash -n "$PACKAGE_ONLY"
"$PY" -m py_compile "$(cygpath -w "$RUNNER")" "$(cygpath -w "$BUILDER")" "$(cygpath -w "$TEST_BASE")" "$(cygpath -w "$TEST_SHA")"
"$PY" "$(cygpath -w "$TEST_BASE")"
"$PY" "$(cygpath -w "$TEST_SHA")"

cd "$WORK"
"$PY" "$(cygpath -w "$MOVE")"
"$PY" "$(cygpath -w "$PREP")"

if "$PY" "$(cygpath -w "$RUNNER")"; then
  rc=0
else
  rc=$?
fi

echo
echo "============================================================"
echo "V46 CANONICAL FINISHED/STOPPED RC=$rc"
echo "THIS SCRIPT DOES NOT DELETE COMPLETED MT5 CHECKPOINTS"
echo "============================================================"
exit "$rc"
