# Feature Request: Repair `innovation_matrix` — declared input, schema-bounded grid, every cell ID in the synthesis

**Priority:** MEDIUM
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS ([judgement](FR-1088-innovation-matrix-repair.judgement.md)); R-1–R-3 folded 2026-09-26. Authority active (2026-09-26): human review recorded — operator instruction 'proceed with all fr changes' (2026-09-26). Not implemented; lands after FR-1073 is merged (judgement C-2).
**Effort:** 0.5 days
**Requested:** 2026-09-25
**First consumer / first event:** the next
`yamlgraph graph run examples/demos/innovation_matrix/pipeline.yaml --var domain=@brief.md`.
On 2026-09-24 the brief never reached state, every cell was domain-free, and
`synthesize` ranked "top 5 of 25" from 21 results plus four error strings,
exit 0 ([docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §1.1, §1.2).
**Research:** FR-890 research route **skipped by operator decision
(2026-09-25: "refile. skip research — document as skipped")**. Substitute:
the in-body [Alternatives Considered](#alternatives-considered) section (six
solution classes, one chosen, one preserved dissent, each dispositioned,
plus the `is_this_a_graph` answer), in the form FR-1076 and FR-1079 use, and
the incident record [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md)
§1, §2 D5 and D9, §7 H.
**Prior art:**
[FR-1070](FR-1070-innovation-matrix-repair.md) (REJECTED). This FR is its
refile. How each judgement objection is answered:
- *R-1, research:* the operator skipped the research route; the substitute
  is the six-class table below, with precedent, dissent and a graph-fit
  answer.
- *R-2, grid bound:* FR-1070 asked for `max_items` to equal a product
  computed at run time. `compile_map_node` reads `max_items` as a plain
  config value and `resolve_items` compares it to the item count
  (`yamlgraph/compile/map_compiler.py#L328-L356`), and `NodeConfig` types it
  `int | None` (`yamlgraph/models/node_schema.py#L222-L224`). A state
  expression or a node return cannot occupy it. This FR keeps the static
  `max_items: 25` and bounds the grid where the model output enters: the
  dimension lists get `max_length: 5` in the prompt schema. A product above
  25 can then not be built. A dynamic cap is refused (class 3).
- *R-3, completeness:* this FR adds no failure handling of its own. It lands
  after [FR-1073](FR-1073-map-result-contract.md), under which this map
  (FR-1073 census row 25) is strict: a failed branch raises at the join and
  `synthesize` never runs. The synthesis prompt also receives every
  dispatched cell ID and marks any cell without an expansion as missing, so
  a reported count can never replace completeness (FR-1070 judgement C-2).
  The four literal "25"s get an exact post-authoring check (AC-06).
[FR-1073](FR-1073-map-result-contract.md) (authority active) owns the map
result and failure contract. This FR relies on it and does not change it.
Its H-4 authorized the provider spend for one `innovation_matrix` rerun
after FR-1073's deterministic acceptance, non-gating.
[FR-1079](FR-1079-retry-ownership.md) (Proposed) owns retries, including
the re-ask after an output validation failure (its item 5). A dimensions
response that breaks the new schema bound is such a failure. This FR sets
no `on_error` and no retry.
[FR-939](FR-939-map-overflow-policy.md) (APPROVED WITH REVISIONS, not
implemented) makes map overflow raise. It composes as a second line of
defence; this FR does not depend on it (class 6).
[FR-1067](FR-1067-reject-undeclared-cli-vars.md) (REJECTED) would make an
undeclared `--var` loud. This FR declares the variable instead; it does not
depend on FR-1067.
The demo's own `PORTING_PLAN.md` is not a proposal.

## Summary

Declare `domain` in `pipeline.yaml`'s `state:` block. Bound each dimension
list to at most five entries in the `generate_dimensions` schema, so the
grid never exceeds the map's static `max_items: 25`. Derive cell IDs from
the actual list lengths. Give `synthesize` every dispatched cell ID and the
real counts instead of the literal "25".

## Value Statement

A reader of the synthesis gets ideas about the domain they described, each
tied to a named cell, and the prompt never claims cells the run did not
produce.

## Problem

- **Input dropped (D5).** `pipeline.yaml` has no `state:` block, so
  `--var domain=…` never reaches state. `graph lint` reports E007 on
  `generate_dimensions` and `synthesize` (witnessed 2026-09-25 at
  `011317a8`). The map sub-node's `domain` variable
  (`pipeline.yaml#L34-L35`) is not reported, but it reads the same missing
  key.
- **Grid assumes 5 × 5 (D9).** Cell IDs use `i // 5` and `i % 5`
  (`nodes/cartesian.py#L33`). With any other constraint count the IDs are
  wrong. The only bound on list length is prose: "Return exactly 5
  capabilities and 5 constraints" (`prompts/generate_dimensions.yaml#L53`);
  the schema fields are plain `list[str]` (`#L8-L13`).
- **Cap truncates silently.** `max_items: 25` (`pipeline.yaml#L30`). A 5 × 6
  answer gives 30 pairs; `resolve_items` logs a warning and keeps the first 25
  (`map_compiler.py#L347-L356`).
- **Synthesis states a count it does not check.** `synthesize.yaml` says
  "25" at L3, L18, L27 and L43. It renders each expansion as-is
  (`#L29-L35`). `expand_cell` has no schema, so an expansion from this map
  is a dict holding `_map_index` and `value`
  (`map_compiler.py#L194-L199`), and the prompt sees no cell ID,
  capability or constraint.
- **Stale "25" elsewhere.** `pipeline.yaml#L3`, `#L12`;
  `nodes/cartesian.py#L3`, `#L10`.
- **Demo proof placement.** `demo-output.log` was produced by `graph.yaml`,
  the single-node variant (its run event names `…/innovation_matrix/graph.yaml`),
  not by `pipeline.yaml`.

## Ideal Result

For any grid the schema allows, the pairs, the IDs, the map cap and the
synthesis agree by construction. `synthesize` runs only when every
dispatched cell has an expansion (FR-1073), and it names every cell it was
given.

## Proposed Solution

All graph and prompt edits go through
`scripts/author.sh feature-requests/authoring-briefs/fr-1088-innovation-matrix-repair-brief.md`
([brief](authoring-briefs/fr-1088-innovation-matrix-repair-brief.md);
`.github/skills/graph-authoring/doctrine.md`, FR-767). The brief is the
artifact boundary: it names the three YAML files the run edits, the files
it only reads (`cartesian.py`, the focused test), the files produced after
it (`demo-output-pipeline.log`, the local authoring report), the
`persona_scenarios` precedent, the lint command, the deterministic render
smoke and the live command. The PreToolUse guard does not match the file
name `pipeline.yaml` (`.github/hooks/scripts/pre-command-guard.sh#L165-L173`),
so for that file the route is held by doctrine, not by the hook. A route
failure is not permission for a direct edit (judgement C-3). `cartesian.py`
is Python and changes under TDD on the same branch.

1. **State.** `pipeline.yaml` declares `domain: str` in a `state:` block.
2. **Bound at the model boundary.** In `prompts/generate_dimensions.yaml`,
   `capabilities` and `constraints` each get
   `constraints: {min_length: 3, max_length: 5}`. `schema_loader.py` passes
   these into the Pydantic `Field` (`yamlgraph/schema_loader.py#L153-L155`).
   Precedent: `examples/demos/persona_scenarios/prompts/analyze_product.yaml#L8-L13`.
   The floor of 3 keeps at least 9 cells for a "top 5" ranking (**H-1**).
3. **Static cap, pinned.** `max_items: 25` stays as a literal int, the only
   form `NodeConfig` accepts. A unit test in
   `tests/unit/test_fr1088_innovation_matrix_repair.py` reads both YAML
   files and asserts
   `max_length(capabilities) × max_length(constraints) == max_items`, so a
   later edit to one cannot drift from the other.
4. **IDs from lengths.** `cartesian.py` builds
   `C{i // n_constraints + 1}S{i % n_constraints + 1}` with
   `n_constraints = len(constraints)`. It knows no cap. It raises
   `ValueError`, naming both lengths, if either list is empty.
5. **Synthesis.** `synthesize` also receives `pairs`. The prompt:
   - states "{{ expansions | length }} of {{ pairs | length }} cells";
   - iterates `pairs` in list order and takes each pair's zero-based
     position as its expected `_map_index`;
   - selects the expansion rows whose `_map_index` equals that position;
   - with exactly one match, renders the pair's ID, capability,
     constraint and the row's `value`;
   - with no match, renders the pair's ID, capability, constraint and
     `MISSING`;
   - with more than one match, renders `DUPLICATE` for that pair and
     shows neither row's value;
   - contains no literal "25".
   Attribution is by `_map_index`, never by list position after filtering
   (judgement C-5).
   Under FR-1073's strict default the two counts are equal whenever
   `synthesize` runs. The `MISSING` marker is what keeps the prompt honest
   if a later edit adds `min_success` to this map.
6. **Stale text.** The "25" in `pipeline.yaml#L3`, `#L12` and the
   `cartesian.py` docstrings become count-free.
7. **Proof.** The pipeline run log is committed as
   `demo-output-pipeline.log`, next to the `graph.yaml` log it does not
   replace. The run's short domain text is committed as
   `examples/demos/innovation_matrix/domain-brief.md`, and the run uses
   `LLM_REQUEST_TIMEOUT=120` and `--full` (AC-09).

Ordering: lands after FR-1073 is merged. Without it, a failed branch still
reaches `synthesize` as a dict holding `_error`.

## Acceptance Criteria

From the judgement's revised criteria. Witness file:
`tests/unit/test_fr1088_innovation_matrix_repair.py`.

- [ ] AC-01: RED first: `cartesian_product` with four capabilities and
  three constraints returns 12 entries with unique ordered IDs `C1S1`
  through `C4S3`, and every entry carries the corresponding capability and
  constraint. Fails today (IDs use `// 5`).
- [ ] AC-02: The model built from `generate_dimensions.yaml` rejects six
  capabilities and two constraints with `ValidationError`, and accepts
  5-by-5 and 3-by-4 inputs.
- [ ] AC-03: A YAML pin test asserts
  `capabilities.max_length * constraints.max_length == expand_all.max_items`;
  changing only `max_items` to 24 in the test fixture makes the assertion
  fail.
- [ ] AC-04: `cartesian_product` with either dimension empty raises
  `ValueError`, and the asserted message values include both observed
  lengths.
- [ ] AC-05: Deterministic prompt rendering (no provider) joins pairs to
  expansions by zero-based `_map_index`, over 12 pairs (4 × 3):
  12 of 12 renders every ID with no `MISSING`; absent index 7 renders
  every ID, marks only `C3S2` `MISSING`, and states `11 of 12`; duplicate
  index 7 marks `C3S2` `DUPLICATE` and shows neither duplicate value,
  rather than selecting one row.
- [ ] AC-06: `synthesize.yaml` contains no literal `25`; `pipeline.yaml`
  contains `25` only as `expand_all.max_items`; count-bearing descriptions
  and Cartesian docstrings are count-free.
- [ ] AC-07: `yamlgraph graph lint examples/demos/innovation_matrix/pipeline.yaml`
  reports zero errors and no E007 finding for `domain`.
- [ ] AC-08: The committed
  [`fr-1088-innovation-matrix-repair-brief.md`](authoring-briefs/fr-1088-innovation-matrix-repair-brief.md)
  names the full artifact boundary and exact validations; running
  `scripts/author.sh feature-requests/authoring-briefs/fr-1088-innovation-matrix-repair-brief.md`
  produces a substantive local `tmp/draft-authoring-report.md` whose
  `Artifacts`, `Precedent`, `Validation`, `Repairs` and
  `Blocked validation` sections, and lint/smoke records, concern
  `pipeline.yaml`. The report stays uncommitted; its exact commands and
  outcomes are copied into this FR's implementation record.
- [ ] AC-09 (live, non-gating): after FR-1073 is merged and its
  deterministic acceptance passes, the one already authorized provider run
  (FR-1073 H-4) is
  `LLM_REQUEST_TIMEOUT=120 yamlgraph graph run examples/demos/innovation_matrix/pipeline.yaml --var domain=@examples/demos/innovation_matrix/domain-brief.md --full`.
  `demo-output-pipeline.log` records the command, one quoted
  domain-specific dimension, all pair IDs presented to synthesis, and the
  run outcome, without retrying a failed branch until it passes. If FR-1073
  H-4 has already been consumed, this criterion is recorded as blocked for
  lack of spend authority and does not authorize another run.
- [ ] AC-10: `capabilities/CAP-278-innovation-matrix-demo.yaml` defines
  `REQ-YG-693` and `fr: FR-1088`; the requirement states the full contract
  (declared `domain`, 3 to 5 entries per dimension, cap equals the schema
  product, dimension-derived unique IDs, index-grounded synthesis that
  renders every pair and marks missing expansions); every new test in
  `tests/unit/test_fr1088_innovation_matrix_repair.py` carries
  `@pytest.mark.req("REQ-YG-693")`; `ARCHITECTURE.md` is regenerated;
  `python scripts/req_coverage.py --strict` passes.
- [ ] AC-11: The focused deterministic test file passes, and RED and GREEN
  are separate commits; RED fails on the missing FR-1088 behavior, not on
  an import, missing fixture, malformed YAML, or unmerged FR-1073
  implementation.
- [ ] AC-12: `changelog/unreleased/fr-1088-innovation-matrix-repair.md`,
  this FR's implementation record, and one `docs/diary/` reflection with
  `Seed:` record the delivered repair and any honest validation limitation.
- [ ] AC-13: The implementation diff contains none of the not-authorized
  surfaces below.

REQ number: the judgement named `REQ-YG-690`. The highest REQ in
`capabilities/*.yaml` is `REQ-YG-692` (FR-1073, `CAP-11-subgraph-map.yaml`),
so this FR takes the next free number above it, `REQ-YG-693`; the
unused 690–691 gap is left to whoever reserved it. `CAP-278` is unclaimed
in `capabilities/` and in every FR.

## Alternatives Considered

Solution classes (chosen: 1; preserved dissent: 2):

1. **Schema bound at the model boundary, static cap pinned to it.**
   Chosen. The bound sits where model output enters (`the_one_law`), in
   YAML (Commandment 3), in a form the loader already supports
   (`schema_loader.py#L153-L155`) and another demo already uses. The cap
   stays a plain int. One test ties them. No framework change.
2. **Exactly 5 × 5: `min_length: 5, max_length: 5`.** Preserved dissent.
   It is the smallest change: the grid is fixed, `i // 5` stays correct, and
   "25" is true whenever FR-1073 lets `synthesize` run. It loses because a
   4-item answer, which the prompt cannot prevent, fails a paid run instead
   of yielding a valid 4 × 5 grid. It also keeps the ID math coupled to a
   constant that a prompt edit can break, which is the D9 defect itself.
3. **Dynamic cap: `max_items` from a state expression.** Rejected. It is a
   compiler change (`map_compiler.py#L328-L330` reads a config value) for
   one consumer, and a cap computed from the data it caps is no cost guard.
   FR-1070 judgement R-2 requires a separately judged contract for it.
4. **`cartesian` truncates or pads to 5 × 5.** Rejected: a silent fallback
   (Commandment 6). Truncation is the exact failure `resolve_items` has today.
5. **`cartesian` refuses above a Python constant.** Rejected. The refusal
   comes after the same paid `generate_dimensions` call as class 1, the
   bound lives in code instead of config, and the constant duplicates
   `max_items` without the schema's validation-feedback path (FR-1079
   item 5).
