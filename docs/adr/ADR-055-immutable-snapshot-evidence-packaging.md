# ADR-055 — Immutable snapshot packaging for live-forward evidence

Date: 2026-08-28

## Context

The V53 timebox-waiver archive exposed a packaging race. The archive itself was CRC-clean, but one manifest entry mismatched because `V53_DEMO_REHEARSAL_STATUS.txt` was hashed while the EA was still running and then updated before the ZIP writer read it.

This can make a valid runtime session appear to have an integrity failure even though the archived bytes are internally consistent.

## Decision

All future forward-runtime evidence packagers must use immutable snapshot semantics:
1. copy every source evidence file into a staging snapshot;
2. stop reading from live runtime files after the snapshot copy completes;
3. generate the SHA256 manifest from staged files only;
4. create the ZIP from the same staged files only;
5. run ZIP CRC validation;
6. verify every manifest hash against the completed ZIP before publishing the artifact.

If a historical bundle has a manifest race but the archive CRC is valid, recovery may recompute metadata only when:
- the exact archived bytes are preserved unchanged;
- the original manifest is retained;
- the mismatch set and reason are recorded explicitly;
- no missing runtime evidence is fabricated;
- the recovered bundle receives a new SHA256 identity.

## V53 application

Original waiver ZIP SHA256:
`b6118b928cafc5528b0dab04cf01f3022cc21a0df693e4acbfcd04048c80da8a`

Original manifest: 16/17 PASS, with exactly one mismatch in the live status file.

Recovered waiver ZIP SHA256:
`602115bc6161e8947835c43033a1899637cc8a288f5192b2631acd6a6dd629db`

Recovered manifest: 19/19 PASS. Runtime evidence bytes were not changed; only recovery provenance and corrected manifest metadata were added.

## Consequence

A manifest race is treated as an artifact-generation defect, not as alpha or execution failure. Future release/runtime code should inherit snapshot-then-hash packaging rather than hash live mutable files.
