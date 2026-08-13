# Feature Request: FR-790 — API Discovery Schema-Extract Step Graph

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-13
**First consumer / first event:** FR-791 API discovery orchestrator,
the first time a confirmed platform needs its capabilities enumerated —
endpoints, auth model, rate limits, data freshness.

**Parent plan:** `docs/adaptive-probing-plan.md` §4.6

## Summary

Create the schema-extract step: a graph that takes a confirmed platform
identification and sample responses, extracts capability information
(endpoints, parameters, auth model, rate limits, freshness, languages),
and returns a structured `CapabilityReport`. Starts as `llm` node;
promote to agent only if sampling proves adaptive iteration is needed.
Packaged as a `runtime.type: graph` tool manifest.

## Value Statement

The orchestrator gets structured API capability data ready for the
final `APIProfile` synthesis — the gap between "we found an API" and
"here's how to use it."

## Problem

A confirmed platform identification (e.g., "CKAN at data.gov.fi") tells
you *what* system it is but not *what it can do*. OpenAPI specs need
parsing; CKAN needs dataset counts and org listings; PxWeb needs subject
trees; custom APIs need response schema inference from samples.

## Ideal Result

Given `family: "ckan", base_url: "https://data.gov.fi"`, the step
returns a `CapabilityReport` with endpoint inventory, auth model,
sample response, record counts, and data freshness indicators.

## Proposed Solution

- **Graph type:** `llm` node with `tool_call` pre-steps for `parse_openapi` (python manifest); promote to agent if sampling shows adaptive iteration is needed
- **Family-specific extraction:**
  - OpenAPI: `parse_openapi` → endpoint inventory
  - CKAN: dataset count, top orgs, recent packages
  - PxWeb: subject tree, one table's variables
  - Custom: sample 1–3 responses, infer schema
- **Output schema:** `CapabilityReport { endpoints: list, auth_model: str, rate_limits: str | None, freshness: str | None, languages: list[str], sample_response: dict }`
- **Manifest:** `steps/schema_extract.tool.yaml` with `runtime.type: graph`

## Acceptance Criteria

- [ ] AC-01: Step graph exists under `examples/api-discovery/steps/schema-extract/graph.yaml`
- [ ] AC-02: Graph-runtime tool manifest `steps/schema_extract.tool.yaml` exists
- [ ] AC-03: OpenAPI specs parsed deterministically via `parse_openapi` tool
- [ ] AC-04: Output conforms to `CapabilityReport` Pydantic schema
- [ ] AC-05: Graph authored via `scripts/author.sh`; lint and smoke pass

## Related

- FR-783 (parse_openapi manifest — the tool this step uses)
- FR-788 (platform-confirm — provides the confirmed platform input)
- FR-791 (orchestrator — the consumer)
- `docs/adaptive-probing-plan.md` §4.6

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
