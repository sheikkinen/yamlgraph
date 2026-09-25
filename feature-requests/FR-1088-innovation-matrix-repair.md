# Feature Request: Repair `innovation_matrix` — declared input, schema-bounded grid, every cell ID in the synthesis

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Human decision (2026-09-25, operator):** H-1 floor of 3 entries per dimension accepted; H-2 AC-09 uses the rerun FR-1073's H-4 already authorized.
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
  computed at run time. `map_edge` reads `max_items` as a plain config
  value and compares it to the item count
  (`yamlgraph/compile/map_compiler.py#L351-L361`), and `NodeConfig` types it
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
  answer gives 30 pairs; `map_edge` logs a warning and keeps the first 25
  (`map_compiler.py#L354-L361`).
- **Synthesis states a count it does not check.** `synthesize.yaml` says
  "25" at L3, L18, L27 and L43. It renders each expansion as-is
  (`#L29-L35`). An expansion from this map is a dict holding `_map_index`
  and `value` (`map_compiler.py#L211-L215`, from source reading), so the
  prompt sees no cell ID, capability or constraint.
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

All graph and prompt edits go through `scripts/author.sh` with a committed
brief under `feature-requests/authoring-briefs/`
(`.github/skills/graph-authoring/doctrine.md`, FR-767). The PreToolUse guard
does not match the file name `pipeline.yaml`
(`.github/hooks/scripts/pre-command-guard.sh#L165-L173`), so for that file
the route is held by doctrine, not by the hook. `cartesian.py` is Python and
changes under TDD on the same branch.

1. **State.** `pipeline.yaml` declares `domain: str` in a `state:` block.
2. **Bound at the model boundary.** In `prompts/generate_dimensions.yaml`,
   `capabilities` and `constraints` each get
   `constraints: {min_length: 3, max_length: 5}`. `schema_loader.py` passes
   these into the Pydantic `Field` (`yamlgraph/schema_loader.py#L153-L155`).
   Precedent: `examples/demos/persona_scenarios/prompts/analyze_product.yaml#L8-L13`.
   The floor of 3 keeps at least 9 cells for a "top 5" ranking (**H-1**).
3. **Static cap, pinned.** `max_items: 25` stays as a literal int, the only
   form `NodeConfig` accepts. A unit test reads both YAML files and asserts
   `max_length(capabilities) × max_length(constraints) == max_items`, so a
   later edit to one cannot drift from the other.
4. **IDs from lengths.** `cartesian.py` builds
   `C{i // n_constraints + 1}S{i % n_constraints + 1}` with
   `n_constraints = len(constraints)`. It knows no cap. It raises
   `ValueError`, naming both lengths, if either list is empty.
5. **Synthesis.** `synthesize` also receives `pairs`. The prompt:
   - states "{{ expansions | length }} of {{ pairs | length }} cells";
   - lists every pair's ID, capability and constraint, with its expansion
     looked up by `_map_index`;
   - marks a pair with no expansion as `MISSING`;
   - contains no literal "25".
   Under FR-1073's strict default the two counts are equal whenever
   `synthesize` runs. The `MISSING` marker is what keeps the prompt honest
   if a later edit adds `min_success` to this map.
6. **Stale text.** The "25" in `pipeline.yaml#L3`, `#L12` and the
   `cartesian.py` docstrings become count-free.
7. **Proof.** The pipeline run log is committed as
   `demo-output-pipeline.log`, next to the `graph.yaml` log it does not
   replace.

Ordering: lands after FR-1073 is merged. Without it, a failed branch still
reaches `synthesize` as a dict holding `_error`.

## Acceptance Criteria

- [ ] AC-01 (RED): `cartesian_product` with 4 capabilities × 3 constraints
  returns 12 pairs with unique IDs `C1S1 … C4S3`, each carrying its own
  capability and constraint. Fails today (IDs use `// 5`).
- [ ] AC-02 (RED): the model built from `generate_dimensions.yaml`'s schema
  rejects 6 capabilities and rejects 2 constraints with a `ValidationError`;
  it accepts 5 × 5 and 3 × 4. An above-cap grid is therefore refused before
  `cartesian` and before any `Send`.
- [ ] AC-03: the pin test from item 3 passes, and fails when
  `max_items` is edited to 24 in a temporary copy.
