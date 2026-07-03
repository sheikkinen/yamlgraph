# Diary: The Image Worships the Beast It Judges

**Date:** 2026-07-03
**FR:** FR-666

## Observation

Building the adversarial content audit demo surfaced three separate traps in quick succession:

1. **Router routes cannot point to END** — routes must target real nodes. When all routes converge to the same destination, the router adds no branching value. Converting to a plain LLM node preserves the structured output (path/reasoning) without the routing machinery. The router pattern is for *diverging* paths, not *classifying* a converged outcome.

2. **Python node tools need a `tools:` registry** — the node's `type: python` with inline `module`/`function` was an older pattern. Current contract: declare in `tools:` section, reference via `tool:` in the node. The error message "not found in tools registry" was clear once you knew the contract.

3. **Python tool functions receive `state` dict, not individual args** — the gate function was authored with named parameters (`beast_output: str`, `forbidden_claims: dict`). But `create_python_node` calls `func(effective_state)` — one dict. The function must extract its own keys from state.

## Trap

**architecture_as_diagram**: I authored the graph YAML and Python gate as if they were independent components. The graph YAML declares the contract; the Python function must conform to it. The contract is: `func(state: dict) -> Any`. Authoring the function with its own parameter names was designing a component without reading the interface specification.

Also **quick_confidence**: the router-to-END pattern seemed obvious. Three routes, all to END. But the validation is: routes must point to nodes in the graph, and END is not a node — it's a sentinel in the edge system.

## Cure

**test_before_reading**: The lint (0 errors) and the runtime error ("route 'agree' points to nonexistent node 'END'") told me exactly what was wrong. I didn't need to read source code to understand the contract — the error message was the documentation.

## Seed

When a router's routes all converge to the same target, is the router expressing intent (classification) or is it a structural illusion? The verdict node *classifies* (agree/split/gate_overrules) but doesn't *route*. YAMLGraph could lint for this: "W0XX: Router node 'X' has all routes pointing to the same target — consider type: llm with structured output instead."
