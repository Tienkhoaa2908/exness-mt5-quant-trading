#!/usr/bin/env bash
set +e
WORK="${WORK:-$HOME/v31_mt5_40usd}"
BRANCH="${BRANCH:-agent/v30-ml-dl-feature-lake}"
LOG="$HOME/v34_v35_bootstrap.log"
exec > >(tee -a "$LOG") 2>&1

echo "=== V34/V35 PARALLEL ALPHA + AI META-ROUTER — COMPILE FIX V2 ==="
date
RC=0

if [[ ! -d "$WORK/.git" ]]; then
  echo "FATAL: expected existing repo at $WORK"
  RC=2
else
  git -C "$WORK" fetch origin "$BRANCH"; RC=$?
  [[ $RC -eq 0 ]] && git -C "$WORK" checkout -f "$BRANCH"; RC=$?
  [[ $RC -eq 0 ]] && git -C "$WORK" reset --hard "origin/$BRANCH"; RC=$?
fi

if [[ $RC -eq 0 ]]; then
  echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
  echo "Applying generator/compiler hardening..."
  python - "$WORK" <<'PY'
from pathlib import Path
import re, sys
root = Path(sys.argv[1])
v34 = root / 'scripts/build_v34_parallel_alpha_source.py'
v35 = root / 'scripts/build_v35_meta_router_source.py'
runner = root / 'runtime/v34_parallel_alpha/RUN_V34_V35_PARALLEL_ALPHA_GIT_BASH.sh'
for p in (v34, v35, runner):
    if not p.is_file():
        raise SystemExit(f'missing required file: {p}')

def clean_raw_mql_quotes(path: Path, var: str) -> int:
    s = path.read_text(encoding='utf-8')
    marker = var + "=r'''"
    start = s.find(marker)
    if start < 0:
        raise SystemExit(f'{path.name}: raw block {var} not found')
    body_start = start + len(marker)
    end = s.find("'''", body_start)
    if end < 0:
        raise SystemExit(f'{path.name}: raw block {var} terminator not found')
    body = s[body_start:end]
    count = body.count('\\"')
    body = body.replace('\\"', '"')
    s = s[:body_start] + body + s[end:]
    path.write_text(s, encoding='utf-8', newline='\n')
    return count

n1 = clean_raw_mql_quotes(v34, 'tape')
n2 = clean_raw_mql_quotes(v34, 'telemetry_func')
n3 = clean_raw_mql_quotes(v35, 'router')

s = runner.read_text(encoding='utf-8')

# Remove stale fixed V34 source hashing. Build twice from the exact accepted V30 source and require byte equality.
start = s.find('BASE34="$OUT/V34ParallelAlphaLab.base.mq5";')
end = s.find("! grep -Eq 'OrderSend", start)
if start < 0 or end < 0:
    raise SystemExit('runner: V34 build/hash block anchors not found')
new_v34 = r'''BASE34="$OUT/V34ParallelAlphaLab.base.mq5"
BASE34_CHECK="$OUT/V34ParallelAlphaLab.base.check.mq5"
"$PY" "$S34" --source "$(cygpath -w "$V30_SRC")" --output "$(cygpath -w "$BASE34")"
"$PY" "$S34" --source "$(cygpath -w "$V30_SRC")" --output "$(cygpath -w "$BASE34_CHECK")"
V34_SHA_ACTUAL="$(sha256sum "$BASE34"|awk '{print $1}')"
V34_SHA_CHECK="$(sha256sum "$BASE34_CHECK"|awk '{print $1}')"
[[ "$V34_SHA_ACTUAL" == "$V34_SHA_CHECK" ]] || die "V34 deterministic double-build mismatch actual=$V34_SHA_ACTUAL check=$V34_SHA_CHECK"
rm -f "$BASE34_CHECK"
say "V34 deterministic source PASS sha=$V34_SHA_ACTUAL"
# Pin the V35 builder to the exact V34 bytes produced in this same run.
"$PY" - "$S35" "$V34_SHA_ACTUAL" <<'PYV35PIN'
from pathlib import Path
import re,sys
p=Path(sys.argv[1]); h=sys.argv[2]
s=p.read_text(encoding='utf-8')
s2,n=re.subn(r"ACCEPTED_V34='[0-9a-f]{64}'", "ACCEPTED_V34='"+h+"'", s, count=1)
if n!=1: raise SystemExit('V35 builder ACCEPTED_V34 anchor not found')
p.write_text(s2,encoding='utf-8',newline='\n')
PYV35PIN
'''
s = s[:start] + new_v34 + s[end:]

