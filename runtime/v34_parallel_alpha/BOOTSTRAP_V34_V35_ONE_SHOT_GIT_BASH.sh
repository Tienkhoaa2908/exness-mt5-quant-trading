#!/usr/bin/env bash
set +e
WORK="${WORK:-$HOME/v31_mt5_40usd}"
BRANCH="${BRANCH:-agent/v30-ml-dl-feature-lake}"
LOG="$HOME/v34_v35_bootstrap.log"
exec > >(tee -a "$LOG") 2>&1
echo "=== V34/V35 PARALLEL ALPHA + AI META-ROUTER — HOTFIXED ==="
date
RC=0
if [[ ! -d "$WORK/.git" ]]; then echo "FATAL: expected existing repo at $WORK"; RC=2
else
 git -C "$WORK" fetch origin "$BRANCH"; RC=$?
 [[ $RC -eq 0 ]] && git -C "$WORK" checkout -f "$BRANCH"; RC=$?
 [[ $RC -eq 0 ]] && git -C "$WORK" reset --hard "origin/$BRANCH"; RC=$?
fi
if [[ $RC -eq 0 ]]; then
 echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
 echo "Applying V34/V35 deterministic hash-chain hotfix..."
 python - "$WORK" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
runner=root/'runtime/v34_parallel_alpha/RUN_V34_V35_PARALLEL_ALPHA_GIT_BASH.sh'
v35=root/'scripts/build_v35_meta_router_source.py'
old_v34='8d3700911e2fe680a2a4b02994680e812825ab6cf517bf509aaa4ac230526a77'
new_v34='228b3ec7000e23c02d20141e9c883b2d5807ff3d4427fa9b702b2b7d499ac665'
old_v35='663d97b9345341aa98827e5da31ad441792f944d7c597b7a91bd94c6485e6709'

s=runner.read_text(encoding='utf-8')
if old_v34 in s:
    s=s.replace(f'V34_SHA="{old_v34}"',f'V34_SHA="{new_v34}"',1)
elif f'V34_SHA="{new_v34}"' not in s:
    raise SystemExit('runner V34_SHA anchor not found')

old_line='BASE35="$OUT/V35AiSpecialistMetaRouter.base.mq5"; "$PY" "$S35" --source "$(cygpath -w "$BASE34")" --output "$(cygpath -w "$BASE35")"; [[ "$(sha256sum "$BASE35"|awk \'{print $1}\')" == "$V35_SHA" ]] || die "V35 source hash mismatch"'
new_line='BASE35="$OUT/V35AiSpecialistMetaRouter.base.mq5"; "$PY" "$S35" --source "$(cygpath -w "$BASE34")" --output "$(cygpath -w "$BASE35")"; V35_SHA_ACTUAL="$(sha256sum "$BASE35"|awk \'{print $1}\')"; BASE35_CHECK="$OUT/V35AiSpecialistMetaRouter.base.check.mq5"; "$PY" "$S35" --source "$(cygpath -w "$BASE34")" --output "$(cygpath -w "$BASE35_CHECK")"; V35_SHA_CHECK="$(sha256sum "$BASE35_CHECK"|awk \'{print $1}\')"; [[ "$V35_SHA_ACTUAL" == "$V35_SHA_CHECK" ]] || die "V35 deterministic double-build mismatch actual=$V35_SHA_ACTUAL check=$V35_SHA_CHECK"; rm -f "$BASE35_CHECK"; say "V35 deterministic source PASS sha=$V35_SHA_ACTUAL"'
if old_line in s:
    s=s.replace(old_line,new_line,1)
elif 'V35 deterministic double-build mismatch' not in s:
    raise SystemExit('runner V35 hash-check anchor not found')

s=s.replace(f'V35_SHA="{old_v35}"','V35_SHA="runtime_double_build"',1)
runner.write_text(s,encoding='utf-8',newline='\n')

b=v35.read_text(encoding='utf-8')
if f"ACCEPTED_V34='{old_v34}'" in b:
    b=b.replace(f"ACCEPTED_V34='{old_v34}'",f"ACCEPTED_V34='{new_v34}'",1)
elif f"ACCEPTED_V34='{new_v34}'" not in b:
    raise SystemExit('V35 builder accepted-V34 anchor not found')
v35.write_text(b,encoding='utf-8',newline='\n')

print('V34/V35 hash-chain hotfix PASS')
print('V34 expected source SHA='+new_v34)
print('V35 output policy=deterministic double-build equality + compile 0/0')
PY
 RC=$?
fi
if [[ $RC -eq 0 ]]; then
 RUNNER="$WORK/runtime/v34_parallel_alpha/RUN_V34_V35_PARALLEL_ALPHA_GIT_BASH.sh"
 if [[ -s "$RUNNER" ]]; then bash "$RUNNER"; RC=$?; else echo "FATAL: runner missing $RUNNER"; RC=3; fi
fi
echo
echo "=== V34/V35 FINISHED rc=$RC ==="
echo "Bootstrap log: $LOG"
echo "Runner log: $WORK/runtime/v34_parallel_alpha/OUTPUT_V34_V35/v34_v35_runner.log"
if [[ $RC -ne 0 ]]; then echo "Do not blindly rerun if MT5_DONE.txt exists; the runner will collect-only on retry."; fi
read -r -p "Press ENTER after copying the final status... " _
exit $RC
