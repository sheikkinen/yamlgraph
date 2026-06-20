# Feature Request: opencode Backend for the Copilot Node

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged (scope frozen 2026-06-20) — authority granted to enforce
**Effort:** ~2-3 days
**Requested:** 2026-06-20

## Judgement (2026-06-20)

Scope frozen after two blocking defects in the Proposed draft were resolved:

1. **`httpx` is not a core dependency.** It appears only in the `booking`/`digest` optional
   extras in `pyproject.toml` — a clean `pip install yamlgraph` does not have it. **Resolution:**
   declare an `opencode = ["httpx>=0.27.0"]` optional extra and raise an install-hint error when
   the import is missing (mirrors the `FileNotFoundError` copilot-binary pattern). No new core dep.
2. **opencode has no per-message `permission` field.** `POST /session/:id/message` accepts
   `{ model, agent, noReply, system, tools, parts }` only; permissions live in agent config
   (`.opencode/agents/*.md`). The original per-node `permission:` block was both unsupported and
   redundant with the named `agent:`. **Resolution:** permissions are owned by a pre-defined
   opencode agent; the node references it via `agent:` and carries **no** `permission:` block.

Minor refinements folded: resume maps to reusing `CopilotResult.session_id` (not a `--resume`
flag); `CopilotResult.backend` docstring extended to include `'opencode'`.

3. **SSE observability was over-claimed.** The Proposed draft sold a "live event stream for the
   watcher" as a third benefit, but the design uses the **synchronous** `POST /session/:id/message`
   (the node still blocks on one HTTP call) and nothing subscribes to `GET /event`. **Resolution:**
   the event-stream/observability story is demoted to a non-goal (future FR alongside the call-site
   migration). This FR delivers exactly two benefits over `copilot --silent`: structured output and
   agent-owned permission sandboxing.

## Summary