6. **Rely on FR-939 `on_overflow: error` alone.** Rejected as the only
   mechanism. FR-939 is not implemented (`map_compiler.py#L347-L356` still
   truncates). Even with it, a 5 × 6 grid would fail at dispatch instead of
   being bounded at the model output. It composes as a second line once it
   lands.

Precedent: `persona_scenarios` bounds a generated list with
`min_length`/`max_length` before its map fans out over it
(`analyze_product.yaml#L8-L13`).

`is_this_a_graph`: the demo is a graph, and it stays one. The fix is a
schema bound, deterministic ID math and a prompt render; no new LLM stage,
no new graph.

## Human decisions

- **H-1 (2026-09-25, operator):** floor of 3 entries per dimension
  (at least 9 cells for a top-5 ranking). The alternative, 5, was class 2.
- **H-2 (2026-09-25, operator):** AC-09 uses the one rerun FR-1073's H-4
  already authorized, sequenced after this FR also lands so one run
  witnesses both. No second paid run.
- **Review (2026-09-26, operator):** judgement and folded revisions
  reviewed; authority activated by the instruction "proceed with all fr
  changes".

## Scope (frozen by judgement)

Deliverables (judgement D-1–D-8):

| # | Surface |
|---|---|
| D-1 | This FR; [`authoring-briefs/fr-1088-innovation-matrix-repair-brief.md`](authoring-briefs/fr-1088-innovation-matrix-repair-brief.md) |
| D-2 | `examples/demos/innovation_matrix/pipeline.yaml`: `state.domain`, `pairs` to `synthesize`, literal `max_items: 25`, count-free descriptions |
| D-3 | `examples/demos/innovation_matrix/prompts/generate_dimensions.yaml` (bounds), `.../prompts/synthesize.yaml` (index join, no literal count) |
| D-4 | `examples/demos/innovation_matrix/nodes/cartesian.py`: IDs from lengths, empty-dimension refusal, count-free docstrings |
| D-5 | `tests/unit/test_fr1088_innovation_matrix_repair.py` |
| D-6 | `capabilities/CAP-278-innovation-matrix-demo.yaml` (`REQ-YG-693`), regenerated `ARCHITECTURE.md`, `changelog/unreleased/fr-1088-innovation-matrix-repair.md` |
| D-7 | Local `tmp/draft-authoring-report.md`; committed `examples/demos/innovation_matrix/demo-output-pipeline.log` and its input `examples/demos/innovation_matrix/domain-brief.md`; this FR's implementation record |
| D-8 | One `docs/diary/` reflection with `Seed:` |

