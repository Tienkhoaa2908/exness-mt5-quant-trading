# V27.1 watchdog diagnostic → V27.2 performance hotfix

Ngày: 2026-08-18.

## Diagnostic evidence

Uploaded diagnostic ZIP SHA-256: `78cec87be173228c6369c315a43348ee844863f991b0125d97bec3122303406b`.

Verified facts:
- MetaEditor compile: 0 errors / 0 warnings;
- broker connection gate passed;
- bootstrap reached `phase=calendar_query_started`;
- V27.1 runner killed MT5 after the fixed 25-minute watchdog because `latest.txt` had not yet been produced;
- the terminal remained connected/synchronized during the query period.

## Root performance defect

V27.1 used 28-day chunks across 5 currencies from 2022-present, creating roughly 300 history requests. More importantly, every returned calendar value repeated `CalendarEventById()` and `CalendarCountryById()` metadata lookups. On the user's low-resource Windows machine this made the full export exceed the fixed watchdog. There was no progress heartbeat, so the runner could not distinguish active work from a true hang.

## V27.2 changes

- calendar chunk size increased to 90 days;
- event metadata cached in-memory by `event_id`;
- country metadata cached in-memory by `country_id`;
- `progress.txt` heartbeat emitted before/after chunks and during value processing;
- runner hard watchdog increased to 90 minutes;
- separate idle watchdog kills only after 12 minutes with no progress update;
- diagnostic ZIP now includes `progress.txt`;
- V27.1 connection/synchronization wait remains in force.

Release SHA-256: `ca915ea466e5544bac6d7e6b32e8b150419b17c47389301a24331f4df2937619`.

Static checks: balanced MQL/PowerShell delimiters, max FileWrite args 28, no `OrderSend`, no `CTrade`, no `AllowLiveTrading=1`, internal kit manifest 5/5 PASS.

## Safety

DATA ONLY. REAL-MONEY LIVE TRADING = FORBIDDEN. No native/external broker order path.
