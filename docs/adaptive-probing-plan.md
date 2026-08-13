# Adaptive API Discovery — Plan

**Date:** 2026-08-13
**Status:** Plan — each component has its own FR (see §6 index)
**Purpose:** Define a family of YAMLGraph graphs for automated API discovery — an orchestrator composing agentic investigation steps, each packaged as a reusable graph-runtime tool manifest (FR-768).

---

## 1. Problem Statement

Every source probe starts with the same manual process: "I think an API exists at {domain} for {purpose}. Let me figure out how to access it." Observed across 50+ source investigations in 5 countries, it is:

- Repeatable (same steps every time)
- Parameterizable (different domain/purpose, same method)
- A mix of deterministic probing (curl, grep) and judgment (try alternatives, interpret errors)
- Time-consuming manually (~10–30 min per source)

**Goal:** a hypothesis in, a structured API profile out — or a documented `not_found` verdict with reasons and alternatives.

---

## 2. Technology Selections

Each decision records the rejected alternative and why it lost.

**Agent nodes over copilot nodes.** Both can drive adaptive retry loops. Agent nodes keep the implementation *inside the example* — tools, prompts, and iteration budget are all declared in the graph artifact, self-contained and runnable with only provider API keys. Copilot nodes delegate to an external CLI session: heavier, harder to reproduce, and the reasoning happens outside the artifact. Copilot remains the fallback if a step turns out to need filesystem/repo-level agency beyond declared tools.

**Graph-runtime tool manifests over subgraph nodes.** These investigation steps feel reusable beyond this orchestrator — recon is a general "who solved this before?" primitive; endpoint-probe is generic liveness checking. A `*.tool.yaml` manifest with `runtime.type: graph` makes each step a named, described, reusable tool — invocable deterministically by the orchestrator via `type: tool_call`, *and* available to any future agent as part of its toolbox. Subgraph nodes bind the step to one parent's wiring; manifests let it travel. `input_mapping`/`output_key` on the graph runtime give the same state-mapping semantics. Subgraph remains the fallback where streaming or shared-checkpoint resume across the boundary is required — tool invocation is invoke-only.

**Shared leaf tool manifests over inline `tools:` blocks.** Same reuse argument one level down. Individual steps will likely surface more tools than the initial set as authoring proceeds (e.g., `dns_lookup`, `robots_txt_fetch`, `jq_extract`, `feed_probe`, `har_filter`); each new one lands as a manifest so later steps and unrelated graphs inherit it for free. Inline declarations only for genuinely one-off commands.

**Net shape: everything below the orchestrator is a tool.** Investigation steps are graph-runtime tools composed of agent nodes; agent nodes consume shell/python-runtime tools. The orchestrator is the only piece not packaged as a tool — until a higher-order research agent needs `api_discovery.tool.yaml`, at which point it becomes one too.

---

## 3. Architecture

```
examples/api-discovery/
├── graph.yaml                          orchestrator — routing + synthesis only
├── steps/
│   ├── recon.tool.yaml                 → runtime: {type: graph, path: recon/graph.yaml}
│   ├── endpoint_probe.tool.yaml        → runtime: {type: graph, path: endpoint-probe/graph.yaml}
│   ├── page_analysis.tool.yaml         → runtime: {type: graph, path: page-analysis/graph.yaml}
│   ├── browser_sniff.tool.yaml         → runtime: {type: graph, path: browser-sniff/graph.yaml}
│   ├── platform_confirm.tool.yaml      → runtime: {type: graph, path: platform-confirm/graph.yaml}
│   ├── schema_extract.tool.yaml        → runtime: {type: graph, path: schema-extract/graph.yaml}
│   ├── recon/graph.yaml                agent graph
│   ├── endpoint-probe/graph.yaml       agent graph
│   ├── page-analysis/graph.yaml        agent graph
│   ├── browser-sniff/graph.yaml        agent graph
│   ├── platform-confirm/graph.yaml     agent graph
│   └── schema-extract/graph.yaml       llm graph (promote to agent if needed)
└── tools/
    ├── curl_probe.tool.yaml            shell manifest
    ├── fetch_page.tool.yaml            shell manifest
    ├── gh_code_search.tool.yaml        shell manifest
    ├── network_sniff.tool.yaml         shell manifest (wraps network-sniff.js)
    ├── network-sniff.js                Playwright XHR capture utility
    └── parse_openapi.tool.yaml         python manifest
```

