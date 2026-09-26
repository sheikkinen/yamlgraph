# Judgement: FR-1104 CI Dedup (Fold `core-test` into the Matrix) + Python 3.14 Ceiling

**Verdict:** SPLIT — CI deduplication and Python 3.14 support are separate, independently useful changes with different evidence and migration gates; no implementation authority exists until each child FR is revised and judged.

**Reviewed against:** `feature-requests/FR-1104-ci-dedup-core-test-and-python-314.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-756-core-test-isolation.md`; `feature-requests/FR-759-otel-observability-boundary.md`; `feature-requests/FR-781-macos-file-hook-example.md`; `feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.md`; `feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.judgement.md`; `feature-requests/FR-918-ci-python-matrix-refresh.md`; `feature-requests/FR-919-ci-doc-only-skip.md`; `feature-requests/FR-934-merge-queue-on-main.md`; `feature-requests/FR-952-optional-extras-must-skip-not-error.md`; `.github/workflows/workflow.yml`; `pyproject.toml`; `tests/conftest.py`; cited `tests/unit/` corpus via targeted witness search, narrowed to `tests/unit/test_otel_observability.py`, `tests/unit/test_fr781_file_hook.py`, and `tests/unit/test_requirement_enforcement.py`; `reference/development-operations.md`; `reference/otel-observability.md`; `README.md`; `reference/getting-started.md`; `ARCHITECTURE.md`.

## What is sound

**Scope and need:** both problems are real. The current workflow has a distinct Python 3.13 `core-test` job with a lean install and `-m "not process"`, plus Python 3.11 and 3.13 full-suite matrix legs (`.github/workflows/workflow.yml:40-75`, `:87-101`). Package metadata simultaneously refuses Python 3.14 and classifies only 3.11–3.13 (`pyproject.toml:10`, `:18-20`). The FR also names two separate consumers and events honestly (`feature-requests/FR-1104-ci-dedup-core-test-and-python-314.md:8-11`), which makes the split boundary visible rather than speculative.

**Measurability and testability:** most proposed outcomes are stated as inspectable workflow contexts, install sets, metadata values, CI results, and branch-protection readbacks (`feature-requests/FR-1104-ci-dedup-core-test-and-python-314.md:168-200`). Existing witnesses make the core boundaries testable: FR-756's collection failure is exercised by `test_unmarked_process_boundary_module_is_rejected` (`tests/unit/test_requirement_enforcement.py:107-149`), and FR-759's no-extra tests are isolated from SDK-dependent tests (`tests/unit/test_otel_observability.py:31-40`, `:59-145`).

**Feasibility and architecture alignment:** an `include` matrix with per-leg extras is a direct GitHub Actions configuration change, not a new abstraction. Retaining the existing `test` job identity preserves the required-context naming pattern and the docs-only no-op design (`.github/workflows/workflow.yml:65-75`, `:123-125`). Keeping the collection hook unchanged also conforms to FR-756's existing boundary mechanism (`tests/conftest.py:43-48`, `:96-138`).

**Strategic classification:** these are two repository-maintenance changes, not framework primitives, contrib examples, or new patterns. Each has a concrete first consumer and can remain narrow: one child changes CI test topology; the other changes the tested support ceiling and package metadata (`feature-requests/FR-1104-ci-dedup-core-test-and-python-314.md:8-14`, `:92-120`). The problems justify those two operational changes, but not a combined authority envelope.

## Required revisions

### R-1: Split the proposal into two independently judged FRs

Create one child FR for **CI deduplication and `core-test` disposition** and one child FR for **Python 3.14 support and required-context migration**. FR-1104 itself names two first events (`feature-requests/FR-1104-ci-dedup-core-test-and-python-314.md:8-11`) and joins deleting a CI job to widening a user-facing interpreter contract (`:46-48`, `:92-120`). Either change can ship without the other: the current 3.13 ceiling leg can become lean without changing supported Python, and a later support FR can replace 3.13 with 3.14 without redesigning test topology. Judge doctrine requires `SPLIT` for that bundle (`.github/skills/judge-fr/doctrine.md:49-50`, `:75-77`), matching the repository's FR-917 precedent (`feature-requests/FR-917-ci-python-matrix-and-doc-only-skip.judgement.md:21-25`, `:71-77`).

Sequence the children: judge and enforce the CI-dedup child against the current 3.11/3.13 matrix first; then author the Python 3.14 child against the resulting workflow. This keeps branch-protection mutation entirely out of the dedup change and prevents either child from depending on an unapproved half of the other.

### R-2: Make the FR-756 signal decision explicit in the CI-dedup child

The current FR says users receive "the same signal" (`feature-requests/FR-1104-ci-dedup-core-test-and-python-314.md:52-54`) but later admits that deleting `core-test` removes the separately collected `-m "not process"` run and its order/side-effect isolation claim (`:122-133`). FR-756 explicitly froze both the collection-time boundary scan and a distinct CI run of the deselected suite (`feature-requests/FR-756-core-test-isolation.md:24-35`, `:42-49`, `:75-81`). Preserving the source scan alone does not preserve that full contract.

