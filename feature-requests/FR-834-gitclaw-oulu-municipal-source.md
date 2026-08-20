# Feature Request: FR-834 GitClaw Oulu Municipal Source

**Priority:** HIGH
**Type:** Feature / GitClaw acceptance task
**Status:** Judged - APPROVED and human-reviewed (2026-08-20); enforcement
authorized
**Effort:** 0.5 day
**Requested:** 2026-08-20
**Parent:** FR-831
**Depends on:** FR-829, FR-830, FR-831, FR-832, FR-833
**Prior art:** FR-831 supplies the human-reviewed Municipal decisions transfer
packet and requires one bounded source judgement at a time. FR-832 and FR-833
prove that single-source GitClaw issues can reach contained closure. FR-825
supplies the proven lossless HTML declaration-precedence strategy. The private
control-plane municipality assets are provenance only: reuse Oulu code `564`,
platform `triplan`, official base, and public-notice route while rejecting
unconditional Latin-1, regex-primary HTML parsing, unbounded retrieval,
title-derived identity, multi-route aggregation, and removal inference.
**First consumer / first event:** A reader of the public Oulu cookbook
repository, when one owner-authored issue autonomously produces and validates
a contained municipal public-notice snapshot without implementing source
composition or bulletin synthesis.

## Summary

Use one owner-authored issue in
`sheikkinen/gitclaw-oulu-civic-intelligence` to make GitClaw generate a
contained Oulu KTweb public-notice feature. It retrieves only the official
`kuullist_tweb.htm` index, decodes it losslessly, parses its table structurally,
uses `docid` as stable identity, and emits one deterministic Markdown source
snapshot with explicit health and bounded-index limitations.

This is Task 4 of FR-831. It does not retrieve agendas, minutes, officer
decisions, attachments, or detail bodies. It does not import the harbour or
procurement features or establish a cross-feature composition boundary.

## Value Statement

The Oulu bulletin gains a tested municipal source whose identity, dates, links,
and encoding behavior are mechanically auditable instead of relying on a
lossy exploratory scraper or treating absence from a bounded index as removal.

## Ideal Result

A public issue closes with governed feature artifacts and a contained,
fixture-tested KTweb adapter. The output lists at most five newest notices with
their official detail links, preserves Finnish text exactly, states the index
and item bounds, and never claims to have retrieved detail or attachment
content or detected a deleted notice.

## Closed Input

The issue may use only this human-reviewed public contract:

- Oulu municipality identity is code `564`; platform is `triplan`.
- Exact unauthenticated GET source:
  `https://asiakirjat.ouka.fi/ktwebscr/kuullist_tweb.htm`.
- Make one gzip-capable request with a 5-second connection timeout, 15-second
  total/read timeout, and 512 KiB maximum decompressed response. Read at most
  the limit plus one byte and reject overflow. Never retain a raw response.
- Require HTTP 200 and media type `text/html`. A redirect may be followed only
  when every hop and the final URL remain HTTPS on `asiakirjat.ouka.fi` and the
  final path is exactly `/ktwebscr/kuullist_tweb.htm`.
- Decode losslessly. Parse valid HTTP and HTML meta charset declarations. If
  both exist they must resolve to the same supported codec; disagreement is
  invalid. Use the valid declaration when exactly one exists. If neither
  exists, require strict UTF-8. Reject malformed or unsupported declarations,
  undecodable bytes, and decoded U+FFFD. Do not guess or unconditionally fall
  back to a single-byte codec.
- Parse HTML with Python's structured `html.parser` or an existing structured
  runtime parser, never regex as the primary HTML parser. Require a notice
  table whose header represents `Kuulutuslaji` and `Nähtävillä`/`Nimike`.
- Each candidate row has an optional notice type in the first cell and, in the
  second cell, a visibility start/end interval plus exactly one primary
  `/ktwebscr/fileshow` link with query `doctype=3` and one decimal `docid`.
  The primary link text is the title. An optional
  `/ktwebscr/kuulattn_tweb.htm?id={docid}` attachment-list link may be recorded
  only when its decimal ID equals the primary `docid`.
- Parse Finnish `D.M.YYYY` visibility dates as real calendar dates. Missing or
  invalid start/end, empty title, duplicate primary links, non-decimal `docid`,
  mismatched attachment ID, or an off-origin/off-path link makes that row
  invalid and excluded while increasing the invalid-row count. It does not
  invalidate other rows in an otherwise valid table.
- Stable identity is `oulu-ktweb-notice-{docid}`. Build the exact official
  detail URL as
  `https://asiakirjat.ouka.fi/ktwebscr/fileshow?doctype=3&docid={docid}`.
  Normalize only identity, `docid`, title, optional notice type, visibility
  start/end, exact detail URL, optional validated attachment-list URL, exact
  source URL, and municipality code/name.
- Deduplicate by `docid`, sort by visibility start descending and then numeric
  `docid` ascending, and emit at most five records. A valid table with no valid
  rows is `ok`, not a source failure.

