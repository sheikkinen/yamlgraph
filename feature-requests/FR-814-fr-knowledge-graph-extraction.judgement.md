# Judgement: FR-814 FR Knowledge Graph Extraction (DRAFT)

**Verdict:** APPROVED WITH REVISIONS — the corpus-as-graph problem is real and has a named first consumer, but authority activates only after the FR grounds its corpus/accuracy claims, repairs stale evidence, narrows first implementation scope, and freezes graph semantics/regeneration gates.

**Reviewed against:** `feature-requests/FR-814-fr-knowledge-graph-extraction.md`; cited evidence `docs/diary/diary-2026-08-17-fr-corpus-as-token-economics.md`; cited evidence path `.github/hooks/prior-art-check.sh` (absent at that path); current prior-art hook artifacts `.github/hooks/scripts/checks/fr-checks.sh`, `.github/hooks/scripts/checks/prior_art.py`, `.github/hooks/scripts/checks/prior_art_gate.py`; cited prior-art examples `feature-requests/FR-723-execution-path-visualization.md`, `feature-requests/FR-723-execution-path-visualization.judgement.md`, `feature-requests/FR-807-route-evidence-record-hardening.md`, `feature-requests/FR-807-route-evidence-record-hardening.judgement.md`, `feature-requests/FR-808-regulated-evidence-profile.md`, `feature-requests/FR-808-regulated-evidence-profile.judgement.md`; repo doctrine `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`.

## What is sound

The FR identifies a real governance cost, not a speculative data-structure hobby. The cited diary records the FR corpus as 779 files, 7.6MB, and about 1.9M tokens consumed mainly by judge/enforce/review/inquisitor flows (`docs/diary/diary-2026-08-17-fr-corpus-as-token-economics.md:6-30`). It also names the causal layer explicitly: late FRs embed relationship types such as prior art, dependency, substrate, seed origin, parent plan, and regression (`docs/diary/diary-2026-08-17-fr-corpus-as-token-economics.md:65-82`), then proposes a machine causality map to avoid re-reading prose for post-judgement consumers (`docs/diary/diary-2026-08-17-fr-corpus-as-token-economics.md:97-122`).

The first consumer is concrete. FR-814 says the prior-art hook should answer duplicate questions with typed edges and transitive closures instead of prose grep (`feature-requests/FR-814-fr-knowledge-graph-extraction.md:8-10`). The current hook is a plausible integration point: `fr-checks.sh` invokes `prior_art.py` for newly created FRs only (`.github/hooks/scripts/checks/fr-checks.sh:64-75`), `prior_art.py` extracts filename nouns and scores candidates by corpus frequency (`.github/hooks/scripts/checks/prior_art.py:66-72`, `:118-182`), and the pre-commit gate requires a staged `**Prior art:**` marker when hits exist (`.github/hooks/scripts/checks/prior_art_gate.py:55-70`).

The strategic classification is a repo-governance primitive. The FR names more than one eventual consumer — prior-art hook, judge context loading, inquisitor, and CLI (`feature-requests/FR-814-fr-knowledge-graph-extraction.md:137-144`) — and the diary names the same post-judgement machine consumers (`docs/diary/diary-2026-08-17-fr-corpus-as-token-economics.md:99-105`). The first implementation must still stay at the first consumer and reusable graph artifact, not authorize every downstream consumer at once.

## Required revisions

### R-1: Ground corpus statistics and the accuracy target in reproducible artifacts

Amend the FR with a reproducible corpus census and a committed/manual validation fixture before implementation. The census must explain or correct the mismatch between FR-814's claims of "723 FRs, 10,147 cross-references" (`feature-requests/FR-814-fr-knowledge-graph-extraction.md:14-18`) and the cited diary's "779 files, 7.6MB, ~1.9M tokens" (`docs/diary/diary-2026-08-17-fr-corpus-as-token-economics.md:6-8`). The validation fixture must name at least 20 labelled FR references, their expected edge types, and the exact scoring formula for the `>85% accuracy` gate (`feature-requests/FR-814-fr-knowledge-graph-extraction.md:153-155`). Unknown/ambiguous edges must not count as correct typed edges.

### R-2: Repair the prior-art hook citation and preserve the current gate contract

