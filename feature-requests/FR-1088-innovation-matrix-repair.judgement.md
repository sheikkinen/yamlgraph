# Judgement: FR-1088 Repair `innovation_matrix` — declared input, schema-bounded grid, every cell ID in the synthesis

**Prior art:** `FR-1088-innovation-matrix-repair.md` is the FR judged here; FR-1070 (Rejected) is its predecessor, dispositioned in the FR.

**Verdict:** APPROVED WITH REVISIONS — the refile now has a supported, boundary-local repair for the witnessed demo defects; authority activates only after the committed authoring brief, exact index join, and traceability surfaces in R-1 through R-3 are folded into the FR.

**Reviewed against:** `feature-requests/FR-1088-innovation-matrix-repair.md`; `docs/issues-2026-09-24.md`; `feature-requests/FR-1070-innovation-matrix-repair.md`; `feature-requests/FR-1070-innovation-matrix-repair.judgement.md`; `feature-requests/FR-1073-map-result-contract.md`; `feature-requests/FR-1073-map-result-contract.judgement.md`; `feature-requests/FR-1079-retry-ownership.md`; `feature-requests/FR-939-map-overflow-policy.md`; `feature-requests/FR-939-map-overflow-policy.judgement.md`; `feature-requests/FR-1067-reject-undeclared-cli-vars.md`; `examples/demos/innovation_matrix/pipeline.yaml`; `examples/demos/innovation_matrix/nodes/cartesian.py`; `examples/demos/innovation_matrix/prompts/generate_dimensions.yaml`; `examples/demos/innovation_matrix/prompts/synthesize.yaml`; `examples/demos/persona_scenarios/prompts/analyze_product.yaml`; `yamlgraph/schema_loader.py`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/models/node_schema.py`; `yamlgraph/executor_base.py`; `.github/hooks/scripts/pre-command-guard.sh`; `.github/skills/graph-authoring/doctrine.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

**Scope and single responsibility.** This is one contrib/example repair: declare one dropped input, constrain the two model-produced dimensions, derive IDs from actual dimensions, and make the existing synthesis truthful (`feature-requests/FR-1088-innovation-matrix-repair.md:59-65,107-145`). It does not change the map compiler, retry ownership, overflow policy, CLI variable policy, or sibling demo graphs (`feature-requests/FR-1088-innovation-matrix-repair.md:233-239`). Those exclusions keep the repair smaller than the framework changes rejected or deferred in FR-1070, FR-939, FR-1079, and FR-1067.

**Consistency.** The summary, ideal result, solution, and criteria now agree on a schema-bounded 3-to-5 by 3-to-5 grid with a static cap of 25 (`feature-requests/FR-1088-innovation-matrix-repair.md:61-65,100-105,117-140,152-167`). The human has selected the floor of three and authorized reuse of FR-1073's single live rerun (`feature-requests/FR-1088-innovation-matrix-repair.md:6`). The dependency is explicit: FR-1088 lands after FR-1073, whose strict row 25 prevents synthesis after a non-tolerated branch failure (`feature-requests/FR-1088-innovation-matrix-repair.md:36-46,147-148`; `feature-requests/FR-1073-map-result-contract.md:276,332-356`).

**Measurability and testability.** AC-01 through AC-07 directly witness the present defects: non-square IDs, schema limits, cap/schema drift, empty dimensions, missing-index rendering, stale literals, and E007 (`feature-requests/FR-1088-innovation-matrix-repair.md:152-169`). These can fail on current behavior rather than on an absent fixture: the current ID calculation divides and takes modulo by five (`examples/demos/innovation_matrix/nodes/cartesian.py:29-37`), both dimension fields are unconstrained lists (`examples/demos/innovation_matrix/prompts/generate_dimensions.yaml:5-13`), `domain` is referenced but undeclared (`examples/demos/innovation_matrix/pipeline.yaml:14-19`), and synthesis contains four literal count claims (`examples/demos/innovation_matrix/prompts/synthesize.yaml:1-43`).

