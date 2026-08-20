# Judgement: FR-834 GitClaw Oulu Municipal Source

**Verdict:** APPROVED - FR-834 is a clear, bounded single-source GitClaw task.
No technical revisions are required. Human review approved publication and
enforcement on 2026-08-20.

**Prior art:** FR-831 is the direct staged-source parent; FR-832 and FR-833 are
the proven one-source GitClaw witnesses; FR-825 supplies the lossless HTML
charset strategy; FR-828 is the failed monolithic predecessor; FR-829 and
FR-830 supply bounded public-read policy and repository-scoped ledger identity.
FR-834 preserves all of those boundaries and rejects private access, source
rediscovery, platform changes, and code reuse across generated features.

**Reviewed against:** `feature-requests/FR-834-gitclaw-oulu-municipal-source.md`;
`feature-requests/FR-831-oulu-bulletin-staged-source-reuse.md`;
`feature-requests/FR-832-gitclaw-oulu-harbour-source.md`;
`feature-requests/FR-833-gitclaw-oulu-procurement-source.md`;
`feature-requests/FR-825-ktweb-encoding-repair.md`;
`feature-requests/FR-828-gitclaw-oulu-civic-intelligence-cookbook.md`;
`feature-requests/FR-829-gitclaw-read-only-public-tool-policy.md`;
`feature-requests/FR-830-gitclaw-repository-scoped-ledger.md`; and repository
judge doctrine. No private control-plane artifact or chat narrative was used by
the judge.

## What is sound

FR-834 authorizes only Task 4 from FR-831: one official Oulu KTweb
public-notice index. It excludes agendas, minutes, officer decisions, detail or
attachment retrieval, composition, and bulletin synthesis.

The executable contract freezes one URL, transport and decompressed-byte
bounds, same-host/same-path redirect validation, HTTP/media checks, charset
declaration precedence, strict decoding, structured table parsing, stable
`docid` identity, calendar-date validation, invalid-row accounting,
deduplication, ordering, and a five-record cap. The exact issue body repeats the
closed contract without depending on private memory or access.

The strategic classification is **contrib/example acceptance task**, not a new
YAMLGraph primitive. Deterministic retrieval, decoding, parsing, validation,
selection, links, and rendering remain code-owned.

## Required revisions

None.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | One unlabelled owner-authored issue titled `Oulu municipal notice source snapshot` with the exact FR-834 body |
| D-2 | One `features/oulu-municipal-notice-source-snapshot/` generated directory |
| D-3 | Normal provenance, graph, prompt, deterministic tool, tests, synthetic fixtures, report, and review under that directory |
| D-4 | Focused tests, lint, synthetic Windows-1252 fixture/live smoke, containment, independent review, and terminal ledger evidence |
| D-5 | FR-834 closure evidence recording issue, run, commit, validation, deviations, and failures |

Not authorized: manual implementation; edits or retries to issues #1-#3;
another source route; detail/attachment fetches; agendas, minutes, officer
decisions; harbour/procurement imports; cross-source composition; shared-library
or dependency changes; LLM fact selection or synthesis; removal inference;
cron/workflow/runtime/policy changes; secrets; notifications; final publication;
private control-plane access; or raw live-response fixture capture.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Human review approves and publishes this judgement before issue creation. | GATE |
| C-2 | The issue body is complete and public-safe; no private access or rediscovery. | GATE |
| C-3 | Generated paths stay under the expected feature directory except normal ledger state. | GATE |
| C-4 | Live evidence records only health, charset, counts, selected IDs/dates, and link modes; no raw response or live fixture. | GATE |
| C-5 | Any platform, dependency, containment, policy, workflow, shared-reuse, or composition need stops for a separate FR. | GATE |
| C-6 | Independent review approval is required before push and issue close. | GATE |

Authority granted: after C-1, create exactly the FR-834 public issue and allow
GitClaw to generate, validate, review, push, and close only the contained Oulu
KTweb public-notice source snapshot described above.
