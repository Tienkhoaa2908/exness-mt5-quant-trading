# V28 USD calendar top-up gate

Purpose: fill the missing USD Economic Calendar window from 2026-03-01 onward without rerunning the expensive multi-currency 2022-present exporter.

## Policy note

This was a historical DATA-ONLY V28 tool. Current project-wide policy is governed by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

The top-up itself had no order path. That is a tool-specific property, not a permanent prohibition on researching or preparing production/live trading with real capital.

The top-up was intentionally narrow:
- currency: USD only;
- from: 2026-03-01 to current trade-server time;
- 31-day chunks;
- retains actual/forecast/previous/revised fields plus event metadata;
- sanitizes text commas for structural CSV validity;
- verifies local OUTPUT before PASS.

Local static QA: 4/4 PASS. Release ZIP SHA-256:
`81d2743c7ae10df21e8b807f2d90c935ef36e965bee28898b84d6a42a96920c2`.

Later Mar-Jul 2026 event-aware scoring was intended to use the frozen V28 routing threshold without retuning it first.

Current production/live research and deployment target is governed by ADR-049 and later V49 readiness evidence.
