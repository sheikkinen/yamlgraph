# Judgement: FR-1060 Subgraph `mode` is unvalidated — `SubgraphNodeConfig` is never applied

**Verdict:** APPROVED WITH REVISIONS — the schema-boundary repair is minimal, feasible, and directly testable; authority activates only after R-1 through R-3 are folded into the FR.

**Prior art:** [FR-1060-subgraph-mode-validation-unwired.md](FR-1060-subgraph-mode-validation-unwired.md) — the subject of this judgement, not competing precedent; the noun overlap is the filename-stem pairing of an FR with its own verdict. The FR's own prior-art line dispositions FR-1058, FR-081, FR-716, FR-797, and FR-210.

**Reviewed against:** `feature-requests/FR-1060-subgraph-mode-validation-unwired.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-1058-subgraph-runnable-config-propagation.md`; `feature-requests/FR-081-copilot-node.md`; `feature-requests/FR-716-preemptive-module-splits.md`; `feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md`; `feature-requests/FR-210-subgraph-interrupt-state-commit.md`; `yamlgraph/models/node_schema.py`; `yamlgraph/models/graph_schema.py`; `yamlgraph/node_factory/subgraph_nodes.py`; `yamlgraph/linter/patterns/subgraph.py`; `reference/graph-yaml.md`; `ARCHITECTURE.md`; `capabilities/CAP-01-config-loading-validation.yaml`; `capabilities/CAP-11-subgraph-map.yaml`; `capabilities/CAP-201-preemptive-module-splits.yaml`; `scripts/req_coverage.py`.

## What is sound

The problem is real and localized. `GraphConfigSchema.nodes` currently validates every node as `NodeConfig` (`yamlgraph/models/graph_schema.py:57-58`), whose `mode` field is unrestricted `str | None` (`yamlgraph/models/node_schema.py:214-218`), while the existing `SubgraphNodeConfig` owns both the `Literal["invoke", "direct"]` contract and the direct-mode mapping validator (`yamlgraph/models/node_schema.py:21-58`). Runtime dispatch then treats only the exact value `direct` specially and lets every other value take the invoke path (`yamlgraph/node_factory/subgraph_nodes.py:187-212`). The proposed schema-boundary dispatch therefore fixes the cause rather than duplicating a runtime check, in accordance with the repository's boundary-normalization rule.

The scope is one responsibility: make the existing subgraph-mode contract truthful across validation, lint guidance, and its reference documentation. The linter currently emits W501/W502 solely from mapping absence (`yamlgraph/linter/patterns/subgraph.py:65-84`), and the subgraph reference currently advertises `stream` instead of `direct` (`reference/graph-yaml.md:877-882`), so both follow-up surfaces are direct consequences of activating the existing validator rather than independent features. FR-1058 explicitly deferred these documentation and linter surfaces as S-1 and S-5 (`feature-requests/FR-1058-subgraph-runnable-config-propagation.md:340-358,415-434`), while the present FR keeps demos, checkpointer behavior, and new modes out of scope (`feature-requests/FR-1060-subgraph-mode-validation-unwired.md:227-236`).

The research is substantive: five alternatives carry concrete probe outcomes and distinguish boundary validation from advisory lint, runtime checking, deletion, documentation-only repair, and globally narrowing `NodeConfig` (`feature-requests/FR-1060-subgraph-mode-validation-unwired.md:177-209`). Prior art is dispositioned rather than merely listed (`feature-requests/FR-1060-subgraph-mode-validation-unwired.md:12-31`). The implementation is feasible with existing Pydantic models and the existing CLI validation boundary (`yamlgraph/models/graph_schema.py:139-149`).

The acceptance tests are mostly derivable without inventing behavior: AC-01 and AC-02 condemn the unwired schema through the CLI; AC-03 protects all supported/default execution paths and the FR-1058 fixture; AC-04 captures both sides of the linter branch; and AC-07 invokes the repository traceability gate (`feature-requests/FR-1060-subgraph-mode-validation-unwired.md:153-174`). This is a repair to an existing framework primitive, not a new abstraction: `SubgraphNodeConfig`, CAP-01 validation, and CAP-11 subgraph execution already exist (`capabilities/CAP-01-config-loading-validation.yaml:1-28`; `capabilities/CAP-11-subgraph-map.yaml:1-33`).

## Required revisions

### R-1: Register REQ-YG-685 before assigning tests to it

Add REQ-YG-685 to `capabilities/CAP-01-config-loading-validation.yaml` with a description covering type-dispatched subgraph validation, supported `invoke`/`direct` modes, direct-mode rejection of `input_mapping`/`output_mapping`, and mode-aware W501/W502 guidance. Declare the implementation and witness surfaces there, and add the matching REQ-YG-685 row to `ARCHITECTURE.md`. Add both files to the Proposed Solution and deliverables. AC-06 currently assigns tests to an unregistered requirement, which `scripts/req_coverage.py:408-431` classifies as a phantom and makes `--strict` fail; AC-07 therefore contradicts AC-06 until this revision is folded.

### R-2: Bound the documentation assertion to the subgraph mode contract

