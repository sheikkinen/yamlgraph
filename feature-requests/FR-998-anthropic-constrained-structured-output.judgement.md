# Judgement: FR-998 Structured output must be constrained, not requested - Anthropic `list[str]` fields arrive as strings

**Prior art:** dispositioned in the parent FR header ([FR-998](FR-998-anthropic-constrained-structured-output.md) — FR-873, FR-059/264/CAP-117, FR-464, FR-678, FR-679); no REJECTED FR in this territory.

**Route:** `scripts/judge.sh` (Copilot backend, `gpt-5.6-sol`, session 329ae6b1) on lane commit `ab41ea35`, 2026-09-05 14:45. Folded verbatim; R-1…R-5 incorporated into the FR as S-1…S-7 and revised AC-01…14.

**Verdict:** APPROVED WITH REVISIONS - constrained decoding is the right framework-level cure for the reproduced Anthropic type lie, but authority activates only after the FR freezes an invocation-time fallback design, a typed provider boundary, its dependency floor, and regression criteria for all three execution surfaces.

**Reviewed against:** `feature-requests/FR-998-anthropic-constrained-structured-output.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `docs/spikes/list-type-lie-2026-09-05/probe.py`; `docs/spikes/list-type-lie-2026-09-05/probe-output.txt`; `docs/2026-09-05-research-plan-cap-journey-census.md`; `feature-requests/FR-873-vision-provider-type-lie.md`; `feature-requests/FR-873-vision-provider-type-lie.judgement.md`; `feature-requests/FR-464-deepseek-structured-output-fallback.md`; `feature-requests/FR-678-narrow-agent-structured-output-catch.md`; `feature-requests/FR-679-consolidate-retry-fallback-post-676.md`; `feature-requests/FR-995-outsider-reader.md`; `yamlgraph/executor_base.py`; `yamlgraph/executor.py`; `yamlgraph/executor_async.py`; `yamlgraph/utils/llm_factory.py`; `yamlgraph/utils/llm_factory_async.py`; `yamlgraph/utils/llm_providers.py`; `yamlgraph/node_factory/race_node.py`; `yamlgraph/tools/agent.py`; `yamlgraph/config.py`; `tests/unit/test_fr679_shared_attempt_invoke.py`; `tests/unit/test_fr678_narrow_structured_catch.py`; `tests/unit/test_race_node.py`; `capabilities/CAP-05-tool-agent-integration.yaml`; `capabilities/CAP-164-structured-output-fallback.yaml`; `ARCHITECTURE.md`; `pyproject.toml`; `.github/skills/outsider-view/adapters/graph.yaml`; `.github/skills/outsider-view/adapters/prompts/outsider.yaml`.

## What is sound

The defect is real and unusually well witnessed. The committed probe uses a real `claude-sonnet-4-5` client and the same Pydantic schema on both paths (`docs/spikes/list-type-lie-2026-09-05/probe.py:12-35`). Three `function_calling` runs return `str` for both list fields and fail with `list_type`, while two `json_schema` runs parse successfully with list-valued fields (`docs/spikes/list-type-lie-2026-09-05/probe-output.txt:1-28`). The raw bullet encoding also proves why FR-873's narrower JSON-string repair would not cover this incident (`feature-requests/FR-873-vision-provider-type-lie.md:48-78`; `FR-998:45-55`).

The causal chain matches the code. The ordinary executor binds structured output without a method and invokes the returned runnable (`yamlgraph/executor_base.py:379-401`); the native-async race path does the same before `ainvoke(..., config={"run_id": run_id})` (`yamlgraph/node_factory/race_node.py:113-143`); and the agent has both a default binding and a deliberate `method="function_calling"` recovery tier (`yamlgraph/tools/agent.py:57-109`). Centralizing provider method selection across those production call sites is therefore a framework concern, not another consumer repair. It follows the repository's boundary law and `partial_remediation` cure (`.github/copilot-instructions.md:41-43`, `67`) and honors the repeated-incident threshold behind `two_strike_split` (`.github/copilot-instructions.md:109`).

Scope and responsibility are coherent: select the strongest Anthropic structured-output method, preserve an explicit fallback for unsupported Anthropic models, and route every existing structured-output surface through that policy. Schema coercion, prompt rewriting, and non-Anthropic behavior are correctly excluded (`FR-998:101-127`). The alternatives are substantive, the prior FR-873/464/678/679 decisions are dispositioned, and the raw-output record contains concrete surprising details rather than only a score (`FR-998:9-10`, `45-57`; `.github/copilot-instructions.md:107`).

Most tests are directly derivable. The proposed method-selection, incident-payload, one-fallback, propagation, race, and agent witnesses map to observable calls and outputs (`FR-998:89-95`). Existing suites already expose the seams that must remain stable: shared sync/threaded-async attempt policy (`tests/unit/test_fr679_shared_attempt_invoke.py:93-158`), the agent's explicit `function_calling` tier (`tests/unit/test_fr678_narrow_structured_catch.py:132-215`), and the race node's native async fallback (`tests/unit/test_race_node.py:1289-1333`).

Strategic classification: **Framework primitive**. Three runtime surfaces already perform the same provider-shaping operation (`executor_base`, race, and agent), the defect class has crossed consumers, and no current abstraction selects constrained Anthropic output while preserving provider-specific fallback behavior. This is one concern and does not require a split.

## Required revisions

### R-1: Repair the evidence contract and bound the guarantee

Replace the dangling first-incident references to `docs/spikes/outsider-llm-2026-09-05/` and its `EXPECTATIONS.md`; that committed path does not exist in the reviewed tree (`FR-998:8`, `24-26`). Cite the exact committed outsider artifact that contains the incident, or state that the committed FR-998 probe is the authoritative witness. Add the doctrine-required explicit answer: `is_this_a_graph: No - this is deterministic provider dispatch and exception policy, not an LLM pipeline`.

Replace "on every supported Anthropic model" with the enforceable contract: models accepted by Anthropic's `json_schema` path receive constrained output; a model that returns the narrowly classified unsupported-feature error receives exactly one `function_calling` attempt with an observable log. Do not claim that fallback models guarantee list fidelity, because fallback intentionally restores the behavior that produced the incident (`FR-998:18-19`, `59-63`, `85-87`).

Record the minimum `langchain-anthropic` version that exposes the relied-on `method="json_schema"` and GA `output_config.format` behavior. The FR cites the locally installed 1.5.1 implementation, while the committed dependency floor is `langchain-anthropic>=0.3.0` (`FR-998:14`, `41`; `pyproject.toml:25`). Raise the declared floor to the earliest version verified to provide this contract, or add committed evidence that the existing floor provides it. The implementation must not rely on one workstation's resolved version.

### R-2: Freeze an invocation-time shared API, not only a binder

Replace S-1 through S-3 with a shared policy that owns both binding and invocation. `with_structured_output(...)` creates a runnable; the provider request and its `BadRequestError` occur when that runnable is invoked. A helper that only returns the bound runnable cannot perform S-3 (`FR-998:67-87`; `yamlgraph/executor_base.py:400-401`; `yamlgraph/node_factory/race_node.py:137-141`).

Fold this exact contract into the FR:

1. Add a focused shared module, `yamlgraph/utils/structured_output.py`, rather than growing the 421-line `executor_base.py` past the repository's 450-line maximum (`yamlgraph/executor_base.py:421`; `CLAUDE.md:79-84`).
2. Define one binding function with an explicit override, equivalent to `bind_structured_output(llm, output_model, *, method: str | None = None)`. An explicit method is forwarded unchanged. With no override, Anthropic selects `json_schema`; every other provider omits the `method` argument.
3. Define sync and native-async invocation functions around that binder. Each invokes the constrained runnable, catches only the unsupported Anthropic structured-output error frozen by R-3, logs once, binds with the explicit `function_calling` override, and invokes exactly once more. The async function must use `ainvoke`; it must not move the race path onto a thread.
4. Route `attempt_structured_invoke`, `_invoke_candidate_async`, and both agent finalization paths through the shared policy. Preserve the agent's existing explicit `function_calling` recovery tier: calling the binder with that override must never reselect `json_schema` (`yamlgraph/tools/agent.py:92-109`).
5. Preserve invocation configuration. In particular, the race path must retain LangSmith `run_id` configuration and cancellation closure semantics for both primary and fallback attempts (`yamlgraph/node_factory/race_node.py:128-143`).

The existing FR-464 JSON-extraction fallback and the agent's later strict-schema/tool-choice/plain tiers remain callers around this policy; do not absorb or reorder them in FR-998.

### R-3: Specify provider and error classification without class-name guessing

Delete the unresolved "`type(llm).__name__ == "ChatAnthropic"` or `isinstance` - Judge to fix which" choice (`FR-998:79`). Class-name equality is not provider identity and fails for subclasses or wrappers. Direct provider imports in generic execution modules also violate the multi-provider factory boundary (`CLAUDE.md:59-67`).

Place Anthropic type/error knowledge in the existing provider boundary (`yamlgraph/utils/llm_providers.py`, whose provider constructors already use lazy imports at lines 1-5 and 125-139). The shared policy may call provider-boundary predicates, but `executor_base.py`, `race_node.py`, and `tools/agent.py` must not import Anthropic SDK or LangChain provider classes.

Freeze the fallback predicate as all of:

1. the LLM is an actual Anthropic chat model according to the provider-boundary predicate;
2. the exception is Anthropic's typed `BadRequestError`;
3. its status is HTTP 400; and
4. its structured error payload identifies unsupported `output_config` / structured-output capability.

A Pydantic `ValidationError`, authentication or permission error, rate limit, timeout, network error, server error, unrelated Anthropic 400, binding/programming error, or error from the fallback invocation must propagate unchanged. Do not use `type(...).__name__`, `str(exception)` alone, or a broad catch that converts unknown failures into a second model call.

### R-4: Preserve composition with the existing fallback state machines

Expand the test plan from "routes through the shared entry point" to behavioral composition tests. The new primary policy sits inside three different existing state machines: FR-464's plain JSON extraction in `attempt_structured_invoke` (`yamlgraph/executor_base.py:402-419`), the race node's native-async extraction and run-ID handling (`yamlgraph/node_factory/race_node.py:142-159`), and the agent's `invalid_json_schema` / `response_format` -> `function_calling` -> optional plain re-invoke tiers (`yamlgraph/tools/agent.py:96-133`).

Add direct tests proving:

1. explicit `method="function_calling"` is passed through and cannot recurse to `json_schema`;
2. the typed unsupported-feature fallback works in sync and native-async invocation;
3. the race fallback retains invocation config and uses a distinct run ID for its second request;
4. FR-464 `response_format` extraction still works for a non-Anthropic provider;
5. the agent's existing invalid-schema and rejected-tool-choice tiers still run in their original order;
6. every non-authorized exception class propagates without a second invocation; and
7. the source contains one production call expression matching `.with_structured_output(`, while tests and documentation are excluded from that source check.

These tests are required in addition to the incident payload witness; a spy proving only that a helper name was called would not exercise the policy seam.

### R-5: Correct traceability and make the live witness executable

Do not create a duplicate capability record. Extend `CAP-164 Structured Output JSON Fallback`, which already owns executor/race structured-output provider rejection (`capabilities/CAP-164-structured-output-fallback.yaml:1-26`; `ARCHITECTURE.md:483`, `2158-2167`), with a new FR-998 requirement and the agent/shared-policy modules. Keep the existing agent requirement `REQ-YG-422` where its established agent behavior is being regression-tested (`capabilities/CAP-05-tool-agent-integration.yaml:55-63`; `ARCHITECTURE.md:652`). Every new test must carry the applicable requirement marker (`.github/copilot-instructions.md:167-169`).

S-5 currently names neither a committed graph nor an executable command and calls the live run "not a gate" even though AC-06 makes it mandatory (`FR-998:97-99`, `112`). Revise it to name the exact existing graph/prompt fixture, command, expected output fields, artifact path, and credential prerequisite. It is a GATE. If satisfying it requires creating or materially editing a graph or prompt artifact, route that artifact through the graph-authoring process; FR-998 itself does not authorize an incidental graph/prompt change.

Specify AC-08's exact insertion point in FR-995 (for example, one new `Related` entry and one implementation-record sentence); "Fixtures/plan §13 pointer" does not identify a section in `feature-requests/FR-995-outsider-reader.md` (`FR-998:114`; `FR-995:43-73`, `144`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-998-anthropic-constrained-structured-output.md` folding R-1 through R-5 |
| D-2 | `yamlgraph/utils/structured_output.py` shared binding plus sync/native-async constrained invocation policy |
| D-3 | `yamlgraph/utils/llm_providers.py` Anthropic identity and typed unsupported-feature classification at the provider boundary |
| D-4 | `yamlgraph/executor_base.py`, `yamlgraph/executor.py`, `yamlgraph/executor_async.py`, and `yamlgraph/utils/llm_factory_async.py` provider-policy wiring without retry/backoff changes |
| D-5 | `yamlgraph/node_factory/race_node.py` native-async policy wiring with run-ID and cancellation semantics preserved |
| D-6 | `yamlgraph/tools/agent.py` shared-policy wiring with its existing fallback tiers preserved |
| D-7 | Focused unit/integration tests for method selection, incident reproduction, typed sync/async fallback, explicit override, propagation, and composition |
| D-8 | `capabilities/CAP-164-structured-output-fallback.yaml` plus generated/maintained `ARCHITECTURE.md` traceability for the new FR-998 requirement |
| D-9 | Dependency floor if R-1 proves it necessary; changelog fragment; exact FR-995 cross-reference; live witness artifact; FR implementation record; diary entry |

Not authorized: schema-level string-to-list repair; markdown bullet parsing; widening generated Pydantic field types; prompt wording changes; changes to non-Anthropic default method selection; model-name allowlists; retry-count, retryability, backoff, timeout, cancellation, or race-winner changes; removal or reordering of FR-464/456/809 fallbacks; new graph or prompt artifacts outside the graph-authoring route; unrelated agent tool-loop changes; provider SDK imports outside the provider boundary.

## Revised acceptance criteria

- [ ] AC-01: The FR's Research field cites only existing committed evidence, includes the explicit `is_this_a_graph: No` rationale, and identifies the committed raw-output artifact as the authoritative reproduction.
- [ ] AC-02: The FR records the earliest verified `langchain-anthropic` version that supports the selected `json_schema`/`output_config.format` contract; `pyproject.toml` declares at least that floor, or committed evidence proves the current floor sufficient.
- [ ] AC-03: `yamlgraph/utils/structured_output.py` owns the only production call expression `.with_structured_output(`. Its binder forwards an explicit method unchanged, selects `json_schema` only for Anthropic when no override is supplied, and omits `method` for non-Anthropic models.
- [ ] AC-04: Provider identity and unsupported-feature classification live in `yamlgraph/utils/llm_providers.py`; generic executor, race, and agent modules contain no Anthropic SDK/provider-class import and no class-name equality check.
- [ ] AC-05: A typed Anthropic `BadRequestError` with HTTP 400 and a structured unsupported-`output_config` diagnostic causes exactly one `function_calling` invocation and exactly one INFO log naming the model and FR-998, in both sync and native-async helpers.
- [ ] AC-06: Pydantic `ValidationError`, auth/permission, rate-limit, timeout/network, server, unrelated Anthropic 400, binding/programming, and fallback-invocation errors each propagate unchanged and perform no unauthorized extra invocation.
- [ ] AC-07: The recorded bullet-string payload for `unclear: list[str]` fails on the old/default-method test path and returns a model whose field is a real `list[str]` on the Anthropic `json_schema` path.
- [ ] AC-08: `attempt_structured_invoke`, race, and both agent finalization paths use the shared policy. A direct explicit-override test proves the agent's `function_calling` recovery cannot be upgraded back to `json_schema`.
- [ ] AC-09: Existing FR-464 executor and race JSON-extraction tests, FR-678 agent exception-boundary tests, FR-679 shared-attempt tests, and agent invalid-schema/tool-choice fallback tests pass without weakening their assertions.
- [ ] AC-10: Native-async race tests prove both constrained and unsupported-model fallback invocations receive tracing config, use distinct run IDs, and preserve cancellation behavior.
- [ ] AC-11: `CAP-164` contains a new FR-998 requirement covering constrained Anthropic output and typed fallback across executor, race, and agent; `ARCHITECTURE.md` reflects it; every new test carries that requirement marker; `python scripts/req_coverage.py --strict` and `lint-imports` pass.
- [ ] AC-12: The FR names and records one credentialed live command through a real YAMLGraph `llm` node on `claude-sonnet-4-5`; the committed `docs/spikes/list-type-lie-2026-09-05/after/` artifact records the command, model, git SHA, and parsed `list[str]` field values.
- [ ] AC-13: The RED commit precedes the GREEN commit; the focused test set and existing structured-output regression tests pass; the changelog fragment uses `type: fix` and `scope: llm`.
- [ ] AC-14: FR-995 receives only the exact cross-reference frozen by R-5; the FR-998 implementation record lists any deviations; the diary entry contains `**Seed:**`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-5 are folded into `feature-requests/FR-998-anthropic-constrained-structured-output.md`. | GATE |
| C-2 | Do not invoke or re-run the judge while enforcing this FR. | GATE |
| C-3 | The unsupported-model retry is exactly one `function_calling` attempt after the narrowly typed Anthropic capability error; all other errors remain visible. | GATE |
| C-4 | Non-Anthropic method selection and every existing FR-464/456/809 fallback tier retain their current behavior and order. | GATE |
| C-5 | No provider class-name heuristic or provider SDK import may enter generic executor, race, or agent modules. | GATE |
| C-6 | No schema coercion, bullet parsing, prompt rewrite, or downstream `str | list[str]` contract may be added under FR-998. | GATE |
| C-7 | No graph or prompt artifact may be created or materially modified unless separately routed through the graph-authoring contract. | GATE |
| C-8 | If a real supported Anthropic model rejects `json_schema` for a reason outside the frozen unsupported-capability predicate, stop and revise the FR; do not widen the catch or add a model-name guess. | GATE |

Authority granted: after the required revisions are folded, enforcement may implement the shared Anthropic constrained-output policy, its single typed fallback, call-site wiring, traceability update, and witnesses within the frozen scope above.
