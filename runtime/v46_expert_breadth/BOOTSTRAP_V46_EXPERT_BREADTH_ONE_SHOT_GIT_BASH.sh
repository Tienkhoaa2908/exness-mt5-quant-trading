#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
WORK="${WORK:-$(cd -- "$SCRIPT_DIR/../.." && pwd -P)}"
BRANCH="${BRANCH:-agent/v46-expert-breadth-walkforward}"
REMOTE="${REMOTE:-origin}"
REMOTE_REF="refs/remotes/$REMOTE/$BRANCH"
RUNNER="$WORK/runtime/v46_expert_breadth/RUN_V46_EXPERT_BREADTH_ONE_SHOT.py"
PACKAGE_ONLY="$WORK/runtime/v46_expert_breadth/PACKAGE_V46_EXISTING_OUTPUT_GIT_BASH.sh"
TEST="$WORK/tests/test_v46_expert_breadth_static.py"
MOVE="$WORK/runtime/v45_multiyear_validation/MOVE_V45_TESTER_STORAGE_TO_D.py"
PREP="$WORK/runtime/v45_multiyear_validation/PREPARE_V45_DISK.py"
VENV="$WORK/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv"
PY="$VENV/Scripts/python.exe"

[[ -d "$WORK/.git" ]] || { echo "FATAL: Git checkout missing: $WORK" >&2; exit 1; }

echo "=== V46 EXPERT-BREADTH WALKFORWARD EXACT-MT5 ==="
echo "WORK=$WORK"
echo "Primary: HL10p05 + >=4/5 expert HL10 EWMAs >=0.05."
echo "Breadth3/5 are sensitivity only; no same-sample promotion."
echo "One tester invocation: 2021.01.03 -> 2026.08.01; first 6 months warm-up."
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

[[ -s "$RUNNER" && -s "$PACKAGE_ONLY" && -s "$TEST" && -s "$MOVE" && -s "$PREP" ]] || { echo "FATAL: V46 entrypoint missing" >&2; exit 1; }
bash -n "$0"
bash -n "$PACKAGE_ONLY"
"$PY" -m py_compile "$(cygpath -w "$RUNNER")" "$(cygpath -w "$TEST")"
"$PY" "$(cygpath -w "$TEST")"

cd "$WORK"
"$PY" "$(cygpath -w "$MOVE")"
"$PY" "$(cygpath -w "$PREP")"

if "$PY" "$(cygpath -w "$RUNNER")"; then
  exit 0
else
  rc=$?
fi

BUNDLE="$WORK/runtime/v46_expert_breadth/OUTPUT_V46/bundle"
if [[ -s "$BUNDLE/V46_EVIDENCE.txt" && -s "$BUNDLE/v46_expert_breadth_analysis.json" && -s "$BUNDLE/monthly_summary.csv" && -s "$BUNDLE/trades.csv" && -s "$BUNDLE/manifest.txt" ]]; then
  echo "V46 runner returned rc=$rc after completed evidence; package-only recovery. MT5 WILL NOT RERUN."
  bash "$PACKAGE_ONLY"
  exit 0
fi
exit "$rc"
