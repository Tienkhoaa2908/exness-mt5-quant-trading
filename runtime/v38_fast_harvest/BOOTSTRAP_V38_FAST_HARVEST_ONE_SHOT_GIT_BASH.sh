#!/usr/bin/env bash
set +e

WORK="${WORK:-$HOME/v31_mt5_40usd}"
BRANCH="${BRANCH:-agent/v30-ml-dl-feature-lake}"
LOG="$HOME/v38_fast_harvest_bootstrap.log"
exec > >(tee -a "$LOG") 2>&1

echo "=== V38 FAST HARVEST LAB — EXACT MT5 ==="
date
echo "Preserves V34 baseline/specialists, V32 keep60 research, and V36 sequence-AI evidence."
echo "Adds exit-only fast-harvest clones + M1/tick telemetry. LIVE orders remain forbidden."

RC=0
if [[ ! -d "$WORK/.git" ]]; then
  echo "FATAL: expected repository at $WORK"
  RC=2
else
  git -C "$WORK" fetch origin "$BRANCH"; RC=$?
  [[ $RC -eq 0 ]] && git -C "$WORK" checkout -f "$BRANCH"; RC=$?
  [[ $RC -eq 0 ]] && git -C "$WORK" reset --hard "origin/$BRANCH"; RC=$?
fi

if [[ $RC -eq 0 ]]; then
  echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
  echo "Hardening legacy V34 generator to exact accepted 8bae semantics..."
  python - "$WORK" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/'scripts/build_v34_parallel_alpha_source.py'
if not p.is_file(): raise SystemExit(f'missing {p}')
s=p.read_text(encoding='utf-8')

def rawify(needle):
    global s
    pos=s.find(needle)
    if pos<0: raise SystemExit(f'V34 hardening needle missing: {needle}')
    start=s.rfind("'''",0,pos)
    end=s.find("'''",pos)
    if start<0 or end<0: raise SystemExit(f'V34 triple block missing for {needle}')
    if start>0 and s[start-1] in ('r','R'):
        return 0
    s=s[:start]+'r'+s[start:]
    return 1

r1=rawify('input string InpV34AlphaTapeFile')
r2=rawify('v34_parallel_alpha_lab=1')
old=r'string V34IntraTradeFile(){ return g_run_folder+"\intra_trade_m15.csv"; }'
new=r'string V34IntraTradeFile(){ return g_run_folder+"\\intra_trade_m15.csv"; }'
if old in s:
    s=s.replace(old,new,1); rt=1
elif new in s:
    rt=0
else:
    raise SystemExit('V34 telemetry path anchor missing')
p.write_text(s,encoding='utf-8',newline='\n')
print(f'V34 accepted-source hardening PASS raw_input={r1} raw_manifest={r2} telemetry={rt}')
PY
  RC=$?
fi

if [[ $RC -eq 0 ]]; then
  RUNNER="$WORK/runtime/v38_fast_harvest/RUN_V38_FAST_HARVEST_EXACT_MT5_GIT_BASH.sh"
  if [[ ! -s "$RUNNER" ]]; then
    echo "FATAL: V38 runner missing: $RUNNER"
    RC=3
  else
    echo "Hardening V38 static-test runner: pytest package is optional..."
    python - "$RUNNER" <<'PYRUNNER'
from pathlib import Path
import sys
p=Path(sys.argv[1])
s=p.read_text(encoding='utf-8')
old='"$PY" -m pytest -q "$REPO_ROOT/tests/test_v38_fast_harvest_static.py"'
new='"$PY" "$REPO_ROOT/tests/test_v38_fast_harvest_static.py"'
if old in s:
    s=s.replace(old,new,1)
    changed=1
elif new in s:
    changed=0
else:
    raise SystemExit('V38 pytest runner anchor missing')
p.write_text(s,encoding='utf-8',newline='\n')
print(f'V38 pytest-free static-test patch PASS changed={changed}')
PYRUNNER
    RC=$?
  fi
fi

if [[ $RC -eq 0 ]]; then
  RUNNER="$WORK/runtime/v38_fast_harvest/RUN_V38_FAST_HARVEST_EXACT_MT5_GIT_BASH.sh"
  if ! bash -n "$RUNNER"; then
    echo "FATAL: bash -n failed for V38 runner"
    RC=4
  else
    bash "$RUNNER"
    RC=$?
  fi
fi

echo
echo "=== V38 FINISHED rc=$RC ==="
echo "Bootstrap log: $LOG"
if [[ $RC -ne 0 ]]; then
  echo "If OUTPUT_V38/checkpoints/v38_fast_harvest/MT5_DONE.txt exists, do not rerun tester manually."
  echo "The V38 runner is checkpointed and will recover collection/analysis without duplicating MT5."
fi
read -r -p "Press ENTER after copying the final status... " _
exit $RC
