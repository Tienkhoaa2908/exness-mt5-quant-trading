# V27.2 partial Economic Calendar recovery

Uploaded diagnostic SHA-256: `1ab14f0593cb39603aadae2ad179363835d26532f53ac3f77f83ad116d1ce6da`.

Runtime evidence:
- MetaEditor compile remained 0 errors / 0 warnings;
- broker connection/bootstrap gate passed;
- V27.2 progressed to `currency=CNY`, `chunks_done=80`, `total_rows=24085`;
- last progress window was `2022.12.27 -> 2023.03.26` for CNY;
- runner stopped only because the 90-minute hard watchdog elapsed;
- `last_error=0` at the final progress marker.

Interpretation:
USD/EUR/GBP/JPY had already progressed through their full chunk sequences and CNY had started. The run was making progress and was not stalled by Calendar API errors. Re-running the entire 90-minute export from the beginning is wasteful.

Decision:
Recover the newest incomplete run folder directly from `MetaQuotes\\Terminal\\Common\\Files\\mt5_quant_calendar_export_v1` and package its existing `calendar_values.csv`, `currency_coverage.csv` and progress/bootstrap markers. Offline merge logic must deduplicate by calendar value/event/time if a later CNY continuation is added.

Recovery one-click SHA-256: `85d8f005ddc2af519f872ce81fa73ae0e3b60514d0d9c0cc017437b54cac6ac6`.

Safety: DATA ONLY. REAL-MONEY LIVE TRADING = FORBIDDEN. No order path.
