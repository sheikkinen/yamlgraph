# Feature Request: FR-826 DeviantArt Publisher Tool

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-19
**First consumer / first event:** the operator, publishing one approved
FR-781-generated post (a `<name>.md` + `<name>.png` twin from the
file-hook output) to the sheikkinen DeviantArt account via one manual
CLI invocation. Backlog waiting behind that event: ~269 images in
`~/Documents/deviant-working/output/`.

**Prior art:** FR-822 [Completed, Judged APPROVED WITH REVISIONS] is the
API publish spike — this FR is its named Phase-2 consumer and inherits
its findings ONLY; the spike script is quarantined non-production
(judgement R-3/C-5) and is not imported or copied here. FR-781
[Enforced] is the Phase-1 describe/MD generator whose output this tool
consumes — producer/consumer, no overlap. FR-769 [Enforced] is the
vision boundary FR-781 uses; this FR touches no vision. FR-772
[Enforced] matches on a DeviantArt-flavored example string only — noun
coincidence.

## Summary

Production-grade Python tool (Layer 3, side effects) that publishes one
image + its FR-781 markdown twin to DeviantArt via the API: token
refresh with rotation persistence, `stash/submit` → `stash/publish`,
MD-to-publish-fields parsing. TDD against the exact response bodies the
FR-822 spike recorded — no live API in tests.

## Value Statement

The operator's manual DeviantArt publishing step (upload via Studio UI,
retype title/description/tags, set flags) disappears; FR-781 drafts
become one-command publications.

## Problem

FR-781 generates style-faithful DeviantArt posts as `.md` twins, and
FR-822 proved the API publish path end-to-end — but nothing connects
them. The gap is a small, tested, reusable publisher: the spike script
that did this once is condemned non-production code by its judgement,
and FR-822's C-5 requires the reusable implementation to re-enter as
its own judged FR with tests and secret-handling constraints. This is
that FR.

## Ideal Result

`python -m examples.deviantart_publisher path/to/artwork.md` publishes
the artwork with title, paragraphs intact, quote, tags,
`is_ai_generated=true`, `noai=true`, and prints the live deviation URL —
using a token that silently refreshed and re-persisted itself. Every
API contract the tool relies on is asserted by a test against a real
recorded response body. Queue, cadence, and automation remain out of
scope: this is the manual-invocation publisher that must publish once
before any automation FR is worth writing.

## Proposed Solution

New example package `examples/deviantart_publisher/` (no core
`yamlgraph/` changes; `requests` only — already used by examples):

1. **`token_store.py`** — credential/token boundary:
   - Creds from env (`DA_CLIENT_ID`/`DA_CLIENT_SECRET`, loaded from
     `~/.env`; never repo files).
   - Token JSON at `~/.deviantart/token.json`, written 0600.
   - `get_access_token()`: refresh grant, then persist the ROTATED
     refresh token before returning (FR-822 Q3: rotation on every
     refresh; a lost rotated token strands the client for re-auth).
   - No interactive PKCE flow here: initial grant is a one-time human
     rite already performed (FR-822); missing/expired-beyond-refresh
     token → raise with instructions, never re-implement the browser
     dance in the publisher.

2. **`md_post.py`** — parse the FR-781 MD contract at the boundary:
   `# Title` heading; body paragraphs (blank-line separated, passed
   through as plain text — FR-822 Q2 proved `\n\n` renders as
   paragraphs, no HTML); optional `> quote` blockquote joined into the
   comments; trailing `#tag` line → tags list, validated `[a-z0-9_]+`
   (DA constraint), max 30. Parse failure → raise with the offending
   line, never publish a half-parsed post.

