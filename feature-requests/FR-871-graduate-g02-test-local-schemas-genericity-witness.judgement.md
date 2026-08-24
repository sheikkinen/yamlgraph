# Judgement: FR-871 Graduate G-02 -- Test-Local Schemas as the Genericity Witness

**Prior art:** dispositioned in the parent FR (`FR-871-graduate-g02-test-local-schemas-genericity-witness.md`) — FR-870 G-02 as discovering witness, CLAUDE.md Option B tension reconciled in scope; no prior FR occupies this territory.

**Verdict:** APPROVED WITH REVISIONS -- the convention and witness are sound, but authority activates only after the FR reconciles the existing `GenericReport` exception, narrows the witness claim to the boundary it can actually police, and removes registry/review ambiguity.

**Reviewed against:** `feature-requests/FR-871-graduate-g02-test-local-schemas-genericity-witness.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `docs/constitution-diff.md`; `feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md`; `feature-requests/FR-870-constitution-diff-speckit-vs-scripture.judgement.md`; `docs/diary/diary-2026-08-23-two-constitutions-one-repo.md`; `docs/diary/diary-2026-08-23-the-generator-transcribed-the-police-not-the-law.md`; `yamlgraph/models/schemas.py`; `yamlgraph/models/__init__.py`; `tests/unit/test_generic_report.py`; `tests/unit/test_router.py`; `tests/unit/test_node_factory_base.py`; `capabilities/CAP-08-error-handling.yaml`; `capabilities/CAP-12-utilities.yaml`; `capabilities/CAP-18-testing-quality.yaml`; `capabilities/CAP-30-copilot-node.yaml`; `capabilities/CAP-243-requirement-witness-audit.yaml`; `ARCHITECTURE.md`; `feature-requests/TEMPLATE.md`. No author chat narrative or uncommitted working notes were consumed.

## What is sound

The problem is real enough for a small convention graduation. FR-870 explicitly classified G-02 as the one genuine generated-only discovery: "Tests MUST use test-only Pydantic models to prove the framework is truly generic" and marked it a future convention candidate (`docs/constitution-diff.md:434-445`). The two cited diary entries independently preserve the same finding and next step: the generator surfaced an implicit norm from test code (`docs/diary/diary-2026-08-23-the-generator-transcribed-the-police-not-the-law.md:46-53`), and the post-enforcement reflection names G-02 graduation as a cheap next FR (`docs/diary/diary-2026-08-23-two-constitutions-one-repo.md:78-88`).

The scope is appropriately small and single-concern if revised as below: one witness test, one Scripture convention line, one CLAUDE.md reconciliation, one REQ/CAP update, and one changelog fragment (`feature-requests/FR-871-graduate-g02-test-local-schemas-genericity-witness.md:69-98`, `109-120`). The FR correctly rejects the noisy AST/import gate because many tests legitimately import framework models under test (`feature-requests/FR-871-graduate-g02-test-local-schemas-genericity-witness.md:94-97`, `121-129`).

The proposed direction aligns with existing doctrine. The Scripture already treats prose-only law as weaker than enforced law through `detection_without_enforcement` and `substance_over_presence` (`.github/copilot-instructions.md:110`, `157`), requires req-tagged tests (`.github/copilot-instructions.md:174-176`), and requires RED/GREEN proof for production branches (`.github/copilot-instructions.md:221`). The existing `schemas.py` module also already claims to contain framework models only (`yamlgraph/models/schemas.py:1-5`), so the proposed witness is a boundary assertion rather than a new abstraction.

Strategic classification: **Pattern documentation with a mechanical witness**. This is not a framework primitive; it codifies one testing/convention rule and adds a guard that protects the meaning of future genericity evidence.

## Required revisions

### R-1: Reconcile `GenericReport` and existing shipped-model test usage

Revise the FR's norm so it does not falsely imply the current suite never uses shipped framework schemas as output-model fixtures. The current repository intentionally exposes `GenericReport` from `yamlgraph.models` (`yamlgraph/models/__init__.py:1-5`, `14-20`, `27-34`), documents `GenericReport` as a flexible output model for arbitrary analysis tasks (`yamlgraph/models/schemas.py:105-147`), and already tests it directly with analysis-style examples (`tests/unit/test_generic_report.py:1-4`, `163-214`). Framework machinery tests also use `yamlgraph.models.GenericReport` to exercise resolver/router paths (`tests/unit/test_router.py:158-163`, `187-219`; `tests/unit/test_node_factory_base.py:17-26`, `56-82`).

Fold this by changing the Convention and Problem text to distinguish three cases:

1. Tests whose purpose is to prove arbitrary structured-output genericity must define test-local Pydantic models or inline YAML schemas.
2. Tests whose subject is framework machinery may import shipped framework models when the import itself, resolver path, or model contract is the behavior under test.
3. New shipped domain schemas are not authorized in `yamlgraph.models.schemas`; any expansion of the public schema class set must pass through a judged FR and the frozen allow-list witness.

Do not require modifications to the existing `GenericReport` tests under this FR unless the revised FR explicitly authorizes them; the current scope says no existing tests change (`feature-requests/FR-871-graduate-g02-test-local-schemas-genericity-witness.md:94-98`, `119-120`).

### R-2: Align the witness claim with what the witness can actually enforce

Revise the first consumer, Ideal Result, and Proposed Solution to state that the witness gates additions to the shipped schema surface, not all future misuse of existing shipped models in tests. A frozen class-set test catches a new class added to `yamlgraph.models.schemas`; it does not catch a test using the already exported `GenericReport` unless the FR also adds the AST/import gate it rejects (`feature-requests/FR-871-graduate-g02-test-local-schemas-genericity-witness.md:8-11`, `63-67`, `73-79`, `94-97`).

Fold this by specifying the exact class-set boundary the witness asserts: public classes defined by `yamlgraph.models.schemas` itself, e.g. names whose objects are classes and whose `__module__ == yamlgraph.models.schemas.__name__`, excluding imported classes such as `BaseModel`. The frozen allow-list must be exactly `ErrorType`, `PipelineError`, `VerificationViolation`, `GuardViolation`, `GenericReport`, and `CopilotResult` unless the revised FR deliberately removes or reclassifies one of those existing models (`yamlgraph/models/schemas.py:18-31`, `86-110`, `154-171`).

### R-3: Pin the capability/requirement registry update before enforcement

Replace "CAP file or extension of an existing testing CAP -- enforcer's choice" with a concrete registry target and requirement text (`feature-requests/FR-871-graduate-g02-test-local-schemas-genericity-witness.md:90-92`). The repo already has CAP-18 for testing/quality and requirement traceability (`capabilities/CAP-18-testing-quality.yaml:1-17`), CAP-08 for error schema/reporting (`capabilities/CAP-08-error-handling.yaml:1-40`), CAP-12 for schema loading/model-building utilities (`capabilities/CAP-12-utilities.yaml:1-32`), and CAP-30 for `CopilotResult` in the copilot node (`capabilities/CAP-30-copilot-node.yaml:1-53`). Leaving the registry owner open makes the enforcement surface non-mechanical.

Fold this by naming one route in the FR. Recommended route: add one new requirement under CAP-18, because the deliverable is a testing-quality witness, with modules including the new witness test and `yamlgraph/models/schemas.py`. If the author chooses a new CAP instead, the FR must name the CAP title, modules, and requirement text before enforcement starts.

### R-4: Make documentation reconciliation mechanically checkable

Revise AC-03 so "no remaining doc invites domain schemas into the shipped models module" has a concrete verification command or artifact list (`feature-requests/FR-871-graduate-g02-test-local-schemas-genericity-witness.md:116-117`). The current contradiction is real: CLAUDE.md currently presents `yamlgraph/models/schemas.py` as the place for shared schemas (`CLAUDE.md:269-288`), while `schemas.py` says the module is framework-only and demo-specific output schemas live inline in YAML (`yamlgraph/models/schemas.py:1-5`).

Fold this by requiring the enforcer to update CLAUDE.md Option B and run a bounded documentation search over `CLAUDE.md`, `reference/`, `ARCHITECTURE.md`, and `docs/` for invitations to put domain output schemas in `yamlgraph/models/schemas.py`. The acceptance criterion must name the search terms or require a recorded `rg` transcript so the check is repeatable.

### R-5: Add the required distill and human-review gates

Add a diary/distill deliverable and a human-review gate. Repo doctrine requires the final task on a task list to add a diary reflection (`.github/copilot-instructions.md:33`, `237`), and CLAUDE.md documents the diary gate for feature/fix PRs with FR references (`CLAUDE.md:417-419`). The FR currently requires a changelog fragment but omits diary reflection (`feature-requests/FR-871-graduate-g02-test-local-schemas-genericity-witness.md:118-120`).

The FR also modifies the Scripture itself (`feature-requests/FR-871-graduate-g02-test-local-schemas-genericity-witness.md:80-85`), which is an instruction-boundary change. Repo doctrine says instruction-boundary/enforcement outputs must be reviewed as adversarial input (`.github/copilot-instructions.md:81-85`), and the judge doctrine requires enforcement-infrastructure changes to demand human review as a GATE (`.github/skills/judge-fr/doctrine.md:94-103`). Fold this by adding an acceptance criterion for a diary reflection and a condition that the Scripture/CLAUDE.md wording is human-reviewed before merge.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-871-graduate-g02-test-local-schemas-genericity-witness.md` folding R-1 through R-5 |
| D-2 | New req-tagged witness test freezing the public class set of `yamlgraph.models.schemas` |
| D-3 | `.github/copilot-instructions.md` Conventions section, one new convention line only |
| D-4 | `CLAUDE.md` Option B reconciliation and bounded doc-search evidence |
| D-5 | Capability registry update for the witness requirement |
| D-6 | `changelog/unreleased/` fragment |
| D-7 | `docs/diary/` reflection for the enforcement |
| D-8 | FR implementation-status notes recording RED/GREEN proof and any deviations |

