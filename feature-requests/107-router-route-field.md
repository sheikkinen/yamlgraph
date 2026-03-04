# Feature Request: Router `route_field` — Kill Hardcoded tone/intent

**Priority:** HIGH
**Type:** Bug / Technical Debt
**Status:** Enforced ✅ — 1854 tests green, 0 errors, all graphs lint clean
**Effort:** 0.5 day
**Requested:** 2026-03-04

---

## Judgement

### Verdict: Approved with scope reduction

The problem is real and the fix is correct. But the proposal overengineers
backward compatibility. Auto-inference from schema (§4) adds complexity to
solve a problem that doesn't exist — all 10 router nodes are under our control
and can be updated in the same PR. Schema introspection at compile time to
guess the field name is the same category of magic we're trying to kill.

### Rulings

1. **`route_field` is mandatory for router nodes.** No auto-inference, no
   fallback to `tone`/`intent`. If you have a router, you declare the field.
   Commandment 3: *config is truth*.

2. **Update all 10 existing graphs in the same PR.** This is 10 one-line
   additions (`route_field: intent` or `route_field: tone`). Not a migration —
   just a config addition.

3. **Drop the linter rule (§5).** Pydantic validation already catches missing
   `route_field` at load time. A linter warning is redundant. Kill entropy.

4. **Drop the phased migration.** One PR, one change, all graphs updated.
   No deprecation warnings, no compat shims.

5. **NC-111 band-aid stays reverted.** The `if route_key: update[state_key] =
   route_key` patch was removed. FR-107 implementation will fix it by design.

### Scope delta from proposal

| Proposed | Ruling | Reason |
|----------|--------|--------|
| §4 Auto-infer from schema | **Cut** | Same magic category as tone/intent. Violates the goal. |
| §5 Linter rule | **Cut** | Pydantic validator is sufficient. |
| Phased migration | **Cut** | 10 graphs, all ours. One PR. |
| `route_field` optional with fallback | **Mandatory** | Explicit > implicit (PEP 20). |
| yamlgraph_gen prompt update | **Keep** | Remove "MUST be intent or tone" lie. |

### Files to touch

| File | Change |
|------|--------|
| `yamlgraph/models/graph_schema.py` | Add `route_field` field + validator |
| `yamlgraph/node_factory/llm_nodes.py` | Read `route_field`, replace hardcoded extraction |
| `tests/unit/test_router.py` | Update 3 NC-111 tests to use `route_field`, add custom field test |
| `examples/demos/router/graph.yaml` | Add `route_field: tone` |
| `examples/yamlgraph_gen/graph.yaml` | Add `route_field: intent` |
| `examples/yamlgraph_gen/snippets/nodes/router-basic.yaml` | Add `route_field`, update comment |
| `examples/yamlgraph_gen/snippets/patterns/classify-then-process.yaml` | Add `route_field` |
| `examples/yamlgraph_gen/prompts/generate_prompts.yaml` | Remove "MUST be intent or tone" |
| `questionnaire-api/questionnaires/navigator/graph.yaml` | 4 routers: add `route_field: intent` |
| `questionnaire-api/questionnaires/ninchat-inquiry-rewrite/graph.yaml` | Add `route_field: intent` |
| `projects/ninchat_voice/graphs/ninchat-voice-coordinator.yaml` | Add `route_field: intent` |
| `reference/graph-yaml.md` | Document `route_field` |

### Risk: Zero

All 10 router nodes use `intent` (9) or `tone` (1). Every schema already has
the field. We're just making the implicit explicit.

---

## Summary

Replace the hardcoded `tone`/`intent` field extraction in router nodes with an
explicit `route_field` config key. The framework currently guesses which field
to read from the LLM result — this is brittle, undocumented magic that forces
all router schemas to use one of two blessed field names.

## Value Statement

Graph authors can name their classification field anything (`decision`,
`category`, `priority`, `status`) without hitting silent routing failures.
The NC-111 band-aid (storing route key over Pydantic object) becomes
unnecessary — route extraction is clean by design.

## Problem

### The Hardcoded Extraction (lines 199–205 of llm_nodes.py)

```python
# Support both Pydantic models (getattr) and dicts (.get)
if isinstance(result, dict):
    route_key = result.get("tone") or result.get("intent")
else:
    route_key = getattr(result, "tone", None) or getattr(
        result, "intent", None
    )
```

**Issues:**

1. **Magic field names** — only `tone` and `intent` work. Any other field name
   (e.g. `decision`, `category`, `priority`, `status`) silently falls through
   to `default_route` or first route. No error, no warning.

2. **Precedence bug** — `tone` is checked before `intent`. A schema with both
   fields always routes on `tone`, even if the author meant `intent`.

3. **NC-111 band-aid** — because `update[state_key] = result` stores the full
   Pydantic object, we need a follow-up `update[state_key] = route_key` to
   fix state pollution. With explicit extraction, this is free.

4. **Documented as known limitation** — the snippet template literally says:
   > *"The prompt must return an object with 'tone' or 'intent' field
   > (hardcoded in framework)."*

### Affected Graphs (full audit — 10 router nodes)

