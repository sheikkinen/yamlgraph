# Feature Request: FR-822 DeviantArt API Publish Spike

**Priority:** MEDIUM
**Type:** Research Spike
**Status:** Completed 2026-08-19; Judged 2026-08-19 APPROVED WITH REVISIONS
(`FR-822-deviantart-publish-spike.judgement.md`) — R-1..R-4 folded below;
deviation live: <https://www.deviantart.com/sheikkinen/art/API-Spike-Veil-and-Vow-1370448491>
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

## Acceptance Criteria (revised per Judgement R-2)

- [x] AC-01 OAuth/token exchange recorded without secret values: scope
      `"basic publish stash"`, 1 h access-token expiry, refresh token present;
      token at `~/.deviantart/token.json`, mode witnessed
      `-rw-------` (0600) at 2026-08-19 07:08
- [x] AC-02 `placebo` response body recorded exactly: `{"status":"success"}`
- [x] AC-03 `stash/submit` response body recorded exactly (itemid, stack,
      stackid — see Implementation Notes); no bearer token in record
- [x] AC-04 `stash/publish` response body recorded exactly (deviation URL,
      deviationid — see Implementation Notes); no bearer token in record
- [x] AC-05 ToS question answered explicitly: publish error codes 0/1 did
      NOT fire for the tested account (website-accepted); Phase 2 surfaces
      them if they appear for a fresh account
- [x] AC-06 Live-page witness proves `\n\n` plain text renders as separate
      paragraphs — see "Live page witness" note (timestamp, method, URL,
      three paragraph-start snippets)
- [x] AC-07 Second-run refresh witness: refresh returned a NEW
      `refresh_token` and `~/.deviantart/token.json` was rewritten
      (mtime 2026-08-19 07:08); token values not stored here
- [x] AC-08 Visible flags/tags evidence: "Created using AI tools" badge and
      all five tags on the live page (see witness note); NoAI is metadata
      only, not surfaced on the public page
- [x] AC-09 Spike disposition recorded: script is non-production, Phase 2
      inherits findings only (see Disposition)
- [x] AC-10 Credential disposition recorded: no repo-committed
      credential/token artifacts; runtime path outside the repository (see
      Credential disposition)

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

## Implementation Notes (2026-08-19)

One-time app registration: confidential OAuth 2.1 client `client_id=75301`
(`yamlgraph-publisher`), redirect `http://localhost:8721/cb` — the form
accepted plain-http localhost despite its https warning text.

**Credential disposition (Judgement R-1):** credentials live outside the
repository — `DA_CLIENT_ID`/`DA_CLIENT_SECRET` in `~/.env` (0600), token at
`~/.deviantart/token.json` (0600). During the spike run the creds sat
briefly in the repo-root `.env`; that file is gitignored and was verified
never committed (`git log --all -- .env` empty); the two entries were moved
to `~/.env` and removed from the repo-root file on 2026-08-19 as part of
this fold. No committed artifact contains access tokens, refresh tokens, or
the client secret.

Run transcript (all HTTP 200, first attempt):

- token exchange: `scope: "basic publish stash"`, 1 h expiry, refresh token
  returned.
- placebo: `{"status":"success"}`
- submit: `{"status":"success","itemid":6311111935494244,"stack":"Sta.sh","stackid":8654406562271036}`
- publish: `{"status":"success","url":"https://www.deviantart.com/sheikkinen/art/API-Spike-Veil-and-Vow-1370448491","deviationid":"FCD30B6B-9173-A4E1-AB5B-81EEA06E2C86"}`

**Q1 (ToS/submission-policy errors 0/1):** did NOT fire — acceptance is
account-level for an account that accepted via the website. No `agree_*`
params needed. Phase 2 needs no ToS handling beyond surfacing the error if it
ever appears for a fresh account.

**Q2 (`artist_comments` rendering):** plain text with `\n\n` renders as
separate paragraphs on the live deviation — verified by fetching the page:
all three paragraphs distinct, no merge, no HTML needed. The julkaisuohje
paragraph structure survives as-is.

**Q3 (refresh rotation):** second run refreshed successfully; a NEW
`refresh_token` was returned and persisted, old one superseded — rotation
confirmed, publisher must always persist the response (as designed).

**Live page witness (Judgement R-4):** observed 2026-08-19 (twice: shortly
after publish, and re-verified ~07:45 EEST during judgement fold), method:
anonymous server-side HTTP fetch of the public deviation page (no session,
no cookies), URL as in Status. Three distinct paragraphs rendered, starting:
"First paragraph of the spike description…", "Second paragraph after a
blank line…", "Be Art. Be Unique." — no merge, no HTML needed. All five
tags visible as links: gothic, ai, digitalart, aiart, inkpunk. "Created
using AI tools" badge shown beside image metadata. NoAI is not surfaced on
the public page (metadata-only flag).

Access/refresh tokens were printed to terminal scrollback by design (spike
verbosity); both rotated out by the AC-07 refresh, so nothing live leaked.
No transcript containing token values is committed.

**Disposition (Judgement R-3):** `scripts/spikes/da_publish_spike.py` is a
non-production witness script — it must not be imported or reused by
Phase 2. Phase 2 inherits only the recorded findings and endpoint/auth
contracts, not the code. Any reusable DeviantArt publisher, queue processor,
token store, or retry/idempotency implementation requires its own judged FR
and normal TDD.
