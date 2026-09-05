# Feature Request: Structured output must be constrained, not requested — Anthropic `list[str]` fields arrive as strings

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-09-05
**First consumer / first event:** any `llm` node with an inline `schema:` that declares a `list[...]` field, running on an Anthropic model — at the moment the model answers. Witnessed first by the outsider-reader spike 2 (`docs/spikes/outsider-llm-2026-09-05/`, run 1, 2026-09-05 08:02Z), whose `unclear: list[str]` field killed the run with `on_error: fail`. Second consumer: `scripts/outsider.sh`'s successor (FR-995 → API transport), which needs list fields to be lists.
**Research:** in-body — the *Investigation* section below is the committed record: causal chain to file and line, a live reproduction with the probe and log committed at [docs/spikes/list-type-lie-2026-09-05/](../docs/spikes/list-type-lie-2026-09-05/) (`probe.py`, `probe.log`), and a dispositioned alternatives table. No `scripts/research.sh` run: the problem is a reproduced defect with one verified fix, not an open design space.
**Prior art:** [FR-873](FR-873-vision-provider-type-lie.md) (Enforced 2026-08-24) — the *identical* defect (`paragraphs` as a JSON-encoded string, `list_type`) in the deviant-daily consumer, fixed **at the consumer** with a capture schema + `json.loads` repair; the framework boundary was left as it was. This FR is the third witnessed occurrence of the class (FR-059 diary → FR-873 → spike 2 + 3 probe runs) and moves the cure to the framework. FR-873's judge rule — *repair only when `json.loads` yields `list[str]`; never guess* — is inherited and is why Alternative B is not chosen: today's reproduction returned a **markdown bullet list**, not JSON, so the FR-873 repair would not have fired either. [FR-059](059-agent-normalize-content-to-string.md) / [FR-264](FR-264-race-node-parse-json-content-normalization.md) / [CAP-117](../capabilities/CAP-117-race-node-parse-json-content-normalization.yaml) — normalise `content: str | list` at the message boundary (`yamlgraph/utils/content.py`); a different axis (message content, not tool-argument field types); not touched. [FR-464](FR-464-deepseek-structured-output-fallback.md) — the `"response_format"` string-match fallback in `attempt_structured_invoke`; this FR shows the match cannot fire for the Anthropic failure and replaces the condition for the new path only. [FR-678](FR-678-narrow-agent-structured-output-catch.md) — no broad swallow; the fallback here catches one typed provider error. No REJECTED FR in this territory (`grep -l "json_schema\|strict tool\|list_type" feature-requests/*.md` → FR-873, FR-631 [interpolation, unrelated], FR-956/706/270/986/683/764 [unrelated matches on "strict"]).

## Summary

