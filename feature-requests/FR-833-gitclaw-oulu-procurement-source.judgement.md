# Judgement: FR-833 GitClaw Oulu Procurement Source

**Verdict:** APPROVED - FR-833 is a clear, one-source GitClaw acceptance task
with closed public inputs, deterministic relevance rules, bounded retrieval,
contained generated-feature scope, and mechanically checkable validation.
Human review approved publication and enforcement on 2026-08-20.

**Prior art:** FR-831 is the direct staged-source parent; FR-832 is the proven
one-source GitClaw witness; FR-828 is the failed monolithic predecessor; FR-829
and FR-830 provide the bounded public-read and repository-scoped ledger
prerequisites. FR-833's Prior Art Disposition table preserves those boundaries
and rejects private access, source rediscovery, platform changes, and code reuse
across generated features.

**Reviewed against:** `feature-requests/FR-833-gitclaw-oulu-procurement-source.md`;
`feature-requests/FR-831-oulu-bulletin-staged-source-reuse.md`;
`feature-requests/FR-832-gitclaw-oulu-harbour-source.md`;
`feature-requests/FR-828-gitclaw-oulu-civic-intelligence-cookbook.md`;
`feature-requests/FR-829-gitclaw-read-only-public-tool-policy.md`;
`feature-requests/FR-830-gitclaw-repository-scoped-ledger.md`; and repository
judge doctrine. No private control-plane artifact or chat narrative was used by
the judge.

## What is sound

FR-833 implements one concern: a contained Hilma procurement source snapshot.
It freezes one public query, strict transport and parser bounds, stable identity,
invalid-record behavior, deterministic deduplication and ordering, a five-item
cap, stable/fallback link construction, explicit source health, and bounded
coverage language.

The relevance predicate is mechanically discriminating. It accepts structured
authority or postal-locality evidence, or exact `FI1D9` location combined with
an Oulu whole-word title token. It rejects query-hit status, arbitrary
substring, NUTS alone, title alone, description, URL, and LLM inference. This
supports the parent stop gate for false-positive and source-link tests.

The strategic classification is **contrib/example acceptance task**, not a
YAMLGraph primitive. Deterministic retrieval, selection, links, and rendering
remain code-owned, while prompts only document the no-synthesis boundary.

## Required revisions

None.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | One unlabelled owner-authored issue titled `Oulu procurement source snapshot` with the exact FR-833 body |
| D-2 | One `features/oulu-procurement-source-snapshot/` generated directory |
| D-3 | Normal provenance, graph, prompt, deterministic tool, tests, synthetic fixtures, report, and review under that directory |
| D-4 | One exact Hilma query with frozen relevance, deduplication, ordering, links, health, and Markdown output |
| D-5 | Focused tests, lint, fixture/live smoke, containment, independent review, and terminal ledger evidence |
| D-6 | FR-833 closure evidence recording issue, run, commit, validation, deviations, and failures |

Not authorized: manual implementation; edits to issue #1 or #2; Digitraffic,
KTweb, or other sources; query variants or CPV loops; cross-source composition;
shared-library, dependency, platform, runtime, policy, or workflow changes;
secrets or authentication; browser/SPA detail retrieval; raw response retention;
LLM fact selection or synthesis; notifications; or final publication.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Human review approves and publishes this judgement before issue creation. | GATE |
| C-2 | The issue body is complete and public-safe; no private access or rediscovery. | GATE |
| C-3 | Generated paths stay under the expected feature directory except normal ledger state. | GATE |
| C-4 | Any platform, workflow, dependency, containment, policy, or shared-library need stops for a separate FR. | GATE |
| C-5 | Live unavailability cannot weaken fixtures, broaden relevance, invent data, or add queries. | GATE |
| C-6 | Independent review approval is required before push and issue close. | GATE |

Authority granted: after C-1, create exactly the FR-833 public issue and allow
GitClaw to generate, validate, review, push, and close only the contained Oulu
Hilma procurement source snapshot described above.
