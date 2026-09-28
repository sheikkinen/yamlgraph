# Judgement: FR-1134 Retire the stale FR knowledge graph and the FR-275 meta-tests

**Verdict:** SPLIT — both retirements are individually plausible, but they remove two independent capabilities with different owners, requirements, code surfaces, witnesses, and rollback paths; no implementation authority is granted until each concern is re-filed and judged separately.

**Reviewed against:** `feature-requests/FR-1134-retire-fr-knowledge-graph-and-fr275-meta-tests.md`; cited prior FRs `feature-requests/FR-275-test-speed-optimization.md`, `feature-requests/FR-814-fr-knowledge-graph-extraction.md`, `feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.md`, `feature-requests/FR-816-knowledge-graph-cluster-display-names.md`, `feature-requests/FR-817-knowledge-graph-cross-cluster-mentions.md`, `feature-requests/FR-818-judge-prior-art-context-narrowing.md`, `feature-requests/FR-938-prior-art-retrieval-in-research-route.md`, and `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md`; cited prior judgements `feature-requests/FR-814-fr-knowledge-graph-extraction.judgement.md`, `feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.judgement.md`, and `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.judgement.md`; cited implementation and evidence surfaces `scripts/extract_fr_graph.py`, `reference/fr-knowledge-graph.yaml`, `reference/fr-knowledge-graph.md`, `tests/fixtures/fr_graph_validation.yaml`, `tests/unit/test_fr_graph.py`, `.github/hooks/scripts/checks/prior_art.py`, `.github/hooks/tests/test_fr938_rare_floor.py`, `tests/unit/test_fr275_test_speed_optimization.py`, `tests/unit/test_fr1012_chaplain_removed.py`, `scripts/size_gate.py`, `capabilities/CAP-126-test-speed-optimization.yaml`, `capabilities/CAP-240-fr-knowledge-graph.yaml`, `capabilities/CAP-264-chaplain-runtime-retired.yaml`, `ARCHITECTURE.md`, `pyproject.toml`, `docs/confessions.md`, and `.github/workflows/workflow.yml`; repository history for `reference/fr-knowledge-graph.yaml`; repo doctrine `.github/copilot-instructions.md`, `.github/skills/judge-fr/doctrine.md`, and `.github/skills/judge-fr/judgement.template.md`.

Input-closure exclusions: the local uncommitted timing log named at `feature-requests/FR-1134-retire-fr-knowledge-graph-and-fr275-meta-tests.md:62-64` and the uncommitted FR-1131 worktree draft named at `:28-30` were not consumed and cannot support authority.

## What is sound

The two reported problems are real enough to plan independently. The committed graph identifies itself as 689 FRs and 1,683 edges (`reference/fr-knowledge-graph.yaml:1-9`), ends at FR-819 (`reference/fr-knowledge-graph.yaml:3623`), and is loaded by the prior-art hook before `_graph_prior_art` looks up the new FR's node (`.github/hooks/scripts/checks/prior_art.py:123-184,213-217`). The hook then applies the 1.5 multiplier and `[graph:cluster]` annotation only when that lookup returns members (`.github/hooks/scripts/checks/prior_art.py:264-286`). The FR therefore correctly identifies a stale derived artifact whose graph path is ineffective for newer FR IDs (`feature-requests/FR-1134-retire-fr-knowledge-graph-and-fr275-meta-tests.md:41-46,68-79`).

The FR-275 pruning target is also concrete. All 13 REQ-YG-275 witnesses are concentrated in one file; several invoke nested pytest processes, one has a `pass` body, and others grep source or documentation text (`tests/unit/test_fr275_test_speed_optimization.py:19-47,53-104,111-159,168-247,249-289`). Keeping the marker-registration assertion preserves a direct witness for the configured marker (`tests/unit/test_fr275_test_speed_optimization.py:19-31`; `pyproject.toml:231`).

The subtraction pattern is aligned with precedent: FR-1012/CAP-264 witnesses a retired end state through an absence test and a retired-state capability (`capabilities/CAP-264-chaplain-runtime-retired.yaml:1-20`; `tests/unit/test_fr1012_chaplain_removed.py:179-231`). The proposal also correctly protects FR-938's `rare_floor` behavior and its bare-Python execution test (`feature-requests/FR-1134-retire-fr-knowledge-graph-and-fr275-meta-tests.md:33-35,126-128`; `.github/hooks/tests/test_fr938_rare_floor.py:50-114,117-157`).

