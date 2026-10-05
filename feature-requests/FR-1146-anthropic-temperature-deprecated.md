# Feature Request: FR-1146 Omit Temperature for Anthropic Models That Reject It

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Requested:** 2026-10-05
**First consumer / first event:** the operator running
`examples/demos/hello/graph.yaml` with `ANTHROPIC_MODEL=claude-sonnet-5-5`
— today it dies on the first `greet` call with a 400 (request
`req_011CfiWMf3TBZWUVmTgU62RV`, 2026-10-05).
**Research:** in-body [Alternatives Considered](#alternatives-considered)
table, each row backed by a probe executed 2026-10-05 (FR-889 style).
**Prior art:** [FR-455-reasoning-model-temperature-guard.md](FR-455-reasoning-model-temperature-guard.md)
— same defect class for OpenAI `o1/o3/o4`; this FR extends that guard to
Anthropic and does not change the OpenAI branch;
[FR-451-agent-temperature-zero-bug.md](FR-451-agent-temperature-zero-bug.md)
— temperature *resolution* chain, not provider acceptance; dismissed;
[FR-071-thinking-budget-graph-level.md](FR-071-thinking-budget-graph-level.md)
— forces `temperature=1` under extended thinking; this FR leaves that
override intact and only adds omission;
[FR-1144-race-node-thinking-budget.md](FR-1144-race-node-thinking-budget.md)
— thinking budget plumbing for race nodes; dismissed (see Out of scope).

## Summary

Anthropic's current model generation (`claude-opus-4-7` and later) rejects
any `temperature` other than the default, and rejects `top_p`/`top_k`
outright. `create_llm()` always sends `temperature` (defaulting `None` to
`0.7`), so every YAMLGraph LLM node fails on these models before producing
a token.

## Value Statement

Graph authors can switch `ANTHROPIC_MODEL` to any current Claude model
without editing graphs, matching what FR-455 already gives OpenAI
reasoning-model users.

## Problem

Witnessed 2026-10-05:

```
yamlgraph graph run examples/demos/hello/graph.yaml  (ANTHROPIC_MODEL=claude-sonnet-5-5)
Creating LLM: anthropic/claude-sonnet-5-5 (temp=0.7)
POST https://api.anthropic.com/v1/messages "HTTP/1.1 400 Bad Request"
invalid_request_error: `temperature` is deprecated for this model.
```

Mechanism (read from code at `f93f8afa`):

- `yamlgraph/utils/llm_factory.py:165-167` replaces `temperature=None`
  with `0.7` ("some providers reject None").
- `yamlgraph/utils/llm_providers.py:41-43` passes it unconditionally to
  `ChatAnthropic(model=..., temperature=...)`.
- `llm_factory_async.create_llm_async` delegates to `create_llm`, so both
  paths are affected; no other module calls the Anthropic API directly
  (grep `messages.batches|MessageBatch` in `yamlgraph/`: no hits).

### Probe 1 — acceptance boundary per sampling parameter

Direct `anthropic==0.120.0` SDK, `max_tokens=8`:

| Request extra | `claude-sonnet-5-5` | `claude-haiku-4-5` |
|---|---|---|
| none | OK | OK |
| `temperature=1` | OK | OK |
| `temperature=0.7` | 400 `temperature` is deprecated | OK |
| `temperature=0` | 400 `temperature` is deprecated | OK |
| `top_p=0.9` | 400 `top_p` is deprecated | OK |
| `top_k=5` | 400 `top_k` is deprecated | OK |

So "omit" and "send the default 1" both work; any non-default value fails.

### Probe 2 — which models (all 13 returned by `models.list`)

`temperature=0.5` against every listed model:

| Rejects | Accepts |
|---|---|
| `claude-sonnet-5-5`, `claude-opus-5-5`, `claude-fable-5-1`, `claude-opus-5`, `claude-sonnet-5`, `claude-fable-5`, `claude-opus-4-8`, `claude-opus-4-7` | `claude-sonnet-4-6`, `claude-opus-4-6`, `claude-opus-4-5-20251101`, `claude-haiku-4-5-20251001`, `claude-sonnet-4-5-20250929` |

### Probe 3 — is there a machine-readable discriminator?

The `models.list` metadata has no sampling-parameter field. However
`capabilities.thinking.types.enabled.supported` is `false` for exactly
the 8 rejecting models and `true` for all 5 accepting ones (13/13
agreement). This is a correlation, not a documented contract.

### Probe 4 — does omission reach the wire?

`ChatAnthropic(model="claude-sonnet-5-5", temperature=None)` →
`"temperature" in llm._get_request_payload("hi")` is `False`, and
`invoke` returns normally. `langchain-anthropic==1.5.2` already omits
`None`; the factory's `None → 0.7` substitution is what defeats it.

## Ideal Result

Any Claude model id placed in `ANTHROPIC_MODEL` (or a node's `model:`)
runs every LLM node unchanged. Older models keep honouring the graph's
`temperature`; newer models silently use their fixed sampling, and the
operator is told once, in the log, that the configured value was not
sent.

## Planned Operations

```yaml
probes:
  - "re-run Probe 2 at enforce time — a new model id absent from the allowlist decides whether the prefix list is still complete"
  - "pytest tests/unit/test_llm_factory.py before edit — existing FR-455 guard tests are the pattern and the regression floor"
  - "grep tests for assertions on ChatAnthropic temperature kwargs — any test pinning temperature=0.7 for a 5.x id must be updated, not skipped"
branches:
  - "a currently-listed model contradicts the prefix rule → widen/narrow the prefix tuple; never add a runtime models.list call"
  - "ChatAnthropic stops omitting None in a pinned version → pass no temperature kwarg instead of None"
delegations:
  - "judge.sh: 1 run"
  - "review.sh: 1 run after PR"
waits:
  - "judge"
  - "CI"
commands:
  - scripts/judge.sh feature-requests/FR-1146-anthropic-temperature-deprecated.md
  - pytest tests/unit/test_llm_factory.py -q --no-cov
  - yamlgraph graph run examples/demos/hello/graph.yaml --var name=World --var style=casual
  - scripts/review.sh
```

## Proposed Solution

Mirror the FR-455 guard in `create_llm()`, keyed on an **allowlist of
model prefixes that still accept sampling parameters**, so an unknown
(newer) Anthropic id defaults to omission:

```python
# Anthropic models that still accept temperature (FR-1146); newer ids reject it
ANTHROPIC_SAMPLING_MODEL_PREFIXES = (
    "claude-haiku-4-5",   # probed
    "claude-sonnet-4-5",  # probed
    "claude-sonnet-4-6",  # probed
    "claude-opus-4-5",    # probed
    "claude-opus-4-6",    # probed
    "claude-3",           # not listed by models.list; probe or drop at enforce
    "claude-sonnet-4-0", "claude-sonnet-4-2025", "claude-opus-4-0",
    "claude-opus-4-1", "claude-opus-4-2025",  # retired 4.0/4.1 ids; same
)

if (
    selected_provider == "anthropic"
    and not selected_model.startswith(ANTHROPIC_SAMPLING_MODEL_PREFIXES)
    and temperature is not None
    and not temperature_overridden
):
    logger.info(f"Omitting temperature for model without sampling control: {selected_model}")
    temperature = None
```

(Prefixes are exact per model line on purpose: a broad `claude-opus-4-`
would also match the rejecting `claude-opus-4-7`/`4-8`. The judge rules on
whether unlisted legacy ids stay in the tuple.)

Constraints:

1. The `None → 0.7` default stays for every other provider and for
   allowlisted Anthropic models.
2. The FR-071 thinking override (`temperature=1`) is untouched; 1 is
   accepted by all probed models.
3. `_create_anthropic_llm`'s signature becomes `temperature: float | None`;
   `ChatAnthropic` already omits `None` (Probe 4).
4. The cache key uses the post-guard temperature, so `0.0` and `0.7` on a
   5.x model share one client (correct: same wire request).

## Acceptance Criteria

- [ ] `create_llm(provider="anthropic", model="claude-sonnet-5-5", temperature=0.7)` builds a client whose request payload has no `temperature` key (unit test via `_get_request_payload`, no network).
- [ ] Same for `temperature=0` and for a hypothetical future id `claude-sonnet-6`.
- [ ] `create_llm(provider="anthropic", model="claude-haiku-4-5", temperature=0.3)` still sends `temperature=0.3`.
- [ ] An info log names the model when temperature is omitted.
- [ ] FR-455 OpenAI behaviour and its tests unchanged.
- [ ] Live witness: `ANTHROPIC_MODEL=claude-sonnet-5-5 yamlgraph graph run examples/demos/hello/graph.yaml --var name=World --var style="holy see of code"` exits 0 (log attached to PR).
- [ ] Tests carry `@pytest.mark.req(...)` for the existing LLM-factory requirement.
- [ ] Changelog fragment (`type: fix`).

## Alternatives Considered

**is_this_a_graph:** no existing YAMLGraph graph fits — this is a
deterministic constructor rule in the provider boundary, not per-item LLM
evaluation or fan-out; no graph is used.

| # | Alternative | Probe / evidence | Disposition |
|---|---|---|---|
| A | Denylist of rejecting prefixes (literal FR-455 shape: `claude-opus-4-7`, `claude-opus-4-8`, `claude-*-5*`) | Probe 2: 8 rejecting ids across 3 lines and 2 majors in ~one year | Rejected — every new release reproduces this incident until someone edits the tuple; the failure direction is a hard 400 |
| B | **Allowlist of accepting prefixes** (chosen) | Probe 2: accepting set is closed (older generations, no new releases expected) | Chosen — unknown ids fail safe (omit), the cost of a wrong guess is "temperature ignored, logged", not a crash |
| C | Query `models.list` at construction and key on `thinking.enabled.supported` | Probe 3: 13/13 correlation, but no documented link to sampling | Rejected — adds a network call to client construction and the cache key; trusting an undocumented correlation is `plausible_wrong_answer` |
| D | Catch the 400 and retry without temperature | Error text `` `temperature` is deprecated for this model`` is stable in Probe 1 | Rejected — reactive patch at the symptom (`downstream_fix`), doubles first-call latency, and must also cover streaming and structured-output paths |
| E | Remove `temperature` from the hello demo / graphs | Factory substitutes `0.7` when `None` (`llm_factory.py:165-167`), so graphs with no temperature still fail | Rejected — does not fix the defect; a graph-level fix also could not serve both model generations |
| F | Always send `temperature=1` for Anthropic | Probe 1: accepted by both generations | Rejected — silently discards a deliberate `temperature: 0` on older models that honour it |

## Out of scope (recorded follow-ups)

- **Extended thinking on new models.** A side probe returned
  `400 "thinking.type.enabled" is not supported for this model. Use
  "thinking.type.adaptive" and "output_config.effort"` for
  `claude-sonnet-5-5` with `thinking_budget=1024`. `thinking_budget`
  (FR-071) is therefore also broken on the 8 models above. It needs its
  own FR (new config surface: adaptive + effort); this FR only fixes
  sampling.
- **`top_p` / `top_k`.** YAMLGraph does not expose them
  (`grep -rn "top_p\|top_k" yamlgraph`: no hits); nothing to guard.
- **Linter warning** for explicit `temperature` on non-sampling models —
  only if the judge asks; the runtime log covers the first consumer.

## Related

- `yamlgraph/utils/llm_factory.py` — guard location (next to FR-455)
- `yamlgraph/utils/llm_providers.py` — `_create_anthropic_llm`
- `tests/unit/test_llm_factory.py` — FR-455 tests to mirror
- `logs/hello-sonnet55.log` (main checkout) — failing run
