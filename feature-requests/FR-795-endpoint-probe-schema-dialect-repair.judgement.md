# Judgement: FR-795 Endpoint-Probe Prompt Schema Dialect Repair

**Verdict:** APPROVED - the FR is a narrow graph-artifact repair for a real compile-blocking schema dialect mismatch, with framework-runtime changes explicitly excluded and authoring-route validation gated.

**Reviewed against:** `feature-requests/FR-795-endpoint-probe-schema-dialect-repair.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/skills/graph-authoring/doctrine.md`; `yamlgraph/schema_loader.py`; `examples/api-discovery/steps/endpoint-probe/prompts/probe.yaml`; `examples/api-discovery/steps/endpoint-probe/graph.yaml`; `examples/beautify/prompts/analyze.yaml`; `feature-requests/FR-794-python-tool-manifest-root-confinement-fix.md`; `feature-requests/FR-794-python-tool-manifest-root-confinement-fix.judgement.md`; `feature-requests/FR-785-api-discovery-endpoint-probe-step.md`; `feature-requests/FR-785-api-discovery-endpoint-probe-step.judgement.md`. The FR-cited `feature-requests/FR-795-endpoint-probe-schema-dialect-repair.judgement.md` was not present as a committed artifact, so it was not used as authority.

## What is sound

The defect is real and precisely localized. The current prompt uses native `schema:` but declares `live_endpoints` as `type: list` with `items:` and nested fields (`examples/api-discovery/steps/endpoint-probe/prompts/probe.yaml:40-67`). Native schema loading calls `build_pydantic_model()` for `schema:` (`yamlgraph/schema_loader.py:256-258`), and native type resolution supports primitive names plus `list[T]`/`dict[K, V]`, not bare `list` or `items:` (`yamlgraph/schema_loader.py:62-102`). The FR's quoted failure follows directly from that boundary (`feature-requests/FR-795-endpoint-probe-schema-dialect-repair.md:16-28`).

The proposed repair follows an existing dialect instead of extending runtime code. JSON-Schema-style `output_schema:` is an implemented loader path (`yamlgraph/schema_loader.py:260-267`) with top-level `type: object`, `properties`, `required`, array `items`, and optionality by omission from `required` (`yamlgraph/schema_loader.py:189-230`). The cited precedent really uses nested array item `properties` under `output_schema:` (`examples/beautify/prompts/analyze.yaml:21-68`), matching FR-795's proposed conversion (`feature-requests/FR-795-endpoint-probe-schema-dialect-repair.md:71-128`).

The scope is minimal after the FR-794 split. FR-794 explicitly separated this prompt-schema defect from framework manifest-root confinement (`feature-requests/FR-794-python-tool-manifest-root-confinement-fix.md:54-57`, `feature-requests/FR-794-python-tool-manifest-root-confinement-fix.md:160-165`), and its judgement forbade graph or prompt artifact edits under FR-794 (`feature-requests/FR-794-python-tool-manifest-root-confinement-fix.judgement.md:32`, `feature-requests/FR-794-python-tool-manifest-root-confinement-fix.judgement.md:50`). FR-795 correctly re-enters as a separate graph-authoring-scoped FR.

The architectural boundary is aligned with repo doctrine. Project doctrine requires any material `prompts/*.yaml` modification to go through `scripts/author.sh` and verify `tmp/draft-authoring-report.md`, never direct manual edits (`.github/copilot-instructions.md:15`; `.github/skills/graph-authoring/doctrine.md:86-102`). FR-795 makes that a gate (`feature-requests/FR-795-endpoint-probe-schema-dialect-repair.md:128-130`, `feature-requests/FR-795-endpoint-probe-schema-dialect-repair.md:150-156`).

Strategic classification: **Contrib/example bug fix**. This repairs a shipped example step from FR-785 (`feature-requests/FR-785-api-discovery-endpoint-probe-step.md:1-20`, `feature-requests/FR-785-api-discovery-endpoint-probe-step.md:98-110`) using existing prompt-schema and graph-authoring primitives; it is not a framework primitive because no loader semantics need to change.

## Required revisions

