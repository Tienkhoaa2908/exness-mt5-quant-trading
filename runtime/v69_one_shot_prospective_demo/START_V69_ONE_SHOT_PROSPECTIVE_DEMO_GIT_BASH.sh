#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
RUNNER="$ROOT/RUN_V69_ONE_SHOT_PROSPECTIVE_DEMO.py"
STATIC="$REPO_ROOT/tests/test_v69_one_shot_prospective_demo_static.py"
EXPECTED_BRANCH="agent/v69-one-shot-prospective-demo"
EXPECTED_HEAD="${V69_ONE_SHOT_EXPECTED_HEAD:-}"

say(){ printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die(){ echo "FATAL: $*" >&2; exit 1; }
trap 'rc=$?; echo "FAILED rc=$rc line=${BASH_LINENO[0]:-?} cmd=${BASH_COMMAND:-?}" >&2; exit $rc' ERR

[[ -d "$REPO_ROOT/.git" ]] || die "repository not found: $REPO_ROOT"
[[ -s "$RUNNER" ]] || die "runner missing: $RUNNER"
[[ -s "$STATIC" ]] || die "static test missing: $STATIC"
[[ -n "$EXPECTED_HEAD" ]] || die "V69_ONE_SHOT_EXPECTED_HEAD is required"

say "Repository exact-state preflight"
BRANCH="$(git -C "$REPO_ROOT" branch --show-current)"
HEAD="$(git -C "$REPO_ROOT" rev-parse HEAD)"
DIRTY="$(git -C "$REPO_ROOT" status --porcelain)"
echo "BRANCH=$BRANCH"
echo "HEAD=$HEAD"
echo "EXPECTED_HEAD=$EXPECTED_HEAD"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || die "wrong branch expected=$EXPECTED_BRANCH actual=$BRANCH"
[[ "$HEAD" == "$EXPECTED_HEAD" ]] || die "wrong HEAD expected=$EXPECTED_HEAD actual=$HEAD"
[[ -z "$DIRTY" ]] || { printf '%s\n' "$DIRTY"; die "working tree dirty; DO NOT git clean and DO NOT stash pop"; }

PY_CMD=()
probe_python(){
  local label="$1"; shift
  if "$@" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 17)' >/dev/null 2>&1; then
    PY_CMD=("$@")
    echo "PYTHON_SELECTED=$label"
    "$@" -c 'import sys; print("PYTHON_EXECUTABLE=" + sys.executable); print("PYTHON_VERSION=" + sys.version.split()[0])'
    return 0
  fi
  echo "PYTHON_REJECTED=$label"
  return 1
}

say "Python discovery"
if [[ -n "${V69_PYTHON:-}" ]]; then probe_python "V69_PYTHON" "$V69_PYTHON" || true; fi
PINNED="$REPO_ROOT/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
if [[ ${#PY_CMD[@]} -eq 0 && -f "$PINNED" ]]; then probe_python "V31_PINNED_VENV" "$PINNED" || true; fi
if [[ ${#PY_CMD[@]} -eq 0 ]] && command -v py.exe >/dev/null 2>&1; then probe_python "py.exe -3" py.exe -3 || true; fi
if [[ ${#PY_CMD[@]} -eq 0 ]] && command -v python.exe >/dev/null 2>&1; then probe_python "python.exe" python.exe || true; fi
if [[ ${#PY_CMD[@]} -eq 0 ]] && command -v python3 >/dev/null 2>&1; then probe_python "python3" python3 || true; fi
if [[ ${#PY_CMD[@]} -eq 0 ]] && command -v python >/dev/null 2>&1; then probe_python "python" python || true; fi
if [[ ${#PY_CMD[@]} -eq 0 ]]; then
  while IFS= read -r candidate; do
    [[ -n "$candidate" ]] || continue
    if probe_python "REPO_VENV:$candidate" "$candidate"; then break; fi
  done < <(find "$REPO_ROOT/runtime" -type f -path '*/.venv/Scripts/python.exe' -print 2>/dev/null | sort)
fi
[[ ${#PY_CMD[@]} -gt 0 ]] || die "no working Python 3.10+ found"

say "Static gates"
bash -n "$0"
"${PY_CMD[@]}" -m py_compile "$RUNNER" "$STATIC"
"${PY_CMD[@]}" "$STATIC"

say "Start V69 frozen prospective DEMO one-shot"
"${PY_CMD[@]}" "$RUNNER"

echo
 echo "V69_ONE_SHOT_LAUNCHER=PASS"
echo "REAL_MONEY_AUTHORIZED=0"
