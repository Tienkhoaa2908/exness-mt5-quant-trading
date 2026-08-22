# V45 clean-clone recovery

Date: 2026-08-22

## Incident

The original local checkout on C: was deleted after MetaTester storage had already been migrated to D:. A fresh clone was created at `D:\v31_mt5_40usd` and the tracked branch/HEAD recovered correctly, but two intentionally untracked local assets were gone:

- `runtime/v38_fast_harvest/OUTPUT_V38/v38_fast_harvest_exact_mt5.zip`;
- `runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv`.

MetaTester physical storage survived at `D:\MT5TesterCache\D0E8209F77C8CF37AD8BF550E51FF075`.

## Recovery design

V45 must not depend on the deleted checkout path or weaken accepted provenance.

1. Bootstrap resolves repository root from its own tracked script location instead of `$HOME/v31_mt5_40usd`, so a clone on D: is first-class.
2. If the pinned Python environment is missing, bootstrap recreates it on the current repo volume and pins `numpy==2.3.5`, `pandas==2.2.3`, `scikit-learn==1.8.0`.
3. Junction migration requires Python >=3.12 with `pathlib.Path.is_junction()` before touching tester storage.
4. If the accepted V38 evidence ZIP is absent, the tracked recoverable runner uses the already installed V45 MQL source in the MT5 data folder only when its SHA is exactly `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`.
5. It reverses only the frozen V45 validation-only edits and writes CRLF UTF-8 output.
6. The recovered parent must hash exactly to accepted V38 parent SHA `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`.
7. The normal V45 builder then rebuilds from that recovered parent and must reproduce frozen V45 source SHA `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2` again.

This gives a two-way identity check: installed V45 -> exact accepted V38 parent -> exact frozen V45. No provenance gate is removed.

## Independent verification

Using accepted V38 parent bytes from accepted V44 evidence, the exact forward V45 transform reproduced SHA `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`; applying the recovery inverse reproduced the original parent byte-for-byte and SHA `4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12`.

## Safety

This recovery changes no strategy logic, entry/exit geometry or risk. Strategy Tester only; `AllowLiveTrading=0`, `AllowDllImport=0`, native/external broker orders remain forbidden, and `LIVE_AUTHORIZED=0`.
