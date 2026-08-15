# Feature Request: FR-787 — API Discovery Recon Step Graph

**Priority:** LOW
**Type:** Feature
**Status:** Enforced 2026-08-15 — AC-01..AC-10 delivered; authoring adapter report verified, lint + live smoke passed, 15/15 tests green (REQ-YG-592, CAP-231)
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

## Dependency Gate (R-1)

FR-787 may not author or validate the recon graph until the FR-783
`gh_code_search.tool.yaml` deliverable exists under
`examples/api-discovery/tools/` and is loadable by a consumer graph.
Enforcement must confirm this before authoring or smoking recon.

## Output Validation Contract (R-2)

The graph must define or reference `ReconResult` with exactly
`candidate_urls`, `auth_hints`, `schema_hints`, and `evidence` as
`list[str]`. The smoke output must be validated against that schema.
Each non-empty evidence entry must include source identity sufficient
for audit: at minimum repository, path, and URL or GitHub result link.

## Validation Evidence and Credential Handling (R-3)

Enforcement must produce `tmp/draft-authoring-report.md` with
`Artifacts`, `Precedent`, `Validation`, `Repairs`, and
`Blocked validation`; list the exact precedent adapted; run
`yamlgraph graph lint examples/api-discovery/steps/recon/graph.yaml`;
and run a narrow smoke command with concrete variables. If `gh`
authentication blocks the smoke, the report must record the exact
blocked command and reason, and the FR must not claim "smoke pass"
for that run.

## Scope Boundary (R-4)

FR-787 does not modify `examples/api-discovery/graph.yaml`,
orchestrator routing, or other step graphs, and must not make FR-791
depend on recon. Recon remains optional to the orchestrator.

## Acceptance Criteria (revised per judgement)

- [x] AC-01: `examples/api-discovery/steps/recon/graph.yaml` exists and was authored through `scripts/author.sh` with a non-empty `tmp/draft-authoring-report.md`.
- [x] AC-02: `examples/api-discovery/steps/recon.tool.yaml` exists and declares a graph runtime pointing to `recon/graph.yaml`.
- [x] AC-03: Enforcement confirms the FR-783 `examples/api-discovery/tools/gh_code_search.tool.yaml` dependency exists and is loadable before authoring or smoking recon.
- [x] AC-04: The recon agent prompt or config generates domain/service/country search-term variants and iterates `gh_code_search` within a bounded iteration budget.
- [x] AC-05: The graph output validates as `ReconResult` with `candidate_urls`, `auth_hints`, `schema_hints`, and `evidence` as `list[str]`.
- [x] AC-06: Non-empty evidence entries include source identity sufficient for audit: repository, path, and URL or GitHub result link.
- [x] AC-07: Empty results are valid: a no-hit or blocked-footprint scenario returns empty lists under `ReconResult`, not a graph error.
- [x] AC-08: `yamlgraph graph lint examples/api-discovery/steps/recon/graph.yaml` is run and recorded in `tmp/draft-authoring-report.md`.
- [x] AC-09: A narrow smoke command is run with concrete variables and recorded; if blocked by missing `gh` auth, the exact command and blocker are recorded without claiming a pass.
- [x] AC-10: FR-787 does not modify the orchestrator or make FR-791 require recon.

## Conditions for Enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement FR-787 until FR-783's `gh_code_search.tool.yaml` exists and loads from a consumer graph. | GATE |
| C-2 | Use the graph-authoring adapter route for governed graph artifacts; do not author `graph.yaml` or prompt artifacts manually from the requesting session. | GATE |
| C-3 | Do not claim smoke success when GitHub CLI authentication or network access blocks the recon smoke; record the blocked command and reason instead. | GATE |
| C-4 | Do not change orchestrator routing or other API discovery steps under this FR. | GATE |

## Related

- FR-783 (gh_code_search manifest — the tool this agent uses)
- FR-791 (orchestrator — the consumer)
- `docs/adaptive-probing-plan.md` §4.1

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.

**Judgement revisions folded:** R-1 (dependency gate on FR-783 `gh_code_search.tool.yaml`), R-2 (mechanical `ReconResult` validation with evidence source-identity requirement), R-3 (authoring-report validation contract with honest blocked-smoke handling), R-4 (recon frozen as optional; no orchestrator coupling) — see `feature-requests/FR-787-api-discovery-recon-step.judgement.md`.

## Implementation Record (2026-08-15)

- C-1 verified before authoring: `gh_code_search.tool.yaml` validates as
  `ToolManifest`; FR-783 suite 17/17 green (`logs/fr787-dep-check.log`).
- Authored via the sole route: `scripts/author.sh tmp/fr-787-authoring-brief.md`
  (copilot adapter, exit 0). `tmp/draft-authoring-report.md` is substantive:
  precedent `endpoint-probe` adapted; four honest prompt repairs recorded
  (nested evidence objects → strings, loop exhaustion → synthesis reserve,
  missing keys → four-key self-check, brace/templating conflict → brace-free
  shape description); Blocked validation: none.
- Artifacts: `steps/recon/graph.yaml` (single agent node, `max_iterations: 8`),
  `steps/recon/prompts/recon.yaml` (`output_schema:` JSON-Schema dialect per
  FR-795 precedent; four required string arrays; `additionalProperties: false`),
  `steps/recon.tool.yaml` (graph runtime → `recon/graph.yaml`,
  `output_key: recon_result`).
- Lint re-verified independently: no issues. Independent live smoke
  (`logs/fr787-smoke.log`, hypothesis "Finnish health statistics API sotkanet
  thl.fi"): agent completed in 5 iterations; `recon_result` carried nine
  candidate URLs including `https://sotkanet.fi/rest/1.1/indicators`, no-auth
  hints, JSON/CSV schema hints, and evidence strings in
  `repo=...; path=...; url=...; note=...` format — the value statement's THL
  Sotkanet case reproduced live.
- Tests: `tests/unit/test_fr787_recon_step.py` 15/15 green (REQ-YG-592,
  CAP-231); includes `load_and_compile` witness, Pydantic build from the
  prompt's own schema, empty-result validation, and orchestrator-absence
  check (AC-10). `req_coverage --strict` passes.
- Deviation from original plan: none; scope stayed inside judgement D-1..D-5.
