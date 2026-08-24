# Feature Request: Graduate G-02 — Test-Local Schemas as the Genericity Witness

**Priority:** LOW
**Type:** Enhancement (convention graduation + witness test)
**Status:** Judged
**Effort:** 0.5 days
**Requested:** 2026-08-23
**First consumer / first event:** the Scripture's Conventions section (the
norm becomes citable law); first event is the next attempt — human or
generated — to add a class to the shipped schema surface
(`yamlgraph.models.schemas`) outside a judged FR, caught red by the witness
instead of landing silently.

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
Scripture never states. As reconciled by the judgement (R-1), the norm has
three cases:

1. Tests whose purpose is to prove arbitrary structured-output genericity
   define test-local Pydantic models or inline YAML schemas.
2. Tests whose subject is framework machinery may import shipped framework
   models (`PipelineError`, `GenericReport`, `CopilotResult`, …) when the
   import, resolver path, or model contract is the behavior under test —
   this includes the intentional `GenericReport` fixture usage in
   `test_generic_report.py`, `test_router.py`, `test_node_factory_base.py`.
3. New shipped domain schemas are not authorized in
   `yamlgraph.models.schemas`; any expansion of its public class set must
   pass through a judged FR and the frozen allow-list witness.

Make case 3 mechanically witnessed and all three written Convention, per
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

Measured state (2026-08-23, reconciled with judgement evidence):

- `yamlgraph/models/schemas.py` ships exactly 6 classes: `ErrorType`,
  `PipelineError`, `VerificationViolation`, `GuardViolation`,
  `GenericReport`, `CopilotResult`. Five are infrastructure;
  `GenericReport` is a deliberately flexible shipped output model, exported
  and directly tested as such — the norm must carve it out, not deny it.
- 32 files in `tests/unit/` define 59 test-local Pydantic models for
  structured-output paths (case 1 practiced).
- 72 test files import from `yamlgraph.models` — legitimately, as machinery
  under test (case 2 practiced).
- The module docstring already claims framework-only scope, but nothing
  enforces it.

So the norm holds in practice and is stated nowhere binding. Two drift
vectors:

1. **CLAUDE.md Option B** invites "shared schemas" into
   `yamlgraph/models/schemas.py`, directly contradicting the module's own
   docstring. The first domain schema landing there erodes the surface
   silently.
2. **Generated tests/code**: chaplain/watcher pipelines write code; an
   unstated norm is invisible to them (FR-870's own headline: prose-only law
   is invisible to generators — this FR is that finding applied to itself).

## Ideal Result

Anyone — human or agent — who adds a class to the shipped schema surface
gets an immediate red naming the convention (the witness gates *additions to
the surface*, per R-2 — it does not and cannot detect fixture misuse of
already-shipped models); the Scripture states the three-case norm in one
Convention line; CLAUDE.md no longer contradicts the module it documents.

## Proposed Solution

Minimal path back from the ideal:

1. **Witness test** (TDD RED): a req-tagged unit test asserting the set of
   public classes *defined by* `yamlgraph.models.schemas` (objects that are
   classes with `__module__ == yamlgraph.models.schemas.__name__`, excluding
   imports like `BaseModel`) equals exactly {`ErrorType`, `PipelineError`,
   `VerificationViolation`, `GuardViolation`, `GenericReport`,
   `CopilotResult`}. Failure message names the convention and this FR.
   Expanding the allow-list requires touching the witness in a judged FR —
   which is the point.
2. **Scripture Convention line** (one sentence, Conventions section):
   genericity tests use test-local Pydantic models or inline YAML schemas;
   shipped `yamlgraph.models.schemas` remains a framework-model surface
   whose expansion requires a judged FR. Provenance note: generator-derived
   (FR-870 G-02), not incident-paid.
3. **CLAUDE.md Option B reconciliation**: reword to direct shared *domain*
   schemas to inline YAML prompt schemas or application code. Verified by a
   bounded doc search (R-4): `rg -n "models/schemas|models\.schemas"
   CLAUDE.md reference/ ARCHITECTURE.md docs/` with the transcript recorded
   in the implementation status; only directly conflicting passages updated
   (C-6).