**Feasibility and architecture alignment.** The selected fix uses existing seams rather than inventing a runtime feature. Schema constraints are already passed into Pydantic `Field` (`yamlgraph/schema_loader.py:145-159`), and the cited `persona_scenarios` prompt already uses `min_length` and `max_length` on a generated list (`examples/demos/persona_scenarios/prompts/analyze_product.yaml:5-14`). Keeping `max_items: 25` is compatible with its `int | None` schema (`yamlgraph/models/node_schema.py:221-224`) and avoids the unsupported dynamic-cap proposal rejected in FR-1070. The cap pin prevents the current truncate-and-succeed path (`yamlgraph/compile/map_compiler.py:350-361`) from becoming reachable for any schema-valid dimension response.

**Research and prior art.** The in-body substitute satisfies the local research substance gate: six materially different mechanisms are dispositioned, fixed 5-by-5 is preserved as dissent, existing prompt-schema precedent is named, and `is_this_a_graph` is answered (`feature-requests/FR-1088-innovation-matrix-repair.md:184-222`; `.github/skills/judge-fr/doctrine.md:118-130`). The rejected FR-1070 is not merely cited; each of its research, supported-cap, and semantic-completeness objections is answered (`feature-requests/FR-1088-innovation-matrix-repair.md:21-42`). The incident evidence establishes a real problem: the domain was dropped, four branches were rendered as error content, and the synthesis still claimed completeness (`docs/issues-2026-09-24.md:45-88`).

**Strategic classification.** This is a **contrib/example** repair. It has one named consumer and uses existing state, prompt-schema, Python-tool, map, and Jinja facilities. No new framework abstraction is justified or authorized.

## Required revisions

### R-1: Commit and cite the artifact-closed authoring brief

Add `feature-requests/authoring-briefs/fr-1088-innovation-matrix-repair-brief.md` and cite that exact path in the FR's Proposed Solution and acceptance criteria. The brief must name the complete artifact boundary: `pipeline.yaml`, `prompts/generate_dimensions.yaml`, `prompts/synthesize.yaml`, `nodes/cartesian.py`, the focused test file, `demo-output-pipeline.log`, and the authoring report. It must state the existing `persona_scenarios` constraint pattern, the exact lint command, the deterministic prompt-render smoke, and the authorized live pipeline command. This is mandatory input closure, not optional process prose: FR-bound briefs must be committed and cited by their governing FR (`.github/skills/graph-authoring/doctrine.md:19-30`).

Amend AC-08 to assert that this committed brief exists and that `scripts/author.sh feature-requests/authoring-briefs/fr-1088-innovation-matrix-repair-brief.md` produces a substantive `tmp/draft-authoring-report.md` with `Artifacts`, `Precedent`, `Validation`, `Repairs`, and `Blocked validation`, all referring to this pipeline (`.github/skills/graph-authoring/doctrine.md:61-75,92-108`). The local report remains uncommitted; copy its exact commands and outcomes into the FR implementation record.

### R-2: Specify the synthesis join and its observable live witness

Replace “looked up by `_map_index`” with the exact render contract:

- iterate `pairs` in list order and use the pair's zero-based position as the expected `_map_index`;
- select expansion rows whose `_map_index` equals that position;
- render the pair ID, capability, constraint, and the matched expansion's `value` when exactly one row matches;
- render `MISSING` when no row matches;
- fail the deterministic render test if more than one row has the same `_map_index`.

Fold this contract into AC-05 with three fixtures: complete 12-of-12, missing index 7, and duplicate index 7. The missing fixture must render all 12 pair IDs, mark only `C3S2` missing, and state `11 of 12`; the duplicate fixture must fail rather than silently choose a row. This pins the semantic join that makes “every cell ID” true and prevents a plausible but misattributed synthesis.

