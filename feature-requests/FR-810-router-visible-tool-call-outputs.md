# Feature Request: FR-810 — Router-Visible Tool-Call Outputs

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced (2026-08-15)
**Effort:** 1 day
**Requested:** 2026-08-15
**First consumer / first event:** FR-809 (orchestrator v2), the moment it
needs the edge condition "enter browser-sniff when page-analysis reported
SPA-without-API" — a decision on a field inside a `tool_call` wrapper
that edge expressions cannot address today.

**Seed origin:** FR-791 documented deviation + diary
(`docs/diary/diary-2026-08-15-fr791-orchestrator-capstone.md`): "the
boundary between state the router can see and state only the LLM can see
is a real design constraint for composed graphs; v2 should consider
promoting step outputs to parsed state."

## Summary

`type: tool_call` nodes store a wrapper
`{task_id, tool, success, result, error}` where `result` is the child
graph's output serialized as a **string**. Edge conditions can address
`wrapper.success` but not fields inside `result` — so composed graphs
route on upstream *hints* rather than the step's actual findings. Add an
opt-in mechanism that parses the child output and exposes it as
addressable state: a single optional `parsed_key` field on tool_call
nodes for graph-runtime tools whose child output is an object (R-1: no
aliases — `parse_result`/`result_key` spellings are not authorized).

## Value Statement

