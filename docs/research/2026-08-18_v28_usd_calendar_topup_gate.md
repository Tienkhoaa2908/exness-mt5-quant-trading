# V28 USD calendar top-up gate

Purpose: fill the missing USD Economic Calendar window from 2026-03-01 onward without rerunning the expensive multi-currency 2022-present exporter.

The top-up is intentionally narrow:
- currency: USD only;
- from: 2026-03-01 to current trade-server time;
- 31-day chunks;
- retains actual/forecast/previous/revised fields plus event metadata;
- text commas are sanitized so CSV rows remain structurally valid;
- primary output is the local `OUTPUT` directory next to the CMD and is verified before PASS.

Local static QA: 4/4 PASS. Release ZIP SHA-256: `81d2743c7ae10df21e8b807f2d90c935ef36e965bee28898b84d6a42a96920c2`.

After upload, use Mar-Jul 2026 as later event-aware model confirmation. Do not retune the 0.25 V28 routing threshold on those months before scoring them.

Safety: DATA ONLY. REAL-MONEY LIVE TRADING = FORBIDDEN. No order path.