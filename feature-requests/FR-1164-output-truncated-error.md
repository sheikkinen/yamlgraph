# Feature Request: FR-1164 Report replies cut off by the output-token limit, with the thinking share

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented (judged 2026-11-14: APPROVED WITH REVISIONS on the revised FR; R-1 folded)
**Requested:** 2026-11-14
**First consumer / first event:** the next map run where a model hits a
small per-item `max_tokens`, whether a model that thinks by default
(Claude Sonnet 5.5, Opus 5.5, Gemini 3.5 Flash) or not. Today the item
returns `""`, cut-off text, or a structured model with a fabricated
trailing element as a success. After this FR the item fails with
"stopped at the output-token limit (stop_reason=max_tokens) …".
**Research:** [FR-1164.research.md](FR-1164.research.md) (dispositioned
alternatives, provider evidence; brief:
[research-briefs/fr1164-truncated-reply-reported-empty-brief.md](research-briefs/fr1164-truncated-reply-reported-empty-brief.md))
**Evidence:** [evidence/FR-1164-truncation-probe.json](evidence/FR-1164-truncation-probe.json)
(`scripts/probe_fr1164_truncation.py`, live, operator-approved spend)
**Prior art:** FR-998 (structured-output policy; this FR adds a check
inside its `invoke_structured`/`ainvoke_structured`, no second policy
surface). FR-464 (JSON-extraction fallback; its re-invoke gets the same
check). FR-679 (sync and threaded async share `attempt_structured_invoke`;
the check lives there once). FR-1148 (its probe recorded
`stop=max_tokens` with thinking-only content; that FR turned thinking off,
this FR reports the case for models that cannot). FR-1152 (sums reasoning
tokens in the usage summary; this FR reads the same field per call).
FR-071/FR-230 (thinking budget). FR-465 (proposed: empty safety-blocked
replies; different stop reason, not covered here). FR-672 (REJECTED: the
shared-attempt extraction, rejected because the duplication did not exist
yet; FR-679 did it later on new evidence, `FR-679:26-29`). This FR adds a
check inside FR-679's attempt and adds no retry, so it does not reopen
FR-672. Retrieval hits FR-736, FR-931, FR-948, FR-959, FR-1060 share only
vocabulary and are dismissed.

## Summary

Read the provider's stop reason on the raw reply at the three places
yamlgraph first holds an LLM node's response, and raise a typed
`OutputTruncatedError` when it reports the output-token limit. The message
names the stop reason, the output token count, how many were thinking (or
"unknown"), and how much visible text came back. This also covers the
operator's third finding: thinking counts toward `max_tokens`, so a small
limit cuts the answer short. The reference docs state the shared budget.

This is deterministic boundary validation, not an LLM graph.

## Value Statement

Operators see "the limit was hit, and thinking used most of it" instead of
an empty answer, cut text or a padded structured model that looks like a
success.

## Problem

- `attempt_structured_invoke` (`yamlgraph/executor_base.py`) returns
  `normalize_content(response.content)` for plain calls and drops
  `response_metadata`. `normalize_content` keeps text blocks only, so a
  thinking-only reply becomes `""`.
- With `parse_json: true`, `extract_json` returns unparseable text
  unchanged (`yamlgraph/utils/json_extract.py`): a cut-off JSON body flows
  downstream as the answer.
- Structured calls go through `invoke_structured`
  (`yamlgraph/utils/structured_output.py`), which returns only the parsed
  model. The live probe shows what that hides: Haiku 4.5 at
  `max_tokens=16` under `json_schema` stopped with `stop_reason:
  max_tokens`, the library's partial-JSON parser closed the cut array, and
  `invoke_structured` returned `Countries(countries=['Afghanistan',
  'Albania', 'Algeria', 'Andorra', 'Angola', ''])` with no error. The
  stop reason lives only on the raw message, which the binder discards.
- The race node (`yamlgraph/node_factory/race_node.py`) has its own
  `ainvoke` and the same blind spot.
- No stop-reason check exists in the LLM path (the only one is in
  `copilot_runtime_opencode.py`).
- Witnessed: `examples/dungeon_master/chapter_close.yaml` records a
  gemini-3.5-flash call where "a 2000 cap was exhausted entirely by
  reasoning (~1921 tok observed in LangSmith), leaving "text": "" → empty
  ledger". FR-1148's probe recorded the Anthropic equivalent.
- Thinking is part of `max_tokens` on Anthropic and part of the output
  limit on OpenAI reasoning models. Models that think by default spend it
  without any `thinking_budget` in the graph. The reference docs describe
  `max_tokens` and `thinking_budget` separately and never say they share
  one budget.

## Ideal Result

