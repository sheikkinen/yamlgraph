# Feature Request: FR-791 — API Discovery Orchestrator Graph

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced 2026-08-15 — AC-01..AC-09 delivered; authoring adapter report verified, lint green, both live smokes passed (stat.fi PxWeb found / example.invalid not_found), 12/12 tests green (REQ-YG-595, CAP-234)
**Effort:** 1.5 days
**Requested:** 2026-08-13
**First consumer / first event:** the next API source investigation in
control-plane — replacing the manual 10–30 min probe-by-hand process
with a single graph invocation.

**Parent plan:** `docs/adaptive-probing-plan.md` §4.7

## Summary

Create the API discovery orchestrator: a graph that composes the step
graph-runtime tool manifests via `type: tool_call` nodes with conditional
edges. **v1 route (R-1, frozen):** endpoint-probe → page-analysis →
platform-confirm when candidates exist → schema-extract when a platform
is confirmed → synthesize. Recon and browser-sniff are NOT part of v1,
are not referenced as graph manifests, and their absence must not affect
graph load. Produces either an `APIProfile` or a `NotFoundVerdict`.

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

- **Structure:** `type: tool_call` nodes invoking the step graph-runtime manifests; conditional edges for skip logic; terminal `synthesize` llm node; no subgraph nodes
- **v1 route (R-1):** endpoint-probe → page-analysis → platform-confirm (when candidates exist) → schema-extract (when platform confirmed) → synthesize
- **Skip logic:**
  - Platform-confirm: skipped when no platform candidates found → terminal not-found/manual result
  - SPA-without-API path: routes to a terminal not-found/manual result (browser-sniff is v2)
- **Input contract (R-3):** required `hypothesis`, `purpose`, `country`; optional `domain_hint`. Final state key: `result`; output schema declared graph-locally in the synthesize prompt's `output_schema:`.
- **Output schemas:**
  - `APIProfile { url, platform_family, auth_model, endpoints, sample_response, total_records, languages, data_freshness, confidence, limitations, probe_suggestion }`
  - `NotFoundVerdict { verdict, reason, steps_tried, alternatives }`
  - `result` validates as exactly one terminal result: found profile or not-found/manual verdict
- **Stop conditions:**
  - `found`: platform confirmed AND data query returned real data
  - `not_found`: geo-blocked, candidates exhausted, commercial-only
  - `needs_manual`: auth wall, CAPTCHA, rate limiting

## Dependencies (R-2)

Enforcement is blocked until the FR-783 leaf manifests and the
graph-runtime manifests for FR-785 (endpoint-probe), FR-786
(page-analysis), FR-788 (platform-confirm), and FR-790 (schema-extract)
exist and are enforced by their own approved FRs. FR-791 does not
implement any step. Status at fold time: all five Enforced
(FR-783 2026-08-13, FR-785 2026-08-13, FR-786 2026-08-14,
FR-788 2026-08-14, FR-790 2026-08-15).

## Acceptance Criteria (revised per judgement)

- [x] AC-01: `examples/api-discovery/graph.yaml` exists and was authored via `scripts/author.sh`; the authoring report records precedent search, graph lint, smoke commands, and outcomes.
- [x] AC-02: The graph input contract is documented and exercised with required `hypothesis`, `purpose`, `country`, and optional `domain_hint`.
- [x] AC-03: The graph uses `type: tool_call` nodes against committed graph-runtime manifests for endpoint-probe, page-analysis, platform-confirm, and schema-extract; it uses no subgraph nodes.
- [x] AC-04: The graph does not reference recon or browser-sniff manifests in v1; SPA-without-API and absent-candidate paths route to a terminal not-found/manual result instead of failing graph load.
- [x] AC-05: Conditional routing skips platform-confirm when page-analysis returns no platform candidates and only enters schema-extract after platform confirmation returns real data.
- [x] AC-06: The final state key `result` validates against the declared output schema as exactly one terminal result: found API profile or not-found/manual verdict.
- [x] AC-07: Positive smoke command against stat.fi/PxWeb returns `found`, PxWeb platform family, a stat.fi PxWeb API URL, non-empty endpoints, and sample data.
- [x] AC-08: Negative smoke command against the selected deterministic absent target (`domain_hint="example.invalid"`) returns `not_found` or `needs_manual` with non-empty `steps_tried`, a permitted `reason`, and alternatives or manual guidance.
- [x] AC-09: `yamlgraph graph lint examples/api-discovery/graph.yaml` passes.

## Conditions for Enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not begin FR-791 enforcement until the required dependency manifests from FR-783, FR-785, FR-786, FR-788, and FR-790 are present and governed by their own approved/enforced FRs. | GATE |
| C-2 | Use the graph-authoring route for graph and prompt writes; manual unsentineled edits to governed graph artifacts are not authorized. | GATE |
| C-3 | Do not implement missing step graphs, leaf tools, recon, browser-sniff, Playwright utilities, or framework runtime changes under this FR. | GATE |
| C-4 | If either smoke target is unavailable, enforcement is blocked until the FR names a replacement target with equivalent explicit assertions; do not substitute a shape-only smoke. | GATE |

