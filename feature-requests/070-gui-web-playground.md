# Feature Request: FR-070 Web Playground (`yamlgraph serve`)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Rejected
**Effort:** 4 days
**Requested:** 2026-02-21
**Judged:** 2026-02-21

## Rejection Rationale

**Contradicts graduated doctrine.** From diary entry "Correction: The Visual Tooling Trap":

> - YAMLGraph is AI-editable by design
> - **No UI, ever**
> - Text is the interface
> - Agents read YAML, agents write YAML
> - Visual tools create a human dependency that YAML eliminates

**Heuristic:** *When tempted to visualize, simplify instead. YAML that needs a diagram is YAML that needs refactoring.*

### Valid Problems, Better Solutions

| Problem | GUI Solution (rejected) | CLI Solution (preferred) |
|---------|------------------------|--------------------------|
| Graph discovery | Web list | `yamlgraph graph list --with-vars` |
| Variable discovery | Form fields | `yamlgraph graph info --detailed` |
| Quick experiments | Browser interface | `yamlgraph graph run --interactive` |
| Stakeholder demos | Web playground | LangSmith trace URLs, `asciinema` recordings |

**Recommendation:** Create FRs for CLI improvements instead.

---

## Original Proposal (for reference)

## Summary

Add a `yamlgraph serve` CLI command that launches a lightweight web-based playground for
exploring and running YAMLGraph pipelines. The UI lists discovered graphs, renders their
topology as a Mermaid diagram (via LangGraph's built-in `get_graph().draw_mermaid()`),
provides a variable-input form, and streams execution output — all without leaving the browser.

## Problem

Today, running a graph requires CLI fluency: you must know the file path, remember required
`--var` names, and parse terminal output. There is no visual way to:

- **Discover** what graphs exist and what variables they accept.
- **Understand** a pipeline's topology before running it.
- **Experiment** quickly (adjust vars, re-run, compare outputs).
- **Demo** YAMLGraph to stakeholders who are not comfortable with terminals.

The MCP server exposes graphs to Copilot/Claude, and the CLI handles scripted use — but
neither covers interactive, human-facing exploration. Example FastAPI apps
(`examples/booking/`, `examples/daily_digest/`) address this per-project, but there is no
reusable, zero-config playground for any graph.

## Proposed Solution

### CLI entry point

```bash
# Serve all graphs under examples/demos (default pattern)
yamlgraph serve

# Custom graph glob and port
yamlgraph serve --graphs "projects/**/*.yaml" --port 8080

# Open browser automatically
yamlgraph serve --open
```

### UI layout

```
┌─────────────────────────────────────────────────────────┐
│  YAMLGraph Playground                                   │
├──────────────┬──────────────────────────────────────────┤
│  Graph list  │  [hello]  Topology (Mermaid)             │
│  • hello     │  ┌──────────────────────────────────┐    │
│  • router    │  │  START → greet → END             │    │
│  • showcase  │  └──────────────────────────────────┘    │
│              │                                          │
│              │  Variables                               │
│              │  name: [_____________]                   │
│              │  style: [_____________]                  │
│              │                                          │
│              │  [▶ Run]                                 │
│              │                                          │
│              │  Output (streaming)                      │
│              │  ┌──────────────────────────────────┐    │
│              │  │  Hello, World! ...                │    │
│              │  └──────────────────────────────────┘    │
└──────────────┴──────────────────────────────────────────┘
```

### Implementation approach

1. **FastAPI backend** (reuses existing pattern from `examples/`):
   - `GET /api/graphs` — list discovered graphs (name, path, description, required vars).
   - `GET /api/graphs/{id}/diagram` — return Mermaid markup via
     `compile_graph(config).compile().get_graph().draw_mermaid()`.
   - `POST /api/graphs/{id}/run` — accept `{"vars": {...}}`, stream SSE tokens from
     `run_graph_streaming_native()` in `yamlgraph/executor_async.py`.

2. **Single-page frontend** (plain HTML + vanilla JS, zero build step):
   - Served as a static `index.html` embedded in the package (`yamlgraph/web/`).
   - Mermaid.js loaded from CDN for diagram rendering.
   - `EventSource` for SSE streaming output.

3. **Graph discovery** — reuses the same glob logic as `mcp_server.py` (no duplication).

4. **Mermaid generation** — uses LangGraph's built-in
   `compile_graph(config).compile().get_graph().draw_mermaid()`. No custom traversal code. A thin
   `graph_to_mermaid(config: GraphConfig) -> str` wrapper compiles the graph and delegates to
   LangGraph. **Rationale:** Option A (LangGraph built-in) is chosen over Option B (custom
   YAML-level traversal) because it is always accurate, requires zero new traversal code, and
   a `cli/__pycache__/graph_mermaid.cpython-313.pyc` artifact from a prior deleted
   implementation confirms the custom approach was already abandoned. If map subgraphs render
   poorly in practice, Option B can be revisited in a follow-up FR with benchmark evidence.

5. **Variable introspection** — extract the `required_vars` logic currently in
   `discover_graphs()` (`yamlgraph/mcp_server.py`) into a shared helper
   `yamlgraph/utils/graph_introspection.py`. Both `mcp_server.py` and the playground backend
   import from there. No parallel implementations.

6. **Optional extra guard** — all `fastapi`/`uvicorn` imports in `yamlgraph/web/` and the
   `serve` command are wrapped in `try/except ImportError` that raises `SystemExit` with
   install hint: `pip install yamlgraph[gui]`. (`TYPE_CHECKING` is not used — it only affects
   static analysis and does not prevent runtime `ImportError`.)

### Package integration

```toml
# pyproject.toml — new optional extra
[project.optional-dependencies]
gui = ["fastapi>=0.111", "uvicorn[standard]>=0.29"]
```

## Acceptance Criteria

- [ ] `yamlgraph serve` starts a FastAPI server on port **8765** (default; avoids conflict
  with Gradio's registered port 7860).
- [ ] `--graphs`, `--port`, `--open` flags work as specified.
- [ ] Graph list shows all discovered graphs with name and description.
- [ ] Selecting a graph renders a Mermaid topology diagram via
  `compile_graph(config).compile().get_graph().draw_mermaid()`.
- [ ] Variable fields are auto-populated from `graph_introspection.get_required_vars(config)`;
  required fields are marked.
- [ ] Clicking Run streams output tokens via SSE using `run_graph_streaming_native()` and
  displays them incrementally.
- [ ] `graph_to_mermaid()` is unit-tested with ≥3 graph fixtures (linear, branching, map).
- [ ] `get_required_vars()` in `graph_introspection.py` is unit-tested; `mcp_server.py`
  imports from it (no duplicate logic).
- [ ] `gui` optional extra documented in README and `reference/getting-started.md`.
- [ ] All `fastapi`/`uvicorn` imports wrapped in `try/except ImportError` with
  `pip install yamlgraph[gui]` hint; no `gui` imports in core package paths.
- [ ] Tests added and tagged `@pytest.mark.req("REQ-YG-078")` through
  `@pytest.mark.req("REQ-YG-081")`.
- [ ] `REQ-YG-078` through `REQ-YG-081` added to `ARCHITECTURE.md` capability table and
  requirement detail table.
- [ ] `ALL_REQS` range in `scripts/req_coverage.py` extended to `range(1, 82)` and
  `CAPABILITIES` dict updated with new entries.

## Requirements Mapping

| ID | Description |
|---|---|
| REQ-YG-078 | `yamlgraph serve` CLI: discovers graphs via glob, starts FastAPI on configurable port (default 8765), supports `--open` to launch browser |
| REQ-YG-079 | Playground API: `GET /api/graphs`, `GET /api/graphs/{id}/diagram` (LangGraph Mermaid), `POST /api/graphs/{id}/run` (SSE via `run_graph_streaming_native`) |
| REQ-YG-080 | Playground UI: single-page HTML, graph list, Mermaid diagram render, variable form, SSE streaming output display |
| REQ-YG-081 | `graph_introspection.get_required_vars()`: shared helper extracted from `mcp_server.discover_graphs()`; used by both MCP server and playground |

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| **Streamlit** | Heavy dependency (~50 MB); opinionated layout; harder to embed SSE streaming; violates lean-dependency principle. |
| **TUI (Textual/Rich)** | Doesn't solve the "demo to stakeholders" or "share a link" use-case; terminal-bound. |
| **Notebook (Jupyter)** | Requires Jupyter install; not zero-config; poor for streaming. |
| **Enhance existing example FastAPI apps** | Per-project, not reusable; doesn't provide topology visualization or variable introspection. |
| **Defer as deployment concern** | Unlike URL-based prompt loading (FR deferred), a playground has no equivalent workaround — the CLI is the only alternative and requires terminal fluency. |
| **Custom Mermaid traversal (Option B)** | LangGraph's built-in `draw_mermaid()` is always accurate and requires zero new code. A prior deleted implementation (`cli/__pycache__/graph_mermaid.cpython-313.pyc` artifact) confirms this approach was already abandoned. |

## Amendment Log

Issues resolved from inbox draft (2026-02-21):

- **ISSUE-1 (REQ numbering):** Replaced `REQ-YG-GUI-01–04` with `REQ-YG-078–081` (sequential
  integers; highest existing was `REQ-YG-077`).
- **ISSUE-2 (streaming function):** Replaced nonexistent `run_graph_stream()` with
  `run_graph_streaming_native()` from `yamlgraph/executor_async.py`.
- **ISSUE-3 (Mermaid approach):** Chose Option A — LangGraph built-in `draw_mermaid()`.
  Rationale documented above and in Alternatives.
- **ISSUE-4 (var introspection duplication):** `infer_required_vars()` replaced by
  `graph_introspection.get_required_vars()` extracted from `mcp_server.py`.
- **ISSUE-5 (lazy import):** `TYPE_CHECKING` guidance removed; all optional imports use
  `try/except ImportError` with `SystemExit`.
- **ISSUE-6 (port conflict):** Default port changed from 7860 to 8765.

## Related

- `yamlgraph/mcp_server.py` — graph discovery glob logic and `required_vars` extraction to refactor
- `examples/booking/api/app.py`, `examples/daily_digest/api/app.py` — FastAPI pattern reference
- `yamlgraph/cli/` — CLI entry point where `serve` command will be added
- `reference/getting-started.md` — documentation target
- FR-034 (novel-generator-demo), FR-020 (soup-generator) — graph examples that benefit from playground
