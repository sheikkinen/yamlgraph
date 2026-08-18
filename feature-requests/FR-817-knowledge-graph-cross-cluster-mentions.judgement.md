# Judgement: FR-817 Knowledge Graph Cross-Cluster Mention Report (DRAFT)

**Verdict:** APPROVED WITH REVISIONS — the weak-tie report is a sound, single-purpose child of the split FR-815, but authority activates only after the FR specifies the deduplicated extraction source, deterministic schema/count semantics, and concrete tests.

**Reviewed against:** `feature-requests/FR-817-knowledge-graph-cross-cluster-mentions.md`; cited predecessor `feature-requests/FR-814-fr-knowledge-graph-extraction.md`; cited predecessor judgement `feature-requests/FR-814-fr-knowledge-graph-extraction.judgement.md`; cited parent `feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.md`; cited parent judgement `feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.judgement.md`; cited implementation surface `scripts/extract_fr_graph.py`; cited graph artifact `reference/fr-knowledge-graph.yaml`; cited schema docs `reference/fr-knowledge-graph.md`; current tests `tests/unit/test_fr_graph.py`; repo doctrine `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, and `.github/copilot-instructions.md`.

## What is sound

The problem is real and already evidenced by the committed artifact. FR-817 says FR-814 excluded all `mentions` edges for size (`feature-requests/FR-817-knowledge-graph-cross-cluster-mentions.md:23-28`), and the generated graph records `mentions_excluded: 1610` while keeping the artifact at 1,662 retained edges and 65 clusters (`reference/fr-knowledge-graph.yaml:1-8`). The current writer excludes every `mentions` edge before emitting the compact graph (`scripts/extract_fr_graph.py:398-425`), so a filtered weak-tie report is a precise recovery of signal that FR-814 intentionally dropped.

The scope is now single-responsibility. FR-815 was split because it bundled cluster naming, cross-cluster mentions, and judge context narrowing (`feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.judgement.md:17-25`); FR-817 carries only the second concern (`feature-requests/FR-817-knowledge-graph-cross-cluster-mentions.md:12-16`, `:82-89`). It does not require graph/prompt authoring, judge adapter changes, or hook rewrites.

The implementation is feasible in the existing extractor. `extract_graph()` builds `unique_edges`, computes clusters, creates `node_cluster_map`, and assigns each clustered node a `cluster` field (`scripts/extract_fr_graph.py:343-369`). That is exactly the data needed to filter `mentions` edges whose endpoints have different cluster IDs. The committed graph already stores cluster IDs on nodes and a `clusters` map (`reference/fr-knowledge-graph.yaml:55`, `:15674-15767`), and the docs define `mentions` as the weak-link associative edge type (`reference/fr-knowledge-graph.md:62-73`).

Strategic classification: repo-governance artifact enrichment. It is not a public YAMLGraph framework API, but it improves the committed governance index used by prior-art and research flows. The first consumer is named, and the change is smaller than restoring all mentions or changing downstream judge context (`feature-requests/FR-817-knowledge-graph-cross-cluster-mentions.md:8-16`, `:76-80`).

## Required revisions

### R-1: Define the extraction source as deduplicated internal mention edges

Replace the proposed `all_edges` wording/code with a requirement to filter the post-deduplication edge set used by `graph["edges"]`. FR-817's sketch filters `all_edges` (`feature-requests/FR-817-knowledge-graph-cross-cluster-mentions.md:38-49`), but the extractor deduplicates raw references into `unique_edges` before graph construction (`scripts/extract_fr_graph.py:343-350`) and only then passes those edges to the writer (`scripts/extract_fr_graph.py:373-386`). Filtering raw `all_edges` can reintroduce duplicate mention records and make the emitted count diverge from the graph's edge semantics.

The folded FR must state: `cross_cluster_mentions` is derived from the same deduplicated edge set as `graph["edges"]`, before the writer removes normal `mentions` edges from the main `edges` section.

### R-2: Freeze schema, ordering, and count semantics

Define the emitted section mechanically. The current FR gives the rough shape (`feature-requests/FR-817-knowledge-graph-cross-cluster-mentions.md:56-65`) but does not state whether `count` is authoritative, how edges are ordered, or whether endpoints must be validated against `nodes`. Fold this contract into the FR:

```yaml
cross_cluster_mentions:
  count: <len(edges)>
  edges:
    - {s: FR-XXX, t: FR-YYY, ln: 123}
