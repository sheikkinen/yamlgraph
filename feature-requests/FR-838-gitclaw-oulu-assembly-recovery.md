# Feature Request: FR-838 GitClaw Oulu Assembly Recovery

**Priority:** HIGH
**Type:** Recovery / GitClaw acceptance task
**Status:** Judged - APPROVED; human-reviewed for publication and exact
rejected-feature deletion preparation on 2026-08-20
**Effort:** 0.5 day
**Requested:** 2026-08-20
**Parent:** FR-837
**Depends on:** FR-831, FR-835, FR-836, FR-837
**Blocks:** FR-831 Task 7
**Prior art:** FR-837 issue #5 reached a green GitClaw closure at consumer commit
`252e79b`, but independent post-closure audit rejected it. Its title-derived
slug is `oulu-deterministic-source-health-assembl`, not the frozen
`oulu-civic-source-health-assembly`; whitespace-only candidate/reason values are
accepted; `Aggregate health:` replaced `Assembly health:`; and source sections
omit required `Status:` lines. Preserve issue #5 and its append-only ledger as
failed evidence. Do not edit that implementation into compliance.
**First consumer / first event:** The Oulu consumer cron, before its next run,
when the rejected but runnable issue #5 feature must be removed and Task 6 must
be regenerated once under the exact canonical slug.

## Summary

Recover FR-837 in two governed steps:

1. operator containment deletes only the rejected
   `features/oulu-deterministic-source-health-assembl/` directory from the
   public consumer while preserving issue #5, commits, and append-only ledger;
2. one new unlabelled owner-authored issue titled
   `Oulu civic source health assembly` lets GitClaw generate the same bounded
   Task 6 contract at the canonical title-derived slug, with explicit
   regressions for the four audit failures.

This is replacement, not parallel implementation. The rejected feature must be
absent before issue #6 is opened so cron never owns two Task 6 composers. No
manual edit, copy, rename, or salvage from issue #5 is allowed.

## Root Cause and Evidence

The issue #5 pipeline run `32351512271` succeeded and closed issue #5 at
consumer head `252e79b`. Focused tests reported 45 passed and graph lint passed,
but they validated a generated local FR that drifted from published FR-837.

Independent audit found:

1. `tools/slug.py` derives paths exclusively from issue title and truncates at
   40 characters. `Oulu deterministic source-health assembly` became
   `oulu-deterministic-source-health-assembl`; the exact corrective title
   `Oulu civic source health assembly` is directly proven to produce
   `oulu-civic-source-health-assembly`.
2. `_require_non_empty_str` rejects only `""`; direct probes accepted
   whitespace-only candidates and reasons.
3. the renderer emits `Aggregate health:` instead of frozen
   `Assembly health:`.
4. source sections omit `Status: succeeded|failed`.
5. generated judgement/review used the rewritten local FR as authority and
   recorded no deviation from the published human-reviewed contract.

These are acceptance failures despite green tests. Task 7 remains blocked.

## Step 1: Contain the Rejected Artifact

In `sheikkinen/gitclaw-oulu-civic-intelligence`, delete exactly:

```text
features/oulu-deterministic-source-health-assembl/
```

The deletion is an operator-owned containment action after rejected review, not
a manual implementation repair. Before commit, prove the directory matches
consumer commit `252e79b` and has no local modifications. Commit only deletions
under that directory. Preserve:

- issue #5 and its comments/state;
- commits `42f4afa` through `252e79b`;
- every issue #5 line in `state/issues.jsonl`;
- source features, runtime, policy, prompts, workflows, dependencies, outputs,
  and all other paths.

A human reviews the exact deletion diff before commit/push. After publication,
prove no graph remains under the rejected slug and the consumer full suite
passes. Do not create the corrective issue until this gate is green.

## Step 2: Exact Corrective Issue

Create one unlabelled owner-authored issue in
`sheikkinen/gitclaw-oulu-civic-intelligence`. The trusted-owner `opened` event
is the sole trigger.

