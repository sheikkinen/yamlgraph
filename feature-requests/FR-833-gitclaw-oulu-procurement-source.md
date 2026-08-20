# Feature Request: FR-833 GitClaw Oulu Procurement Source

**Priority:** HIGH
**Type:** Feature / GitClaw acceptance task
**Status:** Enforced 2026-08-20 — issue #3 completed; 11/11 ACs satisfied
**Effort:** 0.5 day
**Requested:** 2026-08-20
**Parent:** FR-831
**Depends on:** FR-829, FR-830, FR-831, FR-832
**Prior art:** FR-831 supplies the human-reviewed Procurement transfer packet
and requires one bounded source judgement at a time. FR-832 proves that a
single-source GitClaw issue can reach contained closure. FR-828 remains the
failed monolithic predecessor and must not be retried. The private
control-plane Hilma probe is provenance only: reuse its public origin,
publication ordering, identity, normalized fields, and stable-link rule, while
rejecting replacement decoding, repeated custom queries, and untested
substring relevance.
**First consumer / first event:** A reader of the public Oulu cookbook
repository, when one owner-authored issue autonomously produces and validates
a contained Hilma procurement snapshot without implementing another source or
bulletin synthesis.

## Summary

Use one owner-authored issue in
`sheikkinen/gitclaw-oulu-civic-intelligence` to make GitClaw generate a
contained Hilma eForms feature. It retrieves one bounded, publication-ordered
candidate set for `Oulu`, applies a deterministic structured relevance
predicate, deduplicates by eForm ID, and emits one bounded Markdown source
snapshot with explicit health, coverage limits, and stable public links.

This is Task 3 of FR-831. It does not import the harbour feature or establish a
cross-feature composition boundary. KTweb, shared reuse, source assembly, LLM
condensation, and final publication remain separate tasks.

## Value Statement

The Oulu bulletin gains a tested procurement source whose inclusion rule and
links are mechanically auditable instead of treating Hilma full-text search as
proof of local relevance.

## Ideal Result

A public issue closes with governed feature artifacts and a contained,
fixture-tested Hilma tool. The output lists at most five newest qualifying
notices, identifies why each notice qualifies, links to the stable Hilma
procedure/notice route when available, and never claims complete Oulu market
coverage or retrieved SPA detail text.

## Closed Input

The issue may use only this human-reviewed public contract:

- Public unauthenticated GET origin:
  `https://www.hankintailmoitukset.fi/search/eformnotices`.
- Exact candidate query: `search=Oulu`, `queryType=full`, `$top=20`, and
  `$orderby=datePublished desc`. Make one request only; no CPV loop or query
  variants.
- Request gzip with a 5-second connection timeout, 15-second total/read timeout,
  and 2 MiB maximum decompressed response. Read at most limit plus one byte and
  reject overflow; do not retain the raw response.
- Decode strict UTF-8, reject U+FFFD, and parse JSON structurally. Require a
  top-level `value` list; wrong-typed required structure is `invalid`.
- Stable identity is non-empty eForm `id`, normalized as `hilma-{id}`.
  Duplicate IDs collapse deterministically before output.
- Normalize only ID, title, contracting authority, publication date, deadline
  when present, `noticeId`, `procedureId`, notice type, CPV codes,
  procurement-document URL, exact candidate-query URL, detail URL, and a
  machine-readable relevance reason.
- Build a detail URL as
  `https://www.hankintailmoitukset.fi/fi/public/procedure/{procedureId}/enotice/{noticeId}/`
  only when both path components are non-empty scalar values. Percent-encode
  each path component. Otherwise use the bounded fallback
  `https://www.hankintailmoitukset.fi/fi/search?search={percent-encoded id}` and
  mark `detail limitation: search fallback; full SPA detail not retrieved`.
- Prefer non-empty Finnish, then English title and authority fields. Missing
  required ID, title, authority, or parseable `datePublished` makes that record
  invalid and excluded while recording an invalid-record count; it does not
  invalidate other records in an otherwise valid envelope.

## Frozen Oulu Relevance Predicate

Normalize comparison text with Unicode NFKC, case-folding, and collapsed
whitespace. A record qualifies through exactly one of these ordered branches:

1. `authority`: the normalized contracting-authority name contains a complete
   Unicode word token `oulu` or `oulun`, or `organisationAddress` contains a
   complete postal-locality line matching five digits followed by `Oulu` or
   `Oulun kaupunki`; or
2. `located-project`: top-level `nutsCodes` or any structured `lots[].nutsCodes`
   contains exact code `FI1D9`, and the selected title contains a complete
   Unicode word token `oulu` or `oulun`.

The implementation must not qualify a record from query-hit status, arbitrary
substring, NUTS alone, title alone, description text, procurement-document URL,
or an LLM. If both branches match, use reason `authority`. This deliberately
prefers precision over completeness and must be stated in output.

After filtering, sort by descending parsed `datePublished`, then string `id`
ascending, and emit at most five records. A valid response with no qualifying
record is `ok`, not a source failure.

## Exact GitHub Issue

Create one unlabelled owner-authored issue in the public cookbook repository.
The trusted-owner `opened` event is the sole trigger.

