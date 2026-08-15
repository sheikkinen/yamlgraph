# Feature Request: FR-792 — Multi-Step Investigation Template

**Priority:** LOW
**Type:** Feature
**Status:** Judged — APPROVED WITH REVISIONS (2026-08-15); R-1..R-5 folded; R-1 source-instance gate satisfied by FR-791 (Enforced 2026-08-15)
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

### Template mechanism (R-2: surface frozen)

The authorized surface is exactly
`python scripts/scaffold_investigation.py --name <slug> --steps <csv> --home <path>`
(plus an optional `--stub` flag, R-4). `yamlgraph graph scaffold`, CLI
parser changes, package entry points, and runtime graph-loader changes
are NOT authorized by this FR. If a CLI command is desired later, file a
separate FR after the script has at least one enforced consumer. The
script generates files from templates — no runtime behavior, no new
framework primitives. The templates encode the architectural contract
proven by the committed, linted, smoke-run API discovery instance (R-1:
`examples/api-discovery/graph.yaml` + step manifests + step graphs +
shared leaf tools, FR-791 Enforced 2026-08-15 with live positive and
negative smokes recorded in its Implementation Record).

### Source-instance dependency gate (R-1)

Enforcement authority activates only after API discovery has a
committed, linted, smoke-run source instance demonstrating the
orchestrator → graph-runtime step manifest → step graph → shared leaf
tool manifest shape. SATISFIED: `examples/api-discovery/graph.yaml`
(commit fd36b773, FR-791) composes `steps/*.tool.yaml` manifests over
step graphs consuming `tools/*.tool.yaml` leaf manifests; lint green;
positive smoke found statfin.stat.fi PxWeb with live data; negative
smoke returned honest not_found (raw logs cited in FR-791).

### Graph-authoring route coexistence (R-3)

Enforcement tests generate into temporary non-governed directories and
remove those artifacts. Any committed generated example graph/prompt
under governed paths must be produced through the graph-authoring route
with its validation record. The scaffold script is documented as an
operator tool; FR-792 does not create a bypass route for agents to
author governed graph artifacts directly.

### Smoke model (R-4)

The `--stub` flag generates a skeleton whose step graphs and synthesize
node use deterministic non-LLM placeholder nodes (passthrough emitting
canned `{name}Result` shapes), suitable for `yamlgraph graph run` with
no provider keys. AC-08's end-to-end criterion is a committed pytest
smoke that generates a `--stub` skeleton in a temp directory, runs the
generated orchestrator, and asserts the final state shape (verdict and
per-step findings present) — not merely process exit. The default
(non-stub) skeleton uses `type: agent` + TODO prompt stubs and is
validated by lint/compile only.

### Traceability (R-5)

Capability `CAP-235` / requirement `REQ-YG-596`; every new test carries
`@pytest.mark.req("REQ-YG-596")`; tests cover 3-step and 6-step
generation with exact file paths, manifest path resolution, typed output
schemas, lint on all generated graphs, and README content.

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

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: FR-792 cites a committed, linted, smoke-run source investigation instance demonstrating the orchestrator → graph-runtime step manifest → step graph → shared leaf tool manifest shape; until that evidence exists, enforcement remains blocked.
- [ ] AC-02: The revised FR names exactly one script invocation surface, and no `yamlgraph graph scaffold` CLI or entry-point change is included.
- [ ] AC-03: The scaffold script generates the full directory structure for a requested home path: orchestrator `graph.yaml`, one `steps/{step}.tool.yaml` per step, one `steps/{step}/graph.yaml` per step, one prompt stub per step, and a generated `tools/README.md`.
- [ ] AC-04: Generated orchestrator graph uses `type: tool_call` nodes that reference graph-runtime step manifests, not subgraph nodes.
- [ ] AC-05: Generated step manifests use `runtime.type: graph` with paths that resolve correctly from the manifest location.
- [ ] AC-06: Generated step graphs contain the authorized placeholder node shape and a typed output schema for each step result.
- [ ] AC-07: Tests generate both 3-step and 6-step skeletons in temporary directories, assert exact file paths, validate manifest path references, and run graph lint on all generated graphs.
- [ ] AC-08: The end-to-end smoke criterion uses the exact stub model defined by R-4 and asserts final state shape, not merely process exit.
- [ ] AC-09: Generated README documentation explains how to add shared leaf tool manifests, customize conditional edges, and replace TODO prompts.
- [ ] AC-10: Any committed generated graph or prompt artifact under governed paths is authored through `scripts/author.sh` and has validation evidence; ordinary scaffold tests do not write governed paths.
- [ ] AC-11: A capability/requirement entry exists for the scaffold capability, every new test has the exact requirement marker, and requirement coverage passes for the new mapping.
- [ ] AC-12: No files under YAMLGraph runtime/CLI surfaces change, and no API-discovery implementation work from FR-783..FR-791 is performed under this FR.

## Conditions for Enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-5 are folded into the FR and the API-discovery source instance evidence required by R-1 exists. | GATE |
| C-2 | Keep this as a script/template feature. Any CLI command, runtime primitive, graph-loader behavior, or manifest schema change must stop and re-enter the pipeline as a separate FR. | GATE |
| C-3 | The scaffold must not become an agent-side bypass of the graph-authoring route; governed graph/prompt artifacts committed under `examples/` require `scripts/author.sh` validation evidence. | GATE |
| C-4 | Generated skeleton validation must be deterministic in CI/local tests and must not require live provider keys unless the FR explicitly supplies a mocked/stubbed execution model. | GATE |
| C-5 | Do not implement or modify API-discovery FR-783..FR-791 deliverables under FR-792; this FR extracts a template after that source exists. | GATE |
| C-6 | All scaffold tests must be traceable through a capability/requirement entry and exact `@pytest.mark.req` markers. | GATE |

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

**Judgement revisions folded:** R-1 (extraction gated on an enforced source instance — satisfied by FR-791, commit fd36b773), R-2 (surface frozen to `python scripts/scaffold_investigation.py`; no CLI subcommand), R-3 (generation tests use temp non-governed dirs; committed governed artifacts require the authoring route), R-4 (deterministic `--stub` smoke model asserting final state shape), R-5 (CAP-235/REQ-YG-596 traceability with 3-step and 6-step generation tests) — see `feature-requests/FR-792-multi-step-investigation-template.judgement.md`.
