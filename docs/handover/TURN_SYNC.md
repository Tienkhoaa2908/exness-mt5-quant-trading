# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 17:xx (+07)

## User input

User supplied Gemini's response saying its browser/search/sandbox could not read the now-public GitHub repository and asking for a reliable way to let Gemini inspect the repository directly, or alternatively to prepare the Google Drive route Gemini suggested.

## State read before work

Fresh-resolved remote HEAD on `agent/v72-eurusd-independent-validation`:

`79140c5ecf52bcc2f041d232a1222e5c9c34608f`

Read `OPERATING_PROTOCOL.md`, `CURRENT_STATE.md`, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent commits and exact-head CI. Exact-head GitHub checks were green before this docs-only sync.

## External product research

Official current Google Gemini Apps documentation was checked rather than relying on the external model's self-description.

Gemini web on desktop has a native GitHub repository import path:

`Add files -> More uploads -> Import code -> enter repository or branch URL -> Import`.

Important properties from Google's documentation:

- public GitHub repositories can be imported without linking a GitHub account;
- private repositories require the GitHub account with access to be linked;
- one repository can be attached per chat, up to 5,000 files and 100 MB;
- the repository is a snapshot at import time and later GitHub changes are not synchronized into that Gemini chat;
- Gemini's GitHub app cannot retrieve commit history, pull requests or other repository metadata;
- merely putting a GitHub URL in the text prompt does **not** make Gemini read the repository;
- the native import is therefore the preferred route for source-code review and avoids the browser/indexing/outbound-network failures Gemini reported.

Google's file-upload documentation also states that a code folder can be uploaded/imported with the same 5,000-file / 100-MB class of limits, while ordinary ZIP uploads are much less suitable for a full repository because ZIPs are limited to 10 contained files. Therefore a giant repository ZIP on Drive is not the preferred fallback.

## Recommended review transport

Primary route:

1. use Gemini web on a computer;
2. attach the repository through the native **Import code** UI, not by pasting the URL into the prompt;
3. prefer an immutable review-snapshot branch so the external review has stable source content;
4. after the repository card is attached, paste the independent-review prompt and tell Gemini to treat the attached repository as the code source of truth;
5. because GitHub import cannot expose commit history/PR metadata, require the reviewer to use handover docs and repository files for code/evidence claims and explicitly mark unavailable Git metadata instead of inventing it.

Fallback route if native GitHub import is unavailable in that Gemini account/mode:

- create a sanitized code-folder snapshot from Git-tracked files at a pinned commit and use Gemini's **Import code -> Upload folder** path;
- only if that path is also unavailable, use Drive with a small number of consolidated text/Markdown evidence bundles rather than a many-file ZIP.

## Correction to the external Gemini response

Its statement that browser/search/VM networking prevented source access may be true for that execution attempt, but it missed Gemini Apps' separate native GitHub import mechanism. Its claimed GitHub notification state should not be treated as repository authority unless independently verified, because the actual project branch/head/CI must be read from GitHub source-of-truth tooling.

## Project safety / operator cost

No MT5 tester, strategy mutation, SHORT activation or REAL authorization is required for this review-transport work.

`NEXT_MT5_TESTER_ACTION=PAUSED`
`SHORT_ENABLED=0`
`REAL_MONEY_AUTHORIZED=0`

## Next action

Create/use a stable GitHub snapshot branch for Gemini import and have the user attach that branch through Gemini web's **Import code** UI. Use Drive/code-folder fallback only if native GitHub import is unavailable or errors in the user's Gemini account.