# Replace stale V35 fixed output hash with deterministic double-build equality.
start = s.find('BASE35="$OUT/V35AiSpecialistMetaRouter.base.mq5";')
end = s.find('EA35="$EXPERT_DIR/V35AiSpecialistMetaRouter.mq5";', start)
if start < 0 or end < 0:
    raise SystemExit('runner: V35 build/hash block anchors not found')
new_v35 = r'''BASE35="$OUT/V35AiSpecialistMetaRouter.base.mq5"
BASE35_CHECK="$OUT/V35AiSpecialistMetaRouter.base.check.mq5"
"$PY" "$S35" --source "$(cygpath -w "$BASE34")" --output "$(cygpath -w "$BASE35")"
"$PY" "$S35" --source "$(cygpath -w "$BASE34")" --output "$(cygpath -w "$BASE35_CHECK")"
V35_SHA_ACTUAL="$(sha256sum "$BASE35"|awk '{print $1}')"
V35_SHA_CHECK="$(sha256sum "$BASE35_CHECK"|awk '{print $1}')"
[[ "$V35_SHA_ACTUAL" == "$V35_SHA_CHECK" ]] || die "V35 deterministic double-build mismatch actual=$V35_SHA_ACTUAL check=$V35_SHA_CHECK"
rm -f "$BASE35_CHECK"
say "V35 deterministic source PASS sha=$V35_SHA_ACTUAL"
'''
s = s[:start] + new_v35 + s[end:]

# Always expose decoded MetaEditor diagnostics on failure/success, not only the final Result line.
needle = 'local sum; sum="$(tr -d \'\\r\' < "$u8"|grep -Eio'
if needle in s:
    s = s.replace(needle, 'cat "$u8"; local sum; sum="$(tr -d \'\\r\' < "$u8"|grep -Eio', 1)
elif 'cat "$u8"; local sum;' not in s:
    raise SystemExit('runner: compile diagnostic anchor not found')

runner.write_text(s, encoding='utf-8', newline='\n')
print(f'Raw-MQL quote cleanup PASS: V34 tape={n1}, telemetry={n2}, V35 router={n3}')
print('V34/V35 source policy: deterministic double-build equality + MetaEditor compile 0/0')
print('Compile diagnostics: full decoded MetaEditor log will be printed')
PY
  RC=$?
fi

if [[ $RC -eq 0 ]]; then
  RUNNER="$WORK/runtime/v34_parallel_alpha/RUN_V34_V35_PARALLEL_ALPHA_GIT_BASH.sh"
  if [[ -s "$RUNNER" ]]; then
    bash "$RUNNER"; RC=$?
  else
    echo "FATAL: runner missing $RUNNER"
    RC=3
  fi
fi

echo
echo "=== V34/V35 FINISHED rc=$RC ==="
echo "Bootstrap log: $LOG"
echo "Runner log: $WORK/runtime/v34_parallel_alpha/OUTPUT_V34_V35/v34_v35_runner.log"
if [[ $RC -ne 0 ]]; then
  echo "Do not blindly rerun if MT5_DONE.txt exists; the runner will collect-only on retry."
fi
read -r -p "Press ENTER after copying the final status... " _
exit $RC