### Division of responsibility

| Layer | YAMLGraph primitive | Owns |
|-------|--------------------|------|
| Orchestrator | `type: tool_call` on graph-runtime step manifests + conditional edges | Sequencing, skip logic, state hand-off, final synthesis |
| Investigation step | own graph with `type: agent` node + shared tool manifests, packaged as a `runtime.type: graph` tool manifest | Adaptive retry, strategy selection, evidence interpretation |
| Probe action | shell/python tool manifest | One deterministic side effect, sanitized, timeboxed |

### Why agents inside each step

The retry logic ("403 → try different User-Agent; 404 on /api → try /api/v1, /rest, /graphql; 200-but-HTML → parse for API links") is LLM-mediated tool iteration. Encoding it as YAML branches would reproduce the `regex_fourth_exclusion` trap — a special case per failure mode, forever incomplete. The agent gets the strategies as prompt doctrine, the tools as manifests, and a hard `max_iterations` budget.

### Why an orchestrator, not one big agent

Each step graph has a **typed output contract** (Pydantic schema at the boundary — Commandment 5), keeping evidence normalized where it enters the next step. The orchestrator's routing is deterministic and cheap; the expensive judgment stays contained per step.

---

## 4. Step Briefs

Each step is its own graph + graph-runtime tool manifest. This document contains **no graph YAML** — actual graphs are authored through `scripts/author.sh` per the graph-authoring doctrine. Each section is a task brief, not an implementation.

### 4.1 `recon` — GitHub Code Search (FR-787)

- **Input:** `hypothesis`, `domain_hint?`, `purpose`, `country`
- **Tools:** `gh_code_search` (manifest)
- **Behavior:** generate search-term variants (domain forms, service names, country conventions); iterate `gh search code` queries; mine hits for API URLs, auth patterns, client packages, response schemas. Other developers are the best documentation — THL Sampo's hidden JSON-stat endpoint was found this way.
- **Output schema:** `ReconResult { candidate_urls: list[str], auth_hints: list[str], schema_hints: list[str], evidence: list[str] }`
- **Failure mode:** empty result is valid (`on_error: skip` at orchestrator level) — not every source has GitHub footprints.

### 4.2 `endpoint-probe` — DNS / URL Pattern Probing (FR-785)

- **Input:** `candidate_urls` (recon + generated patterns: `api.{domain}`, `{domain}/api[/v1..v3]`, `/swagger.json`, `/openapi.json`, `/api-docs`, `/rest`, `/graphql`, `data.{domain}`, `open.{domain}`)
- **Tools:** `curl_probe` (manifest)
- **Behavior:** adaptive retry doctrine in the prompt:
  - `000` timeout → www/no-www, HTTP fallback; 3+ timeouts → `geo_blocked`
  - `403` → alternate User-Agent, drop Accept-Encoding, detect WAF challenge
  - `404 /api` → version/path variants, trailing-slash, follow relocation redirects
  - `200` HTML → portal page, not API: hand off to page-analysis
  - XML → OData (`?$format=json`), SOAP, RSS/Atom discrimination
- **Output schema:** `ProbeResult { live_endpoints: list[EndpointHit], html_pages: list[str], verdict_hint: str | None }`
- **Note:** first probing pass over the fixed pattern list could be a `type: map` fan-out feeding the agent (feeder pattern, FR-773) — decide at authoring time.

### 4.3 `page-analysis` — Page Source Inspection (FR-786)

- **Input:** `html_pages` from endpoint-probe
- **Tools:** `fetch_page` (manifest)
- **Behavior:** extract `<script src>` bundles, inline `fetch()`/`axios` URLs, feed links, Swagger UI includes, `data-api-url` attributes, `wp-json` refs. Fingerprint platforms: PxWeb, CKAN (`/api/3/action`), Liferay (`p_p_id`), JSF (`ViewState`), SwaggerUI, OData, EntryScape. Platform catalog supplied via `data_files`, not hardcoded in the prompt.
- **Output schema:** `PageAnalysis { api_found: bool, is_spa: bool, platform_candidates: list[str], api_urls: list[str] }`

### 4.4 `browser-sniff` — Playwright Network Capture (FR-789)

