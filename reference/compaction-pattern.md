# Compaction Pattern

**FR-616** | Pattern for managing unbounded state growth in long-running graphs.

## Problem

State in long-running graphs (multi-turn loops, iterative refinement, agent
sessions) grows monotonically. Every accumulated token costs attention budget and
API fees on every subsequent LLM call. Eventually, quality degrades as context
fills and the model's effective attention is diluted.

## Pattern: Guard → LLM → Conditional Loop

Compaction uses three existing YAMLGraph primitives:

1. **Python tool** — estimates token count of accumulated state
2. **Guard** — conditionally skips the LLM call when below threshold
3. **LLM node** — summarizes history into a compact representation

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ generate     │────▶│ count_tokens │────▶│ compact      │──┐
│ (appends)    │     │ (python)     │     │ (guard+llm)  │  │
└──────────────┘     └──────────────┘     └──────────────┘  │
       ▲                                                     │
       └─────────────────────────────────────────────────────┘
                    (loop back if under iteration limit)
```

When the guard's `on_fail: skip` triggers (tokens below threshold), the compact
node is a no-op — no LLM call, no cost.

## Minimal Implementation

### Graph YAML

```yaml
nodes:
  count_tokens:
    type: python
    tool: estimate_tokens
    variables:
      history: "{state.history}"

  compact:
    type: llm
    prompt: compact_history
    variables:
      history: "{state.history}"
    state_key: history
    skip_if_exists: false
    guards:
      pre:
        - check: "state.token_estimate > 400"
          on_fail: skip
          message: "Below token threshold, no compaction needed"
```

### Token Estimation (Python Tool)

```python
def estimate_tokens(state: dict) -> dict:
    history = state.get("history", [])
    total_chars = sum(len(str(item)) for item in history)
    # char/3.5 slightly overestimates (fires early, not late)
    return {"token_estimate": int(total_chars / 3.5)}
```

**Safety margin**: Use char/3.5 (not char/4) to overestimate. Firing compaction
early is safe; firing late risks blowing the context window.

### Compaction Prompt

A recall-first prompt that preserves named entities, open threads, and key events:

```yaml
system: |
  You are a precise summarizer. Preserve ALL important information:
  - Key events and their sequence
  - Named entities (characters, places, objects)
  - Open threads / unresolved points

user: |
  Compress the following history into a concise summary.
  {% for item in history %}
  {{ item }}
  {% endfor %}
```

## Keep-Tail Semantics

For conversation histories where recent messages should remain verbatim:

```yaml
  compact:
    type: llm
    prompt: compact_history
    variables:
      # Only compact older items; keep last 3 verbatim
      history: "{state.history[:-3]}"
    state_key: history
```

Then in the passthrough or post-processing, concatenate:
`[summary] + history[-3:]`

## Hysteresis

Without protection, compaction in a tight loop re-summarizes its own previous
summary (summary of summary of summary — compounding information loss).

**Solution**: Track `last_compaction_iteration` in state and add a guard:

```yaml
guards:
  pre:
    - check: "state.token_estimate > 400"
      on_fail: skip
    - check: "state._loop_counts.generate_turn - state.last_compaction > 2"
      on_fail: skip
      message: "Cooldown: too soon since last compaction"
```

This ensures at least 2 new iterations of content accumulate before the next
compaction fires.

## Token Estimation Approaches

| Approach | Accuracy | Speed | Dependencies |
|----------|----------|-------|--------------|
| `char / 3.5` | ~85% (overestimates) | Instant | None |
| `char / 4` | ~90% | Instant | None |
| `tiktoken` | ~99% (OpenAI) | Fast | `tiktoken` package |
| Provider API | Exact | Network call | Provider SDK |

For v1, `char / 3.5` is recommended — it's zero-dependency and the safety
margin means compaction fires slightly early rather than too late.

## When to Graduate to a Node Type

If you find yourself wiring this pattern in 3+ graphs with identical structure,
consider proposing a first-class `compaction` node type. Signals:

- The guard + python + llm + conditional edge wiring is error-prone
- Multiple graphs copy-paste the same token counting tool
- You need built-in hysteresis that's tedious to express in guards

## Working Example

See `examples/demos/compaction/` for a complete working demo showing a
storytelling loop that stays bounded over 6+ iterations via guard-gated
compaction.
