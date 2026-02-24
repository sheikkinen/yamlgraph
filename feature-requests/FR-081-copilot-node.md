# Feature Request: Copilot Node Type

**Priority:** HIGH
**Type:** Feature
**Status:** Implemented (2026-02-24)
**Effort:** 5 days
**Requested:** 2026-02-24
**FR:** FR-081

## Summary

New `copilot` node type that delegates graph processing to Copilot CLI, replacing the shell-script orchestration pattern used by `watch.sh` and `inquisitor.sh` with a first-class YAML-declarable node. Supports two execution backends: Copilot CLI invocation (warm, with Scripture) and MCP sampling loopback (zero-cost, cold).

## Problem

The `.chaplain/` scripts (`watch.sh`, `inquisitor.sh`) demonstrate a powerful pattern: invoking Copilot CLI to perform reasoning tasks that benefit from full project context (Scripture, file access, MCP tools). However, this pattern lives outside YAMLGraph — it's ad-hoc shell scripting that:

1. **Cannot compose** with other YAMLGraph nodes (LLM, router, map, subgraph)
2. **Cannot participate** in state management, checkpointing, or error handling
3. **Duplicates orchestration logic** that YAMLGraph already provides (looping, routing, interrupts)
4. **Cannot be traced** via LangSmith or standard YAMLGraph observability
5. **Cannot benefit** from FSM-router pattern for multi-phase workflows

The `copilot` CLI with `--allow-all-paths --allow-all-tools -p "prompt"` loads Scripture automatically, giving it deep project understanding that raw LLM calls lack. This is a capability gap: YAMLGraph can call any LLM provider, but cannot call Copilot-as-an-agent.

## Proposed Solution

### Node Type: `copilot`

A new node type in `node_factory/` that invokes Copilot CLI or MCP sampling to delegate reasoning to the host AI assistant.

### YAML Interface

```yaml
metadata:
  name: chaplain-pipeline
  description: Plan-Judge workflow as a YAMLGraph pipeline

nodes:
  plan:
    type: copilot
    prompt: prompts/plan.yaml
    variables:
      topic_file: "{state.inbox_file}"
      output_dir: ".chaplain/drafts"
    backend: cli                    # cli | sampling
    cli_flags:                      # Only for backend: cli
      allow_all_paths: true
      allow_all_tools: true
      model: claude-sonnet-4.6      # Optional model override
    timeout: 600                    # Seconds; default 300
    state_key: plan_result
    on_error: retry

  judge:
    type: copilot
    prompt: prompts/judge.yaml
    variables:
      draft_file: "{state.plan_result.output_path}"
    backend: cli
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
    timeout: 300
    state_key: judgement
    on_error: fail

edges:
  - from: START
    to: plan
  - from: plan
    to: judge
  - from: judge
    to: plan
    condition: "state.judgement.verdict == 'amend'"
  - from: judge
    to: END
    condition: "state.judgement.verdict in ('approve', 'reject')"
```

### Execution Backends

#### Backend 1: `cli` (Recommended, warm context)

Shells out to `copilot` CLI in non-interactive mode. Enhances the proven `watch.sh` pattern by adding `--silent` flag for clean output capture (watch.sh does not use `--silent`; this is an improvement):

```python
# Conceptual implementation
cmd = [
    "copilot",
    "--allow-all-paths",  # If cli_flags.allow_all_paths
    "--allow-all-tools",  # If cli_flags.allow_all_tools
    "--model", model,     # If cli_flags.model specified
    "--silent",           # Always forced — clean output capture
    "-p", rendered_prompt,
]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
```

**Advantages:**
- Copilot loads Scripture (CLAUDE.md, copilot-instructions.md) automatically
- Has access to all configured MCP tools
- Proven pattern from watch.sh / inquisitor.sh
- Model selectable via `--model` flag

**Tradeoffs:**
- Requires `copilot` CLI installed and authenticated
- Process overhead per invocation
- Output is unstructured text (no Pydantic schema enforcement)

**Security:** The CLI backend MUST use list-based `subprocess.run()` (never `shell=True`) so that each argument is passed directly to the process without shell interpretation. This inherently prevents shell injection — no `shlex.quote()` is needed. Note: `yamlgraph/tools/shell.py` uses `shlex.quote()` because it requires `shell=True` for pipe/redirect support in command templates; the copilot node has no such requirement since it always invokes a fixed command with known flags.

#### Backend 2: `sampling` (Zero-cost, MCP loopback)