A reply whose provider reports a stop on the output-token limit is never
returned as a finished answer by the executor attempt, the structured
policy helpers or the race candidate. The failure names the limit and, when
the provider reports it, the thinking share.

Bounded guarantee (R-2): recognized output-limit stop reasons are rejected
in `attempt_structured_invoke`, `invoke_structured`/`ainvoke_structured`
and `_invoke_candidate_async`, including their existing re-invocations
(FR-998 second attempt, FR-464 plain fallback). Out of scope and unchanged:
direct `bind_structured_output` consumers (agent finalisation), agent tool
loops, streaming/token delivery, and any direct provider call. Absent or
unrecognized stop metadata is not proof that a reply is complete; it only
means no new rejection.

## Planned Operations

```yaml
probes:
  - "live Haiku 4.5 (claude-haiku-4-5-20251001), max_tokens=16, plain + json_schema include_raw + today's invoke_structured (done: 3 requests, ~$0.002; evidence/FR-1164-truncation-probe.json)"
  - "offline read of langchain-anthropic 1.7.10 / langchain-openai 1.6.0 / langchain-google-genai 4.4.0 stop keys (done: research record table)"
  - "grep tests for with_structured_output mocks — counts the tests the raw-binding change touches (at enforcement, before RED)"
branches:
  - "more than 30 tests mock with_structured_output().invoke returning a model → add one shared test helper that wraps the return in {raw, parsed, parsing_error}; never a production path that accepts both shapes"
  - "a raw-enabled call returns an envelope without 'raw' → stop, return to plan (no shim)"
delegations:
  - "research.sh: 1 run (done; dispositioned in the research record)"
  - "judge.sh: re-judge (done 2026-11-14: APPROVED WITH REVISIONS, R-1 folded); not re-entered during enforcement"
waits: []
commands:
  # mandatory offline enforcement gate (AC-13)
  - pytest tests/unit/test_fr1164_output_truncated.py tests/unit/test_fr998_structured_output.py tests/unit/test_race_node.py -q --no-cov
  - pytest tests/unit/ -q --no-cov -m "not slow" -n 4
  - python scripts/req_coverage.py --strict
  - lint-imports
  - ruff check yamlgraph/ scripts/ tests/ && ruff format --check yamlgraph/ scripts/ tests/
  # optional paid probe: only with a fresh operator spend approval (AC-11); judge the JSON entries, not the exit code
  - python scripts/probe_fr1164_truncation.py
```

## Proposed Solution

New module `yamlgraph/utils/stop_reason.py`:

```python
TRUNCATED = frozenset({"max_tokens", "length", "MAX_TOKENS"})  # anthropic | openai | google

class OutputTruncatedError(RuntimeError):
    stop_reason: str
    output_tokens: int | None      # None when usage is unavailable
    reasoning_tokens: int | None   # None when the provider does not report it
    visible_chars: int             # len(normalize_content(message.content))
    preview: str                   # first <= 200 chars of that same text

def ensure_complete(message: BaseMessage) -> None:
    """Raise OutputTruncatedError when the raw reply stopped on the output limit."""
```

Classification (R-4), frozen against the research record's provider table:

- Stop value: the first nonempty of `response_metadata["stop_reason"]`,
  then `response_metadata["finish_reason"]`. A value in `TRUNCATED`
  raises; any other value, or neither key, passes unchanged.
- Usage: `usage_metadata["output_tokens"]` and
  `usage_metadata["output_token_details"]["reasoning"]`, each read
  independently. A missing `usage_metadata`, key or `None` stays `None` and
  renders as `unknown`; truncation raises regardless. Missing reasoning is
  never reported as 0 (the probe's Haiku reply had no
  `output_token_details`).
- Visible text: only `normalize_content(message.content)`. No raw message,
  thinking block or provider payload enters the message or the fields.

Message form:

`LLM reply stopped at the output-token limit (stop_reason=max_tokens): 2000 output tokens, 1921 of them thinking; 0 visible characters. Raise max_tokens; where the model supports a thinking budget, lowering it leaves more for the answer.`

With unknown usage: `… (stop_reason=max_tokens): unknown output tokens, unknown of them thinking; 38 visible characters. …`. The message never contains `response_format`, so the FR-464 fallback test (`"response_format" in str(err)`) cannot fire on it.

Call sites (the bounded guarantee above):

1. `bind_structured_output(llm, output_model, *, method=None,
   include_raw=False)`: new keyword-only `include_raw`, forwarded to the
   same single `.with_structured_output(...)` call only when `True`. Direct
   callers (agent finalisation) keep the parsed-only result.