Replace the stale cited hook path `.github/hooks/prior-art-check.sh` (`feature-requests/FR-814-fr-knowledge-graph-extraction.md:182-184`) with the actual current surfaces: `.github/hooks/scripts/checks/fr-checks.sh`, `.github/hooks/scripts/checks/prior_art.py`, and `.github/hooks/scripts/checks/prior_art_gate.py`. State exactly how the generated graph augments or replaces the current filename-noun/frequency retrieval (`.github/hooks/scripts/checks/prior_art.py:66-72`, `:156-182`) while preserving the current boundaries: newly created FRs only (`.github/hooks/scripts/checks/fr-checks.sh:64-75`), staged-blob disposition marker semantics (`.github/hooks/scripts/checks/prior_art_gate.py:44-70`), and silence-over-noise behavior when no rare signal exists (`.github/hooks/scripts/checks/prior_art.py:156-181`). A missing or stale graph must fail with a clear diagnostic for graph-backed mode; it must not silently fall back to scanning everything, because repo doctrine forbids silent fallback/substitute-everything behavior (`.github/copilot-instructions.md:218`).

### R-3: Freeze this FR to extraction plus the first consumer; split or defer the LLM and downstream consumers

Remove the optional LLM classification pass from this FR's authorized implementation, or split it into a separate graph-authoring FR. FR-814 currently sketches `graphs/fr-knowledge-graph/graph.yaml` (`feature-requests/FR-814-fr-knowledge-graph-extraction.md:79-93`), and repo doctrine says any new or materially modified `graph.yaml` or `prompts/*.yaml` artifact must use the graph-authoring route (`.github/copilot-instructions.md:15`). This judge does not authorize that route here. Likewise, judge/enforce/review context loading, inquisitor orphan detection, and `yamlgraph fr deps` are listed as integrations (`feature-requests/FR-814-fr-knowledge-graph-extraction.md:137-144`) but are not covered by the acceptance criteria (`feature-requests/FR-814-fr-knowledge-graph-extraction.md:151-160`). They must be removed from this FR's implementation scope or re-enter as separate FRs after the graph artifact exists.

### R-4: Define edge taxonomy, evidence retention, and closure semantics before coding

Fold a precise schema/taxonomy contract into the FR. Each extracted relationship must preserve source evidence: source FR, target FR, section/context, line or span reference where available, rule id, confidence, and whether it was explicit or inferred. Define which edge types are causal and directional for DAG/cycle/closure computation, and which are associative metadata only. The current list mixes causal edges (`depends_on`, `regression_of`, `spawned_by`) with non-causal or non-FR relations (`prior_art`, `first_consumer_of`) (`feature-requests/FR-814-fr-knowledge-graph-extraction.md:70-78`), while the solution promises a DAG, cycle detection, closures, and clusters (`feature-requests/FR-814-fr-knowledge-graph-extraction.md:94-100`). Without this partition, "zero cycles" and "transitive closures" are underspecified and can produce plausible wrong graphs.

### R-5: Make regeneration deterministic and gate staleness mechanically

Revise the committed-output contract so `reference/fr-knowledge-graph.yaml` is deterministic: stable sorting, stable schema version, no wall-clock timestamp churn in committed content, and a corpus fingerprint or source-file hash set that lets tests detect staleness. FR-814 currently proposes a committed derived artifact with a generated timestamp and pre-commit/CI regeneration (`feature-requests/FR-814-fr-knowledge-graph-extraction.md:102-149`). That is acceptable only if repeated generation on an unchanged corpus produces no diff and FR changes fail the gate when the committed graph is stale.

### R-6: Add prior-art disposition, traceability, and enforcement-infrastructure gates

