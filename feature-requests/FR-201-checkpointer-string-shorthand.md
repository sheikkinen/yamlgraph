# Feature Request: Checkpointer String Shorthand Config

**Priority:** LOW
**Type:** Enhancement
**Status:** Done
**Effort:** 0.5 days
**Requested:** 2026-03-17

## Summary

Allow `get_checkpointer()` and `get_checkpointer_async()` to accept a plain string (e.g., `"memory"`) as shorthand for `{"type": "memory"}`.

## Value Statement

Reduces boilerplate in YAML graph configs and Python callers that only need a checkpointer type without extra options.

## Problem

Currently both sync and async checkpointer factories require a dict config even when only the type matters. Callers writing `checkpointer: memory` in YAML get a string, but the factory demands `{"type": "memory"}`. This forces unnecessary normalization at every callsite.

## Proposed Solution

Normalize at the boundary: when `config` is a `str`, convert it to `{"type": config}` before any further processing. This follows the project's "normalize at the boundary where external data enters" principle.

**Changes:**
- `get_checkpointer(config: dict | str | None)` — type signature widened
- `get_checkpointer_async(config: dict | str | None)` — type signature widened
- Early normalization: `if isinstance(config, str): config = {"type": config}`

## Acceptance Criteria

- [x] `get_checkpointer("memory")` returns `InMemorySaver`
- [x] `get_checkpointer("sqlite")` returns `SqliteSaver` (with default `:memory:` path)
- [x] `get_checkpointer_async("memory")` returns `MemorySaver`
- [x] `get_checkpointer("unknown")` raises `ValueError`
- [x] Existing dict configs still work unchanged
- [x] Tests tagged with REQ-YG-196
- [x] Requirement REQ-YG-196 in ARCHITECTURE.md
- [x] Capability YAML updated

## Alternatives Considered

- Normalizing at each callsite: violates boundary normalization principle, causes duplication.
- Overloaded factory with keyword args: over-engineering for a simple shorthand.

## Related

- REQ-YG-025: Checkpointer provisioning
- REQ-YG-196: Checkpointer string shorthand config
- CAP-07: State Persistence
