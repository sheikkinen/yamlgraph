# FR-938 Research Route: Pass brief_path to the Committed-Context Node

Update `examples/demos/research-route/graph.yaml` so the
`collect_committed_context` node receives the brief path in addition to the
repo root.

The node currently declares:

```yaml
  collect_committed_context:
    type: python
    tool: collect_committed_context
    state_key: committed_context
    variables:
      repo_root: "."
```

Add one variable so it reads:

```yaml
  collect_committed_context:
    type: python
    tool: collect_committed_context
    state_key: committed_context
    variables:
      repo_root: "."
      brief_path: "{state.brief_path}"
```

`brief_path` is already in graph state — the `load_brief` node runs before this
node and `write_alternatives` already reads `state["brief_path"]`. The Python
tool `collect_committed_context(repo_root, brief_path)` already accepts the
second argument; this edit is the wiring only.

Do not change graph structure, node order, edges, state shape, the tool
manifest, prompt text, README, or any other node. No new node, no new state
key. This is a single-variable configuration edit.

Validate with:

```bash
yamlgraph graph lint examples/demos/research-route/graph.yaml
```

**Prior art:** `feature-requests/FR-938-prior-art-retrieval-in-research-route.md`
R-5 and R-9 freeze this edit and route it here (judgement condition C-2);
`feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`
established the node and its author-independence constraint.