- [ ] AC-04: `cartesian_product` with an empty list raises `ValueError`
  naming both lengths.
- [ ] AC-05: rendering `synthesize.yaml` with 12 pairs and 11 expansions
  (index 7 absent) shows all 12 IDs, marks `C3S2` as `MISSING`, and states
  "11 of 12". With 12 of 12 no `MISSING` appears. Deterministic, no provider.
- [ ] AC-06: after authoring, `synthesize.yaml` contains no `25`;
  `pipeline.yaml` contains `25` only in `max_items`.
- [ ] AC-07: `yamlgraph graph lint examples/demos/innovation_matrix/pipeline.yaml`
  reports 0 errors; E007 no longer reports `domain`.
- [ ] AC-08: the authoring report from `scripts/author.sh` exists
  (`tmp/draft-authoring-report.md`), and its lint and smoke records are for
  `pipeline.yaml` itself.
- [ ] AC-09 (live, non-gating, needs spend: **H-2**): one run with a short
  `--var domain=@brief.md` and `LLM_REQUEST_TIMEOUT` set explicitly
  (FR-708). Read the raw output. Record one quoted dimension line that
  names the brief's domain, and the list of cell IDs `synthesize` received.
  Committed as `demo-output-pipeline.log`. If a branch fails, the run
  raises at FR-1073's join; that outcome is recorded as is, not retried
  until it passes.
- [ ] AC-10: new REQ ID on the new tests,
  `python scripts/req_coverage.py --strict` passes, a changelog fragment,
  this FR's implementation record, and a diary entry with a `Seed:`.

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
   compiler change (`map_compiler.py#L351-L353` reads a config value) for
   one consumer, and a cap computed from the data it caps is no cost guard.
   FR-1070 judgement R-2 requires a separately judged contract for it.
4. **`cartesian` truncates or pads to 5 × 5.** Rejected: a silent fallback
   (Commandment 6). Truncation is the exact failure `map_edge` has today.
5. **`cartesian` refuses above a Python constant.** Rejected. The refusal
   comes after the same paid `generate_dimensions` call as class 1, the
   bound lives in code instead of config, and the constant duplicates
   `max_items` without the schema's validation-feedback path (FR-1079
   item 5).
6. **Rely on FR-939 `on_overflow: error` alone.** Rejected as the only
   mechanism. FR-939 is not implemented (`map_compiler.py#L354-L361` still
   truncates). Even with it, a 5 × 6 grid would fail at dispatch instead of
   being bounded at the model output. It composes as a second line once it
   lands.

Precedent: `persona_scenarios` bounds a generated list with
`min_length`/`max_length` before its map fans out over it
(`analyze_product.yaml#L8-L13`).

`is_this_a_graph`: the demo is a graph, and it stays one. The fix is a
schema bound, deterministic ID math and a prompt render; no new LLM stage,
no new graph.

**Human decision needed:**
- **H-1:** the floor per dimension. Suggested default: 3 (at least 9 cells
  for a top-5 ranking). Alternative: 5, which is class 2.
- **H-2:** the AC-09 spend. FR-1073's H-4 authorized one rerun after
  FR-1073's own deterministic acceptance. Suggested default: sequence that
  one rerun after this FR also lands, so one run witnesses both FRs (and
  FR-1079's AC-08 if it is judged by then). If FR-1073's rerun happens
  first, AC-09 needs its own approval.

## Out of scope

Map result and failure channel (FR-1073). Retries and timeouts (FR-1079,
FR-708). Overflow policy (FR-939). Rejecting undeclared `--var` (FR-1067).
E007 missing the map sub-node's variables. `graph.yaml`, `drill-down.yaml`
and `select_cells.yaml`/`generate_matrix.yaml`. Editing the demo under this
FR before it is judged.

## Related

- Refiles: [FR-1070](FR-1070-innovation-matrix-repair.md) ([judgement](FR-1070-innovation-matrix-repair.judgement.md))
- Depends on: [FR-1073](FR-1073-map-result-contract.md)
- Composes with: [FR-1079](FR-1079-retry-ownership.md), [FR-939](FR-939-map-overflow-policy.md)
- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §1, §2 D5, D9, §7 H