**Title:** `Oulu procurement source snapshot`

**Body:**

> **Public provenance:** This contract is the reviewed Procurement transfer
> from
> [FR-831](https://github.com/sheikkinen/yamlgraph/blob/main/feature-requests/FR-831-oulu-bulletin-staged-source-reuse.md),
> narrowed and governed by
> [FR-833](https://github.com/sheikkinen/yamlgraph/blob/main/feature-requests/FR-833-gitclaw-oulu-procurement-source.md)
> and its
> [judgement](https://github.com/sheikkinen/yamlgraph/blob/main/feature-requests/FR-833-gitclaw-oulu-procurement-source.judgement.md).
> These public documents are provenance only; this issue contains the complete
> executable contract. Do not access the private control-plane repository or
> rediscover the source contract.
>
> Implement one contained GitClaw feature for the Oulu Hilma procurement
> source. Do not implement the civic bulletin or another source.
>
> Retrieve only
> `https://www.hankintailmoitukset.fi/search/eformnotices` with one
> unauthenticated gzip GET using `search=Oulu`, `queryType=full`, `$top=20`, and
> `$orderby=datePublished desc`. Use a 5-second connection timeout, 15-second
> total/read timeout, and 2 MiB maximum decompressed response. Read at most the
> limit plus one byte and reject overflow. Never retain a raw response body.
>
> Decode strict UTF-8, reject U+FFFD, and parse JSON structurally. Require a
> top-level `value` list. Deduplicate records by non-empty eForm `id`. Prefer
> Finnish then English title and authority. A record missing ID, title,
> authority, or parseable `datePublished` is excluded and counted invalid.
>
> Normalize comparison text with Unicode NFKC, case-folding, and collapsed
> whitespace. A record qualifies as `authority` when the authority has a whole
> word `oulu` or `oulun`, or `organisationAddress` has a complete postal line
> of five digits plus `Oulu` or `Oulun kaupunki`. Otherwise it qualifies as
> `located-project` only when top-level `nutsCodes` or a structured
> `lots[].nutsCodes` contains exact `FI1D9` and the selected title has a whole
> word `oulu` or `oulun`. Do not qualify from search-hit status, substring,
> NUTS alone, title alone, description, URL, or an LLM. Prefer `authority` when
> both branches match.
>
> Sort qualifying records by descending parsed `datePublished`, then string ID
> ascending, and emit at most five. Normalize only ID, title, authority,
> publication date, optional deadline, notice/procedure IDs, notice type, CPV
> codes, procurement-document URL, exact query URL, detail URL, and relevance
> reason. Build the detail URL from percent-encoded `procedureId` and
> `noticeId` only when both exist; otherwise use a percent-encoded Hilma search
> URL for the eForm ID and mark `detail limitation: search fallback; full SPA
> detail not retrieved`.
>
> Emit exactly one non-empty Markdown candidate beginning with the requested
> `date`. Include `Source health: ok|unavailable|invalid`, exact query URL,
> candidate count, qualifying count, invalid-record count, bounded-coverage
> warning, and either up to five records or an explicit no-qualifying/failure
> statement. A valid empty result is `ok`. Fetch/timeout failures are
> `unavailable`; response-size, decoding, envelope, and JSON failures are
> `invalid`. Do not claim complete Oulu coverage or retrieved SPA detail text.
>
> Keep implementation, synthetic fixtures, and tests entirely under this
> generated feature directory. Use only the Python standard library plus the
> existing GitClaw/YAMLGraph runtime. Tests must cover: authority word-token
> match; postal-locality match; exact NUTS plus title-token match; substring,
> NUTS-only, title-only, description-only, and query-hit false positives;
> Finnish/English fallback; duplicate IDs; deterministic ordering and five-item
> cap; stable and fallback link encoding; missing/invalid records; empty valid
> results; timeout/network failure; oversized response; invalid UTF-8/U+FFFD;
> invalid JSON; and wrong `value` type. Run focused tests, graph lint, a
> synthetic fixture smoke, and one bounded live smoke. Record honest evidence
> without raw response data in `authoring-report.md`.
>
> Exclude Digitraffic, KTweb, other origins, query variants, CPV loops,
> cross-source composition, shared-library changes, LLM fact selection or
> synthesis, cron/workflow/runtime/policy changes, secrets, notifications, and
> final publication.

## Generated Feature Contract

The expected slug is `oulu-procurement-source-snapshot`. GitClaw generates the
normal governed artifacts under that feature directory only. Optional tools,
tests, and bounded synthetic fixtures belong below the same directory.

The graph accepts `date`. Retrieval, relevance, deduplication, ordering, link
construction, and Markdown rendering are deterministic code. A prompt artifact
may document the no-synthesis boundary, but no LLM chooses, rewrites, labels,
or fills source facts.

The feature is independently runnable and cron-compatible. It does not import
another generated feature; Task 5 of FR-831 still owns shared reuse.

## Validation

GitClaw enforcement must provide:

1. focused deterministic tests for every issue-listed positive, false-positive,
   transport, parser, deduplication, ordering, and link case;
2. graph lint;
3. synthetic fixture smoke proving both accepted relevance branches and at
   least two rejected false-positive branches;
4. one bounded live smoke recording health, candidate/qualifying/invalid counts,
   selected IDs and relevance reasons, and link mode only;
5. containment proof; and
6. independent review approval before push and issue close.

Live source unavailability does not authorize invented data, a broader
predicate, or weaker fixtures.

## Acceptance Criteria

- [x] AC-01: The governed judgement is human-reviewed and published before
  public issue creation
- [x] AC-02: Exact unlabelled owner-authored issue contains public FR-831,
      FR-833, and judgement provenance without private access
- [x] AC-03: Intake reaches terminal closed ledger state without modifying
      interrupted issue #1 or completed issue #2
- [x] AC-04: Generated provenance, graph, prompt, contained tool, tests,
      synthetic fixtures, report, and review exist under the expected slug
- [x] AC-05: One exact Hilma query uses finite timeout and decompressed-byte
      bounds, strict UTF-8/U+FFFD rejection, structured JSON, and no raw body
- [x] AC-06: Stable ID, invalid-record handling, deterministic deduplication,
      publication ordering, and five-record output cap match the frozen contract
- [x] AC-07: Relevance tests prove both accepted branches and reject substring,
      NUTS-only, title-only, description-only, and query-hit false positives
- [x] AC-08: Stable procedure/notice links and encoded fallback links are tested;
      output marks SPA and bounded-coverage limitations
- [x] AC-09: Focused tests, graph lint, synthetic fixture smoke, bounded live
      smoke, containment, and independent review pass
- [x] AC-10: No other source, query variant, CPV loop, composition, shared
      library, synthesis, workflow/runtime/policy, secret, or publication change
- [x] AC-11: FR-833 records issue, run, generated commit, ledger close,
      validation evidence, deviations, and failed attempts

## Implementation Evidence (2026-08-20)

The exact unlabelled owner-authored issue
[`sheikkinen/gitclaw-oulu-civic-intelligence#3`](https://github.com/sheikkinen/gitclaw-oulu-civic-intelligence/issues/3)
triggered intake run
[`32338288632`](https://github.com/sheikkinen/gitclaw-oulu-civic-intelligence/actions/runs/32338288632).
The workflow completed successfully in 15.4 minutes and closed the issue as
`COMPLETED`. GitClaw reported implementation commit
[`de85c8bb512476c37da2b8c3e86cbcb8471f21e4`](https://github.com/sheikkinen/gitclaw-oulu-civic-intelligence/commit/de85c8bb512476c37da2b8c3e86cbcb8471f21e4).

The repository-scoped ledger reached `seen -> planned -> judged_approved ->
enforced -> reviewed_approved -> pushed -> closed`. Interrupted issue #1 and
completed issue #2 were not modified. The generated tree is confined to
`features/oulu-procurement-source-snapshot/` apart from normal append-only
ledger commits.

The generated judgement required one revision: make the postal-locality branch
use whole-word, same-line discipline and add an explicit postal false-positive
test. GitClaw folded that revision into its generated FR before implementation.
Independent review then reproduced all 33 focused tests and clean graph lint,
confirmed the synthetic fixture smoke, and approved the feature. The bounded
live Hilma smoke returned `Source health: ok`, qualifying Oulu notices capped
at five, and the required bounded-coverage warning without retaining a raw
response.

Containment and review found no credential or environment reads, non-allowlisted
hosts, external writes, other source, query variant, CPV loop, shared-library
change, LLM fact selection, runtime/policy/workflow change, or publication
work. No deviation or failed enforcement attempt occurred.

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-831 | Direct parent and reviewed Procurement transfer; preserve staged stop gates |
| FR-832 | Reuse the proven one-source GitClaw governance pattern, not harbour code |
| FR-828 | Preserve the failed monolithic issue; do not retry or repair issue #1 |
| FR-829 | Preserve bounded public read-only retrieval and no-secret policy |
| FR-830 | Reuse repository-scoped ledger identity without modification |
| Control-plane Hilma probe | Reuse origin, ordering, ID, normalized fields, and detail-link rule through the approved packet; reject replacement decoding, repeated custom queries, and relevance bypass |

## Alternatives Rejected

- **Repeat the query for each CPV:** the frozen custom search ignores CPV while
  the old loop repeats identical requests.
- **Accept every `Oulu` search hit:** search relevance is candidate retrieval,
  not evidence.
- **Use `FI1D9` alone:** the code covers a region wider than Oulu.
- **Require only Oulu-named authorities:** this excludes Oulu projects procured
  by national authorities; the location-plus-title branch remains explicit and
  testable.
- **Fetch or summarize SPA detail:** the index contract does not provide that
  text and this task does not authorize browser execution or synthesis.
- **Hand-code or import the harbour adapter:** invalidates the GitClaw witness
  and crosses the still-unresolved composition boundary.

## Scope Fence

FR-833 authorizes one separately governed public issue and its generated
single-source procurement feature. It authorizes no manual implementation and
no other FR-831 task. Any GitClaw platform defect stops enforcement for a
separate platform FR.
