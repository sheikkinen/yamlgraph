# Feature Request: FR-816 Knowledge Graph Cluster Display Names

**Priority:** LOW
**Type:** Enhancement
**Status:** Enforced 2026-08-18
**Effort:** 0.5 days
**Requested:** 2026-08-18
**First consumer / first event:** a diary entry or FR referencing a cluster —
currently writes `cluster-20`, which is meaningless; with semantic names
writes `observability-evidence-route`, which is self-documenting.

## Summary

Add a `name` display field to each cluster in the knowledge graph artifact,
derived from shared filename nouns of cluster members. Stable `cluster-N` IDs
are preserved as keys.

## Value Statement

Cluster references in diary, FR, and diagnostic output become self-documenting
without requiring lookup of member lists.

## Problem

FR-814 outputs 65 clusters keyed as `cluster-1` through `cluster-65`. These
are stable and deterministic but semantically opaque. The largest cluster
(23 members including FR-723, FR-808) is `cluster-20` — a human reading the
graph artifact or a diary citing it cannot infer the domain without opening
the member list.

## Ideal Result

Each cluster entry in `reference/fr-knowledge-graph.yaml` has a `name` field
derived from its members' filename nouns, while the key remains `cluster-N`
for stable machine references.

## Proposed Solution

Add a `name_cluster` function to `scripts/extract_fr_graph.py`:

```python
def name_cluster(members: list[str], fr_files: dict[str, Path]) -> str:
    from collections import Counter
    nouns = []
    for fr_id in members:
        if fr_id in fr_files:
            nouns.extend(extract_nouns(fr_files[fr_id].name))
    counts = Counter(nouns)
    top = [n for n, _ in counts.most_common(3)]
    name = "-".join(top) if top else "unnamed"
    return name
```

Output change (additive only):
```yaml
clusters:
  cluster-20:
    name: observability-evidence-route
    members: [FR-006, FR-060, ...]
```

Collision handling: if two clusters produce the same name, append `-N`
where N is the cluster's numeric suffix (e.g., `checkpoint-state-5`).

Stopwords reuse: import `STOPWORDS` and `extract_nouns` from
`.github/hooks/scripts/checks/prior_art.py` or duplicate the minimal
set in the extractor.

## Acceptance Criteria

- [ ] AC-01: Each cluster in the output has a `name` field derived from member filename nouns
- [ ] AC-02: Cluster keys remain `cluster-N` (no migration)
- [ ] AC-03: Naming is deterministic: same members → same name
- [ ] AC-04: Collisions resolved by appending cluster numeric suffix
- [ ] AC-05: Test validates naming for ≥3 known clusters
- [ ] AC-06: `reference/fr-knowledge-graph.md` updated with name field documentation
- [ ] AC-07: Tests with `@pytest.mark.req`, changelog, diary

## Alternatives Considered

1. **Replace keys with semantic names**: Rejected per FR-815 judgement R-3 —
   breaks stable references without migration contract.
2. **LLM-based naming**: Rejected — filename nouns are sufficient and deterministic.

## Related

**Prior art:** FR-814 (knowledge graph extraction, Enforced) created the cluster
output this FR enriches. FR-815 (Split) bundled this with two other concerns;
this FR is the cluster-naming slice. FR-724, FR-295, FR-369, FR-248 share "phase2"
noun only — unrelated domains.

- FR-814: Knowledge graph extraction (Enforced, predecessor)
- FR-815: Knowledge graph phase 2 (Split, parent)
