# Judgement: FR-779 Research-Agent Demo Rot — Unresolved Variable Bindings and Fabrication From Empty Findings

**Verdict:** APPROVED WITH REVISIONS — the defect class is real and the YAML-only repair is directionally sound, but authority activates only after the FR replaces session-local evidence with admissible evidence, chooses one terminal empty-findings behavior, and freezes test traceability and authoring sequence.

**Prior art:** FR-215 created the demo and explicitly deferred loop-back behavior; FR-777 and its judgement keep research-graph publication as a separate FR; no prior FR addresses demo variable-binding rot or empty-findings synthesis gating.

**Reviewed against:** `feature-requests/FR-779-research-agent-demo-rot.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-215-research-agent-demo.md`; `feature-requests/FR-777-shared-shell-toolbelt-manifests.md`; `feature-requests/FR-777-shared-shell-toolbelt-manifests.judgement.md`; `yamlgraph/utils/expressions.py`; `reference/graph-yaml.md`; committed `HEAD:examples/demos/research-agent/graph.yaml`; committed `HEAD:examples/demos/research-agent/demo-output.log`; `docs/diary/diary-2026-08-06-the-provider-was-innocent.md`. Not consumed as evidence: `tmp/research-agent-result.json`, `tmp/research-agent-tool-report.md`, and `logs/research-agent.err`, because the FR itself identifies them as uncommitted session-local artifacts (`feature-requests/FR-779-research-agent-demo-rot.md:27`, `feature-requests/FR-779-research-agent-demo-rot.md:73`) and judge doctrine permits only committed artifacts (`.github/skills/judge-fr/doctrine.md:16-24`).

## What is sound

The binding defect is concrete in the committed graph. The research-agent graph binds `query` and `scope` as bare placeholders at `HEAD:examples/demos/research-agent/graph.yaml:42`, `HEAD:examples/demos/research-agent/graph.yaml:53`, `HEAD:examples/demos/research-agent/graph.yaml:65`, and `HEAD:examples/demos/research-agent/graph.yaml:82`, while the graph reference documents node variable resolution as `{state.field}` / `{state.obj.attr}` (`reference/graph-yaml.md:1188-1200`) and the resolver only interpolates embedded `{state...}` strings in `resolve_template` (`yamlgraph/utils/expressions.py:177-238`). FR-779's proposed `{state.query}` / `{state.scope}` repair and explicit state declarations are therefore aligned with the documented boundary (`feature-requests/FR-779-research-agent-demo-rot.md:35-38`).

The empty-findings synthesis risk is also visible at graph-structure level without trusting the session-local result files. FR-215 intentionally created a linear extract -> plan -> execute -> validate -> respond demo and explicitly deferred loop-back behavior (`feature-requests/FR-215-research-agent-demo.md:28-29`, `feature-requests/FR-215-research-agent-demo.md:144-148`), but the committed graph routes `validate_findings` unconditionally to `synthesize_report` (`HEAD:examples/demos/research-agent/graph.yaml:94-99`). That contradicts the repo doctrine that a plausible wrong answer is harder to catch than a crash and that empty results must not be silently substituted with everything (`.github/copilot-instructions.md:78`, `.github/copilot-instructions.md:218`).

The scope is mostly minimal. The FR keeps the repair in the demo graph, rejects widening `resolve_template` to accept bare `{var}` (`feature-requests/FR-779-research-agent-demo-rot.md:62-66`), forbids `yamlgraph/` production changes unless split (`feature-requests/FR-779-research-agent-demo-rot.md:59`), and requires governed graph edits through the authoring route (`feature-requests/FR-779-research-agent-demo-rot.md:57`; `.github/copilot-instructions.md:15`). This preserves architecture alignment: orchestration stays in YAML, and the resolver contract is not weakened.

The strategic classification is **Contrib/example bug hardening**. FR-777 treats the research graph as a future toolbelt graph-runtime candidate, not current scope (`feature-requests/FR-777-shared-shell-toolbelt-manifests.md:36-57`), and its judgement explicitly keeps research graph publication as a separate FR (`feature-requests/FR-777-shared-shell-toolbelt-manifests.judgement.md:70-73`). FR-779 should make the existing demo trustworthy before that later publication path; it does not need a framework primitive.

## Required revisions

### R-1: Replace session-local evidence with an admissible witness

Fold the cited run evidence into committed, judge-readable form before enforcement authority activates. Either embed a concise raw-evidence excerpt in the FR or add a committed evidence fixture under a tracked path. The evidence must show all of: the original query marker/topic, the extracted intent missing or preserving that marker as applicable, empty `findings`, low-confidence validation with gaps, the final report containing unsupported synthesis, and the loop-cap lines for `plan_research` and `execute_research`. Do not rely on `tmp/` or `logs/` session files as the authoritative witness.

### R-2: Choose one terminal behavior for empty findings

Replace the current "honest validation verdict or loud failure" alternative (`feature-requests/FR-779-research-agent-demo-rot.md:39-45`, `feature-requests/FR-779-research-agent-demo-rot.md:56-57`) with one mechanically testable contract. The minimal authorized contract is: when `findings` is empty and `validation.confidence` is `low`, the graph terminates after `validate_findings`, preserves the validation verdict in state, and does not produce `report`. `synthesize_report` may run only for non-empty findings with non-low validation confidence. If the author wants process failure instead of terminal validation state, that is a different behavior and must be stated explicitly before enforcement.

