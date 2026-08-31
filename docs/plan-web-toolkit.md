# Plan: Web Toolkit — Overview

**Date:** 2026-08-31 (rev 10 — C sources researched live: NO public bulk .fi
list exists (Traficom claim corrected); seed = CC host-graph ∪ CT; fetch route
= index-driven WARC byte-ranges, WET demoted — see
`docs/plan-research-fi-catalog-sources.md`. rev 9 — C cost control: mercury-2
pinned as classifier, LangSmith tracing off at scale via runner script. rev 8
— D grounded in LangGraph natives; map node audited — hardening extracted to
FR-936. rev 7: sibling repos unpark B; rev 6: value audit; rev 5: SPA
rendering; rev 4: converter comparison; rev 3: C primary, D promoted)
**Status:** Draft (pre-FR)
**Scope:** A TLD-scale classification pipeline (C, primary), a resumable
storage-backed map primitive (D, keystone), a text-render graph tool (A), and
a HAR→OpenAPI graph (B) — the last three unblocked by a named production
consumer (hva-weekly-bulletin) and 40+ probe scripts (control-plane) that
document exactly the pain B eliminates.

## Vision

Catalog and classify an entire country-code domain (*.fi) with a YAMLGraph
pipeline, and turn the Finnish gov/municipal probe suite (bespoke shell
scrapers today) into machine-generated OpenAPI specs consumed by production
YAMLGraph pipelines. The build forces two durable framework assets into
existence: a fetch-as-text tool usable inside any graph, and a map primitive
that survives 500k-item runs.

## Priority Order

1. **C — .fi TLD catalog**: the primary analysis focus and the driving use case.
2. **D — resumable storage-backed map**: new framework primitive C requires;
   likely the most durable output for the repo. Prerequisite: FR-936 map
   hardening (rev 8).
3. **A — lynx_render**: graph tool consumed by C's live-fetch tier and by any
   future research graph.
4. **B — har-to-spec**: unparked (rev 7) — named consumers and first HARs
   identified; still sequenced last because D + A come first.

## Named Consumers (rev 7)

The sibling repo suite closes the "for whom" gap for every component except D
(whose consumer is the other three):

| Sibling | Role | Wants from this plan |
|---------|------|----------------------|
| **`hva-weekly-bulletin`** (production, remote) | Weekly YAMLGraph pipeline over 22 HVAs via KTweb, Dynasty, CaseM + Hilma + TED + Market Court. Emits Monday bulletin. | **B**: machine-generated OpenAPI specs for KTweb/Dynasty/CaseM (currently hand-written probes). **C**: platform census tells it which HVAs use which platform. |
| **`control-plane/probes`** (local, 40+ scripts) | Bespoke shell scrapers: `casem-playwright-probe.js`, `dynasty-drequest-probe.sh`, `ktweb-probe.sh`, `hilma-probe.sh`, `eduskunta-probe.sh`, ... | **B**: replace hand-written probes with generated OpenAPI + typed clients. **A**: many probes today are `curl ... \| iconv ... \| regex` — a `lynx_render`-style tool would collapse a lot of that. |
| **`gitclaw-oulu-civic-intelligence`** (production, remote) | YAMLGraph civic-intelligence template, Oulu focus. | **C**: Oulu-region subset of the catalog as ready-made input. **B**: same probe-generation benefit for civic-data endpoints. |

**Consequence for the plan**: B is no longer speculative. The concrete first
HARs are one Dynasty DREQUEST session and one CaseM Playwright trace — both
platforms host 8-22 instances behind identical URL patterns, so one HAR
generates a spec that serves the whole tenant fleet. Multi-tenant leverage is
B's differentiator over generic HAR→OpenAPI.

## Value Audit (forced_opposite, rev 6+7)

