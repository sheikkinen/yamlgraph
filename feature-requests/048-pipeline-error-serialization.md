# FR-048: PipelineError Redis Serialization

**Priority:** HIGH
**Type:** Bug
**Status:** Closed
**Effort:** 0.5 days
**Requested:** 2026-02-19
**Closed:** 2026-02-19

## Summary

`PipelineError` (a Pydantic `BaseModel`) is not handled by `serialize_value()` in `storage/serializers.py`, causing `TypeError` when LangGraph checkpointer saves state to Redis after an error occurs during graph execution.

## Problem

When a node fails (e.g., Anthropic 401), yamlgraph's `on_error` handler wraps the exception into a `PipelineError` and stores it in the graph state. When LangGraph then calls `checkpointer.aput()` to persist the checkpoint, `orjson.dumps()` invokes `serialize_value()` as a fallback — which raises `TypeError: Cannot serialize <class 'yamlgraph.models.schemas.PipelineError'>`.

This causes the **entire SSE response stream to crash**, returning a `RemoteProtocolError` to the client. The original error (e.g., bad API key) is swallowed; the user sees only a broken connection.

### Reproduction

```
# Fly.io logs from questionnaire-api (2026-02-19)
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 401 Unauthorized"
[ERROR] yamlgraph.error_handlers: Node generate_opening failed: ...authentication_error...
ERROR:    Exception in ASGI application

  File "yamlgraph/storage/simple_redis.py", line 146, in aput
    data = orjson.dumps(stored, default=serialize_value)
TypeError: Type is not JSON serializable: PipelineError
```

The error path: `aput()` → `orjson.dumps(stored, default=serialize_value)` → `serialize_value()` does not handle `BaseModel` instances → `TypeError`.

## Proposed Solution

Add a `BaseModel` handler in `serialize_value()`. Since `PipelineError` is a Pydantic model, the fix is generic and covers any future Pydantic models that end up in state:

```python
# storage/serializers.py  line ~93
def serialize_value(obj: Any) -> Any:
    """Serialize non-JSON types for orjson."""
    if isinstance(obj, BaseModel):
        return {"__type__": "pydantic", "class": f"{type(obj).__module__}.{type(obj).__qualname__}", "value": obj.model_dump(mode="json")}
    if isinstance(obj, UUID):
        ...
```

For deserialization, either:
- **Option A (safe):** Deserialize as plain dict — sufficient for error inspection, no import needed
- **Option B (full-fidelity):** `importlib.import_module()` + `getattr()` to reconstruct the model (yamlgraph already uses this pattern for `output_model` resolution)

Option A is simpler and avoids import-time risks:

```python
def deserialize_value(obj: dict) -> Any:
    if isinstance(obj, dict) and "__type__" in obj:
        type_name = obj["__type__"]
        if type_name == "pydantic":
            return obj["value"]  # plain dict, good enough for checkpoints
        ...
```

## Acceptance Criteria

- [x] `PipelineError` in graph state survives `aput()` → Redis → `aget()` round-trip
- [x] Generic `BaseModel` serialization (not PipelineError-specific)
- [x] After a node error, the SSE stream completes gracefully (no crash)
- [x] Error details remain inspectable after checkpoint restore
- [x] Tests: serialize/deserialize round-trip for `PipelineError` with all field types
- [ ] Tests: graph execution with `on_error` + Redis checkpointer

## Alternatives Considered

1. **Handle only `PipelineError`** — Too narrow; any Pydantic model hitting state would crash the same way.
2. **Catch `TypeError` in `aput()`** — Masks the problem; checkpoint data silently lost.
3. **Make `PipelineError` JSON-native via `orjson`** — Would require registering with orjson's `option=orjson.OPT_PASSTHROUGH_DATACLASS`, but Pydantic v2 models aren't dataclasses.

## Related

- `yamlgraph/storage/serializers.py:93` — `serialize_value()`
- `yamlgraph/storage/simple_redis.py:146` — crash site
- `yamlgraph/models/schemas.py:28` — `PipelineError(BaseModel)`
- Discovered in `questionnaire-api` Fly.io e2e (2026-02-19) with expired Anthropic key