**Title:** `Oulu civic source health assembly`

The title is part of the contract: current published `tools/slug.py` maps it
exactly to `oulu-civic-source-health-assembly`. Any collision suffix or other
slug stops enforcement.

**Body:**

> **Recovery provenance:** This replaces rejected issue #5 under
> [FR-838](https://github.com/sheikkinen/yamlgraph/blob/main/feature-requests/FR-838-gitclaw-oulu-assembly-recovery.md)
> and its published judgement. The controlling Task 6 contract is
> [FR-837](https://github.com/sheikkinen/yamlgraph/blob/main/feature-requests/FR-837-gitclaw-oulu-source-health-assembly.md)
> and its published judgement, but this issue contains the complete executable
> contract. Issue #5 used the wrong title-derived slug, accepted whitespace-only
> values, changed `Assembly health:` to `Aggregate health:`, and omitted section
> `Status:` lines. Do not copy, import, rename, read, or salvage issue #5.
>
> Implement exactly one contained deterministic composer at
> `features/oulu-civic-source-health-assembly/`. Before implementation, assert
> that the current issue title derives to exactly that slug and that the path
> does not already exist. Commit `composition.json` with version `1` and exactly
> these dependencies in order: `oulu-harbour-source-snapshot`,
> `oulu-procurement-source-snapshot`, and
> `oulu-municipal-notice-source-snapshot`.
>
> The graph accepts exactly `date: str` and `source_snapshots: str`. Strictly
> decode the FR-835 JSON envelope as exactly three entries in manifest order. A
> succeeded entry has exactly `feature`, `status: "succeeded"`, and one
> non-empty, non-whitespace-only string `candidate`. A failed entry has exactly
> `feature`, `status: "failed"`, and one non-empty, non-whitespace-only string
> `reason`. Reject malformed JSON, wrong root/count/order or slug, duplicate
> slug, unknown status, missing/extra keys, wrong types, `""`, spaces-only,
> tabs-only, newlines-only, and mixed-whitespace-only candidate/reason values,
> candidates over 32 KiB UTF-8, and envelopes over 96 KiB.
>
> Compute only structural health: `complete` for three successes, `partial` for
> one or two, and `unavailable` for zero. Emit one deterministic Markdown
> candidate beginning with requested date, then exactly
> `# Oulu civic source bundle`, exactly
> `Assembly health: complete|partial|unavailable`, exactly
> `Sources available: N/3`, one status line per source in manifest order, and
> one source section per entry in the same order using labels `Harbour`,
> `Procurement`, and `Municipal notices`.
>
> Every source section must contain exactly `Status: succeeded` or
> `Status: failed` before its payload. Encode each successful candidate or
> failed reason as an opaque JSON string in a canonical compact `json` code
> block using `json.dumps(value, ensure_ascii=False, separators=(",", ":"))`.
> Decoding must reproduce Unicode and newlines exactly. Do not inspect, parse,
> classify, summarize, relabel, repair, or rewrite source content. Write the
> final output under exactly `state_key: candidate`.
>
> Use deterministic Python code and no LLM node. Tests must cover malformed and
> wrong-shape envelopes; exact keys/order/slugs; duplicate and unknown status;
> wrong types; every empty and whitespace-only form above for both candidate and
> reason; exact UTF-8 bounds; all eight success/failure combinations; exact
> `Assembly health:` and `Sources available:` lines; exact per-section `Status:`
> lines; fixed source order/labels; Unicode/newline round-trip; opacity;
> determinism; graph lint; and graph smokes for complete, partial, and all-failed
> valid envelopes. Add explicit negative assertions that output contains no
> `Aggregate health:` and that every section has its required status line.
>
> Review against this issue body and published FR-837/FR-838 judgements as
> controlling authority. Do not rewrite the contract into a generated local
> substitute. Record exact focused, lint, smoke, containment, and independent
> review evidence plus any deviation in `authoring-report.md`.
>
> Do not fetch a source, import/copy/read another feature, read `outputs/`, use
> stale state, add a dependency, modify runtime/policy/prompts/workflows/cron/
> containment/ledger behavior, parse source Markdown, make an LLM call,
> synthesize bulletin prose, notify, publish, or implement Task 7.

## Generated Feature Contract

The only new implementation root is
`features/oulu-civic-source-health-assembly/`. Expected artifacts are the normal
provenance, graph, documentation-only prompt/contract, deterministic tool,
synthetic tests/fixtures, exact `composition.json`, authoring report, and review.
Normal append-only issue #6 ledger transitions are allowed.

No file from rejected issue #5 may be copied. Similarity from implementing the
same published contract is expected, but evidence must show generation from the
new issue and tests must explicitly fail the four issue #5 defects.

## Validation

Step 1:

- exact deletion inventory under the rejected root only;
- pre-delete tree matches commit `252e79b`;
- human deletion approval;
- full consumer suite passes after deletion; and
- rejected graph is absent before issue #6 opens.

Step 2:

- issue title derives to exact canonical slug with no collision suffix;
- direct red regressions against issue #5 behavior cover whitespace candidate,
  whitespace reason, `Aggregate health:`, and missing section status;
- focused tests cover all eight combinations and every rejection case;
- graph lint and complete/partial/unavailable graph smokes pass;
- full consumer suite passes;
- containment shows only canonical feature root plus normal ledger state;
- independent review compares generated output to the published FR-837 and
  FR-838 contracts, not only generated local prose; and
- issue reaches terminal closed ledger state.

## Acceptance Criteria

- [ ] AC-01: Human publishes FR-838 judgement before containment or issue #6
- [ ] AC-02: Human approves exact issue #5 feature-directory deletion; no ledger
      or other path is removed or changed
- [ ] AC-03: Consumer full suite passes and rejected graph is absent before
      corrective issue creation
- [ ] AC-04: One unlabelled owner-authored corrective issue has the exact title
      and title-derived canonical slug with no suffix
- [ ] AC-05: Issue #5, commits, comments, and append-only ledger remain preserved
      as rejected evidence
- [ ] AC-06: Canonical feature has exact three-source manifest and only allowed
      inputs/output key, with no LLM node
- [ ] AC-07: Empty and every whitespace-only candidate/reason form fails closed
- [ ] AC-08: All eight valid combinations emit exact assembly health/count,
      manifest order, labels, and per-section status lines
- [ ] AC-09: Candidate/reason JSON round-trips exactly without content parsing
- [ ] AC-10: Focused tests, lint, three graph smokes, full suite, containment,
      and authority-aware independent review pass
- [ ] AC-11: No rejected artifact copy/rename/edit, source access, platform edit,
      synthesis, notification, publication, or Task 7 occurs
- [ ] AC-12: FR-837/FR-838 closure records both issue attempts, runs, commits,
      deletion gate, tests, review, deviations, and failures before Task 7

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-837 | Preserve its Task 6 semantics; correct the title/path contradiction and four failed acceptance surfaces |
| Issue #5 / `252e79b` | Preserve ledger/history; delete only its runnable rejected feature directory |
| FR-835 | Preserve exact composition envelope, order, bounds, and opaque candidate boundary |
| FR-836 | Preserve exact `state_key: candidate` extraction and source witnesses |
| FR-831 | Keep Task 7 blocked until canonical replacement closes |

## Scope Fence

FR-838 authorizes one reviewed deletion of the rejected issue #5 feature root
and one exact-title corrective GitClaw issue. It authorizes no manual feature
repair, rename, copy, history rewrite, ledger deletion, issue #5 reopening,
source change/access, platform/runtime/policy/prompt/workflow/dependency/cron/
containment change, synthesis, notification, publication, or Task 7.