**Rubric findings:**

1. **Scope:** each retirement is bounded, but their union is not minimal. The graph concern deletes CAP-240, REQ-YG-601..603, a generated artifact, extractor, documentation, fixtures, hook logic, and a size-gate entry (`feature-requests/FR-1134-retire-fr-knowledge-graph-and-fr275-meta-tests.md:109-138`). The FR-275 concern edits only a separate CAP-126 witness module while retaining REQ-YG-275 (`:81-94,130-131,149-151`). Either can ship without the other.
2. **Consistency:** the Summary openly names “two things” and two retirements (`:37-52`), while A-6 rejects a split only because of an operator delivery preference (`:170`). That preference does not create a dependency between the capabilities. The proposed single RED test and REQ-YG-716 combine both absences (`:104-116`), although CAP-293 is named only for the graph retirement (`:132-136`).
3. **Measurability:** path absence, symbol absence, requirement coverage, capability validation, and CI duration are mechanically observable (`:142-159`). AC-03 does not actually specify a before/after byte fixture, so unchanged existing tests are only a proxy for the byte-identity claim (`:146-148`). AC-06 is open-ended because it allows the failure list to be invented “at enforce time” (`:154-156`), contrary to the doctrine that the current author owns a red suite (`.github/copilot-instructions.md:20`).
4. **Feasibility:** the named surfaces and dependencies exist. CAP-240 owns the extractor, artifact, hook integration, and REQ-YG-601..603 (`capabilities/CAP-240-fr-knowledge-graph.yaml:1-44`); the size gate has the exact extractor baseline entry (`scripts/size_gate.py:37-43`); and CI runs the full unit suite with coverage in both matrix jobs (`.github/workflows/workflow.yml:41-42,84`).
5. **Architecture alignment:** an absence witness plus retired-state CAP follows CAP-264, and regenerating `ARCHITECTURE.md` from capability records follows the registry pattern. The FR-275 half is not yet aligned with substantive requirement traceability: CAP-126/REQ-YG-275 claims marker selection, slow-test marking, configurable timing, documented commands, unchanged default behavior, and comprehensive acceptance tests (`capabilities/CAP-126-test-speed-optimization.yaml:1-33`), but after the proposed deletion its only REQ-YG-275 witness would assert marker registration.
6. **Single responsibility:** the proposal fails this criterion. CAP-240 graph retirement changes governance retrieval and generated-artifact ownership; CAP-126 test pruning changes the witness set for test-speed infrastructure. They have no causal implementation dependency. Judge doctrine requires orthogonal bundles to receive `SPLIT` (`.github/skills/judge-fr/doctrine.md:49-50,75-77`).
7. **Strategic classification:** the graph successor is retirement of a repo-governance framework primitive because it changes the prior-art hook and capability registry. The FR-275 successor is maintenance of the existing CAP-126 framework primitive, not part of graph retirement. The differing classifications reinforce separate authority.
8. **Testability:** direct failing absence tests can be derived for the graph retirement, and an exact test-count/import assertion can be derived for FR-275 pruning. A faithful combined test cannot map one REQ-YG-716 capability claim to both retirements, and the CAP-126 clause-to-witness gap prevents the proposed one-test end state from proving what REQ-YG-275 still says (`feature-requests/FR-1134-retire-fr-knowledge-graph-and-fr275-meta-tests.md:106-116,132-136`; `capabilities/CAP-126-test-speed-optimization.yaml:15-33`).

## Required revisions

### R-1: Replace FR-1134 with two independently judged feature requests

File one successor FR for the FR knowledge-graph retirement and one successor FR for FR-275 witness pruning. Each must have its own first consumer, Ideal Result, research record, requirement ownership, RED/GREEN sequence, acceptance criteria, changelog fragment, and Distill obligation. Do not reuse a single test module or a single new requirement across both concerns.

The operator decision at `feature-requests/FR-1134-retire-fr-knowledge-graph-and-fr275-meta-tests.md:170` is a delivery preference, not evidence that the changes are one responsibility. The human decision that remains to be recorded after both successors receive independent authority is: **must the independently authorized changes use two PRs, or may two separately witnessed and separately revertible change sets share one PR?** That submission decision cannot collapse the two plans or their judgement gates.

### R-2: Commit substantive research for each successor