Amend AC-09 to name the exact live invocation, including `--full`, so the committed record can expose the domain-bound dimensions, `pairs`, indexed expansions, and final synthesis:

`LLM_REQUEST_TIMEOUT=<explicit-seconds> yamlgraph graph run examples/demos/innovation_matrix/pipeline.yaml --var domain=@<committed-short-brief> --full`

The implementation record must identify the timeout value and committed short-domain brief path. The run remains non-gating and consumes only the already authorized FR-1073 H-4 rerun; if that authorization has already been spent before FR-1088 enforcement, no second run is authorized by this judgement.

### R-3: Name the requirement and capability artifacts

Replace AC-10's unbound “new REQ ID” with `capabilities/CAP-278-innovation-matrix-demo.yaml` and `REQ-YG-690`. The capability requirement must state the full observable contract: declared `domain`, 3-to-5 entries per dimension, cap/schema product equality, dimension-derived unique IDs, and index-grounded synthesis that renders every pair and marks missing expansions. Add `fr: FR-1088`, map every new test to `REQ-YG-690`, regenerate `ARCHITECTURE.md`, and require `python scripts/req_coverage.py --strict` to pass. Name the focused witness file `tests/unit/test_fr1088_innovation_matrix_repair.py` and the changelog fragment `changelog/unreleased/fr-1088-innovation-matrix-repair.md`.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised plan and closed authoring input: `feature-requests/FR-1088-innovation-matrix-repair.md`, `feature-requests/authoring-briefs/fr-1088-innovation-matrix-repair-brief.md` |
| D-2 | Declared input, `pairs` synthesis binding, retained literal cap, and count-free descriptions: `examples/demos/innovation_matrix/pipeline.yaml` |
| D-3 | Schema bounds and index-grounded truthful synthesis: `examples/demos/innovation_matrix/prompts/generate_dimensions.yaml`, `examples/demos/innovation_matrix/prompts/synthesize.yaml` |
| D-4 | Dimension-derived IDs, empty-dimension refusal, and count-free docstrings: `examples/demos/innovation_matrix/nodes/cartesian.py` |
| D-5 | Deterministic RED/GREEN witnesses: `tests/unit/test_fr1088_innovation_matrix_repair.py` |
| D-6 | Traceability and release record: `capabilities/CAP-278-innovation-matrix-demo.yaml`, generated `ARCHITECTURE.md`, `changelog/unreleased/fr-1088-innovation-matrix-repair.md` |
| D-7 | Validation evidence: local `tmp/draft-authoring-report.md`, committed `examples/demos/innovation_matrix/demo-output-pipeline.log`, FR implementation record |
| D-8 | Metacognitive record: one `docs/diary/` reflection with a literal `Seed:` |

Not authorized: changes to `yamlgraph/` runtime, compiler, schema-loader, executor, linter, CLI, hooks, authoring or judge doctrine; map result/failure semantics; retry or timeout ownership; map overflow policy; undeclared-variable policy; `graph.yaml`, `drill-down.yaml`, `select_cells.yaml`, or `generate_matrix.yaml`; a second paid rerun; unrelated demo cleanup; or any generated capability/architecture change beyond CAP-278 and REQ-YG-690.

## Revised acceptance criteria