**Operator decision required in the child FR:** choose exactly one:

1. `preserve` — adopt the substance of Alternative A3 so the lean 3.13 leg runs disjoint `not process` and `process` partitions, each test runs once, coverage is combined without lowering the threshold, and the isolated core partition remains a blocking CI claim; or
2. `retire` — explicitly repeal FR-756's distinct deselected-run CI claim, retain only its collection-time boundary enforcement, remove every "same signal" statement, and state the lost defect class as an accepted tradeoff.

The child FR must record the operator's literal `preserve` or `retire` answer before judgement. It must not delegate that product/signal decision to the Judge or enforcer (`.github/skills/judge-fr/doctrine.md:97-101`).

### R-3: State optional-extra claims at their actual strength

The OTEL claim has a real precedent: FR-759 deliberately made disabled and missing-extra tests runnable without the SDK and assigned the ambient no-`otel` environment to `core-test` (`feature-requests/FR-759-otel-observability-boundary.md:186-197`). The CI-dedup child must name the exact non-skipped test node IDs and assert that `opentelemetry.sdk` is actually absent before running them; merely omitting `otel` from the direct extras string does not prove a transitive dependency or runner image did not provide it.

The current FR incorrectly treats `vision` as the same ambient-missing signal (`feature-requests/FR-1104-ci-dedup-core-test-and-python-314.md:177-181`, `:211`, `:217`). FR-781 says its missing-Pillow path is simulated independently of ambient state and that `core-test` excludes the vision test surface (`feature-requests/FR-781-macos-file-hook-example.md:162-170`, `:293-306`); the witness module is marked `process` (`tests/unit/test_fr781_file_hook.py:20-24`) and its missing-extra test monkeypatches the failure path (`:237-242`). Therefore the child must either:

- describe omission of `vision` only as a lean-install choice while retaining the simulated witness; or
- add a new, explicit ambient-absence assertion and acceptance test, labelled as new coverage rather than a preserved `core-test` claim.

### R-4: Supply the Python 3.14 prerequisite evidence before judging the support child

FR-918 made re-widening to `<3.15` conditional on a green Python 3.14 leg and verified dependency wheels (`feature-requests/FR-918-ci-python-matrix-refresh.md:60-66`, `:156-164`). FR-1104 repeats that prerequisite in its Research field but postpones the probe to enforcement AC-01 (`feature-requests/FR-1104-ci-dedup-core-test-and-python-314.md:12-14`, `:168-174`). That is not research evidence and cannot support advance authority for a public compatibility claim.

Before the Python 3.14 child is judged, cite a committed research record containing:

- the exact Python 3.14 patch version and platform;
- the exact selected-extras install command under a temporary `<3.15` metadata allowance;
- `pip check` output;
- a green Python 3.14 run in an environment equivalent to the proposed CI leg, with the exact unit-suite command and counts;
- wheel-availability evidence for the dependencies FR-918 named, including `langgraph` and `pydantic-core`, plus every selected extra dependency; and
- any skips or source builds, dispositioned rather than omitted.

A failed wheel or test probe blocks that child; it does not authorize dropping an extra, weakening a test, or widening metadata without the tested leg.

### R-5: Replace the merge-queue procedure with the repository's actual strict-protection procedure

The FR says this PR will be enqueued and that `merge_group` will emit the new contexts (`feature-requests/FR-1104-ci-dedup-core-test-and-python-314.md:141-164`, `:222`). The cited precedent says the opposite: merge queue activation is blocked because this is a user-owned repository, the operator chose to keep strict protection, and the existing `merge_group` wiring is dormant (`feature-requests/FR-934-merge-queue-on-main.md:5`, `:267-273`; `reference/development-operations.md:68-79`).

The Python 3.14 child must define an operator-executed migration for the current `pull_request` + `strict: true` regime: record the initial `strict` and contexts, verify the replacement PR's `test (3.11)` and `test (3.14)` results, temporarily remove only the obsolete `test (3.13)` context immediately before the normal squash merge, merge without queue terminology, immediately add `test (3.14)`, and record the final `strict` and contexts. No unrelated PR may merge during the temporary-context window. A first post-merge PR is an operational follow-up witness, not a pre-merge acceptance gate for the implementation commit.

### R-6: Give each child substantive research and exact executable witnesses

FR-1104 has precedent and an alternatives table, but no `is_this_a_graph` answer (`feature-requests/FR-1104-ci-dedup-core-test-and-python-314.md:12-35`, `:213-223`). Each new FR must contain its own `**Research:**` record with 4–6 genuine solution classes, strongest disagreement preserved, cited precedent, and an explicit graph-fit answer, as required by local judge doctrine (`.github/skills/judge-fr/doctrine.md:118-128`).

