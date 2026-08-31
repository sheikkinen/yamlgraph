# Judgement: FR-937 The Research Route's Prompts and Its Validators Disagree About Precedent

**Prior art:** *(added when committing, not part of the judge's output)* the
retrieval returns only `FR-937-research-precedent-vocabulary-drift.md`, the FR
this document judges. A judgement matching its own FR is the intended
relationship, not undistinguished precedent — same self-exclusion gap noted in
`FR-937-evidence.md`.

**Verdict:** SPLIT — the precedent-contract reconciliation is sound and feasible after #525, but classification parsing and wrapper diagnostics are independent defects with separate seams and tests; no implementation authority exists until three replacement FRs carry admissible committed research and re-enter judgement.

**Reviewed against:** `feature-requests/FR-937-research-precedent-vocabulary-drift.md`; `feature-requests/FR-937.research.md`; `feature-requests/research-briefs/fr-937-precedent-vocabulary-drift-brief.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `capabilities/CAP-248-research-sole-route.yaml`; `scripts/research.sh`; `scripts/research_preflight.py`; `examples/demos/research-route/nodes/research_tools.py`; `examples/demos/research-route/prompts/data_process_planner.yaml`; `examples/demos/research-route/prompts/librarian_structure.yaml`; `examples/demos/research-route/prompts/os_infra_primitivist.yaml`; `examples/demos/research-route/prompts/subtractionist.yaml`; `examples/demos/research-route/prompts/yamlgraph_native_planner.yaml`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.judgement.md`; `feature-requests/FR-896-research-route-precedent-traceability.md`; `feature-requests/FR-896-research-route-precedent-traceability.judgement.md`; `feature-requests/FR-583-plot-modeller-evaluator-tolerance-and-vocab-grounding.md`; `feature-requests/FR-584-plot-modeller-L5-salience-and-roles.md`; `feature-requests/FR-592-perspective-vocab-extraction-stage.md`; `feature-requests/FR-593-story-level-vocabulary-pre-analysis-stage.md`; and, at committed ref `featfr932-prior-art-in-research`, `feature-requests/FR-932-prior-art-retrieval-in-research-route.md`, `feature-requests/FR-932-prior-art-retrieval-in-research-route.judgement.md`, `feature-requests/FR-933-retry-cannot-recover-deterministic-rejection.md`, `feature-requests/FR-933-retry-cannot-recover-deterministic-rejection.judgement.md`, `scripts/research_preflight.py`, `examples/demos/research-route/nodes/research_tools.py`, and `tests/unit/test_fr932_prior_art_in_research.py`. The cited `logs/research-coffee.log`, `logs/research-937.log`, and `feature-requests/research-briefs/operator-coffee-physical-actuation-brief.md` were not reviewed because they are absent from the committed tree; the FR, its research record, and its brief are also currently untracked, so they are draft inputs rather than admissible committed evidence.

## What is sound

The core precedent defect is concrete. All five prompts still instruct `brief-echo` (`examples/demos/research-route/prompts/subtractionist.yaml:67-73`; `examples/demos/research-route/prompts/librarian_structure.yaml:78-90`), while the dependency branch deliberately rejects that marker and admits bounded `none-retrieved` (`featfr932-prior-art-in-research:examples/demos/research-route/nodes/research_tools.py:427-457`). The second precedent witness is also grounded in code: the preflight checks `none-retrieved` before identifier shapes (`featfr932-prior-art-in-research:scripts/research_preflight.py:178-205`), whereas the reducer resolves committed identifiers first (`featfr932-prior-art-in-research:examples/demos/research-route/nodes/research_tools.py:437-451`). Correcting that composition bug at the existing validation seams is smaller than introducing a new validator or compile-time mechanism.

The FR protects the important inherited boundaries: `none-retrieved` remains conditional on empty retrieval, `brief-echo` remains rejected, identifier fabrication remains fatal, governed prompt edits use `scripts/author.sh`, and retrieval ranking is excluded (`feature-requests/FR-937-research-precedent-vocabulary-drift.md:119-155,174-185,197-204`). Its `is_this_a_graph` answer is explicit and credible (`feature-requests/FR-937-research-precedent-vocabulary-drift.md:141-147`). FR-896 and FR-932 are dispositioned as direct precedent, and rejected FR-592 plus the retrieved plot-modeller records are distinguished from this route (`feature-requests/FR-937-research-precedent-vocabulary-drift.md:18-31`).

### Rubric disposition

| Criterion | Finding |
|---|---|
| Scope | **Fails as one FR.** The FR itself identifies two defect classes (`feature-requests/FR-937-research-precedent-vocabulary-drift.md:105-107`), but W-5 is not a substring/claim-parsing defect at all: the helper already reports `missing or empty required heading` (`scripts/research_preflight.py:110-128`), while the misleading message comes from the wrapper (`scripts/research.sh:26-30`). Precedent reconciliation, classification parsing, and wrapper diagnostics can be implemented and tested independently. |
| Consistency | **Needs correction.** Proposed step 1 says all five prompts gain `none-retrieved` (`feature-requests/FR-937-research-precedent-vocabulary-drift.md:119-123`), while AC-01 limits that instruction to non-librarians (`feature-requests/FR-937-research-precedent-vocabulary-drift.md:159-162`). The librarian is URL-only (`examples/demos/research-route/prompts/librarian_structure.yaml:20-22,38-46,78-93`). The FR also names a nonexistent dependency API, `_precedent_kind` (`feature-requests/FR-937-research-precedent-vocabulary-drift.md:65-69,171-173`); the committed dependency implements `_classify_precedent` (`featfr932-prior-art-in-research:examples/demos/research-route/nodes/research_tools.py:427-457`). |
| Measurability | **Partly fails.** AC-02 does not define how “vocabulary offered” is extracted from prose or how unlike return types become equal (`feature-requests/FR-937-research-precedent-vocabulary-drift.md:163-166`). AC-04 likewise does not define a shared pass/fail projection. AC-08 targets a message already emitted by the helper rather than the wrapper that adds the false diagnosis (`scripts/research_preflight.py:121-143`; `scripts/research.sh:29-30`). |
| Feasibility | **Passes conditionally.** The dependency branch contains the required `none-retrieved`, retrieval-block, `_check_precedent`, and `_classify_precedent` seams, and direct tests already exercise their bounded behavior (`featfr932-prior-art-in-research:tests/unit/test_fr932_prior_art_in_research.py:200-251,309-375`). Those seams are not present in the current branch, exactly as the dependency declaration acknowledges (`feature-requests/FR-937-research-precedent-vocabulary-drift.md:33-35`). |
| Architecture alignment | **Passes for the precedent concern.** The plan amends the existing prompt, reducer, preflight, capability, and tests rather than adding a new runtime abstraction; authoring remains routed through `scripts/author.sh` (`feature-requests/FR-937-research-precedent-vocabulary-drift.md:119-137,182-185`). |
| Single responsibility | **Fails.** W-1/W-2 and W-3 concern one precedent contract; W-4 concerns classification syntax; W-5 concerns shell-wrapper error propagation (`feature-requests/FR-937-research-precedent-vocabulary-drift.md:82-107`). These are orthogonal change and regression surfaces, so the doctrine requires SPLIT. |
| Strategic classification | **Contrib/example defect corrections.** Each replacement has one repository use case and repairs gaps in existing research-route abstractions. None establishes a framework primitive, and documentation alone cannot cure the executable contradictions. |
| Testability | **Passes after split and grammar revision.** Each seam admits a direct failing test, but the current cross-validator equality criterion is underspecified and the heading criterion names the wrong seam. The existing requirement is `REQ-YG-623` (`capabilities/CAP-248-research-sole-route.yaml:20-50`). |

## Required revisions

### R-1: Split the proposal into three independently judged FRs

Create: (A) precedent-contract reconciliation for W-1/W-2/W-3; (B) classification-claim parsing for W-4; and (C) wrapper diagnostic propagation for W-5. Each FR must contain only its own production seam, tests, live witness if applicable, documentation updates, and implementation record. Do not carry the prompt/validator anti-drift work into B or C.

### R-2: Establish admissible research closure for every replacement FR

Commit each replacement FR's research record and closed brief before judgement. Replace the uncommitted log references with committed evidence or fold exact, reproducible excerpts plus commands into a committed evidence record. The current research record has only three distinct solution classes—`boundary-enforcement`, `schema-data`, and `external-method` (`feature-requests/FR-937.research.md:26-32`)—not the doctrine's substantive 4-6 classes. The precedent replacement must provide 4-6 genuine solution classes, preserve disagreement, and disposition each; B and C need their own committed research records or equivalent committed alternatives tables.

### R-3: State the precedent contract by persona and actual API

In replacement A, require removal of `brief-echo` from all five prompts, but teach `none-retrieved` only to the four internal personas. Preserve the librarian's requirement to copy a real URL from tool results. Replace every `_precedent_kind` reference with the dependency's actual `_classify_precedent` name unless the dependency changes before rebase, in which case cite the landed symbol and update all criteria consistently.

### R-4: Define marker claims and validator agreement mechanically

In replacement A, define a marker claim as a stripped precedent cell equal to the marker or beginning with `<marker>:`; an incidental occurrence elsewhere is not a claim. Resolve committed identifier/URL shapes before marker classification, so a valid citation that merely names `none-retrieved` remains traceable. Specify one truth table and map both validators to the same `accept`/`reject` projection. Preserve the reducer's stronger filesystem existence checks; agreement concerns precedence and marker semantics, not pretending the preflight's shape check proves existence.

Replace AC-02's free-form “vocabulary equals” assertion with exact contract witnesses: all five prompts omit the retired marker; the four internal prompts contain the canonical bounded `none-retrieved` instruction; the librarian contains neither an internal honest-miss escape nor a weakened URL rule; code constants expose the same two marker tokens; and editing either the prompt token or code token alone fails the test.

### R-5: Update the capability contract and dependency boundary

Replacement A must update `capabilities/CAP-248-research-sole-route.yaml`, whose `REQ-YG-623` text still says `brief-echo` is demoted and preserved (`capabilities/CAP-248-research-sole-route.yaml:20-50`). Rebase onto the landed #525 head before RED because the current branch does not contain the target functions. No replacement FR may claim an executable RED against symbols absent from its base.

### R-6: Freeze classification syntax in the classification-only FR

Replacement B must define the classification claim as the first non-empty line's leading enum token, followed only by end-of-line or a documented explanation delimiter. Later explanatory prose is not scanned for additional claims. Add direct fixtures proving: one leading class plus a later disclaimer mentioning another class passes; two classes in the claim position fail; zero/unknown classes fail; and all other brief-closure checks remain unchanged.

### R-7: Test the wrapper diagnostic at the wrapper seam

Replacement C must change only `scripts/research.sh` and its direct test surface so a brief-preflight failure retains the specific `research_preflight.py` violations and the wrapper adds only a neutral summary such as `brief closure preflight failed; see violations above`. A subprocess test with a missing-heading brief must assert exit 64, the exact missing-heading diagnostic, and absence of `remove solution-shaped sections`.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Replacement FR A: internal-persona precedent prompt contract, `research_tools.py`, `research_preflight.py` precedent validation, `CAP-248`, focused tests, two live witnesses, changelog, implementation status, and diary |
| D-2 | Replacement FR B: classification claim parser in `scripts/research_preflight.py`, focused unit fixtures, changelog, implementation status, and diary |
| D-3 | Replacement FR C: neutral brief-preflight failure summary in `scripts/research.sh`, focused subprocess regression test, changelog, implementation status, and diary |
| D-4 | Committed research/brief/evidence records and independent judgements for D-1, D-2, and D-3 |

Not authorized: any implementation under FR-937 as currently written; retrieval ranking/floor/corpus changes; `max_length=400` changes; new personas or schema columns; weakening `none-retrieved`, identifier, or librarian URL validation; compile-time precedent validation; changes to graph topology; changes to judge, authoring, review, CI, or hook routes; or edits outside the three named seams.

## Revised acceptance criteria

- [ ] AC-01: Three replacement FRs exist with the exact D-1/D-2/D-3 scopes, each with a committed `**Research:**` target or equivalent committed alternatives table and its own judgement.
- [ ] AC-02: Replacement A is based on the landed #525 changes and refers to the actual reducer symbol present after rebase.
- [ ] AC-03: Replacement A's RED test proves all five prompts omit `brief-echo`; exactly the four internal persona prompts carry the canonical bounded `none-retrieved` instruction; the librarian remains URL-only.
- [ ] AC-04: Replacement A defines a shared truth table covering a committed citation that mentions `none-retrieved`, a valid empty-retrieval claim, the same claim with non-empty retrieval, `brief-echo: ...`, prose-only precedent, and a fabricated identifier; both validators agree on pass/fail for shared semantics while the reducer retains filesystem existence enforcement.
- [ ] AC-05: Replacement A's anti-drift test fails when either a canonical prompt marker or its code constant changes alone, without attempting general natural-language extraction.
- [ ] AC-06: Replacement A updates `CAP-248`/`REQ-YG-623` from `brief-echo` demotion to bounded `none-retrieved` rejection semantics.
- [ ] AC-07: Replacement A's prompt changes are produced through `scripts/author.sh`; `tmp/draft-authoring-report.md` records governed files, lint, smoke, and limitations.
- [ ] AC-08: Replacement A runs the committed empty-retrieval W-1 witness and non-empty W-3 witness through `scripts/research.sh`; each exits 0, produces five persona rows, passes artifact preflight, and appends a reconcilable provenance line.
- [ ] AC-09: Replacement B's parser accepts one leading classification followed by explanatory prose that mentions/disclaims another enum, and rejects zero, unknown, or two claim-position enum values.
- [ ] AC-10: Replacement B changes no precedent, artifact, forbidden-heading, or candidate-bullet behavior.
- [ ] AC-11: Replacement C's subprocess test proves a missing-heading brief exits 64, prints `missing or empty required heading: ## <name>`, and never prints `remove solution-shaped sections`.
- [ ] AC-12: All new tests use `@pytest.mark.req("REQ-YG-623")`; each replacement FR carries its own changelog fragment, implementation-status update, and diary reflection.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No code, prompt, capability, or script implementation is authorized by this SPLIT verdict; each replacement FR must re-enter judgement independently. | GATE |
| C-2 | Replacement A may begin RED only after #525 lands and the branch is rebased onto the landed implementation. | GATE |
| C-3 | Research records, briefs, and evidence cited for authority must be committed and substantive before each replacement judgement. | GATE |
| C-4 | Prompt edits must be produced through `scripts/author.sh`; direct edits to governed graph artifacts are forbidden. | GATE |
| C-5 | `none-retrieved` remains bounded by the retrieval block, fabricated identifiers remain fatal, and librarian URL reconciliation remains unchanged. | GATE |
| C-6 | Replacement B and C must not modify precedent semantics; replacement A must not modify classification parsing or wrapper diagnostics. | GATE |

Authority granted: none; authority may be granted only by independent judgements on the three replacement FRs after their committed evidence and exact contracts satisfy these gates.
