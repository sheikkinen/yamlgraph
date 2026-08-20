# Judgement: FR-837 GitClaw Oulu Source-Health Assembly

**Verdict:** APPROVED - FR-837 is a bounded Task 6 composer that preserves the
FR-835 same-run envelope and FR-836 `candidate` output contract while excluding
retrieval, synthesis, publication, and platform changes. Human review approved
publication and exact issue enforcement on 2026-08-20.

**Prior art:** FR-831 separates deterministic Task 6 composition from Task 7
synthesis/publication. FR-832 through FR-834 provide the three immutable source
features. FR-835 supplies strict same-run composition and opaque candidates.
FR-836 supplies exact candidate extraction and proves all three committed
source outputs are recognized. FR-829 and FR-830 preserve public-read and
repository-ledger boundaries.

**Reviewed against:** `feature-requests/FR-837-gitclaw-oulu-source-health-assembly.md`;
FR-829 through FR-836 and their judgements; repository judge doctrine,
judgement template, and Copilot instructions. No private control-plane artifact
or chat narrative was used by the judge.

## What is sound

FR-837 has one responsibility and one first consumer. It validates the existing
FR-835 envelope, counts structural statuses, and losslessly assembles opaque
strings for FR-831 Task 7. It explicitly excludes public retrieval, source-fact
interpretation, ranking, summarization, LLM calls, cron/workflow changes,
notification, publication, and Task 7.

The input contract is closed and mechanically testable: exact `date` and
`source_snapshots` variables; exact three-source order; exact success/failure
object shapes; fail-closed malformed-input behavior; inherited 32 KiB candidate
and 96 KiB envelope bounds; and no repair or stale fallback.

The output contract is deterministic. All eight source-status combinations map
to `complete`, `partial`, or `unavailable`; fixed labels and manifest order are
preserved; candidate and reason strings are canonical JSON values whose decoded
Unicode/newlines must match exactly. JSON encoding is allowed, while inspecting
source Markdown or facts is forbidden.

The strategic classification is **contrib/example acceptance task**, not a
framework primitive. It uses the completed composition and candidate-output
boundaries without extending the shared platform.

## Required revisions

None.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | One unlabelled owner-authored issue titled exactly `Oulu deterministic source-health assembly` with the FR-837 issue body |
| D-2 | One generated feature rooted at `features/oulu-civic-source-health-assembly/` |
| D-3 | Exact version-1 `composition.json` declaring harbour, procurement, and municipal source slugs in that order |
| D-4 | Deterministic graph/tool, synthetic fixtures, focused tests, authoring report, and independent review under the feature directory |
| D-5 | Normal ledger/closure evidence recording run, commit, validation, review, deviations, and failed attempts |

Not authorized: source retrieval; source adapter import, copy, or edit;
cross-feature file reads; prior `outputs/` reads; stale-state fallback;
source rediscovery or Markdown parsing; fact extraction; LLM nodes/calls;
bulletin synthesis; ranking or omission of successful facts; notifications;
publication; Task 7; platform/runtime/prompt/policy/containment/workflow/cron/
dependency/secret/ledger-behavior changes; or issue #1/issues #2-#4 changes.

## Acceptance criteria

- [ ] AC-01: Human reviews and publishes this judgement before public issue creation.
- [ ] AC-02: Exactly one unlabelled owner-authored issue has the frozen public-safe title/body.
- [ ] AC-03: Intake reaches terminal closed ledger state without changing issues #1-#4.
- [ ] AC-04: The generated feature and exact composition manifest stay under the expected slug.
- [ ] AC-05: Every malformed, wrong-shape/order/slug/status/type, empty, and over-bound input is rejected.
- [ ] AC-06: All eight valid combinations produce exact health and availability counts.
- [ ] AC-07: Output order and labels match the frozen contract.
- [ ] AC-08: Canonical JSON values round-trip Unicode/newlines without candidate inspection.
- [ ] AC-09: The deterministic graph has no LLM node and writes exact `state_key: candidate`.
- [ ] AC-10: Focused matrix tests, lint, three graph smokes, containment, and review pass.
- [ ] AC-11: No retrieval, cross-feature read, platform change, synthesis, notification, publication, or Task 7 occurs.
- [ ] AC-12: Closure records issue/run/commit, ledger, tests, smokes, containment, review, deviations, and failures before Task 7.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Publish this human-reviewed judgement before issue creation. | GATE |
| C-2 | Stop if planning or enforcement broadens into retrieval, synthesis, platform repair, publication, or Task 7. | GATE |
| C-3 | Generated code may only validate/count the envelope and JSON-encode opaque strings; no sibling/output reads, adapters, fetches, or Markdown parsing. | GATE |
| C-4 | The graph has no LLM node and emits only exact `state_key: candidate`. | GATE |
| C-5 | Focused rejection tests, all eight combinations, lint, and complete/partial/unavailable graph smokes pass before review. | GATE |
| C-6 | Only the generated feature directory and normal ledger state may change; broader needs stop for a separate FR. | GATE |

Authority granted: create exactly the FR-837 public issue and allow GitClaw to
generate one contained deterministic source-health assembly feature within the
frozen scope above.