3. **`publisher.py`** — the two-call flow with FR-822's frozen
   contracts:
   - `POST /placebo` pre-flight token validation.
   - `POST /stash/submit` multipart: file, title, artist_comments,
     indexed `tags[i]` fields, `is_ai_generated=true`, `noai=true`.
   - `POST /stash/publish`: itemid, `is_mature` (from `--mature` CLI
     flag, default false — the invoker is human in this FR's scope and
     judges per image per the julkaisuohje; automated mature judgement
     belongs to the Phase-1 schema extension, not here).
   - `User-Agent` header (FR-822: absent UA → 403 HTML), explicit
     timeout on every request.
   - Error contract: HTTP 429 → exponential backoff (bounded retries,
     then raise); publish `error_code: 9` (already published) →
     idempotent success with a logged notice; ToS/submission-policy
     `error_code: 0/1` → surfaced verbatim in the raised error, never
     handled (FR-822 Q1: account-level acceptance, should not fire).
   - Returns the deviation URL; prints every response body
     (read_raw_output_first applies to API responses).

4. **`__main__.py`** — CLI: `<md_path>` positional (PNG twin derived by
   suffix swap), `--mature` flag, `--dry-run` (parse + validate + print
   the would-be multipart fields, no network).

5. **Tests** (`tests/unit/test_deviantart_publisher.py`) — mocked HTTP
   via monkeypatch; fixtures are the EXACT bodies FR-822 recorded
   (submit itemid/stackid, publish url/deviationid, placebo,
   refresh-rotation response). Witness tests: rotation persisted before
   return; 0600 on token write; MD parse round-trip on a real FR-781
   output fixture; tags validator rejection; 429 backoff; error 9
   idempotency; ToS error surfaced. New capability
   `capabilities/CAP-XXX-deviantart-publisher.yaml` + `REQ-YG-XXX`;
   all tests `@pytest.mark.req`-tagged.

## Acceptance Criteria

- [ ] AC-01: `--dry-run` on a real FR-781 output MD prints parsed
      title, paragraph count, quote, validated tags, and flags — no
      network calls made
- [ ] AC-02: One live manual publish of an approved FR-781 post
      succeeds end-to-end; deviation URL recorded in this FR
      (the single live event; not exercised by CI)
- [ ] AC-03: Token refresh persists the rotated refresh token to
      `~/.deviantart/token.json` (0600) before any API call returns —
      witnessed by a unit test
- [ ] AC-04: All API-contract behaviors tested against FR-822's
      recorded response bodies: submit, publish, placebo, 429 backoff,
      error 9 idempotent success, ToS 0/1 surfaced
- [ ] AC-05: MD parser raises (with offending line) on malformed
      input; tags failing `[a-z0-9_]+` are rejected, not silently
      dropped
- [ ] AC-06: No credentials, tokens, or spike-script imports anywhere
      in the package; `grep -r da_publish_spike examples/` empty
- [ ] AC-07: New CAP/REQ registered; `req_coverage --strict` green;
      tests tagged
- [ ] AC-08: README in the package: one-time auth prerequisite,
      CLI usage, explicit non-scope list (queue/cadence/automation)

## Constraints

- Inherited from FR-822 judgement: no repo credential/token artifacts
  (C-2); spike code not reused (C-5); no graph.yaml/prompts artifacts —
  if a graph ever becomes part of this, it goes through the
  graph-authoring route (C-4).
- No queue, no cadence cap, no launchd wiring, no batch mode, no
  delete/unpublish, no gallery-folder management, no mature
  automation — all deferred until this tool has published once
  (`would_you_use_this`: the automation FR needs this FR's first event
  as its trigger evidence).
- No core `yamlgraph/` changes; example-layer only.

## Alternatives Considered

- Graduating the spike script — forbidden by FR-822 judgement R-3/C-5,
  and rightly: no tests, prints tokens, hardcoded content.
- Building the full pipeline (watch → describe → queue → publish) in
  one FR — rejected as `growth_as_default`; the publisher must prove
  itself on one manual publish first.
- Browser automation of DA Studio — rejected in the research doc; API
  path is complete and proven.

## Related

- `feature-requests/FR-822-deviantart-publish-spike.md` (+ judgement) —
  findings source
- `feature-requests/FR-781-macos-file-hook-example.md` — MD producer
- `docs/research-deviantart-api-2026-08-19.md` — API contract detail
- `.chaplain/inbox/deviantart-auto-publish-pipeline.md` — parent
  proposal (Phase 2 section)

## Judgement (pending)