Add an explicit `**Prior art:**` disposition line to the FR before authority activates. The current `## Related` list cites FR-723, FR-807, and FR-808 as examples (`feature-requests/FR-814-fr-knowledge-graph-extraction.md:180-186`), but repo doctrine requires prior art, including rejected or hook-returned candidates, to be dispositioned before authority (`.github/copilot-instructions.md:232`), and the current gate's marker is exactly `**Prior art:**` (`.github/hooks/scripts/checks/prior_art_gate.py:23-70`). Also add acceptance coverage for requirement traceability and repository gates: tests must carry `@pytest.mark.req(...)` markers and close under the requirement coverage script (`.github/copilot-instructions.md:173-176`), and the diff must include the required changelog/diary artifacts for a feature change (`.github/copilot-instructions.md:33`, `:226`, `:236`). Because this FR changes hooks/pre-commit or CI regeneration behavior, enforcement must include human review of those enforcement-infrastructure changes as a GATE (`.github/skills/judge-fr/doctrine.md:94-103`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `scripts/extract_fr_graph.py`: deterministic structural extractor over `feature-requests/*.md` |
| D-2 | Manual validation fixture and tests for at least 20 labelled references, edge typing, closure, cycles, stale-output detection, and runtime |
| D-3 | `reference/fr-knowledge-graph.yaml`: committed generated graph artifact with schema version, corpus fingerprint, nodes, explicit edges, inferred closures, and clusters |
| D-4 | `.github/hooks/scripts/checks/prior_art.py` and related hook tests: graph-backed prior-art lookup preserving FR-737/FR-738 gate semantics |
| D-5 | `reference/fr-knowledge-graph.md`: schema, taxonomy, regeneration, validation, and prior-art-hook usage docs |
| D-6 | Requirement/capability traceability, changelog fragment, and diary reflection required by repo gates |

Not authorized: creating or modifying `graphs/fr-knowledge-graph/graph.yaml` or `prompts/*.yaml` under this judgement; optional LLM edge classification; judge/enforce/review context-loader changes; inquisitor orphan-detection changes; a new `yamlgraph fr deps` CLI surface; broad CI/pre-commit rewrites beyond a stale-generated-artifact gate; legal/compliance claims; changing unrelated FR workflow gates.

## Revised acceptance criteria

- [ ] AC-01: `scripts/extract_fr_graph.py` deterministically generates `reference/fr-knowledge-graph.yaml` from the committed `feature-requests/*.md` corpus; running it twice on an unchanged corpus produces no diff.
- [ ] AC-02: The generated YAML validates against a documented schema containing corpus fingerprint, schema version, node metadata, explicit edges with evidence/rule/confidence fields, inferred closures separated from explicit edges, and deterministic clusters.
- [ ] AC-03: A committed/manual validation fixture with at least 20 labelled FR references proves Pass 1 edge typing achieves `>85%` accuracy by the FR's stated formula; ambiguous/unknown edges are reported separately and do not count as correct typed edges.
- [ ] AC-04: Closure and cycle detection run only over the FR's declared causal edge types; any cycle failure reports the exact FR chain and edge evidence, while associative edges such as prior-art references do not create false DAG failures.
- [ ] AC-05: A stale-output test fails when an FR file changes without regenerating `reference/fr-knowledge-graph.yaml`, and passes after regeneration.
- [ ] AC-06: The prior-art hook consumes the generated graph for duplicate/prior-art retrieval while preserving newly-created-FR-only behavior, staged `**Prior art:**` marker behavior, and silence when no meaningful signal exists.
- [ ] AC-07: The prior-art hook has a fixture proving graph-backed lookup finds a typed prior-art/dependency relation without scanning the full prose corpus in the success path; missing or stale graph-backed data produces a clear diagnostic, not a silent substitute-everything fallback.
- [ ] AC-08: `reference/fr-knowledge-graph.md` documents the schema, edge taxonomy, confidence semantics, regeneration command, stale gate, and prior-art hook usage.
- [ ] AC-09: Tests are marked with `@pytest.mark.req(...)`; capability/requirement registry changes are included if needed; `python scripts/req_coverage.py --strict` closes; the diff includes changelog and diary artifacts required by repository gates.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-6 into `feature-requests/FR-814-fr-knowledge-graph-extraction.md` before implementation authority activates. | GATE |
| C-2 | Do not create or modify graph/prompt artifacts for optional LLM classification under this authority. | GATE |
| C-3 | Preserve FR-737/FR-738 prior-art hook semantics: newly added FR scope, staged disposition marker, ranked/silent behavior, and no silent stale-graph fallback. | GATE |
| C-4 | Treat hook/pre-commit/CI changes as enforcement-infrastructure changes requiring human review before merge. | GATE |
| C-5 | Do not implement judge/enforce/review/inquisitor context loading or a new `yamlgraph fr deps` CLI command in this FR. | GATE |
| C-6 | Do not commit a generated graph that changes on every run because of timestamps or unstable ordering. | GATE |

Authority granted: after the required revisions are folded into the FR, the enforcer may implement the deterministic FR knowledge-graph extractor, committed graph artifact, documentation, and graph-backed prior-art hook integration within the frozen surfaces above.
