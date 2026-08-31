#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
RUNNER="$ROOT/RUN_V69_TRADE_QUALITY_DIAGNOSTICS.py"
EXPECTED_BRANCH="agent/v69-trade-quality-diagnostics"
EXPECTED_HEAD="${V69_TRADE_QUALITY_EXPECTED_HEAD:-}"

say(){ printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die(){ echo "FATAL: $*" >&2; exit 1; }
trap 'rc=$?; echo "FAILED rc=$rc line=${BASH_LINENO[0]:-?} cmd=${BASH_COMMAND:-?}" >&2; exit $rc' ERR

[[ -d "$REPO_ROOT/.git" ]] || die "repository not found: $REPO_ROOT"
[[ -s "$RUNNER" ]] || die "diagnostics runner missing: $RUNNER"
[[ -n "$EXPECTED_HEAD" ]] || die "V69_TRADE_QUALITY_EXPECTED_HEAD is required"

say "Repository preflight"
BRANCH="$(git -C "$REPO_ROOT" branch --show-current)"
HEAD="$(git -C "$REPO_ROOT" rev-parse HEAD)"
DIRTY="$(git -C "$REPO_ROOT" status --porcelain)"
echo "BRANCH=$BRANCH"
echo "HEAD=$HEAD"
echo "EXPECTED_HEAD=$EXPECTED_HEAD"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || die "wrong branch expected=$EXPECTED_BRANCH actual=$BRANCH"
[[ "$HEAD" == "$EXPECTED_HEAD" ]] || die "wrong HEAD expected=$EXPECTED_HEAD actual=$HEAD"
[[ -z "$DIRTY" ]] || { printf '%s\n' "$DIRTY"; die "working tree dirty; DO NOT git clean and DO NOT stash pop"; }

# Probe the interpreter by executing it. Merely finding py.exe/python.exe in PATH
# is insufficient on Windows because the launcher/alias can point at an uninstalled Python.
PY_CMD=()
probe_python(){
  local label="$1"
  shift
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

# Optional explicit override for recovery, followed by the repository-local venv
# already used by V31/V39, then normal Windows/Git-Bash launchers.
if [[ -n "${V69_PYTHON:-}" ]]; then
  probe_python "V69_PYTHON" "$V69_PYTHON" || true
fi

PINNED_V31="$REPO_ROOT/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
if [[ ${#PY_CMD[@]} -eq 0 && -f "$PINNED_V31" ]]; then
  probe_python "V31_PINNED_VENV" "$PINNED_V31" || true
fi

if [[ ${#PY_CMD[@]} -eq 0 ]] && command -v py.exe >/dev/null 2>&1; then
  probe_python "py.exe -3" py.exe -3 || true
fi
if [[ ${#PY_CMD[@]} -eq 0 ]] && command -v python.exe >/dev/null 2>&1; then
  probe_python "python.exe" python.exe || true
fi
if [[ ${#PY_CMD[@]} -eq 0 ]] && command -v python3 >/dev/null 2>&1; then
  probe_python "python3" python3 || true
fi
if [[ ${#PY_CMD[@]} -eq 0 ]] && command -v python >/dev/null 2>&1; then
  probe_python "python" python || true
fi

# Last-resort repository-local venv discovery. This does not install anything and
# only accepts an interpreter after the same executable probe succeeds.
if [[ ${#PY_CMD[@]} -eq 0 ]]; then
  while IFS= read -r candidate; do
    [[ -n "$candidate" ]] || continue
    if probe_python "REPO_VENV:$candidate" "$candidate"; then
      break
    fi
  done < <(find "$REPO_ROOT/runtime" -type f -path '*/.venv/Scripts/python.exe' -print 2>/dev/null | sort)
fi

[[ ${#PY_CMD[@]} -gt 0 ]] || die "no working Python 3.10+ found; broken PATH launchers were rejected rather than executed"

say "Diagnostics static gates"
"${PY_CMD[@]}" -m py_compile \
  "$REPO_ROOT/scripts/analyze_v69_forward_trade_quality.py" \
  "$REPO_ROOT/tests/test_v69_forward_trade_quality.py" \
  "$REPO_ROOT/tests/test_v69_trade_quality_runtime_static.py" \
  "$RUNNER"
"${PY_CMD[@]}" "$REPO_ROOT/tests/test_v69_forward_trade_quality.py"
"${PY_CMD[@]}" "$REPO_ROOT/tests/test_v69_trade_quality_runtime_static.py"

say "Run read-only V69 trade-quality diagnostics"
"${PY_CMD[@]}" "$RUNNER"

say "V69 trade-quality diagnostics completed"
echo "MT5_DEMO_CAN_REMAIN_RUNNING=1"
echo "V69_TRADE_QUALITY_LAUNCHER=PASS"
