# Feature Request: Protocol Archaeology Graph

**FR-056**
**Priority:** MEDIUM
**Type:** Feature (Demo / Example)
**Status:** Draft — Re-submitted for Judgement
**Effort:** 1.5 days
**Requested:** 2026-02-20

## Summary

Add `examples/demos/protocol-archaeology/` — a YAML graph that accepts a GitHub repository URL, discovers and fetches relevant source files (`gh` CLI + shell tools), and uses a `discover → map(analyze) → synthesize` pipeline to produce a structured integration brief covering endpoint URLs, auth flows, message formats, and error handling. No new framework code is required; this demo exercises the existing `type: agent`, `type: map`, `type: llm`, and `type: shell` capabilities in combination with an inline Pydantic schema.

## Problem

When integrating with a third-party service whose SDK documentation is absent or outdated, developers must manually sift through dozens of source files — routers, middleware, OpenAPI specs, error handlers — context-switching between the browser, terminal, and editor. The investigation is:

1. **Repetitive across projects** — every integration starts from scratch: find the entry file, trace routes, guess auth middleware, reverse-engineer error envelopes.
2. **Lossy** — critical details (token expiry behaviour, undocumented 422 shapes, implicit auth scopes) are scattered across deeply nested files and rarely captured in notes.
3. **Unstructured output** — even when developers document findings, the format varies, making it hard to share or feed downstream to code generators or LLM-assisted API clients.

The `code-analysis` demo (`examples/demos/code-analysis/`) shows YAMLGraph running local shell tools through an agent. The `git-report` demo shows repo-scoped shell commands. The `tavily-rag` demo shows external retrieval feeding a structured LLM output. **Protocol archaeology combines all three patterns but targets remote GitHub repos and produces a typed integration brief** — a use case none of the existing demos covers.

## Proposed Solution

### Scope Judgement — Does This Belong in YAMLGraph?

Yes, as a demo with one minimal framework addition. The framework already provides every primitive needed:

| Need | Existing capability |
|------|-------------------|
| Fetch repo file tree | `type: shell` with `gh api` |
| Fetch individual file content | `type: shell` with `gh api` |
| LLM-guided file discovery | `type: agent` with shell tools |
| Parallel file analysis | `type: map` over discovered files |
| Structured integration brief | `type: llm` with inline Pydantic schema |
| Typed `discover` output | `FileEntry` + `DiscoveredFiles` added to `schemas.py` |

One framework file touched (`schemas.py`, two model classes added). No new node type. No new configuration key.

---

### File Structure

```
examples/demos/protocol-archaeology/
├── README.md
├── graph.yaml              # Core pipeline: discover → map(analyze) → synthesize
├── prompts/
│   ├── discover.yaml       # Directs agent to find relevant files
│   ├── analyze.yaml        # Analyzes one file for protocol signals
│   └── synthesize.yaml     # Merges findings into integration brief
```

**Framework addition (minimal):** `FileEntry` and `DiscoveredFiles` Pydantic models added to `yamlgraph/models/schemas.py` — required because `list[dict]` is not accepted by the inline schema engine.

---

### A. Shell Tools (inline in `graph.yaml`)

```yaml
tools:
  list_repo_tree:
    type: shell
    command: >
      gh api repos/{repo_path}/git/trees/HEAD --recursive
      --jq '[.tree[] | select(.type=="blob") | .path]' 2>&1
    description: >
      List all file paths in the GitHub repository as a JSON array.
      Use repo_path in the form owner/repo (e.g. expressjs/express).
    parse: text

  fetch_file:
    type: shell
    command: >
      gh api repos/{repo_path}/contents/{file_path}
      --jq '.content' 2>&1 | base64 -d 2>/dev/null | head -200
    description: >
      Fetch the content of a specific file from the repo (first 200 lines).
      Use repo_path as owner/repo and file_path as the relative path.
    parse: text
```

> **Note:** `gh` CLI is authenticated via `GH_TOKEN` or `~/.config/gh/hosts.yml`. The demo's `README.md` documents this prerequisite.

---

### B. Core Graph (`graph.yaml`)

