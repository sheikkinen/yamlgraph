# CLI Reference

Complete command reference for the `yamlgraph` CLI.

## Commands Overview

```
yamlgraph [-h] {graph,schema,skill,diary,a2a} ...
```

| Command | Description |
|---------|-------------|
| `graph` | Run graphs, list, validate, lint, generate diagrams |
| `schema` | Export bundled JSON schema and print schema path |
| `skill` | Export graphs as portable skill packages |
| `diary` | Import pending diary insights |
| `a2a` | A2A protocol server: serve graphs as agents, print Agent Cards |

---

## yamlgraph graph

The primary command for running and managing graphs.

```
yamlgraph graph {run,info,validate,lint,codegen,bench,export} ...
```

### graph run

Run a graph with input variables.

```bash
yamlgraph graph run <graph_path> [options]
```

**Arguments:**
- `graph_path` - Path to graph YAML file

**Options:**
| Flag | Short | Description |
|------|-------|-------------|
| `--var VAR` | `-v` | Set state variable (key=value), repeatable |
| `--thread THREAD` | `-t` | Thread ID for state persistence |
| `--export` | `-e` | Export results to files |
| `--full` | `-f` | Show full output without truncation |
| `--json` | | Emit final graph state as JSON-only stdout (machine-readable mode) |
| `--async` | `-a` | Use async execution for parallel map nodes |
| `--share-trace` | | Share LangSmith trace publicly and display the URL |

**Examples:**
```bash
# Basic run with variables
yamlgraph graph run examples/demos/yamlgraph/graph.yaml -v topic=AI -v style=casual

# Parallel map execution (recommended for Mistral provider)
yamlgraph graph run examples/demos/map/graph.yaml -v topic=AI --async

# With thread ID for resumable sessions
yamlgraph graph run examples/demos/interview/graph.yaml -t session-123

# Full output for debugging
yamlgraph graph run examples/demos/reflexion/graph.yaml -v topic="climate" -f

# Machine-readable JSON stdout (no human headers)
yamlgraph graph run examples/demos/typescript-node/graph.yaml \
  --json -v name=World -v style=formal

# Export results
yamlgraph graph run examples/demos/git-report/graph.yaml -v input="What changed?" -e

# Show LangSmith trace URL (requires LANGCHAIN_TRACING_V2=true + LANGSMITH_API_KEY)
yamlgraph graph run examples/demos/yamlgraph/graph.yaml -v topic=AI
# 🔗 Trace: https://smith.langchain.com/o/.../r/...

# Share trace publicly
yamlgraph graph run examples/demos/yamlgraph/graph.yaml -v topic=AI --share-trace
# 🔗 Trace (public): https://smith.langchain.com/public/.../r/...
```

**Subprocess vs MCP/A2A:** use `graph run --json` for simple request/response subprocess integration (e.g., `child_process.execFile` in Node.js). Prefer MCP/A2A for long-lived agent/tool ecosystems, discovery, and protocol-level interoperability.

### graph info

Show structure and metadata of a graph.

```bash
yamlgraph graph info <graph_path>
```

**Example:**
```bash
yamlgraph graph info examples/demos/router/graph.yaml
```

### graph validate

Validate graph YAML against schema.

```bash
yamlgraph graph validate <graph_paths...>
```

**Example:**
```bash
yamlgraph graph validate examples/demos/*/graph.yaml
```

### graph lint

Lint graph for common issues (missing state keys, unused tools, etc.).

```bash
yamlgraph graph lint <graph_paths...>
```

**Example:**
```bash
yamlgraph graph lint examples/demos/yamlgraph/graph.yaml examples/demos/router/graph.yaml
```

### graph export (FR-723)

Render the **authored** graph as Mermaid (typed nodes, condition labels,
router routes, loop limits, explicit `loop_exit` edges). Pure function of
the YAML — no LLM, no API keys, safe for pre-commit.

```bash
yamlgraph graph export <graph.yaml> --mermaid [-o out.mmd]
```

Overlay an executed route (captured via `YAMLGRAPH_ROUTE_LOG=<path-target>`):
taken edges are highlighted and carry decision ordinals (`#1 #2 …`) so the
ordered route is reconstructible from the render.

```bash
yamlgraph graph export <graph.yaml> --mermaid --overlay route.jsonl
```