| | Value of the output | Would yamlgraph add value? |
|--|--|--|
| **D** | Intrinsic and highest: item-durable resumable fan-out is a genuine gap. Named consumers: C pilot, B's map stage, hva-weekly-bulletin's daily collection. | **D *is* yamlgraph value** — the keystone. |
| **C** | External but named: platform census is what hva-weekly-bulletin already does bounded to 22 orgs — C generalizes it to 550k domains. Value in the **data**, not the pipeline. | **Only via D.** Standalone C is a script. As "the workload that forces D and produces the census hva-weekly-bulletin will consume," it earns its keep. |
| **A** | Marginal: `fetch_page` (api-discovery) already exists; the delta is dump quality, link inventory, `render` signal. **Rev 7**: control-plane probes' encoding tax (ISO-8859-1, UTF-16-LE, KTweb anti-copy spacing) shows a real dump-normalization gap `fetch_page` may not cover. | Neutral → mild positive on the encoding evidence. FR still opens with the delta-vs-fetch_page gate; encoding fixtures are now on the table. |
| **B** | **Rev 7 — no longer speculative**: production consumer (hva-weekly-bulletin), 40+ pain-point probes, multi-tenant leverage (one HAR → 8-22 instance clients), differentiators over m2s/har-to-openapi (encoding, tenant templating). | Yes: parallel LLM map over endpoint groups replacing m2s's human curation is the textbook yamlgraph shape, and D's map primitive is the natural runtime. |

## Prior Art (dispositioned)

| Artifact | FR | Relation |
|----------|----|----------|
| `examples/demos/fi_domain_crawl` | FR-204 | Shipped crawl-and-summarise demo (httpx + BeautifulSoup, map fan-out, LLM synthesis). C evolves this — refit, don't duplicate. |
| `examples/api-discovery` | FR-783..790 | Tool manifests `fetch_page`, `curl_probe`, `parse_openapi`; step graphs. A's tool lives beside these manifests; CAP-226's SPA-shell/browser-sniff distinction is the precedent for A's JS policy. **`fetch_page` is also A's potential duplicate — see A's delta gate.** |
| `examples/daily_digest/nodes/content.py` | — | BS4 extraction; its committed `digest.db` dedup is the precedent for C's incremental re-crawl. |
| map `max_items` + CAP-120 inter-run state chaining + SQLite checkpointer | — | The current workaround stack D replaces with a primitive. Map node audited rev 8 — hardening extracted to **FR-936**. |
| **LangGraph natives: `@task` checkpointing, `CachePolicy`, `Send` pending-writes, `durability="sync"`, `Store`** | — | Verified against current docs (rev 8): most of D's contract exists natively, unassembled. See D's coverage table. |
| **`../control-plane/probes/*` (sibling repo, 40+ scripts)** | — | Working scrapers for Finnish gov/municipal platforms — CaseM (Playwright SPA), Dynasty DREQUEST, KTweb, Hilma, eduskunta, Kela, Fingrid, Digitraffic, etc. These *are* the corpus B replaces with machine-generated specs; they also *are* the encoding-tax evidence for A. First HAR candidates for B live here. |
| **`../hva-weekly-bulletin` (sibling repo, production)** | — | Live YAMLGraph consumer over 22 HVAs; consumes B's would-be specs and C's would-be platform census. Closes the "for whom" gap for both. |
| **`../gitclaw-oulu-civic-intelligence` (sibling repo, production)** | — | YAMLGraph civic-intelligence template; second consumer for B and C. |
| **Common Crawl (external): host web graph, columnar URL index, WARC/WET** | — | **Rev 10, probed live**: three-tier access — host-graph vertices (free .fi enumeration), parquet URL index (pre-filter columns: fetch_status, languages, charset, byte-range pointers), ranged WARC GETs for page content. Full access details in `docs/plan-research-fi-catalog-sources.md`. |
| **mitmproxy2swagger / har-to-openapi (external OSS)** | — | Deterministic HAR→OpenAPI converters exist; B wraps, does not reimplement. Compared in the B section. |
| **Jina Reader / Firecrawl / Crawl4AI / browser-use (external)** | — | "URL → LLM-ready text incl. JS" is an occupied product category. A's JS tier wraps Crawl4AI (or Playwright), never builds rendering. See "SPA rendering: product boundary". |

## Component C (primary): `.fi` TLD catalog — classify at country scale

Evolution of FR-204's demo into the toolkit's driving analysis pipeline.