- [ ] AC-01: RED first: `cartesian_product` with four capabilities and three constraints returns 12 entries with unique ordered IDs `C1S1` through `C4S3`, and every entry carries the corresponding capability and constraint.
- [ ] AC-02: The model built from `generate_dimensions.yaml` rejects six capabilities and two constraints with `ValidationError`, and accepts 5-by-5 and 3-by-4 inputs.
- [ ] AC-03: A YAML pin test asserts `capabilities.max_length * constraints.max_length == expand_all.max_items`; changing only `max_items` to 24 in the test fixture makes the assertion fail.
- [ ] AC-04: `cartesian_product` with either dimension empty raises `ValueError`, and the asserted message values include both observed lengths.
- [ ] AC-05: Deterministic prompt rendering joins pairs to expansions by zero-based `_map_index`: complete 12-of-12 renders every ID with no `MISSING`; absent index 7 renders every ID, marks only `C3S2` `MISSING`, and states `11 of 12`; duplicate index 7 fails the witness rather than selecting one row.
- [ ] AC-06: `synthesize.yaml` contains no literal `25`; `pipeline.yaml` contains `25` only as `expand_all.max_items`; count-bearing descriptions and Cartesian docstrings are count-free.
- [ ] AC-07: `yamlgraph graph lint examples/demos/innovation_matrix/pipeline.yaml` reports zero errors and no E007 finding for `domain`.
- [ ] AC-08: The committed `feature-requests/authoring-briefs/fr-1088-innovation-matrix-repair-brief.md` names the full artifact boundary and exact validations; running `scripts/author.sh` with that brief produces a substantive local `tmp/draft-authoring-report.md` whose required sections and lint/smoke records concern `pipeline.yaml`; exact report commands and outcomes are copied into the FR implementation record.
- [ ] AC-09: After FR-1073 is merged and its deterministic acceptance passes, the one already authorized non-gating provider run uses an explicit `LLM_REQUEST_TIMEOUT`, the committed short-domain brief, and `--full`. `demo-output-pipeline.log` records the command, one quoted domain-specific dimension, all pair IDs presented to synthesis, and the run outcome without retrying a failed branch until it passes. If FR-1073 H-4 has already been consumed, this criterion is recorded as blocked for lack of spend authority and does not authorize another run.
- [ ] AC-10: `capabilities/CAP-278-innovation-matrix-demo.yaml` defines `REQ-YG-690` and `fr: FR-1088`; every new test in `tests/unit/test_fr1088_innovation_matrix_repair.py` carries `@pytest.mark.req("REQ-YG-690")`; `ARCHITECTURE.md` is regenerated; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-11: The focused deterministic test file passes, and RED and GREEN are separate commits; RED fails on the missing FR-1088 behavior, not on an import, missing fixture, malformed YAML, or unmerged FR-1073 implementation.
- [ ] AC-12: `changelog/unreleased/fr-1088-innovation-matrix-repair.md`, the FR implementation record, and one diary reflection with `Seed:` record the delivered repair and any honest validation limitation.
- [ ] AC-13: The implementation diff contains none of the not-authorized surfaces.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No implementation authority exists until R-1 through R-3 are folded into FR-1088 and the committed authoring brief exists. | GATE |
| C-2 | FR-1088 lands only after FR-1073 is merged; do not emulate or duplicate its result, failure, accounting, or strict-join contract in this demo. | GATE |
| C-3 | All `pipeline.yaml` and prompt YAML edits run through the sole authoring route with the committed FR-1088 brief; route failure is not permission for a direct edit. | GATE |
| C-4 | The schema bound is enforced where model output enters, and the static cap remains 25; no dynamic cap, compiler change, truncation, padding, or Python-side duplicate cap is authorized. | GATE |
| C-5 | Synthesis attribution is by `_map_index`, not list position after filtering; missing and duplicate-index fixtures must prove the join cannot silently misattribute content. | GATE |
| C-6 | The paid run is non-gating and limited to the unconsumed FR-1073 H-4 authorization; record failure honestly and do not retry to manufacture a passing artifact. | GATE |
| C-7 | Preserve the explicit out-of-scope boundary: no runtime, compiler, retry, timeout, overflow, CLI, linter, hook, doctrine, or sibling-demo changes. | GATE |
| C-8 | Commit a genuine failing RED witness before production changes, then commit GREEN separately. | GATE |

Authority granted: after R-1 through R-3 are folded, implement only the frozen `innovation_matrix` pipeline, prompt, Cartesian-tool, focused-test, traceability, validation, changelog, implementation-record, and diary surfaces listed above.
