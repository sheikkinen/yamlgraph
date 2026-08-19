# Judgement: FR-822 DeviantArt API Publish Spike

**Verdict:** APPROVED WITH REVISIONS — the spike is strategically sound and already answers the Phase-2 unknowns, but authority activates only after the FR fixes the credential-location contradiction and makes the completed evidence mechanically auditable.

**Reviewed against:** `feature-requests/FR-822-deviantart-publish-spike.md`; `docs/research-deviantart-api-2026-08-19.md`; `.chaplain/inbox/deviantart-auto-publish-pipeline.md`; `feature-requests/FR-781-macos-file-hook-example.md`; `feature-requests/FR-769-shared-vision-tool.md`; `feature-requests/FR-772-tool-call-inline-dict-args.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`.

**Prior art:** dispositioned in "What is sound" below — FR-781 (Phase-1 MD generator, stops before publishing) and FR-769 (shared vision tool) are complementary; FR-772 is noun coincidence; FR-822 itself is the subject FR.

## What is sound

The proposal is correctly scoped as a one-publish research spike, not a publisher implementation: it names the Phase-2 publisher as first consumer and the first event as one real API publish of `tmp/da.png` (`FR-822` lines 9-12), while the consumer proposal explicitly gates batch authority on one manual API-publish spike (`.chaplain/inbox/deviantart-auto-publish-pipeline.md` lines 91-95).

The research basis is real and decision-bearing, not inventory. The research doc establishes the two-call API flow and required AI/NoAI/mature fields (`docs/research-deviantart-api-2026-08-19.md` lines 15-49), the OAuth 2.1 PKCE/refresh-token constraints (`docs/research-deviantart-api-2026-08-19.md` lines 51-66), and the exact open questions this spike must answer (`docs/research-deviantart-api-2026-08-19.md` lines 80-87). FR-822 then records concrete response bodies and answers for all three questions (`FR-822` lines 130-150).

The prior-art disposition is adequate. FR-781 owns the WatchPaths-triggered DeviantArt markdown generator and explicitly stops before publishing (`FR-781` lines 25-36 and 67-83); FR-769 owns the shared image-to-text vision boundary (`FR-769` lines 15-21 and 73-75); FR-772 owns inline dict tool-call args (`FR-772` lines 11-26). FR-822's API-publish spike is therefore complementary, not duplicate (`FR-822` lines 14-21).

Strategic classification: **Pattern documentation / research evidence**. This is not a framework primitive and not a reusable contrib example yet; it is a deliberately narrow field probe whose findings unblock a later Phase-2 FR. That matches the repo doctrine preference for research before coding (`.github/copilot-instructions.md` lines 208-214) and the consumer proposal's two-phase decomposition (`.chaplain/inbox/deviantart-auto-publish-pipeline.md` lines 41-83).

## Required revisions

### R-1: Resolve the credential-location contradiction

Revise the FR so its credential contract is internally consistent and safe. The Proposed Solution says credentials come from `~/.env` and tokens from `~/.deviantart/token.json` with `0600` permissions (`FR-822` lines 63-68), and the Constraints forbid credentials or token files in the repo (`FR-822` lines 101-102). But Implementation Notes say "Creds in repo `.env`" (`FR-822` lines 125-128), contradicting both FR-822 and the consumer proposal's "keychain/env, never repo" rule (`.chaplain/inbox/deviantart-auto-publish-pipeline.md` lines 69-76 and 92-95).

Fold this mechanically by replacing the implementation note with an explicit secret-disposition sentence: credentials are outside the repository (`~/.env`, Keychain, or equivalent operator-local path), `~/.deviantart/token.json` is `0600`, no committed artifact contains access tokens, refresh tokens, client secrets, or terminal transcripts containing them, and any repo-root credential file used during the spike has been removed and the client secret disposition recorded.

### R-2: Convert completed checkboxes into evidence-anchored audit criteria

The current acceptance criteria are marked complete (`FR-822` lines 84-97), but several are only self-attested unless the FR records the concrete witness: `0600` token permissions, live page paragraph rendering, AI/NoAI badge, tag attachment, and refresh-token rotation. The judge doctrine requires measurable criteria, not aspirational prose (`.github/skills/judge-fr/doctrine.md` lines 43-44), and repo doctrine says "read_raw_output_first" means raw artifacts must be read before judging conclusions (`.github/copilot-instructions.md` lines 115-116 and 232).

Fold this by rewriting the AC list to the revised ACs below and adding the missing witness details directly to the FR: command/transcript excerpt or stated file-mode observation for token permissions; the three paragraph starts observed on the live deviation; the visible AI badge / NoAI / five tags evidence; and a non-secret rotation witness such as "refresh_token field changed and persisted at `<timestamp>`" without storing token values.

