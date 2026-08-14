# Diary Seed Research: Top Ten Proposals

**Date:** 2026-08-14
**Scope:** Explicit `Seed:` entries in `docs/diary/`, checked against feature
requests, capabilities, changelog fragments, the FR board, the Chaplain inbox,
and recent repository history.

## Verdict

The diary contains 664 explicit seeds across 650 files. Most high-frequency
themes are not new opportunities: they already have an approved feature
request, a shipped mechanism, or active work. Four proposals justify immediate
work. The rest need research, an existing loop closed, or a second consumer
before implementation.

The recommended execution order is:

1. Judge-emitted contract manifest.
2. Atomic authoring completion protocol.
3. Schema-derived egress privacy guard.
4. Capability consumer census and retirement feed.

This order favors repeated, evidenced boundary failures over general-purpose
infrastructure. It also avoids the active API-discovery sequence in FR-783
through FR-792.

## Ranking

### 1. Judge-emitted contract manifest — file now

Have the Judge emit frozen enumerations from the governing feature request as
a machine-readable contract manifest. Enforcement should reconcile the
implementation and its tests against that manifest.

FR-782 produced three successive review escapes with the same shape: the
implementation narrowed a frozen list, then author-written tests and comments
ratified the narrower implementation. Required tables and fields are already
machine-checkable facts; leaving them embedded only in prose invites drift.

**Evidence:**
[The Consent Gate Watched the Wrong Door](2026-08-08-reflection-fr-782-the-consent-gate-watched-the-wrong-door.md)

### 2. Atomic authoring completion protocol — file now

Give the authoring adapter one authoritative completion event. The graph should
write and sync the report, then atomically emit a completion marker. After a
child timeout, the wrapper should allow a short bounded grace period for that
marker before reporting failure.

The endpoint-probe and page-analysis authoring runs both produced valid,
independently reproducible reports after the wrapper had already classified
the run as failed. Two recurrences satisfy the doctrine's graduation threshold;
raising the timeout again would preserve the race.

**Evidence:**
[FR-786 API Discovery Page-Analysis Step](diary-2026-08-14-page-analysis-step.md)

### 3. Schema-derived egress privacy guard — file now

Generate privacy assertions from every field in the outbound Pydantic model.
The first policy should reject committed artifacts containing machine-specific
paths, usernames, hostnames, and equivalent local identifiers. Test it against
the artifact from before the cure to prove that the guard has teeth.

FR-782 first leaked the macOS account name through diagnostic paths, then a
narrow fix still disclosed which local databases existed. The correct boundary
is the complete egress schema, not the field where the latest leak happened.

**Evidence:**
[The Consent Gate Watched the Wrong Door](2026-08-08-reflection-fr-782-the-consent-gate-watched-the-wrong-door.md)

### 4. Capability consumer census and retirement feed — file now

Add a periodic census of shipped runtime variants, enum members, and config
options with zero committed consumers. Feed confirmed unused surfaces into the
existing FR-466 retirement process rather than creating another lifecycle.

The manifest census found that Python had real consumers while shell and graph
manifest runtimes initially had none. Shell later gained consumers; graph is
now the useful first witness for deciding whether a surface should gain a real
consumer or be retired.

**Evidence:**
[Was the Manifest Worth It?](diary-2026-08-05-was-the-manifest-worth-it.md)

### 5. Runnable fixture signature lint — research, then file

Prototype a lint that compares `invoke` and `ainvoke` test-double signatures
with the LangChain Runnable protocol they claim to implement.

Eight narrower fakes converted a legitimate production call expansion into
plausible but false cancellation failures. Before filing, prove that signature
comparison can distinguish intentional lightweight stubs from protocol fakes
without a large suppression registry.

**Evidence:**
[FR-720: The Fake That Lied About the Interface](2026-07-13-fr720-fake-narrower-than-interface.md)

### 6. Stable identities for enforcement exceptions — research, then file

