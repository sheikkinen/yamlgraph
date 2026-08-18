# Feature Request: FR-815 Knowledge Graph Phase 2 — Cluster Naming and Judge Context Narrowing

**Priority:** MEDIUM
**Type:** Feature
**Status:** Split — see judgement; replaced by FR-816 (cluster naming), FR-817 (cross-cluster mentions), FR-818 (judge context narrowing)
**Effort:** 1.5 days
**Requested:** 2026-08-18
**First consumer / first event:** the judge adapter, the moment it
loads prior-art context for a new FR — currently greps the full corpus
(~7.6MB); with closure-based loading it reads only the causal ancestors
(~50KB), a 150× context reduction per judgement.

## Summary

Phase 2 of the FR knowledge graph (FR-814): auto-name clusters from
member nouns, add cross-cluster mention edges as weak-tie report, and
narrow the judge adapter's prior-art context loading to use transitive
closures instead of full-corpus grep.

## Value Statement

Judge sessions get 150× smaller context loads for prior-art disposition,
cluster names become human-readable for diagnostics and diary references,
and cross-cluster mentions surface hidden relationships the current
noun-frequency retrieval misses.

## Problem

1. **Anonymous clusters**: FR-814 outputs `cluster-20`, `cluster-47` —
   numerically ordered, semantically meaningless. The largest cluster (23
   members including FR-723, FR-808) should be named
   `observability-evidence-route`, not `cluster-20`.

2. **Full-corpus judge context**: The judge adapter loads cited FRs by
   reading full prose files. With FR-814's transitive closures, it could
   load only the 3-5 causal ancestors of a new FR instead of grepping 684
   files. Current cost: ~7.6MB of context tokens. Possible cost: ~50KB.

3. **Lost weak ties**: FR-814 excluded 1,610 `mentions` edges to stay
   under 500KB. But cross-cluster mentions (FR-A in cluster-X mentions
   FR-B in cluster-Y) are the weak ties that connect distant arcs. These
   are small in number and high in signal.

## Ideal Result

Clusters have semantic names derived from their members. The judge loads
only the transitive closure's FRs for prior-art context. Cross-cluster
mentions are surfaced as a separate report section in the graph artifact.

## Proposed Solution

### 1. Cluster auto-naming

Extract filename nouns from all members of each cluster, rank by
frequency within the cluster, take top 2-3 nouns as the cluster name:

```python
def name_cluster(members: list[str], fr_files: dict[str, Path]) -> str:
    nouns = []
    for fr_id in members:
        if fr_id in fr_files:
            nouns.extend(extract_nouns(fr_files[fr_id].name))
    # Most common nouns within this cluster
    counts = Counter(nouns)
    top = [n for n, _ in counts.most_common(3)]
    return "-".join(top) or "unnamed"
```

Output: `clusters` section uses semantic names as keys instead of
`cluster-N`.

### 2. Cross-cluster mention report

Filter the excluded `mentions` edges: keep only those where source and
target are in different clusters. Add as a separate `cross_cluster_mentions`
section in the graph output.

Expected volume: ~200-400 edges (small subset of 1,610 total mentions).

### 3. Judge context narrowing

Modify the judge adapter's evidence-loading step to:
1. Parse the new FR's ID
2. Look up its cluster in the knowledge graph
3. Load transitive closure FRs as primary prior-art context
4. Fall back to full-corpus grep only if the graph is absent/stale

**Integration surface**: `.github/skills/judge-fr/adapters/` — the judge
graph's evidence-loading node or its pre-processing step.

**Prior art:** The judge adapter currently receives `fr_path` as input and
reads cited evidence files directly. The narrowing adds a pre-filter: "which
FRs are causally related?" answered by the graph, before "what do they say?"
answered by reading the files.

## Acceptance Criteria

- [ ] AC-01: Clusters in `reference/fr-knowledge-graph.yaml` use semantic names derived from member filename nouns
- [ ] AC-02: Cluster names are deterministic (same members → same name; name collisions resolved by appending member count)
- [ ] AC-03: `cross_cluster_mentions` section in graph output contains only mentions where source and target are in different clusters
- [ ] AC-04: Cross-cluster mention count is <500 (subset of 1,610 excluded mentions)
- [ ] AC-05: Judge adapter loads transitive closure FRs for prior-art context when graph is available
- [ ] AC-06: Judge falls back to existing behavior when graph is absent/stale — no silent degradation, diagnostic emitted
- [ ] AC-07: Existing judge accuracy preserved: re-judge 3 recent FRs, compare findings
- [ ] AC-08: Tests, REQ traceability, changelog, diary

## Alternatives Considered

1. **LLM-based cluster naming**: Send member titles to LLM for semantic naming.
   Rejected: filename nouns are sufficient and deterministic; LLM adds cost
   and non-determinism for marginal quality gain.

2. **Full mentions restoration**: Keep all 1,610 mentions in the graph.
   Rejected: file size exceeds 500KB limit. Cross-cluster filter preserves
   the high-signal subset.

3. **Replace judge grep entirely**: Remove noun-frequency retrieval.
   Rejected: the graph may be stale; noun-frequency is the fallback.
   Both signals compose (graph for structured relations, nouns for lexical
   similarity).

## Related

**Prior art:** FR-814 (knowledge graph extraction, Enforced) is the direct
predecessor. This FR extends its output and adds the first downstream
consumer (judge adapter). FR-737/FR-738 (prior-art hook) established the
noun-frequency retrieval that this FR augments, not replaces.
FR-724, FR-295, FR-369, FR-248 share "phase2" in name only — unrelated domains.

- FR-814: Knowledge graph extraction (Enforced)
- FR-737/FR-738: Prior-art hook and gate
- Diary: `docs/diary/diary-2026-08-17-fr-corpus-as-token-economics.md`
- Diary: `docs/diary/diary-2026-08-18-fr814-knowledge-graph-extraction.md`
