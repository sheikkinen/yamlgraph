# Feature Request: Log exceptions in MCP _handle_run_graph before returning error JSON

**Priority:** MEDIUM
**Type:** Bug
**Status:** Judged
**Effort:** 0.5 days
**Requested:** 2026-07-03

## Summary

`_handle_run_graph` (inner graph-execution handler) in the MCP server catches
exceptions and returns `{"error": ...}` JSON without logging. The outer
tool handler (~line 246) logs with `exc_info=True`, but because the inner
handler catches first, the outer logging never fires for graph failures.
Blind debugging for MCP clients.

## Value Statement

Operators diagnosing failed MCP tool calls find the full stack trace in
server logs instead of reverse-engineering a one-line JSON error string.

## Problem

`yamlgraph/mcp_server.py:315-321`:

```python
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"error": f"Graph execution failed: {e}"}),
            )
        ]
```

No `logger.error`. Provider auth failures, YAML compile errors, and runtime
faults all collapse into an opaque string. Inconsistent with the outer
handler at `mcp_server.py:246-252`, which correctly logs
`logger.error("Tool %s failed: %s", name, e, exc_info=True)`. Because the
inner handler catches first, the outer logging never fires for graph
execution failures. Commandment 6: bear witness of thy errors.

The `TimeoutError` branch above it has the same gap (no log on timeout).

## Proposed Solution

```python
    except TimeoutError:
        logger.error("Graph '%s' timed out after %ss", graph_name, INVOKE_TIMEOUT)
        ...
    except Exception as e:
        logger.error("Graph '%s' execution failed", graph_name, exc_info=True)
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"error": f"Graph execution failed: {e}"}),
            )
        ]
```

## Acceptance Criteria

- [ ] Failing test first (RED): `_handle_run_graph` with a graph that raises →
      assert `logger.error` called with `exc_info=True` (caplog)
- [ ] Timeout branch also logs
- [ ] Returned JSON shape unchanged (MCP clients unaffected)
- [ ] Changelog fragment in `changelog/unreleased/`

## Alternatives Considered

- **Re-raise and let the outer handler log** — rejected: outer handler
  returns a generic error without the graph-name context and available-graphs
  hint the inner handler provides; would change client-visible payloads.
- **Return traceback in the JSON payload** — rejected: leaks internals to
  remote MCP clients; logs are the right sink.

## Related

- docs/2026-07-03-review-fable.md (Issue 4)
- yamlgraph/mcp_server.py:300-321 (inner handler), 246-252 (outer handler)

## Judgement

**APPROVED with corrections.** The FR's description of which handler logs
and which doesn't is inverted: the OUTER tool handler (line 246) DOES log
with `exc_info=True`; the INNER graph-execution handler (~line 315) does NOT
log. The fix direction is correct — add logging to the inner handler — but
the FR text is misleading.

**Amendments:**
1. Correct the FR description: the outer handler logs, the inner doesn't.
   The FR says the opposite.
2. TimeoutError branch (~line 306) also confirmed: no logging. Fix both
   branches as proposed.
3. This is a 2-line fix. Effort 0.5 days is generous but acceptable for
   TDD overhead.
