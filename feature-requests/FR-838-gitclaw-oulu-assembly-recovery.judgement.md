# Judgement: FR-838 GitClaw Oulu Assembly Recovery

**Verdict:** APPROVED - FR-838 is a bounded recovery that preserves rejected
issue #5 evidence, removes only its runnable artifact, and re-enters GitClaw once
under the canonical slug with explicit regressions for the audited failures.
Human review approved publication and deletion preparation on 2026-08-20; the
exact deletion commit and corrective issue remain gated.

**Prior art:** FR-837 separates deterministic Task 6 from Task 7 but froze a
title inconsistent with its expected title-derived slug. FR-835 supplies the
opaque same-run composition boundary. FR-836 supplies exact candidate output.
Issue #5 and consumer commit `252e79b` are preserved as rejected evidence.

**Reviewed against:** `feature-requests/FR-838-gitclaw-oulu-assembly-recovery.md`;
FR-831, FR-835, FR-836, FR-837 and their judgements; repository judge doctrine,
judgement template, and Copilot instructions. The sole route consumed no chat
narrative, external consumer checkout, private artifact, or uncommitted note.

## What is sound

The recovery is specific: issue #5 produced a wrong title-derived slug, accepts
whitespace-only values, substitutes `Aggregate health:`, and omits section
`Status:` lines. Each defect is directly testable.

The sequence is minimal. First remove exactly the rejected runnable feature
while preserving issue, commits, comments, and append-only ledger. Then open one
fresh issue whose exact title is proven to derive to the canonical slug. No
manual repair, rename, copy, or salvage is allowed.

The corrective issue remains within Task 6. It preserves the exact manifest,
strict envelope, deterministic health, opaque canonical JSON encoding, no-LLM
boundary, and Task 7 prohibition while adding regressions for the four observed
failures.

Strategic classification: **contrib/example operational recovery**, not a
framework primitive.

## Required revisions

None.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Published human-reviewed FR-838 and judgement |
| D-2 | Operator deletion of exactly `features/oulu-deterministic-source-health-assembl/` after byte-match and separate human diff approval |
| D-3 | Full consumer-suite and rejected-graph absence proof before corrective issue creation |
| D-4 | One unlabelled issue titled exactly `Oulu civic source health assembly` |
| D-5 | One generated feature under exact `features/oulu-civic-source-health-assembly/` with normal ledger transitions |
| D-6 | Regressions, focused tests, lint, complete/partial/unavailable smokes, full suite, containment, and authority-aware review |

Not authorized: editing/renaming/copying/reading/salvaging issue #5 feature;
deleting issue #5 history or ledger; reopening issue #5; changing sources,
platform/runtime/policy/prompts/workflows/dependencies/cron/containment/ledger
behavior/outputs; fetching sources; stale reads; Markdown parsing; LLM use;
synthesis; notification; publication; or Task 7.

## Acceptance criteria

- [ ] AC-01: Human-reviewed judgement is published before deletion or issue #6.
- [ ] AC-02: Rejected root byte-matches `252e79b`, has no local modifications, and is the only human-approved deletion surface.
- [ ] AC-03: Issue #5 history and ledger remain preserved.
- [ ] AC-04: Full suite passes and rejected graph is absent before issue #6.
- [ ] AC-05: Exact unlabelled corrective issue title derives to canonical slug without suffix.
- [ ] AC-06: Canonical feature has exact manifest, inputs/output key, and no LLM.
- [ ] AC-07: Empty and every whitespace-only candidate/reason fails closed.
- [ ] AC-08: All eight combinations emit exact health/count/order/labels/section status.
- [ ] AC-09: Canonical JSON values round-trip opaquely.
- [ ] AC-10: Focused tests, lint, three smokes, full suite, containment, and authority-aware review pass.
- [ ] AC-11: No salvage, source/platform access, synthesis, notification, publication, or Task 7 occurs.
- [ ] AC-12: Closure preserves and records both attempts before Task 7.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Publish this judgement before consumer deletion or issue creation. | GATE |
| C-2 | Exact deletion may remove only the rejected feature root and requires separate human approval. | GATE |
| C-3 | Do not open issue #6 until rejected graph is absent and full suite passes. | GATE |
| C-4 | Stop unless title derives exactly to canonical slug without suffix. | GATE |
| C-5 | Regenerate from the new issue; do not salvage issue #5. | GATE |
| C-6 | Preserve deterministic opaque no-LLM/no-publication Task 6 scope. | GATE |
| C-7 | Independent review must use published FR-837/FR-838 authority. | GATE |
| C-8 | Preserve both failed and corrective evidence before Task 7. | GATE |

Authority granted: after publication, prepare the exact rejected-feature
deletion for human review; after separate deletion approval and a green full
suite, open one exact-title corrective GitClaw issue within this frozen scope.