Add `backend: "opencode"` to the copilot node, alongside the existing `cli` / `api` / `sampling`
backends. The new backend drives a headless [`opencode serve`](https://opencode.ai/docs/server/)
instance over its HTTP/SDK surface instead of shelling out to `copilot --silent`. This is contained
to the node layer and reuses the existing `CopilotResult` contract (extended with an optional
structured-output field). It buys two things the GitHub Copilot CLI cannot give the chaplain:
**structured (json_schema) output with retries** and **agent-owned permission sandboxing** (the node
names an opencode agent whose markdown config carries the permissions). A live SSE event stream for
watcher observability is available on the same server but is **out of scope** here (see Scope
Boundary) — this FR keeps the node's synchronous request/response shape.

See `docs/research-opencode.md` for the full investigation and the alternative directions (B:
doctrine-as-plugins, C: graphs-as-MCP-tools) that this FR deliberately does **not** pursue.

## Value Statement

Chaplain pipeline authors get a coding-agent backend whose verdicts are schema-validated (no free-text
parsing in judge/enforce) and whose filesystem/shell access is permission-gated during enforce (via a
referenced opencode agent) — without introducing a TypeScript toolchain into the Python repo.

## Problem

The chaplain drives a coding agent today via `yamlgraph/node_factory/copilot_runtime.py::_execute_cli`,
which runs `copilot --silent ... -p <prompt>` and wraps the raw stdout text in a `CopilotResult`. Three
structural limits follow from that seam:

1. **Unstructured output.** The judge and enforce steps parse free text. There is no schema contract,
   so a plausibly-shaped-but-wrong verdict is hard to catch (the `plausible_wrong_answer` trap).
2. **No sandbox.** The CLI runs with `--allow-all-tools` / `--allow-all-paths`. The enforce agent can
   `git push`, write outside the worktree, or run arbitrary bash with no per-action gate. The repo's
   own Scripture forbids `--no-verify` and force-push, but the runtime cannot *enforce* that on the
   agent — only the post-command hooks can, after the fact.
3. **Blocking opacity.** `_execute_cli` is a blocking `subprocess.run` with a timeout. The watcher
   cannot observe tool calls or completion mid-flight; it only sees the final exit code and text.

opencode addresses the first two natively: `json_schema` output format with `retryCount`, and
per-tool / per-bash-glob permissions (carried by the named agent). The third (mid-flight
observability via the `/event` SSE stream) is a separate, later concern — this FR keeps the node
synchronous and does not consume events (see Scope Boundary).

## Proposed Solution

Add an `opencode` backend that talks to `opencode serve` over HTTP from Python (no TS authoring).

### Graph YAML

```yaml
nodes:
  judge:
    type: copilot
    backend: opencode          # new
    state_key: judgement
    prompt: judge
    opencode:                  # backend-scoped config block
      base_url: http://127.0.0.1:4096   # connect to an existing server
      # or: serve: true                  # spawn `opencode serve` for this node
      agent: judge                        # opencode agent (.opencode/agents/judge.md)
                                          #   — the agent's markdown OWNS the permissions
                                          #     (edit/bash gates); the node does not set them
      model: anthropic/claude-sonnet-4    # provider/model-id form (overrides agent default)
      output_format: json_schema          # request structured output
      timeout: 600
    output_model: yamlgraph.models.JudgeVerdict   # drives the json_schema
```

The permission sandbox is defined once, in the agent markdown the node references — e.g.
`.opencode/agents/judge.md`:

```markdown
---
description: Chaplain judge — read-only verdict, no edits, no push
mode: subagent
permission:
  edit: deny
  bash:
    "*": deny
    "git diff": allow
    "git log*": allow
    "grep *": allow
---
You are the Chaplain's judge. ...
```

This keeps permissions in opencode's native, supported location and avoids a per-message field
that the server API does not accept.

### Execution path

- New `yamlgraph/node_factory/opencode_runtime.py::_execute_opencode(...)` mirroring `_execute_cli`'s
  signature and return shape (`{state_key: CopilotResult, "current_step": node_name}`).
- Dispatch added in `copilot_node.py` (`if backend == "opencode": return _execute_opencode(...)`).
- HTTP client is a thin Python wrapper over the documented REST endpoints (`POST /session`,
  `POST /session/:id/message` with `format: json_schema` and `agent: <name>`, `POST
  /session/:id/abort`). The request body uses only documented fields
  (`{ model, agent, noReply, system, tools, parts, format }`) — there is **no** per-message
  permission field; permissions come from the named agent.
- **Dependency.** `httpx` is **not** a core yamlgraph dependency (it lives only in the
  `booking`/`digest` extras). Add an `opencode = ["httpx>=0.27.0"]` optional extra in
  `pyproject.toml`. `_execute_opencode` imports `httpx` lazily and, on `ImportError`, raises a
  `RuntimeError` with an install hint (`pip install "yamlgraph[opencode]"`) — mirroring the
  `FileNotFoundError` copilot-binary guard in `_execute_cli`.
- `CopilotResult` gains an optional `structured_output: dict | None` field; when `output_format:
  json_schema` and an `output_model` is set, the dict is validated through that Pydantic model and a
  `StructuredOutputError` from opencode maps to a `PipelineError` (`VALIDATION_ERROR`, non-retryable).
- Server lifecycle: `serve: true` spawns `opencode serve --port <p> --hostname 127.0.0.1` and tears it
  down in a `finally` (mirroring the `_execute_cli` `share_tmpdir` cleanup); `base_url` connects to an
  already-running instance and does **not** manage its lifecycle.
- Session resume: opencode resume is *not* a `--resume <id>` flag — it is posting a new message
  into an existing session id. Map `resume` / `continue_session` to **reusing**
  `CopilotResult.session_id` (skip `POST /session`, post directly to `/session/:id/message`).
- `CopilotResult.backend` docstring/enum is extended from `'cli' | 'api' | 'sampling'` to include
  `'opencode'`.

### Linter

Extend `yamlgraph/linter/patterns/copilot.py`:

- `E-COPILOT-OPENCODE-TARGET`: `backend: opencode` requires exactly one of `opencode.base_url` or
  `opencode.serve`.
- `W-COPILOT-OPENCODE-SCHEMA`: `output_format: json_schema` without an `output_model` is a warning
  (falls back to text).
- `E-COPILOT-OPENCODE-PERMISSION`: a per-node `opencode.permission` block is rejected — permissions
  belong in the referenced agent's markdown, not the graph node (guards against the unsupported
  per-message field re-appearing).

## Acceptance Criteria

- [ ] `backend: opencode` dispatches to `_execute_opencode` and returns a `CopilotResult`.
- [ ] `output_format: json_schema` with an `output_model` populates `CopilotResult.structured_output`,
      validated through the Pydantic model.
- [ ] An opencode `StructuredOutputError` (post-retry) surfaces as a `PipelineError`
      (`VALIDATION_ERROR`, `retryable=False`), not a crash.
- [ ] The node forwards `agent:` to `POST /session/:id/message`; an integration test using a
      `deny`-permissioned agent asserts a denied `bash` command is refused by the agent.
- [ ] A per-node `opencode.permission` block fails the linter (`E-COPILOT-OPENCODE-PERMISSION`);
      permissions are sourced only from the referenced agent's markdown.
