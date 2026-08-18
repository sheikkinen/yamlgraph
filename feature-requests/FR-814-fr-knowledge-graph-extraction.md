# Feature Request: FR-814 FR Knowledge Graph Extraction

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged
**Effort:** 2 days
**Requested:** 2026-08-17
**First consumer / first event:** the prior-art hook, the moment it
must answer "is this FR a duplicate?" — currently it greps prose;
with the causality graph it queries typed edges and transitive closures.

## Summary

Extract the implicit knowledge graph from the FR corpus (~723 FRs excluding
judgements, ~779 total files including judgements; 10,147 cross-references)
into a machine-queryable structure. The discrepancy: 723 = FR content files,
779 = content + judgement + legacy files in the directory. The FR system has
evolved a causal DAG embedded in prose — dependency chains, prior art,
regressions, substrate relationships — that costs 30-50% of late-FR tokens
to re-derive on every judge/enforce/review invocation.

## Value Statement

Post-judgement tools (enforce, review, inquisitor, prior-art hook) get
pre-computed causal context at 60-70% lower token cost, and the system
gains queryable dependency chains, cluster detection, and orphan identification.

## Problem

1. **Hidden structure**: 10,147 FR cross-references encode typed relationships
   (depends_on, prior_art, regression_of, substrate, spawned_by) but only in
   prose. No tool can query "what depends on FR-723?" without reading every FR.

2. **Redundant re-derivation**: Every judge session re-reads the full prose of
   cited FRs to understand causal position. The same relationships are re-parsed
   by each consumer.

3. **No transitive visibility**: FR-813 depends on FR-811 depends on FR-759.
   This transitive chain is discovered only by reading all three. No pre-computed
   closure exists.

4. **Governance cost growth**: Late FRs spend 30-50% of tokens on causal
   positioning (Prior art, First consumer, dependency declarations). This grows
   linearly with corpus size.

## Raw Output Read

N/A — this FR does not add or change a scorer/metric.

## Ideal Result

Any tool can query `knowledge_graph.yaml` for the typed causal relationships
of any FR — dependencies, dependents, prior art, regressions, clusters,
transitive closures — without loading FR prose. The graph is auto-regenerated
on FR changes. Post-judgement tools load the graph (~50KB) instead of the
prose corpus (~7.6MB).

## Proposed Solution

### Three-pass extraction pipeline

**Pass 1: Structural extraction (Python, zero LLM cost)**

```python
# scripts/extract_fr_graph.py
# For each FR:
#   1. Parse metadata (status, priority, type, date)
#   2. Extract all FR-XXX references with section context
#   3. Apply heuristic edge typing based on section + keyword proximity
```

Edge taxonomy (R-4: partitioned into causal vs associative):

Causal edges (form DAG, support cycle detection and transitive closure):
- `depends_on`: "blocked until" / "dependency" / "depends on"
- `regression_of`: "regression" within 50 chars of FR ref in ## Problem
- `spawned_by`: "Seed origin" / "Parent plan"
- `substrate`: "substrate" / "built on" / "consumes contracts from"
- `supersedes`: "supersedes" / "replaces"

Associative edges (metadata only, no DAG/closure computation):
- `prior_art`: `## Related` / `## Prior art` / `**Prior art:**`
- `first_consumer_of`: Front-matter `First consumer` referencing another FR
- `mentions`: Any FR reference not matching above rules

Each edge preserves evidence: source FR, target FR, section context, line
number, rule ID that fired, confidence (1.0 for exact keyword, 0.7 for
proximity heuristic), and explicit vs inferred flag.

**Pass 2: LLM classification — OUT OF SCOPE**

Deferred to a future FR. This FR authorizes only heuristic extraction.

**Pass 3: Graph construction and validation (Pass 2 in implementation)**

- Build DAG from causal edges only (depends_on, regression_of, spawned_by,
  substrate, supersedes)
- Detect cycles (report exact chain and edge evidence)
- Compute transitive closures over causal edges
- Identify clusters (connected components = "feature arcs")
- Output: `reference/fr-knowledge-graph.yaml` (deterministic: stable sort,
  corpus fingerprint from source file hashes, no timestamps in committed content)

### Output schema

```yaml
# reference/fr-knowledge-graph.yaml
meta:
  schema_version: 1
  corpus_fingerprint: "sha256:<hash-of-sorted-source-file-hashes>"
  fr_count: 723
  edge_count: ~1200
  clusters: ~45

nodes:
  FR-813:
    status: enforced
    priority: high
    type: bug
    requested: 2026-08-17
    cluster: otel-observability

edges:
  - source: FR-813
    target: FR-811
    type: regression_of
    causal: true
    confidence: 0.95
    section: "## Problem"
    line: 15
    rule: "regression_keyword_proximity"
  - source: FR-813
    target: FR-759
    type: substrate
    causal: true
    confidence: 0.85
    transitive: true

closures:
  FR-813: [FR-811, FR-759]  # transitive causal dependencies

clusters:
  otel-observability:
    members: [FR-759, FR-811, FR-813]
    root: FR-759
```

