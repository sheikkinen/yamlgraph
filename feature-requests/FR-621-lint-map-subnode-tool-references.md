# Feature Request: Linter must descend into map sub-nodes for tool references

**Priority:** MEDIUM
**Type:** Bug
**Status:** Implemented (2026-06-28) — RED→GREEN, all acceptance criteria met
**Effort:** 0.5 days
**Requested:** 2026-06-28

## Implementation Notes (2026-06-28)

- Extracted `_collect_node_tools()` in [yamlgraph/linter/checks.py](../yamlgraph/linter/checks.py),
  which gathers a node's `tool`/`tools` references, emits E003 for undefined refs,
  and **recurses one level into `node:`** so map sub-nodes are seen by the
  reachability walk. Recursion (rather than special-casing `node["node"]["tool"]`)
  also covers any future nesting that reuses the `node:` sub-node shape.
- `check_tool_references()` now delegates per-node collection to the helper.
- RED tests added to `tests/unit/test_graph_linter.py`
  (`test_map_subnode_tool_not_unused`, `test_map_subnode_undefined_tool_errors`),
  tagged `@pytest.mark.req("REQ-YG-003")`. Confirmed failing pre-fix, green post-fix.
- Verified `graph lint examples/plot_modeller/graphs/roundtrip_skeleton.yaml`
  now reports no issues; full `test_graph_linter.py` suite green (26 passed).

## Summary

`check_tool_references()` in [yamlgraph/linter/checks.py](../yamlgraph/linter/checks.py) only
inspects a node's top-level `tool` / `tools` keys. A `type: map` node carries its real work in a
nested sub-node under `node:`, whose `tool` reference is never collected. This produces a **W001
false positive** (a tool used only in a map sub-node is reported "defined but never used") and,
more dangerously, an **E003 false negative** (a reference to an *undefined* tool inside a map
sub-node is not flagged — a broken graph passes lint).

## Value Statement

Graph authors who use map nodes (the common fan-out pattern) get correct tool-reference linting
instead of spurious warnings that train them to ignore lint output, and broken sub-node tool
references are caught statically instead of failing at runtime.

## Judgement (2026-06-28)

**Verdict: Authority GRANTED with corrections.** The strongest-evidenced FR of the batch — a
reproducible bug with a boundary-correct fix and TDD-shaped acceptance criteria.

**PROCESS DEFECT — number collision (RESOLVED).** This FR originally collided on FR-616 with
`FR-616-compaction-node.md`. Renumbered to **FR-621** (next free; max was 620) — it has the
independent origin (P0 scaffold review) and only self-references, whereas the research trio
FR-616(compaction)/617/618/619 cross-reference each other by number and kept theirs. Filename and
title updated; no external back-references existed.

