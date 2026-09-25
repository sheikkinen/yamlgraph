# FR-1088 authoring brief — repair `innovation_matrix/pipeline.yaml`

**Prior art:** `fr-853-task-shapes-brief.md` edited only the `description` of
`innovation_matrix/graph.yaml`, the single-node variant; this brief does not
touch that file. `fr-890-research-route-brief.md` names the demo as prior art
only. No earlier brief covers `pipeline.yaml`.

## Task

`pipeline.yaml` drops `--var domain=…`, assumes a 5 × 5 grid, and its
synthesis claims "25" cells it never checks. Declare the input, bound the
grid in the dimensions schema, and make the synthesis render every cell by
its map index. Nothing else.

## Artifact boundary

Edited by this authoring run (YAML only):

1. `examples/demos/innovation_matrix/pipeline.yaml`
   - Add `state:` with `domain: str`.
   - `synthesize.variables` gains `pairs: "{state.pairs}"`.
   - `expand_all.max_items: 25` stays a literal int. It is the only `25`
     left in the file.
   - `description` (L3) and the `cartesian_product` tool `description`
     (L12) become count-free.
2. `examples/demos/innovation_matrix/prompts/generate_dimensions.yaml`
   - `capabilities` and `constraints` each get
     `constraints: {min_length: 3, max_length: 5}`.
   - Field descriptions and the task prose say "3 to 5", not "5" or
     "exactly 5"; the `C1-C5` / `S1-S5` headings become count-free.
3. `examples/demos/innovation_matrix/prompts/synthesize.yaml`
   - Contains no literal `25`.
   - States `{{ expansions | length }} of {{ pairs | length }} cells`.
   - Iterates `pairs` in list order. For the pair at zero-based position
     `i`, select the `expansions` rows whose `_map_index == i`:
     one row → render the pair's `id`, `capability`, `constraint` and the
     row's `value`; no row → render the pair's `id`, `capability`,
     `constraint` and `MISSING`; more than one row → render
     `DUPLICATE` for that pair and no value.
   - `top_ideas` asks for each idea's cell ID.

Read-only for this run, changed on the same branch under RED/GREEN commits:

- `examples/demos/innovation_matrix/nodes/cartesian.py` — IDs
  `C{i // len(constraints) + 1}S{i % len(constraints) + 1}`; `ValueError`
  naming both lengths when either list is empty; count-free docstrings.
- `tests/unit/test_fr1088_innovation_matrix_repair.py` — the focused
  witnesses (FR-1088 AC-01 to AC-05).

Produced after this run, not by it:

- `examples/demos/innovation_matrix/demo-output-pipeline.log` (FR-1088
  AC-09).
- The local report `tmp/draft-authoring-report.md` (not committed).

Do not touch `graph.yaml`, `drill-down.yaml`, `expand_cell.yaml`,
`select_cells.yaml`, `generate_matrix.yaml`, `demo-output.log`, or anything
under `yamlgraph/`.

## Precedent

List bounds in a prompt schema:
`examples/demos/persona_scenarios/prompts/analyze_product.yaml#L8-L13`
(`min_length` / `max_length` on a generated `list[str]` that a map later fans
out over). `yamlgraph/schema_loader.py#L153-L155` passes `constraints` into the
Pydantic `Field`. An expansion row from this map is
`{"_map_index": i, "value": <text>}` because `expand_cell` has no schema
(`yamlgraph/compile/map_compiler.py#L194-L199`).

## Validation

- Lint: `yamlgraph graph lint examples/demos/innovation_matrix/pipeline.yaml`
  — 0 errors, no E007 for `domain`.
- Deterministic smoke (no provider): render `synthesize.yaml` with 12 pairs
  (4 × 3) and three expansion sets — all 12 indices; index 7 absent; index 7
  twice. Expected: every ID shown in all three; `11 of 12` and only `C3S2`
  `MISSING` in the second; `C3S2` `DUPLICATE` with neither duplicate value in
  the third. Record the exact command used.
- Not part of this run: the live provider run is FR-1088 AC-09, limited to
  the unconsumed FR-1073 H-4 rerun:
  `LLM_REQUEST_TIMEOUT=120 yamlgraph graph run examples/demos/innovation_matrix/pipeline.yaml --var domain=@examples/demos/innovation_matrix/domain-brief.md --full`.
  Do not run it here. Record it under `Blocked validation` as "spend held
  for FR-1088 AC-09".

## Governing FR

`feature-requests/FR-1088-innovation-matrix-repair.md` and its judgement
`feature-requests/FR-1088-innovation-matrix-repair.judgement.md` (R-1, R-2;
gates C-3, C-4, C-5).
