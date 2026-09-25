# Judgement: FR-1087 Repair the safety-guards demo so it compiles and routes as documented

**Prior art:** `FR-1087-safety-guards-demo-repair.md` is the FR judged here; FR-1069 (Rejected) is its predecessor, dispositioned in the FR.

**Verdict:** APPROVED WITH REVISIONS — the scalar-edge repair is the minimal correct contrib/example fix; authority activates only after the FR names its committed authoring brief, freezes W803 handling to documentation, and replaces the stochastic route claim with a deterministic loop-path witness.

**Reviewed against:** `feature-requests/FR-1087-safety-guards-demo-repair.md`; `feature-requests/FR-1069-lint-builds-graph.md`; `feature-requests/FR-1069-lint-builds-graph.judgement.md`; `feature-requests/FR-1086-lint-compile-check.md`; `feature-requests/027-execution-safety-guards.md`; `feature-requests/FR-718-edge-compiler-decomposition.md`; `feature-requests/FR-234-parallel-fan-out-edges.md`; `examples/demos/safety-guards/graph.yaml`; `examples/demos/safety-guards/README.md`; `examples/demos/safety-guards/prompts/review.yaml`; `yamlgraph/compile/edge_compiler.py`; `.github/skills/graph-authoring/doctrine.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md`.

## What is sound

The defect is real and localized: the demo declares a condition on a fan-out list (`examples/demos/safety-guards/graph.yaml:80-87`), while the compiler rejects exactly that shape and directs authors to split it into conditional edges (`yamlgraph/compile/edge_compiler.py:35-43,91-93`). Replacing only `[revise, expand]` with `revise` preserves the documented cycle and existing high-score edge; scalar conditioned edges use the expression path, including resolution of a map target through its fan-out (`yamlgraph/compile/edge_compiler.py:53-70,256-261,417-425`).

The FR honors the FR-1069 split by excluding lint implementation (`feature-requests/FR-1087-safety-guards-demo-repair.md:22-27,131-137`) and supplies substantive research: four exhaustive edge-shape solution classes, preserved dissent, precedent, and an explicit `is_this_a_graph` answer (`feature-requests/FR-1087-safety-guards-demo-repair.md:110-129`). Scope is otherwise small and feasible through the existing authoring route. Strategic classification: **contrib/example** — one broken demo is repaired using existing compiler abstractions; no framework primitive is authorized.

## Required revisions

### R-1: Name and require the committed authoring brief

Add `feature-requests/authoring-briefs/fr-1087-safety-guards-demo-repair-brief.md` to the Proposed Solution, deliverables, and acceptance criteria, and require the FR to cite that exact path before `scripts/author.sh` runs. The current generic "`<brief>`" reference (`feature-requests/FR-1087-safety-guards-demo-repair.md:75-80`) does not satisfy the cited doctrine's artifact-closure rule that FR-bound briefs are committed under `feature-requests/authoring-briefs/` and cited by the governing FR (`.github/skills/graph-authoring/doctrine.md:21-31`).

### R-2: Freeze W803 handling to an honest README correction

Delete "either close it or state it in the README" and "plus any W803 change the report justifies" (`feature-requests/FR-1087-safety-guards-demo-repair.md:87-90,100-101`). Authorize no graph change for W803. Require the README to retract "should pass clean" (`examples/demos/safety-guards/README.md:8-10`) and state that lint reports W803 when the optional Z3 condition-gap check is available; require the report to record the exact observed lint output and whether that optional check was available. This keeps the Summary's one-edge promise (`feature-requests/FR-1087-safety-guards-demo-repair.md:38-43`) internally consistent and prevents an adjacent routing-policy change from entering through a warning exception.

### R-3: Prove the repaired branch deterministically

Add `tests/unit/test_safety_guards_demo.py` as a deliverable. Its graph execution witness must supply deterministic structured review results with a low score followed by a high score and assert the visit sequence `draft, review, revise, review, expand`; `revise` runs once, `expand` runs once, and `expand` starts only after the final `review`. Keep the documented CLI smoke as a separate real-run attempt recorded in the authoring report. A single unconstrained LLM smoke (`feature-requests/FR-1087-safety-guards-demo-repair.md:91-104`) can take the high-score edge immediately and never exercise the repaired low-score edge, so it cannot by itself prove FR-1069 judgement AC-04.

