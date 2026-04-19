# Feature Request: FR-244 A2A SDK v1.0 Compatibility

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-04-19

## Summary

Upgrade the `a2a-sdk` dependency from `>=0.3,<1.0` to `>=1.0,<2.0` and fix all breaking changes introduced by the v1.0 stable release (Linux Foundation, IANA-registered media type).

## Value Statement

YAMLGraph users running A2A agents get compatibility with the v1.0 stable protocol, avoiding dependency conflicts with the broader A2A ecosystem that has moved to v1.0.

## Problem

The A2A protocol reached v1.0.0 on March 12, 2026. YAMLGraph's `pyproject.toml` pins `a2a-sdk>=0.3,<1.0` (line 102), which excludes the stable release. The v1.0 SDK introduces breaking changes:

1. **`kind` discriminator removed**: v0.3 used `{"kind": "text", "text": "..."}` in JSON-RPC payloads. v1.0 uses member-name discriminator (the presence of the `text` key itself identifies a TextPart).
2. **Field renaming**: Per Appendix A of the v1.0 spec, some fields have been renamed.
3. **Part construction**: Server-side code already uses `Part(root=TextPart(text=...))` (correct for v1.0), but the client-side `a2a_nodes.py` constructs raw dicts with `{"kind": "text", ...}` (v0.3 pattern).

### Affected Files

| File | Issue | Lines |
|------|-------|-------|
| `pyproject.toml` | Version pin `>=0.3,<1.0` | 102 |
| `yamlgraph/node_factory/a2a_nodes.py` | 3× `kind` field usage (construct + extract) | 53, 63, 99 |
| `yamlgraph/a2a_server.py` | Import paths and API signatures may shift | 22–38 |
| `yamlgraph/a2a_message.py` | Import paths; error type constructors | 16–24 |
| `tests/unit/test_a2a_call_node.py` | 5× test fixtures with `{"kind": "text", ...}` | 285, 324–329, 361, 410 |

### What Is Already v1.0-Compatible

The server-side code (`a2a_server.py`, `a2a_message.py`) already uses `Part(root=TextPart(text=...))` for Part construction and `isinstance(root, TextPart)` for extraction — this pattern is v1.0-compatible. The issue is isolated to:
- The **client-side** `a2a_nodes.py` which builds raw JSON-RPC payloads with `kind` discriminator.
- **Test fixtures** that mock v0.3 response shapes.

## Proposed Solution

### 1. Bump Dependency

```toml
# pyproject.toml
a2a = [
    "a2a-sdk[http-server]>=1.0,<2.0",
]
```

### 2. Fix `a2a_nodes.py` Part Construction (line 99)

```python
# BEFORE (v0.3)
"parts": [{"kind": "text", "text": message}],

# AFTER (v1.0) — member-name discriminator
"parts": [{"text": message}],
```

### 3. Fix `a2a_nodes.py` Part Extraction (lines 53, 63)

```python
# BEFORE (v0.3)
if part.get("kind") == "text" and part.get("text"):

# AFTER (v1.0) — check for text key presence
if "text" in part and part["text"]:
```

### 4. Update Test Fixtures

Replace all `{"kind": "text", "text": "..."}` patterns in `test_a2a_call_node.py` with `{"text": "..."}`.

### 5. Fix Any Import/API Changes

Install `a2a-sdk>=1.0,<2.0` and run the full test suite. Fix any import path changes or renamed fields discovered during the run. The server-side files (`a2a_server.py`, `a2a_message.py`) may need import adjustments even though their Part construction pattern is already correct.

## Acceptance Criteria

- [x] `pyproject.toml` pins `a2a-sdk>=1.0,<2.0`
- [x] `pip install -e ".[a2a]"` installs a2a-sdk v1.0+
- [x] No `kind` discriminator field in any source file (grep-verified)
- [x] `pytest tests/unit/test_a2a_server.py tests/unit/test_a2a_message.py tests/unit/test_a2a_commands.py tests/unit/test_a2a_call_node.py -v` — all 96 tests pass
- [x] `ruff check yamlgraph/a2a_server.py yamlgraph/a2a_message.py yamlgraph/node_factory/a2a_nodes.py` — clean
- [x] Part construction in `a2a_nodes.py` uses v1.0 member-name discriminator format
- [x] Part extraction in `a2a_nodes.py` uses key-presence check instead of `kind` field
- [x] Tests updated to use v1.0 response shapes

## Alternatives Considered

1. **Pin `>=0.3`** (accept both v0.3 and v1.0): Rejected — the breaking changes mean code cannot support both simultaneously. The `kind` field is removed, not optional.
2. **Vendor the v0.3 types**: Rejected — adds maintenance burden for a protocol that has stabilized at v1.0.
3. **Drop A2A support entirely**: Rejected — A2A is a growing standard (23.3K stars, Linux Foundation backing) and YAMLGraph has 946 LOC + 92 tests invested.

## Related

- **CAP-81**: A2A Protocol Server (REQ-YG-206–213)
- **CAP-101**: A2A Call Node Type (REQ-YG-243)
- **FR-208**: A2A Graph Support (Implemented)
- **FR-209**: A2A Demo Streaming Response (Implemented)
- **FR-225**: A2A Test Coverage (Implemented)
- **FR-240**: A2A Call Node Type (Implemented)
- `yamlgraph/a2a_server.py`, `yamlgraph/a2a_message.py`, `yamlgraph/node_factory/a2a_nodes.py`
- `tests/unit/test_a2a_server.py`, `tests/unit/test_a2a_message.py`, `tests/unit/test_a2a_commands.py`, `tests/unit/test_a2a_call_node.py`
