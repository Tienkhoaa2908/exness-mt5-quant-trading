# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 08:00 (+07)

## User input

User requested moving beyond XAUUSD and testing Forex pairs because gold moves quickly and fast losses may be difficult to avoid structurally on that instrument.

## State read before work

Resolved exact pre-change remote HEAD on `agent/v70-exit-harvest-research`:

`bf2b30985432893dd57875dc2950819b939be606`

Read `OPERATING_PROTOCOL.md`, `CURRENT_STATE.md`, `KNOWN_FAILURES.md`, `TURN_SYNC.md` and checked exact-head CI. All six pre-change checks were completed successfully.

V70 remained closed research-only / no exit promotion. Frozen V69 safety/identity remained unchanged.

## Research decision

Create a separate cross-symbol successor rather than mutating frozen V69 or retuning XAU thresholds.

New branch:

`agent/v71-fx-portability-research`

V71 asks a narrow question: does the exact V69 LONG setup/entry/real-exit logic transfer to major FX symbols when nominal lot and cash-risk budget are held constant?

The first pass intentionally performs **no symbol-specific retuning**. This prevents optimization leakage and makes the comparison interpretable.

## Default campaign

One compile, five full-period real-tick Strategy Tester passes:

1. `XAUUSDm` — contemporaneous control;
2. `EURUSDm`;
3. `GBPUSDm`;
4. `USDJPYm`;
5. `AUDUSDm`.

Each pass covers `2025.09.01 -> 2026.06.01`, M15, LONG only, Model=4.

V69 cash/geometry contract remains unchanged:

- lot 0.01;
- stop-risk band $0.85-$1.10;
- emergency $1.20;
- target $3.50;
- risk/spread >=4;
- separation $1.30;
- confirm age >=30 seconds.

No V70 TIERED exit is activated. SHORT remains disabled. REAL authorization remains false.

## Code implemented

Added:

- `scripts/build_v71_fx_portability_source.py`;
- `scripts/analyze_v71_fx_portability.py`;
- `runtime/v71_fx_portability_research/RUN_V71_FX_PORTABILITY_RESEARCH.py`;
- `runtime/v71_fx_portability_research/RUN_V71_FX_PORTABILITY_RESEARCH_GIT_BASH.sh`;
- `tests/test_v71_fx_portability_research.py`;
- `.github/workflows/v71_fx_portability_quality.yml`.

Builder regression normalizes V71 metadata back to V69 and requires exact source equality with `parent.transform(1)`. Therefore V71 cannot silently change decision semantics while claiming portability.

The runner uses one full-period pass per symbol instead of monthly tester passes. Analyzer reconstructs month-level PnL afterward and reports per symbol:

- trades/wins/losses;
- net/PF/realized DD;
- explicit costs;
- fast losses <=60 seconds and share;
- positive/negative/flat month count;
- month breakdown;
- event funnel;
- top evaluation rejects;
- FX ranking with XAU kept as same-run control.

`V71_FX_SYMBOLS` can override the default comma-separated symbol list if broker naming differs, but XAU control is automatically retained.

## CI status during implementation

At code checkpoint `a6782f7334190cc678760a0cb54e624f64757e78`, the new `v71-fx-portability-static` workflow completed successfully. Legacy V69/V70 checks observed at that checkpoint had no failures; final exact-head CI must still be rechecked after handover synchronization.

## Safety

`V71_V69_LONG_STRATEGY_EQUIVALENT=1`
`V71_FX_ENTRY_RETUNE=0`
`V71_FX_EXIT_RETUNE=0`
`SHORT_ENABLED=0`
`REAL_MONEY_AUTHORIZED=0`

## Next operator action

After final exact-head CI is fully green:

1. close MT5 and MetaEditor;
2. fast-forward to the final V71 HEAD;
3. run the single V71 launcher;
4. return the final `V71_FX_RESULTS`, `V71_FX_RANKING`, `V71_FX_BY_MONTH`, `V71_FX_EVENT_FUNNEL` and PASS markers.

If a symbol such as `EURUSDm` is not available on the broker account, classify it as broker symbol naming/availability only and adjust the symbol list. Do not retune strategy thresholds to solve a symbol-name failure.
