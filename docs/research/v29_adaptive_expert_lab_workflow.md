# V29 Adaptive Expert Lab — workflow

## Active distribution

`v29_3_distribution_hardening` wraps the frozen V29.2 strategy payload.

Pinned decoded payload SHA-256:
`d469f527cb96197ed265c1e1a62c4d3f3f2d220efca0f44fb4478e928f68f334`.

V29.3 không đổi catalog/risk/exit/adaptive logic.

## Pre-Windows gates

Clean checkout phải verify exact archive hash, helper definitions, standard MQL structure members, tester/safety markers, no native-order path, analyzer compile, template safety, chunk schedule, pytest và secret scan.

Chỉ CI PASS mới được upload user-facing one-click artifact.

## Windows

Root V29.3 wrapper verify payload manifest và stale `.minute` trước khi dispatch inner V29.2 launcher. MetaEditor 0/0 là runtime gate đầu tiên. Sau đó mới chạy stateful 18-month replay.

Nếu fail, upload outer V29.3 diagnostic ZIP nếu wrapper tạo được; nó chứa distribution identity + inner diagnostic.

LIVE remains forbidden.