When YAMLGraph runs as an MCP server (CAP-19), it can call back to the host LLM via `sampling/createMessage`, as proven by `scripts/loopback-poc/`:

```python
# Conceptual implementation (inside MCP tool context)
response = await ctx.session.create_message(
    messages=[SamplingMessage(role="user", content=TextContent(text=rendered_prompt))],
    system_prompt=system_prompt,
    max_tokens=4096,
)
```

**Advantages:**
- Zero API cost (uses host LLM)
- No subprocess overhead
- Structured response possible

**Tradeoffs:**
- Cold LLM (no Scripture context unless injected into system prompt)
- Only works when running inside MCP server context
- Depends on client supporting `sampling/createMessage`

### CLI Flags Mapping

| YAML Key | CLI Flag | Default | Notes |
|----------|----------|---------|-------|
| `allow_all_paths` | `--allow-all-paths` | `false` | Grants file system access |
| `allow_all_tools` | `--allow-all-tools` | `false` | Grants all tool access |
| `model` | `--model` | (omit — uses Copilot default) | Model override |
| — | `--silent` | Always forced | Not user-configurable; required for clean output capture |

### Timeout Configuration

The `timeout` field is added to the copilot node config:

- **Default:** 300 seconds (5 minutes)
- **Configurable:** Per-node via `timeout: <seconds>` in YAML
- **Behavior:** `subprocess.run(..., timeout=timeout)` raises `subprocess.TimeoutExpired`, caught by the node and surfaced as `on_error` handling

### FSM-Router Integration

The copilot node naturally composes with the FSM-router pattern. An FSM can route between YAMLGraph LLM nodes for structured tasks and copilot nodes for open-ended reasoning:

```yaml
nodes:
  classify:
    type: router
    routes:
      structured: analyze      # LLM node — fast, typed output
      creative: brainstorm     # Copilot node — deep, contextual reasoning
      audit: inquisit          # Copilot node — Scripture-aware judgement

  analyze:
    type: llm
    prompt: prompts/analyze.yaml
    schema: { name: Analysis, fields: { ... } }

  brainstorm:
    type: copilot
    prompt: prompts/brainstorm.yaml
    backend: cli

  inquisit:
    type: copilot
    prompt: prompts/inquisit.yaml
    backend: cli
    cli_flags:
      allow_all_paths: true
```

### Output Handling

Since Copilot CLI returns unstructured text, the node wraps output in a structured envelope:

```python
class CopilotResult(BaseModel):
    output: str          # Raw Copilot response text
    exit_code: int       # Process exit code (cli backend)
    model: str | None    # Model used (if reported)
    backend: str         # "cli" or "sampling"
```

For `sampling` backend, if a `schema` is specified in the prompt YAML, structured extraction applies as with normal LLM nodes.

### Config Model Approach: Option A (Extend NodeConfig)

**Decision:** Add `backend`, `cli_flags`, and `timeout` fields to the existing `NodeConfig` class in `yamlgraph/models/graph_schema.py`.

**Justification:** The existing pattern uses a single `NodeConfig` for all node types (llm, router, tool, agent, python, map, tool_call, interrupt, passthrough). The sole exception is `SubgraphNodeConfig`, which exists because subgraph config is *fundamentally different* (input/output mappings, nested node definitions). Copilot's `cli_flags` dict and `backend` string are structurally similar to existing `NodeConfig` fields like `variables` (dict) and `provider` (string). Creating a separate class would break the established pattern without sufficient justification.

New fields on `NodeConfig`:

```python
backend: str | None = None          # "cli" or "sampling"; copilot nodes only
cli_flags: dict[str, Any] | None = None  # CLI flags; copilot nodes only
timeout: int | None = None          # Timeout in seconds; copilot nodes only
```

## Implementation Approach

### File Changes

| File | Change |
|------|--------|
| `yamlgraph/constants.py` | Add `COPILOT = "copilot"` to `NodeType` enum |
| `yamlgraph/node_factory/copilot_node.py` | New — `create_copilot_node()` factory |
| `yamlgraph/node_factory/__init__.py` | Re-export `create_copilot_node` |
| `yamlgraph/node_compiler.py` | Add `elif node_type == NodeType.COPILOT` to dispatch chain (~line 127) |
| `yamlgraph/models/graph_schema.py` | Add `backend`, `cli_flags`, `timeout` fields to `NodeConfig` |
| `yamlgraph/models/schemas.py` | Add `CopilotResult` model |
| `yamlgraph/models/state_builder.py` | No change — already generic via `state_key` |
| `scripts/req_coverage.py` | Add REQ-YG-087–089 to `ALL_REQS`; add CAP-30 to `CAPABILITIES` |
| `ARCHITECTURE.md` | Add REQ-YG-087–089 requirement definitions |
| `reference/graph-yaml.md` | Document copilot node type |
| `examples/demos/copilot-node/` | Demo graph showing Plan-Judge pattern |

