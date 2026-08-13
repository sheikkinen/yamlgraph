# Feature Request: FR-792 — Multi-Step Investigation Template

**Priority:** LOW
**Type:** Feature
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-08-13
**First consumer / first event:** the next investigation pipeline after
API discovery (FR-791) — e.g., "research a company," "audit a codebase,"
"investigate an incident" — the first time someone builds one and
discovers they are re-inventing the same orchestrator + step + tool
directory structure from scratch.

**Seed origin:** `docs/adaptive-probing-plan.md` reflection (2026-08-13)

## Summary

Extract the "N investigation steps, each an agent graph exposed as a
graph-runtime tool manifest, composed by a routing orchestrator" pattern
from API discovery (FR-783..FR-791) into a reusable scaffolding template.
A single command produces a working skeleton: orchestrator graph, N step
stubs (each with agent node + tool manifest), shared tool directory, and
typed output schemas at every boundary.

## Value Statement

The next investigation pipeline starts from structure, not from scratch.
The API discovery family (9 FRs, ~7 days effort) established a pattern;
this FR packages that pattern so the second instance costs hours, not days.

## Problem

The shape recurs across domains:

| Investigation | Steps | Tools |
|---------------|-------|-------|
| API discovery | recon, endpoint-probe, page-analysis, browser-sniff, platform-confirm, schema-extract | curl, gh search, fetch, playwright, parse_openapi |
| Company research | registry lookup, financial filings, news search, beneficial ownership, sanctions check | curl, company registry APIs, news search |
| Codebase audit | dependency scan, dead code, complexity analysis, security scan, architecture check | ruff, bandit, radon, vulture, import-linter |
| Incident investigation | changelog review, log search, trace analysis, hypothesis testing, root cause synthesis | git log, grep, LangSmith API, curl |

Each follows the same architectural contract:
1. **Orchestrator** routes between steps via `type: tool_call` on graph-runtime manifests
2. **Steps** are agent graphs with typed input/output schemas, exposed as `*.tool.yaml` manifests
3. **Leaf tools** are shared shell/python manifests consumed by whichever step needs them
4. **Conditional edges** implement skip logic based on intermediate results
5. **Terminal synthesis** node produces the final structured verdict

Without a template, each new investigation pipeline re-discovers this
structure by reading the API discovery example and manually reproducing
its layout. That's the "pattern documented but not contracted" trap
(`architecture_as_diagram`).

## Ideal Result

```bash
# Scaffold a new 4-step investigation pipeline
yamlgraph graph scaffold investigation \
  --name company-research \
  --steps "registry,financials,news,sanctions" \
  --home examples/company-research

# Produces:
examples/company-research/
├── graph.yaml                          # orchestrator with tool_call nodes + conditional edges
├── steps/
│   ├── registry.tool.yaml              # graph-runtime manifest stub
│   ├── registry/graph.yaml             # agent graph stub with TODO prompts
│   ├── financials.tool.yaml
│   ├── financials/graph.yaml
│   ├── news.tool.yaml
│   ├── news/graph.yaml
│   ├── sanctions.tool.yaml
│   └── sanctions/graph.yaml
└── tools/
    └── README.md                       # instructions for adding shared leaf manifests
```

Each stub is a valid, lintable graph. The orchestrator routes through all
steps sequentially with skip-logic edge placeholders. Step graphs contain
a single `type: agent` node with a `TODO` prompt and empty tool list.
Output schemas are placeholder Pydantic stubs. The entire skeleton passes
`yamlgraph graph lint` out of the box.

## Proposed Solution

### Template mechanism

This is a `yamlgraph graph scaffold` subcommand (or a documented
`scripts/scaffold-investigation.sh` if CLI extension is out of scope).
It generates files from templates — no runtime behavior, no new
framework primitives. The templates encode the architectural contract
proven by FR-783..FR-791.

### What the template produces

**Orchestrator (`graph.yaml`):**
- `type: tool_call` node per step, referencing `steps/{name}.tool.yaml`
- Conditional edge placeholders (`# TODO: add skip condition`)
- Terminal `synthesize` llm node with union output schema
- `metadata.provider` defaulting to graph-level setting

**Step manifest (`steps/{name}.tool.yaml`):**
- `runtime.type: graph` pointing to `steps/{name}/graph.yaml`
- Input/output mapping stubs

**Step graph (`steps/{name}/graph.yaml`):**
- Single `type: agent` node
- `tools: []` with `# TODO: add tool manifests`
- `max_iterations: 5` default
- Output schema stub: `{name}Result { findings: list[str], confidence: str }`
- Prompt file stub: `steps/{name}/prompts/investigate.yaml`

**Tool directory (`tools/README.md`):**
- Instructions for creating shared leaf manifests per FR-768

### Scope boundaries

**In scope:**
- File generation (orchestrator, step manifests, step graphs, prompt stubs, tool README)
- All generated files pass `yamlgraph graph lint`
- The skeleton runs (with mock/stub results) via `yamlgraph graph run`

**Out of scope:**
- CLI `scaffold` subcommand (start as a script; promote if pattern proves)
- Template customization beyond step names (no conditional-edge DSL, no tool pre-population)
- Runtime template expansion (this is a one-time generator, not a compile-time feature)

### Target location

`examples/` as a stand-alone example. Consumers like control-plane
consume the generated skeleton directly as a starting point — the
generated files are ordinary YAMLGraph graphs, not framework-coupled
artifacts.

## Acceptance Criteria

- [ ] AC-01: Scaffold script/command exists and generates the full directory structure
- [ ] AC-02: Generated orchestrator uses `type: tool_call` on graph-runtime step manifests (not subgraph nodes)
- [ ] AC-03: Generated step graphs each contain a `type: agent` node with typed output schema
- [ ] AC-04: Generated step manifests use `runtime.type: graph` with correct path references
- [ ] AC-05: All generated files pass `yamlgraph graph lint`
- [ ] AC-06: Generated orchestrator runs end-to-end (with stub/placeholder results)
- [ ] AC-07: Generating a 3-step and a 6-step skeleton both produce valid, lintable graphs
- [ ] AC-08: Documentation in generated `README.md` explains how to add tools, customize edges, and fill in prompts

## Alternatives Considered

- **Cookiecutter / copier template:** external tooling adds a dependency for file generation that `scripts/` + Jinja2 (already in the project) handles natively
- **Document the pattern only:** the API discovery example *is* documentation; if that were sufficient, the second pipeline wouldn't need to reverse-engineer the layout. The template mechanizes what documentation describes (`detection_without_enforcement`)
- **Graph-level inheritance / composition primitives:** a framework feature for template graphs; too heavy for generating static scaffolds, and the pattern is in the *directory structure and manifest wiring*, not in graph runtime semantics

## Related

- FR-783..FR-791 (API discovery family — the pattern source)
- FR-768 (tool manifests — the primitive step manifests use)
- FR-773 (feeder pattern — the tool-to-map seam)
- FR-767 (graph-authoring sole route — generated graphs still go through `scripts/author.sh` for customization)
- `docs/adaptive-probing-plan.md` §8 (composition patterns showing the orchestrator as a reusable unit)

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
