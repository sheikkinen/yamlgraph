# Judgement: FR-816 Knowledge Graph Cluster Display Names (DRAFT)

**Verdict:** APPROVED WITH REVISIONS — the split-out cluster-naming slice is real and correctly preserves stable cluster IDs, but authority activates only after the FR admits the schema-shape change, updates the current graph consumer, and pins the naming algorithm with exact fixture expectations.

**Reviewed against:** `feature-requests/FR-816-knowledge-graph-cluster-display-names.md`; cited predecessor `feature-requests/FR-814-fr-knowledge-graph-extraction.md`; cited predecessor judgement `feature-requests/FR-814-fr-knowledge-graph-extraction.judgement.md`; cited split parent `feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.md`; cited split-parent judgement `feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.judgement.md`; cited prior-art FRs `feature-requests/FR-724-icpc2-process-codes-phase2.md`, `feature-requests/FR-295-watcher-fsm-phase2-single-worker-validation.md`, `feature-requests/FR-369-fsm-snapshot-hooks-phase2-subclassing.md`, and `feature-requests/FR-248-a2a-consumer-agent-card-skill-streaming.md`; current extractor `scripts/extract_fr_graph.py`; current graph consumer `.github/hooks/scripts/checks/prior_art.py`; generated artifact `reference/fr-knowledge-graph.yaml`; schema docs `reference/fr-knowledge-graph.md`; validation tests `tests/unit/test_fr_graph.py`; fixture `tests/fixtures/fr_graph_validation.yaml`; repo doctrine `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, and `.github/copilot-instructions.md`.

## What is sound

The problem is real and narrow. FR-816 names a concrete first event: diary or FR prose currently has to cite opaque IDs like `cluster-20`, while a semantic display name would make that reference self-documenting (`feature-requests/FR-816-knowledge-graph-cluster-display-names.md:8-16`). The current generated artifact confirms the shape of the problem: `reference/fr-knowledge-graph.yaml` reports 65 clusters (`reference/fr-knowledge-graph.yaml:1-8`), node entries for FR-723 and FR-808 both point to `cluster-20` (`reference/fr-knowledge-graph.yaml:3112-3117`, `:3561-3566`), and `cluster-20` is a 23-member list including FR-723 and FR-808 (`reference/fr-knowledge-graph.yaml:15744-15767`).

The FR correctly obeys the main split-parent ruling. FR-815 was split because it bundled cluster naming, cross-cluster mentions, and judge context narrowing (`feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.judgement.md:17-25`). FR-816 isolates only the cluster-naming concern and explicitly preserves `cluster-N` keys instead of replacing them with semantic identifiers (`feature-requests/FR-816-knowledge-graph-cluster-display-names.md:14-16`, `:31-35`, `:81-83`), satisfying the core risk identified by FR-815 R-3 (`feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.judgement.md:33-38`).

The implementation surface is feasible. Cluster assignment is already centralized in `find_clusters()` and serialized by `write_graph()` (`scripts/extract_fr_graph.py:266-299`, `:394-426`), and filename noun extraction already exists in the prior-art helper (`.github/hooks/scripts/checks/prior_art.py:38-73`). Strategic classification: this is a small repo-governance artifact enrichment, not a new framework primitive; it improves a committed governance index and its human diagnostics without authorizing new graph, prompt, judge, or retrieval behavior.

## Required revisions

### R-1: Replace the "additive only" claim with an explicit schema-shape migration

FR-816 says the output change is "additive only" while showing `clusters.cluster-20` changing from a list into an object with `name` and `members` (`feature-requests/FR-816-knowledge-graph-cluster-display-names.md:54-60`). The current schema documents `clusters.cluster-1: [FR-XXX, FR-YYY]` (`reference/fr-knowledge-graph.md:43-45`), the current writer emits the raw cluster list (`scripts/extract_fr_graph.py:416-426`), and the current prior-art hook reads `graph["clusters"][cluster]` as a list (`.github/hooks/scripts/checks/prior_art.py:160-165`).

Revise the FR to state the exact new schema: `meta.schema_version` becomes `2`; each cluster entry is `{name: <kebab-display-name>, members: [FR-XXX, ...]}`; node `cluster` fields remain `cluster-N`. Add `.github/hooks/scripts/checks/prior_art.py` to the authorized maintenance surface only for adapting `_graph_prior_art()` to read the new `members` field without changing ranking policy.

### R-2: Pin the naming algorithm and fixture names mechanically

The proposed implementation uses `Counter.most_common(3)` over filename nouns (`feature-requests/FR-816-knowledge-graph-cluster-display-names.md:39-51`), but the FR does not define tokenization, the exact stopword source, tie ordering, whether a "shared" noun must occur in multiple member filenames, or how missing member files are handled. It also uses `observability-evidence-route` as the motivating name (`feature-requests/FR-816-knowledge-graph-cluster-display-names.md:8-10`, `:56-59`), but that name is not proven by the proposed helper and current cited noun extractor (`.github/hooks/scripts/checks/prior_art.py:38-73`) against the current `cluster-20` member list (`reference/fr-knowledge-graph.yaml:15744-15767`).

Revise the FR to define one deterministic algorithm in full: filename parsing rule, stopword set, noun counting rule, descending-count then lexical tie-break, top-N selection, collision pass ordered by numeric cluster suffix, and stale/missing-member behavior. The revised FR must name at least three cluster fixture IDs, including `cluster-20`, and list the exact expected `name` for each as produced by that algorithm. Remove or correct any illustrative name that is not asserted by the same algorithm.

### R-3: Choose an import-safe noun helper boundary

FR-816 allows importing `STOPWORDS` and `extract_nouns` from `.github/hooks/scripts/checks/prior_art.py` or duplicating them (`feature-requests/FR-816-knowledge-graph-cluster-display-names.md:65-67`). That is not a foldable implementation contract: `.github/hooks/...` is hook infrastructure, not a normal package boundary, and cross-importing it from `scripts/extract_fr_graph.py` couples the generator to enforcement internals. Repo doctrine also says code paths with hyphens must be converted to snake_case to avoid import issues (`.github/copilot-instructions.md:28-31`), and hook changes are enforcement-infrastructure changes requiring stricter review (`.github/skills/judge-fr/doctrine.md:94-103`).

Revise the FR to require extractor-local noun tokenization for this slice, matching the documented prior-art helper semantics where intended, and add a small test fixture for tokenization. Do not import from `.github/hooks/scripts/checks/prior_art.py` in `scripts/extract_fr_graph.py` under this authority.

### R-4: Strengthen tests from presence checks to schema and consumer checks

AC-05 only says to validate naming for at least three known clusters (`feature-requests/FR-816-knowledge-graph-cluster-display-names.md:75`), which would miss the schema migration and the existing prior-art consumer break. Existing tests already cover deterministic generation, stale detection, cycle behavior, and fixture accuracy (`tests/unit/test_fr_graph.py:94-249`); FR-816 must add targeted tests for the new schema and keep those existing guarantees green.

Revise the acceptance criteria to require tests for: the v2 cluster object schema, node cluster IDs remaining `cluster-N`, exact fixture names for three known clusters, deterministic collision suffixing, and `.github/hooks/scripts/checks/prior_art.py::_graph_prior_art()` returning cluster members from the v2 shape.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `scripts/extract_fr_graph.py`: cluster naming helper, v2 cluster serialization, deterministic collision handling |
| D-2 | `reference/fr-knowledge-graph.yaml`: regenerated schema-version-2 artifact with `clusters.<id>.name` and `clusters.<id>.members` |
| D-3 | `reference/fr-knowledge-graph.md`: documented v2 cluster schema and regeneration notes |
| D-4 | `.github/hooks/scripts/checks/prior_art.py`: minimal v2 cluster-member read adaptation only |
| D-5 | Tests and fixtures covering v2 cluster schema, exact names for at least three clusters, collision determinism, prior-art consumer parsing, and existing FR-814 determinism/staleness guarantees |
| D-6 | Requirement traceability, changelog fragment, and diary reflection required by repo gates |

Not authorized under FR-816: replacing `cluster-N` keys with semantic keys; adding `cross_cluster_mentions`; changing judge adapter graph, prompt, doctrine, or input-closure behavior; changing prior-art hook ranking, rare-noun policy, disposition marker behavior, or fallback semantics; adding LLM-based naming or edge classification; creating or modifying `graph.yaml` or `prompts/*.yaml`; adding CLI commands; broad CI/pre-commit rewrites beyond tests needed for this schema change.

## Revised acceptance criteria

- [ ] AC-01: `reference/fr-knowledge-graph.yaml` uses `meta.schema_version: 2`, and every `clusters.<cluster-N>` entry is an object containing `name: <non-empty-kebab-string>` and `members: [FR-XXX, ...]`.
- [ ] AC-02: Node `cluster` values remain stable `cluster-N` IDs; no node stores a semantic display name as its cluster identifier.
- [ ] AC-03: The cluster-name algorithm is fully specified and deterministic: filename tokenization, stopwords, count ordering, lexical tie-breaks, top-N selection, collision suffixes, and missing-member behavior are all covered by tests.
- [ ] AC-04: Tests assert exact expected names for at least three known clusters, including `cluster-20`, using committed fixture expectations produced by the declared algorithm.
- [ ] AC-05: A collision fixture proves two clusters with the same base name receive deterministic numeric-suffix names based on the cluster numeric suffix.
- [ ] AC-06: `.github/hooks/scripts/checks/prior_art.py::_graph_prior_art()` reads the v2 cluster shape and returns member FR IDs for a graph-backed cluster lookup without changing prior-art scoring policy.
- [ ] AC-07: `reference/fr-knowledge-graph.md` documents the v2 cluster schema, the display-name derivation rule, collision semantics, and regeneration command.
- [ ] AC-08: Existing FR-814 graph tests for determinism, staleness, cycle handling, and validation-fixture accuracy remain green after the schema change.
- [ ] AC-09: Tests are marked with `@pytest.mark.req(...)`; requirement/capability registry updates are included if needed; the diff includes changelog and diary artifacts required by repository gates.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 into `feature-requests/FR-816-knowledge-graph-cluster-display-names.md` before implementation authority activates. | GATE |
| C-2 | Do not replace stable `cluster-N` keys or node `cluster` values with semantic names. | GATE |
| C-3 | Do not modify judge adapter files, judge/review doctrine, graph-authoring artifacts, or prompt artifacts under this authority. | GATE |
| C-4 | Do not import `.github/hooks/scripts/checks/prior_art.py` from `scripts/extract_fr_graph.py`; keep noun tokenization import-safe within the authorized extractor surface. | GATE |
| C-5 | If `.github/hooks/scripts/checks/prior_art.py` changes, treat it as enforcement-infrastructure maintenance and require human review before merge. | GATE |
| C-6 | Do not claim an example display name unless a committed test proves the declared algorithm produces that exact string from the current cluster members. | GATE |

Authority granted: after the required revisions are folded into the FR, the enforcer may implement deterministic cluster display names in the FR knowledge graph artifact, update the schema docs and current prior-art graph consumer, and add the frozen tests/artifacts listed above.
