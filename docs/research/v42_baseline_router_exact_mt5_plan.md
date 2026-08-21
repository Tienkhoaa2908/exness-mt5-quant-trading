# V42 Baseline Router Upgrade Lab — exact-MT5 plan

Date: 2026-08-21

## Objective

Improve the strongest verified baseline itself rather than add another offline ML overlay. The economic judge is exact MT5 Strategy Tester on the accepted V38 12-month development window, with hard control reproduction checks.

## Frozen control

- `adaptive_ewma_hl8_thr0`
- `usd40_r1p0_cent_continuous`
- 2025-08-01 -> 2026-08-01
- XAUUSDm / M15 / Model=0
- USD40 / 1:200
- accepted end 107.432645; 563 trades; risk <=1.00%/trade

The analyzer hard-checks all 12 control monthly trade counts and all 12 monthly final balances against V38 before accepting challenger economics.

## Immutable parent source

V42 must **not** reconstruct V38 through the historical V30 -> V34 -> V38 builder chain. A 2026-08-21 run exposed a stale V34 byte-hash contract: the current deterministic V34 builder produced `228b3ec7...` while an older runner expected `8bae2c56...`. Changing the accepted hash without proving source identity would be unsafe.

Instead V42 anchors directly to the accepted V38 exact-MT5 bundle:

`runtime/v38_fast_harvest/OUTPUT_V38/v38_fast_harvest_exact_mt5.zip`

Accepted outer SHA256:

`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`

The runner verifies that outer SHA, runs ZIP CRC validation, extracts the unique `V38FastHarvestLab.base.a.mq5`, checks V38 release/tester/router markers, and builds V42 twice from those exact accepted bytes. V34 specialist tape and the frozen adaptive state are still hash-verified because the accepted V38 source consumes them at runtime.

## Existing router comparators

`adaptive_ewma_hl8_thr0p05`, `adaptive_ewma_hl10_thr0p05`, `adaptive_ewma_hl12_thr0p05`, `adaptive_cp_fast5_slow20_thr0p30`.

## New bounded catalog

| Candidate | Frozen parent | Switch persistence |
|---|---|---:|
| `v42_hl8_switch15m` | HL8 thr0 | 15m |
| `v42_hl8_switch30m` | HL8 thr0 | 30m sensitivity |
| `v42_hl8_thr0p05_switch15m` | HL8 thr0.05 | 15m |
| `v42_hl10_thr0p05_switch15m` | HL10 thr0.05 | 15m |
| `v42_hl12_thr0p05_switch15m` | HL12 thr0.05 | 15m |
| `v42_cp_fast5_slow20_switch15m` | fast5/slow20 proxy | 15m |

No additional duration sweep is allowed after results.

## Mechanism

For V42 challengers only, track the most recently observed direction. The first direction is allowed. When direction flips, reject the flip bar and start a persistence clock; accept the new direction only after it persists for the configured delay. Original candidates have delay=0 and are unchanged.

This is a switching-cost/hysteresis proxy, not a new alpha signal. Expert signals, entry/exit geometry, sizing and risk remain frozen.

## Exact workflow — canonical direct runner

Runtime shell generation was removed after repeated Windows harness failures. The canonical full workflow follows the successful V32/V34/V38 direct-runner shape:

Preflight -> static tests + `bash -n`/secret scan -> V30 environment + V34 tape/state verification -> accepted V38 ZIP SHA/CRC/source extraction -> deterministic V42 double-build -> generated-MQL safety lint -> direct MetaEditor artifact checkpoint -> exact Strategy Tester -> complete manifested output checkpoint -> V38 control reproduction -> exact economics -> one SHA-manifested/CRC-verified ZIP.

Compile acceptance is **artifact-driven**, not process-return-code-driven:

- installed V42 `.mq5` must equal generated V42 source SHA;
- reusable compile checkpoint requires final `Result: 0 errors, 0 warnings` plus non-empty EX5 tied to that source;
- fresh compile polls combined log + final Result + EX5 postcondition;
- the full runner does not fail merely because a Windows launcher returned a nonzero rc if accepted artifacts prove success;
- no `set +e` under the global Bash ERR trap.

MT5 completion is also artifact-driven: new `LATEST` run id/folder and complete `monthly_summary.csv`, `trades.csv`, `manifest.txt` with tester/no-order safety markers.

## Current compiled-EA recovery

The 2026-08-21 20:12 run produced `V42BaselineRouterLab.mq5`, `.log`, and `.ex5` before the then-current fixed-deadline runner falsely reported a missing compile log. No Strategy Tester run occurred.

For that machine state, use:

`runtime/v42_baseline_router_exact_mt5/RESUME_V42_FROM_COMPILED_EA_GIT_BASH.sh`

The resume path never launches MetaEditor. It requires exact installed source SHA `142bb4fdb066de712395f32942e8ff24cbc3af0a4c9d82c88f96317d8acc248e`, compile log `Result: 0 errors, 0 warnings`, non-empty EX5, accepted V38 ZIP, V34 tape and frozen state. It then runs only Strategy Tester and uses the same hard analyzer/ZIP contract.

## Development freeze gate

All must pass: end equity >=105% of control; geo/month uplift >=+0.50pp; max DD <=control+1pp; improved return/DD; >=10 positive months; beats control >=7/12 months; worst month >=-5%; turnover <=110% of control; trades >=75% of control.

A pass only permits freezing one challenger for genuinely fresh chronological confirmation. The 15%/month target remains aspirational and cannot override the gate.
