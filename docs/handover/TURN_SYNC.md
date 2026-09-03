# TURN SYNC — LATEST PROJECT TURN

Updated: 2026-09-03 18:xx (+07)

## User input

User supplied Gemini's response saying its browser/search/sandbox could not read the now-public GitHub repository and asked for a reliable way to let Gemini inspect the repository directly, or alternatively to prepare the Google Drive route Gemini suggested.

## State read before work

Fresh-resolved remote HEAD on `agent/v72-eurusd-independent-validation` at turn start:

`79140c5ecf52bcc2f041d232a1222e5c9c34608f`

Read `OPERATING_PROTOCOL.md`, `CURRENT_STATE.md`, `KNOWN_FAILURES.md`, `TURN_SYNC.md`, recent commits and exact-head CI. Pre-change exact-head checks were green.

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
- the native import therefore bypasses the browser/indexing/outbound-network failures Gemini reported for source-code review.

Google's file-upload documentation also states that a code folder has the same 5,000-file / 100-MB class of limits, while an ordinary ZIP can contain only up to 10 files. A giant repository ZIP on Drive is therefore not the preferred transport.

Repository metadata confirms this public project is comfortably below the native Gemini repository size limit.

## Stable Gemini review snapshot created

Created a dedicated read-only-by-convention snapshot branch for the external review:

`external/gemini-review-20260903`

Pinned commit:

`f94aa2c1cd4d2e20fbfc94bc41a788658b78cc8e`

This branch is intentionally not the active development branch and should not be advanced during the Gemini review. Its purpose is to give Gemini one stable branch URL for **Import code** while active research remains paused.

## Recommended review transport

Primary route:

1. use Gemini web on a computer;
2. attach `external/gemini-review-20260903` through the native **Import code** UI, not by pasting the URL as prompt text;
3. after the repository card is attached, paste the independent-review prompt and tell Gemini to treat the attached repository as the source-code truth;
4. because GitHub import cannot expose commit history/PR metadata, require Gemini to mark that metadata unavailable instead of inventing it, and use the handover docs plus `.github/workflows/` for repository-grounded context.

Fallback route if native GitHub import is unavailable in that Gemini account/mode:

- create a sanitized code-folder snapshot from Git-tracked files at the pinned commit and use Gemini's **Import code -> Upload folder** path;
- only if that is also unavailable, use Drive with a small number of consolidated text/Markdown evidence bundles rather than a many-file repository ZIP.

## Correction to the external Gemini response

Its browser/search/VM networking failures may be genuine for that execution attempt, but they do not establish that Gemini Apps lacks repository access: the separate native GitHub import feature exists. Its claimed GitHub notification state must not be treated as repository authority unless independently verified; the actual active branch/head at turn start was `79140c5...`, not the unrelated short SHAs it reported.

## Project safety / operator cost

No MT5 tester, strategy mutation, SHORT activation or REAL authorization is required for this review-transport work.

`NEXT_MT5_TESTER_ACTION=PAUSED`
`SHORT_ENABLED=0`
`REAL_MONEY_AUTHORIZED=0`

## Next action

User should attach the stable snapshot branch in Gemini web using **Add files -> More uploads -> Import code**, then paste a revised review prompt that refers to the attached repository rather than asking Gemini's browser to fetch GitHub. Use code-folder/Drive fallback only if native import is unavailable or errors in the user's Gemini account.
