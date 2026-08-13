# Feature Request: FR-791 — API Discovery Orchestrator Graph

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 1.5 days
**Requested:** 2026-08-13
**First consumer / first event:** the next API source investigation in
control-plane — replacing the manual 10–30 min probe-by-hand process
with a single graph invocation.

**Parent plan:** `docs/adaptive-probing-plan.md` §4.7

## Summary

Create the API discovery orchestrator: a graph that composes the step
graph-runtime tool manifests (FR-785..FR-790) via `type: tool_call`
nodes with conditional edges, routing through recon → endpoint-probe →
page-analysis → [browser-sniff] → platform-confirm → schema-extract →
synthesize, and producing either an `APIProfile` or a `NotFoundVerdict`.

## Value Statement

One command — `yamlgraph graph run examples/api-discovery/graph.yaml
--var hypothesis="Finnish health statistics" --var country="FI"` — produces
a structured API profile or a documented not-found verdict, replacing
10–30 min of manual investigation per source.

## Problem

API discovery is a multi-step process where each step's output determines
the next step's input and whether certain steps should be skipped (e.g.,
browser-sniff only when the page is an SPA with no API found). Without
an orchestrator, the human must sequence these steps manually, interpret
intermediate results, and decide routing — exactly the kind of
deterministic-routing-around-judgment-steps that YAMLGraph is built for.

## Ideal Result

```bash
yamlgraph graph run examples/api-discovery/graph.yaml \
  --var hypothesis="Danish company register" \
  --var domain_hint="cvr.dk" \
  --var purpose="company lookup" \
  --var country="DK" --full
```

Returns either a complete `APIProfile` (URL, platform family, auth model,
endpoints, sample response, confidence level, probe suggestion) or a
`NotFoundVerdict` (reason, steps tried, alternatives).

## Proposed Solution

- **Structure:** `type: tool_call` nodes invoking the step graph-runtime manifests; conditional edges for skip logic; terminal `synthesize` llm node
- **Skip logic:**
  - Browser-sniff: only when `is_spa == true AND api_found == false`
  - Platform-confirm: skipped when no platform candidates found
  - Recon: optional (orchestrator v1 ships without it — FR-787 is lowest priority)
- **Output schemas:**
  - `APIProfile { url, platform_family, auth_model, endpoints, sample_response, total_records, languages, data_freshness, confidence, limitations, probe_suggestion }`
  - `NotFoundVerdict { verdict, reason, steps_tried, alternatives }`
- **Stop conditions:**
  - `found`: platform confirmed AND data query returned real data
  - `not_found`: geo-blocked, candidates exhausted, commercial-only
  - `needs_manual`: auth wall, CAPTCHA, rate limiting

## Acceptance Criteria

- [ ] AC-01: Orchestrator graph at `examples/api-discovery/graph.yaml`
- [ ] AC-02: Uses `type: tool_call` on step graph-runtime manifests (not subgraph nodes)
- [ ] AC-03: Conditional edges implement skip logic for browser-sniff and platform-confirm
- [ ] AC-04: Output conforms to `APIProfile` or `NotFoundVerdict` Pydantic schema
- [ ] AC-05: Smoke test against a known Finnish source (e.g., stat.fi PxWeb) returns correct APIProfile
- [ ] AC-06: Smoke test against a known-absent/geo-blocked source returns NotFoundVerdict
- [ ] AC-07: Graph authored via `scripts/author.sh`; lint and smoke pass
- [ ] AC-08: v1 ships without recon (FR-787) and browser-sniff (FR-789); orchestrator tolerates their absence

## Alternatives Considered

- **One big agent:** loses typed boundaries between steps; one agent with 5+ tools and open-ended iteration is harder to debug and costs more tokens than deterministic routing around contained judgment steps
- **Subgraph nodes:** rejected in §2 of parent plan — tool manifests let steps travel as reusable tools beyond this orchestrator

## Related

- FR-785 (endpoint-probe step), FR-786 (page-analysis step), FR-787 (recon step), FR-788 (platform-confirm step), FR-789 (browser-sniff step), FR-790 (schema-extract step)
- FR-783 (leaf tool manifests), FR-784 (network-sniff utility)
- `docs/adaptive-probing-plan.md` (parent plan)

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
