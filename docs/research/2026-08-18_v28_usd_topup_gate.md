# V28 USD calendar top-up gate

Purpose: fill USD Economic Calendar coverage after the V27 recovered segment without rerunning the expensive multi-currency exporter.

## Policy note

This was a historical DATA-ONLY V28 tool with no trading/order path. Current project-wide policy is governed by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

Its no-order semantics are tool-specific and do not prohibit later production/live research or real-capital deployment engineering.

## V1 runtime result

User ZIP SHA-256 `e7ca5d14200f89a3c11d8b49144ddd33c9f9d69654e55bf84912472a91fda337`.
- internal hashes 6/6 PASS;
- MetaEditor 0 errors / 0 warnings;
- requested 2026-03-01 → 2026-08-18;
- 304 rows;
- only 1/6 chunks succeeded;
- 5 chunks failed with ERR_CALENDAR_TIMEOUT=5401;
- actual coverage 2026-03-02 → 2026-03-31;
- status partial, so V1 was not valid later confirmation.

## V2 gate

- resume from 2026-04-01;
- 1 day per CalendarValueHistory chunk;
- 5 bounded retries/day;
- hard watchdog 45m, idle watchdog 5m;
- PASS only when USD coverage status=ok and failed counters are zero;
- primary output local OUTPUT next to CMD;
- static QA 6/6 PASS;
- release SHA-256 `e3aaa4d09dc2a23480006426c3ce86fd802c05853ae72eb71a47bb6969f34de6`.

Later confirmation merged usable calendar segments and scored Mar-Jul 2026 without retuning the frozen V28 threshold first.

Current production/live research and deployment target is governed by ADR-049 and later V49 readiness evidence.
