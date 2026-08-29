---
type: feat
scope: governance
req: REQ-YG-601
---
- **FR-814 FR Knowledge Graph Extraction**: Deterministic extraction of typed causal/associative edges from the FR corpus into `reference/fr-knowledge-graph.yaml`. Supports cycle detection, transitive closures, cluster identification, and staleness gating. Prior-art hook augmented with graph-backed cluster boost. (REQ-YG-601)
- **FR-816 Cluster Display Names**: Semantic cluster names derived from member filename nouns (schema v2). Stable `cluster-N` keys preserved. (REQ-YG-602)
- **FR-817 Cross-Cluster Mentions**: Weak-tie report of mention edges crossing cluster boundaries (178 edges). (REQ-YG-603)
