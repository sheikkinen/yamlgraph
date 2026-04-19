# Feature Request: Compile-Time Pipeline Templates

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Judged:** 2026-04-18
**Effort:** 3 days
**Requested:** 2026-04-18

## Summary

Add a `type: pipeline` meta-node that defines a sequence of stages once, iterates over a list of items, and expands to concrete nodes + edges before graph compilation — eliminating the repetitive boilerplate that dominates multi-chapter, multi-phase graphs.

## Value Statement

Graph authors defining repetitive multi-step patterns (e.g., write→judge→amend per chapter) can reduce graph size by 80%+ and maintain the pattern in a single place, preventing drift between copies.

## Problem

The ebook graph (`examples/ebook/graph.yaml`) has 377 lines where 7 chapters repeat an identical write→judge→amend triplet — 21 nodes, 21 edges, ~168 lines of boilerplate. Only 3 variables change per chapter: the chapter name, the prompt path, and the filename variable.

This causes:

1. **Maintenance burden**: Changing the pipeline pattern (e.g., adding a "review" stage) requires modifying 7 nodes and 7 edges manually.
2. **Copy-paste drift**: Subtle inconsistencies creep in when one chapter's node is updated but others are not.
3. **Readability collapse**: The graph's intent (sequential chapters, each with quality control) is buried under repetitive YAML.

Map nodes (`type: map`) solve the *runtime* parallel case — fan out over data items with `Send()`. Pipeline templates solve the *compile-time* sequential case — stamp out a repeating subgraph pattern for each item in a static list.

## Proposed Solution

### YAML Configuration

```yaml
nodes:
  chapters:
    type: pipeline
    items:
      - name: introduction
        prompt_prefix: chapter/introduction
        filename: "{state.filename_introduction}"
      - name: doctrine
        prompt_prefix: chapter/doctrine
        filename: "{state.filename_doctrine}"
      - name: conclusion
        prompt_prefix: chapter/conclusion
        filename: "{state.filename_conclusion}"
    stages:
      - name: write
        type: copilot
        prompt: "{item.prompt_prefix}"
        variables:
          filename: "{item.filename}"
        state_key: current_chapter
        timeout: 300
      - name: judge
        type: copilot
        prompt: judge/chapter
        variables:
          filename: "{item.filename}"
        state_key: current_chapter
        timeout: 300
      - name: amend
        type: copilot
        prompt: amend/chapter
        variables:
          filename: "{item.filename}"
        state_key: current_chapter
        timeout: 300

edges:
  - from: START
    to: chapters        # Resolves to first expanded node
  - from: chapters      # Resolves to last expanded node
    to: END
```

### Expansion Semantics

At load time, `expand_pipeline_templates()` transforms the above into concrete nodes and edges:

```yaml
# Expanded nodes (generated):
nodes:
  chapters__introduction__write:
    type: copilot
    prompt: chapter/introduction
    variables:
      filename: "{state.filename_introduction}"
    state_key: current_chapter
    timeout: 300
  chapters__introduction__judge:
    type: copilot
    prompt: judge/chapter
    variables:
      filename: "{state.filename_introduction}"
    state_key: current_chapter
    timeout: 300
  chapters__introduction__amend:
    type: copilot
    prompt: amend/chapter
    variables:
      filename: "{state.filename_introduction}"
    state_key: current_chapter
    timeout: 300
  chapters__doctrine__write:
    type: copilot
    # ... same pattern ...
  # ... etc ...

# Expanded edges (generated):
edges:
  # Intra-item chaining (stages within each item)
  - from: chapters__introduction__write
    to: chapters__introduction__judge
  - from: chapters__introduction__judge
    to: chapters__introduction__amend
  # Inter-item chaining (last stage of item N → first stage of item N+1)
  - from: chapters__introduction__amend
    to: chapters__doctrine__write
  # ... etc ...
  # External edges rewritten
  - from: START
    to: chapters__introduction__write
  - from: chapters__conclusion__amend
    to: END
```

### Naming Convention

Expanded node names follow: `{pipeline_name}__{item_name}__{stage_name}`

Double-underscore (`__`) is consistent with the `expand_interactive_tools()` convention (e.g., `tool__start`, `tool__ask`).

### Variable Interpolation

Item fields are substituted into stage configs using `{item.field}` syntax. Substitution happens during expansion (string replacement in the config dict), not at runtime. This keeps the expansion logic simple and the resulting nodes identical to hand-written ones.

Only string values in `prompt`, `variables`, and `state_key` fields are interpolated. Non-string fields (`timeout`, `temperature`) are copied verbatim from the stage definition.

### Integration Points

| Component | Change |
|-----------|--------|
| `yamlgraph/pipeline_template.py` | New module: `expand_pipeline_templates()` function |
| `yamlgraph/graph_loader.py` | Call `expand_pipeline_templates(config)` after `expand_interactive_tools()` (line ~212) |
| `yamlgraph/lint.py` | Validate pipeline node: `items` non-empty, `stages` non-empty, all `{item.*}` references resolve |
| `yamlgraph/models/graph_schema.py` | Add `PIPELINE = "pipeline"` to `NodeType`; add `items`, `stages` fields to `NodeConfig` |

### Implementation Approach

Follow the `expand_interactive_tools()` pattern from FR-049 (`yamlgraph/interactive_tool.py`):

1. **Scan**: Find all `type: pipeline` nodes in `config["nodes"]`.
2. **Deep copy**: Work on `copy.deepcopy(config)` to avoid mutation.
3. **Expand**: For each pipeline node, for each item, for each stage:
   - Generate concrete node name: `{pipeline}__{item.name}__{stage.name}`
   - Clone stage config, substituting `{item.*}` references with item field values
   - Add to `result_nodes`