Replace file-level phrases such as "disabled/missing-extra tests run and pass" and "existing FR-756 test" with exact pytest node IDs and commands. Add a static workflow contract test that asserts emitted matrix contexts, per-leg extras, retained docs-only no-op behavior, and unchanged out-of-scope job pins. Separate pre-merge acceptance criteria from post-merge operational evidence so every gate can fail for the intended missing implementation rather than for timing or an unavailable platform event (`.github/skills/judge-fr/doctrine.md:58-61`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | New CI-dedup/`core-test`-disposition FR: `.github/workflows/workflow.yml` test topology on the existing Python 3.11/3.13 matrix; exact OTEL/vision claims; FR-756 decision; directly related workflow tests and documentation |
| D-2 | New Python 3.14 support FR, authored only after D-1's disposition is known: committed 3.14 research evidence; 3.13→3.14 ceiling replacement; `pyproject.toml` metadata; directly related docs/tests; strict branch-protection migration |
| D-3 | FR-1104 status update marking it Split/superseded by D-1 and D-2, with no implementation claims |

No implementation is authorized under FR-1104. Not authorized: editing workflow jobs, Python versions, extras, package metadata, branch protection, FR-952, reference docs, changelog fragments, or diary entries as enforcement of this combined FR. Neither child may change the Python 3.11 floor, coverage threshold or flags, `constraints/dev-py312.txt`, or interpreter pins in `build`, `windows-encoding`, `security.yml`, or `commitlint.yml`. Merge-queue enablement remains outside both children.

## Revised acceptance criteria

- [ ] AC-01: FR-1104 is marked `Status: Split` or superseded, with links to both child FRs and no claimed implementation authority.
- [ ] AC-02: The CI-dedup child has one responsibility and leaves the matrix at Python 3.11/3.13, `requires-python`, classifiers, and required contexts unchanged.
- [ ] AC-03: The CI-dedup child records the operator's literal `preserve` or `retire` decision for FR-756's distinct `-m "not process"` CI signal and aligns its summary, value statement, solution, and tests with that decision.
- [ ] AC-04: The CI-dedup child names exact OTEL and vision witness node IDs, distinguishes ambient-absence claims from simulated missing-import tests, and includes an explicit environment-absence assertion for every ambient claim.
- [ ] AC-05: The CI-dedup child defines a static workflow contract test for job removal or partitioning, emitted contexts, per-leg extras, docs-only no-op behavior, unchanged out-of-scope pins, and the unchanged FR-756 collection hook.
- [ ] AC-06: The Python 3.14 child has one responsibility and does not redesign `core-test`, matrix extras policy, pytest partitioning, or optional-extra semantics.
- [ ] AC-07: The Python 3.14 child cites a committed Python 3.14 research record satisfying R-4 before requesting judgement.
- [ ] AC-08: The Python 3.14 child aligns the tested ceiling, `requires-python`, classifiers, support documentation, and exact required contexts in mechanically checkable criteria.
- [ ] AC-09: The Python 3.14 child replaces all queue/enqueue assumptions with the current strict-protection migration and separates post-merge follow-up evidence from pre-merge acceptance.
- [ ] AC-10: Each child contains substantive alternatives, preserved dissent, cited precedent, and an explicit `is_this_a_graph` answer.
- [ ] AC-11: Each child requires explicit operator review of its workflow diff; the Python 3.14 child additionally requires operator execution and before/after readback of branch-protection mutation.
- [ ] AC-12: Both child FRs re-enter the judge pipeline and receive authority before any implementation edit is made.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No code, workflow, package-metadata, documentation, changelog, diary, or repository-setting implementation may proceed under combined FR-1104. | GATE |
| C-2 | The CI-dedup child must not change supported Python versions, classifiers, `requires-python`, or branch-protection contexts. | GATE |
| C-3 | The Python 3.14 child must inherit the separately judged CI topology and must not redesign optional-extra or pytest-partition policy. | GATE |
| C-4 | The operator must record `preserve` or `retire` for FR-756's isolated core-run signal before the CI-dedup child is judged. | GATE |
| C-5 | No Python 3.14 support authority may activate without the committed install, wheel, `pip check`, and test evidence required by R-4. | GATE |
| C-6 | Workflow and branch-protection changes require explicit human review; branch-protection mutation is operator-executed with before/after readback. | GATE |
| C-7 | Neither child may change the 3.11 floor, coverage threshold/flags, `constraints/dev-py312.txt`, unrelated workflow pins, or merge-queue state. | GATE |

Authority granted: only to create and submit the two replacement FRs and mark FR-1104 Split; no implementation authority is granted.

## Operator override (2026-09-26)

The operator overruled SPLIT and granted implementation authority to
FR-1104 as one FR, with FR-756's separate `-m "not process"` CI run
retired (R-2 option `retire`). Folded: R-3 (vision omission described
as lean-install only), R-4 (3.14 probe recorded in the FR before the
workflow edit), R-5 (merge-queue steps replaced by the strict-protection
migration). Not folded: R-1 (split) and R-6 (per-child research
records), overruled.

**Prior art:** FR-1104-ci-dedup-core-test-and-python-314.md is the FR
under judgement, not precedent; its own prior art (FR-756, FR-759,
FR-918, FR-934, FR-952) is dispositioned in the FR header.