**Claim verified against source.** [check_tool_references](../yamlgraph/linter/checks.py) (line 190)
walks only `node_config.get("tools")` and `node_config.get("tool")` at the top level — it never
descends into `node_config["node"]`. Both symptoms are real: the W001 false positive (sub-node
tool reported unused) and the latent E003 false negative (undefined sub-node tool passes lint).
The recurse-one-level helper is the right boundary fix ("enumerate all references," not "tolerate
misses"), and the rejection of the `stub_` prefix suppression is correct discipline.

**Correction 1 (PRIMARY — scope the blindness, don't just patch one shape).** The fix recurses into
`node:` (the map sub-node). Verify that `node:` is the **only** composite shape carrying executable
tool refs. If `race`/parallel candidates, `subgraph`, or branch nodes also nest a `tool`/`tools`
key, they share the identical blindness and the same E003 false negative. Either generalize the
walk to every nested node-shape or **explicitly scope to `node:` and file the remaining shapes** as
known gaps — do not leave the reader believing all composite nodes are now covered when only one is.

**Correction 2 (secondary).** The `used |=` union across nesting levels is correct for the W001
computation; keep the `f"{node_name}.node"` path in E003 messages so the author can locate the
sub-node reference. Add a RED test asserting the **message path** points at the sub-node, not the
map wrapper.

**Frozen scope.** The linter enumerates tool refs in a node AND its `node:` sub-node; two RED tests
(W001 suppressed for sub-node-only use, E003 raised for undefined sub-node ref); `roundtrip_skeleton`
lints clean; req-tagged. Composite shapes other than `node:` are either covered or explicitly filed.

## Problem

The reachability walk in `check_tool_references()` is flat:

```python
for node_name, node_config in graph.get("nodes", {}).items():
    node_tools = node_config.get("tools", [])      # top-level only
    ...
    single_tool = node_config.get("tool")          # top-level only
```

For a map node the executed tool lives at `node_config["node"]["tool"]`:

```yaml
draft_chapter:
  type: map
  over: "{state.briefs}"
  as: brief
  node:                       # <-- linter never looks here
    type: python
    tool: stub_draft_chapter  # <-- used, but reported as W001 unused
    state_key: draft
  collect: chapter_drafts
```

Two concrete symptoms, both reproducible today on
[examples/plot_modeller/graphs/roundtrip_skeleton.yaml](../examples/plot_modeller/graphs/roundtrip_skeleton.yaml):

1. **W001 false positive** (observed): `⚠ [W001] Tool 'stub_draft_chapter' is defined but never
   used` — the tool is used inside the map sub-node.
2. **E003 false negative** (latent, worse): rename the sub-node's `tool:` to a name that is **not**
   in the `tools:` section and `graph lint` still reports `0 error(s)` — an undefined tool
   reference passes lint and only fails when the graph runs.

A gate that cannot see its own subgraph silently exempts the most common composite node type from
the check it advertises.

## Proposed Solution

Collect tool references from a node **and** its map sub-node before computing the
`defined − used` difference. Extract the per-node collection into a small helper that recurses one
level into `node:`:

```python
def _collect_node_tools(node_name, node_config, defined_tools, issues):
    """Add this node's tool refs to a used set; emit E003 for undefined refs."""
    used: set[str] = set()
    refs = list(node_config.get("tools", []))
    if node_config.get("tool"):
        refs.append(node_config["tool"])
    for tool in refs:
        used.add(tool)
        if tool not in defined_tools:
            issues.append(LintIssue(severity="error", code="E003", ...))
    # Map nodes nest the executed node under `node:` — recurse one level.
    sub = node_config.get("node")
    if isinstance(sub, dict):
        used |= _collect_node_tools(f"{node_name}.node", sub, defined_tools, issues)
    return used
```

Recursing (rather than special-casing `node["node"]["tool"]`) also covers any future nesting that
reuses the `node:` sub-node shape.

## Acceptance Criteria

- [ ] RED test: a graph whose only use of a defined tool is inside a `type: map` sub-node produces
      **no** W001 for that tool.
- [ ] RED test: a `type: map` sub-node referencing an **undefined** tool produces **E003**.
- [ ] `graph lint examples/plot_modeller/graphs/roundtrip_skeleton.yaml` reports
      `0 error(s) and 0 warning(s)`.
- [ ] Existing W001/E003 top-level behavior unchanged (regression tests green).
- [ ] `@pytest.mark.req` tags on new tests link to the linter capability requirement.

## Alternatives Considered

- **Inline special-case** `node_config["node"]["tool"]` without a helper — rejected: duplicates the
  E003 emission logic and does not generalize to deeper nesting.
- **Suppress W001 for tools matching a `stub_` prefix** — rejected: hides the symptom, leaves the
  E003 false negative (the dangerous half) unfixed, and is a downstream patch rather than a
  boundary fix (the boundary is "enumerate all tool references," not "tolerate some misses").

## Related

- [yamlgraph/linter/checks.py](../yamlgraph/linter/checks.py) `check_tool_references()` (W001/E003)
- [tests/unit/test_graph_linter.py](../tests/unit/test_graph_linter.py) (existing W001/E003 tests)
- Surfaced during FR-610 P0 scaffold review of the round-trip walking skeleton
  ([docs/architecture-walking-skeleton.md](../docs/architecture-walking-skeleton.md)).
- Prior art for nested-reference linting: FR-319 (lint unanchored prompt variables).