4. **Chain**: Generate sequential edges:
   - Within each item: `stage[0] → stage[1] → ... → stage[N]`
   - Between items: `item[K].stage[N] → item[K+1].stage[0]`
5. **Rewrite edges**: Redirect external edges referencing the pipeline node:
   - `to: pipeline_name` → `to: first_item__first_stage`
   - `from: pipeline_name` → `from: last_item__last_stage`
6. **Remove**: Delete the original pipeline meta-node from `result_nodes`.
7. **Return**: Modified config dict for further processing.

## Acceptance Criteria

- [x] `type: pipeline` node with `items` and `stages` expands to concrete nodes at load time
- [x] Expanded nodes are functionally identical to hand-written equivalents
- [x] Sequential chaining: stages chain within each item, items chain between each other
- [x] Edge rewriting: external edges to/from pipeline node redirect to first/last expanded node
- [x] `{item.field}` interpolation substitutes item values into stage `prompt`, `variables`, and `state_key`
- [x] Non-string stage fields (`timeout`, `temperature`, `type`) are copied verbatim, not interpolated
- [x] Lint validates: `items` has ≥ 1 entry, `stages` has ≥ 1 entry, all `{item.*}` references resolve
- [x] Lint reports error for unresolved `{item.*}` references
- [x] Pipeline expansion composes with other expansions (`expand_interactive_tools`, `apply_loop_node_defaults`)
- [ ] Expanded graph is visible via `yamlgraph graph info` (shows concrete nodes, not the template)
- [x] Unit tests: expansion logic with mock configs (varying items/stages counts)
- [x] Unit tests: edge rewriting (START→pipeline, pipeline→END, pipeline→other_node)
- [x] Unit tests: `{item.field}` interpolation including nested variables
- [ ] Integration test: ebook graph rewritten with `type: pipeline`, produces identical execution
- [x] Requirement traceability: `REQ-YG-235+` tagged on all tests
- [ ] Documentation: `reference/graph-yaml.md` updated with pipeline node type

## Alternatives Considered

### 1. Extend map node with `sequential: true` flag

Map nodes use `Send()` for runtime parallel fan-out over *data*. Pipeline templates generate static subgraph structure at *compile time*. The semantics are fundamentally different: map items share a single sub-node definition and execute in parallel; pipeline items generate distinct nodes that appear in the graph topology and execute sequentially. Overloading map would confuse the mental model.

### 2. Jinja2 `{% for %}` loops in YAML

YAML is loaded before Jinja2 is available, and mixing template directives with YAML structure creates unparseable files. The YAML must be valid YAML first; Jinja2 is used only inside string values for prompt content, not for structural generation.

### 3. Subgraph composition (type: subgraph × N)

One could define a single-chapter graph in a separate file and reference it N times via `type: subgraph`. This works but requires managing separate files, loses the single-file overview, and doesn't support item-specific variable injection without additional plumbing. Pipeline templates keep everything in one file with clear parameterization.

### 4. Runtime loop node

A runtime loop would re-execute the same nodes with different state on each iteration. This is viable but loses the static graph topology — `graph info`, visualization, and checkpointing wouldn't show individual chapters as distinct nodes. Compile-time expansion preserves full observability.

## Out of Scope

- **Cross-item dependencies**: Stages in item N that depend on results from item M (non-sequential patterns). Document as future extension path.
- **Parallel stage execution**: Running stages within an item concurrently. The current scope is strictly sequential chaining.
- **Conditional items**: Skipping items based on runtime conditions. Use router nodes after pipeline expansion for this.
- **Nested pipelines**: Pipeline templates containing other pipeline templates. Could be supported by running expansion recursively, but not in initial scope.

## Related

- **FR-049**: `expand_interactive_tools()` in `yamlgraph/interactive_tool.py` — direct precedent for compile-time node expansion
- **Map nodes**: `yamlgraph/map_compiler.py` — runtime parallel fan-out (complementary, not competing)
- **Ebook graph**: `examples/ebook/graph.yaml` — primary motivating example (377 lines, 86% boilerplate)
- **Node compiler**: `yamlgraph/node_compiler.py` — `NODE_TYPE_HANDLERS` registry (pipeline nodes are expanded before reaching this)
- **Graph loader**: `yamlgraph/graph_loader.py` — insertion point at line ~212

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted to implement.

**Evaluation:**

1. **Scope**: Clear, minimal, single-responsibility. One concern (compile-time template expansion) with well-defined out-of-scope boundaries (nested pipelines, parallel stages, conditional items).

2. **Feasibility**: Proven pattern. Follows `expand_interactive_tools()` (FR-049) step-for-step — scan, deep copy, expand, chain, rewrite edges, remove, return. All infrastructure exists.

3. **Claims verified**: All 14 factual claims confirmed against codebase — ebook boilerplate counts, naming conventions, integration points, registry patterns, map node complementarity.

4. **Acceptance criteria**: 16 criteria, all measurable with clear pass/fail conditions.

5. **Architecture alignment**: Compile-time expansion preserves the three-layer pattern. Pipeline nodes are consumed before `NODE_TYPE_HANDLERS`, matching interactive_tool precedent.

**Implementation notes (path corrections):**
- `NodeType` enum lives in `yamlgraph/constants.py`, not `graph_schema.py` (Integration Points table says `graph_schema.py`)
- Lint checks live in `yamlgraph/linter/checks.py` with patterns in `yamlgraph/linter/patterns/`, not `yamlgraph/lint.py`
- `VALID_NODE_TYPES` set in `yamlgraph/linter/checks.py` must include `"pipeline"`
- These are cosmetic path errors; the design and approach are correct