```yaml
version: "1.0"
name: protocol-archaeology
description: >
  Given a GitHub repo URL, extract endpoints, auth flows, message formats,
  and error handling into a structured integration brief.
prompts_relative: true
prompts_dir: prompts

state:
  repo_url: str       # e.g. https://github.com/expressjs/express
  repo_path: str      # derived: owner/repo — extracted by discover agent

tools:
  list_repo_tree:
    type: shell
    command: >
      gh api repos/{repo_path}/git/trees/HEAD --recursive
      --jq '[.tree[] | select(.type=="blob") | .path]' 2>&1
    description: >
      List all file paths in the GitHub repository.
      repo_path must be owner/repo format.
    parse: text

  fetch_file:
    type: shell
    command: >
      gh api repos/{repo_path}/contents/{file_path}
      --jq '.content' 2>&1 | base64 -d 2>/dev/null | head -200
    description: >
      Fetch the first 200 lines of a file from the repository.
    parse: text

nodes:
  discover:
    type: agent
    prompt: discover
    tools: [list_repo_tree, fetch_file]
    max_iterations: 12
    state_key: discovered_files
    model: DiscoveredFiles
    variables:
      repo_url: "{state.repo_url}"

  analyze:
    type: map
    over: "{state.discovered_files.files}"
    as: file_info
    node:
      type: llm
      prompt: analyze
      state_key: file_analysis
      variables:
        repo_path: "{state.discovered_files.repo_path}"
        file_path: "{state.file_info.path}"
        file_content: "{state.file_info.content}"
    collect: file_analyses

  synthesize:
    type: llm
    prompt: synthesize
    requires: [analyze]
    state_key: integration_brief
    variables:
      repo_url: "{state.repo_url}"
      file_analyses: "{state.file_analyses}"
    schema:
      name: IntegrationBrief
      fields:
        endpoints:
          type: list[str]
          description: "Discovered HTTP endpoint paths with methods, e.g. POST /api/v1/tokens"
        auth_flows:
          type: list[str]
          description: "Authentication mechanisms detected (OAuth2, API key, JWT, basic, etc.)"
        message_formats:
          type: list[str]
          description: "Request/response payload formats and notable schema constraints"
        error_codes:
          type: list[str]
          description: "Notable error codes or status codes with their semantics"
        integration_notes:
          type: str
          description: "Summary: base URL, versioning strategy, rate limits, gotchas"

edges:
  - from: START
    to: discover
  - from: discover
    to: analyze
  - from: analyze
    to: synthesize
  - from: synthesize
    to: END
```

---

### C. Discover Agent Prompt (`prompts/discover.yaml`)

```yaml
system: |
  You are a protocol archaeologist. Your task: explore a GitHub repository
  and identify the files most likely to reveal its HTTP API contract.

  Target files (in priority order):
  1. OpenAPI / Swagger specs: openapi.yaml, swagger.json, *spec*, *schema*, api*.yaml
  2. Router / route files: routes/, routers/, controllers/, api/, handlers/
  3. Middleware: auth*, middleware*, security*
  4. Error definitions: errors*, exceptions*, status*
  5. Model/schema files: models/, schemas/, types/

  Strategy:
  - First, call list_repo_tree to get all file paths.
  - Identify at most 15 high-signal files using the priority list above.
  - Call fetch_file on each to confirm it contains protocol-relevant content.
  - Stop when you have at most 10 confirmed files.

  Return a JSON object with:
    - repo_path: "owner/repo" (extracted from the URL)
    - files: list of confirmed file paths (max 10)

user: |
  Repo URL: {repo_url}

  Explore this repository and return the JSON object as instructed.
```

---

### D. Analyze Prompt (`prompts/analyze.yaml`)

```yaml
system: |
  You are analyzing a single source file for HTTP API protocol signals.
  Extract ONLY what is explicitly present in the file content provided.
  Do NOT infer or extrapolate.

user: |
  Repository: {repo_path}
  File: {file_path}

  File content (already fetched):
  {file_content}

  Extract:
  - HTTP endpoints defined in this file (method + path)
  - Authentication/authorization patterns
  - Request/response payload shapes
  - Error/status code definitions

  Be terse. Use bullet points. If the file has no protocol signals, say "no signals".
```

> **Implementation note:** The `discover` agent fetches the content of each file it selects; its output `discovered_files.files` carries `{path, content}` pairs. The `analyze` node maps over those pairs, accessing them via `{state.file_info.path}` and `{state.file_info.content}` (dot-path interpolation is supported by the expressions engine).

