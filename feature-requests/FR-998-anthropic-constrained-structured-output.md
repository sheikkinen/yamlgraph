# Feature Request: Structured output must be constrained, not requested — Anthropic `list[str]` fields arrive as strings

**Priority:** HIGH
**Type:** Bug
**Status:** Enforced 2026-09-05 — PR #599 (stacked on the plan PR #596); RED `175f4151` → GREEN `7fea7d5a`; [judgement](FR-998-anthropic-constrained-structured-output.judgement.md) R-1…R-5 folded below; [implementation record](#implementation-record-2026-09-05)
**Effort:** 0.5 day
**Requested:** 2026-09-05
**First consumer / first event:** any `llm` node with an inline `schema:` that declares a `list[...]` field, running on an Anthropic model — at the moment the model answers. Witnessed first by the outsider-reader spike 2 (`docs/spikes/outsider-llm-2026-09-05/`, run 1, 2026-09-05 08:02Z), whose `unclear: list[str]` field killed the run with `on_error: fail`. Second consumer: `scripts/outsider.sh`'s successor (FR-995 → API transport), which needs list fields to be lists.
**Research:** in-body — the *Investigation* section below is the committed record; `is_this_a_graph: No` (deterministic provider dispatch and exception policy, not an LLM pipeline). The authoritative reproduction is `docs/spikes/list-type-lie-2026-09-05/probe-output.txt`; the first incident is quoted from the outsider spike 2 record ([EXPECTATIONS.md](../docs/spikes/outsider-llm-2026-09-05/EXPECTATIONS.md) line 10, merged in PR #593) as context. causal chain to file and line, a live reproduction with the probe and log committed at [docs/spikes/list-type-lie-2026-09-05/](../docs/spikes/list-type-lie-2026-09-05/) (`probe.py`, `probe-output.txt`), and a dispositioned alternatives table. No `scripts/research.sh` run: the problem is a reproduced defect with one verified fix, not an open design space.
**Prior art:** [FR-873](FR-873-vision-provider-type-lie.md) (Enforced 2026-08-24) — the *identical* defect (`paragraphs` as a JSON-encoded string, `list_type`) in the deviant-daily consumer, fixed **at the consumer** with a capture schema + `json.loads` repair; the framework boundary was left as it was. This FR is the third witnessed occurrence of the class (FR-059 diary → FR-873 → spike 2 + 3 probe runs) and moves the cure to the framework. FR-873's judge rule — *repair only when `json.loads` yields `list[str]`; never guess* — is inherited and is why Alternative B is not chosen: today's reproduction returned a **markdown bullet list**, not JSON, so the FR-873 repair would not have fired either. [FR-059](059-agent-normalize-content-to-string.md) / [FR-264](FR-264-race-node-parse-json-content-normalization.md) / [CAP-117](../capabilities/CAP-117-race-node-parse-json-content-normalization.yaml) — normalise `content: str | list` at the message boundary (`yamlgraph/utils/content.py`); a different axis (message content, not tool-argument field types); not touched. [FR-464](FR-464-deepseek-structured-output-fallback.md) — the `"response_format"` string-match fallback in `attempt_structured_invoke`; this FR shows the match cannot fire for the Anthropic failure and replaces the condition for the new path only. [FR-678](FR-678-narrow-agent-structured-output-catch.md) — no broad swallow; the fallback here catches one typed provider error. No REJECTED FR in this territory (`grep -l "json_schema\|strict tool\|list_type" feature-requests/*.md` → FR-873, FR-631 [interpolation, unrelated], FR-956/706/270/986/683/764 [unrelated matches on "strict"]).

## Summary

`yamlgraph` asks the provider for structured output with `llm.with_structured_output(output_model)` and no `method` ([executor_base.py L400](../yamlgraph/executor_base.py#L400), [race_node.py L137](../yamlgraph/node_factory/race_node.py#L137), [tools/agent.py L93, L107](../yamlgraph/tools/agent.py#L93)). For `ChatAnthropic` (langchain-anthropic 1.5.1) that default is `method="function_calling"`: a forced, non-strict tool call. The schema is a *request*; `claude-sonnet-4-5` answers `list[str]` fields with a single string — sometimes a JSON array in quotes, sometimes a markdown bullet list — and Pydantic rejects it (`list_type`). The FR-464 fallback never fires (it looks for `"response_format"` in the error text; a `ValidationError` propagates), so the node fails and, with `on_error: fail`, the run dies.

The fix is to use the provider's **constrained decoding** — `method="json_schema"` (Anthropic `output_config.format`, GA in the installed SDK) — for Anthropic models, so the shape is guaranteed by the decoder instead of requested from the model. Verified live: 2/2 runs correctly typed against the same prompt that failed 3/3 under the default.

## Value Statement

Anyone who writes `type: list[str]` in a prompt schema gets a list, on every run, on every Anthropic model that accepts constrained decoding — instead of a run that dies on a container-type error while the content was correct. A model that rejects constrained decoding gets exactly one forced-tool-call attempt (today's behaviour, today's exposure) and an INFO line saying so; no list-fidelity guarantee is claimed on that path.

## Problem

### Witnessed incident

Spike 2 of the outsider reader, run 1 (`/Users/sheikki/Documents/src/outsider-spike-llm/out/positive-claude-sonnet-4-5-20260905T080227Z.log`, recorded in [plan §13](../docs/2026-09-05-research-plan-cap-journey-census.md) and [EXPECTATIONS.md](../docs/spikes/outsider-llm-2026-09-05/EXPECTATIONS.md) line 10):

```
[ERROR] yamlgraph.error_handlers: Node outsider failed (on_error=fail): 1 validation error for OutsiderReading
unclear
  Input should be a valid list [type=list_type, input_value='["capabilities/CAP-*.yam...ructure do these have?]', input_type=str]
```

The spike worked around it by declaring the two list fields as `str` and splitting in its own code (`_lines()` in `tools.py`) — a consumer-side repair, exactly the FR-873 shape, for the second time.

### Investigation (2026-09-05)

**Causal chain**

1. [`attempt_structured_invoke`](../yamlgraph/executor_base.py#L378) calls `llm.with_structured_output(output_model)` with default arguments. The async path (`llm_factory_async.py`, FR-679) shares this function; the race node ([L137](../yamlgraph/node_factory/race_node.py#L137)) and the agent tool ([L93](../yamlgraph/tools/agent.py#L93), [L107](../yamlgraph/tools/agent.py#L107)) repeat the same call.
2. `ChatAnthropic.with_structured_output` defaults to `method="function_calling"` (`.venv/lib/python3.14/site-packages/langchain_anthropic/chat_models.py` L2063): `bind_tools([schema], tool_choice=<name>)` — forced tool call, `strict` not set — parsed by `PydanticToolsParser`. The model is *told* the argument schema; nothing constrains the tokens it emits.
3. `claude-sonnet-4-5` emits array-typed tool arguments as one string. Two encodings observed: JSON-array-in-a-string (spike run 1) and a markdown bullet list (`"\n- \"yamlgraph\" · is this…\n- \"FR-990\" · …"`, probe runs 1–3).
4. `PydanticToolsParser` → `ValidationError: list_type`. The FR-464 fallback condition `"response_format" in str(struct_err)` is false; the error propagates; `on_error: fail` ends the run.

**Live reproduction** — `docs/spikes/list-type-lie-2026-09-05/probe.py`, exact spike prompt and input (`inputs/positive.md`), schema restored to run-1 shape (`unclear`, `needs` as `list[str]`), `claude-sonnet-4-5`, T=0, `include_raw=True` so the raw tool arguments are visible before parsing. Log: `probe-output.txt` (`*.log` is gitignored).

| method | run | raw `unclear` type | parse | note |
|---|---|---|---|---|
| `function_calling` (framework default) | 1 | `str` | `list_type` ×2 | bullet list: `"\n- \"yamlgraph\" · is this the name of this project or a tool it uses?\n- \"FR-990\" · what does the FR pref…"` |
| `function_calling` | 2 | `str` | `list_type` ×2 | byte-identical opening to run 1 |
| `function_calling` | 3 | `str` | `list_type` ×2 | same encoding, one wording change ("or a dependency?") |
| `json_schema` (constrained) | 1 | — (content is the JSON object) | OK | `unclear=5 needs=0` |
| `json_schema` | 2 | — | OK | `unclear=7 needs=0` |

Surprising details a fabricated log would not contain: the failing encoding is *not* JSON (so `json.loads` repair — FR-873's cure and spike 2's `_lines()` first branch — is useless against it); the three failing runs are near-identical at T=0 (this is a stable behaviour of the model under non-strict tool use, not noise); and under `json_schema` the *content* changed too (`needs` went 6–7 → 0 for the same input), which is out of scope here but is recorded so nobody attributes it later to a prompt edit.

**Why the FR-464 fallback cannot save it.** The fallback was written for providers that reject `response_format` at request time (DeepSeek, FR-464). Anthropic accepts the request and lies in the answer; the error is a Pydantic `ValidationError`, produced client-side, whose text never contains `response_format`.

**Model gate for the fix.** Anthropic structured outputs (`output_config.format`) require Sonnet 4.5 / Opus 4.1 or later (per langchain-anthropic's `convert_to_anthropic_tool` note, L2323, and the SDK comment at L1463 that betas are no longer required). The repo default `ANTHROPIC_MODEL` is `claude-haiku-4-5` ([config.py L67](../yamlgraph/config.py#L67), supported). Graph inventory: 25× `claude-haiku-4-5`, 7× `claude-sonnet-4-20250514`, 6× `claude-sonnet-4-6`, 3× `claude-opus-4.6`, 1× `claude-3-haiku-20240307`. The last two families are the gate's edge: `claude-sonnet-4-20250514` and `claude-3-haiku` are expected to return an API error for `output_config`; the fix must fall back to today's behaviour for them, on the provider's **typed** error, not a substring.

## Ideal Result

A prompt schema that says `list[str]` produces a `list[str]` on every Anthropic model that accepts constrained decoding, because the decoder — not the model's goodwill — enforces the shape. On a model that rejects constrained decoding the framework makes exactly one forced-tool-call attempt (today's behaviour, with today's exposure to the lie) and says so in the log. The codebase has **one** place where "how do we ask this provider for a shape, and what do we do when it refuses" is decided, at the provider boundary — not four copies of a library default.

## Proposed Solution — Alternative A: constrained decoding for Anthropic (revised per judgement R-2/R-3)

### S-1: a shared structured-output policy module

New `yamlgraph/utils/structured_output.py` (not `executor_base.py`, which is at 421 lines against the 450 cap). It owns **binding and invocation**, because `with_structured_output(...)` only builds a runnable — the provider request, and therefore the unsupported-feature error, happens at `invoke`/`ainvoke`:

```python
def bind_structured_output(llm, output_model, *, method: str | None = None):
    """Explicit method is forwarded unchanged; otherwise Anthropic → json_schema, others → library default."""
    if method is not None:
        return llm.with_structured_output(output_model, method=method)
    if is_anthropic_chat_model(llm):                       # provider boundary, R-3
        return llm.with_structured_output(output_model, method="json_schema")
    return llm.with_structured_output(output_model)

def invoke_structured(llm, output_model, messages, **config):
    try:
        return bind_structured_output(llm, output_model).invoke(messages, **config)
    except Exception as err:
        if not is_anthropic_unsupported_structured_output(llm, err):   # provider boundary, R-3
            raise
        logger.info("Anthropic constrained output unsupported on %s; one forced-tool-call attempt (FR-998)", model_name(llm))
        return bind_structured_output(llm, output_model, method="function_calling").invoke(messages, **config)

async def ainvoke_structured(llm, output_model, messages, **config): ...   # same shape, ainvoke; never a thread
```

This module is the only production site of the call expression `.with_structured_output(`.

### S-2: provider knowledge stays at the provider boundary

`yamlgraph/utils/llm_providers.py` (already lazy-imports each provider) gains two predicates:

- `is_anthropic_chat_model(llm) -> bool` — `isinstance` against `langchain_anthropic.ChatAnthropic` behind a lazy import; `False` when the package is absent. **No** `type(llm).__name__` equality anywhere.
- `is_anthropic_unsupported_structured_output(llm, err) -> bool` — true only when **all** of: (1) `is_anthropic_chat_model(llm)`; (2) `err` is `anthropic.BadRequestError`; (3) `err.status_code == 400`; (4) the structured error body (`err.body["error"]["message"]`, not `str(err)` alone) identifies `output_config` / structured-output capability as unsupported. Pydantic `ValidationError`, auth/permission, rate limit, timeout/network, 5xx, unrelated Anthropic 400, binding/programming errors, and any error from the **fallback** invocation are outside the predicate and propagate unchanged (FR-678).

`executor_base.py`, `race_node.py`, `tools/agent.py` import neither the Anthropic SDK nor any provider class.

### S-3: route the four call sites; preserve every existing state machine

| Site | Today | After |
|---|---|---|
| `attempt_structured_invoke` ([executor_base.py L400](../yamlgraph/executor_base.py#L400); shared by `executor.py` and `llm_factory_async.py`, FR-679) | `llm.with_structured_output(m).invoke(msgs)` | `invoke_structured(llm, m, msgs)` — FR-464's `"response_format"` JSON-extraction branch stays around it, unchanged and in the same order |
| `_invoke_candidate_async` ([race_node.py L137](../yamlgraph/node_factory/race_node.py#L137)) | `.ainvoke(msgs, config={"run_id": run_id})` | `await ainvoke_structured(llm, m, msgs, config={"run_id": run_id})`; the fallback attempt gets its **own** `uuid4()` run id (FR-720 semantics); FR-464 extraction branch unchanged |
| agent default tier ([agent.py L93](../yamlgraph/tools/agent.py#L93)) | `llm_base.with_structured_output(m)` | `bind_structured_output(llm_base, m)` |
| agent recovery tier ([agent.py L107](../yamlgraph/tools/agent.py#L107)) | `with_structured_output(m, method="function_calling")` | `bind_structured_output(llm_base, m, method="function_calling")` — the explicit override is forwarded; it can never be upgraded back to `json_schema`. The agent's `invalid_json_schema` / `response_format` → `function_calling` → plain re-invoke tiers keep their order (FR-456/678/809) |

No change to retry counts, backoff, timeouts, cancellation, race-winner selection, or non-Anthropic method selection.

### S-4: condemning tests (offline, no API) — `tests/unit/test_fr998_structured_output.py`

RED first, `SKIP=pytest`, then GREEN. Fakes are Anthropic *by predicate* (an object the provider-boundary predicate recognises via monkeypatched `isinstance` target), never by class name.

1. **Method selection** — Anthropic fake through `attempt_structured_invoke` receives `method="json_schema"`; non-Anthropic fake receives no `method` kwarg.
2. **Explicit override** — `bind_structured_output(..., method="function_calling")` forwards it for an Anthropic fake; no recursion to `json_schema`.
3. **The incident** — fake whose default-method invoke returns the recorded bullet-string payload for `unclear: list[str]` (verbatim from `probe-output.txt`) raises `list_type` on the old path; on the `json_schema` path the same fake returns typed lists and the result's `unclear` is a real `list[str]`.
4. **Typed fallback, sync and async** — fake raising a constructed `anthropic.BadRequestError` (status 400, body naming `output_config`) on the first invoke → exactly one second invoke with `function_calling`, exactly one INFO record naming the model and `FR-998`.
5. **Propagation** — parametrised over `ValidationError`, `AuthenticationError`, `RateLimitError`, `APITimeoutError`, `APIConnectionError`, `InternalServerError`, an unrelated 400, `TypeError` from binding, and a `BadRequestError` raised by the **fallback** invoke: each propagates unchanged with no unauthorised extra invocation.
6. **Race composition** — both constrained and fallback invocations receive `config={"run_id": ...}` with **distinct** ids; existing cancellation tests (`tests/unit/test_race_node.py`) unchanged and green.
7. **FR-464 composition** — a non-Anthropic fake raising a `"response_format"` error still reaches JSON extraction in `attempt_structured_invoke` and in the race path.
8. **Agent composition** — existing `tests/unit/test_fr678_narrow_structured_catch.py` tiers pass unweakened; one new test proves tier order unchanged with the shared binder in place.
9. **Single call site** — an AST/grep test asserts exactly one production occurrence of `.with_structured_output(` under `yamlgraph/`, tests and docs excluded.

Existing suites that must stay green with no assertion weakened: `test_fr679_shared_attempt_invoke.py`, `test_fr678_narrow_structured_catch.py`, `test_race_node.py`, FR-464 executor/race extraction tests.

### S-5: live witness — a GATE, one credentialed run

Command (no graph or prompt edit; `examples/demos/five-whys/prompts/ask_why.yaml` already declares `chain: list[str]` and the graph uses the default provider):

```bash
ANTHROPIC_MODEL=claude-sonnet-4-5 yamlgraph graph run examples/demos/five-whys/graph.yaml --var problem="Deployment failed on Friday" --full
```

Prerequisite: `ANTHROPIC_API_KEY`. Record under `docs/spikes/list-type-lie-2026-09-05/after/run-evidence.txt`: the command, model, git SHA of the code under test, the `[INFO] Creating LLM` line, and the parsed `chain` values showing a real list. Committed as `.txt` (`*.log` is gitignored). One run; pytest does not depend on it, but AC-12 does.

### S-6: dependency floor

`method="json_schema"` and GA `output_config.format` were verified on `langchain-anthropic==1.5.1` (workstation) and the FR-761 constraints artifact pins `1.5.2` (`constraints/dev-py312.txt:72`). `pyproject.toml` declares `langchain-anthropic>=0.3.0`, which predates the `json_schema` method. Raise the floor to `>=1.5.1` — the earliest **verified** version — unless enforcement verifies an earlier one with a committed note.

### S-7: traceability

Extend `capabilities/CAP-164-structured-output-fallback.yaml` (owner of executor/race structured-output provider rejection) with one new requirement, **REQ-YG-664** "Anthropic constrained structured output with typed single fallback", `fr: FR-464, FR-998`, modules += `yamlgraph/utils/structured_output.py`, `yamlgraph/utils/llm_providers.py`, `yamlgraph/tools/agent.py`. No new CAP. `REQ-YG-422` stays on the agent regression tests that exercise established agent behaviour. Regenerate `ARCHITECTURE.md` with `python scripts/aggregate_capabilities.py`.

`is_this_a_graph`: **No** — deterministic provider dispatch and exception policy; no LLM decision is made by the change itself.

## Implementation record (2026-09-05)

**Delivered (PR #599, stacked on #596):** `yamlgraph/utils/structured_output.py` (binder + sync/native-async invocation, the only production caller of the library binder); `yamlgraph/utils/llm_providers.py` gains the isinstance identity + four-condition unsupported-`output_config` predicate (lazy SDK imports), with its FR-708/710 request bounds extracted to `yamlgraph/utils/llm_bounds.py`; wiring in `executor_base.attempt_structured_invoke`, `race_node._invoke_candidate_async` (second attempt gets its own `uuid4()` run id via a `nonlocal` closure, so span closure keeps FR-720 F1 "last retained"), and both agent tiers via `bind_structured_output`; `tests/unit/test_fr998_structured_output.py` (47 tests, `REQ-YG-664`); `CAP-164` + REQ-YG-664, `ARCHITECTURE.md` regenerated; `pyproject.toml` floors; changelog fragment; FR-995 cross-reference (one `Related` bullet, one implementation-record sentence); live witness `docs/spikes/list-type-lie-2026-09-05/after/run-evidence.txt`; diary `docs/diary/2026-09-05-reflection-fr-998-the-edge-that-had-already-gone.md`.

**RED → GREEN:** `175f4151` (suite fails at collection: policy module absent) → `7fea7d5a`; review round 1: RED `a337b00e` (3 failing: agent typed second attempt ×2, predicates-in-`llm_providers`) → GREEN `807e3416`; review round 2: RED `7f71997c` (collection fails: `is_second_attempt_error` absent; plus the schema-keyword negative) → GREEN (next commit). Focused set 47/47; regression set (FR-464/678/679/449 executor, race, async factory) 116/116 with no assertion weakened.

**Live witness (AC-12):** `PROVIDER=anthropic ANTHROPIC_MODEL=claude-sonnet-4-5 yamlgraph graph run examples/demos/five-whys/graph.yaml --var problem="Deployment failed on Friday" --full` on git `7fea7d5a`; exit 0; `chain` parsed as `list` of 5 `str`; no second-attempt INFO line. Command, model line, SHA, values and trace URL in the committed evidence file.

**Deviations and decisions:**
- **AC-04 / S-2 file (review #599 P2):** the first GREEN put the predicates in a new `llm_provider_identity.py` because `llm_providers.py` sat at exactly 450 lines. The review refused that as source-of-truth drift. Resolution: the FR-708/710 request-bound helpers (`_request_timeout`, `_bounded`, `_vertex_transport`, `_masked_env`, the deadline floors) moved to `yamlgraph/utils/llm_bounds.py` (no SDK imports), and the predicates now live in `llm_providers.py` (412 lines) as frozen. `test_fr708_client_timeout.py` imports `_request_timeout` from `llm_bounds`; no assertion changed.
- **Agent default tier (review #599 P1):** the frozen S-3 table routed the agent's default tier through the *binder* only, so an Anthropic unsupported-`output_config` 400 raised out of the agent with no second attempt (the review's probe: `invocations=["json_schema"]`). The tier now calls `invoke_structured`; the explicit `function_calling` recovery tier is unchanged. A second-attempt error propagates through the agent's existing FR-456/809 tiers with no third call because those tiers key on OpenAI/DeepSeek error strings (`invalid_json_schema`, `additionalProperties`, `response_format`) that Anthropic's forced-tool-call path does not emit; both behaviours are tested (`TestAgentComposition`).
- **The gate's edge is gone.** Probing `claude-sonnet-4-20250514` and `claude-3-haiku-20240307` with `method="json_schema"` returned `404 not_found_error` — both models are retired from the API. Every Anthropic model the API serves today accepts constrained decoding, so the typed-400 second-attempt path has no live trigger and is witnessed only by constructed `BadRequestError`s (AC-05/AC-06). C-8 did not fire: no supported model rejected `json_schema`. The path is kept as designed (narrow predicate; next capability-less model family); see the diary's Seed.
- **Predicate condition (4)** is implemented as: the structured body message names `output_config`/`structured output`, contains unsupported wording (`not support`, `unsupported`, `not available`, `unavailable`), blames the **model** (the word `model` is present), and does not point into the schema (`.schema`, `json schema`, `keyword`, `invalid schema` absent — review #599 round 2 P2). An unsupported JSON-Schema *keyword* is a schema defect and propagates (tested). If a real model's capability message ever has a different shape, C-8 applies: stop and revise, do not widen.
- **Second-attempt provenance (review #599 round 2 P1):** the policy marks the exception raised by its forced-tool-call attempt (an attribute on the same object; type and identity unchanged) and exposes `is_second_attempt_error`. The executor's and race node's FR-464 branch and the agent's FR-456/809 tiers re-raise such an error before their string checks, so a second-attempt error whose text happens to contain `response_format`/`additionalProperties` cannot cause a third structured or plain call (tested on all three surfaces).
- **New direct dependency:** `anthropic>=0.96.0` (what `langchain-anthropic==1.5.1` requires) is declared in `pyproject.toml` with a rationale entry, because `direct_import_scan.py --strict` rejects an undeclared `import anthropic` even when lazy. Floor for `langchain-anthropic` raised to `>=1.5.1` per S-6; this workstation ran 1.7.0 / anthropic 1.3.0 (the constraints artifact pins 1.5.2 / 0.120.0).
- `req_coverage.py` reads decorators, not module `pytestmark`; markers are on each test class.
- Adding one import to `agent.py` and `executor_base.py` moved confessions CONF-304/350/351 by one line; `scripts/hedging_check.py` ALLOWLIST and `docs/confessions.md` anchors updated. Hedging finding set otherwise identical before/after (verified against a worktree of the RED commit).
- Enforced on a Windows host without `pre-commit`: gates run by hand — `ruff`, `lint-imports` (3 kept), `req_coverage --strict` (420/420), `validate_capabilities --strict`, `dependency_rationale --strict`, `direct_import_scan --strict`, `hedging_check --strict` (no new findings), `vulture`, `radon -n D`, `aggregate_capabilities`. Full unit suite: the 263 failures are shell/hook/path-separator/symlink tests that fail on this host before and after; the eight failing files near the changed code were inspected individually (path separators, symlink privileges). POSIX-hook verification is owed to CI on the PR.

## Review record (2026-09-05, `scripts/review.sh 599`)

Route: `scripts/review.sh 599 feature-requests/FR-998-…md` (Copilot backend, `gpt-5.6-sol`) on head `e444af57`. **Not approved**, two blocking findings, both accepted and enforced RED→GREEN in the same PR:

- **P1** — the agent's default structured re-invocation used the binder only, so the typed unsupported-`output_config` 400 never reached the invocation policy (reviewer's probe: one `json_schema` call, `BadRequestError` raised, no `function_calling` attempt). Fixed: `_try_structured_output` calls `invoke_structured`; two new tests assert the two-call sequence with a typed result and that a second-attempt error propagates with exactly two invocations.
- **P2** — predicates in a new `llm_provider_identity.py` while AC-04 (frozen at `llm_providers.py`) was ticked: source-of-truth drift. Fixed by extracting the FR-708/710 request bounds to `llm_bounds.py` and placing the predicates in `llm_providers.py`; a test asserts they are attributes of that module.
- Non-blocking: the unsupported-capability path stays synthetic (edge models 404). Reviewer's validations: focused suites 102 passed, `req_coverage --strict` 420/420, `lint-imports` 3 kept, all GitHub checks green.

**Round 2** on head `807e3416`: **Not approved**, two new blocking findings, both accepted and enforced RED (`7f71997c`) → GREEN (next commit):

- **P1** — the agent applied its FR-456/809 substring tiers to an error returned by the policy's *second* attempt, so a second-attempt 400 mentioning `additionalProperties` produced `json_schema → function_calling → function_calling → plain` (reviewer's probe: four calls). My round-1 test missed it because the constructed error carried the diagnostic only in `body`, not in `str()`. Fixed with second-attempt provenance (above); four new tests use an error whose `str()` contains both `additionalProperties` and `response_format`, on the agent, executor, and race surfaces.
- **P2** — the predicate accepted `output_config.format.schema: JSON Schema keyword oneOf is unsupported` (capability token + unsupported token co-occur). Fixed by requiring the message to blame the model and rejecting schema-pointer wording; the unsupported-keyword shape is a negative witness.
- Reviewer's validations: 117 + 116 focused tests passed, ruff, `req_coverage --strict` 420/420, `lint-imports` 3 kept, capability/dependency/direct-import validators passed, `git diff --check` clean.

**Round 3** on head `090a384f`: **Merge-approved** — no blocking findings; one non-blocking note (PR body said five commits, GitHub has eight) fixed in the description. CI green on the same head (3.11, 3.13, core-test, windows-encoding, security, convention gates). Review output is advisory until the human merge decision.

**Outsider view** (`scripts/outsider.sh 599`, FR-995): run 1 on the original description derived **NO** (6 unglossed terms: FR-998, PR #596, the FR-464/678/679/449 suites, five-whys, agent finalisation tiers, race node; 5 needs: test commands, dependency-floor compatibility, full CI status, cost/latency, stacking order). The description was rewritten to gloss every term and answer every need; run 2 derived **YES** (0 unclear, 4 remaining needs that are reviewer actions, not description gaps). Both rows in `docs/census/outsider-ledger.jsonl`; the launcher's `python3` fallback on this host is the Windows Store stub, so run 1's ledger row was appended by hand with the same tool functions after validating the report.

## Deferred — Alternative B: repair at the schema boundary (not in this FR)

`build_pydantic_model` could attach a `model_validator(mode="before")` that turns a `str` into a `list` for list-typed fields when `json.loads` yields `list[str]` (FR-873's exact rule, never guessing at bullet text). It is provider-agnostic and offline-testable. **It is not done here** because (1) the witnessed encoding today is bullet text, which the rule correctly refuses, so B alone would not have saved the incident; (2) after A the lie cannot be told on supported Anthropic models, and B's remaining territory is *other providers' tool-argument lies*, of which this repo has no witnessed incident. **Trigger for revisiting:** the first `list_type` error from a non-Anthropic provider, or from an Anthropic model on the S-1 fallback path, recorded with its raw payload. Until that row exists, B is refused, not queued.

## Acceptance Criteria (revised per judgement)

- [x] AC-01: The Research field cites only committed evidence, states `is_this_a_graph: No` with rationale, and names `docs/spikes/list-type-lie-2026-09-05/probe-output.txt` as the authoritative reproduction.
- [x] AC-02: The FR records the earliest verified `langchain-anthropic` version for the `json_schema`/`output_config.format` contract (1.5.1) and `pyproject.toml` declares at least that floor.
- [x] AC-03: `yamlgraph/utils/structured_output.py` owns the only production call expression `.with_structured_output(`; the binder forwards an explicit `method` unchanged, selects `json_schema` only for Anthropic when no override is given, and omits `method` for non-Anthropic models.
- [x] AC-04: Provider identity and unsupported-feature classification live in `yamlgraph/utils/llm_providers.py`; executor, race, and agent modules contain no Anthropic SDK/provider-class import and no class-name equality check.
- [x] AC-05: A typed Anthropic `BadRequestError` (HTTP 400, structured body naming unsupported `output_config`) causes exactly one `function_calling` invocation and exactly one INFO log naming the model and FR-998, in both the sync and the native-async helper.
- [x] AC-06: Pydantic `ValidationError`, auth/permission, rate-limit, timeout/network, server, unrelated Anthropic 400, binding/programming, and fallback-invocation errors each propagate unchanged with no extra invocation.
- [x] AC-07: The recorded bullet-string payload for `unclear: list[str]` fails on the default-method path and yields a real `list[str]` on the Anthropic `json_schema` path.
- [x] AC-08: `attempt_structured_invoke`, the race candidate path, and both agent finalisation paths use the shared policy; a direct test proves the agent's explicit `function_calling` recovery cannot be upgraded to `json_schema`.
- [x] AC-09: FR-464 executor/race extraction tests, FR-678 agent boundary tests, FR-679 shared-attempt tests, and agent invalid-schema/tool-choice tests pass with no assertion weakened.
- [x] AC-10: Native-async race tests prove constrained and fallback invocations both receive tracing config, use distinct run ids, and preserve cancellation behaviour.
- [x] AC-11: `CAP-164` carries REQ-YG-664 covering constrained Anthropic output and typed fallback across executor, race, and agent; `ARCHITECTURE.md` regenerated; every new test carries the marker; `python scripts/req_coverage.py --strict` and `lint-imports` pass.
- [x] AC-12: The S-5 command is run once on `claude-sonnet-4-5` and `docs/spikes/list-type-lie-2026-09-05/after/run-evidence.txt` records command, model, git SHA, and the parsed `chain` list values.
- [x] AC-13: RED commit precedes GREEN commit; the focused test set and the existing structured-output regression tests pass; changelog fragment `changelog/unreleased/fr-998-anthropic-constrained-structured-output.md` with `type: fix`, `scope: llm`, `req: REQ-YG-664`.
- [x] AC-14: FR-995 receives exactly one new `## Related` bullet ("FR-998 — why the API-transport successor can declare `unclear`/`needs` as `list[str]`") and one sentence appended to its *Implementation record* pointing to FR-998; the FR-998 implementation record lists any deviations; diary `docs/diary/2026-09-05-reflection-fr-998-*.md` contains `**Seed:**`.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A | `method="json_schema"` for Anthropic + typed fallback | **Chosen.** Probe: 3/3 fail under default, 2/2 pass constrained. Removes the class at the provider boundary. |
| B | `model_validator(mode="before")` repair in `build_pydantic_model` | **Deferred with trigger** (section above). Would not have caught today's bullet encoding; territory after A is unwitnessed. |
| C | A + B | Not now — B's half is unwitnessed; add on B's trigger. |
| D | `strict=True` on the forced tool call (`bind_tools(strict=True)`) instead of `output_config` | Rejected: `with_structured_output` ignores `strict` in kwargs (L2066 "Additional keyword arguments are ignored"); would need our own `bind_tools` + parser assembly, duplicating the library. Same model gate as A. |
| E | Widen FR-464's fallback to catch `ValidationError` and re-ask with a schema hint | Rejected: re-asks the same model that just lied, unconstrained; and the JSON-extraction path validates with the same Pydantic model → same `list_type`. Fixes the symptom's neighbour. |
| F | Prompt wording ("return a JSON array, not a string") | Rejected: two-strike rule — FR-873 and spike 2 already reworded; the abstraction level belongs in code. |
| G | Consumer-side repair (as FR-873 and spike 2 did) | Rejected: third occurrence; `partial_remediation`. |

## Related

- [FR-873](FR-873-vision-provider-type-lie.md) — consumer-side cure, same defect.
- [FR-464](FR-464-deepseek-structured-output-fallback.md), [FR-678](FR-678-narrow-agent-structured-output-catch.md), [FR-679](FR-679-consolidate-retry-fallback-post-676.md) — the call path this FR edits.
- [FR-995](FR-995-outsider-reader.md) — first consumer's successor.
- [docs/2026-09-05-research-plan-cap-journey-census.md §13](../docs/2026-09-05-research-plan-cap-journey-census.md) — where the incident was recorded.
- [docs/spikes/list-type-lie-2026-09-05/](../docs/spikes/list-type-lie-2026-09-05/) — probe + log.