4. **Capability/REQ** (pinned per R-3): one new requirement under **CAP-18
   testing-quality** — "the shipped schema class surface is frozen by a
   witness test" — modules: the new witness test +
   `yamlgraph/models/schemas.py`.
5. **Diary reflection** for the enforcement (R-5).

Explicitly NOT in scope: no AST/import scan of test imports (72 legitimate
machinery imports, zero observed offenders); no changes to existing tests
(`GenericReport` usages stay — any change re-enters as a separate FR); no
runtime behavior changes; no retro-fitting of examples/. Human review
required before merging the Scripture/CLAUDE.md wording (C-5, instruction
boundary).

## The Case Against (forced_opposite)

No incident has ever been paid for this gap; the judge may ask what failure
this prevents that eight months didn't produce. The honest answer: it
protects an *evidentiary* property — what a green suite is allowed to mean —
same family as the req-coverage gate, not a runtime defect class. If the
judge finds that family insufficient for law, the correct verdict is REJECT
and the exhibit's G-02 row gets annotated "proposed and declined" — which is
itself a valid disposition of the generator's finding.

## Acceptance Criteria

As revised by the judgement (authoritative list in
`FR-871-graduate-g02-test-local-schemas-genericity-witness.judgement.md`):

- [x] AC-01: FR revised to fold R-1 through R-5 (this revision)
- [ ] AC-02: req-tagged witness test asserts public classes defined by
      `yamlgraph.models.schemas` are exactly the 6 listed; imported helpers
      like `BaseModel` excluded by test logic
- [ ] AC-03: RED proof via canary class (witness fails, message names the
      convention); GREEN proof removes canary and passes
- [ ] AC-04: Scripture gains one Convention line (three-case norm, judged-FR
      expansion, FR-870 G-02 provenance)
- [ ] AC-05: CLAUDE.md Option B reworded to direct shared domain schemas to
      inline YAML or application code
- [ ] AC-06: bounded doc-search evidence recorded (CLAUDE.md, reference/,
      ARCHITECTURE.md, docs/) — no remaining invitation of domain schemas
      into the module
- [ ] AC-07: capability registry updated via CAP-18 route;
      `python scripts/req_coverage.py --strict` passes
- [ ] AC-08: changelog fragment referencing the new REQ
- [ ] AC-09: diary reflection added
- [ ] AC-10: no existing test modified except adding the witness

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

## Judgement (2026-08-24)

**Verdict:** APPROVED WITH REVISIONS — full judgement in
[FR-871-graduate-g02-test-local-schemas-genericity-witness.judgement.md](FR-871-graduate-g02-test-local-schemas-genericity-witness.judgement.md)
(model gpt-5.5, via `scripts/judge.sh`, input closure honored).

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | Original norm falsely implied tests never use shipped output models — `GenericReport` is a shipped flexible output model, intentionally tested as such | Three-case norm folded; existing `GenericReport` tests untouched |
| R-2 | Witness claim overstated — a frozen class set gates surface additions, not fixture misuse | Claim narrowed; exact `__module__` boundary + 6-class allow-list specified |
| R-3 | "Enforcer's choice" registry route non-mechanical | Pinned: new REQ under CAP-18 testing-quality |
| R-4 | AC-03 doc reconciliation not checkable | Bounded `rg` search with recorded transcript |
| R-5 | Missing diary deliverable and human-review gate for Scripture/CLAUDE.md edits | Both added (AC-09, C-5) |

**Scope frozen:** D-1 revised FR (done), D-2 witness test, D-3 Scripture
Convention line, D-4 CLAUDE.md Option B + doc-search evidence, D-5 CAP-18
REQ, D-6 changelog fragment, D-7 diary, D-8 implementation status with
RED/GREEN proof. Not authorized: AST/import gates, existing-test rewrites,
runtime changes, `GenericReport` removal/rename, hook/CI/doctrine changes
beyond the named line. Gates C-1..C-6 per judgement file.