Because `list[dict]` is an untyped dict and violates Commandment 5, the inline schema engine cannot represent this type — `resolve_type()` does not accept `list[dict]`. The `discover` agent's output schema must therefore be promoted to `yamlgraph/models/schemas.py` as proper Pydantic models:

```python
# yamlgraph/models/schemas.py  (addition)

class FileEntry(BaseModel):
    """A single file discovered during protocol archaeology."""
    path: str = Field(description="Repo-relative file path")
    content: str = Field(description="First 200 lines of file content")


class DiscoveredFiles(BaseModel):
    """Output of the discover agent in the protocol-archaeology demo."""
    repo_path: str = Field(description="owner/repo extracted from URL")
    files: list[FileEntry] = Field(description="Confirmed high-signal files (max 10)")
```

The `discover` node references this model via `model: DiscoveredFiles` (loaded from `schemas.py`). `analyze` maps over `discovered_files.files` with `as: file_info`, so each iteration exposes `state.file_info.path` and `state.file_info.content`.

---

### E. Synthesize Prompt (`prompts/synthesize.yaml`)

```yaml
system: |
  You are a senior integration engineer. Consolidate per-file protocol
  analysis into a precise integration brief.

  Rules:
  - Only report what was observed, never speculate.
  - Deduplicate endpoints (same path seen in multiple files = one entry).
  - If auth flow contradicts between files, report the conflict explicitly.
  - Prefer specific over vague: "Bearer JWT in Authorization header" > "uses auth".

user: |
  Repository: {repo_url}

  Per-file analysis results:
  {file_analyses}

  Produce the structured integration brief.
```

---

### Usage

```bash
# Requires: gh CLI authenticated, ANTHROPIC_API_KEY set
yamlgraph graph run examples/demos/protocol-archaeology/graph.yaml \
  --var repo_url="https://github.com/expressjs/express"

# Print as JSON
yamlgraph graph run examples/demos/protocol-archaeology/graph.yaml \
  --var repo_url="https://github.com/tiangolo/fastapi" \
  --output json
```

---

### Complexity Budget

The discover agent calls `fetch_file` up to 15 times + the map over 10 files + 1 synthesis call = ~26 LLM/tool invocations. At typical token counts this fits in one Claude context window per analysis node. No chunking infrastructure is needed for v1.

## Acceptance Criteria

- [ ] `examples/demos/protocol-archaeology/graph.yaml` passes `yamlgraph graph lint`
- [ ] `yamlgraph graph run examples/demos/protocol-archaeology/graph.yaml --var repo_url="https://github.com/expressjs/express"` completes without error and returns a non-empty `integration_brief`
- [ ] `integration_brief` has all five fields: `endpoints`, `auth_flows`, `message_formats`, `error_codes`, `integration_notes`
- [ ] `integration_brief` is validated by the inline Pydantic schema (`IntegrationBrief`) — type errors raise, not silently return empty
- [ ] `discover` agent extracts `repo_path` (owner/repo) correctly from both `https://github.com/owner/repo` and `https://github.com/owner/repo.git` URL forms
- [ ] `discover` agent returns at most 10 files (enforced by prompt, validated by test)
- [ ] `analyze` map node is configured without `max_concurrency` override — linter produces no `max_concurrency` warning (parallel execution is the default)
- [ ] Graceful failure when `gh` is not authenticated: error captured in `state.errors`, not a Python crash
- [ ] Graceful failure for non-existent repo (404 from `gh api`): error in `state.errors`
- [ ] Unit test for URL → `repo_path` extraction logic (if extracted in Python helper; otherwise integration test covers it). Tests are demo-local only — no `REQ-YG-XXX` tag required; tests do not enter the framework test suite.
- [ ] Integration test guarded by `GH_TOKEN` availability and network access flag. Marked demo-local; no `@pytest.mark.req` annotation needed.
- [ ] `README.md` documents prerequisites (`gh` CLI, `GH_TOKEN`), usage, and a worked example with `expressjs/express`
- [ ] Diary entry in `docs/diary.md`

## Alternatives Considered

### 1. Use GitHub REST API directly via Python `requests` (no `gh` CLI)
Rejected for v1. The `gh` CLI is already present in the development environment and handles auth automatically. Using `requests` would require a custom Python tool (`nodes/github_fetch.py`) adding code with no new capability. Can be added in v2 if `gh` CLI proves unavailable in target environments.

