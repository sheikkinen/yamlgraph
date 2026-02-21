# Feature Request: Multi-Turn Test Fixtures

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-02-21

## Summary

Add `@pytest.fixture` helpers that simulate 3+ sequential invocations of the same node with accumulating state, catching reducer composition bugs that single-invocation tests miss.

## Problem

Current tests invoke nodes once:

```python
def test_agent_node(mock_llm):
    state = {"topic": "AI"}
    result = agent_node(state)
    assert "messages" in result  # ✅ Passes
```

This missed FR-057 (quadratic message growth) because the bug only manifests when the node is invoked **multiple times** with its own output fed back:

| Turn | messages in state | Agent returns | State after `add` |
|------|-------------------|---------------|-------------------|
| 1 | 0 | 5 | 5 |
| 2 | 5 | 10 | 15 ← duplication starts |
| 3 | 15 | 20 | 35 ← 3x expected |

**Patterns that need multi-turn testing:**
- `Annotated[list, add]` reducers — do nodes return new items only, or full list?
- `skip_if_exists` logic — does it correctly skip on turn 2+?
- Checkpoint resume — is state correctly restored mid-graph?
- Agent loops — does context grow as expected?

## Proposed Solution

### 1. Multi-Turn State Fixture

```python
@pytest.fixture
def multi_turn_state():
    """Factory for multi-turn state simulation."""
    def _create(initial_state: dict, turns: int = 3):
        """Yield state after each turn, simulating reducer application."""
        from yamlgraph.models.state_builder import merge_state

        state = initial_state.copy()
        yield state  # Turn 0 (initial)

        for turn in range(1, turns + 1):
            yield state  # State for turn N input
            # Caller updates state after yield

    return _create
```

### 2. Node Multi-Turn Helper

```python
@pytest.fixture
def invoke_multi_turn():
    """Invoke a node function multiple times with accumulating state."""
    def _invoke(node_fn, initial_state: dict, turns: int = 3) -> list[dict]:
        """Returns list of states after each turn."""
        from copy import deepcopy
        from yamlgraph.models.state_builder import apply_reducers

        states = [deepcopy(initial_state)]
        state = deepcopy(initial_state)

        for _ in range(turns):
            result = node_fn(state)
            state = apply_reducers(state, result)
            states.append(deepcopy(state))

        return states

    return _invoke
```

### 3. Growth Assertion Helper

```python
@pytest.fixture
def assert_linear_growth():
    """Assert that a list field grows linearly, not quadratically."""
    def _assert(states: list[dict], field: str, expected_per_turn: int):
        """Verify field grows by expected_per_turn each iteration."""
        for i, state in enumerate(states[1:], start=1):
            expected = i * expected_per_turn
            actual = len(state.get(field, []))
            assert actual == expected, (
                f"Turn {i}: expected {field} length {expected}, got {actual}. "
                f"Possible reducer composition bug."
            )

    return _assert
```

### Usage Example

```python
@pytest.mark.req("REQ-YG-022")
def test_agent_messages_linear_growth(invoke_multi_turn, assert_linear_growth, mock_llm):
    """Verify agent messages grow linearly across turns (FR-057 regression)."""
    from yamlgraph.tools.agent import create_agent_node

    node_fn = create_agent_node(config, tools=[])
    initial_state = {"topic": "test", "messages": []}

    states = invoke_multi_turn(node_fn, initial_state, turns=5)

    # Should add ~5 messages per turn, not accumulate duplicates
    assert_linear_growth(states, "messages", expected_per_turn=5)
```

## Acceptance Criteria

- [ ] `invoke_multi_turn` fixture simulates N sequential node invocations
- [ ] `assert_linear_growth` validates list fields don't grow quadratically
- [ ] At least 3 existing tests converted to multi-turn style
- [ ] FR-057 regression test added using new fixtures
- [ ] `skip_if_exists` multi-turn test verifies skip on turn 2+
- [ ] Documentation in `tests/conftest.py` docstrings

## Downstream Impact

| Component | Effect |
|-----------|--------|
| `tests/conftest.py` | New fixtures (~50 lines) |
| `tests/unit/test_agent.py` | New multi-turn regression test |
| Future node tests | Pattern available for composition testing |
| CI | May catch more bugs before merge |

**Not affected:** Framework code — this is test infrastructure only.

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Integration tests only | Too slow, requires real LLMs |
| Manual state setup per test | Verbose, error-prone |
| Property-based testing (Hypothesis) | Overkill for this pattern |

## Related

- FR-057: Agent messages quadratic growth (the bug this would have caught)
- FR-058: Agent streaming filter
- Diary entry: "Meta-Reflection — The Recurring Traps" (composition bugs)
- `tests/conftest.py` (existing fixture patterns)
