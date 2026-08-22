# V44 Baseline Robustness Validation — Exact MT5 Results

Status: **PAPER_DEMO_READY** for the V44 historical workflow.

Project-wide policy has since been superseded by ADR-049:
- `LIVE_RESEARCH_ALLOWED=1`;
- `LIVE_DEPLOYMENT_TARGET=1`.

Therefore the V44 result must be read as historical evidence, not as a permanent prohibition on real-money research or future production/live deployment engineering.

Accepted V44 evidence ZIP SHA256:
`550396cc2806538ae1f38ba596e3af705a08bcb2305335a14d0cfa39aabc8fa4`

Integrity: ZIP CRC PASS, canonical internal manifest 130/130 PASS. Evidence HEAD:
`7da3735e899d0aea13aa2ff513b77fd1feb1fef4`.

The accepted annual control reproduced exactly at $107.432645 with 563 trades. All 19 exact windows completed: 12 monthly restart windows, 4 quarter blocks, 2 half-year blocks and 1 annual continuous window.

| Candidate | Annual end | Geo/month | DD | PF | Monthly restart + | Quarter + | Half-year + | Sign agreement |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| adaptive_ewma_hl8_thr0 | $107.432645 | 8.5816% | 9.9038% | 1.5008 | 9/12 | 3/4 | 2/2 | 10/12 |
| adaptive_ewma_hl8_thr0p05 | $111.285257 | 8.9009% | 10.4368% | 1.5210 | 8/12 | 3/4 | 2/2 | 10/12 |
| adaptive_ewma_hl10_thr0p05 | $110.025682 | 8.7976% | 9.8587% | 1.5301 | 9/12 | 3/4 | 2/2 | 11/12 |

HL8 threshold0.05 is the annual-return winner. HL10 threshold0.05 has the best deployment-style robustness profile: lower DD than HL8 threshold0.05, highest PF, best restart sign agreement, lowest turnover and stronger restart compounding.

Therefore V45 froze HL10 threshold0.05 as the primary deployment-validation candidate, HL8 threshold0.05 as the return shadow, and HL8 threshold0 as control.

V44 itself did not constitute sufficient evidence for a real-capital deployment decision. Later V45-V49 evidence and ADR-049 supersede that historical phase boundary.
