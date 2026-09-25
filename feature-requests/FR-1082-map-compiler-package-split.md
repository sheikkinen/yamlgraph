# Feature Request: Split `map_compiler.py` into a `yamlgraph/compile/map_node/` package (literal move)

**Priority:** MEDIUM
**Type:** Enhancement (refactor)
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-09-25
**First consumer / first event:** the first implementation commit of
[FR-1073](FR-1073-map-result-contract.md) (map result contract; authority
active, no implementation commit on `main` at `011317a8`). Its D-3 surface is
`yamlgraph/compile/map_compiler.py`. It adds a branch-outcome helper to the
wrapper, turns the map node into a dispatch node, and adds a result join.
With this FR landed first, that diff lands in small modules and contains
behavior only.
**Research:** FR-890 research route **not run, by operator decision
(2026-09-25: "refile. skip research — document as skipped")**. Substitute:
the in-body [Alternatives Considered](#alternatives-considered) table below
(five solution classes, one chosen, one preserved dissent, a precedent line
per class, and an `is_this_a_graph` answer). This is the "equivalent
committed dispositioned alternatives table" of
`.github/skills/judge-fr/doctrine.md` (Research evidence clause), the form
accepted for [FR-1065](FR-1065-resumable-map-investigation.md) and
[FR-1076](FR-1076-shared-map-reuse-helpers.md). Source reading at
`011317a8`; plan context in
[docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §6.5.
**Prior art:**
[FR-1063](FR-1063-map-compiler-package-split.md) (**Rejected**,
[judgement](FR-1063-map-compiler-package-split.judgement.md)). Same goal.
This refile answers each objection:
- *R-1 (research):* FR-1063 compared four variants of one refactor with no
  precedent and no graph-fit answer. This FR compares five solution classes,
  each with a precedent line, keeps a dissent, and answers
  `is_this_a_graph`. The committed research record R-1 asked for is replaced
  by the in-body table, by operator decision (see Human decision needed).
- *R-2 (behavior at the import boundary):* FR-1063 promised a typed
  `CompiledMap` record and a shared normalisation in `wrap_for_reducer`.
  Both changed code beyond a move. This FR drops both. Function bodies move
  unchanged, which is checked by AST equality (AC-02). Every importer, patch
  target and doc reference is enumerated below. A characterization test pins
  the exact return value of `wrap_for_reducer` on the dict, non-dict and
  error paths before the move (AC-01).
- *R-2 (no FR-1064 behavior):* no join, failure record or retry change is
  included. Those belong to FR-1073 and
  [FR-1079](FR-1079-retry-ownership.md), the two halves of the SPLIT
  [FR-1064](FR-1064-map-branch-contract.md).
- *C-2 (no failure or retry change):* the move changes no map execution
  path. AC-02 and AC-04 witness this.

[FR-717](FR-717-root-package-seams.md) (Completed) — created
`yamlgraph/compile/` itself as a move-only package split, with rename
similarity witnessed per PR and no aliases left. Its finding F1 (a package
named after a builtin shadows it at `from yamlgraph import compile`) is why
this FR names the package `map_node`, not `map`.
[FR-716](FR-716-preemptive-module-splits.md) (Completed) — pre-emptive
split before a file reached the cap.
[FR-718](FR-718-edge-compiler-decomposition.md) (Completed) —
decomposition with new internal functions (classify-then-dispatch); the
precedent for class 2 below.
[FR-674](FR-674-proactive-module-splits.md) (Enforced) — splits made when
the size ceiling was hit; the precedent for class 3.
[FR-681](FR-681-module-reorg-restore-module-map-budget.md) (Rejected,
superseded) — a reorganisation justified by a budget, not a consumer; the
precedent for class 5.
[FR-936](FR-936-map-node-hardening.md) (SPLIT) — map *behavior* work; this
FR changes no contract.

## Summary

Move the four functions of `yamlgraph/compile/map_compiler.py`, unchanged,
into three modules of a new package `yamlgraph/compile/map_node/`. Update
every importer to the new paths and delete the old file. Pin the wrapper's
current outputs with a characterization test first. No behavior change.

## Value Statement

The FR-1073 author edits a 150-line module instead of a 368-line one, and
the FR-1073 reviewer reads a diff that contains only behavior, because the
move was reviewed separately and proven by AST equality.

## Problem

- `yamlgraph/compile/map_compiler.py` is 368 lines. The size gate warns
  above 400 and fails above 450 (`.pre-commit-config.yaml#L163`,
  `scripts/size_gate.py#L25`).
- The file holds four functions with different change rates:
  - `flatten_map_results`
    ([map_compiler.py#L30-L89](../yamlgraph/compile/map_compiler.py#L30-L89)),
    added by FR-052 and not touched by FR-1073;
  - `_execute_node_fn` and `wrap_for_reducer`
    ([#L92-L225](../yamlgraph/compile/map_compiler.py#L92-L225)), the branch
    wrapper that FR-1073 items 3–5 rewrite;
  - `compile_map_node`
    ([#L228-L368](../yamlgraph/compile/map_compiler.py#L228-L368)), the
    sub-node factory plus the `map_edge` fan-out closure
    ([#L335-L366](../yamlgraph/compile/map_compiler.py#L335-L366)), which
    FR-1073 items 1 and 8 replace with a dispatch node and a join.
- FR-1073 adds a dispatch node, a branch-outcome helper and a join to this
  file. How many lines that adds is a forecast, not a measurement.
- Neighbouring files are closer to the cap: `edge_compiler.py` 436 lines,
  `node_compiler.py` 446, `graph_loader.py` 450. This FR does not relieve
  them (see Out of scope).

## Ideal Result

Each map concern has its own module. The move is proven by equal ASTs, not
by reading a diff. The test suite is green before and after, and the only
test edits are import lines, patch targets and one doc-evidence marker.
FR-1073 then opens a diff with behavior only.

## Proposed Solution

```text
yamlgraph/compile/map_node/
  __init__.py   docstring only; no imports, no re-exports
  results.py    flatten_map_results                    (map_compiler.py#L30-L89)
  branch.py     _execute_node_fn, wrap_for_reducer     (#L92-L225)
  builder.py    compile_map_node                       (#L228-L368)
```

1. **Characterization first (commit 1).** Add
   `tests/unit/test_map_wrapper_characterization.py`, importing from
   `yamlgraph.compile.map_compiler`. It asserts the exact return dict of
   `wrap_for_reducer` for each path:
   - dict result with `state_key` present, and without it (falls back to
     the whole result, #L204);
   - dict result whose `state_key` value is a Pydantic model, with and
     without `_map_index` in state, with `flatten_output` true and false;
   - non-dict result: scalar, list and Pydantic model, with and without
     `_map_index` in state (#L175-L190);
   - error-bearing update: `errors` key, `error` key, and `error: None`
     (#L192-L202);
   - raised exception (#L161-L173) and timeout (#L142-L160), including the
     `errors` entry's `node` and `error_type`.

   This test passes on current code. It is a witness of today's behavior,
   not a RED: nothing is broken. The `error: None` case pins a defect that
   FR-1073 fixes on purpose; FR-1073 changes that assertion in its own RED
   commit.
2. **Move (commit 2).** Create the package. Each function body is copied
   byte for byte. Each module gets only the imports its functions use.
   `branch.py` imports `flatten_map_results` from `results.py`;
   `builder.py` imports `wrap_for_reducer` from `branch.py`. Delete
   `map_compiler.py`. No module re-exports another (Commandment 8).
3. **Importers.** Edit each to the new module:
   - production: `yamlgraph/compile/node_compiler.py#L16` → `builder`;
   - tests, import lines only: `test_fr026_chaplain_fixes.py#L16`,
     `test_fr027_execution_safety.py#L42,77,111,144`,
     `test_map_flatten_output.py` (12 lines, #L17–#L204),
     `test_map_keyerror_context.py#L64`, `test_map_node_timeout.py#L10`,
     `test_map_node.py#L7`, `test_style_convert.py#L252,306`,
     `test_tool_call_integration.py#L10`, and the new characterization test;
   - patch targets: `test_map_node_timeout.py#L187`
     (`...map_compiler.create_node_function`) and `test_map_node.py#L305`,
     `#L337` (`...map_compiler.load_python_function`) →
     `yamlgraph.compile.map_node.builder.<name>`, because `compile_map_node`
     looks those names up in `builder`.
4. **References.** Update to the new module paths:
   - `capabilities/CAP-11-subgraph-map.yaml#L5,6,12,16`,
     `CAP-16-linter-cross-reference.yaml#L11,31`,
     `CAP-17-execution-safety-guards.yaml#L17,32`,
     `CAP-84-import-linter-boundaries.yaml#L17`,
     `CAP-96-per-node-timeout.yaml#L14,32`,
     `CAP-155-schema-loader-tool-type.yaml#L13,38`; then regenerate the
     `ARCHITECTURE.md` capability block with
     `scripts/aggregate_capabilities.py` (block `ARCHITECTURE.md#L330-L3340`).
     Mentions outside that block (#L235, #L3400, #L3947) are edited by
     hand.
   - `vulture_whitelist.py#L79` comment.
   - `reference/module-map.md` regenerated with
     `scripts/generate_module_map.py`; `reference/patterns.md#L1552` prose.
   - `docs/concurrency-safety.md#L34,37` cite `yamlgraph/map_compiler.py`,
     a path already stale since FR-717. `test_concurrency_safety_doc.py#L28`
     pins that string. Both move to the new paths together.
5. **Left unchanged.** The tuple `(map_edge_fn, sub_node_name)` returned by
   `compile_map_node` stays. Its unpack sites stay:
   `edge_compiler.py#L123,140,189,225,226,240,247,355`,
   `routing.py#L100`, `node_compiler.py#L174`, and the test unpacks and
   tuple fixtures (`test_fr027_execution_safety.py`,
   `test_map_keyerror_context.py#L81`, `test_map_node.py`,
   `test_tool_call_integration.py#L157`, `test_fr718_edge_shapes.py#L18`,
   `test_parallel_fanout_edges.py#L176`, `test_route_log.py#L182`). FR-1073
   item 8 changes this metadata to carry three names, so it owns the shape.
   Dated records keep their old links: `docs/issues-2026-09-24.md`,
   diaries, feature requests, changelog fragments, and
   `examples/demos/fi_domain_crawl/demo-output.log`.
6. **One observable change.** The fan-out truncation warning is logged by
   `logging.getLogger(__name__)` (#L27). Its logger name changes from
   `yamlgraph.compile.map_compiler` to `yamlgraph.compile.map_node.builder`.
   No test filters on that name (grep at `011317a8`).

## Acceptance Criteria

- [ ] AC-01: commit 1 adds the characterization test covering every path in
  item 1. It passes on the base commit with only
  `yamlgraph.compile.map_compiler` imports. After commit 2 it passes with
  only its import line changed.
- [ ] AC-02: for `flatten_map_results`, `_execute_node_fn`,
  `wrap_for_reducer` and `compile_map_node`, `ast.dump` of the function node
  at the base commit equals `ast.dump` at the new location. The check is
  run and its output quoted in the FR implementation record.
- [ ] AC-03: `yamlgraph/compile/map_compiler.py` does not exist.
  `grep -rn "map_compiler" yamlgraph tests scripts capabilities reference vulture_whitelist.py`
  returns nothing. `ARCHITECTURE.md` contains no `map_compiler` outside
  quoted history.
- [ ] AC-04: the full unit suite is green. The diff under `tests/` contains
  only the new characterization test, import lines, the three patch
  targets and `test_concurrency_safety_doc.py#L28`. No assertion changes.
- [ ] AC-05: each module under `yamlgraph/compile/map_node/` is under 200
  lines. `__init__.py` has no import statements.
- [ ] AC-06: `lint-imports`, `ruff check`, `vulture` and
  `python scripts/req_coverage.py --strict` pass. The characterization
  tests carry `@pytest.mark.req("REQ-YG-041")`.
- [ ] AC-07: the tuple returned by `compile_map_node` and all its unpack
  sites in item 5 are unchanged.
- [ ] AC-08: FR implementation record and diary entry.

## Alternatives Considered

Solution classes (chosen: 1; dissent preserved: 4).

| # | Class | Alternative | Precedent | Disposition |
|---|---|---|---|---|
| 1 | literal move | Move the four functions unchanged into three modules; keep the tuple | [FR-717](FR-717-root-package-seams.md) (move-only package, no aliases); [FR-716](FR-716-preemptive-module-splits.md) (pre-emptive split) | **Chosen.** The only class whose correctness is a mechanical check (AST equality) instead of a review. It gives FR-1073 small modules without touching anything FR-1073 rewrites. |
| 2 | decomposition | FR-1063's plan: extract the sub-node factory and `map_edge` into own modules, add a typed `CompiledMap`, share the wrapper's normalisation | [FR-718](FR-718-edge-compiler-decomposition.md) (new internal functions, same behavior) | **Rejected.** FR-1063 judgement R-2: changes code beyond a move. FR-1073 replaces exactly these parts: `map_edge` becomes a dispatch node (item 1), the metadata gets three names (item 8), and the normalisation is replaced by one branch-outcome helper (item 3). Work done here would be rewritten there. |
| 3 | reactive split inside the behavior FR | FR-1073 splits the file itself if its change crosses the size gate | [FR-674](FR-674-proactive-module-splits.md) (splits when the ceiling was hit) | **Rejected.** One diff would mix a move with a behavior change, so neither can be reviewed on its own (`mixed_commits_erode_auditability`). FR-1073's frozen D-3 surface names `map_compiler.py` only; a new package is outside it. FR-1063 judgement R-2 also forbids folding the two. |
| 4 | split after the behavior FR | Land FR-1073 in `map_compiler.py`, then split the resulting shape in a separate move-only FR | [FR-717](FR-717-root-package-seams.md) (move-only split of a settled shape) | **Dissent preserved.** It splits the final shape, so no boundary is drawn around code about to be rewritten, and it cannot conflict with an FR-1073 branch already in progress. It loses because FR-1073's own diff would then land in the larger file, and its reviewer would read behavior changes inside a 368-line module with three concerns. If an FR-1073 implementation branch exists when this FR is enforced, this class wins (see Human decision needed). |
| 5 | do nothing | Keep one file; 368 lines is under the 400-line warning | [FR-681](FR-681-module-reorg-restore-module-map-budget.md) (Rejected: reorganisation justified by a budget, not a consumer) | **Rejected.** FR-681 died for lacking a consumer; this FR has one (FR-1073). The file is under the gate today, so the case for a split rests on FR-1073's diff, which is a forecast. That is why class 1 is chosen over class 4 only when no FR-1073 branch exists. |

`is_this_a_graph`: no. This is deterministic code motion checked by AST
equality. No step asks a model anything.

## Human decision needed

- **Research form.** FR-1063 judgement R-1 asks for a *committed research
  record*. The operator ruled "skip research — document as skipped"; this
  FR offers the in-body table the judge doctrine names as an equivalent.
  *Suggested default:* accept the in-body table, as the FR-1065 and FR-1076
  judgements did. If the judge rejects on R-1 alone, the operator decides
  between running `scripts/research.sh` and overriding.
- **Order against FR-1073.** *Suggested default:* enforce this FR only if no
  FR-1073 implementation branch or open PR exists at that time. If one
  exists, withdraw this FR and file class 4 after FR-1073 merges, because a
  move on top of an in-flight rewrite of the same file is a rebase against
  every hunk.
- **FR-1073's D-3 path.** If this FR lands first, FR-1073's D-3 surface
  `yamlgraph/compile/map_compiler.py` names a file that no longer exists.
  *Suggested default:* the operator records a one-line note in FR-1073 that
  D-3 reads as `yamlgraph/compile/map_node/*`; a path rename, not a scope
  change, so no rejudgement.

## Out of scope

- The `CompiledMap` record or any change to the tuple (FR-1073 item 8).
- Any change to `wrap_for_reducer` behavior, including the `error: None`
  key-presence defect (FR-1073 item 3).
- Map result, failure, join, retry or timeout behavior (FR-1073, FR-1079,
  [FR-956](FR-956-map-branch-timeout-lifecycle-investigation.md)).
- Overflow policy ([FR-939](FR-939-map-overflow-policy.md)); it edits the
  fan-out wherever it then lives.
- Moving the map edge handlers out of `edge_compiler.py` (436 lines).
  FR-1073 item 8 edits them; that pressure is not relieved here.
- `examples/ebook/prompts/chapter/wizard.yaml#L32,99`, which already names
  the stale path `yamlgraph/map_compiler.py`. It is a governed prompt
  artifact; changing it goes through the graph-authoring route.

## Related

- Refile of: [FR-1063](FR-1063-map-compiler-package-split.md) (Rejected)
- First consumer: [FR-1073](FR-1073-map-result-contract.md)
- Sibling: [FR-1079](FR-1079-retry-ownership.md)
- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §6.5