- **Honest framing (rev 6)**: standalone, C is a script. C's value to the
  *repo* is that it forces D to exist and hands the framework a 500k-scale
  witness. The catalog dataset is the exhaust — but rev 7 gives that exhaust
  a live production consumer (hva-weekly-bulletin's 22-org list is the
  bounded version of C's platform census).
- **Sources (rev 10, corrected — full record in
  `docs/plan-research-fi-catalog-sources.md`)**: there is **no public bulk
  .fi domain list** — Traficom's avoindata dataset (CC-BY 4.0) exposes only
  per-domain search/WHOIS UIs, and the zone file is registrar-only. Seed =
  **CC host-graph vertices** (every observed .fi hostname, free HTTPS
  download) **∪ Certificate Transparency** hosts (crt.sh `%.fi`); Traficom's
  published *count* (~550k) survives only as the coverage denominator.
  Coverage is reported as an estimate against that count, never as a
  subtraction from a register we don't have.
- **v1 is Common Crawl, not crawling — route pinned (rev 10)**: the parquet
  URL index (`url_host_tld='fi'`; fetch_status, content_languages, charset
  columns) is a free pre-filter stage *before* any DNS/HEAD probe; page text
  comes via **index-driven WARC byte-range GETs**
  (`data.commoncrawl.org` + `Range:` header + warcio), not bulk WET
  streaming — WET is demoted to fallback (segment-organized, bandwidth-heavy
  for a single TLD, rougher encoding). Query route for the pilot:
  HTTPS-downloaded parquet partition + DuckDB (no AWS account, reproducible);
  Athena is the alternative at cents per TLD-filtered query. Latest crawl at
  research time: CC-MAIN-2026-34; crawls are ~monthly.
- **Pipeline**: seed (CC vertices ∪ CT) → **index pre-filter** (parquet:
  status, language, charset — free, rev 10) → deterministic live pre-filter
  (DNS resolve + HTTP HEAD, only for domains the index can't settle; LLM
  never sees dead sites) → **D-map**(text extract → LLM classify with inline
  schema: category, language, organisation type, **platform
  (CaseM/Dynasty/KTweb/other) — added rev 7 for B/hva-bulletin handoff**, API
  presence, liveness, `render: empty|thin|full`) → catalog artifact
  (SQLite/JSONL).
- **Cost model (required before scope freeze, rev 9)**: classifier pinned to
  **mercury-2** (`provider: inception`, already in the provider matrix) —
  diffusion-LM speed/price is what makes 550k × classify plausible; token cap
  per page dump; measured cost per 1k domains from a pilot batch. Pilot must
  also spot-check mercury-2 classification quality against a frontier-model
  sample (read_raw_output_first applies to the model choice, not just the
  prompt). No full run without the pilot number.
- **Runner script (cost control, rev 9)**: the full-scale run goes through a
  dedicated runner that forces `LANGCHAIN_TRACING_V2=false` — 550k traced
  node executions would swamp LangSmith and add per-call overhead for zero
  diagnostic value at that volume. Tracing stays ON for the pilot batch
  (Commandment 9 satisfied there); at scale, observability comes from D's
  progress JSONL + the catalog artifact itself. The runner owns the scale
  posture: tracing off, mercury-2 pinned, token caps, politeness limits —
  config as truth, not operator memory.
- **Evaluation (read_raw_output_first)**: before any aggregate accuracy claim,
  dump N classified samples with their source text and read them; spot-check
  accuracy criterion in the FR. An unaudited catalog is a liability. Ready
  eval set (rev 10): control-plane/hva tenant lists give ground-truth
  platform labels for the census columns.
- **Incremental semantics**: dedup + change detection + entry TTL (precedent:
  daily_digest's digest.db). Liveness re-check is deterministic and LLM-free.
- **Politeness constraints** (live-fetch tier only): robots.txt respect,
  per-host rate limits, identifying User-Agent — FR acceptance criteria. Also
  applies to CC community infra: identifying UA everywhere; parquet index,
  never the rate-limited CDX API, for bulk (rev 10).
- **Named consumer**: public-sector platform census (which municipalities and
  HVAs run CaseM/Dynasty/KTweb/CKAN/PxWeb/OData) — the census output feeds
  `hva-weekly-bulletin` and gates which B specs get generated first.

## Component D: resumable storage-backed map primitive

C at 500k items is a scale the map node has never seen; `max_items` +
CAP-120 chaining is a workaround, not a primitive. D makes it one.

**Keystone (rev 6)**: D is the only component whose value is intrinsic to
the framework — it survives even if C's full run is never funded (the
primitive pays for itself at 10k-item scale) and B never unparks.

### LangGraph-native coverage (rev 8, verified against current docs)

| D contract line | Native mechanism | Gap remaining |
|---|---|---|
| Item-level durability | `@task` inside a node: task results are checkpointed; resume skips completed task work. Plus `durability="sync"` invoke mode. | Results live in the **checkpoint blob** — at 500k items per-superstep state serialization is the bottleneck. Thread-scoped; task-order-sensitive on resume. |
| Resume-by-skip (cross-run) | Node/task caching: `CachePolicy(key_func=stable_item_id)` + persistent cache backend — cached item returns `{'__metadata__': {'cached': True}}` instead of re-executing; works **across threads/runs**. Alternative: the **Store** (cross-thread KV, SQLite/Postgres) as item-result home; skip = key-presence check. | Cache semantics are memoization — TTL/eviction become load-bearing if used as the result store. |
| Fan-out | `Send` — native map-reduce. **Pending-writes** already persist successful parallel branches within a failed superstep: mid-fan-out crash doesn't re-run completed siblings. | `Send` schedules **everything in one superstep** — no bounded batches, no concurrency cap. 500k Sends = unbounded memory. The genuinely missing piece. |
| Progress observability | `stream_mode="updates"` gives per-item completion events. | No queryable mid-run counts; needs FR-723-style JSONL. |

**Where LangGraph stops helping** (Open Question 1, answered): exactly two
places — bounded/chunked scheduling of the fan-out, and keeping 500k results
out of the state channel (write to Store, not state; reduce reads the Store).
Everything else — durability, skip, fan-out, crash-safe partial supersteps —
is native. D shrinks from "new `durable_map` node type" toward a **thin
composition**: chunked driver around `Send` batches + `CachePolicy`/Store
keyed by item id + `durability="sync"` + progress JSONL. Strong prior for the
FR: extend the existing map node with `durable:` options, don't invent a type.

### Existing map node audit (rev 8) → FR-936

`yamlgraph/compile/map_compiler.py` uses the canonical Send+reducer pattern,
but with two scale-hostile deviations and three missed natives — extracted to
**FR-936 (map node hardening)**, a prerequisite for D:

1. **Full-state copy per Send**: `Send(sub, {**state, item, index})` vs the
   docs' minimal per-item payload. Memory × fan-out; bloats every
   pending-write. Cure: declared inputs — pass only keys the sub-node's
   variables reference.
2. **Silent truncation at `max_items`**: `logger.warning` + slice. A 550k run
   "succeeds" with 1000 items — plausible_wrong_answer, Commandment 6. Cure:
   raise by default; truncation only as explicit config.
3. **Per-branch timeout leaks a thread**: one-shot pool +
   `shutdown(wait=False, cancel_futures=True)` abandons the running thread.
   At scale, zombie threads holding LLM connections.
4. **No `RetryPolicy`** surfaced on sub-nodes (hand-rolled `on_error` instead).
5. **No `CachePolicy`** surfaced at all (this one lands with D, not FR-936).

Free lunch already banked: with the SQLite checkpointer attached, pending
writes give partial in-run crash durability today — currently undermined by
deviation 1 making every write huge.

- **Contract sketch** (unchanged, now mapped to natives above): item-level
  durability; resume-by-skip keyed by stable item id (extends
  `skip_if_exists` to item level); chunked execution with bounded
  concurrency; progress observability.
- **Witness**: kill -9 mid-run at scale N, re-run, prove completed items are
  not re-executed and the final catalog is identical to an uninterrupted run.
- **Acceptance demos**: C's pilot; also hva-weekly-bulletin's daily collection
  over 22 orgs (smaller scale, higher operational frequency — validates
  resume semantics against a live cron).

## Component A: `lynx_render` — text-render tool for graphs

A graph tool (FR-768-style manifest), consumed by C's live-fetch tier and by
research graphs generally — fetch-as-text *inside* a graph, which the
chat-surface `fetch_webpage` is not.

- **fetch_page delta gate (rev 6)**: api-discovery already ships a
  `fetch_page` tool manifest. A's FR must open with the delta: either
  **extend fetch_page** (add dump rendering, link inventory, render signal)
  or show **same-page evidence** that a separate lynx tool is materially
  better. Without that evidence A is the duplicate — false_duplicate in
  reverse — and collapses into a fetch_page patch, size XS.
- **Encoding-tax evidence (rev 7)**: control-plane's Dynasty probes iconv
  ISO-8859-1→UTF-8; KTweb detail pages are **UTF-16-LE without BOM**; KTweb
  also injects anti-copy whitespace that has to be collapsed. If `fetch_page`
  doesn't already handle these, the delta is measurable and the FR writes
  itself. Fixtures from control-plane test data. Rev 10 adds: WARC-sourced
  page bytes carry the *original* server encoding — the same normalization
  boundary serves both live fetches and CC archive reads.
- **Form**: shell tool manifest wrapping `lynx -dump`; modes `-nolist`
  (reading text) and `-listonly` (numbered link inventory).
- **Boundary rules** (no silent fallbacks): fail fast if binary missing;
  normalize encoding; cap dump size; per-fetch timeout; Finnish-encoding
  witness fixtures (ä/ö ISO-8859-1, UTF-16-LE KTweb, anti-copy KTweb).
- **JS policy**: empty/thin dump is **a signal, not a failure** — returned
  tagged (`render: empty|thin|full`), classified downstream as "JS-required".
- **JS tier (disposition: wrap, don't build)**: rendering JS pages to text is
  an occupied product category (Jina Reader, Firecrawl, Crawl4AI ~40k stars,
  browser-use). If C's pilot shows the "JS-required" fraction matters, the
  escalation tier is a second tool manifest wrapping **Crawl4AI** (pip,
  Playwright-based, LLM-friendly markdown). Building a renderer is out of
  scope for yamlgraph permanently: by the three-layer doctrine a renderer is
  Layer 3 side-effect plumbing, not orchestration.
- **Fork for the judge**: lynx (system binary, better layout fidelity) vs
  html2text/trafilatura (pip dep, cheaper CI) — decided on same-page dump
  evidence, not preference. Jina Reader rejected: external service dependency.
- **Deliverable**: tool manifest + smoke demo graph (URL → dump → summarise).

### SPA rendering: product boundary

"Text rendering of SPA" *is* a product — but the one-shot URL→markdown slot
is taken (Jina Reader, Firecrawl, Crawl4AI). The unclaimed adjacent slot is
the actual **lynx UX for agents**: a persistent, navigable text browser —
numbered links, form fill, session state — exposed as tool calls. That is
lynx's interaction model reborn for LLM consumers (build-for-agents thesis
applied to the browser), distinct from both one-shot renderers and
browser-use-style automation. If pursued, it is a **separate repo/product**,
not a yamlgraph component; yamlgraph would be its first consumer (tool
manifest + the C census as demo workload) — the same relationship pattern as
ninchat_voice and the outcaller. Recorded here so the census work doesn't
scope-creep into building a browser.

## Component B: `har-to-spec` (unparked, rev 7)

Rev 6 parked B pending the "for whom / what pain / vs which alternative"
answer. Rev 7 has all three:

- **For whom**: `hva-weekly-bulletin` (production, remote) consumes probe
  outputs today via bespoke shell scripts. Generated OpenAPI specs replace
  those scripts. `control-plane`'s 40+ probes are the second consumer.
  `gitclaw-oulu-civic-intelligence` the third.
- **What pain**: no vendor of CaseM, Dynasty DREQUEST, or KTweb publishes an
  OpenAPI spec. Each new HVA/municipality onboarding today = a hand-written
  probe with encoding hacks and HTML regex. Multiply by 22 HVAs × 3 platforms
  × N sections and the marginal cost of each new tenant is real engineering.
- **Vs which alternative**: mitmproxy2swagger's two-pass human curation
  cannot scale to per-tenant onboarding; har-to-openapi's heuristics don't
  handle non-UTF-8 encoding or the multi-tenant same-platform pattern (one
  HAR should yield a spec parameterized over `{tenant_host}`). B's LLM map
  stage does that curation *and* the tenant templating.

### First HAR candidates (research Q1 answered — rev 7)

1. **Dynasty DREQUEST** (8 HVAs behind `https://<tenant>.oncloudos.com/cgi/DREQUEST.PHP`)
   — CGI-style query params, ISO-8859-1 encoding. High leverage:
   one HAR → spec that generalizes across 8 tenants.
2. **CaseM** (10+ HVA/municipality instances behind `https://<tenant>.cloudnc.fi`)
   — JS-rendered SPA; the HAR must come from a Playwright capture (control-plane
   already has `casem-playwright-probe.js` — extend it to save HAR).
3. **KTweb** (7+ HVAs behind various `julkaisu.*` hosts) — UTF-16-LE detail
   pages, anti-copy spacing; a stress test for both the LLM curation and the
   scrub-boundary encoding handling.

### Converter comparison (verified against upstream READMEs, 2026-08-31)

| Dimension | mitmproxy2swagger (alufers) | har-to-openapi (jonluca) |
|-----------|----------------------------|--------------------------|
| Runtime | Python, pip — fits this repo natively | TypeScript, npm — needs a node toolchain in the loop |
| Maturity | 9.6k stars, 0.15.0, active, MIT | 134 stars, v2.5.1, active, MIT; based on dcarr178/har2openapi |
| Spec output | OpenAPI 3.0 | OpenAPI 3.0.0 **or 3.1.0** (repo's `parse_openapi` witness targets 3.1) |
| Inputs | mitmproxy flows **and** HAR | HAR only |
| Path templating | **Two-pass, human-curated**: first pass emits `x-path-templates` with `ignore:`-prefixed paths; a human promotes and edits them; second pass generates | **Automatic heuristics**: `attemptToParameterizeUrl` (UUID/numeric segments → `{param}`), `minLengthForNumericPath`, `pathReplace` regex rules |
| Incremental merge | Merges repeated runs into an existing schema; never overwrites curated endpoints | Single-shot per HAR; multi-domain splitting via `--multi-spec` |
| Auth/secrets | `--examples`/`--headers` opt-in with explicit sensitive-data warning | `guessAuthenticationHeaders`, `securityHeaders`, `filterStandardHeaders` |
| Noise control | Manual (curation pass) | `dropPathsWithoutSuccessfulResponse`, `ignoreBodiesForStatusCodes`, domain include/exclude, `urlFilter` |
| Programmatic API | CLI-first | Library-first (`generateSpec()`) + CLI |

**Reading**: the two tools bracket the design space. mitmproxy2swagger's
two-pass curation step is a *human-in-the-loop slot* — exactly the slot an
LLM map stage can fill. har-to-openapi shows how far pure heuristics go
(numeric/UUID segments) and where they stop: slug ids (`/users/matti-v`),
semantic parameter naming (`{id}` vs `{userId}`), enum detection, descriptions,
and merging near-duplicate schemas. Neither addresses non-UTF-8 encodings or
multi-tenant same-platform templating — B's differentiators.

### Map-reduce on HAR

Hybrid design — deterministic converter as scaffold, LLM map-reduce as the
curation pass:

```
har file
  │ scrub boundary (deterministic Python: cookies/auth/tokens out,
  │                 encoding normalize (utf-16le, iso-8859-1 → utf-8),
  │                 Pydantic entry records)
  ▼
baseline convert (wrap converter; emits draft spec + x-path-templates)
  │ group entries by (host-family, method, path-skeleton)
  ▼
map over endpoint groups (LLM per group, parallel; D's second consumer):
  - promote/reject candidate path (replaces m2s human curation)
  - infer template segments incl. slugs; name parameters semantically
  - infer request/response schema from body samples; detect enums
  - **tenant templating**: recognize when host varies but path shape is
    identical → emit `{tenant_host}` server variable + tenant map
  - one-line operation description
  ▼
reduce (deterministic): merge fragments into OpenAPI 3.1 doc,
  dedup shared component schemas (LLM-assisted only on near-duplicates)
  ▼
witness: round-trip through parse_openapi (FR-783) — our own parser
  must accept what we emit; then generate a typed client and re-hit
  the live tenant → response validation as end-to-end acceptance
```

- The map stage is D's consumer number two: a large HAR (thousands of
  entries, hundreds of endpoint groups) wants item-durable, resumable fan-out.
- Fallback posture: if the baseline converter already covers a given HAR
  fully, the LLM stage must degrade to a no-op-with-evidence, not invent
  changes (plausible_wrong_answer guard).

### Remaining research questions (updated rev 7)

1. ~~Concrete first HAR~~ **Answered**: Dynasty DREQUEST, CaseM, KTweb.
2. Baseline run: execute *both* converters on Dynasty DREQUEST HAR first
   (Python-native, deterministic path skeleton) — measure what each already
   delivers; the delta defines the LLM's honest scope.
3. Capture path: manual DevTools export vs agent-captured via Chrome DevTools
   MCP network tools vs extending `casem-playwright-probe.js` to save HAR.
4. Which converter to wrap: python-native m2s (repo fit, LLM replaces its
   human pass) vs har-to-openapi (better heuristics + 3.1 output, but drags
   in node). Rev 7 leans m2s: LLM-as-curation is a cleaner substitution than
   LLM-as-heuristic-supplement.
5. Tenant templating primitive: is `{tenant_host}` a plain server variable,
   or does it need a first-class "instance-fleet" concept in the spec?

When answered, B lands as `examples/api-discovery/steps/har-to-spec/`.

## Sequencing

| FR | Scope | Depends on | Size |
|----|-------|------------|------|
| **FR-936** | map node hardening: declared-inputs Send payload, raise-don't-truncate, timeout fix, RetryPolicy (filed rev 8) | — | S |
| D | resumable map: chunked driver, CachePolicy/Store-backed results, `durability="sync"`, progress JSONL + kill-and-resume witness | FR-936 | M (shrunk by native coverage) |
| A | fetch_page delta evidence → extend or new tool (fork resolved by judge) + smoke demo + Finnish encoding fixtures | — (parallel to D) | S (XS if fetch_page patch) |
| C-seed | seed assembly + index pre-filter (CC vertices ∪ CT → parquet/DuckDB prune) — deterministic, LLM-free, can start today (rev 10) | — | S |
| C | fi-catalog pilot on D + A: classify (with platform field), catalog artifact, cost number + mercury-2 quality spot-check; scale runner (tracing off) | C-seed, D, A | M |
| C2 | full-run decision gated on C's pilot cost/accuracy numbers | C | — |
| B | har-to-spec on Dynasty DREQUEST first; consumed by hva-weekly-bulletin | D (map), A (docs fetch) | M |
| B2 | CaseM (Playwright HAR) + KTweb, tenant-templating primitive | B | — |

Each component enters as a `.chaplain/inbox/` proposal and follows
Plan → Judge → Enforce. All graph authoring goes through the
`scripts/author.sh` route per graph-authoring doctrine.

## Open Questions

1. ~~**D's home**~~ **Answered (rev 8)**: extend the existing map node —
   LangGraph stops helping only at chunked scheduling and result-store
   placement; everything else is native. See D's coverage table.
2. **A's dependency fork**: lynx vs html2text/trafilatura, evidence-based —
   preceded by the fetch_page extend-vs-new decision and now informed by the
   encoding fixtures from control-plane.
3. **CC freshness for the .fi long tail** (narrowed rev 10): crawls are
   ~monthly (latest CC-MAIN-2026-34) and the seed no longer depends on
   freshness (host graph ∪ CT catches new domains fast via cert issuance);
   the remaining question is what fraction of *page content* is stale enough
   to need the live-fetch tier — C-seed's index stage measures it for free
   (fetch_time column).
4. **Catalog artifact home**: SQLite under `outputs/` for the pilot; a full
   production catalog likely deserves its own repo/dataset boundary — perhaps
   consumed by hva-weekly-bulletin directly.
5. **JS-required fraction**: C's pilot measures it; the number decides whether
   the Crawl4AI wrap tier is built at all.
6. **Tenant templating**: does B need a first-class instance-fleet concept in
   the emitted spec, or does `{tenant_host}` as a server variable suffice?
   Decision blocks B2.
7. **mercury-2 classification quality (rev 9)**: does the diffusion LM hold
   accuracy on the inline classification schema? Pilot spot-check vs a
   frontier-model sample decides; if it fails, the cost model reopens.