### Integration points (first consumer only — others deferred)

1. **Prior-art hook**: `.github/hooks/scripts/checks/prior_art.py` augmented
   with graph-backed lookup. Preserves: newly-created-FR-only scope
   (`.github/hooks/scripts/checks/fr-checks.sh`), staged `**Prior art:**`
   marker semantics (`prior_art_gate.py`), silence-over-noise when no rare
   signal exists. Missing/stale graph → clear diagnostic, never silent fallback.

Deferred to future FRs: judge/enforce/review context loading, inquisitor
orphan detection, `yamlgraph fr deps` CLI command.

### Regeneration

`python scripts/extract_fr_graph.py` on any `feature-requests/*.md` change.
Output is committed. Determinism enforced: corpus fingerprint = SHA-256 of
sorted source file content hashes. Running twice on unchanged corpus produces
zero diff. Staleness gate: CI/pre-commit checks fingerprint matches; stale →
fail with diagnostic naming changed files.

### Validation fixture (R-1)

A committed fixture at `tests/fixtures/fr_graph_validation.yaml` containing
20+ manually labelled FR references with expected edge types. Accuracy formula:
`correct_typed / (total - ambiguous)` where ambiguous edges are reported
separately. Target: >85%.

## Acceptance Criteria

- [ ] AC-01: `scripts/extract_fr_graph.py` deterministically generates `reference/fr-knowledge-graph.yaml`; running twice on unchanged corpus produces no diff
- [ ] AC-02: Generated YAML validates against documented schema (corpus fingerprint, schema version, nodes, explicit edges with evidence/rule/confidence, inferred closures separated, clusters)
- [ ] AC-03: Committed validation fixture (20+ labelled refs) proves >85% accuracy; ambiguous edges reported separately
- [ ] AC-04: Cycle detection runs only over causal edge types; cycles report exact chain and evidence; associative edges excluded from DAG
- [ ] AC-05: Stale-output test fails when FR files change without regeneration
- [ ] AC-06: Prior-art hook consumes graph for lookup, preserving newly-created-FR scope, staged marker behavior, and silence-over-noise semantics
- [ ] AC-07: Missing/stale graph produces clear diagnostic, not silent fallback
- [ ] AC-08: `reference/fr-knowledge-graph.md` documents schema, taxonomy, regeneration, and hook usage
- [ ] AC-09: Tests marked with `@pytest.mark.req(...)`, req coverage closes, changelog + diary included

## Alternatives Considered

1. **LLM-only extraction**: Send each FR to LLM for full classification.
   Rejected: ~$5 cost, unnecessary for formulaic prose where section context
   is a strong signal.

2. **Embedded vector search**: Embed FRs and find similar ones.
   Rejected: similarity ≠ causality. "Similar" misses the typed edge
   (depends_on vs regression_of vs prior_art distinction).

3. **Manual curation**: Human labels edges.
   Rejected: 10,147 references, not scalable. Heuristics + spot-check is
   the right cost/accuracy tradeoff.

4. **No extraction, compress prose instead**: Just make FRs shorter.
   Rejected: loses the relational structure that IS the value. Compression
   without extraction discards the graph.

## Related

**Prior art:** The current prior-art hook (`.github/hooks/scripts/checks/prior_art.py`)
uses filename-noun extraction and corpus frequency scoring. FR-814 augments this
with typed graph edges — it does not replace the existing retrieval for cases where
the graph is absent/stale. FR-723, FR-807, FR-808 are cited as examples of high-connectivity
hub nodes that demonstrate the value of pre-computed edges, not as duplicates or
dependencies of this FR.

- Diary: `docs/diary/diary-2026-08-17-fr-corpus-as-token-economics.md`
- Prior art hook: `.github/hooks/scripts/checks/fr-checks.sh`, `.github/hooks/scripts/checks/prior_art.py`, `.github/hooks/scripts/checks/prior_art_gate.py`
- FR-723: Route evidence (example hub node)
- FR-807/FR-808: Example deep dependency chain (regulated profile arc)

## Judgement (2026-08-17)

**Verdict:** APPROVED WITH REVISIONS — see `FR-814-fr-knowledge-graph-extraction.judgement.md`

Revisions R-1 through R-6 folded into this FR above.
