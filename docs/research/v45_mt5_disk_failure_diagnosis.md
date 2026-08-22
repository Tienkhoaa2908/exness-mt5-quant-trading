# V45 first-run failure diagnosis — confirmed disk exhaustion

Date: 2026-08-22

## Evidence identity

Diagnostic ZIP SHA256:

`3af2ab70f02920ad6fbd0eb5b3fd67ef66a550bf2db08bd523ee4b63372e8b1f`

The diagnostic-only collector was run twice and produced the same SHA256. It did not launch MT5, MetaEditor or Strategy Tester.

## What passed before the failure

- V45 static gates: 15/15 PASS.
- Secret scan PASS.
- Accepted V38 immutable parent PASS.
- Verified V34 causal tape PASS.
- Deterministic V45 source SHA: `36335a92bfb2b9f6448a177cf80481c357f1cf13b8793d7302e153d13901c2b2`.
- MetaEditor compile: `Result: 0 errors, 0 warnings`.
- Terminal launched with the intended V45 config.
- XAUUSDm history synchronized from 2021-01-03 through 2026-08-14.
- M15/H1 history both began in 2021, so the 2022 requested start was available.
- EA initialized successfully and printed `V45_MULTIYEAR_VALIDATION START` at 2022-01-01.

## Confirmed root cause

Terminal log at the failed run:

- `03:05:12` — MT5 started and reported only `3 / 136 Gb disk` free.
- `03:05:21` — automatic testing started.
- `03:05:31` — V45 EA initialized successfully.
- `03:06:09` — `XAUUSDm: cannot generate history data, check disk space`.
- `03:06:09` — tester produced `0 ticks, 0 bars generated`.
- `03:06:09` — last test result: `no disk space in ticks generating function`.
- `03:06:18` — terminal exited with process code `100018`.

Therefore `100018` in this incident is a terminal/tester consequence of disk exhaustion. It is not evidence of an MQL trade-server retcode, strategy failure, missing 2022 history, state failure, or compile failure.

## History inventory

The terminal-side XAUUSDm inventory contains annual HCC history tokens for 2018 through 2026. Main terminal broker history must not be deleted to solve this failure.

## Recovery fix

Canonical V45 bootstrap now performs a disk preflight before MT5:

- minimum free space: 12 GiB;
- if below threshold, it may delete only recomputable local MetaTester agent `bases` copies and tester temp/cache files;
- it never deletes Terminal broker history, accepted project evidence, state files, repo files, or compiled EAs;
- if safe cache cleanup still leaves <12 GiB free, it fails before launching MT5 and reports the additional GiB required.

The threshold is deliberately conservative for the single 2022-2026 `Every tick` generation workload. Prior one-year exact runs showed roughly 1.9 GB total tick-data footprint; the multi-year run needs materially more working space.

## Recovery rule

Do not shorten V45 from 2022 merely because this attempt failed. The requested historical range initialized correctly. Free disk space, preserve the cold-start protocol, then rerun the same canonical bootstrap once.
