#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
OUT="$ROOT/OUTPUT_V44"
CP="$OUT/checkpoints"
BUNDLE="$OUT/bundle"
ZIP="$OUT/v44_baseline_robustness_validation.zip"
PACKAGER="$REPO_ROOT/scripts/package_research_bundle_portable.py"
PY="$REPO_ROOT/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"

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

die(){ echo "FATAL: $*" >&2; exit 1; }
[[ -x "$PY" ]] || die "pinned Python missing: $PY"
[[ -s "$PACKAGER" ]] || die "portable packager missing: $PACKAGER"
for f in V44_EVIDENCE.txt v44_baseline_validation_analysis.json v44_window_metrics.csv; do
  [[ -s "$OUT/$f" ]] || die "completed V44 analysis artifact missing: $OUT/$f"
done
for tag in "${WINDOW_TAGS[@]}"; do
  for f in DONE.txt monthly_summary.csv trades.csv manifest.txt WINDOW.txt; do
    [[ -s "$CP/$tag/$f" ]] || die "completed checkpoint missing: $tag/$f"
  done
  grep -Fq 'tester_only=1' "$CP/$tag/manifest.txt" || die "$tag tester_only marker missing"
  grep -Fq 'native_broker_orders=0' "$CP/$tag/manifest.txt" || die "$tag native-order marker mismatch"
  grep -Fq 'external_broker_orders=0' "$CP/$tag/manifest.txt" || die "$tag external-order marker mismatch"
  grep -Fq 'v44_live_authorized=0' "$CP/$tag/manifest.txt" || die "$tag live-authorized marker mismatch"
done

mkdir -p "$BUNDLE"
rm -rf "$BUNDLE"/*
for f in \
  "$OUT/V44_EVIDENCE.txt" \
  "$OUT/v44_baseline_validation_runner.log" \
  "$OUT/V44BaselineValidationLab.compile.txt" \
  "$OUT/V38FastHarvestLab.accepted_parent.mq5" \
  "$OUT/V44BaselineValidationLab.base.a.mq5" \
  "$OUT/v44_baseline_validation_analysis.json" \
  "$OUT/v44_window_metrics.csv" \
  "$OUT/v44_annual_preflight.json" \
  "$OUT/v44_annual_preflight.csv"; do
  [[ -s "$f" ]] && cp -f "$f" "$BUNDLE/$(basename "$f")"
done
for tag in "${WINDOW_TAGS[@]}"; do
  d="$CP/$tag"
  for f in WINDOW.txt LATEST.txt SOURCE_RUN_FOLDER.txt manifest.txt monthly_summary.csv trades.csv; do
    [[ -s "$d/$f" ]] && cp -f "$d/$f" "$BUNDLE/${tag}__${f}" || true
  done
done
for f in \
  "$REPO_ROOT/scripts/build_v44_baseline_validation_source.py" \
  "$REPO_ROOT/scripts/analyze_v44_baseline_validation.py" \
  "$REPO_ROOT/scripts/package_research_bundle_portable.py" \
  "$REPO_ROOT/tests/test_v44_baseline_validation_static.py" \
  "$ROOT/RUN_V44_BASELINE_VALIDATION_EXACT_MT5_GIT_BASH.sh" \
  "$ROOT/BOOTSTRAP_V44_BASELINE_VALIDATION_ONE_SHOT_GIT_BASH.sh" \
  "$0"; do
  [[ -s "$f" ]] && cp -f "$f" "$BUNDLE/$(basename "$f")"
done

"$PY" -m py_compile "$PACKAGER"
"$PY" "$PACKAGER" --bundle "$(cygpath -w "$BUNDLE")" --output "$(cygpath -w "$ZIP")"

echo "V44 PACKAGE-ONLY RECOVERY DONE"
echo "MT5 WAS NOT RERUN"
echo "LIVE_AUTHORIZED=0"
echo "UPLOAD THIS ONE ZIP:"
cygpath -w "$ZIP"
sha256sum "$ZIP"