- **Trigger:** orchestrator routes here only when `api_found == false AND is_spa == true` — the expensive last resort. Handles SPAs that hide APIs behind client-side rendering.
- **Tools:** `network_sniff` (manifest; wraps `network-sniff.js`)
- **Behavior:** load page headless, capture XHR/fetch, filter to JSON/XML, identify data-carrying requests vs telemetry, extract URL patterns and auth tokens.
- **Output schema:** `SniffResult { api_calls: list[CapturedRequest], auth_required: bool }`
- **Failure mode:** auth token / CAPTCHA discovered → `needs_manual` verdict hint, not an error.

### 4.5 `platform-confirm` — Family Confirmation (FR-788)

- **Input:** platform candidates + base URLs from previous steps
- **Tools:** `curl_probe` (reused manifest — one tool, four consumers)
- **Behavior:** targeted confirmation per family — CKAN `status_show`/`package_search?rows=0`, PxWeb `/api/v1/{lang}/{db}`, OData `?$top=1&$format=json`, OpenAPI spec fetch, WordPress `/wp-json/wp/v2/types`, JSON-stat `{cube}.json`. Confirmed = platform query returned **real data**, not just 200 (`plausible_wrong_answer` guard — assert substance, not shape).
- **Output schema:** `PlatformConfirmation { family: str, base_url: str, confirmed: bool, sample_response: str }`

### 4.6 `schema-extract` — Capability Extraction (FR-790)

- **Input:** confirmed platform + sample responses
- **Behavior:** OpenAPI → parse endpoints/methods/params (`parse_openapi` python manifest); CKAN → dataset count, top orgs; PxWeb → subject tree, one table's variables; custom → sample 1–3 responses, infer schema. Record auth model, rate limits, freshness (latest timestamp in sample data), languages.
- **Output schema:** `CapabilityReport` (fields mirror final profile)
- Start as `llm` node with `tool_call` pre-steps; promote to agent only if sampling proves adaptive.

### 4.7 Orchestrator — `api-discovery` (FR-791)

- **Input:** `hypothesis`, `domain_hint?`, `purpose`, `country`
- **Structure:** `type: tool_call` nodes invoking the step graph-runtime manifests; conditional edges implementing skip logic (browser-sniff only when `is_spa == true AND api_found == false`; platform-confirm skipped when nothing found); terminal `synthesize` llm node.
- **Output:** exactly one of `APIProfile` or `NotFoundVerdict`:

```json
{
  "url": "https://api.example.dk/v2/",
  "platform_family": "custom_rest",
  "auth_model": "none",
  "endpoints": ["search", "lookup/{id}", "metadata"],
  "sample_response": {},
  "total_records": 50000,
  "languages": ["da", "en"],
  "data_freshness": "2026-08-11",
  "confidence": "high",
  "limitations": ["no bulk export", "rate limited"],
  "probe_suggestion": "curl -s {url}/search?q={term} | jq ..."
}
```

```json
{
  "verdict": "not_found | needs_manual",
  "reason": "geo_blocked | commercial | no_api | spa_only | auth_wall | captcha",
  "steps_tried": [],
  "alternatives": ["commercial reseller X", "try from local IP"]
}
```

- **Stop conditions** (enforced by orchestrator routing + per-agent `max_iterations`):
  - `found`: platform confirmed AND data query returned real data, or OpenAPI spec with 3+ endpoints
  - `not_found`: geo-blocked (3+ timeout retries), candidates exhausted, only commercial/session-bound endpoints
  - `needs_manual`: auth token required, CAPTCHA, rate limiting prevents confirmation

---

## 5. Tool Manifest Library

Shared under `examples/api-discovery/tools/`. Each per FR-768 schema: `name` + `description` + `runtime`.

| Manifest | Runtime | FR | Command / function sketch | Consumers |
|----------|---------|-----|---------------------------|-----------|
| `curl_probe.tool.yaml` | shell | FR-783 | `curl -s --max-time 10 -w '{"status":%{http_code},…}' {url}` + body head; UA param | endpoint-probe, platform-confirm, page-analysis |
| `fetch_page.tool.yaml` | shell | FR-783 | `curl -sL` full page fetch, UA override | page-analysis |
| `gh_code_search.tool.yaml` | shell | FR-783 | `gh search code {query} --limit 20 --json path,repository,textMatches` | recon |
| `parse_openapi.tool.yaml` | python | FR-783 | spec JSON → endpoint inventory (deterministic; no LLM) | schema-extract |
| `network_sniff.tool.yaml` | shell | FR-784 | `node network-sniff.js {url} --timeout 10000` | browser-sniff |

