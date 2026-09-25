# Feature Request: Graph `variables:` keys become state fields, so their defaults reach state

**Priority:** LOW
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-09-25
**First consumer / first event:** the implementer of FR-1084 AC-06, whose
fixture passes `--var gv_only=x` for a graph `variables:` key that is not in
`state:`. Today `gv_only` is dropped whether it comes from `variables:` or
from `--var`. After this FR it is a state key and reaches state (see "Human
decision needed", item 1). The second event is the next graph author who
writes `variables:` and does not also copy the key into `state:`. No graph in
the repo does that today (census, Problem finding 5), because authors copy
every key by hand.
**Research:** FR-890 research route **skipped by operator decision
(2026-09-25)**: the standing decision for this batch is an in-body
dispositioned alternatives table, as FR-1084 did. Substitute: Alternatives
Considered below (six solution classes, one chosen, one preserved dissent,
each dispositioned, plus an `is_this_a_graph` answer); the FR-1084 runtime
probe of 2026-09-25
([FR-1084#L73-L89](FR-1084-reject-undeclared-cli-vars.md#L73-L89)); and a
grep census run on 2026-09-25 against this worktree (Problem, finding 5).
**Prior art:**
[FR-688](FR-688-cli-variables-injection.md) (Closed). Made the CLI merge
`variables:` into the initial state as the lowest layer. It did not add the
keys to the schema; its acceptance graph `genesis.yaml` passed only because
`premise_file` is also under `state:`
([genesis.yaml#L18-L26](../examples/novel_fandom/genesis.yaml#L18-L26)).
This FR makes FR-688's intent true for undeclared keys.
[FR-1084](FR-1084-reject-undeclared-cli-vars.md) (Proposed, sibling). Checks
user input (`--var`, `--var-file`) against the schema at the CLI. This FR
changes the schema itself, for graph-authored `variables:`. It moves one key
class from "refused" to "accepted" under FR-1084 (its AC-06); see "Human
decision needed", item 1.
[FR-1067](FR-1067-reject-undeclared-cli-vars.md) (REJECTED). FR-1084's
predecessor, refused for a missing research record. It did not touch
`variables:`; nothing here re-enters its territory.
[FR-686](FR-686-novel-fandom-agent-first-rewrite.md) and
[FR-689](FR-689-genesis-canon-consistency.md) (Judged). Added graph-tool
`default_variables`
([graph_loader.py#L246](../yamlgraph/compile/graph_loader.py#L246),
[graph_tool.py#L61-L65](../yamlgraph/tools/graph_tool.py#L61-L65)). The same
schema gap applies there; this FR fixes both paths with one change and does
not change the injection.
[FR-629](FR-629-data-files-glob-support.md) and FR-021 (no file in
`feature-requests/`; cited in code). Precedent for the fix: each
`data_files` key becomes an `Any` field
([state_builder.py#L201-L205](../yamlgraph/models/state_builder.py#L201-L205)).
[FR-955](FR-955-map-branch-input-projection.md) (Judged, APPROVED WITH
REVISIONS). Projects map `Send` payloads onto the effective
`build_state_class` field set. Adding `variables:` keys widens that set by
the same keys; FR-955 needs no change.
[FR-618](FR-618-lazy-reference-variables.md) (Judged). About node-level
`variables:` resolution, not the graph-level block; dismissed.
No REJECTED FR about graph-level `variables:` or `build_state_class` was
found (search of `feature-requests/` for `variables`, `state_builder`,
`build_state_class`, `default_variables`, and `Status: Rejected`).

## Summary

`build_state_class` adds each top-level `variables:` key as an `Any` field
when no other source has declared it. The linter's known-field set gets the
same keys. A `variables:` default then reaches state in the CLI and
graph-tool paths without being copied into `state:`.

## Value Statement

A graph author who declares a default under `variables:` gets that value in
state, as FR-688 promised, instead of a silent `None`.

## Problem

1. **Merge.** The CLI merges `variables:` under all other input layers
   ([graph_run_helpers.py#L129-L131](../yamlgraph/cli/graph_run_helpers.py#L129-L131)).
   The graph-tool path passes the child's `variables:` as defaults for the
   child invoke
   ([graph_loader.py#L246](../yamlgraph/compile/graph_loader.py#L246),
   [graph_tool.py#L61-L65](../yamlgraph/tools/graph_tool.py#L61-L65)).
2. **Schema.** `build_state_class` builds the state `TypedDict` from base
   fields, common input fields, `state:`, `data_files`, and node-derived keys.
   It never reads `variables:`
   ([state_builder.py#L174-L213](../yamlgraph/models/state_builder.py#L174-L213)).
   The graph schema model has no `variables` field either; it passes through
   `extra: allow`
   ([graph_schema.py#L85](../yamlgraph/models/graph_schema.py#L85),
   [#L113](../yamlgraph/models/graph_schema.py#L113)).
3. **Drop.** LangGraph drops input keys that are not in that schema. FR-1084's
   probe (2026-09-25) on a graph with `variables: {gv: …}`: `gv` is absent
   from `app.get_input_jsonschema()["properties"]` and from the `invoke`,
   `ainvoke` and `astream(stream_mode="values")` results
   ([FR-1084#L73-L89](FR-1084-reject-undeclared-cli-vars.md#L73-L89)). So
   finding 1's merge has no effect for any key not declared elsewhere.
4. **Lint mirrors the gap.** The E007 known-field set lists the same sources
   and also omits `variables:`
   ([checks_semantic.py#L115-L131](../yamlgraph/linter/checks_semantic.py#L115-L131)).
   A `{state.gv}` reference in a node's `variables`/`output`/`args`/
   `input_mapping` is reported as an undeclared field
   ([#L176-L194](../yamlgraph/linter/checks_semantic.py#L176-L194)). This is
   by code reading, not a run. It explains the census: lint pushes authors to
   copy each key into `state:`. Fixing only the schema would leave E007
   reporting a now-valid graph.
5. **Census** (grep, 2026-09-25, `^variables:` at column 0 in `*.yaml`/
   `*.yml`, excluding `tmp/`): 10 files, 11 keys, all under `examples/`
   (7 in `examples/novel_fandom/`, 3 in `examples/demos/`). A 2-space key
   match under each file's `state:` block finds all 11 keys declared there.
   So **0 of 10 graphs lose a key today**. Bound: this is exact for block-style
   YAML at column 0. It does not see flow-style or indented `variables:`
   blocks, test fixtures built as Python dicts, or graphs outside the repo.
6. **Other entries do not merge `variables:`.** `invoke_graph` passes the
   caller's dict unchanged
   ([graph_loader.py#L395-L417](../yamlgraph/compile/graph_loader.py#L395-L417)).
   `subgraph_nodes.py`, `bench_commands.py` and `observability/otel.py`
   (`run_graph_async`) contain no read of the graph-level `variables:` block
   (grep for `variables` / `default_variables`, 2026-09-25). Only the CLI and
   graph-tool paths apply these defaults.
7. **Side finding: descriptor-shaped values.** 2 of the 10 files use a
   descriptor dict instead of a value:
   `topic: {description, default}`
   ([image-that-speaks/graph.yaml#L27-L30](../examples/demos/image-that-speaks/graph.yaml#L27-L30))
   and `query: {description, example}`, `scope: {description, default}`
   ([research-agent/graph.yaml#L14-L20](../examples/demos/research-agent/graph.yaml#L14-L20)).
   No code reads `default` or `example` from a `variables:` entry (grep for
   `["default"]`, `get("default")`, `get("example")` in `yamlgraph/`: only
   `schema_loader.py`). So a run without `--var topic` puts the whole dict
   into `state.topic`, which is declared `str`
   ([#L42-L43](../examples/demos/image-that-speaks/graph.yaml#L42-L43)).
   This is a different defect (wrong value, not dropped key). See "Human
   decision needed", item 2.
8. **Docs.** [reference/graph-yaml.md](../reference/graph-yaml.md) does not
   document the graph-level `variables:` block. It is absent from File
   Structure ([#L5-L39](../reference/graph-yaml.md#L5-L39)) and from
   Top-Level Properties (which has `data_files` at
   [#L144](../reference/graph-yaml.md#L144)). The "Variable Templates"
   section ([#L1302-L1323](../reference/graph-yaml.md#L1302-L1323)) covers
   node-level `variables:` only.

## Ideal Result

A key written under a graph's top-level `variables:` is a state field of that
graph. Its value reaches state when no higher layer supplies one, in the CLI
and graph-tool paths, in sync, async and stream modes. Lint treats it as
declared. The reference documents the block. No author has to write the key
twice.

## Proposed Solution

1. **Schema.** In `build_state_class`, after the common input fields and
   before `state:`
   ([state_builder.py#L192-L199](../yamlgraph/models/state_builder.py#L192-L199)),
   add each key of `config.get("variables") or {}` as `Any`, only if the key
   is not already present. Effects:
   - `state:`, `data_files`, and node-derived keys still override, as today,
     so a declared type wins.
   - A `variables:` key that collides with a base field (`errors`,
     `messages`, …) or a common input (`topic: str`) keeps the existing
     type and reducer.
   - Type is `Any`, as for `data_files`. The `TypedDict` is not enforced at
     run time, and inferring a type from a YAML scalar would type `"3"` as
     `str`.
2. **Lint parity.** In `_build_known_state_fields`
   ([checks_semantic.py#L115-L131](../yamlgraph/linter/checks_semantic.py#L115-L131)),
   add the `variables:` keys. E007 then accepts `{state.gv}` and still
   reports `{state.typo}`.
3. **Docs.** Add a `### variables` entry under Top-Level Properties and one
   line in File Structure in `reference/graph-yaml.md`. It says: keys become
   state fields; values are defaults used as written; precedence is
   `variables:` < `data_files` < `--import-state` < `--var-file` < `--var`
   (FR-688); applied by `graph run` and graph tools, not by `invoke_graph`.

No change to the merge code, to FR-1084's check, or to `state_codegen.py`
(which already omits `data_files`; out of scope).

## Acceptance Criteria

All tests are deterministic, make no LLM call, and carry
`@pytest.mark.req("REQ-YG-024")` (Dynamic state class generation,
[CAP-07-state-persistence.yaml](../capabilities/CAP-07-state-persistence.yaml)).

- [ ] AC-01 (RED, committed failing first with `SKIP=pytest`, then GREEN in a
  separate commit): `build_state_class({"variables": {"gv": "x"}, "nodes": {}})`
  has `gv` in its annotations. Test in `tests/unit/test_state_builder.py`.
- [ ] AC-02: a `tmp_path` fixture graph with `variables: {gv: default}`, no
  `state:` entry for `gv`, and one `passthrough` node. The compiled app's
  `get_input_jsonschema()["properties"]` contains `gv`. `invoke`, `ainvoke`
  and `astream(stream_mode="values")` with input `{"gv": "v"}` all return
  `gv == "v"`.
- [ ] AC-03: `graph run` on the AC-02 fixture with no `--var` ends with
  `gv == "default"`; with `--var gv=over` it ends with `gv == "over"`. Test
  drives `cmd_graph_run` with an `argparse.Namespace` and reads the final
  state.
- [ ] AC-04: precedence and collisions in `build_state_class`:
  `state: {gv: int}` plus `variables: {gv: 3}` gives `int`;
  `variables: {errors: x}` keeps `Annotated[list, add]`;
  `variables: {topic: x}` keeps `str`.
- [ ] AC-05: graph-tool path. A child fixture graph with
  `variables: {entity_type: faction}` and no `state:` entry, compiled and
  wrapped by `make_graph_tool_fn(..., output_key="entity_type",
  default_variables=...)`. Calling the tool with no kwargs returns
  `"faction"`. Test in `tests/unit/test_graph_tool.py`.
- [ ] AC-06: lint. A fixture graph whose node has
  `variables: {v: "{state.gv}"}` and graph `variables: {gv: x}` gives no
  E007. The same graph with `{state.typo}` still gives E007 naming `typo`.
- [ ] AC-07: `pytest tests/unit/test_state_builder*.py
  tests/unit/test_graph_commands.py tests/unit/test_graph_tool.py
  tests/unit/test_linter*.py -q` passes, and
  `python scripts/req_coverage.py --strict` passes.
- [ ] AC-08: `yamlgraph graph lint` gives the same findings as before on the
  10 census files (they declare every key, so the schema change adds no field
  to them).
- [ ] AC-09: `reference/graph-yaml.md` documents the block (Proposed
  Solution item 3); changelog fragment in `changelog/unreleased/` with
  `type: fix`, `req: REQ-YG-024`; this FR updated with implementation
  status; diary entry in `docs/diary/`.

## Alternatives Considered

Solution classes (chosen: 1):

1. **`build_state_class` adds `variables:` keys as `Any` fields, plus lint
   known-field parity.** Chosen. The schema is where the drop happens, so the
   fix is at that boundary (`the_one_law`). One change covers the CLI and
   graph-tool paths and all three run modes. Precedent: `data_files` keys are
   added the same way. Lint parity is needed, not optional: without it E007
   reports the newly valid graph (finding 4).
2. **Lint error for `variables:` keys missing from `state:`.** Rejected as
   the primary fix. It makes the author write each key twice, which is the
   workaround the census shows, and it leaves FR-688's merge dead for any
   graph that skips lint. After class 1 there is nothing left for it to
   report, so it is not kept as a complement either.
3. **Both 1 and 2.** Rejected for the same reason: after class 1 every
   `variables:` key is declared by definition.
4. **Refuse at compile time when a `variables:` key is not in `state:`.**
   Rejected. It turns FR-688's documented behaviour into an error and keeps
   the double declaration, only later than class 2.
5. **Merge `variables:` into the loaded config as data, like `data_files`, so
   every entry point applies them** (`invoke_graph`, subgraph nodes, map
   branches). **Preserved dissent.** It would also close finding 6. It loses
   here because it changes what every caller passes in, including subgraph
   relay and FR-955's map projection, and no caller outside the CLI and graph
   tools has asked for it. If a Python API or subgraph user reports missing
   defaults, this class is the next step.
6. **Do nothing; document "declare each `variables:` key under `state:` too".**
   Rejected. It is the cheapest option and matches current practice (census:
   11 of 11 keys copied). But it writes a silent drop into the docs as a rule,
   when the code fix is a few lines with a precedent.

Sub-choice for class 1, field type: `Any` (chosen) or inferred from the
value. Inference rejected: YAML scalars are often strings for numeric
intent, and the `TypedDict` is not checked at run time, so inference would
add a wrong annotation without adding a check.

`is_this_a_graph`: no. This is a state-schema bug. The fix is set
membership in a `TypedDict` builder; nothing asks a model anything.

## Human decision needed

1. **FR-1084 AC-06 conflicts with this FR.** FR-1084 AC-06 expects
   `--var gv_only=x` to be refused because `gv_only` is a `variables:` key
   that is not a schema key. After this FR, `gv_only` is a schema key and is
   accepted. Suggested default: this FR's semantics win (a `variables:` key
   is a declared input, which is FR-688's intent). Whichever of FR-1084 and
   FR-1091 is enforced second updates FR-1084's AC-06 fixture to expect
   acceptance and adds a truly unknown key for the refusal case. This FR does
   not edit FR-1084.
2. **Descriptor-shaped `variables:` values** (finding 7) put a dict into
   state in 2 graphs. Suggested default: not fixed here. Choosing whether the
   language supports a `{description, default, example}` descriptor or lint
   rejects it is a language decision; file it as its own FR. This FR's
   fixtures use plain values only.

## Out of scope

Applying `variables:` defaults in `invoke_graph`, subgraph nodes, map
branches, or `graph bench` (finding 6; Alternatives class 5). Descriptor
values (Human decision needed, item 2). Adding `variables:` or `data_files`
to `state_codegen.py`. Any change to FR-1084's CLI check. Changing the merge
order set by FR-688. Node-level `variables:`.

## Related

- Makes true: [FR-688](FR-688-cli-variables-injection.md)
- Sibling: [FR-1084](FR-1084-reject-undeclared-cli-vars.md) (its Problem
  finding 4 and "Human decision needed" named this FR's scope)
- Composes with: [FR-686](FR-686-novel-fandom-agent-first-rewrite.md),
  [FR-689](FR-689-genesis-canon-consistency.md),
  [FR-955](FR-955-map-branch-input-projection.md)
- Capability: [CAP-07-state-persistence.yaml](../capabilities/CAP-07-state-persistence.yaml) (REQ-YG-024)