## Live Reverification (2026-08-20)

A bounded live GET returned HTTP 200, `text/html`, 26,479 decompressed bytes,
and no HTTP charset. The HTML contains a valid `windows-1252` meta declaration.
Strict UTF-8 failed at byte `0xe4`; strict Windows-1252 decoded without U+FFFD.

Structured parsing found one table header and 50 candidate rows with 50 unique
decimal `docid` values. Each sampled candidate had one `doctype=3` `fileshow`
link, a visibility interval, and title text; notice type was absent on at least
one valid row and is therefore optional. This is shape evidence, not a retained
fixture. All committed fixtures must be synthetic.

## Exact GitHub Issue

Create one unlabelled owner-authored issue in the public cookbook repository.
The trusted-owner `opened` event is the sole trigger.

**Title:** `Oulu municipal notice source snapshot`

**Body:**

> **Public provenance:** This contract is the reviewed Municipal transfer from
> [FR-831](https://github.com/sheikkinen/yamlgraph/blob/main/feature-requests/FR-831-oulu-bulletin-staged-source-reuse.md),
> narrowed and governed by
> [FR-834](https://github.com/sheikkinen/yamlgraph/blob/main/feature-requests/FR-834-gitclaw-oulu-municipal-source.md)
> and its
> [judgement](https://github.com/sheikkinen/yamlgraph/blob/main/feature-requests/FR-834-gitclaw-oulu-municipal-source.judgement.md).
> These public documents are provenance only; this issue contains the complete
> executable contract. Do not access the private control-plane repository or
> rediscover the source contract.
>
> Implement one contained GitClaw feature for Oulu's KTweb public-notice
> source. Do not implement the civic bulletin or another source.
>
> Retrieve only
> `https://asiakirjat.ouka.fi/ktwebscr/kuullist_tweb.htm` with one
> unauthenticated gzip-capable GET. Use a 5-second connection timeout,
> 15-second total/read timeout, and 512 KiB maximum decompressed response. Read
> at most the limit plus one byte and reject overflow. Require HTTP 200 and
> `text/html`. Follow redirects only when every hop and final URL stay HTTPS on
> `asiakirjat.ouka.fi` and the final path stays exactly
> `/ktwebscr/kuullist_tweb.htm`. Never retain a raw response.
>
> Decode losslessly. Parse valid HTTP and HTML meta charset declarations. When
> both exist they must resolve to the same supported codec; disagreement is
> invalid. Use the valid declaration when exactly one exists. With neither,
> require strict UTF-8. Reject malformed/unsupported declarations,
> undecodable bytes, and U+FFFD. Do not guess or unconditionally use Latin-1 or
> Windows-1252.
>
> Parse HTML structurally, never with regex as the primary parser. Require a
> notice table headed by `Kuulutuslaji` and `Nähtävillä`/`Nimike`. A candidate
> row has optional notice type and a second cell containing a Finnish
> `D.M.YYYY` visibility start/end interval plus exactly one primary
> `/ktwebscr/fileshow?doctype=3&docid={decimal}` link. Its link text is the
> title. Accept an optional `/ktwebscr/kuulattn_tweb.htm?id={decimal}` link only
> when its ID matches the primary `docid`.
>
> Exclude and count a row with missing/invalid dates, empty title, duplicate
> primary links, non-decimal `docid`, mismatched attachment ID, or off-origin
> or off-path links. Deduplicate valid rows by `docid`, sort by visibility
> start descending then numeric `docid` ascending, and emit at most five.
> Stable identity is `oulu-ktweb-notice-{docid}`. Normalize only identity,
> `docid`, title, optional notice type, visibility dates, exact official detail
> URL, optional validated attachment-list URL, exact source URL, and Oulu
> municipality code `564`/name.
>
> Emit exactly one non-empty Markdown candidate beginning with requested
> `date`. Include `Source health: ok|unavailable|invalid`, source URL, declared
> charset used, candidate/valid/invalid counts, bounded-index warning, and
> either up to five records or an explicit no-valid-row/failure statement. A
> valid empty result is `ok`. Network/timeout/HTTP failures are `unavailable`;
> size, redirect, media type, charset, decoding, table, and document failures
> are `invalid`. Never infer deletion from index absence or claim detail or
> attachment content was retrieved.
>
> Keep implementation, synthetic fixtures, and tests entirely under this
> generated feature directory. Use only the Python standard library plus the
> existing GitClaw/YAMLGraph runtime. Tests must cover: valid HTTP charset;
> valid meta charset; matching declarations; conflicting, malformed, and
> unsupported declarations; no declaration with strict UTF-8; strict
> Windows-1252 meta decoding; invalid UTF-8/U+FFFD; timeout/network failure;
> redirect boundary; wrong HTTP/media status; oversized decompressed response;
> missing/wrong table header; valid optional notice type; missing type; invalid
> dates; empty title; duplicate/off-path primary links; non-decimal `docid`;
> matching/mismatched attachment ID; duplicate IDs; deterministic ordering and
> five-item cap; and valid empty results. Run focused tests, graph lint, a
> synthetic fixture smoke, and one bounded live smoke. Record honest evidence
> without raw response data in `authoring-report.md`.
>
> Exclude agendas, minutes, officer decisions, detail/attachment fetches, other
> origins/routes, Digitraffic, Hilma, cross-source composition, shared-library
> changes, LLM fact selection or synthesis, removal inference,
> cron/workflow/runtime/policy changes, secrets, notifications, and final
> publication.

## Generated Feature Contract

The expected slug is `oulu-municipal-notice-source-snapshot`. GitClaw generates
normal governed artifacts under that feature directory only. Optional tools,
tests, and bounded synthetic fixtures belong below the same directory.

The graph accepts `date`. Retrieval, decoding, HTML parsing, validation,
deduplication, ordering, links, and Markdown rendering are deterministic code.
A prompt artifact may document the no-synthesis boundary, but no LLM chooses,
rewrites, labels, or fills source facts.

The feature is independently runnable and cron-compatible. It does not import
another generated feature; Task 5 of FR-831 still owns shared reuse.

## Validation

GitClaw enforcement must provide:

1. focused deterministic tests for every issue-listed transport, charset,
   parser, identity, date, link, deduplication, ordering, and empty case;
2. graph lint;
3. synthetic Windows-1252 fixture smoke with frozen expected Finnish text and
   at least one rejected invalid row;
4. one bounded live smoke recording health, charset, candidate/valid/invalid
   counts, selected IDs, visibility dates, and link modes only;
5. containment proof; and
6. independent review approval before push and issue close.

Live source unavailability does not authorize captured live fixtures, lossy
decoding, weaker parser fixtures, a broader route, or invented data.

## Acceptance Criteria

- [x] AC-01: Governed judgement is human-reviewed and published before public
      issue creation
- [ ] AC-02: Exact unlabelled owner-authored issue contains public FR-831,
      FR-834, and judgement provenance without private access
- [ ] AC-03: Intake reaches terminal closed ledger state without modifying
      interrupted issue #1 or completed issues #2/#3
- [ ] AC-04: Generated provenance, graph, prompt, contained tool, tests,
      synthetic fixtures, report, and review exist under the expected slug
- [ ] AC-05: One exact KTweb GET uses finite timeout and decompressed-byte
      bounds, redirect/media validation, and no raw response retention
- [ ] AC-06: Charset declaration precedence, strict decoding, contradiction,
      unsupported declaration, UTF-8 fallback, and U+FFFD cases are tested
- [ ] AC-07: Structured table parsing, `docid` identity, visibility dates,
      optional type, official links, invalid rows, and deduplication are tested
- [ ] AC-08: Deterministic ordering, five-item cap, explicit health, charset,
      counts, and bounded-index/no-removal limitations match the contract
- [ ] AC-09: Focused tests, graph lint, synthetic fixture smoke, bounded live
      smoke, containment, and independent review pass
- [ ] AC-10: No other route/source, detail fetch, composition, shared library,
      synthesis, removal inference, workflow/runtime/policy, secret, or
      publication change
- [ ] AC-11: FR-834 records issue, run, generated commit, ledger close,
      validation evidence, deviations, and failed attempts

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-831 | Direct parent and reviewed Municipal transfer; preserve staged stop gates |
| FR-832 / FR-833 | Reuse the proven one-source GitClaw governance pattern, not feature code |
| FR-825 | Reuse validated declaration precedence and fail-closed decoding strategy |
| FR-828 | Preserve failed monolithic issue #1; do not retry or repair it |
| FR-829 / FR-830 | Preserve bounded public-read policy and repository-scoped ledger identity |
| Control-plane municipality assets | Reuse Oulu identity, official base, and notice route through the approved packet; reject exploratory parsing and aggregation |

## Alternatives Rejected

- **Aggregate all KTweb endpoint families:** crosses source judgements and makes
  identity/date semantics heterogeneous.
- **Treat Windows-1252 as an unconditional fallback:** current evidence is a
  valid HTML declaration, not authority to guess when declarations are absent.
- **Use regex as the HTML parser:** brittle against nesting and explicitly
  condemned by the reviewed transfer.
- **Use title as identity:** titles are mutable and the official link supplies
  stable `docid`.
- **Fetch detail or attachments:** this task validates index facts and links;
  it does not authorize additional requests or content claims.
- **Infer removal from absence:** a 50-row bounded current index cannot prove a
  previously observed notice was deleted.
- **Import an existing generated adapter:** crosses the still-unresolved
  composition boundary and invalidates the GitClaw witness.

## Scope Fence

FR-834 authorizes one separately governed public issue and its generated
single-source municipal feature. It authorizes no manual implementation and no
other FR-831 task. Any GitClaw platform defect stops enforcement for a separate
platform FR.
