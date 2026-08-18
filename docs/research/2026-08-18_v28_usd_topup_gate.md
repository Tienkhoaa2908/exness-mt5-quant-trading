# V28 USD calendar top-up gate

Purpose: fill USD Economic Calendar coverage after the V27 recovered segment without rerunning the expensive multi-currency exporter.

## V1 runtime result
User ZIP SHA-256 `e7ca5d14200f89a3c11d8b49144ddd33c9f9d69654e55bf84912472a91fda337`.
- internal hashes 6/6 PASS;
- MetaEditor 0 errors / 0 warnings;
- requested 2026-03-01 → 2026-08-18;
- 304 rows;
- only 1/6 chunks succeeded;
- 5 chunks failed with ERR_CALENDAR_TIMEOUT=5401;
- actual coverage 2026-03-02 → 2026-03-31;
- status partial, so V1 is not valid later confirmation.

## V2 gate
- resume from 2026-04-01;
- 1 day per CalendarValueHistory chunk;
- 5 bounded retries/day;
- hard watchdog 45m, idle watchdog 5m;
- runner only PASSes when USD coverage status=ok and all failed-chunk counters are zero;
- primary output local `OUTPUT` next to CMD;
- static QA 6/6 PASS;
- release SHA-256 `e3aaa4d09dc2a23480006426c3ce86fd802c05853ae72eb71a47bb6969f34de6`.

After V2 upload, merge March V1 + Apr-now V2, dedupe by value/event/time and score Mar-Jul 2026 without retuning the frozen 0.25 V28 routing threshold first.

Safety: DATA ONLY. REAL-MONEY LIVE TRADING = FORBIDDEN. No order path.