### Implementation Steps

1. **Red:** Write unit tests for `create_copilot_node()` with mocked `subprocess.run`. Tag with `@pytest.mark.req("REQ-YG-087")`.
2. **Green:** Implement `copilot_node.py` — CLI backend first (proven pattern). Add `COPILOT` to `NodeType` enum in `constants.py`. Add fields to `NodeConfig`. Wire dispatch in `node_compiler.py`.
3. **Red:** Write integration test for sampling backend (requires MCP context mock). Tag with `@pytest.mark.req("REQ-YG-088")`.
4. **Green:** Implement sampling backend in same factory.
5. **Red:** Write composition test (copilot + router). Tag with `@pytest.mark.req("REQ-YG-089")`.
6. **Green:** Verify copilot node works with router, map, and FSM-router patterns.
7. **Refactor:** Extract shared prompt rendering; ensure node follows standard pre-check/loop-protection/resume pattern. Run ruff, vulture, radon.
8. **Demo:** Port `watch.sh` Plan-Judge loop to `examples/demos/copilot-node/graph.yaml`.
9. **Docs:** Update `reference/graph-yaml.md` with copilot node reference.

### Requirements

| ID | Description |
|----|-------------|
| REQ-YG-087 | Copilot node executes via CLI backend with configurable flags and timeout |
| REQ-YG-088 | Copilot node executes via MCP sampling loopback when available |
| REQ-YG-089 | Copilot node composes with router, map, and FSM-router patterns |

### Prior Art

- `yamlgraph/interactive_tool.py` — Config-level node expansion pattern (top-level module, not in `node_factory/`)
- `yamlgraph/tools/shell.py` — `sanitize_variables()` using `shlex.quote()` for shell injection protection
- `yamlgraph/node_factory/agent_node.py` — Agent node factory pattern (closest analogy)

## Acceptance Criteria

- [ ] `COPILOT = "copilot"` added to `NodeType` enum in `yamlgraph/constants.py`
- [ ] `type: copilot` recognized in graph YAML and compiles without error
- [ ] CLI backend invokes `copilot --silent -p "..."` with configured flags
- [ ] CLI backend captures output into `CopilotResult` on `state_key`
- [ ] `timeout` configurable per-node; default 300s; `TimeoutExpired` handled via `on_error`
- [ ] All state variables sanitized via list-based `subprocess.run()` (no `shell=True`); `shlex.quote()` NOT used
- [ ] Sampling backend calls `session.create_message()` when in MCP context
- [ ] Standard node guarantees apply: `requires`, `on_error`, `skip_if_exists`, loop protection
- [ ] `--silent` always forced for CLI backend (not user-configurable)
- [ ] Graceful error with clear message when `copilot` binary is not installed (`FileNotFoundError`)
- [ ] Demo graph replicates watch.sh Plan-Judge workflow
- [ ] Unit tests with mocked subprocess (no real Copilot dependency)
- [ ] Integration test with real Copilot CLI (guarded by env check)
- [ ] `reference/graph-yaml.md` documents copilot node type
- [ ] `req_coverage.py` updated with REQ-YG-087–089 in `ALL_REQS` and CAP-30 in `CAPABILITIES`
- [ ] `ARCHITECTURE.md` updated with REQ-YG-087–089 definitions
- [ ] Tests tagged with `@pytest.mark.req("REQ-YG-087")`, `@pytest.mark.req("REQ-YG-088")`, `@pytest.mark.req("REQ-YG-089")`

## Alternatives Considered

### 1. Shell tool node with `copilot` command
Use existing `type: tool` with `command: "copilot -p '...'"`. Rejected: no structured output handling, prompt rendering is awkward in shell quoting, no sampling backend, no cli_flags abstraction.

### 2. Agent node with MCP tools
Use `type: agent` with Copilot's MCP tools registered. Rejected: agent node uses a raw LLM, not Copilot-the-agent. Loses Scripture context, tool orchestration intelligence, and the ability to compose multi-step reasoning.

### 3. Pure MCP sampling (no CLI backend)
Only support the loopback pattern. Rejected: sampling gives a cold LLM without Scripture. The CLI backend's warm context (loading CLAUDE.md, copilot-instructions.md) is the primary value proposition. Sampling is a useful secondary backend for zero-cost scenarios.

