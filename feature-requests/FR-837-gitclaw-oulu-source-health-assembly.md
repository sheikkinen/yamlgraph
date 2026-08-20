# Feature Request: FR-837 GitClaw Oulu Source-Health Assembly

**Priority:** HIGH
**Type:** Feature / GitClaw acceptance task
**Status:** Judged - APPROVED; human-reviewed for publication and exact issue
enforcement on 2026-08-20
**Effort:** 0.5 day
**Requested:** 2026-08-20
**Parent:** FR-831
**Depends on:** FR-829, FR-830, FR-831, FR-832, FR-833, FR-834, FR-835,
FR-836
**Blocks:** FR-831 Task 7
**Prior art:** FR-832 through FR-834 provide three independently governed,
deterministic source snapshots. FR-835 provides strict `composition.json`,
dependency-first same-run execution, and the bounded `source_snapshots` JSON
envelope. FR-836 repairs the exact `state_key: candidate` output contract and
proves all three live source outputs are recognized. Preserve those contracts:
do not import adapters, re-fetch sources, read stale outputs, parse source
Markdown, or add synthesis/publication behavior.
**First consumer / first event:** FR-831 Task 7, when one bounded synthesis graph
needs a current, deterministic account of which Oulu source snapshots succeeded
and their opaque same-run candidates, including partial or all-source failure.

## Summary

Use one owner-authored issue in
`sheikkinen/gitclaw-oulu-civic-intelligence` to make GitClaw generate one
contained composer feature. It declares the exact three Oulu source slugs in
manifest order, accepts only the FR-835 `source_snapshots` string, validates the
complete envelope, computes structural source health, and emits one
deterministic Markdown source bundle under `state_key: candidate`.

This is Task 6 of FR-831 only. It performs no public retrieval, source-fact
interpretation, ranking, summarization, LLM call, cron/workflow change,
notification, or publication. Task 7 remains separately planned and judged.

## Value Statement

The future bulletin receives one current, auditable source bundle whose
availability semantics are code-owned. A failed source remains an explicit
bounded failure instead of disappearing, and an all-source failure still
produces a deterministic candidate that downstream publication policy can
handle honestly.

## Ideal Result

A public issue closes with one contained composer whose manifest names exactly
the three committed source features. Across all eight success/failure
combinations it emits stable source order, exact structural health, and a
lossless representation of each successful candidate or bounded failure reason.
No source candidate is parsed or rewritten, and no source or platform file is
modified.

## Closed Input Contract

The graph accepts exactly these runtime state inputs:

- `date: str`; and
- `source_snapshots: str`, supplied only by the FR-835 runner boundary.

`source_snapshots` must decode as a JSON list of exactly three objects in this
exact order:

1. `oulu-harbour-source-snapshot`;
2. `oulu-procurement-source-snapshot`; and
3. `oulu-municipal-notice-source-snapshot`.

Each object must have one exact shape:

- success: `feature`, `status: "succeeded"`, and non-empty string `candidate`;
  or
- failure: `feature`, `status: "failed"`, and non-empty string `reason`.

Reject malformed JSON, a non-list root, wrong count/order/slug, duplicate slug,
unknown status, missing/extra key, wrong type, empty/whitespace-only candidate or
reason, and any candidate over 32 KiB UTF-8 or encoded envelope over 96 KiB.
Do not accept an alternate input variable, infer a missing source, read a prior
output, or repair malformed entries. Invalid envelope input makes this composer
fail; it is distinct from a valid envelope in which all three sources failed.

## Deterministic Assembly Contract

The composer maps only entry status to one aggregate health value:

- `complete`: three succeeded;
- `partial`: one or two succeeded; or
- `unavailable`: zero succeeded.

It emits exactly one non-empty Markdown candidate beginning with requested
`date`, followed by:

1. `# Oulu civic source bundle`;
2. `Assembly health: complete|partial|unavailable`;
3. `Sources available: N/3`;
4. one status line per source in manifest order; and
5. one source section per entry in the same order.

Use fixed display labels `Harbour`, `Procurement`, and `Municipal notices`.
For a succeeded entry, the section records `Status: succeeded` and includes the
candidate as an opaque JSON string value inside one canonical JSON code block.
For a failed entry, it records `Status: failed` and includes the reason as an
opaque JSON string value in the same canonical form. Use `json.dumps` with
`ensure_ascii=False` and compact separators so decoding the field reproduces
the exact original string, including Unicode and newlines. The composer may
count statuses and JSON-encode strings; it must not inspect candidate lines,
headings, source health, dates, identifiers, URLs, or facts.