Not authorized: changes to `yamlgraph/` runtime, compiler, schema loader,
executor, linter, CLI, hooks, authoring or judge doctrine; map result and
failure semantics (FR-1073); retry or timeout ownership (FR-1079, FR-708);
map overflow policy (FR-939); undeclared-variable policy (FR-1067);
`graph.yaml`, `drill-down.yaml`, `select_cells.yaml`,
`generate_matrix.yaml`; E007 coverage of map sub-node variables; a second
paid run; unrelated demo cleanup; any capability or architecture change
beyond CAP-278 and REQ-YG-693.

Enforcement conditions C-1–C-8 are in the
[judgement](FR-1088-innovation-matrix-repair.judgement.md#conditions-for-enforcement);
all are GATE.

## Related

- Refiles: [FR-1070](FR-1070-innovation-matrix-repair.md) ([judgement](FR-1070-innovation-matrix-repair.judgement.md))
- Authoring brief: [fr-1088-innovation-matrix-repair-brief.md](authoring-briefs/fr-1088-innovation-matrix-repair-brief.md)
- Depends on: [FR-1073](FR-1073-map-result-contract.md)
- Composes with: [FR-1079](FR-1079-retry-ownership.md), [FR-939](FR-939-map-overflow-policy.md)
- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §1, §2 D5, D9, §7 H