### 2. Download entire repo as a tarball and parse locally
Rejected. A full repo clone/tarball is overkill; most repos have hundreds of files. The agent-guided discovery pattern fetches only the ~10 highest-signal files — much cheaper in tokens and latency.

### 3. Use Tavily with `include_domains=github.com`
Considered (synergy with FR-053). Tavily's web scraping cannot access raw file content on GitHub without special handling, and GitHub's raw.githubusercontent.com is inconsistently indexed. The `gh api` shell tool is more reliable and works on private repos.

### 4. Generalise into a reusable "repo explorer" framework primitive
Rejected. This is application logic, not framework logic. The right home is `examples/demos/`. If the `gh api` shell pattern proves useful across multiple demos, it can be promoted to `examples/shared/github_tools.py` in a follow-on FR (same pattern as `examples/shared/websearch.py`).

### 5. Include code generation from the brief (generate SDK stub, integration test)
Out of scope for this FR. The integration brief is the natural stopping point; consuming it for codegen is a separate concern and belongs in a follow-on demo (e.g., `examples/demos/protocol-codegen/`).

## Related

- `examples/demos/code-analysis/` — Pattern reference: agent with shell tools → LLM synthesis
- `examples/demos/git-report/` — Pattern reference: `gh`-style shell tools against a local repo
- `examples/demos/tavily-rag/` — Pattern reference: structured output via inline Pydantic schema (FR-053)
- `examples/shared/websearch.py` — Precedent for promoting shared retrieval tools
- FR-053: Tavily Domain RAG Demo (structured retrieval → synthesis pattern)
- FR-030: Map concurrency control (relevant if `analyze` map needs per-item timeout)
- FR-032: Node-level caching (cache `fetch_file` results to avoid re-fetching on retry)
- FR-045: A2A Protocol brainstorm (distinct — A2A is about agent interop protocol, not reverse-engineering third-party APIs)

---

## Judgement (Round 2 — Chaplain automated)

**Verdict: AMEND**

Round 1 defects 1, 3, 4 (variable syntax, repo_path reference, naming) correctly resolved. Two new critical defects identified: agent output is raw string (not Pydantic), and schemas placed in wrong module.

*(Preserved for history — see Round 3 below for current evaluation.)*

---

## Judgement (Round 3 — Human)

**Verdict: AMEND**

**Date:** 2026-02-20
**Reviewed by:** Human judge (code-verified)

The Chaplain's Round 2 judgment correctly identified the two critical architectural defects (A: agent output is raw string; B: schemas in framework module). Both are **confirmed** against source code. However, the FR has additional issues the Chaplain missed, and its own proposed fixes need refinement.

---

### Status of Chaplain Round 2 Defects

**Defect A — Agent nodes produce raw strings** — **CONFIRMED CRITICAL.**
Verified: `yamlgraph/tools/agent.py` line 285 stores `response.content` (string) into `state_key`. No `output_model` or schema support exists in agent nodes. `model:` on an agent node is the LLM model name override (line 208–214), not a Pydantic model reference. The Chaplain's Option (a) — add a `type: python` parse node between `discover` and `analyze` — is the correct fix. A `type: llm` parse node wastes an LLM call; a Python node that does `json.loads()` + Pydantic validation is cheaper and deterministic.

**Defect B — Schemas in wrong module** — **CONFIRMED CRITICAL.**
Verified: `yamlgraph/models/schemas.py` lines 1–5 explicitly state "FRAMEWORK models only." The Chaplain's fix (demo-local `schemas.py` + dotted path import) is correct. `resolve_class()` in `node_factory/base.py` line 17 supports `importlib.import_module` with dotted paths.

---

### New Defects Found

**Defect C — `--output json` does not exist (INCORRECT CLAIM)**

The Usage section claims:
```bash
yamlgraph graph run ... --output json
```

`yamlgraph graph run` has no `--output` flag. Supported flags: `--var`, `--var-file`, `--thread`, `--export`, `--full`, `--async`, `--share-trace`, `--recursion-limit`, `--timeout`, `--token-usage`. The `--output` flag exists only on `graph codegen`. This usage example would fail with an unrecognized argument error.

