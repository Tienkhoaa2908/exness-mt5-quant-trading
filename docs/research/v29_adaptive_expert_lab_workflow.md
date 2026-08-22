# V29 Adaptive Expert Lab — workflow

## Policy note

V29 was a historical Strategy Tester workflow. Current project-wide live policy is governed by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

V29's tester-only/no-native-order contract was phase-specific and does not prohibit later production/live research or real-capital deployment engineering.

## Active historical distribution

`v29_3_distribution_hardening` wrapped the frozen V29.2 strategy payload.

Pinned decoded payload SHA-256:
`d469f527cb96197ed265c1e1a62c4d3f3f2d220efca0f44fb4478e928f68f334`.

V29.3 did not change catalog/risk/exit/adaptive logic.

## Pre-Windows gates

Clean checkout verified exact archive hash, helper definitions, standard MQL structure members, tester/safety markers, absence of native-order path, analyzer compile, template safety, chunk schedule, pytest and secret scan.

## Windows

Root V29.3 wrapper verified payload manifest and stale `.minute` before dispatch. MetaEditor 0/0 was the first runtime gate, followed by the stateful 18-month replay.

Failure evidence used the V29.3 diagnostic ZIP containing distribution identity and inner diagnostics when available.

Current production/live research and deployment target is governed by ADR-049 and the later V49 readiness process.
