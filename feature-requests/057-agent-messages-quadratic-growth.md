# Feature Request: Agent Node Messages Quadratic Growth

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-02-20

## Summary

`type: agent` nodes return the full internal `messages` list, but the `add` reducer on `messages` (from `BASE_FIELDS`) appends it to existing state — causing quadratic growth when the agent node is invoked multiple times across interrupt boundaries.

## Problem

In a graph with an interrupt loop around an agent node:

```
agent → interrupt → router → (loop back to agent)
```

Each invocation of the agent node:
1. Reads `existing_messages = state.get("messages", [])` (already bloated)
2. Extends with new conversation: `existing_messages + [HumanMessage(...)]`
3. Runs tool loop, accumulating more messages
4. Returns `{"messages": messages}` — the **full** list including existing

The `Annotated[list, add]` reducer then appends the full returned list to what's already in state:

| Turn | Agent reads | Agent returns | State after `add` |
|------|-------------|---------------|--------------------|
| 1 | 0 msgs | 5 msgs | 5 |
| 2 | 5 msgs | 10 msgs | 15 |
| 3 | 15 msgs | 20 msgs | 35 |
| 4 | 35 msgs | 40 msgs | 75 |
| 5 | 75 msgs | 80 msgs | 155 |

Since the agent reads from the bloated state, the LLM context itself grows quadratically — containing duplicated earlier turns. This degrades response quality, wastes tokens, and can hit context window limits.

### Where it happens

- `yamlgraph/tools/agent.py` L234-238: reads `existing_messages` from state
- `yamlgraph/tools/agent.py` L283: returns full `messages` list
- `yamlgraph/models/state_builder.py` L71: `"messages": Annotated[list, add]`

### When it doesn't matter

Single-invocation agents (no loop) — the agent is called once, returns messages, done. No duplication. This is the current usage in all yamlgraph examples.

### When it breaks

Any graph where an agent node is called **more than once** in the same session — either via graph loops, or across interrupt boundaries (as in the questionnaire-api Terveystalo RAG flow).

## Proposed Solution

The agent node should return only **new** messages (everything after `existing_messages`), not the full conversation:

```python
# Current (agent.py L283):
result = {
    state_key: response.content,
    "messages": messages,  # Full list including existing
}

# Fixed:
new_messages = messages[len(existing_messages):]
result = {
    state_key: response.content,
    "messages": new_messages,  # Only new messages
}
```

The `add` reducer then correctly appends only the new messages to state, preserving linear growth.

Same fix needed at L343 (max iterations path).

### Alternative: Use `last_value` reducer

Change `messages` from `Annotated[list, add]` to `Annotated[list, last_value]`. But this would break non-agent nodes that legitimately accumulate messages (e.g., LLM nodes that append to conversation history).

**Rejected** — the fix should be in the agent return, not the reducer.

## Acceptance Criteria

- [x] Agent node returns only new messages (delta), not the full conversation
- [x] Multi-turn agent loop test: verify linear message growth
- [x] Test with 5 loop iterations: state messages count grows linearly
- [x] Existing single-invocation agent tests still pass
- [ ] Documentation updated (patterns.md Pattern 7)

## Alternatives Considered

1. **Passthrough node to clear messages** — `add` reducer prevents clearing; appending `[]` is a no-op
2. **Cap loop iterations** — Workaround, not a fix. Currently used in questionnaire-api (cap at 3 turns)
3. **Don't use `existing_messages`** — Agent would lose multi-turn context within a single invocation. Breaks the agent's internal tool loop.

## Related

- `yamlgraph/tools/agent.py` — agent node implementation
- `yamlgraph/models/state_builder.py` — BASE_FIELDS with `messages: Annotated[list, add]`
- `questionnaire-api/docs/plan-tavily-agent.md` — consumer hit by this bug
- `reference/patterns.md` Pattern 7 — "Stateful Memory" (only documents single-invocation)
