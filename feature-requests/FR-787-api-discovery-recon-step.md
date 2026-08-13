# Feature Request: FR-787 — API Discovery Recon Step Graph

**Priority:** LOW
**Type:** Feature
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-13
**First consumer / first event:** FR-791 API discovery orchestrator,
when it wants prior-art evidence from GitHub before blind probing —
but the orchestrator already tolerates recon's absence, making this
the lowest-priority step.

**Parent plan:** `docs/adaptive-probing-plan.md` §4.1

## Summary

Create the recon step: an agent graph that searches GitHub for code
referencing a target domain/API, extracting candidate URLs, auth
patterns, and schema hints from other developers' implementations.
Packaged as a `runtime.type: graph` tool manifest.

## Value Statement

Other developers are the best documentation — THL Sampo's hidden
JSON-stat endpoint was found via GitHub code search, not official docs.
The recon step automates this "who solved this before?" investigation.

## Problem

Manual GitHub code search is effective but slow: generating search-term
variants (domain forms, service names, country conventions), scanning
results for API URLs, auth patterns, and client packages. An agent with
`gh_code_search` iterates this systematically.

## Ideal Result

Given `hypothesis: "Finnish health statistics API"`, the step returns
`ReconResult` with candidate URLs, auth hints, and evidence links
extracted from GitHub code search results.

## Proposed Solution

- **Graph type:** single `type: agent` node with `gh_code_search` manifest tool
- **Output schema:** `ReconResult { candidate_urls: list[str], auth_hints: list[str], schema_hints: list[str], evidence: list[str] }`
- **Manifest:** `steps/recon.tool.yaml` with `runtime.type: graph`
- **Failure mode:** empty result is valid — not every source has GitHub footprints

## Acceptance Criteria

- [ ] AC-01: Step graph exists under `examples/api-discovery/steps/recon/graph.yaml`
- [ ] AC-02: Graph-runtime tool manifest `steps/recon.tool.yaml` exists
- [ ] AC-03: Agent generates search-term variants and iterates queries
- [ ] AC-04: Output conforms to `ReconResult` Pydantic schema
- [ ] AC-05: Empty result handled gracefully (valid outcome, not error)
- [ ] AC-06: Graph authored via `scripts/author.sh`; lint and smoke pass

## Related

- FR-783 (gh_code_search manifest — the tool this agent uses)
- FR-791 (orchestrator — the consumer)
- `docs/adaptive-probing-plan.md` §4.1

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
