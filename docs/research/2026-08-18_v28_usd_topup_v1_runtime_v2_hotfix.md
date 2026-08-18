# V28 USD calendar top-up — V1 runtime and V2 hotfix

User runtime ZIP SHA-256 `e7ca5d14200f89a3c11d8b49144ddd33c9f9d69654e55bf84912472a91fda337`.

V1 evidence:
- bundle hash manifest 6/6 PASS;
- MetaEditor 0 errors / 0 warnings;
- 304 USD calendar rows;
- requested range 2026-03-01 -> 2026-08-18;
- only 1/6 chunks succeeded;
- 5 chunks failed with `ERR_CALENDAR_TIMEOUT=5401`;
- actual coverage 2026-03-02 14:45 -> 2026-03-31 21:10;
- status `partial`, so V1 is NOT valid Mar-Jul confirmation.

Root cause direction: broad monthly CalendarValueHistory calls remain prone to timeout on this terminal/server path even for USD-only retrieval.

V2 hotfix:
- resume from 2026-04-01, preserving the useful March rows from V1;
- 1 day per CalendarValueHistory chunk;
- bounded 5 retries per day;
- hard watchdog 45 minutes, idle watchdog 5 minutes;
- runner refuses PASS unless USD coverage status is `ok`, `chunks_failed=0`, and metadata `failed_chunks=0`;
- primary output remains local `OUTPUT` next to CMD;
- no trading/order path.

Local static QA: 6/6 PASS. Release ZIP SHA-256 `e3aaa4d09dc2a23480006426c3ce86fd802c05853ae72eb71a47bb6969f34de6`.

Official MQL5 contract: Economic Calendar functions use trade-server time; error 5401 is `ERR_CALENDAR_TIMEOUT`. V2 does not change the frozen V28 routing threshold 0.25.
