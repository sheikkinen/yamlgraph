# Feature Request: Graduate G-02 — Test-Local Schemas as the Genericity Witness

**Priority:** LOW
**Type:** Enhancement (convention graduation + witness test)
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-23
**First consumer / first event:** the Scripture's Conventions section (the
norm becomes citable law); first event is the next test or chaplain-generated
test that reaches for a shipped domain schema as an LLM-output fixture and is
caught by the witness instead of silently weakening the genericity evidence.

**Prior art:** FR-870 `docs/constitution-diff.md` table (e), row G-02 — the
discovering witness; this FR is exactly the "future proposal via the normal
pipeline" that FR-870's frozen scope required for any GENERIC_MISSED clause
worth adopting. CLAUDE.md "Option B" (shared schemas in
`yamlgraph/models/schemas.py`) is in-repo prior art in *tension* with the
norm and is dispositioned in scope below. No prior FR proposes this
convention (grep: genericity/test-only models — no hits).

## Summary

Graduate the one genuine finding of the FR-870 constitution-diff experiment
into law. The Spec Kit generator derived from our test code a norm the
Scripture never states: *tests prove the framework is generic by defining
their own Pydantic output models, never by importing shipped domain schemas.*
Make it a written Convention with a mechanical witness, per
`detection_without_enforcement`.

## Value Statement

"Any schema, any graph" is YAMLGraph's headline claim. Today its only proof
is an unstated habit. One convenient import of a shipped domain schema into a
test converts "the framework works with schemas it has never seen" into "the
framework works with its own models" — with no red anywhere. This FR makes
the evidentiary property visible (law) and defended (gate). It is also the
first Scripture clause originating from a generator rather than an incident —
entering honestly labeled as untraced-generic.

## Problem

Measured state (2026-08-23):

- `yamlgraph/models/schemas.py` ships exactly 6 classes, all framework
  infrastructure: `ErrorType`, `PipelineError`, `VerificationViolation`,
  `GuardViolation`, `GenericReport`, `CopilotResult`. Zero domain schemas.
- 32 files in `tests/unit/` define 59 test-local Pydantic models for
  structured-output paths.
- 72 test files import from `yamlgraph.models` — legitimately: they import
  the error/result machinery *under test*, not output-schema fixtures.

So the norm holds in practice and is stated nowhere. Two drift vectors:

1. **CLAUDE.md Option B** invites "shared schemas" into
   `yamlgraph/models/schemas.py`. The first domain schema landing there
   creates the import temptation the norm forbids.
2. **Generated tests**: chaplain/watcher pipelines write tests; an unstated
   norm is invisible to them (FR-870's own headline: prose-only law is
   invisible to generators — this FR is that finding applied to itself).

## Ideal Result

A test author (human or agent) who tries to add a domain schema to the
shipped models module, or to grow the infrastructure surface silently, gets
an immediate red with a message naming the convention; the Scripture states
the norm in one Convention line; the genericity claim has a citable,
mechanically defended witness.

## Proposed Solution

Minimal path back from the ideal:

1. **Witness test** (TDD: this is the RED): a req-tagged unit test asserting
   the public class set of `yamlgraph.models.schemas` equals the frozen
   allow-list of the 6 infrastructure models. Any new class fails with a
   message: "domain schemas live in prompt YAML or application code; test
   fixtures are test-local — see Scripture convention (FR-871)". Expanding
   the infrastructure allow-list requires touching the witness in a judged
   FR — which is the point.
2. **Scripture Convention line** (one sentence, Conventions section): tests
   prove genericity with test-local Pydantic models or inline YAML schemas;
   shipped `yamlgraph.models` stays infrastructure-only; production-model
   imports in tests are for machinery under test, never as LLM-output
   fixtures. Provenance note: generator-derived (FR-870 G-02), not
   incident-paid.
3. **CLAUDE.md Option B reconciliation**: reword to direct shared *domain*
   schemas to inline YAML prompt schemas or application code, keeping
   `yamlgraph/models/schemas.py` scoped to framework infrastructure —
   matching 8 months of actual practice.
4. **Capability/REQ**: new REQ-YG-XXX tag on the witness test via the
   existing capabilities registry flow (CAP file or extension of an
   existing testing CAP — enforcer's choice, registry is YAML-driven).

Explicitly NOT in scope: no AST scan of test imports (the 72 legitimate
machinery imports make an import-based gate noisy for zero catch — the
witness on the shipped module is the cheap, precise boundary); no changes to
existing tests (practice already conforms); no retro-fitting of examples/.

## The Case Against (forced_opposite)

No incident has ever been paid for this gap; the judge may ask what failure
this prevents that eight months didn't produce. The honest answer: it
protects an *evidentiary* property — what a green suite is allowed to mean —
same family as the req-coverage gate, not a runtime defect class. If the
judge finds that family insufficient for law, the correct verdict is REJECT
and the exhibit's G-02 row gets annotated "proposed and declined" — which is
itself a valid disposition of the generator's finding.

## Acceptance Criteria

- [ ] AC-01: witness test exists, req-tagged, asserting the frozen 6-class
      allow-list of `yamlgraph.models.schemas`; RED commit proves it fails
      when a canary class is added (SKIP=pytest), GREEN commit follows
- [ ] AC-02: Scripture Conventions gains one line stating the norm, with
      generator-derived provenance (FR-870 G-02) noted
- [ ] AC-03: CLAUDE.md Option B reworded; no remaining doc invites domain
      schemas into the shipped models module
- [ ] AC-04: REQ/CAP registry updated; `req_coverage --strict` passes
- [ ] AC-05: changelog fragment present; no existing test modified

## Alternatives Considered

- **AST/grep gate on test imports**: rejected — 72 files legitimately import
  production models (machinery under test); discriminating fixture-use from
  subject-use needs semantic analysis for zero observed offenders.
- **Docs-only (no witness)**: rejected by `detection_without_enforcement` —
  advisory docs are what we already effectively have (the habit).
- **Do nothing**: the norm remains invisible to generated tests — FR-870's
  own finding predicts exactly how it erodes.

## Related

- FR-870 / `docs/constitution-diff.md` (e) G-02 — discovering witness
- `docs/diary/diary-2026-08-23-two-constitutions-one-repo.md` — next-steps
  item 2
- `docs/diary/diary-2026-08-23-the-generator-transcribed-the-police-not-the-law.md`
  — the legibility argument (prose-only law is invisible)
- CLAUDE.md "Option B" — reconciled in scope item 3