Diff two routes, occurrence-aligned per `(node, Nth firing)` — exits 1 on
divergence, so an empty diff is a cheap determinism witness:

```bash
yamlgraph graph export --diff a.route.jsonl b.route.jsonl
```

Path-target examples for route capture:

```bash
# logger only
YAMLGRAPH_ROUTE_LOG=1 yamlgraph graph run <graph.yaml>

# explicit file (parents auto-created)
YAMLGRAPH_ROUTE_LOG=outputs/routes/reflexion.route.jsonl yamlgraph graph run <graph.yaml>

# existing directory target -> writes <dir>/route.jsonl
YAMLGRAPH_ROUTE_LOG=outputs/routes yamlgraph graph run <graph.yaml>

# trailing separator intent -> create dir then write <dir>/route.jsonl
YAMLGRAPH_ROUTE_LOG=outputs/routes/ yamlgraph graph run <graph.yaml>
```

Relative path targets are resolved against the process working directory (CWD at run time).

Route lines are emitted on the `yamlgraph.route` logger — a **public API**
namespace for downstream handlers/filters. See
[graph-yaml.md § Observability](graph-yaml.md#observability-fr-723) for the
line grammar and opt-in surfaces.

---

## yamlgraph a2a

A2A protocol server commands. See [A2A Server Reference](a2a-server.md) for full documentation.

```
yamlgraph a2a {serve,card} ...
```

### a2a serve

Start an A2A HTTP server exposing discovered graphs as agent skills.

```bash
yamlgraph a2a serve <graph_path> [options]
```

**Arguments:**
- `graph_path` — Path to a graph YAML file or directory (optional; defaults to auto-discovery)

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `0.0.0.0` | Server bind address |
| `--port` | `8080` | Server port |

**Examples:**
```bash
# Serve the hello graph
yamlgraph a2a serve examples/demos/hello/ --port 9090

# Serve all discovered graphs
yamlgraph a2a serve
```

### a2a card

Print the Agent Card JSON for discovered graphs without starting the server.

```bash
yamlgraph a2a card <graph_path> [options]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `localhost` | Hostname for Agent Card URL |
| `--port` | `8080` | Port for Agent Card URL |

**Example:**
```bash
yamlgraph a2a card examples/demos/hello/
```

---

## yamlgraph skill

Portable skill packaging commands.

```bash
yamlgraph skill export <graph_path_or_dir> [--format skill-md|copilot|cursor|agent-md] [--output-dir PATH]
```

### skill export

Export a graph into a portable skill bundle with:

- `SKILL.md`
- `scripts/run.sh`
- `references/`
- `assets/schema.json`

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--format` | `skill-md` | Output layout variant: `skill-md`, `copilot`, `cursor`, `agent-md` |
| `--output-dir` | `output` | Base output directory |

**Layout by format:**

| Format | Output path |
|--------|-------------|
| `skill-md` | `<output-dir>/<skill-name>/...` |
| `copilot` | `<output-dir>/.copilot/skills/<skill-name>/...` |
| `cursor` | `<output-dir>/.cursor/skills/<skill-name>/...` |
| `agent-md` | `<output-dir>/.github/agents/<skill-name>.agent.md` |

**Examples:**

```bash
# Standard package layout
yamlgraph skill export examples/demos/hello/graph.yaml --format skill-md

# Copilot-compatible skills directory
yamlgraph skill export examples/demos/hello/graph.yaml --format copilot --output-dir .

# Cursor-compatible skills directory
yamlgraph skill export examples/demos/hello/graph.yaml --format cursor --output-dir .

# Copilot agent mode file constrained to YAMLGraph MCP tools
yamlgraph skill export examples/demos/hello/graph.yaml --format agent-md --output-dir .
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic Claude API key |
| `MISTRAL_API_KEY` | Mistral API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `PROVIDER` | Default LLM provider (`anthropic`, `mistral`, `openai`) |
| `YAMLGRAPH_ROUTE_LOG` | Route decision log opt-in (FR-723/FR-752): `1` = logger only; path target = append raw JSONL (`<file>` or `<dir>/route.jsonl`), parent dirs auto-created, relative targets CWD-relative |
| `LANGSMITH_API_KEY` | LangSmith tracing key |
| `LANGSMITH_PROJECT` | LangSmith project name |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
