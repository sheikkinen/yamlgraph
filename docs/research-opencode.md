# Research: opencode vs / with YAMLGraph

*Date: 2026-06-20*

## What is opencode?

[opencode](https://opencode.ai/) is an open source AI coding agent, available as a terminal UI,
desktop app, and IDE extension. Source lives at
[github.com/anomalyco/opencode](https://github.com/anomalyco/opencode) (recently moved from
`sst/opencode`).

- **License:** MIT — fully open, genuinely self-hostable, not a thin client over a hosted service.
- **Scale:** ~176k GitHub stars, 944 contributors, 825 releases (v1.17.8 at time of writing),
  daily commits. Used by ~7.5M devs/month per the project.
- **Stack:** TypeScript / Bun. ~69% TypeScript, ~27% MDX (docs).
- **Privacy posture:** Stores no code or context server-side; designed for privacy-sensitive
  environments.
- **Provider-agnostic:** 75+ LLM providers via Models.dev, including GitHub Copilot login,
  ChatGPT Plus/Pro login, and local models.

The architecture is the important part: running `opencode` starts **a TUI client + a server**. The
server exposes an **OpenAPI 3.1 spec** (`/doc`), from which a type-safe SDK is generated. The TUI is
just one client. This is what makes opencode programmatically drivable.

## Capabilities relevant to integration

| Capability | Detail |
|---|---|
| Headless server | `opencode serve [--port] [--hostname] [--cors]`; OpenAPI spec at `/doc`; optional HTTP basic auth via `OPENCODE_SERVER_PASSWORD` |
| Type-safe SDK | `@opencode-ai/sdk`: `createOpencode()` (spawns server+client) or `createOpencodeClient({ baseUrl })` (connect to existing) |
| Sessions | create / `prompt` (sync) / `prompt_async` (204, no wait) / `command` (slash) / `shell` / `fork` / `revert` / `unrevert` / `abort` / `summarize` |
| Structured output | `format: { type: "json_schema", schema, retryCount }`; returns validated JSON or a `StructuredOutputError` after retries |
| Events | SSE stream at `/event`: `session.idle`, `session.error`, `tool.execute.before/after`, `permission.asked/replied`, `file.edited`, `message.*` |
| Agents | JSON (`opencode.json`) or markdown (`.opencode/agents/*.md`); per-agent `model`, `prompt`, `temperature`, `steps`, `permission`, `mode` (primary/subagent), task-permissions for subagent invocation |
| Plugins | TS/JS modules in `.opencode/plugins/`; hooks incl. `tool.execute.before/after`, `shell.env`, `experimental.session.compacting`, event subscription; receive an SDK `client` + Bun `$` shell |
| Custom tools | TS definition (`tool()` helper, Zod args) that may shell to **any language** (e.g. Python via `Bun.$`) |
| Permissions | per-tool and per-bash-glob `allow` / `ask` / `deny`; `external_directory` gate; wildcard patterns over built-in, custom, and MCP tools |
| MCP | consumes MCP servers; can add them dynamically via `POST /mcp` |

## Comparison with YAMLGraph

| Dimension | opencode | YAMLGraph |
|---|---|---|
| **Kind** | An agent (runtime + UI) you talk to | A framework for declaring LLM pipelines |
| **Language** | TypeScript / Bun | Python |
| **Unit of work** | A session (conversation with tools) | A compiled graph (nodes + edges + state) |
| **Extension model** | Agents (md/json), plugins (TS hooks), custom tools (TS) | Node types, YAML graphs/prompts, Python tools |
| **Structured output** | `json_schema` with retry | Pydantic v2 / inline YAML schemas |
| **Governance** | Permissions + plugin hooks | Scripture + Chaplain pipeline (FR/CAP/REQ/test/precommit) |
| **Observability** | SSE event stream + share links | LangSmith tracing |
| **Orchestration** | Implicit (the agent decides) | Explicit (the graph declares) |

These are **not** the same category. opencode is a coding *agent*; YAMLGraph is a pipeline
*framework* that today already shells out to a coding agent (the GitHub Copilot CLI) from its
`copilot` node. opencode is a candidate **backend** for that node, and separately a candidate
**host** for chaplain doctrine.

## The existing seam

YAMLGraph's chaplain already drives a coding agent as a subprocess:

- `yamlgraph/node_factory/copilot_node.py` dispatches on `backend ∈ {cli, api, sampling}`.
- `yamlgraph/node_factory/copilot_runtime.py::_execute_cli` runs `copilot --silent ... -p <prompt>`,
  extracts a session id from the `--share` file for resume, and wraps the text output in a
  `CopilotResult` Pydantic model.

This is the precise place an opencode integration would attach.

## Options

### Direction A — opencode as a copilot-node backend (high fit, low effort)

Add `backend: "opencode"` to the copilot node (alongside `cli` / `api`), driving `opencode serve`
over its HTTP/SDK surface instead of `copilot --silent`. Gains over the raw Copilot CLI:

- **Structured output with retries** (`json_schema`) instead of parsing free text in judge/enforce.
- **SSE event stream** → the watcher can observe `tool.execute.before` (enforce gates live) and
  `session.idle` (completion) rather than blocking on a subprocess.
- **Permissions** → `deny git push`, restrict bash globs during enforce — a real sandbox the
  Copilot CLI does not provide.
- **Session `fork` / `revert`** → cleaner retry semantics than re-running from scratch.

Contained to the node layer; reuses the existing `CopilotResult` contract (extended with a
structured-output field). **This FR: FR-546.**

### Direction B — chaplain doctrine as opencode plugins/tools/agents (medium-high fit, more work)

Re-home the governance so it runs *inside* opencode for anyone, not just yamlgraph:

- **Custom tools** (TS shims → existing Python: `req_coverage.py`, `aggregate_changelog.py`,
  FR/CAP lookups).
- **Plugin hooks as gates:** `tool.execute.before` on `bash` to block `--no-verify` / multiline
  `git commit -m` (logic already in `.github/hooks/pre-command-guard.sh`); `session.idle` to require
  a diary entry / changelog fragment before "done".
- **Agents** (`plan.md`, `judge.md`, `enforce.md`) encoding the Sermon with read-only vs full-access
  permissions — mirrors opencode's own Build/Plan split.

This effectively ports `.github/hooks/` enforcement and `.chaplain/graphs/` orchestration onto
opencode's native extension points.

### Direction C — expose YAMLGraph graphs to opencode via MCP (already partly built)

YAMLGraph already ships an MCP server (`yamlgraph/mcp_server.py`, CAP-19) that exposes graphs as
tools. opencode consumes MCP servers. So opencode could call YAMLGraph graphs as tools today with no
new YAMLGraph code — only opencode-side config. Lowest effort, but it is the *inverse* of the
chaplain use case (opencode orchestrates yamlgraph, not yamlgraph orchestrating the agent).

## The honest caveats

1. **Runtime split.** opencode is TypeScript/Bun; YAMLGraph is Python. Directions B and C-authoring
   require a Bun/TS surface in a Python-governed repo. Direction A avoids this — it talks to
   `opencode serve` over HTTP from Python, no TS authoring required.
2. **Two governance homes.** Direction B would split enforcement between Python (Scripture,
   import-linter, pre-commit) and TS (opencode plugins), creating drift risk between two sources of
   the same rules.
3. **Velocity / churn.** Org rename + 825 releases signals fast movement. The SDK/server surface is
   OpenAPI-generated and relatively stable, but agent/plugin schemas still carry `experimental.*`
   and `deprecated` fields (`maxSteps` → `steps`, `tools` → `permission`).

## Recommendation

Pursue **Direction A first** — it is the natural extension of the seam that already exists, it is
contained to the copilot node, and it buys structured output + permissions + live events with no
second governance home and no TS authoring. Treat **Direction B** as a separate, later question:
worth it only to make chaplain doctrine usable *outside* yamlgraph, and only after accepting a
Bun/TS surface. **Direction C** is essentially free and orthogonal — note it, but it does not serve
the chaplain-as-orchestrator goal.

Minimal Direction-A proof: stand up `opencode serve`, drive one enforce cycle via HTTP with a
`json_schema` judge verdict, and compare resume/observability against the current `copilot --silent`
path.

## Related

- `yamlgraph/node_factory/copilot_node.py` — backend dispatch (`cli` / `api` / `sampling`)
- `yamlgraph/node_factory/copilot_runtime.py` — `_execute_cli` seam
- `yamlgraph/models/schemas.py` — `CopilotResult`
- `yamlgraph/mcp_server.py` — MCP server (CAP-19), relevant to Direction C
- `feature-requests/FR-546-opencode-copilot-backend.md` — Direction A
- opencode docs: [SDK](https://opencode.ai/docs/sdk/), [Server](https://opencode.ai/docs/server/),
  [Agents](https://opencode.ai/docs/agents/), [Plugins](https://opencode.ai/docs/plugins/),
  [Custom Tools](https://opencode.ai/docs/custom-tools/)
