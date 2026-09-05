# Judgement: FR-966 reject unsatisfiable multi-value `visibility` in authored-PR discovery

**Verdict:** APPROVED WITH REVISIONS — the boundary rejection is the smallest workable fix, but authority activates only after R-1 through R-4 are folded into the FR and its research record.

**Prior art:** [FR-966-visibility-conjunction-unsatisfiable.md](FR-966-visibility-conjunction-unsatisfiable.md) and [FR-966.research.md](FR-966.research.md) — the subject of this judgement, not competing prior art. [FR-967-unwitnessed-acceptance-criteria.md](FR-967-unwitnessed-acceptance-criteria.md) and its judgement — the sibling arc from the same audit; it closes the process hole that let this defect ship, this one fixes the defect. Disjoint deliverables, no overlap in frozen scope. [FR-534-dm-v2-project-protected-characters-into-prose.md](FR-534-dm-v2-project-protected-characters-into-prose.md) [Enforced] — matched on the noun "conjunction" used in the grammatical sense in dungeon-master prose generation; a vocabulary collision with no bearing on GitHub query semantics.

**Reviewed against:** `feature-requests/FR-966-visibility-conjunction-unsatisfiable.md`; `feature-requests/FR-966.research.md`; `feature-requests/FR-962-person-profile-census-authored-prs.md`; `feature-requests/FR-939-map-overflow-policy.md`; `feature-requests/FR-943-census-row-failure-containment.md`; `feature-requests/FR-967-unwitnessed-acceptance-criteria.md`; `examples/demos/corpus_census/adapters/corpus_adapters.py`; `examples/demos/person_profile_census/README.md`; `capabilities/CAP-253-org-repo-census.yaml`; `capabilities/CAP-259-declared-text-encoding.yaml`; `ARCHITECTURE.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The defect is concrete and reproduced: `_parse_visibility` accepts multiple valid values, then `gh_authored_prs_discover` emits one repeated flag per value (`corpus_adapters.py:202-266`), while the committed corp invocation supplies two values (`person_profile_census/README.md:112`). Rejecting the impossible conjunction after existing entry validation and before `_gh` is a minimal boundary fix aligned with the repository's normalization law. The FR preserves the FR-962 list-shaped slot input (`FR-962:98-101`), avoids a new model or framework primitive, keeps unrelated overflow and row-containment behavior outside scope, and proposes direct no-network witnesses. Strategic classification: **Contrib/example** — one authored-PR adapter and its person-profile caller are affected; no framework abstraction is warranted.

Scope, consistency, feasibility, single responsibility, and direct testability are otherwise sound. The acceptance plan correctly distinguishes the parser rejection, the surviving one-value argv, pre-network ordering, documentation, and changelog surfaces.

| Rubric criterion | Finding |
|---|---|
| Scope | Minimal after revision: one parser guard, one focused witness file, and the caller documentation (`FR-966:75-105`); union semantics and scalar-input churn are rejected (`FR-966:131-147`). |
| Consistency | Direction is consistent, but the proposed canonical-list diagnostic conflicts with AC-01's verbatim-echo claim, and AC-03 incompletely names existing validation (`FR-966:86-91,110-119`); R-3 resolves both. |
| Measurability | Pre-network rejection, argv cardinality, parser results, README text, strict requirement coverage, and a changelog artifact are mechanically checkable (`FR-966:110-127`); R-4 supplies the missing requirement identity and delivery records. |
| Feasibility | The existing parser already owns JSON, enum, duplicate, and canonicalization checks, and the call occurs before argv construction (`corpus_adapters.py:202-266`), so the guard requires no new dependency or abstraction. |
| Architecture alignment | The correction occurs at the external-input validation boundary, matching the repository's normalize-at-entry law (`.github/copilot-instructions.md:45-47,225`) and preserving FR-962's list-shaped tool-slot contract (`FR-962:98-101`). |
| Single responsibility | The FR changes only unsatisfiable authored-PR visibility input and its documented invocation; FR-939 overflow and FR-943 row containment are explicitly separated (`FR-966:13,150-153`). |
| Strategic classification | **Contrib/example**: one existing example adapter and one sibling demo consume the behavior (`FR-966:29-64`); no third use case or framework gap is established. |
| Testability | A failing cardinality test, a fail-if-called `_gh` stub, and an accepted-response argv stub derive directly from the requested behavior (`FR-966:110-124`); R-3 freezes edge cases and R-4 gives every witness an owning REQ. |

## Required revisions

### R-1: Replace implementation variants with substantive research classes

Amend `FR-966.research.md` to contain four to six genuinely distinct solution classes, each with precedent/evidence, effort-risk, and disposition. The current five rows collapse to only two outcomes: reject multiple values or change the same input to a scalar (`FR-966.research.md:16-20`); moving the same length rule between a function and Pydantic is not another solution class. Include and disposition at least: boundary rejection while retaining list shape; one query per class with an explicit union/provenance contract; a platform-supported disjunctive query only if cited evidence proves one exists; and subtraction of the visibility filter or multi-value surface. Preserve real disagreement, or state that no dissent survived only after these distinct outcomes were compared. Keep the explicit `is_this_a_graph: no` answer.

### R-2: Repair the dangling prior-art citation

Replace `FR-939-map-overflow-detection.md` in the FR's Prior art field (`FR-966:13`) with the committed `FR-939-map-overflow-policy.md`. Retain the disposition that overflow policy and FR-943 row containment do not authorize query-construction changes.

### R-3: Freeze validation order and diagnostic identity

Revise the Proposed Solution and criteria to state that existing shape and entry validation completes before the new cardinality check. Unknown values, non-string entries, empty lists, malformed JSON strings, non-list JSON values, and casefold duplicates must retain their existing failure classes; a valid single value must retain casefold canonicalization. For a valid multi-value list, the conjunction error must include the parsed list's `repr` in original order and spelling, name repeated `--visibility` conjunction semantics, and state the one-class-per-run remedy. Do not call a malformed JSON string merely "non-JSON input," and do not claim the canonicalized list is a verbatim echo (`FR-966:86-91, 110-119`).

### R-4: Add the missing requirement owner and complete the delivery record

Add `capabilities/CAP-260-authored-pr-visibility.yaml` with `REQ-YG-642`, regenerate `ARCHITECTURE.md`, and require every new test to carry `@pytest.mark.req("REQ-YG-642")`. Define REQ-YG-642 as the retained list-shaped visibility contract: exactly one valid class per authored-PR discovery run, rejection before GitHub execution for valid multi-class input, and exactly one emitted `--visibility` flag for accepted input. Amend the changelog criterion to require a `fix` fragment naming FR-966 and REQ-YG-642. Add criteria for a RED witness committed before GREEN, the FR implementation/status record, and the final diary reflection required by repo doctrine (`.github/copilot-instructions.md:168-169,196`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-966-visibility-conjunction-unsatisfiable.md` and `feature-requests/FR-966.research.md` — fold R-1 through R-4 and later record implementation status |
| D-2 | `examples/demos/corpus_census/adapters/corpus_adapters.py` — add only the post-entry-validation cardinality guard |
| D-3 | `tests/unit/test_fr966_authored_pr_visibility.py` — parser, pre-network rejection, and accepted argv witnesses |
| D-4 | `examples/demos/person_profile_census/README.md` — document one class per run and change the corp invocation to one class |
| D-5 | `capabilities/CAP-260-authored-pr-visibility.yaml` and regenerated `ARCHITECTURE.md` — REQ-YG-642 registration |
| D-6 | One `fix` fragment under `changelog/unreleased/` naming FR-966 and REQ-YG-642 |
| D-7 | One FR-966 reflection under `docs/diary/` |

