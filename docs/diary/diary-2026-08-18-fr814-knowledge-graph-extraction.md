# Diary: FR-814 Knowledge Graph Extraction

**Date:** 2026-08-18
**FR:** FR-814
**Context:** Enforcing the FR knowledge graph extraction

## Trap encountered: inverse_prerequisite

The initial extractor misclassified "prerequisite for FR-X" and
"depends on this FR" as the source depending on the target. The
semantic direction was reversed — these phrases mean the TARGET
depends on the SOURCE.

**Cure applied:** Added explicit inverse-signal detection before
the causal keyword match. Two patterns ("prerequisite for", "depends
on this") now short-circuit to `mentions` classification.

## Insight: cycles as genealogy signal

4 genuine mutual-dependency cycles remain (co-developed FR pairs like
FR-573/574, FR-761/762). These aren't classifier errors — they're
evidence of FRs that should have been a single FR or were deliberately
split for scheduling. The cycle report is a genealogy diagnostic, not
a quality defect.

## Metrics

- 684 FRs parsed (excluding judgements)
- 3,272 unique edges extracted
- 210 causal edges forming the DAG
- 65 connected clusters
- 4 genuine cycles (documented mutual dependencies)
- >85% accuracy on 20-reference validation fixture

## Phase 2: FR-816/FR-817 (cluster naming + cross-cluster mentions)

**Date:** 2026-08-18

### Trap: phantom cluster members

The cross-cluster mention filter passed nodes that existed in the DAG
(as edge targets) but had no `.md` file and therefore no entry in the
`nodes` dict. The test caught it: FR-105 was in a cluster but had
`cluster=None` in the written output. Fix: require both endpoints to
exist in `nodes` AND have cluster assignments.

### Insight: cluster naming quality

Auto-naming from filename nouns produces decent results for technical
clusters (`dependency-route-boundary`, `api-discovery-step`) but weak
results for creative/domain clusters (`fandom-novel-canon`). The naming
algorithm is a 80/20 solution — good enough for diagnostics, not
publication quality.

### Metrics (phase 2)

- Schema upgraded to v2 (clusters as objects with name + members)
- 65 clusters named, 0 collisions
- 174 cross-cluster mentions (well under 500 cap)
- Artifact size: 265KB (under 500KB)
- 29 tests total (12 new for FR-816/FR-817)

### Seed

The cross-cluster mentions are the "bridging" FRs — the ones that
connect distant feature arcs. Could a "bridge score" (ratio of
cross-cluster to same-cluster edges) identify FRs that are
architectural pivots vs implementation details?
