# Feature Request: Split `map_compiler.py` into a `yamlgraph/compile/map/` package (move-only)

**Priority:** MEDIUM
**Type:** Enhancement (refactor)
**Status:** Rejected — [judgement](FR-1063-map-compiler-package-split.judgement.md); no implementation authority. Re-file with substantive research.
**Refiled (2026-09-25):** as [FR-1082](FR-1082-map-compiler-package-split.md).
**Effort:** 0.5 days
**Requested:** 2026-09-25
**First consumer / first event:** [FR-1064](FR-1064-map-branch-contract.md)
(map branch contract): its first commit adds a failure-record helper to the
branch wrapper and a join node at the fan-in, and must land in modules that
already exist rather than in a 368-line file that it would push past the
450-line cap.
**Research:** in-body dispositioned alternatives table below, plus
[docs/issues-2026-09-24.md §6.5](../docs/issues-2026-09-24.md#65-implementation-shape-does-the-map-need-to-become-a-package)
(source reading of the map compiler, edge compiler and routing at `a4f788f8`).
The FR-890 research route was not run: this is a move-only refactor with no
design space beyond module boundaries.
**Prior art:** [FR-936-map-node-hardening.md](FR-936-map-node-hardening.md)
(SPLIT) — split map *behavior* work into four contracts; this FR moves code
only and changes no contract.

## Summary

Move the four functions of `yamlgraph/compile/map_compiler.py` into a package
whose modules follow the change rate of the planned map work, and replace the
`(edge_fn, sub_node_name)` tuple with a typed `CompiledMap` record. No behavior
change.

## Value Statement

Authors of the map fixes (FR-1064, FR-1065, FR-939) each touch one small module
instead of one growing file, and the compiled map's shape can gain a field
without editing nine unpack sites.

## Problem

- `map_compiler.py` is 368 lines (target 400, cap 450). FR-1064 and the
  resumable-map work add key and version handling, a failure-record helper,
  a join node, a store lookup and a ledger; together well past the cap.
- The file mixes parts with unrelated change rates: the sub-node factory
  (`if/elif` over five node types, ~70 lines) changes only when a node type is
  added; the branch wrapper and the fan-out change with every map fix.
- `compile_map_node` returns a bare tuple `(edge_fn, sub_node_name)`, unpacked
  at seven sites in `yamlgraph/compile/edge_compiler.py`, one in
  `yamlgraph/routing.py` and one in `yamlgraph/compile/node_compiler.py`.
  FR-1064 adds a join node name; with a tuple that edit touches all nine sites.
- `wrap_for_reducer` repeats its result normalisation (`model_dump` plus
  `_map_index`) on the non-dict and the dict path.

## Ideal Result

The map lives in a package where each planned fix has an obvious home, the
compiled map is a named record, and the test suite is green before and after
with only import paths changed.

## Proposed Solution

```text
yamlgraph/compile/map/
  __init__.py   compile_map_node, CompiledMap
  subnode.py    sub-node factory dispatch (tool_call, python, agent, subgraph, llm)
  fan_out.py    map_edge construction: resolve `over`, cap, Send list
  branch.py     wrap_for_reducer, _execute_node_fn
  results.py    flatten_map_results
```

- `CompiledMap` is a frozen dataclass with `edge_fn` and `sub_node_name`.
  The nine unpack sites read fields by name.
- `yamlgraph/compile/map_compiler.py` is deleted. All importers (one
  production module, nine test files, three `mock.patch` target strings) move
  to the new paths. No re-export module (Scripture: no shims).
- The duplicated normalisation in `wrap_for_reducer` becomes one local
  function. Output is byte-identical for every existing test.
- `fan_in.py`, `store.py` and `ledger.py` are **not** created here; the FRs
  that need them create them.

## Acceptance Criteria

- [ ] `yamlgraph/compile/map_compiler.py` no longer exists; `grep -r map_compiler yamlgraph tests` returns nothing.
- [ ] Every module in `yamlgraph/compile/map/` is under 200 lines.
- [ ] `compile_map_node` returns `CompiledMap`; no tuple unpacking of a map remains in `edge_compiler.py`, `routing.py`, `node_compiler.py`.
- [ ] Full unit suite green with no test assertion changed (only imports and patch targets).
- [ ] `lint-imports`, `ruff`, `vulture` clean; `vulture_whitelist.py` comment on line 79 updated.
- [ ] REQ-YG-040/041/055 component columns in `ARCHITECTURE.md` point at the new modules.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Keep one file, split when the cap is hit | Rejected: FR-1064's first commit would then mix a refactor with a behavior change (one concern per commit). |
| Fold the split into FR-1064 | Rejected: a move-only diff is reviewable by `git diff -M`; mixed with new behavior it is not. |
| Leave the tuple, split only the file | Rejected: the tuple is the one shape FR-1064 must change; changing it here keeps FR-1064's diff to behavior. |
| Re-export from `map_compiler.py` | Rejected: a compat shim (Commandment 8). |

## Related

- Plan: [docs/issues-2026-09-24.md §6.5, §7](../docs/issues-2026-09-24.md)
- Blocks: [FR-1064](FR-1064-map-branch-contract.md); precedes [FR-939](FR-939-map-overflow-policy.md) only if FR-939 is enforced after it (either order works; FR-939 then edits `fan_out.py`).