The output key is exactly `state_key: candidate`. Rendering and validation are
deterministic Python code. The graph contains no LLM node.

## Exact Composition Manifest

Commit `features/oulu-civic-source-health-assembly/composition.json` with exactly:

```json
{
  "version": 1,
  "dependencies": [
    "oulu-harbour-source-snapshot",
    "oulu-procurement-source-snapshot",
    "oulu-municipal-notice-source-snapshot"
  ]
}
```

The expected slug is `oulu-civic-source-health-assembly`. All generated
implementation, fixtures, tests, reports, and review artifacts remain under
that feature directory. Normal GitClaw repository ledger updates are allowed;
no other tracked path may change.

## Exact GitHub Issue

Create one unlabelled owner-authored issue in the public consumer repository.
The trusted-owner `opened` event is the sole trigger.

**Title:** `Oulu deterministic source-health assembly`

**Body:**

> **Public provenance:** This is Task 6 of
> [FR-831](https://github.com/sheikkinen/yamlgraph/blob/main/feature-requests/FR-831-oulu-bulletin-staged-source-reuse.md),
> governed by
> [FR-837](https://github.com/sheikkinen/yamlgraph/blob/main/feature-requests/FR-837-gitclaw-oulu-source-health-assembly.md)
> and its published judgement. FR-835 supplies the composition boundary;
> FR-836 supplies the exact candidate-output contract. This issue is the
> complete executable contract. Do not access the private control-plane
> repository or rediscover any source.
>
> Implement one contained deterministic composer at
> `features/oulu-civic-source-health-assembly/`. Commit `composition.json` with
> version `1` and exactly these dependencies in order:
> `oulu-harbour-source-snapshot`, `oulu-procurement-source-snapshot`, and
> `oulu-municipal-notice-source-snapshot`.
>
> The graph accepts `date: str` and `source_snapshots: str`. Strictly decode the
> FR-835 JSON envelope as exactly three entries in manifest order. A succeeded
> entry has exactly `feature`, `status: "succeeded"`, and one non-empty string
> `candidate`. A failed entry has exactly `feature`, `status: "failed"`, and
> one non-empty string `reason`. Reject malformed JSON, wrong root/count/order
> or slug, duplicate slug, unknown status, missing/extra keys, wrong types,
> empty strings, candidates over 32 KiB UTF-8, and envelopes over 96 KiB.
>
> Compute only structural health: `complete` for three successes, `partial`
> for one or two, and `unavailable` for zero. Emit one deterministic Markdown
> candidate beginning with requested date, `# Oulu civic source bundle`,
> aggregate health, `Sources available: N/3`, status lines, and one section per
> source in manifest order using labels `Harbour`, `Procurement`, and
> `Municipal notices`. Encode each successful candidate or failed reason as an
> opaque JSON string in a canonical compact `json` code block with
> `ensure_ascii=False`; decoding must reproduce Unicode and newlines exactly.
> Do not inspect, parse, classify, summarize, relabel, repair, or rewrite any
> source candidate. Write the final output under exactly
> `state_key: candidate`.
>
> Use deterministic Python code and no LLM node. Tests must cover malformed
> and wrong-shape envelopes; exact key rules; wrong order/slug and duplicates;
> unknown statuses; empty/wrong-type values; UTF-8 candidate and envelope
> bounds; all eight success/failure combinations; exact aggregate health and
> available counts; fixed source order/labels; Unicode/newline round-trip;
> candidate/reason opacity; determinism; graph lint; and a graph smoke for
> complete, partial, and all-failed valid envelopes. Record honest focused,
> lint, smoke, containment, and independent-review evidence in
> `authoring-report.md`.
>
> Do not fetch any source, import or copy another feature's adapter, access
> another feature directory, read `outputs/`, use stale state, add a dependency,
> modify runtime/policy/prompts/workflows/cron/containment/ledger behavior,
> parse source Markdown, make an LLM call, synthesize bulletin prose, rank or
> omit successful facts, notify, publish, or implement Task 7.

## Generated Feature Contract

Expected artifacts are the normal governed provenance, graph, prompt or
contract artifact, deterministic tool, focused tests, synthetic fixtures,
`composition.json`, `authoring-report.md`, and independent review under
`features/oulu-civic-source-health-assembly/`.

The prompt artifact, if generated, documents the no-LLM/no-interpretation
boundary only. It is not executed for assembly. The graph has one deterministic
Python node that receives `date` and `source_snapshots` and writes exactly one
candidate.

No live source request is required or allowed during enforcement. Fixtures use
synthetic envelopes and synthetic opaque candidate strings only. Source adapter
behavior was separately accepted in FR-832 through FR-834 and witnessed through
`run_feature` in FR-836.

## Validation

GitClaw enforcement must provide:

1. focused deterministic unit tests for every input rejection and output rule;
2. a parameterized matrix covering all eight source-status combinations;
3. exact Unicode/newline round-trip and canonical JSON encoding assertions;
4. graph lint;
5. graph-level synthetic smokes for complete, partial, and unavailable health;
6. containment proof showing only the generated feature directory plus normal
   ledger state changed; and
7. independent review approval before push and issue close.

A synthetic smoke must invoke the generated graph, not only its Python helper.
No test may import a source adapter or use a captured live response.

## Acceptance Criteria

- [ ] AC-01: Human reviews and publishes FR-837 judgement before public issue
      creation
- [ ] AC-02: One unlabelled owner-authored issue has the exact title and closed,
      public-safe body without private access or source rediscovery
- [ ] AC-03: Intake reaches a terminal closed ledger state without modifying or
      retrying issues #1 through #4
- [ ] AC-04: One contained feature exists at the expected slug with exact
      three-source `composition.json` declaration order
- [ ] AC-05: Strict envelope validation rejects every malformed, wrong-shape,
      wrong-order, duplicate, unknown, empty, and over-bound case
- [ ] AC-06: All eight valid status combinations map exactly to `complete`,
      `partial`, or `unavailable` and `N/3`
- [ ] AC-07: Output source sections and status lines always use manifest order
      and frozen display labels
- [ ] AC-08: Canonical JSON fields round-trip successful candidates and failure
      reasons exactly, including Unicode/newlines, without Markdown parsing
- [ ] AC-09: The graph uses deterministic code, has no LLM node, and writes one
      non-empty final output under exact `state_key: candidate`
- [ ] AC-10: Focused tests, graph lint, complete/partial/all-failed graph smokes,
      containment, and independent review pass
- [ ] AC-11: No source request, adapter import/copy, cross-feature read, stale
      output read, platform/shared/dependency/workflow/cron/ledger change,
      synthesis, notification, or publication occurs
- [ ] AC-12: FR closure records issue/run/commit, terminal ledger state, exact
      test and smoke evidence, review, deviations, and failed attempts before
      Task 7 is filed

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-831 | Execute only Task 6; preserve separate Task 7 synthesis/publication gate |
| FR-829 | Preserve public-read and same-directory policy; this feature performs no retrieval |
| FR-830 | Preserve repository-scoped append-only ledger; normal issue transition only |
| FR-832 / FR-833 / FR-834 | Consume their same-run candidates opaquely; do not import, copy, fetch, or reinterpret |
| FR-835 | Use exact manifest, declaration-order envelope, same-run failure transport, and resource bounds |
| FR-836 | Use exact `state_key: candidate`; all three sources are recognized prerequisites |
| GitClaw issue #1 | Preserve interrupted monolithic evidence; no retry, relabel, or ledger repair |
| Completed issues #2-#4 | Preserve generated source artifacts and terminal records unchanged |

## Alternatives Rejected

- **Synthesize the bulletin now:** merges deterministic availability semantics
  with LLM fact selection, prose, and publication reserved for Task 7.
- **Parse each source Markdown to derive health or fields:** violates the opaque
  FR-835 boundary and couples the composer to three independently owned formats.
- **Import adapters or fetch sources again:** duplicates reviewed retrieval and
  breaks same-run single-execution semantics.
- **Drop failed sources:** makes partial or all-source failure invisible to the
  downstream policy.
- **Fail when all sources fail:** prevents deterministic honest assembly even
  though FR-835 explicitly runs composers on all-source failure.
- **Read prior output files as fallback:** silently converts current failure into
  stale success.

## Scope Fence

FR-837 authorizes one judged GitClaw issue and one contained deterministic
composer. It authorizes no source changes, private access, platform repair,
dependency, workflow, cron, containment, policy or prompt change, LLM call,
bulletin synthesis, notification, publication, issue #1 action, or Task 7 issue.
Any need outside the frozen issue body stops for a separate judgement.
