# Feature Request: FR-810 — Router-Visible Tool-Call Outputs

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
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
addressable state, e.g. a `parse_result: true` / `result_key: <state_key>`
option on tool_call nodes for graph-runtime tools whose child output is
a dict.

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

- **Surface:** an optional `parsed_key` field on `tool_call` node config.
  When set and the tool is a graph-runtime tool, the node parses the
  child output (`json.loads` when it is a string; pass-through when
  already a dict) and returns it under `parsed_key` alongside the
  wrapper under `state_key`. Parse failure with `parsed_key` set follows
  the node's `on_error` policy — no silent fallback (Commandment 6).
- **Scope guard:** wrapper shape, existing `state_key` semantics, and
  shell/python tool_call behavior are untouched; `parsed_key` is opt-in
  and absent-by-default (no migration, nothing to keep compatible).
- **Layer:** node_factory tool_call runtime + config model field +
  linter awareness (warn when `parsed_key` is set on a non-graph tool).
- **Docs:** `reference/graph-yaml.md` tool_call section; FR-792 scaffold
  template TODO comment updated to name the mechanism (comment-only
  change; any scaffold behavior change is a separate scaffold
  follow-up FR if judged material).

## Acceptance Criteria

- [ ] AC-01: A `tool_call` node with `parsed_key` on a graph-runtime tool exposes the child's dict output under that state key; a unit test routes an edge condition on a parsed field.
- [ ] AC-02: Without `parsed_key`, behavior is byte-identical to today (existing tool_call tests unchanged and green).
- [ ] AC-03: Parse failure with `parsed_key` set follows `on_error` (fail raises; no empty-dict substitution).
- [ ] AC-04: Linter warns when `parsed_key` is set on a shell/python tool.
- [ ] AC-05: `reference/graph-yaml.md` documents the field with a routing example; changelog fragment + req/CAP traceability.
- [ ] AC-06: (Demonstration) FR-809 or a committed demo graph uses `parsed_key` for a real skip condition.

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