Do not rely on the local timing log or the uncommitted FR-1131 draft. Promote the measurements needed by each successor into committed evidence, including command, revision, environment, per-test timing rows, and workflow run identifiers for the claimed 366–592 second baseline. The graph successor may cite reproducible facts from the committed artifact and repository history; the FR-275 successor must carry the timing evidence on which its value claim depends.

Each Research field must explicitly answer `is_this_a_graph`. For both successors the expected answer is “No: this is deterministic subtraction and registry/test reconciliation, not a per-item model pipeline, multi-stage LLM flow, or subagent fan-out.” The current in-body alternatives omit that required answer (`.github/skills/judge-fr/doctrine.md:118-128`; `.github/copilot-instructions.md:129`).

### R-3: Freeze the graph-retirement successor around CAP-240

The graph successor may propose only:

- deletion of `scripts/extract_fr_graph.py`, `reference/fr-knowledge-graph.yaml`, `reference/fr-knowledge-graph.md`, `tests/fixtures/fr_graph_validation.yaml`, `tests/unit/test_fr_graph.py`, and `capabilities/CAP-240-fr-knowledge-graph.yaml`;
- removal of graph-only loading, lookup, scoring, and annotation code from `.github/hooks/scripts/checks/prior_art.py`;
- removal of the extractor's stale `scripts/size_gate.py` baseline entry;
- the graph-specific docstring cleanup in `.github/hooks/tests/test_fr938_rare_floor.py`;
- registry regeneration, a graph-retired capability/requirement, a graph-only absence witness, changelog, and Distill.

It must preserve noun extraction, status handling, weighted-zone ranking, rare-floor policy, self-exclusion, and TOP_N output. Replace the current AC-03 proxy with a committed fixture for an FR ID above 819 whose complete `build_prior_art` output is asserted before and after graph removal. Existing FR-737/738/938 tests remain necessary but are not by themselves proof of byte identity (`feature-requests/FR-1134-retire-fr-knowledge-graph-and-fr275-meta-tests.md:146-148`).

### R-4: Reconcile CAP-126 before pruning REQ-YG-275 witnesses

The FR-275 successor must map every clause of CAP-126/REQ-YG-275 to a surviving behavioral witness. For each clause, either name the surviving test ID that directly proves it or narrow the capability requirement text in the same GREEN change. `python scripts/req_coverage.py --strict` is necessary but insufficient: one remaining `@pytest.mark.req("REQ-YG-275")` marker would shape-check the registry while leaving most of the current requirement prose unwitnessed.

The successor may delete the empty test, nested-pytest checks of pytest's own marker syntax, and source/documentation greps only after that clause-to-witness table is frozen. It must retain the direct marker-registration witness. It must not introduce `--strict-markers`, alter pytest defaults, change production timing behavior, or edit graph-retirement surfaces.

### R-5: Replace open-ended suite exceptions with green gates

Remove the clause allowing failures to be listed at enforce time. Each successor must name targeted commands and require them to pass, followed by a green full unit suite. A red result must be reproduced and corrected or the change must stop; unchanged failure counts are not acceptance evidence (`feature-requests/FR-1134-retire-fr-knowledge-graph-and-fr275-meta-tests.md:154-156`; `.github/copilot-instructions.md:20,198`).

Timing criteria must identify the exact measurement command and committed output record. Record CI job URLs/IDs, revisions, Python versions, durations, and conclusions rather than only copying two elapsed-time numbers into prose.

### R-6: Require human review of the hook subtraction

The graph successor changes enforcement infrastructure. Its judgement must carry a GATE requiring human review of the `prior_art.py` and hook-test diff before merge, as required by judge doctrine (`.github/skills/judge-fr/doctrine.md:98-103`). No graph-retirement authority may alter judge/review doctrine, the research route, `prior_art_gate.py`, FR marker policy, or CI configuration.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Replacement FR: retire CAP-240 and the stale FR knowledge graph, including only its extractor/artifact/docs/fixtures/tests, graph-only prior-art-hook code, size-gate entry, registry output, retired-state witness, changelog, and Distill |
| D-2 | Replacement FR: prune FR-275 meta-tests while reconciling every CAP-126/REQ-YG-275 claim with surviving direct witnesses, plus its own changelog and Distill |

Not authorized under FR-1134: any code or test implementation; deleting either capability surface; changing `.github/hooks/scripts/checks/prior_art.py`; editing `tests/unit/test_fr275_test_speed_optimization.py`; allocating CAP-293 or REQ-YG-716; combining both retirements in one witness or requirement; changing `prior_art_gate.py`, research-route behavior, judge/review doctrine, pytest defaults, CI configuration, or `--strict-markers`; editing historical FRs, judgements, diaries, recaps, released changelog records, or `docs/mercury-census/findings.md`; invoking another judge.

