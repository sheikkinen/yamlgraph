# Diary: FR-291 Per-Graph Typed MCP Tools

**Date:** 2026-04-27
**FR:** FR-291
**CAP:** CAP-136 (REQ-YG-310–314)

## What Happened

Implemented per-graph typed MCP tools — each YAMLGraph graph now auto-generates its own named MCP tool with a typed JSON Schema derived from the YAML `state:` block. Built a Mastra (TypeScript) integration example proving cross-runtime discovery.

## Cognitive Process

**Research → FR → Judge → RED → GREEN → Demo** — the full rite.

The research phase (Mastra comparison) surfaced the real insight: the competitive moat isn't in the framework code but in the **declarative contract**. If graph YAML is the single source of truth for both pipeline logic AND API contract, then MCP/A2A clients discover typed tools without knowing they're YAML pipelines.

## Traps Encountered

### 1. Boundary Normalization (The One Law)
State values can be strings (`str`) or dicts (`{type: list, reducer: sorted_add}`). The `_yaml_type_to_json_schema` function crashed on dict values. **Fix:** Normalize at the boundary — `_extract_input_vars` now handles both shapes before calling the type mapper.

**Graduated pattern:** State block values are polymorphic (str | dict). Any function consuming them must normalize first.

### 2. Vendor API Costume (vendor_default_as_help)
Mastra's `@mastra/mcp` package renamed `MCPClient` → `MCPConfiguration` and `MastraMCPClient`. The FR cited the old API from research notes. Also, Mastra prefixes all tool names with the server key (`yamlgraph_`), making `hello_mastra` appear as `yamlgraph_hello_mastra`.

**Lesson:** External SDK APIs are untrusted input — verify exports at runtime, not from docs.

### 3. Pre-commit Gate Choreography
The `changelog-required` hook checks `git diff --cached` for changelog fragments. When a changelog was committed in an earlier GREEN commit and a later feat commit needed to amend, the fragment wasn't in the diff. Required a real content change to the fragment, not just a touch.

**Lesson:** Pre-commit hooks are boundary enforcement. Working *with* them (real content changes) is faster than working *around* them.

## Heuristic

> **External SDK APIs are boundaries, not contracts.** Verify exports, prefixes, and naming conventions at integration time. Research notes decay faster than the code they describe.

## Seed

Could YAMLGraph auto-detect tool name prefix conventions from MCP clients and strip/add them as needed? Or should the `tool_name` in discovery include a `namespace` field so clients can compose names their way?
