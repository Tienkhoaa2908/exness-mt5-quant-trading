# RECOVERY PROMPT — Exness / MT5 Quant Trading System

Repository: `Tienkhoaa2908/exness-mt5-quant-trading`

## Recover current work

Current campaign branch:

`agent/v44-baseline-robustness-validation`

Base acceptance commit:

`e96262f4600e57cd956a9a78f3e717dca8b24ccb`

Do not `git clean`.

Read first:

1. `docs/handover/CURRENT_STATE.md`
2. `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`
3. `docs/research/v44_baseline_robustness_validation_plan.md`
4. `docs/adr/ADR-044-baseline-robustness-before-deployment.md`

## Safety

REAL-MONEY LIVE TRADING remains forbidden. Research risk <=1.00%/trade.
No Martingale/grid/doubling. All V44 runs are Strategy Tester only with
`AllowLiveTrading=0` and `AllowDllImport=0`.

A V44 PASS means PAPER/DEMO research readiness only. `LIVE_AUTHORIZED=0`.

## Accepted baseline

`adaptive_ewma_hl8_thr0`, USD40 continuous, exact 2025-08-01 -> 2026-08-01:

- end $107.432645;
- total +168.5816%;
- 8.58163% geometric/month;
- DD 9.9038%;
- 563 trades;
- AvgR 0.214608R;
- PF 1.500756.

Historical exact comparators frozen for V44:

- HL8 threshold0.05: $111.285257 / 8.900900% month / DD 10.4368%.
- HL10 threshold0.05: $110.025682 / 8.797648% month / DD 9.8587%.

Do not retune these on V44.

## V44 exact protocol

19 exact windows:

- annual first: 2025-08-01 -> 2026-08-01;
- 2 half-years;
- 4 sequential quarter blocks;
- 12 independent monthly windows.

Every window restarts from accepted state SHA
`5110519f2fe9722b4c13eb1e5ceec42f00bd04dd3b4f071af28349068b6097b0`.

The annual run is a hard semantic gate. It must reproduce:

- final $107.432645;
- 563 trades;
- exact 12 monthly trade counts;
- exact 12 monthly final balances.

If that gate fails, stop. Do not run the remaining 18 windows.

## Provenance

Accepted V38 ZIP SHA:
`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`.

Accepted V38 source SHA:
`4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`.

Frozen V44 source SHA:
`cfde6716916cd6adcf89cec2c7c2795ff762ea845795a9108e0247ee84e311d3`.

V44 source changes telemetry/output markers only; strategy logic/risk stay frozen.

## Recovery ladder

Follow:

`provenance -> source -> compile -> MT5 -> collection -> analysis -> packaging`

Never restart earlier stages without evidence that they failed.

- valid compile checkpoint => reuse it;
- `MT5_DONE.txt` + source run folder => collection-only;
- `DONE.txt` => that window must not rerun MT5;
- all 19 DONE + aggregate analysis => package-only recovery;
- packaging failure never justifies another Strategy Tester run.

Historical failures already encountered and fixed:

- historical V34/V38 builder hash drift -> immutable V38 ZIP;
- CP1252 decoding -> explicit UTF-8 and Python UTF-8 env;
- Bash ERR trap + `set +e` -> conditional return-code capture only;
- runtime shell patcher -> prohibited;
- MetaEditor rc/artifact race -> source SHA + final 0/0 + EX5;
- MT5 rc ambiguity -> new LATEST + complete manifested outputs;
- MSYS `<hash> *filename` -> portable Python packager;
- V42 packaging-only failure -> package completed evidence without rerunning MT5.

See `WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md` for full incident details.

## Readiness interpretation

Analyzer status:

- `PAPER_DEMO_READY`: at least one frozen candidate passes all V44 robustness
  gates.
- `HOLD`: none pass; do not weaken the gate after seeing results.

Even `PAPER_DEMO_READY` does not authorize live capital.

## Output

Upload one ZIP only:

`runtime/v44_baseline_validation/OUTPUT_V44/v44_baseline_robustness_validation.zip`

On receipt verify outer SHA, ZIP CRC, canonical internal manifest, evidence,
all 19 window manifests, annual control reproduction and aggregate readiness
metrics before making any deployment recommendation.
