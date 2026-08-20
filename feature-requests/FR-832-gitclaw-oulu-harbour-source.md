# Feature Request: FR-832 GitClaw Oulu Harbour Source

**Priority:** HIGH
**Type:** Feature / GitClaw acceptance task
**Status:** Judged — APPROVED WITH REVISIONS folded (2026-08-20); enforcement
authorized
**Effort:** 0.5 day
**Requested:** 2026-08-20
**Parent:** FR-831
**Depends on:** FR-827, FR-829, FR-830, FR-831
**Prior art:** FR-831 provides the reviewed Harbour transfer packet and requires
one bounded source judgement at a time. FR-828 is the failed monolithic Oulu
issue and remains preserved, not retried. The private control-plane
Digitraffic probe is provenance only; its public contract is reused through the
reviewed packet, while its replacement decoding, raw detail retention, and
post-fetch-only bound are rejected. FR-824 supplies source-health and
transport-boundary precedent but no harbour implementation is copied.
**First consumer / first event:** A reader of the public Oulu cookbook
repository, when issue #2 autonomously produces and validates one contained
`FIOUL` harbour source snapshot without implementing another source or bulletin
synthesis.

## Summary

Use one owner-authored issue in
`sheikkinen/gitclaw-oulu-civic-intelligence` to make GitClaw generate a
contained Digitraffic Marine feature. The feature retrieves Oulu (`FIOUL`) port
calls from the reviewed public endpoint, selects the earliest strictly future
ETA deterministically, and emits one bounded Markdown source snapshot with
explicit health and provenance.

This is Task 2 of FR-831. It validates one adapter contract; it does not claim
that the adapter is already reusable across feature directories. Hilma, Oulu
KTweb, cross-source composition, LLM condensation, and final bulletin
publication remain separate tasks.

## Value Statement

The Oulu bulletin gains a tested harbour source artifact without asking one
GitClaw enforcement call to discover or implement unrelated sources.

## Ideal Result

A public issue closes with governed feature artifacts and a contained,
fixture-tested harbour tool. A live smoke names the next future Oulu port call
or reports source unavailability honestly. Every value is derived from the
bounded Digitraffic response, cargo is never invented, and no private
control-plane access is needed.

## Closed Input

The issue may use only this human-reviewed public contract:

- Public unauthenticated GET origin:
  `https://meri.digitraffic.fi/api/port-call/v1/port-calls?locode=FIOUL`.
- Request gzip with a 5-second connection timeout, 15-second total/read timeout,
  and 1 MiB maximum decompressed response. Read at most limit plus one byte and
  reject overflow; do not retain the raw response.
- Parse JSON structurally and decode strict UTF-8. Reject invalid JSON,
  unsupported/undecodable text, and U+FFFD.
- Require a top-level `portCalls` list. Treat missing/wrong-typed required
  structure as `invalid`, not an empty successful source.
- Stable identity is `portCallId`.
- For every call, derive its candidate ETA as the earliest parseable `eta`
  inside `portAreaDetails`. Select only ETAs strictly later than the supplied
  run instant. Sort by `(eta, string(portCallId))` for deterministic ties.
- Normalize selected call ID, vessel name, ETA, previous port, next port,
      berth/port-area details when present, vessel type code, and exact source URL.
- When vessel type code exists, render exactly
      `Vessel type hint: code <code> (hint only; cargo unknown)`. Omit the line when
      the code is absent. No free-text vessel label or mapping is authorized. Never
      infer or name a cargo commodity, vessel purpose, or type label.
- Fetch/network/timeout failures are `unavailable`; contract, decoding, size,
  timestamp, and JSON failures are `invalid`; a valid response with no future
  call is `ok` with an explicit no-upcoming-call result.

The source-specific implementation must reverify current response shape and
field nullability in a bounded live smoke. It must record observations without
committing a raw response.

## Exact GitHub Issue

Create one unlabelled owner-authored issue in the public cookbook repository.
The normal trusted-owner `opened` event is the sole trigger.

**Title:** `Oulu harbour source snapshot`

