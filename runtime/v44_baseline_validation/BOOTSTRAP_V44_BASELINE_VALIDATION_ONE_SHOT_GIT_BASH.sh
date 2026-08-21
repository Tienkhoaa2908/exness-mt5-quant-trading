#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

WORK="${WORK:-$HOME/v31_mt5_40usd}"
BRANCH="${BRANCH:-agent/v44-baseline-robustness-validation}"
REMOTE="${REMOTE:-origin}"
REMOTE_REF="refs/remotes/$REMOTE/$BRANCH"
RUNNER="$WORK/runtime/v44_baseline_validation/RUN_V44_BASELINE_VALIDATION_EXACT_MT5_GIT_BASH.sh"
PACKAGE_ONLY="$WORK/runtime/v44_baseline_validation/PACKAGE_V44_EXISTING_OUTPUT_GIT_BASH.sh"
OUT="$WORK/runtime/v44_baseline_validation/OUTPUT_V44"
CP="$OUT/checkpoints"

WINDOW_TAGS=(
y01_2025_08_2026_08
h01_2025_08_2026_02
h02_2026_02_2026_08
q01_2025_08_11
q02_2025_11_2026_02
q03_2026_02_05
q04_2026_05_08
m01_2025_08
m02_2025_09
m03_2025_10
m04_2025_11
m05_2025_12
m06_2026_01
m07_2026_02
m08_2026_03
m09_2026_04
m10_2026_05
m11_2026_06
m12_2026_07
)

[[ -d "$WORK/.git" ]] || { echo "FATAL: Git checkout missing: $WORK" >&2; exit 1; }
echo "=== V44 BASELINE ROBUSTNESS VALIDATION — EXACT MT5 ==="
echo "REAL-MONEY LIVE TRADING remains FORBIDDEN."
echo "A readiness PASS is PAPER/DEMO only."

git -C "$WORK" fetch --no-tags "$REMOTE" "+refs/heads/$BRANCH:$REMOTE_REF"
git -C "$WORK" show-ref --verify --quiet "$REMOTE_REF" || { echo "FATAL: remote ref missing $REMOTE_REF" >&2; exit 1; }
git -C "$WORK" checkout -B "$BRANCH" "$REMOTE_REF"
git -C "$WORK" reset --hard "$REMOTE_REF"

echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
echo "BRANCH=$(git -C "$WORK" branch --show-current)"
echo "PYTHONUTF8=$PYTHONUTF8 PYTHONIOENCODING=$PYTHONIOENCODING"

[[ -s "$RUNNER" ]] || { echo "FATAL: V44 direct runner missing: $RUNNER" >&2; exit 1; }
[[ -s "$PACKAGE_ONLY" ]] || { echo "FATAL: V44 package-only recovery missing: $PACKAGE_ONLY" >&2; exit 1; }
bash -n "$RUNNER"
bash -n "$PACKAGE_ONLY"

cd "$WORK"
if bash "$RUNNER"; then
  exit 0
else
  rc=$?
fi

# Never mask a research/runtime failure. Package-only recovery is allowed only
# after all 19 exact checkpoints and the aggregate analysis already exist.
all_done=1
[[ -s "$OUT/V44_EVIDENCE.txt" && -s "$OUT/v44_baseline_validation_analysis.json" && -s "$OUT/v44_window_metrics.csv" ]] || all_done=0
for tag in "${WINDOW_TAGS[@]}"; do
  [[ -s "$CP/$tag/DONE.txt" && -s "$CP/$tag/monthly_summary.csv" && -s "$CP/$tag/trades.csv" && -s "$CP/$tag/manifest.txt" ]] || all_done=0
done
if [[ "$all_done" -eq 1 ]]; then
  echo "V44 runner returned rc=$rc after completed exact evidence; attempting package-only recovery."
  echo "MT5 WILL NOT RERUN."
  bash "$PACKAGE_ONLY"
  exit 0
fi
exit "$rc"