For authors of composed investigation graphs, versus the candidate-hints
workaround (routing on what an early llm node *predicted* instead of
what the step *found*): conditions read ground truth. FR-791 shipped
with the workaround and a documented deviation; every future composed
pipeline (company research, codebase audit, incident investigation —
the FR-792 scaffold's consumers) inherits the same constraint until the
boundary is fixed once, in code.

## Problem

Observed in FR-791 enforcement (Implementation Record, documented
deviation): the judgement's AC-05 asked skip routing on "page-analysis
returns no platform candidates," but the page-analysis output lives
inside `page_analysis.result` as a JSON string. The route had to key on
`candidate_urls.has_platform_hint` — an upstream prediction — and the
substance was preserved only because platform-confirm's own gate
(`platform_confirmation.success`) backstopped it. The FR-792 scaffold
generates TODO skip-condition edges that will hit the identical wall;
its diary Seed asks for exactly this cure so "the second pipeline
doesn't rediscover it."

This is `the_one_law` territory: the child graph's typed output is
normalized at its own boundary (output_schema), then *de*-normalized
into a string at the tool_call boundary and re-parsed downstream by an
LLM. The router should consume the typed artifact, not a lossy
projection.

## Ideal Result

```yaml
nodes:
  page_analysis:
    type: tool_call
    tool: page_analysis
    args: {...}
    state_key: page_analysis          # wrapper, unchanged
    parsed_key: page_findings         # NEW: child dict output, addressable

edges:
  - from: page_analysis
    to: browser_sniff
    condition: "page_findings.is_spa == true and page_findings.api_found != true"
```

## Proposed Solution

- **Surface (R-1):** exactly one optional field, `parsed_key`, on
  `tool_call` node config. No aliases, migrations, or synonym fields.
- **Eligibility (R-2):** `parsed_key` is valid only when the resolved
  tool is a graph-runtime tool (manifests with `runtime.type: graph`
  and any existing inline graph-tool form with the same invocation
  semantics). Two enforcement points: the linter warns when a
  statically known shell/python tool uses `parsed_key`; runtime treats
  a dynamically resolved non-graph tool with `parsed_key` as a node
  failure governed by `on_error`. Never silently ignored.
- **Parse/state/failure contract (R-3):** parsing occurs only after the
  child graph tool succeeds. The wrapper under `state_key` is returned
  unchanged. JSON strings must parse to an object/dict; dict outputs
  pass through; invalid JSON, lists, scalars, missing child output, and
  failed child wrappers are parse failures. Parse failures never emit
  an empty dict or partial parsed state. `parsed_key` joins the
  generated state surface exactly like `state_key` so edge conditions
  can address it.
- **on_error outcomes (R-4):** `on_error: fail` raises at the node;
  `on_error: skip` returns the failure envelope under `state_key` and
  does not set `parsed_key`; `retry`/`fallback` remain rejected at
  graph load per current tool_call docs.
- **Layer:** node_factory tool_call runtime + config model field +
  linter awareness.
- **Docs:** `reference/graph-yaml.md` tool_call section (routing
  example, graph-tool-only eligibility, wrapper preservation, failure
  behavior); FR-792 scaffold template TODO comment updated to name
  `parsed_key` (comment-only change).
- **Traceability:** `capabilities/CAP-236-router-visible-tool-outputs.yaml`
  providing `REQ-YG-597`; all tests marked
  `@pytest.mark.req("REQ-YG-597")`.

## Acceptance Criteria (revised per judgement)

- [x] AC-01: `tool_call` node config accepts exactly one new optional field, `parsed_key`; `parse_result`, `result_key`, and other aliases are rejected or absent from the public schema.
- [x] AC-02: A graph-runtime tool call with `parsed_key` exposes the child graph's object output under that state key, and a unit test routes an edge condition on a parsed field.
- [x] AC-03: Without `parsed_key`, the observable `tool_call` behavior and wrapper shape under `state_key` remain unchanged; existing `tool_call` tests stay green.
- [x] AC-04: JSON-string graph outputs parse only when they are JSON objects; dict outputs pass through; invalid JSON, lists, scalars, missing child output, and failed child wrappers are parse failures with no empty-dict substitution.
- [x] AC-05: Parse failures with `parsed_key` have explicit tests for `on_error: fail` and `on_error: skip`; `skip` returns a failure envelope under `state_key` and does not set `parsed_key`.
- [x] AC-06: Lint warns when `parsed_key` is configured on a statically known shell/python tool, and runtime fails under the node `on_error` policy when a dynamic tool expression resolves to a non-graph tool.
- [x] AC-07: `reference/graph-yaml.md` documents `parsed_key` with a routing example, graph-tool-only eligibility, wrapper preservation, and failure behavior.
- [x] AC-08: `capabilities/CAP-236-router-visible-tool-outputs.yaml` exists supplying `REQ-YG-597`, every new test has the exact `@pytest.mark.req("REQ-YG-597")` marker, `python scripts/req_coverage.py --strict` passes, and a changelog fragment is added.
- [x] AC-09: A deterministic committed witness uses `parsed_key` for a real skip condition (unit-test fixture graph routing on `parsed_key`); FR-810 enforcement does not depend on FR-809 being implemented.

## Alternatives Considered

- **Candidate-hints pattern (status quo):** routes on predictions, not findings; already produced one documented deviation and will recur per pipeline.
- **Have child graphs write extra scalar flags into their output for routing:** pushes orchestrator concerns into every step's schema; N steps × M flags versus one boundary fix.
- **Auto-parse every graph-tool wrapper (no opt-in):** changes existing state shapes under running graphs; opt-in keeps the change surface minimal.

## Related

- FR-791 (deviation source; AC-05 substance backstopped, mechanism deferred here)
- FR-809 (first consumer — SPA-path entry condition)
- FR-792 (scaffold generates the TODO edges that need this; diary Seed names it)
- FR-768 (tool manifest primitive owning graph-runtime semantics)

**Prior art:** FR-791 Implementation Record documents the deviation and its cause ("edge expressions cannot address tool_call wrapper JSON"); the FR-792 diary Seed proposes encoding the lesson. No prior FR has touched tool_call output parsing.

## Judgement

See `feature-requests/FR-810-router-visible-tool-call-outputs.judgement.md` —
APPROVED WITH REVISIONS; R-1..R-5 folded above (single `parsed_key`
field, graph-tool eligibility + dynamic-tool failure, exact
parse/state/failure contract, mechanically testable `on_error`
outcomes, deterministic unit-test witness independent of FR-809).
Gates C-1..C-6 accepted: fail-closed on parse errors and misuse; wrapper
shape and `state_key` semantics unchanged; any governed demo artifact
via the authoring route; req-traceable positive and negative witnesses.

## Implementation Record

Enforced 2026-08-15. RED commit `49ae35da` (25 witnesses, 22 confirmed
failing), GREEN in the same session.

- `yamlgraph/models/node_schema.py`: `parsed_key: str | None` on
  `NodeConfig`; `extra: "forbid"` already rejects `parse_result`/`result_key`.
- `yamlgraph/node_factory/tool_nodes.py`: new `graph_tool_names` parameter;
  module-level `_parse_output` (dict pass-through, JSON-object-string parse,
  everything else fail-closed) and `_envelope`; parse failures and
  dynamic non-graph misuse honor `on_error` (fail raises with node name /
  parsed_key in message, skip returns failure envelope without `parsed_key`).
  Refactored closures to module level to satisfy C901.
- `yamlgraph/compile/node_compiler.py`: passes
  `graph_tool_names=set(ctx.graph_tool_configs or {})`; map-compiler call
  site unchanged (default keeps map sub-nodes graph-tool-free).
- `yamlgraph/models/state_builder.py`: `parsed_key` joins the generated
  state surface (`Any`).
- `yamlgraph/linter/checks_semantic.py`: `W703` on statically known
  non-graph tool with `parsed_key`.
- `yamlgraph/tools/graph_tool.py`: **deviation (in spirit of AC-04)** —
  graph tools serialized dict outputs via `str()` (Python repr, unparseable);
  normalized at the boundary to `json.dumps` for dict/list outputs. Without
  this the compiled-graph witness cannot parse any real child output;
  existing graph-tool tests unaffected (scalar outputs still `str()`).
- Docs: `reference/graph-yaml.md` § tool_call; changelog fragment
  `changelog/unreleased/fr-810-parsed-key.md`.
- Witness: `tests/unit/test_fr810_parsed_key.py` — 25 tests incl. compiled
  parent/child fixture graphs routing `page_findings.is_spa == true`
  through sniff/no_sniff. Full fast suite green (5822+ passed).
