# Judgement: FR-810 Router-Visible Tool-Call Outputs

**Prior art:** FR-810-router-visible-tool-call-outputs.md is the judged FR itself (verdict target, not precedent); no other FR touches tool_call output parsing.

**Verdict:** APPROVED WITH REVISIONS - the boundary fix is real and strategically a framework primitive, but authority activates only after the FR freezes the public field name, graph-tool eligibility, parse/error semantics, and deterministic test surface.

**Reviewed against:** `feature-requests/FR-810-router-visible-tool-call-outputs.md`; cited evidence `feature-requests/FR-791-api-discovery-orchestrator.md`; `feature-requests/FR-791-api-discovery-orchestrator.judgement.md`; `feature-requests/FR-792-multi-step-investigation-template.md`; `feature-requests/FR-792-multi-step-investigation-template.judgement.md`; `feature-requests/FR-809-api-discovery-orchestrator-v2-recon-browser-sniff.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.judgement.md`; `docs/diary/diary-2026-08-15-fr791-orchestrator-capstone.md`; repo doctrine `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `reference/graph-yaml.md`.

## What is sound

The problem is real. FR-791 records the exact defect class: platform-confirm skip routing had to key on `candidate_urls.has_platform_hint` because `tool_call` wrappers return child output as JSON strings that edge expressions cannot address (`feature-requests/FR-791-api-discovery-orchestrator.md:148-154`). The diary independently names the same boundary: edge expressions cannot address tool_call wrapper JSON strings, so composed graphs need router-visible parsed state (`docs/diary/diary-2026-08-15-fr791-orchestrator-capstone.md:40-46`).

The first consumer is concrete. FR-810 names FR-809's SPA-without-API branch as the first event needing an edge condition over a field inside a tool-call wrapper (`feature-requests/FR-810-router-visible-tool-call-outputs.md:8-11`), and FR-809 itself currently plans to use a workaround until FR-810 exists (`feature-requests/FR-809-api-discovery-orchestrator-v2-recon-browser-sniff.md:71-75`, `feature-requests/FR-809-api-discovery-orchestrator-v2-recon-browser-sniff.md:100-103`).

The proposed direction aligns with repo doctrine. The current design de-normalizes a typed child output into a string at the `tool_call` boundary (`feature-requests/FR-810-router-visible-tool-call-outputs.md:54-58`), while doctrine says to normalize where external data enters (`.github/copilot-instructions.md:49-52`) and not substitute silent fallbacks (`.github/copilot-instructions.md:216-218`). The implementation surface is also plausible: `tool_call` nodes already store results under a state key and support deterministic `on_error` policy (`reference/graph-yaml.md:730-737`), while graph tool manifests already have a distinct `runtime.type: graph` and `output_key` contract (`reference/graph-yaml.md:1458-1464`).

Strategic classification: **Framework primitive**. The cited use cases are not one-off: FR-809 needs it immediately, FR-792 generalizes the orchestrator plus graph-runtime step manifest pattern to multiple investigation domains (`feature-requests/FR-792-multi-step-investigation-template.md:33-47`), and the existing abstraction forces routing on predictions rather than findings (`feature-requests/FR-810-router-visible-tool-call-outputs.md:31-39`).

## Required revisions

### R-1: Freeze the public field name to `parsed_key`

Rewrite the Summary, Ideal Result, Proposed Solution, Acceptance Criteria, and docs plan so the only authorized public field is `parsed_key`. Remove the alternate `parse_result: true` / `result_key` spelling from the FR. The current text introduces `parse_result` / `result_key` as the mechanism (`feature-requests/FR-810-router-visible-tool-call-outputs.md:26-28`) but the example and proposed solution use `parsed_key` (`feature-requests/FR-810-router-visible-tool-call-outputs.md:62-75`, `feature-requests/FR-810-router-visible-tool-call-outputs.md:79-84`). No aliases, migrations, or synonym fields are authorized.

### R-2: Define graph-tool eligibility and dynamic-tool behavior

State that `parsed_key` is valid only when the resolved tool is a graph-runtime tool, including graph manifests with `runtime.type: graph` and any existing inline graph-tool form with the same invocation semantics. Because `tool_call.tool` may be a state expression resolved at runtime (`reference/graph-yaml.md:696-706`, `reference/graph-yaml.md:734-735`), the FR must define two enforcement points: the linter warns when a statically known shell/python tool uses `parsed_key`, and runtime treats a dynamically resolved non-graph tool with `parsed_key` as a node failure governed by `on_error`. Do not silently ignore `parsed_key` on non-graph tools.

### R-3: Specify the parse, state, and failure contract exactly

Add a contract section stating that parsing occurs only after the child graph tool succeeds; the wrapper under `state_key` is still returned unchanged; JSON strings must parse to an object/dict; dict outputs pass through; invalid JSON, lists, scalars, missing child output, or failed child wrappers are parse failures; parse failures never emit an empty dict or partial parsed state. The new `parsed_key` must be included in the generated state surface exactly like `state_key` so edge conditions can address it. This closes the untyped-dict and silent-fallback gap against the repo type/error doctrine (`.github/copilot-instructions.md:216-218`).

### R-4: Make `on_error` outcomes mechanically testable

Revise AC-03 to enumerate expected outcomes for supported `tool_call` error modes: `on_error: fail` raises at the node; `on_error: skip` returns a failure envelope under `state_key` and does not set `parsed_key`; `retry` and `fallback` remain rejected at graph load as current `tool_call` docs require (`reference/graph-yaml.md:736-737`). The FR currently says parse failure follows `on_error` (`feature-requests/FR-810-router-visible-tool-call-outputs.md:83-84`, `feature-requests/FR-810-router-visible-tool-call-outputs.md:99-100`) but does not define the state shape that tests must assert.

### R-5: Replace the demonstration ambiguity with deterministic enforcement evidence

Rewrite AC-06 so FR-810 itself has a deterministic committed witness: either a unit-test fixture graph routes on `parsed_key` for a real skip condition, or a governed example/FR-809 graph does so through the graph-authoring route with validation evidence. Do not make FR-810 enforcement depend on FR-809 being implemented, because FR-809 is still Proposed (`feature-requests/FR-809-api-discovery-orchestrator-v2-recon-browser-sniff.md:3-6`) and graph/prompt artifacts under governed paths require `scripts/author.sh` (`.github/copilot-instructions.md:15`). The current "FR-809 or a committed demo graph" criterion is directionally right but underspecified (`feature-requests/FR-810-router-visible-tool-call-outputs.md:101-102`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `tool_call` node configuration/model support for optional `parsed_key` |
| D-2 | `tool_call` runtime support that emits parsed graph-tool output under `parsed_key` while preserving the existing wrapper under `state_key` |
| D-3 | Dynamic state/lint support needed for edge conditions to address `parsed_key` and for non-graph misuse to warn/fail as defined |
| D-4 | Unit tests with requirement markers covering routing on parsed fields, absent-`parsed_key` unchanged behavior, parse failures, non-graph misuse, and `on_error` outcomes |
| D-5 | `reference/graph-yaml.md` documentation for `parsed_key`, graph-tool eligibility, examples, and failure behavior |
| D-6 | Capability/requirement registry entry and changelog fragment |
| D-7 | Optional demonstration graph or FR-809 integration only if produced through the graph-authoring route and not used as a substitute for deterministic tests |

Not authorized: `parse_result`, `result_key`, or any alias/shim field; automatic parsing of every `tool_call` wrapper; changing the wrapper shape `{task_id, tool, success, result, error}`; changing existing `state_key` semantics; changing shell/python tool output behavior; changing graph manifest declaration or graph-tool invocation semantics; adding a new edge-condition DSL; implementing FR-809 recon/browser-sniff routing; changing FR-792 scaffold behavior beyond a comment that names `parsed_key`; CI, hooks, judge/review doctrine, or other enforcement-infrastructure changes.

## Revised acceptance criteria

- [ ] AC-01: `tool_call` node config accepts exactly one new optional field, `parsed_key`; `parse_result`, `result_key`, and other aliases are rejected or absent from the public schema.
- [ ] AC-02: A graph-runtime tool call with `parsed_key` exposes the child graph's object output under that state key, and a unit test routes an edge condition on a parsed field.
- [ ] AC-03: Without `parsed_key`, the observable `tool_call` behavior and wrapper shape under `state_key` remain unchanged; existing `tool_call` tests stay green.
- [ ] AC-04: JSON-string graph outputs parse only when they are JSON objects; dict outputs pass through; invalid JSON, lists, scalars, missing child output, and failed child wrappers are parse failures with no empty-dict substitution.
- [ ] AC-05: Parse failures with `parsed_key` have explicit tests for `on_error: fail` and `on_error: skip`; `skip` returns a failure envelope under `state_key` and does not set `parsed_key`.
- [ ] AC-06: Lint warns when `parsed_key` is configured on a statically known shell/python tool, and runtime fails under the node `on_error` policy when a dynamic tool expression resolves to a non-graph tool.
- [ ] AC-07: `reference/graph-yaml.md` documents `parsed_key` with a routing example, graph-tool-only eligibility, wrapper preservation, and failure behavior.
- [ ] AC-08: A capability/requirement entry exists for router-visible graph-tool outputs, every new test has the exact `@pytest.mark.req("REQ-YG-XXX")` marker, `python scripts/req_coverage.py --strict` passes, and a changelog fragment is added.
- [ ] AC-09: A deterministic committed witness uses `parsed_key` for a real skip condition; if that witness is a governed graph/prompt artifact or FR-809 integration, it is authored via `scripts/author.sh` with validation evidence.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-5 are folded into the FR. | GATE |
| C-2 | The only public field name authorized is `parsed_key`; aliases and migration shims are out of scope. | GATE |
| C-3 | `parsed_key` must fail closed on parse errors and non-graph tool misuse; silent ignore, empty-dict substitution, or best-effort fallback is forbidden. | GATE |
| C-4 | Existing wrapper shape, `state_key` behavior, graph manifest declaration, and graph-tool invocation semantics must remain unchanged. | GATE |
| C-5 | Any committed graph or prompt artifact used as a demonstration must be produced through the graph-authoring route; FR-810 must not implement FR-809's orchestrator v2 behavior. | GATE |
| C-6 | Tests must be requirement-traceable and must include both positive routing and negative failure-state witnesses. | GATE |

Authority granted: after the required revisions are folded in, the enforcer may implement only the opt-in `parsed_key` framework primitive for graph-runtime `tool_call` outputs, its tests, docs, traceability, changelog, and any governed demonstration evidence within the frozen scope above.
