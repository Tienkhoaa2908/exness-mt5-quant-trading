# Recovery checkpoint — V28 Event-Aware Regime Router

Ngày: 2026-08-18.

REAL-MONEY LIVE TRADING = FORBIDDEN.

## User-facing requirement
Không hiển thị code Python/tooling nội bộ nếu user không yêu cầu. Tooling phải chạy âm thầm; user-visible tập trung vào evidence, artifact, hash, hướng dẫn và lỗi.

## V28 research state
V27 recovered calendar: 24,085 rows, recovery ZIP SHA-256 `a88473422aa16eda7e3c3cbfa050768409451248b0de45c96b4ae1e6b2e1556e`.

Event-aware model:
- 13 OOS months Feb-2025 → Feb-2026;
- LightGBM event-aware future-range Spearman ~0.5493, 13/13 positive;
- paired uplift vs price/cross-asset base +0.01210 with bootstrap 95% CI above zero;
- direction remains weak; mechanical families retain Long/Short ownership.

Only low-range quartile 0.25 is pre-registered for V28 stateful routing. V28 replay kit static QA 6/6 PASS; runtime pending.

## USD later-confirmation top-up
V1 output SHA-256 `e7ca5d14200f89a3c11d8b49144ddd33c9f9d69654e55bf84912472a91fda337`: 6/6 hashes PASS, MetaEditor 0/0, but partial only. 304 rows, one successful chunk, five 5401 timeouts, coverage only March 2026.

Do not score Mar-Jul confirmation from V1.

V2 resumes 2026-04-01 using 1-day chunks and strict completeness gate. Static QA 6/6 PASS. Release SHA-256 `e3aaa4d09dc2a23480006426c3ce86fd802c05853ae72eb71a47bb6969f34de6`.

On V2 upload: verify full coverage, merge with March V1, dedupe, score later-period model without retuning threshold 0.25, then run V28 MT5 replay only if confirmation survives.

Stop-risk ceiling remains 1.00%/trade. No native broker orders.