`yamlgraph` asks the provider for structured output with `llm.with_structured_output(output_model)` and no `method` ([executor_base.py L400](../yamlgraph/executor_base.py#L400), [race_node.py L137](../yamlgraph/node_factory/race_node.py#L137), [tools/agent.py L93, L107](../yamlgraph/tools/agent.py#L93)). For `ChatAnthropic` (langchain-anthropic 1.5.1) that default is `method="function_calling"`: a forced, non-strict tool call. The schema is a *request*; `claude-sonnet-4-5` answers `list[str]` fields with a single string — sometimes a JSON array in quotes, sometimes a markdown bullet list — and Pydantic rejects it (`list_type`). The FR-464 fallback never fires (it looks for `"response_format"` in the error text; a `ValidationError` propagates), so the node fails and, with `on_error: fail`, the run dies.

The fix is to use the provider's **constrained decoding** — `method="json_schema"` (Anthropic `output_config.format`, GA in the installed SDK) — for Anthropic models, so the shape is guaranteed by the decoder instead of requested from the model. Verified live: 2/2 runs correctly typed against the same prompt that failed 3/3 under the default.

## Value Statement

Anyone who writes `type: list[str]` in a prompt schema gets a list, on every run, on every supported Anthropic model — instead of a run that dies on a container-type error while the content was correct.

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

**Live reproduction** — `docs/spikes/list-type-lie-2026-09-05/probe.py`, exact spike prompt and input (`inputs/positive.md`), schema restored to run-1 shape (`unclear`, `needs` as `list[str]`), `claude-sonnet-4-5`, T=0, `include_raw=True` so the raw tool arguments are visible before parsing. Log: `probe.log`.

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

A prompt schema that says `list[str]` produces a `list[str]` on every Anthropic model this repo runs, because the decoder is constrained to the schema; on a model that cannot be constrained the framework falls back to today's forced tool call and says so in the log; and the codebase has one place where "how do we ask this provider for a shape" is decided, not four copies of a default.

## Proposed Solution — Alternative A: constrained decoding for Anthropic

### S-1: one structured-output entry point

Add `structured_output(llm, output_model)` in `yamlgraph/executor_base.py` (next to `attempt_structured_invoke`) that returns the bound runnable:

```python
def structured_output(llm, output_model):
    """Choose the provider's strongest shape guarantee (FR-998)."""
    if _is_anthropic(llm):
        return llm.with_structured_output(output_model, method="json_schema")
    return llm.with_structured_output(output_model)
```

`_is_anthropic` tests the class (`langchain_anthropic.ChatAnthropic` via `type(llm).__name__ == "ChatAnthropic"` or an `isinstance` behind an optional import — Judge to fix which; the test double must be able to trigger it without the package).

### S-2: replace the four call sites

`attempt_structured_invoke` (sync + async share it), `race_node.py` L137, `tools/agent.py` L93 and L107 call `structured_output(...)` instead of `llm.with_structured_output(...)`. No behaviour change for OpenAI/Mistral/other providers.

### S-3: typed fallback for unsupported Anthropic models

When the constrained call raises the provider's request error for `output_config` (Anthropic `BadRequestError`, HTTP 400, message naming `output_config`/`structured outputs`), log at INFO `"Anthropic constrained output unsupported on <model>; falling back to forced tool call (FR-998)"` and retry once with `method="function_calling"`. Anything else propagates unchanged (FR-678). The existing FR-464 `"response_format"` branch is untouched — it serves a different provider.

### S-4: condemning tests (offline, no API)

- **RED-1** (`tests/unit/test_fr998_structured_output_method.py`): a fake `ChatAnthropic`-named LLM records the `method` kwarg passed to `with_structured_output`; through `attempt_structured_invoke` it must receive `"json_schema"`. Fails today (`None`/default).
- **RED-2**: the same fake, non-Anthropic class name → `method` not passed. (Guards S-1 from over-reaching.)
- **RED-3**: fake Anthropic whose `json_schema` invoke raises the typed 400 → second call uses `"function_calling"`, one INFO line, result returned. A fake raising any other exception → propagates (FR-678).
- **RED-4** (the incident): a fake whose default-method invoke returns the recorded bullet-string payload for `unclear` raises `list_type` today through `attempt_structured_invoke`; after the fix the fake's `json_schema` path returns the typed list and the node result is `list[str]`. This is the witness that the *incident* is covered, not just the kwarg.
- Race node and agent tool: one test each that the shared entry point is what they call (import-level or spy).

### S-5: live witness (one run, recorded, not a gate)

Re-run `docs/spikes/list-type-lie-2026-09-05/probe.py`'s `json_schema` arm through a real `llm` node — the spike 2 graph with `unclear`/`needs` restored to `list[str]` — and commit the output under `docs/spikes/list-type-lie-2026-09-05/after/`. One run; pytest does not depend on it.

## Deferred — Alternative B: repair at the schema boundary (not in this FR)

`build_pydantic_model` could attach a `model_validator(mode="before")` that turns a `str` into a `list` for list-typed fields when `json.loads` yields `list[str]` (FR-873's exact rule, never guessing at bullet text). It is provider-agnostic and offline-testable. **It is not done here** because (1) the witnessed encoding today is bullet text, which the rule correctly refuses, so B alone would not have saved the incident; (2) after A the lie cannot be told on supported Anthropic models, and B's remaining territory is *other providers' tool-argument lies*, of which this repo has no witnessed incident. **Trigger for revisiting:** the first `list_type` error from a non-Anthropic provider, or from an Anthropic model on the S-3 fallback path, recorded with its raw payload. Until that row exists, B is refused, not queued.

## Acceptance Criteria

- [ ] AC-01: `structured_output()` exists in `executor_base.py` and is the only place `with_structured_output` is called in `yamlgraph/` (`grep -rn with_structured_output yamlgraph/` returns exactly the one definition site).
- [ ] AC-02: For an Anthropic LLM, `method="json_schema"` is passed (RED-1); for any other provider no `method` is passed (RED-2).
- [ ] AC-03: The typed Anthropic 400 for `output_config` falls back once to `function_calling` with one INFO log line; any other exception propagates unchanged (RED-3).
- [ ] AC-04: The incident payload (bullet-list string for a `list[str]` field) is reproduced by a failing test before the fix and yields `list[str]` after (RED-4).
- [ ] AC-05: Race node and agent tool route through the shared entry point (one test each).
- [ ] AC-06: One live run through a real `llm` node with `list[str]` fields on `claude-sonnet-4-5` committed under `docs/spikes/list-type-lie-2026-09-05/after/` (S-5); fields arrive as lists.
- [ ] AC-07: RED commit (`SKIP=pytest`) precedes GREEN commit; changelog fragment `changelog/unreleased/fr-998-*.md` (`type: fix`, `scope: llm`); CAP file with new REQ id; `python scripts/req_coverage.py --strict` green; `lint-imports` green.
- [ ] AC-08: FR-995's successor note (`feature-requests/FR-995-outsider-reader.md`, Fixtures/plan §13 pointer) references this FR as the reason the API transport can declare list fields as lists.
- [ ] AC-09: Diary entry `docs/diary/2026-09-05-reflection-fr-998-*.md` with a `**Seed:**`.

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