Not authorized: changing the visibility input from a JSON list to a scalar; executing or unioning multiple GitHub queries; changing `_gh`, `gh_pr_extract`, graph or prompt artifacts, tool-slot manifests, empty-population behavior, overflow policy, row-failure containment, YAMLGraph core, CI, hooks, or judge/review doctrine; modifying FR-962's frozen artifact; introducing Pydantic or a shared validation abstraction.

## Revised acceptance criteria

- [ ] AC-01: `FR-966.research.md` records four to six substantively distinct solution classes with evidence/precedent, effort-risk, disposition, preserved disagreement, and `is_this_a_graph: no`; parser-location variants are not counted as separate classes.
- [ ] AC-02: The FR's FR-939 prior-art link resolves to `FR-939-map-overflow-policy.md`; FR-939 and FR-943 remain explicitly outside query-construction scope.
- [ ] AC-03: A valid two-or-more-value visibility list raises before `_gh`; the exact error asserts repeated `--visibility` conjunction semantics, the parsed list's `repr` in original order and spelling, and the one-class-per-run remedy.
- [ ] AC-04: A stub that fails if called proves the AC-03 rejection occurs before every GitHub invocation.
- [ ] AC-05: Existing validation remains ordered and witnessed for malformed JSON string, non-list JSON value, empty list, non-string entry, unknown class, and casefold duplicate.
- [ ] AC-06: A mixed-case single-element list returns the canonical one-element list, and `gh_authored_prs_discover` sends exactly one `--visibility` flag with the canonical value to a stubbed `_gh`; no network call occurs.
- [ ] AC-07: The retained argv test also proves the accepted non-empty GitHub response is converted to the existing sorted authored-PR identity shape; no unrelated discovery behavior changes.
- [ ] AC-08: `examples/demos/person_profile_census/README.md` states that each run accepts one visibility class and separate classes require separate operator-invoked runs; its corp example supplies exactly one list element.
- [ ] AC-09: `CAP-260-authored-pr-visibility.yaml` registers FR-966 and REQ-YG-642; regenerated `ARCHITECTURE.md` contains REQ-YG-642; every new test carries `@pytest.mark.req("REQ-YG-642")`; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-10: The failing cardinality witness is committed before the production fix; the GREEN commit makes the focused FR-966 test file pass.
- [ ] AC-11: A `fix` changelog fragment names FR-966 and REQ-YG-642; the FR records implementation status, decisions, and deviations; a diary entry records the completed correction and a `Seed:`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No implementation authority exists until R-1 through R-4 are folded into the committed FR and research record. | GATE |
| C-2 | Preserve the JSON-list slot shape and all existing one-value validation/canonicalization behavior. | GATE |
| C-3 | The new guard runs only after existing entry validation and before `_gh`; no network-backed test is permitted. | GATE |
| C-4 | Commit the failing REQ-YG-642 witness before the production change, then make the focused suite green. | GATE |
| C-5 | Do not modify any graph or prompt artifact; this correction is not graph authoring. | GATE |
| C-6 | Stop enforcement if satisfying the fix requires union semantics, shared framework code, or any surface outside D-1 through D-7. | GATE |

Authority granted: after R-1 through R-4 are folded and human-reviewed, implement only the single-class authored-PR visibility boundary, its deterministic no-network witnesses, documentation correction, traceability registration, changelog, FR record, and diary entry frozen above.