### R-3: Quarantine the spike script as non-production evidence

The FR's test exception is acceptable only if the script remains a condemned spike, not reusable production code. FR-822 says no tests are required because the spike code is "condemned at birth" (`FR-822` lines 107-109), while repo doctrine requires witness tests for production branches (`.github/copilot-instructions.md` lines 220-233). Those can coexist only if the script is explicitly barred from being imported or reused by Phase 2.

Fold this by adding a disposition note: `scripts/spikes/da_publish_spike.py` is a non-production witness script; Phase 2 may inherit only the recorded findings and endpoint/auth contracts, not the code; any reusable DeviantArt publisher, queue processor, token store, or retry/idempotency implementation requires its own judged FR and normal TDD.

### R-4: Name the human-visible observation method

The spike's second and fourth questions depend on what DeviantArt rendered to a human. FR-822 records that paragraph rendering was fetched and observed (`FR-822` lines 143-146) and that tags/AI badge were confirmed (`FR-822` lines 152-153), but does not name the observation method, timestamp, or page evidence. Because the research doc says docs do not state paragraph formatting (`docs/research-deviantart-api-2026-08-19.md` lines 80-87), this live observation is a primary witness and must be auditable.

Fold this by adding a short "Live page witness" note with timestamp, URL, observation method (`browser` or `curl`/fetch), three paragraph-start snippets, visible tags, and visible AI/NoAI flag evidence. Do not include cookies, HTML containing account/session tokens, or private profile data.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-822-deviantart-publish-spike.md` with credential disposition, completed evidence, and quarantined-spike status |
| D-2 | Non-production witness script `scripts/spikes/da_publish_spike.py`, only if it contains no credentials/tokens and is clearly marked throwaway |
| D-3 | Recorded API findings for Phase 2: PKCE + refresh rotation, `stash/submit`, `stash/publish`, ToS error behavior, paragraph rendering, tags, AI/NoAI flags |

Not authorized: any reusable DeviantArt publisher; queue processing; launchd/file-hook changes; graph or prompt artifact authoring; batch publish cadence; retry/backoff/idempotency implementation; gallery-folder management; delete/unpublish support; mature-classification automation; browser automation; core `yamlgraph/` changes; dependency changes; committing `.env`, token files, terminal transcripts with token values, cookies, or private account HTML.

## Revised acceptance criteria

- [ ] AC-01: FR records the exact successful OAuth/token exchange shape without secret values: scopes, 1-hour access-token expiry, refresh-token presence, token file path, and `0600` permission observation.
- [ ] AC-02: FR records `placebo` success response body exactly: `{"status":"success"}`.
- [ ] AC-03: FR records `stash/submit` success response body exactly, including `itemid`, `stack`, and `stackid`, without any bearer token or secret.
- [ ] AC-04: FR records `stash/publish` success response body exactly, including deviation URL and `deviationid`, without any bearer token or secret.
- [ ] AC-05: FR answers ToS/submission-policy question explicitly: publish error codes `0`/`1` did not fire for the tested account; Phase 2 surfaces them if they appear for a fresh account.
- [ ] AC-06: FR includes a live-page witness note proving plain text `\n\n` rendered as separate paragraphs, with timestamp, observation method, URL, and three paragraph-start snippets.
- [ ] AC-07: FR records a second-run refresh witness: refresh returned a new `refresh_token` and the persisted token file was updated, without storing the token value.
- [ ] AC-08: FR records visible DeviantArt flags/tags evidence: AI-generated badge, NoAI state where visible, and all five submitted tags attached.
- [ ] AC-09: FR records spike disposition: script remains throwaway/non-production; Phase 2 inherits findings only and must not copy the spike script as production code without a new judged FR.
- [ ] AC-10: FR records credential disposition: no repo-committed credential/token artifacts; runtime credential path outside the repository; any repo-root credential file used during the spike removed and secret disposition recorded.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority activates only after R-1..R-4 are folded into FR-822; until then the spike findings are advisory evidence, not Phase-2 authority. | GATE |
| C-2 | Do not commit credentials, token JSON, cookie-bearing HTML, or terminal transcripts containing access/refresh tokens or client secrets. | GATE |
| C-3 | Do not implement Phase-2 publisher behavior under this FR; only record the spike and quarantine the witness script. | GATE |
| C-4 | If any graph.yaml or prompts/*.yaml artifact becomes part of follow-up work, it must use the graph-authoring route; FR-822 itself authorizes none. | GATE |
| C-5 | Any reusable code graduated from the spike must re-enter as a new judged FR with tests, requirement traceability where applicable, and secret-handling constraints. | GATE |

Authority granted: after the revisions are folded, FR-822 may stand as the completed research-spike record and as evidence for writing a separate Phase-2 DeviantArt publisher FR; it does not authorize production publisher implementation.
