# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 17:35 (+07)

## User input

User asked for a reusable prompt to give another LLM so it can independently diagnose the trading system and research workflow, propose technical and research-process improvements, and explicitly inspect the GitHub repository rather than relying on a chat summary.

## State read before work

Fresh-resolved remote HEAD on `agent/v72-eurusd-independent-validation`:

`c92836f194a6cf7590d5a9cace057b75c5c64c1d`

Read `OPERATING_PROTOCOL.md`, `CURRENT_STATE.md`, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent commits and exact-head CI. Exact-head CI had 8 checks, all completed success.

## Prompt-design decision

The external-LLM prompt should require repo-first recovery and explicitly distinguish source-of-truth evidence from model inference. It should instruct the other model to:

1. access `Tienkhoaa2908/exness-mt5-quant-trading` directly;
2. fresh-resolve the active branch and current remote HEAD rather than trusting a pasted SHA;
3. read `docs/handover/OPERATING_PROTOCOL.md`, `CURRENT_STATE.md`, `KNOWN_FAILURES.md`, and `TURN_SYNC.md` first;
4. inspect recent commits and exact-head CI;
5. then inspect frozen V69 source lineage, V70 exit-harvest diagnostics, V71 FX portability code/evidence, and V72 EURUSD untouched-validation code/evidence;
6. separate strategy/economic logic, execution/broker transport, and harness/observability defects;
7. critique both strategy design and research methodology, including overfitting risk, evidence reuse, sample size, regime concentration, cross-symbol portability, drawdown criteria, operator cost, tester turnaround time, and prospective validation design;
8. propose a prioritized low-operator-cost research plan that reuses accepted raw evidence before requesting new MT5 real-tick runs;
9. avoid post-hoc rescue tuning on the consumed V72 holdout;
10. keep SHORT disabled and REAL unauthorized unless separately researched and explicitly approved.

The prompt should ask for concrete repository paths/files inspected, claims tied to commits/evidence, alternative hypotheses, falsification tests, and a ranked action plan rather than generic trading advice.

## Settled project state that the external LLM should discover from the repo

- Frozen V69 is development-only XAU LONG research with accepted headline `24 trades / 10W / 14L / +$7.14 / PF 1.462 / DD $3.34`.
- V70 did not justify promoting a new real-exit policy.
- V71 direct portability showed strong symbol dispersion: EURUSD was the best small-sample FX screen, GBPUSD failed badly, AUDUSD was mildly positive, USDJPY near flat.
- V72 untouched EURUSD earlier-period validation produced `23 trades / +$4.11 / PF 1.250457 / DD $10.23` and formally failed the preregistered DD gate.
- Further operator-heavy MT5 campaigns are paused by default; next research should start offline/cheap using existing evidence.

These facts should be verified by the external LLM from the repository, not merely accepted from the prompt.

## Safety

`NEXT_MT5_TESTER_ACTION=PAUSED`
`SHORT_ENABLED=0`
`REAL_MONEY_AUTHORIZED=0`

## Next action

No operator command is required. User will copy the prepared diagnostic/research-review prompt into another LLM. That model should inspect GitHub directly and return an independent critique and prioritized research plan.
