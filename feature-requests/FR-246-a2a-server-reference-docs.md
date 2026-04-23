# Feature Request: A2A Server Reference Documentation

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-04-19
**Judged:** 2026-04-19

## Summary

Write `reference/a2a-server.md` — the user-facing reference documentation for the A2A protocol server (FR-208/209/225, CAP-81). The A2A server is fully implemented but undiscoverable without reading source code.

## Value Statement

Users and integrators can adopt the A2A server by reading a single reference document, without reverse-engineering `a2a_server.py` or the demo scripts.

## Problem

The A2A server is implemented across four modules (`a2a_server.py`, `a2a_message.py`, `discovery.py`, `cli/a2a_commands.py`) with 30+ tests and two demos, but zero user-facing reference documentation. The MCP server has `reference/mcp-server.md`; the A2A server has nothing equivalent. The CLI reference (`reference/cli.md`) also omits the `a2a` subcommands entirely.

Consequences:
1. New users cannot discover that `yamlgraph a2a serve` exists
2. Integration developers cannot understand message format, Agent Card structure, or error mapping without reading Python source
3. The relationship between MCP and A2A servers is unclear (shared discovery, different transports)

## Proposed Solution

Create `reference/a2a-server.md` covering:

### 1. Quickstart (hello graph)

```bash
# Install A2A dependency
pip install -e ".[a2a]"

# Start server with the hello graph
yamlgraph a2a serve examples/demos/hello/ --port 9090

# Fetch Agent Card
curl http://localhost:9090/.well-known/agent-card.json

# Send a task
curl -X POST http://localhost:9090/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "name=World style=casual"}]
      }
    }
  }'
```

### 2. CLI Commands

| Command | Description |
|---------|-------------|
| `yamlgraph a2a serve [path] --host --port` | Start A2A server exposing discovered graphs |
| `yamlgraph a2a card [path] --host --port` | Print Agent Card JSON without starting server |

### 3. Agent Card Generation

How `build_agent_card()` maps graph metadata to the A2A `AgentCard`:

| Graph YAML | Agent Card field |
|------------|-----------------|
| `name` | `skills[].id`, `skills[].name` |
| `description` | `skills[].description` |
| presence of `nodes` | included in discovery |
| `state` keys | `required_vars` (used at message parse time) |

### 4. Message-to-State Mapping

Document the four parsing modes (JSON → key_value → single_input → fallback) with examples for each. Reference `parse_a2a_message()`.

### 5. Task Lifecycle

| A2A method | YAMLGraph behaviour |
|------------|---------------------|
| `message/send` | Compile and invoke graph, return result as artifact |
| `message/stream` | SSE event stream: working → artifact → completed |
| `task/cancel` | Cancel running asyncio task |

Task state mapping: `submitted` → `working` → `completed`/`failed`/`input-required`/`canceled`.

### 6. Error Mapping

| PipelineError type | A2A error | HTTP status |
|--------------------|-----------|-------------|
| `LLM_ERROR`, `STATE_ERROR`, `UNKNOWN_ERROR` | `InternalError` | 500 |
| `VALIDATION_ERROR`, `PROMPT_ERROR`, `VERIFICATION_ERROR` | `InvalidParamsError` | 400 |

### 7. Interrupt / Human-in-Loop

When a graph hits `interrupt_before`/`interrupt_after`, the server emits `TaskState.input_required`. Document how `__interrupt__` detection works.

### 8. Authentication

State: not implemented. Document the recommended deployment pattern: reverse proxy (nginx/Caddy/Traefik) for production auth. Reference that Agent Cards are generated with `authentication: null`.

### 9. Deployment Patterns

- Standalone (development): `yamlgraph a2a serve`
- Behind reverse proxy (production): nginx/Caddy with TLS + auth
- Container: Dockerfile snippet with `CMD ["yamlgraph", "a2a", "serve"]`

### 10. Relationship to MCP Server

| Aspect | MCP (`yamlgraph mcp serve`) | A2A (`yamlgraph a2a serve`) |
|--------|-----|-----|
| Transport | stdio | HTTP (JSON-RPC) |
| Discovery | Shared `discovery.py` | Shared `discovery.py` |
| Model | Tools | Agent Skills |
| Streaming | No | SSE |
| Auth | None (IDE-controlled) | None (use reverse proxy) |