| Graph | Router Node | Schema Field | `route_field` to add |
|-------|------------|--------------|---------------------|
| `demos/router/graph.yaml` | classify | `tone` | `route_field: tone` |
| `navigator/graph.yaml` | classify | `intent` | `route_field: intent` |
| `navigator/graph.yaml` | tavily_check_done | `intent` | `route_field: intent` |
| `navigator/graph.yaml` | classify_priority | `intent` | `route_field: intent` |
| `navigator/graph.yaml` | ninchat_check_done | `intent` | `route_field: intent` |
| `ninchat-inquiry-rewrite/graph.yaml` | check_done | `intent` | `route_field: intent` |
| `yamlgraph_gen/graph.yaml` | classify_patterns | `intent` | `route_field: intent` |
| `ninchat-voice-coordinator.yaml` | classify_intent | `intent` | `route_field: intent` |
| Snippet: `router-basic.yaml` | template | `intent` | `route_field: __ROUTE_FIELD__` |
| Snippet: `classify-then-process.yaml` | template | `intent` | `route_field: intent` |

All current graphs use `tone` (1) or `intent` (9). All under our control.

## Proposed Solution

### 1. Add `route_field` to NodeConfig (mandatory for routers)

```yaml
classify:
  type: router
  prompt: classify_tone
  route_field: tone          # ← mandatory: which field to extract
  routes:
    positive: respond_positive
    negative: respond_negative
  default_route: respond_neutral
```

### 2. Schema change in `models/graph_schema.py`

```python
class NodeConfig(BaseModel):
    route_field: str | None = Field(
        default=None,
        description="Field name to extract route key from LLM result (router nodes)",
    )
```

Validator (alongside existing router checks):
```python
if self.type == NodeType.ROUTER and not self.route_field:
    raise ValueError("Router node requires 'route_field'")
```

### 3. Replace extraction logic in `llm_nodes.py`

Before (fragile):
```python
if isinstance(result, dict):
    route_key = result.get("tone") or result.get("intent")
else:
    route_key = getattr(result, "tone", None) or getattr(
        result, "intent", None
    )
```

After (explicit):
```python
if isinstance(result, dict):
    route_key = result.get(route_field)
else:
    route_key = getattr(result, route_field, None)

# Store extracted key, not the full Pydantic object (NC-111 free)
if route_key is not None:
    update[state_key] = route_key
```

### 4. Update all 10 graphs + 2 snippets

One-line addition per router node. No behavior change.

## Acceptance Criteria

- [ ] `route_field: str | None` added to `NodeConfig` in `graph_schema.py`
- [ ] Pydantic validator: router without `route_field` → `ValueError`
- [ ] `llm_nodes.py` extraction uses `route_field` instead of hardcoded `tone`/`intent`
- [ ] `state_key` stores extracted string, not Pydantic object (NC-111 by design)
- [ ] All 10 router graphs updated with explicit `route_field`
- [ ] 2 snippet templates updated
- [ ] NC-111 tests updated to use `route_field`
- [ ] New test: custom field name (e.g. `decision`) works
- [ ] `yamlgraph_gen` prompts: remove "MUST be intent or tone"
- [ ] `yamlgraph graph lint` passes on all updated graphs
- [ ] Full test suite green (`pytest tests/unit/ -q --no-cov`)

## Test Plan

### RED (write first)

```python
def test_router_route_field_custom_name():
    """Router extracts route key from explicitly named field."""
    mock_result = MagicMock()
    mock_result.decision = "approve"
    node_config = {
        "type": "router",
        "prompt": "classify",
        "route_field": "decision",
        "routes": {"approve": "approve_handler", "reject": "reject_handler"},
        "state_key": "verdict",
    }
    node_fn = create_node_function("classify", node_config, {})
    result = node_fn({})
    assert result["verdict"] == "approve"
    assert result["_route"] == "approve_handler"

def test_router_missing_route_field_raises():
    """Router without route_field fails Pydantic validation."""
    with pytest.raises(ValidationError, match="route_field"):
        NodeConfig(type="router", prompt="classify", routes={"a": "b"})

def test_router_state_key_stores_string_not_pydantic():
    """route_field extraction gives string, not Pydantic object."""
    # ... existing NC-111 test, updated with route_field="intent"
```

### GREEN

Implement `route_field` in schema + extraction.

### Update existing

- 3 NC-111 tests: add `route_field` to `node_config`
- 11 existing router tests: add `route_field` where needed

## Alternatives Considered

1. **Keep hardcoded + add more field names** — rejected: infinite list, still
   magic. Violates Commandment 3 (config is truth).

2. **NC-111 band-aid only** — rejected: treats symptom (Pydantic in state),
   not disease (hardcoded field names). Already reverted.

3. **Auto-infer from schema** — rejected at Judgement: same category of magic
   as hardcoded names. Schema introspection to guess the field is complexity
   that serves no one when all 10 graphs are under our control.

4. **Use first field from schema** — rejected: fragile if schema has multiple
   fields (e.g. `tone` + `confidence` + `reasoning` in `classify_tone.yaml`).

## Related

- NC-111: Router `state_key` storing Pydantic objects (band-aid reverted, root cause is this FR)
- [llm_nodes.py](yamlgraph/node_factory/llm_nodes.py#L197-L215) — current router block
- [router-basic.yaml](examples/yamlgraph_gen/snippets/nodes/router-basic.yaml#L22) — documents the limitation
- [classify_tone.yaml](examples/demos/router/prompts/classify_tone.yaml) — uses `tone` field
- [classify.yaml](questionnaire-api/questionnaires/navigator/prompts/classify.yaml) — uses `intent` field
- [graph_schema.py NodeConfig](yamlgraph/models/graph_schema.py#L53) — where `route_field` goes