Not authorized: AST/import gates over the test suite; modifying existing tests except to add the new witness test; changing runtime schema loading or output-model resolution behavior; deleting or renaming `GenericReport`; adding domain schemas to `yamlgraph.models.schemas`; modifying graph artifacts or prompt YAML; changing hooks, CI, judge/review/authoring doctrine, or requirement-coverage tooling; broad documentation rewrites beyond the named convention and Option B reconciliation.

## Revised acceptance criteria

- [ ] AC-01: FR-871 is revised to fold R-1 through R-5, including the `GenericReport`/machinery-test exception, exact witness boundary, concrete CAP/REQ route, bounded doc-search check, diary deliverable, and human-review gate.
- [ ] AC-02: A new req-tagged unit test asserts the public classes defined by `yamlgraph.models.schemas` are exactly `ErrorType`, `PipelineError`, `VerificationViolation`, `GuardViolation`, `GenericReport`, and `CopilotResult`; imported helper classes such as `BaseModel` are excluded by the test logic.
- [ ] AC-03: RED proof is recorded by adding a canary class to `yamlgraph.models.schemas` and showing the new witness test fails with a message naming the convention; GREEN proof removes the canary and passes the targeted witness test.
- [ ] AC-04: `.github/copilot-instructions.md` gains one Convention line stating that genericity tests use test-local Pydantic models or inline YAML schemas, while shipped `yamlgraph.models.schemas` remains a framework-model surface whose expansion requires a judged FR; the line notes generator-derived provenance from FR-870 G-02.
- [ ] AC-05: CLAUDE.md Option B is reworded so shared domain schemas are directed to inline YAML prompt schemas or application code, not to `yamlgraph/models/schemas.py`.
- [ ] AC-06: Documentation reconciliation evidence is recorded with a bounded search over `CLAUDE.md`, `reference/`, `ARCHITECTURE.md`, and `docs/`, showing no remaining invitation to put domain output schemas in `yamlgraph/models/schemas.py`.
- [ ] AC-07: The capability registry is updated via the specific CAP/REQ route named in the revised FR, and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-08: A changelog fragment exists under `changelog/unreleased/` and references the new or revised REQ.
- [ ] AC-09: A diary reflection is added under `docs/diary/` for the enforcement.
- [ ] AC-10: Existing tests are not modified except the newly added witness test; if the author decides existing `GenericReport` usages should change, that must re-enter as a separate FR or an explicit revision before enforcement.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-5 are folded into `feature-requests/FR-871-graduate-g02-test-local-schemas-genericity-witness.md`. | GATE |
| C-2 | Do not invoke or re-run the judge while enforcing this FR. | GATE |
| C-3 | Do not add an AST/import scanner, runtime output-model restrictions, graph/prompt changes, or existing-test rewrites under this FR. | GATE |
| C-4 | Do not claim the witness detects fixture misuse of already shipped models; it freezes additions to the shipped schema class surface. | GATE |
| C-5 | Human review is required before merging the `.github/copilot-instructions.md` and `CLAUDE.md` wording changes. | GATE |
| C-6 | If the bounded doc search finds additional documentation that invites domain schemas into `yamlgraph.models.schemas`, update only those directly conflicting passages or return for scope revision. | GATE |

Authority granted: after the required revisions are folded, enforcement may add the schema-surface witness, update the named doctrine/docs/REQ/changelog/diary artifacts, and record RED/GREEN proof without changing runtime behavior.
