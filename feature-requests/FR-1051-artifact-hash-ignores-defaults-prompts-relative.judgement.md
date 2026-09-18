# Judgement: FR-1051 `artifact_hash` ignores `defaults.prompts_relative`

**Verdict:** APPROVED WITH REVISIONS — the one-line presence-based fallback is the minimal feasible fix, but authority activates only after R-1 through R-4 are folded into the FR.

**Reviewed against:** `feature-requests/FR-1051-artifact-hash-ignores-defaults-prompts-relative.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; cited prior art `feature-requests/FR-1050-loop-limits-bind-or-fail.md` and `feature-requests/FR-842-lint-compile-validation-parity.md`; cited source evidence `yamlgraph/utils/artifact_hash.py`, `yamlgraph/compile/graph_loader.py`, `yamlgraph/linter/checks.py`, `yamlgraph/compile/map_compiler.py`, `yamlgraph/compile/node_compiler.py`, `yamlgraph/node_factory/llm_nodes.py`, `yamlgraph/node_factory/race_node.py`, and `yamlgraph/tools/agent.py`; supporting prompt-resolution surfaces returned by the repository source search: `yamlgraph/executor.py`, `yamlgraph/executor_base.py`, `yamlgraph/node_factory/base.py`, `yamlgraph/node_factory/router_race_node.py`, and `yamlgraph/node_factory/copilot_node.py`; repo contract/evidence `reference/graph-yaml.md`, `reference/module-map.md`, `ARCHITECTURE.md`, and `tests/unit/test_fr807_route_evidence_record.py`.

## What is sound

The defect is real and localized: `artifact_hash.py:40-43` already falls back to `defaults.prompts_dir` but reads `prompts_relative` only from the top level, while the loader uses presence-based top-level precedence with a defaults fallback at `graph_loader.py:106-111`. The proposed `dict.get(key, default)` expression preserves an explicit top-level `false`, unlike an `or` expression, and directly satisfies the consumer failure described at FR lines 26-84.

The proposal is minimal, feasible, and architecturally aligned. It changes the hasher's interpretation rather than teaching the consumer to work around an engine defect; it keeps the hash implementation consistent with the loader without introducing a new abstraction. The first consumer, failure event, reproduction, and deferred larger `GraphConfig` refactor are explicit (FR lines 7-16, 113-125, and 149-151). The prior-art dispositions distinguish the fix from FR-1050 and correctly preserve FR-842's loader/linter parity direction (FR lines 18-24).

Single responsibility is preserved if the scope remains the artifact-hash reader plus its direct witnesses. Strategic classification: **framework primitive correction** — executable-artifact identity is an existing framework primitive, and this FR repairs its configuration semantics rather than adding a contrib example or new abstraction. Direct regression tests are practical in the existing REQ-YG-552 artifact-hash suite (`tests/unit/test_fr807_route_evidence_record.py:53-73`).

## Required revisions

### R-1: Satisfy the prospective research-evidence gate

Replace the three-row alternatives table with an in-body research record containing four to six genuine solution classes. Preserve A1-A3, add at least one materially distinct class such as extracting and migrating a shared presence-based prompt-setting resolver, and disposition every class against the first consumer, blast radius, and one-line fix. Add an explicit `is_this_a_graph` answer: this is deterministic configuration resolution with no per-item model evaluation or multi-stage LLM pipeline, so no YAMLGraph research/authoring graph fits. The current record has only three classes and no graph-fit answer (FR lines 145-151), below the mandatory substance threshold in `judge-fr/doctrine.md:118-130`.

### R-2: Narrow the agreement claim to the governed seam

Replace the repository-wide claim in Ideal Result and AC-05 with a mechanically testable contract between raw YAML hashing and the loader's effective `GraphConfig`: for the same graph, `compute_artifact_hash` must use the loader-equivalent `prompts_relative` value when the key is absent, top-level `true`, top-level `false`, or present only under `defaults`. Do not claim or test that every reader has identical precedence semantics. The cited linter uses falsey fallback (`linter/checks.py:94-98`), so an explicit top-level `false` with `defaults: true` disagrees with the loader even after this fix; the current universal claim at FR lines 87-91 and 139-141 is therefore false. Park linter precedence cleanup for a separate FR.

### R-3: Make the RED witness condemn the defect

Rewrite AC-01 so the committed test asserts the desired behavior: a graph with `defaults.prompts_dir`, `defaults.prompts_relative: true`, and a referenced local prompt hashes successfully and changes hash when that prompt changes. On the baseline, that assertion must fail because `compute_artifact_hash` raises the unresolved-prompt `ValueError`; after the fix, the same test must pass. The current AC-01 asks the test to assert the defective exception (FR lines 129-131), which would be green before implementation and contradict AC-02.

### R-4: Pin requirement traceability and validation commands

State that every new test carries `@pytest.mark.req("REQ-YG-552")`, matching the existing artifact-hash witnesses at `tests/unit/test_fr807_route_evidence_record.py:53-100`, and require `python scripts/req_coverage.py --strict`. Replace the unbounded "full unit suite green" clause with the repository's exact unit command, `pytest tests/unit/ -q --no-cov -m "not slow" -n auto`, plus `ruff check yamlgraph/`. Retain the RED/GREEN commit IDs, changelog fragment, FR implementation record, and diary `Seed:` requirements.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Presence-based `defaults.prompts_relative` fallback in `yamlgraph/utils/artifact_hash.py` |
| D-2 | REQ-YG-552 regression witnesses in the existing artifact-hash unit-test surface, including prompt-content sensitivity and all four precedence cases |
| D-3 | FR-1051 implementation status, decisions, RED/GREEN commit IDs, and any deviations |
| D-4 | One changelog fragment and one `docs/diary/` entry containing `Seed:` |

Not authorized: changing `prompts_dir` empty-string semantics; changing `yamlgraph/linter/` precedence; migrating all readers to a shared resolver or parsed `GraphConfig`; changing graph YAML syntax; modifying consumer repositories or consumer graphs; changing prompt search order; adding a capability registry entry; or refactoring unrelated artifact-hash behavior.

## Revised acceptance criteria

- [ ] AC-01: A committed REQ-YG-552 test constructs a graph with `defaults.prompts_dir: prompts`, `defaults.prompts_relative: true`, and a local referenced prompt, then asserts `compute_artifact_hash` succeeds and changes when the prompt content changes; the unmodified baseline fails this test with the unresolved-prompt `ValueError`, and the RED commit ID is recorded.
- [ ] AC-02: `yamlgraph/utils/artifact_hash.py` resolves an absent top-level `prompts_relative` from `defaults.prompts_relative`, defaulting to `false` only when both declarations are absent.
- [ ] AC-03: Parameterized REQ-YG-552 witnesses cover absent everywhere, defaults-only `true`, top-level `true`, and explicit top-level `false` against `defaults: true`; artifact hashing uses the same effective value as `GraphConfig` in every case.
- [ ] AC-04: The defaults-relative fixture's manifest includes the resolved prompt: changing only that prompt changes the artifact hash, and deleting it raises the existing unresolved-prompt `ValueError`.
- [ ] AC-05: No production file other than `yamlgraph/utils/artifact_hash.py` changes; in particular, linter precedence, `prompts_dir` semantics, prompt search order, and graph syntax remain unchanged.
- [ ] AC-06: Every added test has `@pytest.mark.req("REQ-YG-552")`; `python scripts/req_coverage.py --strict`, `pytest tests/unit/ -q --no-cov -m "not slow" -n auto`, and `ruff check yamlgraph/` pass.
- [ ] AC-07: RED and GREEN are separate commits and both IDs are recorded in FR-1051; the FR records implementation status, decisions, and deviations; a changelog fragment and a diary entry containing `Seed:` are committed.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 into FR-1051 before beginning implementation; this draft grants no authority by itself. | GATE |
| C-2 | Preserve presence-based precedence so explicit top-level `false` wins over `defaults: true`; an `or` fallback is forbidden. | GATE |
| C-3 | The RED test must assert desired successful hashing and fail because of this defect, not assert the current exception as expected behavior. | GATE |
| C-4 | Keep production scope to `yamlgraph/utils/artifact_hash.py`; any linter or shared-resolver correction requires a separate judged FR. | GATE |
| C-5 | Human review must confirm the folded research record is substantive and promote this advisory draft before enforcement. | GATE |

Authority granted: after all revisions are folded and this advisory draft is human-reviewed and promoted, implement the one-line artifact-hash fallback and its frozen REQ-YG-552 witnesses and records only.