### Secondary: Update `reference/cli.md`

Add the `a2a` subcommands to the commands overview table and add a `yamlgraph a2a` section with `serve` and `card` subcommand documentation.

## Acceptance Criteria

- [x] REQ-YG-246 added to `ARCHITECTURE.md` capabilities table and requirement descriptions (reference doc for A2A server)
- [x] `reference/a2a-server.md` created with all 10 sections above (REQ-YG-246)
- [x] Quickstart example is copy-pasteable and works with the hello graph
- [x] `reference/cli.md` updated to include `a2a serve` and `a2a card` commands
- [x] `reference/README.md` updated to link to `a2a-server.md` (if it maintains a doc index)
- [x] No new Python code — documentation only
- [x] All code examples verified against current implementation in `a2a_server.py`, `a2a_message.py`, `cli/a2a_commands.py`

## Alternatives Considered

1. **Inline docs only (docstrings + `--help`)**: Insufficient for integration developers who need the full message format and deployment patterns. CLI `--help` only covers flags, not protocol semantics.

2. **Expand `examples/demos/a2a_server/README.md`**: Demo READMEs are for running the demo, not comprehensive reference. Mixing reference material into demo docs violates separation of concerns.

3. **Add to existing `reference/cli.md`**: The A2A server is more than a CLI command — it's a protocol server with its own message format, lifecycle, and deployment model. A dedicated doc mirrors the MCP server pattern.

## Related

- `reference/mcp-server.md` — structural template for this doc
- `yamlgraph/a2a_server.py` — server implementation (331 lines)
- `yamlgraph/a2a_message.py` — message parsing, Agent Card, error mapping (242 lines)
- `yamlgraph/cli/a2a_commands.py` — CLI integration (89 lines)
- `yamlgraph/discovery.py` — shared graph discovery (75 lines)
- `examples/demos/a2a_server/` — demo with `demo.sh` and `README.md`
- `examples/demos/a2a_call/` — consumer-side demo (FR-240)
- `feature-requests/FR-208-a2a-graph-support.md` — original A2A FR
- `feature-requests/FR-209-a2a-demo-streaming-response.md` — SSE streaming
- `feature-requests/FR-225-a2a-test-coverage.md` — test coverage
- `feature-requests/FR-240-a2a-call-node-type.md` — consumer node type
- `capabilities/CAP-81-a2a-server.yaml` — capability registration

## Judgement

**Verdict: APPROVE**

### Verification

All factual claims verified against the codebase:
- All 4 source files exist with accurate line counts (±1 line)
- Both demo directories exist
- All 4 referenced FRs exist
- CAP-81 exists
- `parse_a2a_message()` implements exactly 4 parsing modes as described
- `build_agent_card()` exists as claimed
- `reference/mcp-server.md` exists as structural template
- `reference/a2a-server.md` does not exist (gap confirmed)
- `reference/cli.md` exists with zero mentions of `a2a` (gap confirmed)
- 92 A2A test functions across 4 files (far exceeds the "30+" claim)
- FR is purely documentation — no Python code changes

### Assessment

1. **Scope:** Clear and minimal. One reference doc + one CLI doc update. Documentation-only, no code changes.
2. **Contradictions:** None. All claims verified accurate.
3. **Acceptance criteria:** Measurable — each criterion is a file existence or content check.
4. **Feasibility:** High. Source material is comprehensive (4 modules, 92 tests, 2 demos). 1-day estimate is reasonable.
5. **Architecture alignment:** Follows the established `reference/mcp-server.md` pattern exactly.
6. **Single responsibility:** Yes. "Document the A2A server" is one concern. The CLI update is a natural companion (same discoverability problem).

### Amendments applied

- Added acceptance criterion: REQ-YG-245 must be added to `ARCHITECTURE.md` before the doc can reference it. The FR references this requirement but it does not yet exist (REQ-YG-244 is the current highest).

### Authority granted

Scope frozen. Implementer may proceed.