All runtime variables pass through existing `shlex.quote()` sanitization; manifests validate at graph load, never at invocation. Additional tools will surface during authoring — each lands as a manifest so later steps inherit it.

---

## 6. Sub-FR Index

| FR | Component | Type | Depends on | Status |
|----|-----------|------|------------|--------|
| FR-783 | Shared leaf tool manifests (curl_probe, fetch_page, gh_code_search, parse_openapi) | Example | FR-768 | Proposed |
| FR-784 | Playwright network sniff utility (network-sniff.js + network_sniff.tool.yaml) | Example | FR-768 | Proposed |
| FR-785 | Endpoint-probe step graph | Example | FR-783 | Proposed |
| FR-786 | Page-analysis step graph | Example | FR-783 | Proposed |
| FR-787 | Recon step graph | Example | FR-783 | Proposed |
| FR-788 | Platform-confirm step graph | Example | FR-783 | Proposed |
| FR-789 | Browser-sniff step graph | Example | FR-784 | Proposed |
| FR-790 | Schema-extract step graph | Example | FR-783 | Proposed |
| FR-791 | API discovery orchestrator | Example | FR-785..FR-790 | Proposed |

Upstream dependencies (already enforced): FR-768 (tool manifests), FR-773 (feeder pattern).

---

## 7. Implementation Order

1. **FR-783** — leaf tool manifests first (smallest, multi-consumer); validate with a trivial consumer graph
2. **FR-785** — endpoint-probe: the core adaptive loop; test against known-good Finnish sources
3. **FR-786 + FR-788** — page-analysis + platform-confirm: completes the static-analysis path
4. **FR-791 v1** — orchestrator composing steps 2–3 with synthesis; skip recon and browser-sniff initially
5. **FR-784 + FR-789** — network-sniff.js + browser-sniff: the only non-YAML deliverable
6. **FR-787** — recon: GitHub search last; highest variance, orchestrator tolerates its absence
7. **Unknown-source test** — run against an unexplored country (Norway?) as honest validation

Each graph goes through the authoring doctrine (`scripts/author.sh`): precedent search, lint, smoke, validation record. Precedents: `examples/demos/shared-vision-tool` (manifest consumption), `examples/demos/book-summary` (feeder pattern), `subgraph_demo`, `git_report` (agent + subgraph patterns).

---

## 8. Composition Patterns

The orchestrator is the foundation primitive; higher-order graphs compose it:

```
api-discovery            (this plan — atomic operation)
    ↑ tool_call ×7       country-exploration    (statistics, companies, procurement, …)
    ↑ tool_call ×n       sector-research        (health: patient/drug/professional registries)
    ↑ map ×countries     multi-country-sweep
    + code-gen node      auto-probe-generator   (profile + template → working probe script)
```

Value propositions (field experience): source verification ~2 min, probe generation ~3 min, country mapping ~10 min, change detection (profile diff) ~5 min — versus 10–30 min manual per source.

---

## 9. Follow-Up

- **FR-792 Multi-Step Investigation Template:** Can the step graph → tool manifest → orchestrator pattern be extracted as a reusable scaffold? The shape recurs beyond API discovery (company research, codebase audit, incident investigation). FR-792 proposes a generator that produces the orchestrator + N step stubs + shared tool directory from a step-name list, so the next investigation pipeline starts from structure, not from scratch.

---

## 10. Open Questions

- **Manifest home:** per-example `tools/` vs `examples/shared/` — decided by whether other example families adopt `curl_probe`.
- **Map-then-agent vs agent-only** in endpoint-probe (§4.2) — measure token cost of agent-driven probing over the fixed pattern list first (`read_raw_output_first` applies: read the agent transcripts before optimizing).
- **Platform catalog transport:** `data_files` per step graph vs orchestrator-level injection into child state.
- **Checkpointing:** whether country-level sweeps need SQLite checkpointer resume across tool invocation boundaries.
- **Home repo:** these graphs serve the control-plane repo's mission; decide whether they land here as `examples/api-discovery/` (framework demo) or in control-plane consuming yamlgraph as a dependency.
