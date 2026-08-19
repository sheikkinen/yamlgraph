# Feature Request: FR-822 DeviantArt API Publish Spike

**Priority:** MEDIUM
**Type:** Research Spike
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-19
**First consumer / first event:** the Phase-2 publisher of the
`deviantart-auto-publish-pipeline` inbox proposal — its authority is gated on
this spike's answers. First event: one real API publish of `tmp/da.png` to
the sheikkinen account, today.

**Prior art:** FR-781 [Enforced] shipped `examples/demos/file-hook/` — the
WatchPaths-triggered DeviantArt MD generator (description generation, the
pipeline's Phase 1) — but publishes nothing; this spike probes the missing
last leg (API publish) that will consume FR-781's output. Complementary, not
duplicate. FR-769 [Enforced] is the shared vision tool FR-781 uses; this
spike touches no vision. FR-772 [Enforced] matches only on a
DeviantArt-flavored example string in a tool-args FR — noun coincidence, no
territorial overlap.

## Summary

Execute one end-to-end DeviantArt API publish (OAuth 2.1 auth-code+PKCE →
`stash/submit` → `stash/publish`) of a single test image, as a throwaway
spike script, to answer the open questions in
`docs/research-deviantart-api-2026-08-19.md` §4 before any pipeline is built.

## Value Statement

The auto-publish pipeline (Phase 2) gets its unknowns resolved by one cheap
real-world publish instead of being designed against documentation guesses.

## Problem

Desk research confirmed the API shape but left runtime unknowns only a real
publish can answer:

1. Do publish error codes 0/1 (submission-policy/ToS acceptance) fire for an
   account that accepted them via the website, or is acceptance account-level?
   (Legacy `agree_*` params are gone from the OpenAPI schema.)
2. How does `artist_comments` render paragraphs — HTML, plain text with
   newlines, or something lossy? The julkaisuohje style spec depends on
   paragraph structure surviving.
3. Does the interactive PKCE flow + refresh-token persistence work as
   documented for a locally registered confidential client?

## Ideal Result

A deviation of `tmp/da.png` is live on the sheikkinen account, published
entirely via API with `is_ai_generated=true`, `noai=true`,
`is_mature=false`, style-spec-shaped description — and this FR records the
deviation URL, the answer to each of the three questions, and the persisted
refresh-token mechanics. The Phase-2 FR can then be written without a single
"probably".

## Proposed Solution

Throwaway spike script `scripts/spikes/da_publish_spike.py` (stdlib +
`requests`; deleted or graduated by Phase 2):

1. **Auth**: reads `DA_CLIENT_ID`/`DA_CLIENT_SECRET` from `~/.env`. If no
   token file exists: PKCE S256 flow — print authorize URL, catch the code on
   a localhost HTTP listener (`http://localhost:8721/cb`, whitelisted at app
   registration), exchange at `/oauth2/token`, persist the full token JSON to
   `~/.deviantart/token.json` (chmod 600). If token file exists: refresh and
   persist the rotated refresh token.
2. **Validate**: `POST /api/v1/oauth2/placebo`.
3. **Submit**: `POST /stash/submit` multipart — `tmp/da.png`, test title,
   3-paragraph `artist_comments` (to observe paragraph rendering), tags
   `["ai", "aiart", "digitalart", "inkpunk", "gothic"]`,
   `is_ai_generated=true`, `noai=true` → `itemid`.
4. **Publish**: `POST /stash/publish` — `itemid`, `is_mature=false`,
   `is_ai_generated=true`, `noai=true` → deviation URL.
5. Print every response body verbatim (read_raw_output_first applies to API
   responses too); operator eyeballs the live deviation for paragraph
   rendering.

Human prerequisite (one-time): register a confidential OAuth 2.1 app at
<https://www.deviantart.com/developers/register> with redirect URI
`http://localhost:8721/cb`, put `DA_CLIENT_ID`/`DA_CLIENT_SECRET` in `~/.env`.

## Acceptance Criteria

- [ ] AC-01 PKCE flow completes; token JSON persisted with 0600 perms
- [ ] AC-02 `placebo` returns success
- [ ] AC-03 `stash/submit` returns `itemid` (response body recorded here)
- [ ] AC-04 `stash/publish` returns deviation URL (recorded here); deviation
      visible on the account with AI flags set
- [ ] AC-05 Question 1 answered: error 0/1 behavior recorded
- [ ] AC-06 Question 2 answered: `artist_comments` paragraph rendering
      observed on the live deviation and recorded
- [ ] AC-07 Second run refreshes the token (proves rotation persistence);
      recorded
- [ ] AC-08 Spike disposition noted: script stays in `scripts/spikes/` marked
      throwaway; Phase-2 FR inherits its findings, not its code

## Constraints

- No credentials or token files in the repo; `~/.env` and
  `~/.deviantart/` only.
- `is_mature=false` verified by eyeballing `tmp/da.png` (ink illustration,
  gothic nun — no DA mature triggers).
- One image, one publish. The operator deletes the test deviation afterward
  if unwanted — the spike does not implement delete.
- No tests required: spike code is condemned at birth (AC-08); findings, not
  code, are the deliverable. This is the documented exception to TDD — the
  test would outlive the code it tests.

## Alternatives Considered

- Answering the questions from docs alone — already exhausted, see research
  doc §4.
- Browser automation of DA Studio — rejected; API path is complete and
  supported.

## Related

- `docs/research-deviantart-api-2026-08-19.md` (desk research)
- `.chaplain/inbox/deviantart-auto-publish-pipeline.md` (consumer proposal)
