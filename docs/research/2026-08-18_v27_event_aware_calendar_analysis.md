# V27 — Event-aware Economic Calendar analysis

Ngày: 2026-08-18.

## Policy note

V27 was historical data/model research. Current project-wide policy is governed by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

V27's no-native-order and 1.00% research-risk constraints were phase-specific and are not a permanent prohibition on researching or preparing production/live trading with real capital.

## Recovered calendar bundle

User upload SHA-256: `a88473422aa16eda7e3c3cbfa050768409451248b0de45c96b4ae1e6b2e1556e`.

Recovered calendar output contained 24,085 rows. CSV QA found rows with unescaped commas in event names; those were repaired deterministically offline without dropping rows. Future exporter revisions must quote/sanitize delimiters.

## Coverage used for event-aware modeling

The partial export contained major-calendar history through early 2026 with some earlier timeout gaps. Modeling used a continuous major-currency region and chronological expanding walk-forward with purge; no random CV.

## Range-regime result

Event-aware price+calendar models improved range-regime rank correlation over the paired price/cross-asset control on the discovery folds, with USD high-impact schedule/proximity carrying most incremental information.

## What calendar information was useful

Useful variables were largely ex-ante schedule/proximity clocks and upcoming USD high-impact counts rather than actual/forecast surprise. Calendar was therefore treated primarily as a volatility/regime clock rather than a direct macro-direction oracle.

## Direction result

Calendar did not produce a stable direct direction improvement. Mechanical strategy families retained Buy/Sell ownership while ML/calendar controlled regime routing/abstention in this research stage.

## Trade-ledger diagnostic

Joining event-aware range scores to existing historical trades suggested family-specific routing rather than a blanket news blackout. Same-sample quintiles were hypothesis generation only, not production thresholds.

## Next gate at that time

Freeze the event-aware range/regime architecture around USD schedule/proximity and test later untouched periods before promotion. Do not promote surprise-heavy features or direct direction ownership from the V27 sample.

Current production/live research and deployment target is governed by ADR-049 and later V49 readiness evidence.