## Revised acceptance criteria

- [ ] AC-01: FR-1134 is superseded by two committed successor FR files matching D-1 and D-2; each re-enters judgement independently before implementation.
- [ ] AC-02: Each successor has a committed substantive research record with 4–6 genuine solution classes, precedent disposition, preserved disagreement, and an explicit `is_this_a_graph` answer; no authority depends on the local timing log or uncommitted FR-1131 draft.
- [ ] AC-03: The graph successor enumerates the exact six deletions and exact graph-only edits to `prior_art.py`, `test_fr938_rare_floor.py`, and `size_gate.py`; it explicitly preserves all non-graph retrieval behavior.
- [ ] AC-04: The graph successor defines a graph-only RED witness and a committed FR>819 fixture whose full `build_prior_art` output is identical before and after removal; existing hook tests and the full hook suite must pass.
- [ ] AC-05: The graph successor removes CAP-240 and REQ-YG-601..603, adds one graph-retired CAP/REQ and absence witness, regenerates `ARCHITECTURE.md`, and passes strict requirement and capability validation.
- [ ] AC-06: The FR-275 successor names exactly which tests are removed, retains the marker-registration witness, and includes a clause-to-witness table covering every surviving CAP-126/REQ-YG-275 claim; no claim is treated as covered merely because one test carries the requirement marker.
- [ ] AC-07: The FR-275 successor records the exact timing command and committed per-test results, and proves the retained test file has the frozen imports and test count without changing pytest marker semantics or timing behavior.
- [ ] AC-08: Each successor has its own RED commit containing only its focused failing witness and its own GREEN change; targeted tests, strict requirement coverage, capability validation, and the full unit suite are green with no deferred failure allowance.
- [ ] AC-09: Each successor includes its own removal changelog fragment and Distill diary entry with a **Seed:**.
- [ ] AC-10: A human reviews the graph successor's enforcement-infrastructure diff before merge; the review confirms that rare-floor retrieval and hook output outside the removed graph annotation remain unchanged.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement FR-1134 as written; create and judge the two successor FRs first. | GATE |
| C-2 | Do not share one CAP, REQ, RED witness, or GREEN authority across the graph retirement and FR-275 pruning. | GATE |
| C-3 | Do not delete REQ-YG-275 witnesses until every surviving CAP-126 claim has a named direct witness or is narrowed in the same change. | GATE |
| C-4 | Do not use uncommitted timing logs, an uncommitted FR-1131 draft, or an enforce-time failure list as acceptance evidence. | GATE |
| C-5 | Preserve FR-938 `rare_floor` behavior, noun-frequency ranking, self-exclusion, status tags, TOP_N behavior, and bare-Python hook execution. | GATE |
| C-6 | Treat the prior-art-hook subtraction as enforcement infrastructure requiring human review; do not modify adjacent gates, doctrine, research-route behavior, or CI. | GATE |
| C-7 | Historical records remain immutable; retirement is represented by current capability, architecture, witness, changelog, and diary surfaces only. | GATE |

Authority granted: no implementation authority is granted; authority is limited to filing the two committed successor FRs described in D-1 and D-2 for independent judgement.

## Operator override (2026-09-28)

**Prior art:** FR-1134 (the judged FR itself); FR-1104 judgement
(precedent for this override section).

The operator overruled SPLIT ("no split") and granted implementation
authority to FR-1134 as one FR and one PR (precedent: FR-1104).
Folded: R-2 (measurements committed in the FR body with command,
revision and environment; `is_this_a_graph` answered), R-3 (committed
characterization witness for FR ids above FR-819, plus a whole-corpus
before/after diff recorded in the FR), R-4 (REQ-YG-275 narrowed to the
claim its surviving witness proves, clause table in the FR), R-5 (no
failure allowance; targeted commands and a green full unit suite; CI
run IDs recorded), R-6 (human review of the `prior_art.py` diff is a
GATE before merge). C-2 partly folded: the two retirements keep
separate requirements (REQ-YG-720 for the graph, REQ-YG-275 for FR-275)
and separate witnesses. Not folded: R-1 and C-1 (split), overruled.
CAP-293/REQ-YG-716 named above were taken on main by FR-1129 (#739)
before this FR merged; renumbered to CAP-297/REQ-YG-720.