### R-3: Freeze RED/GREEN and authoring sequence

Amend the FR to say the RED tests are created and committed before any governed graph mutation is applied, and the graph edits are then generated through `scripts/author.sh` with `tmp/draft-authoring-report.md` recording lint, validate, and smoke evidence. The existing "fix drafted, uncommitted" note (`feature-requests/FR-779-research-agent-demo-rot.md:35-38`) cannot be used as implementation proof and must not bypass the required RED witness or FR-767 authoring route.

### R-4: Add requirement traceability for the new tests

Fold an explicit traceability rule into the FR: every new or changed test must carry an exact `@pytest.mark.req("REQ-YG-...")` marker, and `python scripts/req_coverage.py --strict` must pass. If no existing requirement covers demo variable binding and empty-findings routing, enforcement must add a focused capability/REQ pair rather than leaving placeholder or unmarked tests.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-779-research-agent-demo-rot.md` revisions for admissible evidence, terminal empty-findings behavior, authoring sequence, and test traceability |
| D-2 | `examples/demos/research-agent/graph.yaml` variable bindings and state declarations, authored only through `scripts/author.sh` |
| D-3 | `examples/demos/research-agent/graph.yaml` edge/routing change so empty findings plus low confidence cannot reach `synthesize_report` |
| D-4 | Tests proving no bare non-`{state...}` node-variable placeholders in committed demo graphs and proving the research-agent empty-findings path bypasses synthesis |
| D-5 | Regenerated `examples/demos/research-agent/demo-output.log` from a grounded successful run, plus authoring validation evidence |
| D-6 | Changelog fragment, FR implementation-status fold, requirement traceability update if needed, and diary reflection |

Not authorized: changes under `yamlgraph/`; widening `resolve_template` or `resolve_state_expression` to accept bare `{var}`; prompt-only anti-fabrication instructions as the sole gate; publishing the research graph as a toolbelt manifest; modifying `.github/skills/judge-fr/adapters/graph.yaml`; changing judge/authoring/review doctrine, hooks, CI, provider defaults, shell-tool semantics, or unrelated demos. The all-demo variable-binding sweep is authorized as a guard; graph edits outside `examples/demos/research-agent/` are not authorized by this FR and must stop for a split or revised judgement if violations are found.

## Revised acceptance criteria

- [ ] AC-01: The FR contains committed admissible evidence, or cites a committed evidence fixture, showing the binding failure and empty-findings fabrication chain; no session-local `tmp/` or `logs/` file is required to understand the defect.
- [ ] AC-02: RED test proves the committed research-agent graph contains bare non-`{state...}` node-variable bindings; GREEN changes the four affected bindings to `{state.query}` / `{state.scope}` and declares `state: {query: str, scope: str}`.
- [ ] AC-03: A committed guard test asserts every committed demo graph uses only `{state...}` placeholders in node `variables:` mappings; if it finds violations outside research-agent, enforcement stops for split or re-judgement.
- [ ] AC-04: A committed graph-structure or execution test proves an empty `findings` value with `validation.confidence: low` terminates after `validate_findings`, preserves the validation verdict, and never executes or produces `synthesize_report` / `report`.
- [ ] AC-05: A committed positive-path test or demo witness proves non-empty findings with acceptable validation confidence can still reach `synthesize_report`.
- [ ] AC-06: `examples/demos/research-agent/demo-output.log` is regenerated from a successful grounded run whose output visibly echoes the query topic, contains no fatal markers, and is committed with the graph change.
- [ ] AC-07: Governed graph edits are authored through `scripts/author.sh`; `tmp/draft-authoring-report.md` records lint, validate, and smoke evidence for the changed graph.
- [ ] AC-08: No `yamlgraph/` production files change; if a production change is genuinely required, enforcement stops and a separate bug FR is filed.
- [ ] AC-09: Every new or changed test has an exact `@pytest.mark.req(...)` marker, the capability registry is updated if needed, and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-10: Changelog fragment, FR implementation-status update, and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-4 are folded into `feature-requests/FR-779-research-agent-demo-rot.md`. | GATE |
| C-2 | The empty-findings branch must be enforced by graph topology or deterministic graph configuration, not by prompt wording alone. | GATE |
| C-3 | The resolver contract remains `{state...}`-only for node variables; broadening bare `{var}` resolution is forbidden in this FR. | GATE |
| C-4 | If the all-demo variable-binding guard fails outside research-agent, stop for split or re-judgement before editing additional demos. | GATE |
| C-5 | If implementation requires changes under `yamlgraph/`, stop and file a separate bug FR; this FR may not repair production runtime behavior. | GATE |
| C-6 | Graph edits must pass through the graph-authoring route and retain its validation record; manual governed-graph edits are not enforcement authority. | GATE |

Authority granted: after the required revisions are folded into the FR, enforcement may harden only the research-agent demo's variable bindings and empty-findings routing, add the directly related tests and witness artifacts, and complete the required traceability, changelog, FR-status, and diary updates.