2. `invoke_structured` / `ainvoke_structured`: both the primary and the
   earned `function_calling` second attempt bind with `include_raw=True`
   and pass the envelope to one private `_unwrap(out)`:
   `ensure_complete(out["raw"])` first; then `raise out["parsing_error"]`
   (the same object) if set; else `return out["parsed"]`. Provider errors
   (the typed 400) still raise from the call itself, so
   `_second_attempt_earned`, the second-attempt mark, `config` forwarding
   and the async `second_attempt_config` are unchanged. A truncation raised
   from the primary attempt is not a typed 400, so it earns no second
   attempt; one raised from the second attempt is marked like any other
   second-attempt error.
3. `attempt_structured_invoke`: the plain path and the FR-464 fallback
   re-invoke call `ensure_complete(response)` before `normalize_content`.
   A truncation from `invoke_structured` propagates (it contains no
   `response_format`), so it earns no FR-464 fallback.
4. `race_node._invoke_candidate_async`: the FR-464 re-invoke and the plain
   `ainvoke` call `ensure_complete(response)` before `normalize_content`;
   the structured path inherits it from `ainvoke_structured`. A truncated
   candidate raises like any failed candidate, so it cannot win.

`OutputTruncatedError` is not added to `RETRYABLE_EXCEPTIONS`
(`executor_base.py:70`): the same limit reproduces the same cut. Node
`on_error` policies are unchanged and apply as for any error.

