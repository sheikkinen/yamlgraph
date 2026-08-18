# Judgement: FR-815 Knowledge Graph Phase 2 — Cluster Naming and Judge Context Narrowing

**Verdict:** SPLIT — the direction is sound, but the FR bundles three independently testable changes and its judge-context premise contradicts the cited adapter surface; no implementation authority is granted until the split FRs re-enter judgement.

**Reviewed against:** `feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.md`; cited predecessor `feature-requests/FR-814-fr-knowledge-graph-extraction.md`; cited predecessor judgement `feature-requests/FR-814-fr-knowledge-graph-extraction.judgement.md`; cited prior-art FRs `feature-requests/FR-737-graveyard-hook-prior-art-on-fr-creation.md` and `feature-requests/FR-738-prior-art-disposition-gate.md`; cited diary evidence `docs/diary/diary-2026-08-17-fr-corpus-as-token-economics.md` and `docs/diary/diary-2026-08-18-fr814-knowledge-graph-extraction.md`; cited graph artifact `reference/fr-knowledge-graph.yaml`; cited judge-adapter surface `.github/skills/judge-fr/adapters/README.md`, `.github/skills/judge-fr/adapters/graph.yaml`, and `.github/skills/judge-fr/adapters/prompts/judge.yaml`; repo doctrine `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, and `.github/copilot-instructions.md`.

## What is sound

The problem is real. FR-814 produced numeric cluster identifiers and an artifact with `cluster_count: 65` and `mentions_excluded: 1610` (`reference/fr-knowledge-graph.yaml:1-8`), while the diary explicitly records the usability gap: numeric names such as `cluster-47` are less useful than semantic names, and the new graph could let the judge preload cluster FRs instead of grepping the full corpus (`docs/diary/diary-2026-08-18-fr814-knowledge-graph-extraction.md:35-41`). FR-815 also identifies a concrete current witness: `cluster-20` contains FR-723, FR-808, and 21 other members (`reference/fr-knowledge-graph.yaml:15744-15767`), matching the FR's claim that the largest cluster is anonymous (`feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.md:29-32`).

The proposal correctly treats FR-814 as substrate rather than reinvention. FR-814 froze causal-vs-associative taxonomy, closures, deterministic output, and current deferred consumers (`feature-requests/FR-814-fr-knowledge-graph-extraction.md:72-103`, `:148-157`); FR-815's cluster names and weak-tie report are natural artifact-enrichment follow-ups, and judge context loading is a plausible later consumer.

Strategic classification: the graph artifact enrichment is a repo-governance primitive because it improves a committed governance index used by multiple flows. The judge-context narrowing is enforcement infrastructure and must be treated more strictly: the judge doctrine requires adversarial review for enforcement-infrastructure changes (`.github/skills/judge-fr/doctrine.md:94-103`), and repo doctrine says graph/prompt artifacts are governed surfaces with adapter routes and re-entry guards (`.github/copilot-instructions.md:15`, `:232`).

## Required revisions

### R-1: Split the FR into independently judged concerns

Replace this bundled FR with separate FRs:

1. Cluster display naming for `reference/fr-knowledge-graph.yaml`.
2. Cross-cluster mention extraction/reporting.
3. Judge prior-art context narrowing.

These are orthogonal under the single-responsibility criterion. Cluster names are a human-readable diagnostic improvement (`feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.md:52-70`), cross-cluster mentions restore a filtered subset of excluded associative edges (`:72-78`), and judge context narrowing changes the judge execution/input path (`:80-94`). Each has different risks, tests, and rollback surfaces.

### R-2: Correct the judge-adapter premise before any narrowing FR

The judge-narrowing FR must state the actual current surface. FR-815 says the judge adapter has an evidence-loading step or pre-processing step to modify (`feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.md:82-89`), but the cited adapter graph is a single Copilot node that only passes `fr_path` into the prompt (`.github/skills/judge-fr/adapters/graph.yaml:14-31`). The prompt instructs the judge execution to read the FR plus cited evidence and repo doctrine (`.github/skills/judge-fr/adapters/prompts/judge.yaml:12-18`); it does not implement full-corpus grep, cluster lookup, or automatic evidence loading. The README likewise says the graph writes `tmp/draft-judgement.md` and must not auto-fold, run CI, or perform other workflow actions (`.github/skills/judge-fr/adapters/README.md:19-30`).

The replacement FR must therefore choose and justify the real implementation surface: prompt instruction only, wrapper pre-processing, a new non-judge helper artifact, or another explicit surface. It must not claim a nonexistent evidence-loading node.

### R-3: Preserve stable cluster identity while adding semantic names

The cluster-naming FR must not replace stable machine identifiers with collision-prone display strings unless it also defines a complete migration. FR-815 proposes using semantic names as keys instead of `cluster-N` (`feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.md:69-70`), while current nodes store cluster IDs such as `cluster-20` (`reference/fr-knowledge-graph.yaml:3112-3117`, `:3561-3566`) and the `clusters` map is keyed by those IDs (`reference/fr-knowledge-graph.yaml:15674-15767`). A safer first increment is to keep `cluster-20` as the stable ID and add a deterministic `name` or `label` field. If the FR still wants key replacement, it must define migration rules for node references, collision resolution, and stale-output tests.

The naming algorithm must define tokenization, stopwords, tie-breaks, and collision suffixes mechanically. AC-02's "append member count" is insufficient when two clusters can share both top nouns and member count (`feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.md:98-100`).

### R-4: Define how excluded mentions are retained before reporting weak ties

The cross-cluster mention FR must specify the extraction source for the 1,610 excluded mentions. The committed artifact records only the count (`reference/fr-knowledge-graph.yaml:1-8`); FR-815 says to filter excluded `mentions` edges (`feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.md:72-78`) but does not define whether the extractor should retain all mention candidates internally, emit a separate artifact, or enrich the main graph. The replacement FR must define the schema, evidence fields, stable ordering, and whether `cross_cluster_mentions` affects the artifact size budget that caused FR-814 to exclude full mentions in the first place (`feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.md:39-42`, `:113-115`).

### R-5: Replace judge-accuracy prose with a mechanical comparison gate

The judge-narrowing FR's AC-07 says "re-judge 3 recent FRs, compare findings" (`feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.md:104-105`), but it does not define which FRs, which baseline outputs, which fields must match, or what variance is acceptable. Because this changes the judge's input context, the replacement FR must use named fixture FRs, committed baseline judgements or expected evidence sets, and a mechanical assertion such as "the closure loader includes all cited prior-art FRs and omits unrelated corpus files." Human review remains a GATE for the enforcement-infrastructure change; an LLM re-run comparison alone is not a test.

### R-6: Fold prior-art disposition into each replacement FR

Each split FR must disposition FR-814 and the relevant part of FR-737/FR-738. Repo doctrine requires prior art, including rejected or hook-returned candidates, to be dispositioned before authority (`.github/copilot-instructions.md:228-233`). FR-815's Related section lists FR-814, FR-737, and FR-738 (`feature-requests/FR-815-knowledge-graph-phase2-cluster-naming-judge-narrowing.md:122-132`), but the replacement FRs need per-scope disposition: artifact enrichment extends FR-814; judge narrowing extends the deferred consumer explicitly excluded from FR-814's first implementation (`feature-requests/FR-814-fr-knowledge-graph-extraction.md:156-157`); prior-art hook history constrains fallback/noise behavior (`feature-requests/FR-737-graveyard-hook-prior-art-on-fr-creation.md:58-84`, `feature-requests/FR-738-prior-art-disposition-gate.md:59-76`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Replacement FR: cluster semantic display names for `reference/fr-knowledge-graph.yaml` and its generator/docs/tests |
| D-2 | Replacement FR: cross-cluster mention report for `reference/fr-knowledge-graph.yaml` or a separately named derived artifact |
| D-3 | Replacement FR: judge prior-art context narrowing for the actual `.github/skills/judge-fr/adapters/` surface or a clearly named preprocessing/helper surface |

Not authorized under FR-815: changing `.github/skills/judge-fr/adapters/graph.yaml`; changing `.github/skills/judge-fr/adapters/prompts/judge.yaml`; modifying judge doctrine; changing the judge input-closure contract; replacing full-corpus grep in any hook; changing `reference/fr-knowledge-graph.yaml`; adding `cross_cluster_mentions`; renaming existing cluster keys; adding fallback behavior; running or invoking another judge; implementing any code under this bundled authority.

## Revised acceptance criteria

- [ ] AC-01: The bundled FR is replaced by three separate FRs matching D-1, D-2, and D-3, each with its own first consumer, proposed solution, purge list, prior-art disposition, and mechanically checkable acceptance criteria.
- [ ] AC-02: The cluster-naming FR preserves stable cluster identity or defines a complete migration; its naming algorithm specifies tokenization, stopwords, ordering, tie-breaks, collision handling, and deterministic stale-output tests.
- [ ] AC-03: The cross-cluster mention FR defines the extraction source for excluded mentions, output schema, evidence fields, deterministic ordering, size budget, and a test proving every emitted mention crosses two distinct cluster IDs.
- [ ] AC-04: The judge-narrowing FR corrects the adapter premise by citing the actual single-node `fr_path` prompt surface and naming the exact implementation surface it will change.
- [ ] AC-05: The judge-narrowing FR includes a fixture-based evidence-loading test with named FRs and expected closure/evidence sets; it does not rely on an undefined "compare findings" LLM rerun.
- [ ] AC-06: The judge-narrowing FR defines stale/absent graph behavior as an explicit diagnostic path and preserves input closure; no silent substitute-everything fallback is permitted.
- [ ] AC-07: Any replacement FR that modifies judge adapter graph/prompt files or other enforcement infrastructure declares human review as a GATE.
- [ ] AC-08: Each replacement FR includes tests with requirement traceability, plus changelog and diary obligations required by repo doctrine.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement FR-815 as written; split first and re-enter judgement. | GATE |
| C-2 | Do not modify judge adapter graph/prompt files under this bundled authority. | GATE |
| C-3 | Do not replace cluster IDs with semantic keys without a judged migration contract. | GATE |
| C-4 | Do not claim judge context reduction until the replacement FR proves the actual adapter path loads less committed evidence while preserving input closure. | GATE |
| C-5 | Treat all judge-adapter or hook changes as enforcement-infrastructure changes requiring human review. | GATE |

Authority granted: no implementation authority is granted; authority is limited to filing the three replacement FRs above for independent judgement.

**Prior art:** FR-815 parent FR (same artifact); FR-724, FR-295, FR-369, FR-248 share "phase2" noun only — unrelated domains (process codes, FSM watcher, FSM hooks, A2A consumer).
