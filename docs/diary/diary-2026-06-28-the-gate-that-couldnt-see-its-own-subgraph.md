# The gate that couldn't see its own subgraph

**FR-621** — 2026-06-28

## What happened

A 0.5-day linter fix: `check_tool_references()` walked nodes flat, reading only
top-level `tool`/`tools`. A `type: map` node hides its real work under `node:`, so
a tool used only inside a map sub-node was reported W001 "defined but never used"
(false positive), and — worse — an *undefined* tool inside a map sub-node passed
lint entirely (E003 false negative). The fix: extract `_collect_node_tools()` and
recurse one level into `node:`.

## The trap

This is `gate_checks_shape_not_substance` wearing a new coat. The linter advertised
"every tool reference is checked," but silently exempted the single most common
composite node type. The gate *ran*, produced output, exited 0 — all the shape of
working enforcement — while the substance (does it see the map sub-node?) was
absent. A false negative in a *linter* is the expensive kind: it doesn't just
miss a bug, it manufactures false confidence. `graph lint ... 0 error(s)` is a
certificate the author trusts.

## The insight

The W001 false positive was the gift. It was *noisy* — it nagged on a correct
graph, so it got noticed and filed. The E003 false negative was silent — a broken
graph passing clean — and would never have surfaced until a runtime failure. The
loud wrong answer led me to the quiet wrong answer. When a gate produces a visible
false positive, look immediately for its mirror-image false negative: the same
blind spot usually cuts both ways.

The cure was structural, not a patch: recursing into `node:` (rather than
special-casing `node["node"]["tool"]`) means any future node shape that reuses the
sub-node container is covered for free. Normalize at the structure, not the symptom.

## Seed

Which other linter checks (`check_prompt_files`, state-key reachability,
edge-target validation) walk nodes flat and silently skip map/subgraph sub-nodes?
The map sub-node is a recurring blind spot — should there be one shared
`iter_executable_nodes(graph)` generator that every check consumes, so the
descent-into-subgraphs decision is made *once* instead of re-litigated per check?