```

Edges must be sorted deterministically by `(s, t, ln)`. `count` must equal `len(edges)`. Every edge must originate from a `mentions` edge, both `s` and `t` must exist in `nodes`, both nodes must have a `cluster`, and those cluster values must differ. If the current corpus has excluded mentions but the filter emits zero cross-cluster mentions, the extractor must fail with a diagnostic rather than substituting all mentions or emitting a success-shaped empty report; repo doctrine forbids hidden substitute-everything behavior (`.github/copilot-instructions.md:218`).

### R-3: Make the size budget and docs update explicit

Keep the artifact-size guard tied to the exact committed output, not an estimate. FR-817 states expected volume `<500 edges` and requires total size `<500KB` (`feature-requests/FR-817-knowledge-graph-cross-cluster-mentions.md:30-34`, `:67-74`), but the implementation must assert those after writing `reference/fr-knowledge-graph.yaml`, because the current schema docs still describe only `meta`, `nodes`, `edges`, `closures`, `clusters`, and optional `cycles` (`reference/fr-knowledge-graph.md:11-48`). The folded FR must require `reference/fr-knowledge-graph.md` to document `cross_cluster_mentions`, its compact field names, its relation to `mentions_excluded`, and the size/count guards.

### R-4: Replace broad acceptance prose with direct tests

AC-05 says only that a test validates the cross-cluster property (`feature-requests/FR-817-knowledge-graph-cross-cluster-mentions.md:69-74`). The folded FR must name the test obligations directly: a fixture or unit test that proves cross-cluster mentions are included, same-cluster mentions are excluded, isolated/unclustered endpoints are excluded, duplicate raw references do not duplicate emitted edges, ordering is deterministic, `count == len(edges)`, emitted count is `<500`, and the generated artifact is `<500KB`. Tests must carry requirement markers under the local traceability rule (`.github/copilot-instructions.md:173-176`), and implementation decisions must be reflected in the FR because the FR is the source of truth (`.github/copilot-instructions.md:33-35`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `scripts/extract_fr_graph.py`: derive and emit `cross_cluster_mentions` from deduplicated mention edges and existing cluster assignments |
| D-2 | `reference/fr-knowledge-graph.yaml`: regenerated committed artifact with the new compact section |
| D-3 | `reference/fr-knowledge-graph.md`: schema and regeneration docs for the new section |
| D-4 | `tests/unit/test_fr_graph.py` and/or `tests/fixtures/fr_graph_validation.yaml`: focused tests for filtering, determinism, count, and size |
| D-5 | FR implementation-status update, requirement traceability if needed, changelog fragment, and diary reflection required by repo doctrine |

Not authorized under FR-817: restoring all `mentions` edges to the main `edges` list; changing causal edge taxonomy; changing cluster construction or naming; modifying judge adapter graph/prompt/doctrine; changing prior-art hook behavior; adding a CLI; creating or modifying `graph.yaml` or `prompts/*.yaml`; changing unrelated generated-artifact gates; implementing FR-816 or FR-818 concerns.

## Revised acceptance criteria

- [ ] AC-01: `reference/fr-knowledge-graph.yaml` contains `cross_cluster_mentions` with `count` and compact `edges` entries shaped exactly as `{s, t, ln}`.
- [ ] AC-02: `cross_cluster_mentions.edges` is derived from the deduplicated internal `mentions` edge set, not raw pre-deduplication references.
- [ ] AC-03: For every emitted edge, `s` and `t` exist in `nodes`, both have `cluster` values, and `nodes[s].cluster != nodes[t].cluster`; unclustered endpoints are excluded.
- [ ] AC-04: `cross_cluster_mentions.count == len(cross_cluster_mentions.edges)`, edges are sorted deterministically by `(s, t, ln)`, and running the extractor twice on an unchanged corpus produces no diff.
- [ ] AC-05: Normal `mentions` edges remain excluded from the main `edges` list; non-mention edge emission, closures, and clusters retain their existing schema.
- [ ] AC-06: The emitted cross-cluster mention count is `<500`, and the written `reference/fr-knowledge-graph.yaml` remains `<500KB`.
- [ ] AC-07: Tests prove inclusion of cross-cluster mentions, exclusion of same-cluster mentions, exclusion of unclustered endpoints, duplicate suppression, deterministic ordering, count equality, and size budget.
- [ ] AC-08: `reference/fr-knowledge-graph.md` documents the new section, field meanings, regeneration behavior, and relation to `mentions_excluded`.
- [ ] AC-09: Tests are marked with `@pytest.mark.req(...)`; requirement/capability updates are included if needed; the FR records implementation decisions; changelog and diary artifacts are included as required by repo gates.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 into `feature-requests/FR-817-knowledge-graph-cross-cluster-mentions.md` before implementation authority activates. | GATE |
| C-2 | Do not derive `cross_cluster_mentions` from raw pre-deduplication `all_edges`; use the deduplicated edge set that underlies `graph["edges"]`. | GATE |
| C-3 | Do not emit same-cluster, unclustered, or non-`mentions` edges in `cross_cluster_mentions`. | GATE |
| C-4 | Do not exceed `<500` emitted cross-cluster mentions or `<500KB` total artifact size. | GATE |
| C-5 | Do not modify judge adapter, prior-art hook behavior, cluster naming, graph/prompt artifacts, or CLI surfaces under this authority. | GATE |

Authority granted: after the required revisions are folded into the FR, the enforcer may implement the deterministic cross-cluster mention report in the extractor, generated artifact, schema docs, and focused tests within the frozen surfaces above.