### R-4: Remove the sibling-dependent acceptance clause and name completion evidence

Make this FR independently enforceable: remove the future "`graph lint --build` after FR-1086 lands" clause from AC-01 (`feature-requests/FR-1087-safety-guards-demo-repair.md:96-99`). Replace the shorthand AC-06 with mechanically checkable evidence: one `changelog/unreleased/` fragment naming FR-1087, an implementation record and completed status in this FR, and a `docs/diary/` entry naming FR-1087 and containing `Seed:`.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/authoring-briefs/fr-1087-safety-guards-demo-repair-brief.md` |
| D-2 | `examples/demos/safety-guards/graph.yaml` — low-score edge target only |
| D-3 | `examples/demos/safety-guards/README.md` — lint expectation only |
| D-4 | `tests/unit/test_safety_guards_demo.py` — deterministic compile and route witness |
| D-5 | `tmp/draft-authoring-report.md` — authoring-route validation record |
| D-6 | FR-1087 implementation record, one FR-1087 changelog fragment, and one FR-1087 diary entry |

Not authorized: changes to linter behavior or FR-1086; compiler, runtime, loop-limit, state-schema, or prompt changes; a W803 fallback edge or other W803 graph repair; edits to any other graph or demo; dependency additions; or changes to the documented safety-feature set.

## Revised acceptance criteria

- [ ] AC-01: `feature-requests/authoring-briefs/fr-1087-safety-guards-demo-repair-brief.md` is committed, cited by FR-1087, names the frozen artifact boundary, and is the task passed to `scripts/author.sh`.
- [ ] AC-02: the complete `graph.yaml` diff changes only `to: [revise, expand]` to `to: revise` on the `review.score < 0.8` edge.
- [ ] AC-03: the authoring report records the exact command and successful outcome for `load_graph_config` + `compile_graph` + `.compile()` on `examples/demos/safety-guards/graph.yaml`.
- [ ] AC-04: `tests/unit/test_safety_guards_demo.py` deterministically drives review scores below and then at or above `0.8` and asserts the exact node sequence `draft, review, revise, review, expand`.
- [ ] AC-05: the same deterministic witness asserts `revise` runs once, `expand` runs exactly once, and no `expand` visit precedes the last `review`.
- [ ] AC-06: the authoring report records the exact lint command and output, identifies whether the optional Z3 check was available, and the README no longer promises a clean lint; it documents W803 when that check is available.
- [ ] AC-07: the documented CLI run is attempted with the README variables and its exact command, node sequence, and outcome are recorded; if credentials or a dependency block it, the report records the exact blocker and does not claim success.
- [ ] AC-08: `tmp/draft-authoring-report.md` contains the required `Artifacts`, `Precedent`, `Validation`, `Repairs`, and `Blocked validation` headings and identifies the FR-1087 brief and authored paths.
- [ ] AC-09: one `changelog/unreleased/` fragment names FR-1087; FR-1087 records implementation decisions and completed status; one `docs/diary/` entry names FR-1087 and contains `Seed:`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 into FR-1087 before implementation begins. | GATE |
| C-2 | All `graph.yaml` work must occur inside the sole authoring execution launched with the committed FR-1087 brief; direct graph edits are forbidden. | GATE |
| C-3 | The graph diff is exactly the scalar low-score target change; W803 receives documentation only. | GATE |
| C-4 | Do not substitute an uncontrolled live LLM run for the deterministic low-score/high-score route witness. | GATE |
| C-5 | Do not modify lint, compiler, runtime, loop-limit semantics, state schema, prompts, dependencies, or other demos under FR-1087. | GATE |

Authority granted: after R-1 through R-4 are folded into FR-1087, implement the frozen safety-guards demo repair and its deterministic validation evidence through the committed authoring brief.
