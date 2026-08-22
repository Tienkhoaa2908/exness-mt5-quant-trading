#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
DEFAULT_WORK="$(cd -- "$SCRIPT_DIR/../.." && pwd -P)"
WORK="${WORK:-$DEFAULT_WORK}"
BRANCH="${BRANCH:-agent/v45-multiyear-single-run-validation}"
REMOTE="${REMOTE:-origin}"
REMOTE_REF="refs/remotes/$REMOTE/$BRANCH"
RUNNER="$WORK/runtime/v45_multiyear_validation/RUN_V45_MULTIYEAR_ONE_SHOT_RECOVERABLE.py"
BASE_RUNNER="$WORK/runtime/v45_multiyear_validation/RUN_V45_MULTIYEAR_ONE_SHOT.py"
MOVE="$WORK/runtime/v45_multiyear_validation/MOVE_V45_TESTER_STORAGE_TO_D.py"
PREP="$WORK/runtime/v45_multiyear_validation/PREPARE_V45_DISK.py"
PACKAGE_ONLY="$WORK/runtime/v45_multiyear_validation/PACKAGE_V45_EXISTING_OUTPUT_GIT_BASH.sh"
DISK_TEST="$WORK/tests/test_v45_disk_preflight_static.py"
MOVE_TEST="$WORK/tests/test_v45_tester_storage_migration_static.py"
RECOVERY_TEST="$WORK/tests/test_v45_clean_clone_recovery_static.py"
VENV="$WORK/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv"
PY="$VENV/Scripts/python.exe"

[[ -d "$WORK/.git" ]] || { echo "FATAL: Git checkout missing: $WORK" >&2; exit 1; }

echo "=== V45 MULTIYEAR SINGLE-RUN EXACT-MT5 BOOTSTRAP ==="
echo "WORK=$WORK"
echo "One MT5 tester invocation. Monthly results are retained."
echo "Clean-clone recovery: pinned Python env can be rebuilt; accepted V38 parent can be exactly recovered from installed V45 source if the old V38 ZIP is missing."
echo "MetaTester heavy storage is migrated to D:\\MT5TesterCache via NTFS junction before the run."
echo "Disk preflight then requires >=2 GiB on the terminal volume and >=12 GiB on the tester-storage volume."
echo "REAL-MONEY LIVE TRADING remains FORBIDDEN. LIVE_AUTHORIZED=0."

git -C "$WORK" fetch --no-tags "$REMOTE" "+refs/heads/$BRANCH:$REMOTE_REF"
git -C "$WORK" show-ref --verify --quiet "$REMOTE_REF" || { echo "FATAL: remote ref missing $REMOTE_REF" >&2; exit 1; }
git -C "$WORK" checkout -B "$BRANCH" "$REMOTE_REF"
git -C "$WORK" reset --hard "$REMOTE_REF"

echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
echo "BRANCH=$(git -C "$WORK" branch --show-current)"
echo "PYTHONUTF8=$PYTHONUTF8 PYTHONIOENCODING=$PYTHONIOENCODING"

[[ -s "$RUNNER" && -s "$BASE_RUNNER" && -s "$MOVE" && -s "$PREP" && -s "$PACKAGE_ONLY" && -s "$DISK_TEST" && -s "$MOVE_TEST" && -s "$RECOVERY_TEST" ]] || { echo "FATAL: V45 entrypoint missing" >&2; exit 1; }
bash -n "$0"
bash -n "$PACKAGE_ONLY"

if [[ ! -x "$PY" ]]; then
  echo "=== Create pinned V45 Python environment on current repo volume ==="
  SYS_PY=""
  if command -v python >/dev/null 2>&1; then
    SYS_PY="$(command -v python)"
  elif command -v python3 >/dev/null 2>&1; then
    SYS_PY="$(command -v python3)"
  elif command -v py.exe >/dev/null 2>&1; then
    SYS_PY="$(command -v py.exe)"
  fi
  [[ -n "$SYS_PY" ]] || { echo "FATAL: system Python 3 not found; install Python 3 and rerun" >&2; exit 64; }
  mkdir -p "$(dirname "$VENV")"
  VENV_WIN="$(cygpath -w "$VENV")"
  if [[ "$(basename "$SYS_PY")" == "py.exe" ]]; then
    MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' "$SYS_PY" -3 -m venv "$VENV_WIN"
  else
    "$SYS_PY" -m venv "$VENV_WIN"
  fi
fi

[[ -x "$PY" ]] || { echo "FATAL: V45 venv Python missing after creation: $PY" >&2; exit 65; }

"$PY" - <<'PYBASE'
import sys
from pathlib import Path
if sys.version_info < (3, 12) or not hasattr(Path('.'), 'is_junction'):
    raise SystemExit(f"FATAL: V45 storage migration requires Python >=3.12 with pathlib.Path.is_junction(); actual={sys.version}")
print(f"V45_PYTHON_RUNTIME_PASS version={sys.version.split()[0]} junction_api=1")
PYBASE

if ! "$PY" - <<'PYCHK' >/dev/null 2>&1
import numpy,pandas,sklearn
assert numpy.__version__=="2.3.5"
assert pandas.__version__=="2.2.3"
assert sklearn.__version__=="1.8.0"
PYCHK
then
  echo "=== Install pinned V45 Python dependencies ==="
  "$PY" -m pip install --disable-pip-version-check --upgrade pip
  "$PY" -m pip install --disable-pip-version-check "numpy==2.3.5" "pandas==2.2.3" "scikit-learn==1.8.0"
fi

"$PY" - <<'PYCHK'
import numpy,pandas,sklearn
assert numpy.__version__=="2.3.5"
assert pandas.__version__=="2.2.3"
assert sklearn.__version__=="1.8.0"
print("V45_PINNED_PYTHON_PASS numpy=2.3.5 pandas=2.2.3 sklearn=1.8.0")
PYCHK

"$PY" -m py_compile "$(cygpath -w "$RUNNER")" "$(cygpath -w "$BASE_RUNNER")" "$(cygpath -w "$MOVE")" "$(cygpath -w "$PREP")" "$(cygpath -w "$DISK_TEST")" "$(cygpath -w "$MOVE_TEST")" "$(cygpath -w "$RECOVERY_TEST")"
"$PY" "$(cygpath -w "$RECOVERY_TEST")"
"$PY" "$(cygpath -w "$MOVE_TEST")"
"$PY" "$(cygpath -w "$DISK_TEST")"

cd "$WORK"

# One-time/idempotent storage migration. The old C: tester path becomes a
# junction; only MetaTester agent storage moves. Terminal broker history,
# project evidence, states, and compiled EAs stay in place.
"$PY" "$(cygpath -w "$MOVE")"

# Junction-aware fail-fast disk gate. It checks the actual physical tester
# storage volume (normally D:) separately from the terminal volume (normally C:).
"$PY" "$(cygpath -w "$PREP")"

if "$PY" "$(cygpath -w "$RUNNER")"; then
  exit 0
else
  rc=$?
fi

BUNDLE="$WORK/runtime/v45_multiyear_validation/OUTPUT_V45/bundle"
if [[ -s "$BUNDLE/V45_EVIDENCE.txt" && -s "$BUNDLE/v45_multiyear_analysis.json" && -s "$BUNDLE/monthly_summary.csv" && -s "$BUNDLE/trades.csv" && -s "$BUNDLE/manifest.txt" ]]; then
  echo "V45 runner returned rc=$rc after completed evidence; attempting package-only recovery. MT5 WILL NOT RERUN."
  bash "$PACKAGE_ONLY"
  exit 0
fi
exit "$rc"