**Body:**

> **Public provenance:** This contract is the reviewed Harbour transfer from
> [FR-831](https://github.com/sheikkinen/yamlgraph/blob/main/feature-requests/FR-831-oulu-bulletin-staged-source-reuse.md),
> narrowed and governed by
> [FR-832](https://github.com/sheikkinen/yamlgraph/blob/main/feature-requests/FR-832-gitclaw-oulu-harbour-source.md)
> and its
> [judgement](https://github.com/sheikkinen/yamlgraph/blob/main/feature-requests/FR-832-gitclaw-oulu-harbour-source.judgement.md).
> These public documents are provenance only; this issue contains the complete
> executable contract. Do not access the private control-plane repository or
> rediscover the source contract.
>
> Implement one contained GitClaw feature for the Oulu harbour source. Do not
> implement the full civic bulletin.
>
> Retrieve only
> `https://meri.digitraffic.fi/api/port-call/v1/port-calls?locode=FIOUL` with an
> unauthenticated HTTP GET and gzip support. Use a 5-second connection timeout,
> 15-second total/read timeout, and a 1 MiB maximum decompressed response. Read
> at most the limit plus one byte and reject overflow. Never commit or retain a
> raw response body.
>
> Decode strict UTF-8 and parse JSON structurally. Reject undecodable text,
> U+FFFD, invalid JSON, and a missing or non-list `portCalls`. For each call,
> derive its candidate ETA from the earliest parseable `eta` in
> `portAreaDetails`. The graph accepts `date` and an ISO-8601 UTC
> `run_instant`. Fixture tests and fixture smoke must supply a frozen
> `run_instant`; live/cron execution may default it to current UTC only when it
> is omitted. Record the selected instant in smoke evidence. Compare ETAs to
> `run_instant`, never to calendar `date`; select the earliest ETA strictly
> later than it and break equal-ETA ties by string `portCallId`.
>
> Normalize only `portCallId`, vessel name, ETA, previous port, next port,
> berth/port-area details when present, vessel type code, and exact source URL.
> If the code exists, render exactly
> `Vessel type hint: code <code> (hint only; cargo unknown)`; omit that line
> when code is absent. Do not map codes to free-text labels or infer cargo,
> vessel purpose, or type from vessel name, route, ports, berth, or an LLM.
>
> Emit exactly one non-empty Markdown candidate beginning with the requested
> date. Include `Source health: ok|unavailable|invalid`, the exact source URL,
> and either the selected future call or an explicit no-upcoming-call/failure
> statement. Do not use an LLM to choose, alter, or invent source facts.
>
> Keep implementation, fixtures, and tests entirely under this generated
> feature directory and use only the Python standard library plus the existing
> GitClaw/YAMLGraph runtime. Tests must cover: future versus past selection,
> equal-ETA tie, no future calls, nullable optional fields, timeout/network
> failure, oversized response, invalid UTF-8/U+FFFD, invalid JSON, wrong
> `portCalls` type, and cargo-inference absence. Run focused tests, graph lint,
> and one bounded live smoke; report all evidence honestly in
> `authoring-report.md`.
>
> Exclude Hilma, KTweb, other origins, cross-source composition, shared-library
> changes, LLM synthesis, cron/workflow/runtime/policy changes, secrets,
> notifications, and final bulletin publication.

## Generated Feature Contract

The expected slug is `oulu-harbour-source-snapshot`. GitClaw must generate the
normal governed artifacts under that feature directory only. Optional tools,
tests, and bounded fixtures belong below the same directory.

The graph must accept `date` and ISO-8601 UTC `run_instant`. Fixture tests and
fixture smoke supply a frozen value. Live and cron execution may default
`run_instant` to current UTC only when omitted, and smoke evidence records the
selected instant. ETA comparisons use `run_instant`, never calendar `date`.
Source selection and Markdown rendering are deterministic code. The required
prompt artifact may document the no-synthesis contract, but no LLM may choose,
rewrite, label, or fill source facts.

The feature is independently runnable and cron-compatible, but its existence
does not authorize imports from another generated feature. Task 5 of FR-831
still owns the shared reuse/composition boundary.

## Validation

GitClaw enforcement must provide:

1. focused deterministic tests for every issue-listed case;
2. graph lint;
3. fixture smoke with frozen run instant and selected expected call;
4. bounded live smoke recording health, item count, and selected stable ID only;
5. containment proof; and
6. independent review approval before push and issue close.

Live source unavailability does not justify invented data or weakening fixture
tests. A judge/reviewer rejection is a legitimate pipeline outcome but does not
satisfy the positive acceptance witness.

## Acceptance Criteria

- [x] AC-01: FR-832 is governed-judged and R-1 through R-3 are folded before
      public issue creation
- [ ] AC-02: Exact owner-authored issue `Oulu harbour source snapshot` is filed
      without a label and contains public FR-831, FR-832, and judgement
      provenance without requiring private control-plane access
- [ ] AC-03: Intake reaches plan, judge, enforce, review, containment, push, and
      closed terminal ledger state without touching interrupted issue #1
- [ ] AC-04: Generated provenance includes `FR.md`, `judgement.md`, `review.md`,
      `authoring-report.md`, `graph.yaml`, prompts, contained tool, tests, and
      bounded fixtures
- [ ] AC-05: Retrieval uses only the frozen FIOUL origin, gzip, finite timeouts,
      strict 1 MiB decompressed bound, strict UTF-8, and structured JSON parsing
- [ ] AC-06: Graph accepts `date` and `run_instant`; fixtures freeze the latter;
      live execution may default current UTC; selection uses earliest ETA after
      `run_instant` and deterministic `portCallId` tie-breaking; valid no-future
      input remains explicit `ok`
- [ ] AC-07: Output exposes exact source URL, selected run instant, and health,
      preserves normalized facts, uses only the folded code-only hint format,
      and contains no cargo claim or invented type label
- [ ] AC-08: Tests cover all exact issue cases, including unknown/missing vessel
      type code and cargo-inference absence, and pass
- [ ] AC-09: Graph lint and fixture smoke pass; fixture smoke freezes
      `run_instant` and asserts the expected selected call
- [ ] AC-10: Bounded live smoke records no raw response and records health, item
      count, selected stable ID if any, and run instant without weakening
      deterministic validation
- [ ] AC-11: Diff containment proves all generated implementation paths stay
      under `features/oulu-harbour-source-snapshot/` plus ledger state
- [ ] AC-12: No Hilma, KTweb, composition, shared-library, synthesis, workflow,
      runtime, policy, secret, notification, or final-publication change occurs
- [ ] AC-13: FR-832 records issue, intake run, generated commit, ledger close,
      validation evidence, deviations, and any failed attempt

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-831 | Direct parent and reviewed source contract; preserve one-task-at-a-time and composition stop gates |
| FR-828 | Preserve both failures; do not retry or manually repair issue #1 |
| FR-829 | Preserve bounded read-only public retrieval policy and no-secret boundary |
| FR-830 | Reuse repository-scoped ledger identity without modification |
| Control-plane Digitraffic probe | Reuse public endpoint, identity, ETA, gzip, and cargo caveat through the approved packet; reject exploratory decoding/detail/bounding behavior |
| FR-824 source adapters | Reuse transport-boundary and health honesty principles only; do not copy HVA scope or state model |

## Alternatives Rejected

- **Implement all three sources:** repeats FR-828's abstraction-span failure.
- **Hand-code the adapter:** invalidates the GitClaw acceptance witness.
- **Increase enforcement timeout:** hides rather than removes task overload.
- **Treat first sorted call as next:** can publish a past call.
- **Use an LLM for selection or missing fields:** source facts and ordering are
  deterministic and validator-covered.
- **Claim cross-feature reuse now:** current policy and containment do not
  establish that import boundary.

## Scope Fence

FR-832 authorizes one separately governed public issue and its generated
single-source harbour feature. It authorizes no manual implementation and no
other FR-831 task. Any GitClaw platform defect stops enforcement for a separate
platform FR.