Requirement (R-5): new `REQ-YG-729` under `CAP-164` (structured output,
which owns FR-998's REQ-YG-664 and the FR-464 REQs), `fr:` gains FR-1164,
modules `utils/stop_reason.py`, `utils/structured_output.py`,
`executor_base.py`, `node_factory/race_node.py`; ARCHITECTURE.md
regenerated by `scripts/aggregate_capabilities.py`. Tests carry
`@pytest.mark.req("REQ-YG-729")`.

Docs: `reference/graph-yaml.md`, next to `max_tokens` and
`thinking_budget`: on providers that count thinking as output (Anthropic
`max_tokens`; OpenAI reasoning models' output limit), thinking and answer
share one budget; models that think by default spend it without a
`thinking_budget` setting; executor, structured and race calls that stop
on the limit raise `OutputTruncatedError` (bounded as above, no universal
completeness claim); lowering a thinking budget helps only where the model
supports one.

## Acceptance Criteria

Adopted from the judgement's revised criteria; AC-01/02 are met by this
revision and the rest are enforcement criteria.

- [x] AC-01: the research record folds R-1..R-5: dispositioned alternatives
  A1-A5 with code/precedent lines, the corrected factory-wrapper claim, the
  failed data-process persona, the graph-fit answer, the FR-672/FR-679
  disposition; the brief is committed.
- [x] AC-02: provider evidence names package versions and stop keys/values
  (research record table) and the live `include_raw` envelope; the FR
  states the bounded guarantee and its exclusions.
- [x] AC-03: thinking-only, mixed thinking/text and partial-text messages,
  with each of `max_tokens`, `length`, `MAX_TOKENS`, raise
  `OutputTruncatedError` from `attempt_structured_invoke` (plain and
  `parse_json`-style text) before normalization or JSON extraction; with
  output 2000 / reasoning 1921 the message contains both numbers.
- [x] AC-04: missing `usage_metadata`, missing keys and `None` values still
  raise on truncation, keep the fields `None` and print `unknown`, never 0;
  `stop_reason` wins over `finish_reason` when both are present; an empty
  `stop_reason` falls through to `finish_reason`.
- [x] AC-05: no stop key, an unrecognized value, and `end_turn`/`stop`
  produce no error and return today's result.
- [x] AC-06: `invoke_structured` and `ainvoke_structured`, on the primary
  and on the earned second attempt, raise `OutputTruncatedError` for a
  truncated raw message even when `parsed` is a valid model (the probe's
  case); a complete call returns `parsed`; a complete call with
  `parsing_error` re-raises the identical object (`is`).
- [x] AC-07: `bind_structured_output` without `include_raw` passes no
  `include_raw` kwarg (agent finalisation unchanged); the one production
  `.with_structured_output(` call remains; `config` forwarding, the
  exactly-one second attempt, its mark and the async
  `second_attempt_config` run id stay as FR-998 tests pin them; a
  primary-attempt truncation earns no second attempt (one invoke).
- [x] AC-08: executor and race FR-464 plain re-invokes raise on a truncated
  reply, with no further call; a truncation from the structured attempt
  earns no FR-464 fallback (invoke counts asserted; race run ids distinct).
- [x] AC-09: a truncated race candidate raises; in a race with a complete
  candidate the complete one wins; existing race tests stay green;
  `is_retryable(OutputTruncatedError(...))` is `False`.
- [x] AC-10: the error's fields carry the stop reason, available usage, the
  visible-character count and a preview of at most 200 characters, both
  from `normalize_content`; a sentinel in a thinking block is absent from
  `str(err)` and from `err.preview`.
- [x] AC-11: live probe reproducible from `python
  scripts/probe_fr1164_truncation.py` (`ANTHROPIC_API_KEY`; operator spend
  approval 2026-11-14, at most 4 requests / $0.05); result
  `evidence/FR-1164-truncation-probe.json` records model
  `claude-haiku-4-5-20251001`, `max_tokens=16`, package versions, SHA
  `3fd52fec`, sanitized metadata, the include_raw envelope and today's
  structured result (3 of the 4 approved requests used). This file is
  baseline evidence of the provider contract and the defect, not of the
  fix. A post-GREEN re-run needs a fresh operator spend approval; if
  granted, `plain` and `structured_include_raw` stay direct-provider
  observations (not required to raise), and for a reply reporting
  truncation `structured_today` (YAMLGraph's policy) must record
  `OutputTruncatedError`, checked in the JSON, not by exit code. If not
  granted, the FR records that no paid re-run occurred and the unit
  witnesses built from the recorded envelope stand.
- [x] AC-12: `reference/graph-yaml.md` states the shared thinking/output
  budget for providers that count it, the qualified advice, and the
  bounded `OutputTruncatedError` behaviour without a universal claim.
- [x] AC-13: a behavioural RED commit precedes GREEN; the mandatory offline
  commands under Planned Operations pass (targeted tests, unit suite,
  `req_coverage --strict`, `lint-imports`, ruff check and format); the
  optional paid probe and the judge are not part of this gate; new tests
  carry `@pytest.mark.req("REQ-YG-729")`, registered in CAP-164 and the
  generated ARCHITECTURE.md.
- [x] AC-14: fix changelog fragment, Implementation Status with decisions
  and deviations, and a diary entry with `**Seed:**` are committed.

## Alternatives Considered

Dispositioned in [FR-1164.research.md](FR-1164.research.md#dispositioned-alternatives)
(the run's four rows were one idea; they are not counted as four):

- A1 invocation-boundary rejection at the three call sites: chosen.
- A2 a new provider-client response wrapper in `create_llm`: rejected. The
  factory returns plain LangChain clients and never sees a response (the
  run's "factory already wraps every invoke" claim is false); a wrapper
  would have to cover `with_structured_output`, `bind_tools` and streaming.
- A3 carrying stop reason and reasoning tokens downstream as schema fields
  (the failed data-process persona): rejected; a field nobody reads does
  not stop the probe's `Countries(..., '')` passing as finished.
- A4 warn without rejecting: rejected (Commandment 6).
- A5 validate `thinking_budget` against `max_tokens` at construction:
  rejected; the probe's truncation had no thinking at all, and
  default-thinking models have no budget to compare.

## Implementation Status

Implemented 2026-11-14 on branch `fix/fr1164-output-truncated-error`.

- RED `test(llm): FR-1164 RED ...`: 43 witnesses in
  `tests/unit/test_fr1164_output_truncated.py`, 37 failing on behaviour
  (DID NOT RAISE). `stop_reason.py` shipped the error class with a no-op
  `ensure_complete` so failures were behavioural, not import errors; the
  RED commit skipped vulture alongside pytest because the stub was not yet
  wired in.
- GREEN: `ensure_complete` as frozen; `bind_structured_output(...,
  include_raw=False)`; `_unwrap` on both attempts of both helpers (the
  second attempt's `_unwrap` is inside the marking `try`, so its
  truncation is marked like any second-attempt error); `ensure_complete`
  before `normalize_content` on the executor plain path, the executor
  FR-464 re-invoke, and both race `ainvoke` paths.
- Decision (branch rule): 31 existing tests mocked the structured
  runnable's bare return, so one shared helper
  `tests/unit/_structured_envelope.py` (`envelope(parsed)`) wraps mocks in
  `{raw, parsed, parsing_error}`. FR-998's fake LLM now mirrors LangChain:
  envelope only when bound with `include_raw=True`. Production accepts one
  shape only.
- Deviation: one witness (`None` reasoning detail) builds its message with
  `AIMessage.model_construct`, because `AIMessage` validation rejects
  `None` there; the classifier's `None` handling stays witnessed.
- Module-map budget 304 → 306 for `utils/stop_reason.py`.
- Gate: targeted tests 149 passed; unit suite shows no failure absent from
  `main` at `6239c99b` (the remaining Windows shell/hook failures are
  identical on `main`); `req_coverage --strict`, `lint-imports`, ruff check
  and format clean.
- AC-11: no paid post-GREEN re-run occurred; the unit witnesses built from
  the recorded envelope stand.

## Related

- [FR-1164.research.md](FR-1164.research.md)
- [FR-1148](FR-1148-anthropic-thinking-off.md), [FR-1152](FR-1152-thinking-tokens-in-token-usage.md)