None.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/api-discovery/steps/endpoint-probe/prompts/probe.yaml` converted from native `schema:` to JSON-Schema `output_schema:` while preserving `live_endpoints`, `html_pages`, and `verdict_hint`. |
| D-2 | `tmp/draft-authoring-report.md` produced by `scripts/author.sh <task-brief.md>` with substantive artifact, precedent, validation, repairs, and blocked-validation sections. |
| D-3 | Regression coverage proving `yamlgraph.compile.graph_loader.load_and_compile("examples/api-discovery/steps/endpoint-probe/graph.yaml")` succeeds after the prompt repair. |
| D-4 | Changelog fragment and diary reflection. |

Not authorized: changes under `yamlgraph/**`; extending either schema dialect; adding nested Pydantic model generation; changing graph loader, agent execution, tool manifests, `curl_probe`, API-discovery orchestrator/step graphs, CI/hooks/doctrine, judge/review routes, or any API-discovery artifact outside `examples/api-discovery/steps/endpoint-probe/prompts/probe.yaml`.

## Revised acceptance criteria

- [ ] AC-01: `examples/api-discovery/steps/endpoint-probe/prompts/probe.yaml` uses `output_schema:` with top-level `type: object`, `properties.live_endpoints`, `properties.html_pages`, and `properties.verdict_hint`; no top-level native `schema:` block remains.
- [ ] AC-02: `live_endpoints` is `type: array` with `items.type: object` and `items.properties` preserving `url`, `status`, `content_type`, and `body_preview`; `html_pages` is `type: array` with string items.
- [ ] AC-03: Top-level `required:` includes `live_endpoints` and `html_pages` and omits `verdict_hint`, preserving the prompt's intended optional hint semantics without inventing a JSON-Schema `required: false` marker.
- [ ] AC-04: `tmp/draft-authoring-report.md` exists, is non-empty, contains headings `Artifacts`, `Precedent`, `Validation`, `Repairs`, and `Blocked validation`, and lists `examples/api-discovery/steps/endpoint-probe/prompts/probe.yaml` under authored artifacts.
- [ ] AC-05: `yamlgraph graph lint examples/api-discovery/steps/endpoint-probe/graph.yaml` passes, or `tmp/draft-authoring-report.md` records that exact command as blocked with the concrete reason.
- [ ] AC-06: The authoring report records a narrow smoke attempt for the endpoint-probe graph, or records the exact smoke command as blocked with the concrete reason; blocked smoke is honest validation evidence, not a pass claim.
- [ ] AC-07: A regression test or equivalent command-backed check using `yamlgraph.compile.graph_loader.load_and_compile("examples/api-discovery/steps/endpoint-probe/graph.yaml")` passes without raising on the repaired prompt.
- [ ] AC-08: No files under `yamlgraph/**` change under this FR.
- [ ] AC-09: No API-discovery artifact changes occur outside `examples/api-discovery/steps/endpoint-probe/prompts/probe.yaml`.
- [ ] AC-10: Changelog fragment and diary reflection are added.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | The prompt edit must be performed through `scripts/author.sh <task-brief.md>` and verified by the substance of `tmp/draft-authoring-report.md`; adapter exit code alone is not evidence. | GATE |
| C-2 | Framework runtime files, including `yamlgraph/schema_loader.py`, must not change under this FR. If runtime schema behavior needs alteration, stop and open a separate FR. | GATE |
| C-3 | No graph, manifest, tool, orchestrator, or sibling API-discovery step artifact may be edited under this FR. | GATE |
| C-4 | The repair must preserve nested `live_endpoints.items.properties` as model guidance even though the current JSON-Schema loader maps object items to `dict`. | GATE |
| C-5 | The missing committed FR-795 judgement path cited in the FR must not be treated as implementation authority; this draft judgement and any human-accepted final judgement are the governing scope. | GATE |

Authority granted: upon human acceptance of this draft judgement, the enforcer may repair only the endpoint-probe prompt schema dialect and add the directly related authoring report, regression evidence, changelog, and diary artifacts listed above.

**Prior art:** No existing FR addresses this dialect mismatch. FR-794 (python-tool-manifest-root-confinement-fix) attempted to bundle this repair into its own scope but received a SPLIT verdict requiring it to re-enter the pipeline as this separate, graph-authoring-scoped FR — cited FR-794 hits are that same predecessor judgement, not an unresolved overlap.