- [ ] Missing `httpx` raises a `RuntimeError` with the `pip install "yamlgraph[opencode]"` hint
      (unit test patches the import).
- [ ] `serve: true` spawns and tears down `opencode serve`; `base_url` connects without managing
      lifecycle. Teardown runs on timeout and on exception.
- [ ] Timeout maps to `POST /session/:id/abort` then a `PipelineError` (mirrors `_execute_cli`
      timeout behaviour).
- [ ] Linter checks `E-COPILOT-OPENCODE-TARGET`, `W-COPILOT-OPENCODE-SCHEMA`, and
      `E-COPILOT-OPENCODE-PERMISSION` added with tests.
- [ ] `opencode = ["httpx>=0.27.0"]` optional extra added to `pyproject.toml`.
- [ ] New capability `capabilities/CAP-XXX-opencode-copilot-backend.yaml` with `REQ-YG-XXX`; all new
      tests tagged `@pytest.mark.req(...)`.
- [ ] Unit tests mock the HTTP layer (no live server); one `@pytest.mark.slow` integration test guarded
      by an `opencode` binary / `OPENCODE_BASE_URL` presence check.
- [ ] Changelog fragment in `changelog/unreleased/`.
- [ ] `docs/research-opencode.md` referenced; copilot-node reference doc updated with the backend.

## Test Plan (TDD)

1. **RED** — `tests/unit/test_copilot_opencode_backend.py`: assert dispatch to `_execute_opencode`,
   json_schema → `structured_output`, `StructuredOutputError` → `PipelineError`, timeout → abort+error.
   Commit RED with `SKIP=pytest`.
2. **GREEN** — implement `opencode_runtime.py` + dispatch + schema field; mock `httpx`.
3. **Linter** — RED then GREEN for the three new codes.
4. **Integration** (`@pytest.mark.slow`) — against a real `opencode serve`, run one judge cycle with a
   `JudgeVerdict` schema and assert a denied bash command is refused.

## Scope Boundary

**In scope:** the `opencode` backend for the copilot node — execution, structured output,
agent-referenced permission sandboxing, server lifecycle, resume, linter, the `opencode` optional
extra, capability + tests.

**Out of scope (deliberately):**
- **Direction B** — porting chaplain doctrine (`.github/hooks/`, `.chaplain/graphs/`) to opencode
  plugins/agents. Separate FR; introduces a TS/Bun governance home.
- **Direction C** — exposing YAMLGraph graphs to opencode via the existing MCP server (CAP-19). Already
  largely works; opencode-side config only; orthogonal to chaplain-as-orchestrator.
- Migrating the existing `cli` backend or the chaplain graphs to opencode. This FR only *adds* a
  backend; switching call sites is a follow-up once the backend is proven.
- Authoring or shipping the opencode agent markdown files (e.g. `.opencode/agents/judge.md`). The
  backend *references* an agent by name; defining the chaplain's agent roster is a follow-up that
  belongs with the call-site migration.
- **SSE event-stream observability.** Subscribing to `GET /event` (`tool.execute.*`, `session.idle`)
  to give the watcher mid-flight visibility. The node stays synchronous (`POST /session/:id/message`,
  wait-for-response) here; live observability is a separate FR alongside the call-site migration.

## Alternatives Considered

- **Keep `copilot --silent`.** Status quo; no structured output, no sandbox, no events. Rejected — those
  three gaps are exactly the chaplain's pain points.
- **Use opencode only via MCP (Direction C).** Inverts the relationship (opencode orchestrates
  yamlgraph). Does not serve chaplain-as-orchestrator. Noted as free/orthogonal, not a substitute.
- **Author opencode plugins in TS (Direction B).** Higher ceiling but adds a Bun/TS toolchain and a
  second enforcement home. Deferred to its own FR.
- **`createOpencode()` Node SDK as a subprocess.** Would require Node in the loop; the HTTP/REST surface
  is equivalent and stays Python-only. Rejected for the runtime-split reason.

## Related

- `docs/research-opencode.md` — investigation + options A/B/C
- `yamlgraph/node_factory/copilot_node.py` — backend dispatch
- `yamlgraph/node_factory/copilot_runtime.py` — `_execute_cli` seam to mirror
- `yamlgraph/node_factory/opencode_runtime.py` — **new**
- `yamlgraph/models/schemas.py` — `CopilotResult` (+ `structured_output`)
- `yamlgraph/linter/patterns/copilot.py` — new lint codes
- opencode: [Server](https://opencode.ai/docs/server/), [SDK](https://opencode.ai/docs/sdk/),
  [Agents](https://opencode.ai/docs/agents/), [Permissions](https://opencode.ai/docs/permissions/)