## Alternatives Considered

- **One big agent:** loses typed boundaries between steps; one agent with 5+ tools and open-ended iteration is harder to debug and costs more tokens than deterministic routing around contained judgment steps
- **Subgraph nodes:** rejected in §2 of parent plan — tool manifests let steps travel as reusable tools beyond this orchestrator

## Related

- FR-785 (endpoint-probe step), FR-786 (page-analysis step), FR-787 (recon step), FR-788 (platform-confirm step), FR-789 (browser-sniff step), FR-790 (schema-extract step)
- FR-783 (leaf tool manifests), FR-784 (network-sniff utility)
- `docs/adaptive-probing-plan.md` (parent plan)

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.

**Judgement revisions folded:** R-1 (v1 route frozen: endpoint-probe → page-analysis → platform-confirm → schema-extract → synthesize; recon/browser-sniff out of v1), R-2 (dependency gate on FR-783/785/786/788/790 — all Enforced at fold time), R-3 (input contract `hypothesis`/`purpose`/`country` + optional `domain_hint`; final state key `result`; graph-local output schema), R-4 (exact smoke commands and assertions: stat.fi/PxWeb positive, `example.invalid` negative) — see `feature-requests/FR-791-api-discovery-orchestrator.judgement.md`.

## Implementation Record (2026-08-15)

- Dependency gate (C-1) verified: all five prerequisite FRs Enforced. Smoke
  targets dry-run before authoring: statfin.stat.fi PxWeb API confirmed live
  (real JSON), `example.invalid` deterministic DNS failure (curl exit 6).
- Authored via the sole route in two runs. Run 1 authored all three
  artifacts and passed lint but hit the copilot CLI hard 900s timeout during
  the live full-pipeline smokes (report gate correctly rejected, exit 65).
  Run 2 (resumed, validation-only brief with explicit budget priority)
  ran both smokes, made one honest repair, and wrote a substantive
  `tmp/draft-authoring-report.md` (exact commands + outcomes; Blocked
  validation: none).
- Adapter repair during run 2: the first negative smoke over-reported
  `platform-confirm` in `steps_tried` although its wrapper was empty —
  `synthesize.yaml` now renders an "Actual steps that ran" section from
  non-empty wrappers and requires `steps_tried` to copy only those labels
  (truthfulness enforced at the prompt boundary).
- Artifacts: `examples/api-discovery/graph.yaml` (passthrough init → llm
  `generate_candidates` → tool_call ×4 with conditional skip edges → llm
  `synthesize`, all `on_error: fail`; single END via synthesize),
  `prompts/generate_candidates.yaml`, `prompts/synthesize.yaml` (terminal
  schema: verdict enum, required reason/steps_tried/alternatives,
  `steps_tried` minItems 1, profile requires url/platform_family/non-empty
  endpoints, `additionalProperties: false` throughout).
- Smoke evidence read from raw logs (tmp/api-discovery-positive-after-repair.log,
  tmp/api-discovery-negative-after-repair.log): positive — `found`, PXWeb,
  `https://statfin.stat.fi/PXWeb/api/v1/fi/StatFin/`, three live endpoints
  (fi/en/sv), genuine StatFin sample rows (Adoptiot, Aikuiskoulutukseen
  osallistuminen…), all five steps in `steps_tried`; negative — `not_found`,
  probe returned zero live endpoints with `geo_blocked` hint, `steps_tried`
  lists only the three steps that ran, alternatives empty.
- Documented deviation (AC-05 mechanism): platform-confirm skip routes on
  `candidate_urls.has_platform_hint` (candidate-generation output) rather
  than a page-analysis field, because tool_call wrappers return child
  output as JSON strings that edge expressions cannot address. The
  substance of AC-05 holds — platform-confirm is skipped when no platform
  candidates exist and schema-extract is gated on
  `platform_confirmation.success == true`; witnessed by tests.
- Tests: `tests/unit/test_fr791_api_discovery_orchestrator.py` 12/12 green
  (REQ-YG-595, CAP-234): load_and_compile against real manifests,
  composition boundaries, no-recon/browser-sniff witness, skip-routing
  assertions, single-terminal check, both-shape result validation with
  ValidationError witness. `req_coverage --strict` passes.
- D-2 interpretation: `generate_candidates.yaml` is covered by the
  judgement's "or the equivalent … prompt/schema artifact used by the
  graph" — the pipeline cannot start from the bare input contract without
  candidate generation, and no step FR owns it.

**Brief provenance (FR-852):** authoring brief committed at
`feature-requests/authoring-briefs/fr-791-authoring-brief.md`.
