# Feature Request: Replace type: a2a_call with type: python + contrib client

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 2 days
**Requested:** 2026-04-19

## Summary

Remove the dedicated `type: a2a_call` node type and replace it with a contrib function (`yamlgraph/contrib/a2a_client.py`) invoked via `type: python`. This eliminates a disproportionate framework surface (502 lines across factory + linter + compiler) for a feature used in exactly one demo graph.

## Value Statement

Framework maintainers get reduced surface area and SDK coupling, while A2A consumer functionality is preserved intact via the established `type: python` + contrib pattern.

## Problem

`type: a2a_call` is one of 15 node types in the registry with a full compilation pipeline (factory, linter, compiler handler, enum value), 5 requirements, and 3 capabilities — for a feature exercised by a single demo graph. The implementation cost is disproportionate to usage:

- **362 lines** in `a2a_nodes.py` with DRY violations (3 text extractors doing the same thing) and mixed abstraction (raw `httpx.post` for non-streaming vs SDK `Client` for streaming)
- **140 lines** of dedicated linter patterns
- **~23 lines** of compiler handler in `node_compiler.py` (already at 444 lines)
- **Direct protobuf import** for Agent Card parsing
- **Tight coupling** to A2A SDK (`>=1.0.0a0,<2.0`) — FR-244 already patched one breaking change

MCP is consumed via agent tools (no dedicated node type). A2A consumer got a dedicated node type for no principled reason — protocol enthusiasm at implementation time.

## Proposed Solution

### Phase 1: Create contrib client (~80 lines)

Create `yamlgraph/contrib/a2a_client.py` with a single entry point:

```python
def send_a2a_message(state: dict) -> dict:
    """Send message to A2A agent. type: python tool function contract."""
```

The function:
- Reads from state: `agent_url` (required), `message` or `message_template` (required), `skill` (optional), `streaming` (optional), `timeout` (optional, default 120)
- Unifies on A2A SDK `Client` for both streaming and non-streaming (eliminates raw httpx path)
- Performs Agent Card fetch + skill validation when `skill` present
- Renders Jinja2 templates if `message_template` present
- Returns `{"response": extracted_text}`

### Phase 2: Remove dedicated node type

**Delete:**
- `yamlgraph/node_factory/a2a_nodes.py` (362 lines)
- `yamlgraph/linter/patterns/a2a.py` (140 lines)

**Modify:**
- `yamlgraph/constants.py` — remove `A2A_CALL` from `NodeType` enum
- `yamlgraph/node_compiler.py` — remove `_compile_a2a_call_node` + registry entry
- `yamlgraph/node_factory/__init__.py` — remove `create_a2a_call_node` import
- `yamlgraph/linter/patterns/__init__.py` — remove `check_a2a_call_patterns`
- `yamlgraph/linter/graph_linter.py` — remove `check_a2a_call_patterns` call
- `yamlgraph/models/graph_schema.py` — remove A2A-specific fields from `NodeConfig` if present

### Phase 3: Update demo graph

Rewrite `examples/demos/a2a_call/graph.yaml` to use `type: python` + contrib:

```yaml
tools:
  a2a_send:
    type: python
    module: yamlgraph.contrib.a2a_client
    function: send_a2a_message
    description: "Send message to A2A agent"

nodes:
  ask_agent:
    type: python
    tool: a2a_send
    state_key: agent_response
    variables:
      agent_url: "http://localhost:9240/"
      message: "name={state.name} style={state.style}"
      timeout: "60"
```

Re-run demo and capture new `demo-output.log`.

### Phase 4: Migrate tests

- Delete `tests/unit/test_a2a_call_node.py`
- Create `tests/unit/test_a2a_contrib_client.py` covering: send, streaming, skill validation, error handling

### Phase 5: Update docs and capabilities

- `reference/a2a-server.md` — update consumer section with `type: python` + contrib example
- `ARCHITECTURE.md` — update REQ-YG-243, 250–253 to describe contrib pattern
- `capabilities/CAP-101-a2a-call-node.yaml` — retitle and update
- `capabilities/CAP-105-a2a-consumer-phase2.yaml` — update

## Acceptance Criteria

- [x] `yamlgraph/contrib/a2a_client.py` exists with `send_a2a_message(state) → dict`
- [x] `yamlgraph/node_factory/a2a_nodes.py` deleted
- [x] `yamlgraph/linter/patterns/a2a.py` deleted
- [x] `A2A_CALL` removed from `NodeType` enum
- [x] `node_compiler.py` has no A2A handler
- [x] Demo graph uses `type: python` + contrib
- [ ] Demo runs end-to-end (`demo-output.log` regenerated)
- [x] Unit tests cover contrib client: send, streaming, skill validation, error handling
- [x] Reference docs updated
- [x] All existing tests pass (no regressions)
- [x] Net line count reduction ≥ 400 lines

## Alternatives Considered

1. **Keep `type: a2a_call` but clean up DRY violations only** — Reduces code quality issues but doesn't address the disproportionate framework surface or SDK coupling breadth. The fundamental problem (dedicated node type for one-demo feature) remains.

2. **Delete A2A consumer entirely** — Too aggressive. The contrib function preserves functionality at minimal cost (~80 lines, single-module SDK coupling) and can be promoted back if usage grows.

3. **Move to a plugin/extension system** — Overengineered for the current need. The `contrib/` pattern already exists (`progress.py`, `utils.py`) and serves the same isolation purpose without new infrastructure.

## Dependencies

- **FR-252** (Python node `variables:` expression support) — Status: Approved. Required so the demo graph can pass `agent_url`, `message`, `timeout` as variables to the `type: python` node.

## Design Rationale

**Serving** (exposing graphs as A2A agents) is infrastructure — it earns its place in the core. **Consuming** (calling external agents) is plumbing — it belongs in contrib, where SDK coupling is isolated and usage can grow organically. This mirrors how MCP consumption is handled (via agent tools, not a dedicated node type). If A2A consumer usage grows beyond one demo, the contrib function can be promoted. If it doesn't, no framework weight is wasted.

## Related

- FR-240: Original `type: a2a_call` implementation
- FR-244: A2A SDK breaking change patch
- FR-248: Agent Card, skill selection, streaming additions
- FR-252: Python node variables support (prerequisite)
- `examples/demos/a2a_call/` — the sole consumer of this node type

## Judgement

**Verdict: APPROVED** — 2026-04-19

**Rationale:** The FR is clear, minimal, and internally consistent. It addresses a single concern (demote A2A consumer from dedicated node type to contrib function) using a proven pattern (type: python + contrib, mirroring MCP consumption). All acceptance criteria are measurable. The phased approach is logical and feasible. FR-252 prerequisite is confirmed approved.

**Corrections applied:**
- Node type count: 14 → 15
- Compiler handler lines: ~14 → ~23
- SDK version: "pre-1.0 (v0.3.26)" → `>=1.0.0a0,<2.0`
- Effort bumped 1.5 → 2 days (1,234-line test file migration warrants padding)

**Authority granted.** Scope frozen. Proceed to Enforce.
