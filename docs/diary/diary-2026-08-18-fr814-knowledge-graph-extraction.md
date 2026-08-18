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

## Seed

The cluster detection names groups numerically (cluster-1, cluster-2).
Could the clusters be auto-named from their member FRs' shared nouns?
"otel-observability" is more useful than "cluster-47". And: now that
the graph exists, can the judge pre-load only the cluster's FRs
instead of grepping the full corpus for prior art?