**Required fix:** Remove `--output json` from Usage. Use `--full` for complete output, or pipe to `jq` for JSON extraction.

---

**Defect D — `type: shell` is not a real tool type (MINOR)**

The FR declares tools with `type: shell`. In practice, shell tools are identified by the presence of a `command:` key, not by `type: shell`. The `parse_tools` function in `yamlgraph/tools/shell.py` line 186 only checks for `type: python` (to skip) and `command:` (to include). `type: shell` is silently ignored — it doesn't cause errors, but it's misleading documentation. It suggests a first-class `type: shell` that doesn't exist.

**Required fix:** Either remove `type: shell` from tool definitions (just use `command:`) or document that `type: shell` is conventional, not enforced.

---

**Defect E — `tavily-rag` vs `tavily_rag` (MINOR)**

The Related section references `tavily-rag` (hyphenated). The actual directory is `examples/demos/tavily_rag/` (underscored). This is exactly the kind of hyphen/underscore mismatch the copilot-instructions warn about: "Convert paths with hyphens to snake_case to avoid import issues."

**Required fix:** Use `tavily_rag` consistently.

---

**Defect F — Summary claims "no new framework code" but adds to `schemas.py` (CONTRADICTION)**

The Summary says: "No new framework code is required." The Capabilities table and the Schema section both say `FileEntry`/`DiscoveredFiles` are "added to `yamlgraph/models/schemas.py`." This is a direct contradiction — `schemas.py` is framework code. Once Defect B is fixed (move to demo-local), the Summary becomes correct. But the current text is internally inconsistent.

**Required fix:** After fixing Defect B, update the Summary and Capabilities table to state "No framework files touched."

---

**Defect G — Double tool definition (STRUCTURAL)**

The FR defines shell tools twice: once in Section A ("Shell Tools") and again inline in Section B ("Core Graph — graph.yaml"). The Section B version is the authoritative one (it's the actual file). Section A is redundant and creates a maintenance mismatch risk. During the Amend cycle, one could be updated and the other forgotten.

**Required fix:** Remove Section A entirely. The tools are defined inline in the graph YAML — that's canonical.

---

### Complexity Budget — Undercount

The FR says "~26 LLM/tool invocations." The agent's `max_iterations: 12` means up to 12 LLM reasoning steps (not just 12 tool calls — each iteration is an LLM call + potential tool call). With `fetch_file` called up to 15 times, that's up to 12 LLM calls + 15 tool executions in the discover phase alone, plus 10 map LLM calls + 1 synthesis = up to 23 LLM calls + 15 tool executions = 38 total invocations. The "~26" estimate undercounts agent reasoning steps.

Not blocking, but the estimate should be corrected for cost transparency.

---

### What Works Well

1. **Problem statement is genuine and well-scoped.** Protocol archaeology is a real developer pain, and the "agent discovers, map analyzes, LLM synthesizes" pattern is the right shape.
2. **Alternatives are thorough and correctly rejected.** The tarball/Tavily/framework-generalization rejections are well-reasoned.
3. **Acceptance criteria are specific and testable.** URL parsing, graceful failures, lint passing — these are verifiable.
4. **The agent-as-file-discoverer pattern is novel** within the demo portfolio. No existing demo uses an agent to selectively fetch remote files and feed them to a map pipeline.
5. **The prompts are well-written.** The discover prompt's priority list and the synthesize prompt's deduplication/conflict rules show domain understanding.

---

### Path to APPROVE

1. **Add a `type: python` parse node** between `discover` and `analyze` that does `json.loads(state["discovered_files"])` → `DiscoveredFiles.model_validate()`. This is deterministic, costs zero tokens, and produces the typed object the map needs.
2. **Move schemas to demo-local** `examples/demos/protocol-archaeology/schemas.py`. Reference via `output_model: examples.demos.protocol_archaeology.schemas.DiscoveredFiles` on the parse node (or just import inline in the Python node function).
3. **Remove `--output json`** from Usage examples.
4. **Remove Section A** (duplicate tool definitions).
5. **Fix `tavily-rag` → `tavily_rag`** in Related.
6. **Update Summary** to reflect "no framework files touched" after schemas move.
7. **Correct complexity budget** to ~38 invocations.

Defects A, B, C require amendment. Defects D–G are minor cleanups that should be fixed in the same pass. Resubmit after addressing all 7.
