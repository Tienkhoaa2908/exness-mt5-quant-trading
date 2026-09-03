# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 14:15 (+07)

## User input

Operator completed the V71 five-symbol direct-portability run at exact evidence HEAD:

`82994371d4717ed947a0d9e8057617bf96ea8c8b`

The run compiled 0/0 and completed all five real-tick passes for XAUUSDm, EURUSDm, GBPUSDm, USDJPYm and AUDUSDm. User then asked whether richer ZIP evidence could be exported instead of relying on giant pasted terminal output.

## State read before work

Fresh-resolved remote HEAD before this turn:

`82994371d4717ed947a0d9e8057617bf96ea8c8b`

Read `OPERATING_PROTOCOL.md`, `CURRENT_STATE.md`, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, inspected the current V71 runner/analyzer/builder and verified all seven exact-head checks were completed successfully.

## V71 run evidence received

Source SHA256:

`32615744d81e48be9f95638a8062e590b690bf1ec56437dc3293fda4bb202e7c`

EX5 SHA256:

`69896c6b330c6dd4bbb13acf7ee27ea1efccbe7f7cc47b64f582ea02db0c20b5`

`V71_V69_LONG_STRATEGY_EQUIVALENT=1`, no entry/exit retune, SHORT disabled, REAL false.

Economic screen:

- XAUUSDm: 24 trades / 10W / 14L / +$6.44 / PF 1.417098 / DD $3.65 / fast-loss 10/14.
- EURUSDm: 8 / 4W / 4L / +$4.55 / PF 2.060606 / DD $3.30 / fast-loss 0/4.
- AUDUSDm: 7 / 3W / 4L / +$1.29 / PF 1.305687 / DD $2.10 / fast-loss 0/4.
- USDJPYm: 6 / 2W / 4L / +$0.21 / PF 1.049065 / DD $3.28 / fast-loss 0/4.
- GBPUSDm: 19 / 3W / 16L / -$14.43 / PF 0.171166 / DD $16.32 / fast-loss 0/16.

Interpretation locked for now:

- XAU <=60-second loss behavior is not universal across the tested FX pairs.
- Slower loss timing alone is not edge; GBPUSD is a strong negative control.
- EURUSD is the strongest FX candidate but only eight reused-development trades, so no deployment or semantic promotion is justified.

## Code action this turn

Added packaging-only evidence tooling. It reuses the already-completed V71 output and does not reopen or rerun Strategy Tester:

- `scripts/package_v71_fx_evidence.py`;
- `runtime/v71_fx_portability_research/PACK_V71_FX_EVIDENCE_GIT_BASH.sh`;
- `tests/test_v71_fx_evidence_packaging.py`;
- V71 CI extended to compile/test the packer and shell launcher.

Package integrity contract:

- exact packaging HEAD and original evidence HEAD are recorded separately;
- existing generated source must match the current V71 builder exactly and retain V69 LONG strategy equivalence;
- analysis protocol/control/safety flags must match;
- all symbols require raw deals/events/entry-eval evidence;
- raw entry/exit deal pairs must equal analyzed trade counts;
- manifest includes SHA256 and byte size for every packed file;
- EX5 binaries are intentionally excluded.

Outputs:

- `V71_FX_EVIDENCE_FULL.zip`;
- `V71_FX_EVIDENCE_CORE.zip`;
- one `V71_FX_EVIDENCE_<SYMBOL>.zip` per tested symbol;
- `V71_FX_EVIDENCE_MANIFEST.json`.

The full package contains the richest raw telemetry. The per-symbol packages allow EURUSD/GBPUSD/XAU comparison without uploading the whole campaign if size is inconvenient.

## CI status

Packaging code checkpoint `8eb4bb38eb9130b1620307585585c77d92e59cdc` completed all seven checks successfully before handover synchronization.

Final exact-head CI must be checked again after these handover commits.

## Safety

`V71_V69_LONG_STRATEGY_EQUIVALENT=1`
`V71_FX_ENTRY_RETUNE=0`
`V71_FX_EXIT_RETUNE=0`
`SHORT_ENABLED=0`
`REAL_MONEY_AUTHORIZED=0`

## Next operator action

After final exact-head CI is green, fast-forward to the final V71 HEAD and run the packaging-only launcher with:

- `V71_FX_EXPECTED_HEAD=<final packaging HEAD>`;
- `V71_FX_EVIDENCE_HEAD=82994371d4717ed947a0d9e8057617bf96ea8c8b`.

MT5 and MetaEditor may remain open because packaging touches only retained files. Do not rerun the five Strategy Tester passes.

Return/upload `V71_FX_EVIDENCE_FULL.zip`. If it is too large, upload at minimum the EURUSDm, GBPUSDm and XAUUSDm symbol ZIPs.
