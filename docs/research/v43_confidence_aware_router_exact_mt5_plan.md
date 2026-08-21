# V43 Confidence-Aware Router — exact MT5 plan

Date: 2026-08-21
Status: preregistered development research

## Objective

Improve the accepted causal baseline router without adding a separate ML overlay or repeating V42 global time hysteresis. The economic judge remains exact MetaTrader 5 Strategy Tester because router decisions change realized-R feedback and therefore future routing state.

## Frozen control and evidence

Control: `adaptive_ewma_hl8_thr0` / `usd40_r1p0_cent_continuous`.

Exact accepted V38/V42 reproduction:

- XAUUSDm / M15 / Model=0;
- 2025-08-01 -> 2026-08-01;
- USD40 / 1:200;
- end `$107.432645`;
- geometric/month `8.58163%`;
- max DD `9.9038%`;
- 563 trades;
- risk ceiling <=1.00% per trade.

Accepted immutable V38 ZIP SHA256:

`224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`

V43 source must be derived directly from the unique accepted `V38FastHarvestLab.base.a.mq5` member, never via historical V34/V38 source reconstruction.

## Why V43

V42 exact MT5 showed that broad direction-switch delays improved AvgR/PF/DD but reduced participation enough to lower compounded return. V42 = HOLD. The historical threshold routers remained more promising:

- `adaptive_ewma_hl8_thr0p05`: `$111.285257`, `8.900900%/month`;
- `adaptive_ewma_hl10_thr0p05`: `$110.025682`, `8.797648%/month`, DD `9.8587%`.

V43 therefore changes only ambiguous cross-direction routing. It does not impose a time delay on ordinary direction changes.

## Frozen V43 catalog

Exactly four challengers are preregistered:

| Candidate | Frozen parent | Directional score margin |
|---|---|---:|
| `v43_hl8_thr0p05_conf0p05` | HL8 threshold0.05 | 0.05R |
| `v43_hl10_thr0p05_conf0p05` | HL10 threshold0.05 | 0.05R |
| `v43_hl8_thr0p05_conf0p10` | HL8 threshold0.05 | 0.10R |
| `v43_hl10_thr0p05_conf0p10` | HL10 threshold0.05 | 0.10R |

No same-window margin retuning. Do not add 0.025/0.075/0.15/0.20 after seeing results. Do not add a time-hysteresis rescue arm.

Frozen generated source SHA256:

`487f2fffdfb7a348bd697fc0a8e6682d39a83f06b1a09453f7a194d5f5000c8a`

## Mechanism

For each V43 candidate only:

1. score every currently active expert using the same causal realized-R EWMA score and the same parent minimum score;
2. identify the strongest active LONG expert and strongest active SHORT expert;
3. if only one direction is active, select it immediately;
4. if both directions are active and their top-score gap is at least the fixed candidate margin, select the leader immediately;
5. if both are active and the gap is below the margin, prefer the candidate's currently active incumbent direction if one exists;
6. if there is an exact tie and no incumbent, abstain for that decision;
7. once a direction is chosen, preserve the existing expert selection/entry/exit/risk machinery.

This is a confidence/credit allocation rule, not a new alpha signal. `v43_global_time_hysteresis=0` is mandatory.

## Frozen invariants

V43 does not change:

- the five expert signal definitions;
- stop/TP geometry;
- position sizing;
- USD40 continuous accounting;
- risk ceiling;
- tester-only / no-order safety controls;
- parent EWMA half-life and minimum score.

V38 heavy M1/M15 telemetry remains disabled for runtime efficiency; monthly summary, trade ledger and tester manifest are mandatory.

## Exact-MT5 gates

Before considering any challenger, analyzer must exactly reproduce the accepted control monthly trade-count vector and monthly final-balance vector.

### Control material-uplift gate

All must pass:

- ending equity >=105% of control;
- geometric/month uplift >=+0.50 percentage points;
- max DD <= control +1.00pp;
- return/DD improved;
- >=10 positive months;
- beats control in >=7/12 months;
- worst month >=-5%;
- turnover <=110% of control;
- trades >=75% of control.

### Frozen-parent incremental gate

A V43 candidate must also improve its own HL8/HL10 threshold0.05 parent:

- ending equity > parent;
- geometric/month > parent;
- return/DD not worse than parent;
- max DD <= parent +0.50pp;
- beats parent in >=7/12 months;
- turnover <=105% of parent;
- trades >=90% of parent.

A candidate must pass both gates. A pass only freezes the policy for genuinely fresh chronological confirmation; it is not live approval.

## Runtime/recovery contract

V43 inherits the V42 failure playbook as mandatory engineering controls:

- immutable V38 parent;
- explicit UTF-8 on Windows and no CP1252 dependence;
- no `set +e` under a global ERR trap;
- no runtime patcher/self-modifying shell;
- compile artifact checkpoint before deleting a valid EX5/log;
- MetaEditor success = exact source + final 0/0 compiler result + EX5, not launcher rc;
- MT5 success = new LATEST + complete manifested outputs, not launcher rc;
- portable Python SHA/ZIP packaging, not parsing MSYS `sha256sum` rendering;
- package-only recovery if exact MT5 and analysis already finished;
- do not rerun MT5 when only packaging failed;
- no `git clean` because untracked evidence/checkpoints/compiled artifacts may be required.

See `docs/handover/WINDOWS_RUNTIME_FAILURE_PLAYBOOK.md`.