### 4. External process node (generic)
Create a generic `type: external` node that can invoke any CLI tool. Rejected: over-generalizes. Copilot has specific semantics (flags, authentication, Scripture loading) that warrant a dedicated node type. A generic external node could be a future follow-up.

### 5. Separate CopilotNodeConfig class (Option B)
Create a separate config class like `SubgraphNodeConfig`. Rejected: the subgraph exception exists because subgraph config is fundamentally different (input/output mappings, nested node definitions). Copilot's `cli_flags` and `backend` are structurally similar to existing `NodeConfig` fields (`variables`, `provider`). A separate class would break the established single-class pattern without sufficient justification.

## Judgement Amendment Log

**Original Judgement:** 2026-02-24 — AMEND

| # | Issue | Resolution |
|---|-------|------------|
| 1 | REQ ID collision (084–086 taken) | ✅ Allocated REQ-YG-087, 088, 089 |
| 2 | Wrong file references | ✅ Fixed: `graph_schema.py`, `node_compiler.py:32`, `yamlgraph/interactive_tool.py` |
| 3 | Missing `constants.py` NodeType update | ✅ Added to file changes table and acceptance criteria |
| 4 | Config model pattern unclear | ✅ Decision: Option A — extend existing `NodeConfig` with justification |
| 5 | No security/sanitization criterion | ✅ Added `shlex.quote()` criterion and security section in CLI backend |
| 6 | CLI flags mapping incomplete | ✅ Added full mapping table with `--silent` always-forced policy |
| 7 | Timeout not addressed | ✅ Added `timeout` field with default 300s, configurable per-node |
| 8 | `-s` flag not from watch.sh | ✅ Noted as enhancement over watch.sh pattern |

**Final Judgement:** 2026-02-24 — APPROVE

| # | Issue | Resolution |
|---|-------|------------|
| 9 | CAP-29 reuse: previously "Incaller Voice Demo" (removed/relocated), reuse creates traceability confusion | ✅ Changed to CAP-30 |
| 10 | Security model contradiction: FR prescribed `shlex.quote()` (from shell.py pattern) but conceptual code uses list-based `subprocess.run()` where quoting is unnecessary and harmful. shell.py needs `shlex.quote()` because it uses `shell=True`; copilot node does not. | ✅ Clarified: list-based `subprocess.run()` IS the injection protection. Removed `shlex.quote()` requirement. |
| 11 | Missing CLI availability check: no criterion for graceful `FileNotFoundError` handling | ✅ Added acceptance criterion |

## Related

- `.chaplain/watch.sh` — Plan-Judge loop using Copilot CLI (the pattern to formalize)
- `.chaplain/inquisitor.sh` — Audit loop using Copilot CLI
- `scripts/loopback-poc/` — MCP sampling proof-of-concept
- `feature-requests/054-copilot-cli-reflection.md` — Copilot CLI reflection after diary digest (overlapping pattern)
- `feature-requests/045a-a2a-provider.md` — A2A protocol provider (related agent-to-agent pattern)
- `examples/fsm-router/` — FSM-router pattern for state-based routing
- `yamlgraph/interactive_tool.py` — Prior art: config-level node expansion pattern
- CAP-19 / REQ-YG-066–068 — MCP server interface

## Implementation Notes

**Implemented:** 2026-02-24

| File | Change |
|------|--------|
| `yamlgraph/constants.py` | Added `COPILOT = "copilot"` to NodeType enum |
| `yamlgraph/models/graph_schema.py` | Extended NodeConfig with `backend`, `cli_flags`, `timeout` fields |
| `yamlgraph/models/schemas.py` | Added CopilotResult model |
| `yamlgraph/node_factory/copilot_node.py` | New file - create_copilot_node factory (276 lines) |
| `yamlgraph/node_factory/__init__.py` | Export create_copilot_node |
| `yamlgraph/node_compiler.py` | Added dispatch for NodeType.COPILOT |
| `tests/unit/test_copilot_node.py` | 11 tests covering REQ-YG-087, REQ-YG-089 |
| `tests/unit/test_constants.py` | Added 'copilot' to expected node types |
| `ARCHITECTURE.md` | Added CAP-30 and REQ-YG-087–089 |
| `scripts/req_coverage.py` | Updated with new requirements |

**Deferred:**
- REQ-YG-088 (MCP sampling backend) raises `NotImplementedError` - requires MCP loopback infrastructure