Replace `file:line` references in noqa confessions and enforcement allowlists
with stable identities such as symbol plus rule code, optionally guarded by a
content hash. Resolve the current position lazily.

A harmless CLI edit shifted one suppression and broke multiple independent
gates. The research must answer whether stable anchors preserve the deliberate
human re-read that today's friction sometimes forces.

**Evidence:**
[Verification as a First-Class Construct](2026-07-04-reflection-fr-677-verification-first-class.md)

### 7. Artifact-class governance telemetry — research, then file

Detect writes to governed `graph.yaml` and `prompts/*.yaml` paths when the
session has not entered the graph-authoring route. Begin with warning telemetry
and measure false positives before considering denial.

The instruction trigger now binds to artifact class, but enforcement still
depends on the model recognizing that a request phrased as `mv`, `copy`, or
`adapt` creates a governed artifact. The original near miss ran against the
wrong provider and was caught only by linting habit.

**Evidence:**
[The Skill That Did Not Fire](diary-2026-07-29-skill-trigger-artifact-class.md)

### 8. Local pre-egress inference probe — prototype only

Prototype an advisory local-model step that asks what a reader could infer from
an outbound artifact that the author did not explicitly intend to disclose.
Show the findings to the human; do not silently redact or block on an opaque
score.

This targets semantic inference that structural schema checks cannot see. It
belongs after proposal 3, because deterministic field coverage is cheaper and
more reliable than model judgement.

**Evidence:**
[The Consent Gate Watched the Wrong Door](2026-08-08-reflection-fr-782-the-consent-gate-watched-the-wrong-door.md)

### 9. Close FR-118 audit auto-escalation — resume, do not refile

Verify whether approved FR-118 was ever implemented. If not, enforce or
explicitly retire it; do not create another audit-escalation feature request.

Automatic escalation of recurring Inquisitor findings is the largest semantic
seed cluster, with roughly 30 recurrences. That repetition is evidence of an
unclosed loop, not demand for a duplicate plan.

**Precedent:**
[FR-118 Inquisitor Auto-Propose](../../feature-requests/FR-118-inquisitor-auto-propose.md)

### 10. Installer render/plan contract — defer pending census

Inventory side-effecting installers under `examples/`. File a common
render/plan-mode contract only if a second installer needs deterministic CI
coverage without applying host mutations.

The `install-hook.sh --render-only` witness is strong, but one instance does
not justify repository-wide infrastructure. The second consumer should decide
the abstraction.

**Evidence:**
[The Hook Is the Cheap Part](diary-2026-08-08-the-hook-is-the-cheap-part.md)

## Occupied Or Closed Territory

- API and protocol archaeology is actively covered by FR-783 through FR-792.
- First-class graph verification shipped through FR-677.
- REQ, capability, and changelog cross-validation substantially shipped in
  later traceability gates.
- Generic tool manifests shipped in FR-768; consumer proof and retirement are
  the remaining questions.
- Canonical feeder chunks explicitly await a second real feeder.
- Diary seed substance already has proposed FR-682.
- Prior-art discovery and disposition already exist in FR-737, FR-738, FR-745,
  and FR-748.

## Selection Method

Seeds were clustered semantically rather than ranked by wording frequency.
Each candidate was then checked for:

1. A concrete failure or measured repository fact in nearby diary context.
2. Recurrence or an unusually strong single incident.
3. An identifiable first consumer and enforcement boundary.
4. Existing FR, capability, changelog, inbox, or negative precedent.
5. A smaller action than the seed's most general formulation.

Frequency was evidence, not authority. A recurring seed with an approved FR
was classified as an unclosed loop. A novel seed without a second consumer was
deferred. Proposals ranked highest when a small mechanical boundary could
prevent a demonstrated class of plausible wrong artifacts.

## Seed

When diary review finds that the strongest proposal already has an approved
feature request, should the review emit a separate **closure queue** ordered by
recurrence count, so abandoned authority becomes more visible than novel ideas?