Replace AC-05's global phrase “no longer mentions `stream`” with an assertion scoped to the `type: subgraph` property table: that row must identify exactly `invoke` and `direct` as accepted values, mark `invoke` as the default, and must not identify `stream` as a subgraph mode. Keep the schema-to-reference equality test, but state that it extracts the accepted values from that specific row. `reference/graph-yaml.md` legitimately contains unrelated streaming configuration and CLI documentation, so a file-wide absence criterion is ambiguous and would test the wrong contract.

### R-3: Name the mappings that direct mode rejects

Replace “mappings not accepted” in the Proposed Solution with “`input_mapping` and `output_mapping` are not accepted in direct mode,” matching the existing validator at `yamlgraph/models/node_schema.py:52-58` and AC-02. Add `interrupt_output_mapping` semantics for direct mode to the not-authorized list: this FR neither validates nor documents a new rule for that field. The current generic wording implies a broader contract than the proposed implementation and tests establish.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Wire real `type: subgraph` graph YAML through `SubgraphNodeConfig` validation at the existing graph-schema boundary in `yamlgraph/models/graph_schema.py`, reusing the validators in `yamlgraph/models/node_schema.py`. |
| D-2 | Gate W501/W502 on non-direct mode in `yamlgraph/linter/patterns/subgraph.py`. |
| D-3 | Correct and explain the subgraph `mode` row in `reference/graph-yaml.md`, including the precise `input_mapping`/`output_mapping` restriction. |
| D-4 | Add CLI validation, run-path regression, linter, and reference/schema drift tests under `tests/unit/`, reusing `tests/fixtures/subgraph_direct_fr1058/` unchanged. |
| D-5 | Register REQ-YG-685 in `capabilities/CAP-01-config-loading-validation.yaml` and `ARCHITECTURE.md`; tag every new test with it. |
| D-6 | Add the required bug-fix changelog fragment, update FR-1060 with implementation status and decisions, and record the Distill entry with a `Seed:` in `docs/diary/`. |

Not authorized: a new subgraph mode; changes to invoke/direct runtime semantics in `yamlgraph/node_factory/subgraph_nodes.py` or relay/checkpointer behavior; changes to `interrupt_output_mapping` semantics for direct mode; new or modified graph/prompt/demo artifacts; changes to FR-1058 fixtures; general `NodeConfig.mode` narrowing; JSON-schema redesign; unrelated linter cleanup; CI, hook, judge, review, or other enforcement-infrastructure changes.

## Revised acceptance criteria

- [ ] AC-01: Through the `yamlgraph graph validate` CLI entry point, subgraph nodes with `mode: stream` and `mode: bogus-typo` each exit non-zero, and each diagnostic names `invoke` and `direct` as the supported values.
- [ ] AC-02: Through the same CLI boundary, `mode: direct` combined with either `input_mapping` or `output_mapping` exits non-zero with a diagnostic identifying the forbidden direct-mode mapping.
- [ ] AC-03: Subgraph nodes with `mode: invoke`, `mode: direct`, and omitted `mode` each validate and run successfully; the committed fixtures in `tests/fixtures/subgraph_direct_fr1058/` remain unchanged and pass.
- [ ] AC-04: `yamlgraph graph lint` emits neither W501 nor W502 for `mode: direct`, and emits both warnings for `mode: invoke` without `input_mapping` and `output_mapping`.
- [ ] AC-05: The `type: subgraph` property table in `reference/graph-yaml.md` identifies exactly `invoke` and `direct` as accepted `mode` values, identifies `invoke` as the default, does not identify `stream` as a subgraph mode, and explains that direct mode shares the state schema and rejects `input_mapping`/`output_mapping`.
- [ ] AC-06: A test extracts the accepted values from that specific reference-table row and proves equality with the `Literal` members of `SubgraphNodeConfig.mode`.
- [ ] AC-07: REQ-YG-685 is declared under CAP-01 and in `ARCHITECTURE.md`; every new test is tagged `@pytest.mark.req("REQ-YG-685")`.
- [ ] AC-08: The RED commit demonstrates failures caused by the unwired behavior through the CLI/linter/reference seams, followed by a separate GREEN implementation commit.
- [ ] AC-09: `python scripts/req_coverage.py --strict` exits 0.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-3 into FR-1060 before implementation authority activates. | GATE |
| C-2 | Validation must reuse `SubgraphNodeConfig`; do not duplicate its supported-mode or mapping rules in the CLI, linter, loader, or node factory. | GATE |
| C-3 | Tests must exercise real graph YAML through the CLI validation boundary; direct construction of `SubgraphNodeConfig` is insufficient evidence for AC-01 or AC-02. | GATE |
| C-4 | Preserve the accepted/default execution paths and the unchanged FR-1058 fixture required by AC-03. | GATE |
| C-5 | Do not broaden this repair into runtime, checkpointer, interrupt-mapping, graph-authoring, or exported JSON-schema work. | GATE |
| C-6 | Human review must promote this advisory draft before enforcement begins. | GATE |

Authority granted: after R-1 through R-3 are folded and this draft is human-promoted, implement only D-1 through D-6 subject to C-1 through C-6.
