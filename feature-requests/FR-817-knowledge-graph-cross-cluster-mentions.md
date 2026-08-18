# Feature Request: FR-817 Knowledge Graph Cross-Cluster Mention Report

**Priority:** LOW
**Type:** Enhancement
**Status:** Enforced 2026-08-18
**Effort:** 0.5 days
**Requested:** 2026-08-18
**First consumer / first event:** the prior-art hook or a researcher
querying "which FRs bridge distinct feature arcs?" — currently invisible
because FR-814 excluded all 1,610 `mentions` edges for file size.

## Summary

Add a `cross_cluster_mentions` section to the knowledge graph artifact
containing only `mentions` edges where source and target belong to
different clusters. These are the weak ties connecting distant feature arcs.

## Value Statement

Cross-cluster mentions surface hidden relationships between feature arcs
that noun-frequency retrieval and same-cluster prior-art miss entirely.

## Problem

FR-814 excluded 1,610 `mentions` edges to keep the artifact under 500KB.
But mentions between clusters are high-signal weak ties: FR-A in the
observability arc mentioning FR-B in the dependency-governance arc reveals
a cross-cutting concern invisible to cluster-scoped tools.

## Ideal Result

`reference/fr-knowledge-graph.yaml` has a `cross_cluster_mentions` section
containing only edges where source and target are in different clusters.
Expected volume: <500 edges (small subset of 1,610 total).

## Proposed Solution

In `scripts/extract_fr_graph.py`, after cluster assignment, filter the
full `mentions` edge set:

```python
cross = [
    {"s": e["source"], "t": e["target"], "ln": e["line"]}
    for e in all_edges
    if e["type"] == "mentions"
    and node_cluster_map.get(e["source"]) != node_cluster_map.get(e["target"])
    and e["source"] in node_cluster_map
    and e["target"] in node_cluster_map
]
```

Only edges where BOTH source and target have cluster assignments AND those
clusters differ are included. FRs without cluster membership (isolates) are
excluded — they have no cluster context to bridge.

Schema:
```yaml
cross_cluster_mentions:
  count: 247
  edges:
    - {s: FR-723, t: FR-761, ln: 45}
    - {s: FR-808, t: FR-573, ln: 12}
```

Compact format (s, t, ln only) to stay within size budget.

## Acceptance Criteria

- [ ] AC-01: `cross_cluster_mentions` section present in generated graph
- [ ] AC-02: Every edge in the section has source and target in different clusters
- [ ] AC-03: Edge count < 500
- [ ] AC-04: Total artifact size remains < 500KB
- [ ] AC-05: Test validates cross-cluster property for all emitted edges
- [ ] AC-06: Docs updated, changelog, diary, req traceability

## Alternatives Considered

1. **Restore all mentions**: Rejected — exceeds 500KB size limit.
2. **Separate artifact**: Rejected — one graph file is simpler; the filtered
   subset is small enough to fit.

## Related

**Prior art:** FR-814 (Enforced) excluded mentions for size; this FR recovers
the high-signal subset. FR-815 (Split) bundled this with two other concerns.
No other FRs address cross-cluster relationships.

- FR-814: Knowledge graph extraction (Enforced, predecessor)
- FR-815: Knowledge graph phase 2 (Split, parent)
