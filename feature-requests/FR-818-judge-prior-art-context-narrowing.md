# Feature Request: FR-818 Judge Prior-Art Context Narrowing via Knowledge Graph

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-18
**First consumer / first event:** the judge copilot node, the moment it
processes a new FR whose cluster has >5 members — currently the judge
prompt instructs it to read cited evidence and repo doctrine; with graph
context it also receives a pre-computed list of causally related FRs,
reducing discovery from full-corpus search to targeted reads.

## Summary

Augment the judge adapter's pre-processing (the `scripts/judge.sh` wrapper)
to inject the new FR's transitive closure and cluster members as context
into the judge prompt variables, so the copilot node receives structured
prior-art context without scanning the full corpus.

## Value Statement

Judge sessions get targeted prior-art context (3-10 FRs from the closure)
instead of relying on the copilot node's own corpus discovery, reducing
token cost and improving prior-art coverage for deeply connected FRs.

## Problem

The judge adapter (`.github/skills/judge-fr/adapters/graph.yaml`) is a
single copilot node that receives `fr_path` as input. The prompt
(`.github/skills/judge-fr/adapters/prompts/judge.yaml`) instructs the
copilot to read the FR, cited evidence, and repo doctrine. Prior-art
discovery is left to the copilot's own search — which means it greps or
reads files ad hoc, with no guarantee of finding causally related FRs
that aren't explicitly cited.

FR-814's knowledge graph provides pre-computed transitive closures and
cluster membership. The judge wrapper (`scripts/judge.sh`) can query the
graph and inject this as an additional variable, so the copilot starts
with structured context.

## Ideal Result

`scripts/judge.sh` queries `reference/fr-knowledge-graph.yaml` for the
new FR's causal ancestors and cluster siblings, formats them as a
structured context block, and passes it as a variable to the judge graph.
The copilot node receives this as part of its input, uses it for prior-art
disposition, and produces better-targeted findings.

## Proposed Solution

### 1. Graph query in judge.sh

```bash
# In scripts/judge.sh, before invoking the graph:
GRAPH_CONTEXT=$(python scripts/extract_fr_graph.py --context "$FR_PATH" 2>/dev/null || echo "")
```

Add `--context FR_PATH` mode to `extract_fr_graph.py` that:
1. Parses the FR-ID from the filename
2. Looks up transitive closure in the committed graph
3. Looks up cluster membership and cluster siblings
4. Outputs a formatted context block (markdown or YAML)

### 2. Pass as variable to the judge graph

```bash
yamlgraph graph run .github/skills/judge-fr/adapters/graph.yaml \
  --var fr_path="$FR_PATH" \
  --var graph_context="$GRAPH_CONTEXT" \
  --full
```

### 3. Prompt integration

Add `graph_context` to the judge prompt as optional context:

```yaml
# In judge.yaml prompt, add:
{% if graph_context %}
## Pre-computed prior-art context (from FR knowledge graph)
{{ graph_context }}
{% endif %}
```

### Fallback behavior

- Missing/stale graph: `--context` emits empty string, prompt section omitted
- Diagnostic on stderr when graph is absent: "⚠ FR knowledge graph not found"
- No silent degradation: the judge still works, just without pre-computed context

## Acceptance Criteria

- [ ] AC-01: `extract_fr_graph.py --context <fr-path>` outputs structured context for the FR's closure and cluster
- [ ] AC-02: `scripts/judge.sh` passes `graph_context` variable to the judge graph
- [ ] AC-03: Judge prompt includes graph context when available, omits when empty
- [ ] AC-04: Missing/stale graph produces diagnostic on stderr, empty context, judge proceeds normally
- [ ] AC-05: Fixture test: named FR with known closure produces expected context output
- [ ] AC-06: Human review of judge adapter changes (enforcement infrastructure gate)
- [ ] AC-07: Tests with req traceability, changelog, diary

## Alternatives Considered

1. **Modify the judge adapter graph to add a pre-processing node**: Rejected —
   the adapter is a single copilot node by design; adding nodes changes its
   architecture. The wrapper script is the right pre-processing surface.

2. **Inject context via system prompt or file**: Rejected — variables are the
   established mechanism for passing data to graph runs.

3. **Have the copilot node query the graph itself**: Rejected — the copilot
   node already reads files; adding graph-query logic to its prompt increases
   complexity. Pre-computing in the wrapper is simpler.

## Related

**Prior art:** FR-814 (Enforced) created the knowledge graph and closures this
FR consumes. FR-815 (Split) bundled this with cluster naming and cross-cluster
mentions; this FR is the judge-narrowing slice. FR-815 judgement R-2 identified
that the adapter is a single copilot node, not a multi-step pipeline — this FR
corrects that premise by targeting the wrapper script instead.

- FR-814: Knowledge graph extraction (Enforced, substrate)
- FR-815: Knowledge graph phase 2 (Split, parent)
- FR-815 judgement R-2: Adapter premise correction
