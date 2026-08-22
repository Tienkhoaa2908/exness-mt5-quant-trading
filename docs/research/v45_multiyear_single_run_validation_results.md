# V45 Multi-year Single-run Validation — Results

Date: 2026-08-22

## Policy note

V45 is historical evidence. Project-wide live policy has since been superseded by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

V45 `LIVE_AUTHORIZED=0` and tester-only markers describe the V45 build/evidence level. They are not a permanent prohibition on researching or preparing later production/live trading with real capital.

## Evidence integrity

Accepted uploaded ZIP SHA256:
`490cf399d549943cd7dfbeec79102af5e9e85ad197f6527c76376fc889072d79`

ZIP CRC: PASS. Internal bundle manifest: 23/23 listed files hash exactly.

Canonical run provenance:
- HEAD `1566a0bf0988fbab4395f5a604a0d428f4f95b97`;
- branch `agent/v45-multiyear-single-run-validation`;
- accepted V38 parent ZIP SHA `224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b`;
- accepted V38 parent source SHA `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`;
- frozen V45 source SHA `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`;
- compiler evidence `Result: 0 errors, 0 warnings`;
- exact run id `v45_multiyear_single_run_validation_v1__XAUUSDm__PERIOD_M15__2022-01-01_00-00-00__972671`.

Historical V45 markers: `tester_only=1`, native/external broker orders disabled, risk unchanged, `live_authorized=0`.

## Protocol

One continuous exact MT5 Strategy Tester run, XAUUSDm M15, 2022-01-01 -> 2026-08-01, $40 USD, 1:200, cold-start adaptive state, no 2025 state injected. First six months are warm-up; readiness evaluation covers 49 months from July 2022 through July 2026.

## Formal result

`STATUS=HOLD`

No frozen candidate passes the V45 multiyear readiness gate.

### adaptive_ewma_hl8_thr0
- evaluation compounded return +111.884951%;
- annualized +20.188040%;
- max reported MTM DD 59.9492%;
- PF 1.126242;
- worst full year -31.004730%;
- worst rolling 12m -33.779135%;
- -0.05R/trade stress +31.92613R.

### adaptive_ewma_hl8_thr0p05
- evaluation compounded return +95.603830%;
- annualized +17.857634%;
- max reported MTM DD 56.2877%;
- PF 1.136437;
- worst full year -23.050274%;
- worst rolling 12m -28.341895%;
- -0.05R/trade stress +37.83332R.

### adaptive_ewma_hl10_thr0p05 — preregistered primary
- evaluation compounded return +105.786638%;
- annualized +19.331535%;
- max reported MTM DD 56.2976%;
- 1,556 trades;
- AvgR +0.072124R;
- SumR +112.22564R;
- PF 1.132725;
- worst full year -25.749354%;
- worst rolling 12m -30.690805%;
- -0.05R/trade stress +34.42564R;
- full cold-start $40 -> $63.863453.

## Structural diagnosis

The failure was broad-regime rather than one isolated expert. The selected-source router could remain locally eligible while the broader ensemble was unhealthy.

A causal diagnostic reconstruction suggested that requiring at least 4 of 5 HL10 expert scores >=0.05 materially improved realized-R quality. That observation was diagnostic only and became the preregistered V46 breadth4 hypothesis.

## Decision

V45 formally rejects direct deployment escalation of the then-current frozen baseline family. That statement describes V45 evidence; later V46-V49 work superseded the deployment path.

Next research targeted a causal cross-expert breadth/cash gate rather than same-sample retuning. Breadth4 was preregistered as the V46 primary hypothesis.

Current project-wide live-trading research/readiness semantics are governed by ADR-049, not by the historical V45 `LIVE_AUTHORIZED=0` marker.
