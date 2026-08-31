# Plan: Web Toolkit — Overview

**Date:** 2026-08-31 (rev 6 — value audit folded: D is the keystone, C's
framework value contingent on D, A gated on a fetch_page delta, B's value
sentence incomplete until baseline research. rev 5: SPA rendering
dispositioned; rev 4: converter comparison; rev 3: C primary, D promoted,
B parked)
**Status:** Draft (pre-FR)
**Scope:** A TLD-scale classification pipeline (C, primary) and the two
foundations it stands on: a text-render graph tool (A) and a resumable
storage-backed map primitive (D). HAR→OpenAPI (B) parked pending research.

## Vision

Catalog and classify an entire country-code domain (*.fi) with a YAMLGraph
pipeline. The build forces two durable framework assets into existence: a
fetch-as-text tool usable inside any graph, and a map primitive that survives
500k-item runs.

## Priority Order

1. **C — .fi TLD catalog**: the primary analysis focus and the driving use case.
2. **D — resumable storage-backed map**: new framework primitive C requires;
   likely the most durable output for the repo.
3. **A — lynx_render**: graph tool consumed by C's live-fetch tier and by any
   future research graph.
4. **B — har-to-spec**: parked; needs more info before an FR (see Parked).

## Value Audit (forced_opposite, rev 6)

Each component challenged with "what value does the output add?" and "would
yamlgraph add value, or is it costume?":

| | Value of the output | Would yamlgraph add value? |
|--|--|--|
| **D** | Intrinsic and highest: item-durable resumable fan-out is a genuine gap — LangGraph checkpoints at superstep level, not per-item; the max_items + CAP-120 stack is documented user pain. Three named consumers (C pilot, B map stage, any bulk job). | **D *is* yamlgraph value** — a framework primitive, not an application. The only component whose worth doesn't depend on the others shipping. The keystone. |
| **C** | Real but external: a classified ccTLD census doesn't exist; consumer named. The value lives in the **data**, not the pipeline. | **Only via D.** The graph shape is single-stage embarrassingly-parallel classify — a 50-line asyncio+SQLite script does it today. Without D, yamlgraph here is framework_costume. With D, the framework earns its keep (resume at 550k, provider swap, typed outputs) and gains a scale witness it has never had. |
| **A** | Marginal: api-discovery already ships `fetch_page`. Honest delta is rendered-text quality, link inventory, and the render-emptiness signal — commodity wrapper territory. | Neutral — Layer 3 plumbing working as designed. The FR is gated on stating the delta vs fetch_page (see A's delta gate). |
| **B** | Most speculative output value (no named first HAR, no consumer, delta over deterministic converters unmeasured) — but the best native graph-shape fit of all four: LLM map replacing m2s's human curation pass, deterministic reduce, round-trip witness. | Yes *iff* the baseline research (Q2) shows a real delta. If the converters already cover the HAR, the LLM stage is growth_as_default and B dies. Parking is the plan working. |

**Summary**: D is the keystone — sequenced first, correctly. C standalone is
a script; C stated as "the workload that forces D to exist and produces a
citable dataset as exhaust" is honest and defensible. A must prove it isn't
a duplicate of fetch_page. B cannot yet complete the "for whom / what pain"
sentence.

## Prior Art (dispositioned)

| Artifact | FR | Relation |
|----------|----|----------|
| `examples/demos/fi_domain_crawl` | FR-204 | Shipped crawl-and-summarise demo (httpx + BeautifulSoup, map fan-out, LLM synthesis). C evolves this — refit, don't duplicate. |
| `examples/api-discovery` | FR-783..790 | Tool manifests `fetch_page`, `curl_probe`, `parse_openapi`; step graphs. A's tool lives beside these manifests; CAP-226's SPA-shell/browser-sniff distinction is the precedent for A's JS policy. **`fetch_page` is also A's potential duplicate — see A's delta gate.** |
| `examples/daily_digest/nodes/content.py` | — | BS4 extraction; its committed `digest.db` dedup is the precedent for C's incremental re-crawl. |
| map `max_items` + CAP-120 inter-run state chaining + SQLite checkpointer | — | The current workaround stack D replaces with a primitive. |
| **Common Crawl WET files (external)** | — | .fi pages already crawled *and rendered to text*. C v1 classifies from CC extracts; live-fetch only gaps/refresh. Kills most cost, politeness, and seed problems. |
| **mitmproxy2swagger / har-to-openapi (external OSS)** | — | Deterministic HAR→OpenAPI converters exist; any future B wraps, not reimplements. Compared in the Parked section. |
| **Jina Reader / Firecrawl / Crawl4AI / browser-use (external)** | — | "URL → LLM-ready text incl. JS" is an occupied product category. A's JS tier wraps Crawl4AI (or Playwright), never builds rendering. See "SPA rendering: product boundary". |

## Component C (primary): `.fi` TLD catalog — classify at country scale

Evolution of FR-204's demo into the toolkit's driving analysis pipeline.

- **Honest framing (rev 6)**: standalone, C is a script — its graph shape is
  a single LLM-classify stage over items. C's value to the *repo* is that it
  forces D to exist and hands the framework a 500k-scale witness; the catalog
  dataset is the exhaust. C's yamlgraph value is contingent on D — the FR
  must present it as D's acceptance workload, not as a product needing a
  framework.
- **v1 is Common Crawl, not crawling**: CC WET files carry pre-rendered text
  for .fi pages — classify from those, live-fetch (A) only for gaps and
  refresh. The Traficom open-data domain list (~550k domains) is the
  completeness reference.
- **Pipeline**: CC/seed domains → deterministic pre-filter (DNS resolve +
  HTTP HEAD; LLM never sees dead sites) → **D-map**(text extract → LLM
  classify with inline schema: category, language, organisation type, API
  presence, liveness, `render: empty|thin|full`) → catalog artifact
  (SQLite/JSONL).
- **Cost model (required before scope freeze)**: haiku-class model pinned,
  token cap per page dump, measured cost per 1k domains from a pilot batch.
  550k × classify is real money — no full run without the pilot number.
- **Evaluation (read_raw_output_first)**: before any aggregate accuracy claim,
  dump N classified samples with their source text and read them; spot-check
  accuracy criterion in the FR. An unaudited catalog is a liability.
- **Incremental semantics**: dedup + change detection + entry TTL (precedent:
  daily_digest's digest.db). Liveness re-check is deterministic and LLM-free.
- **Politeness constraints** (live-fetch tier only): robots.txt respect,
  per-host rate limits, identifying User-Agent — FR acceptance criteria.
- **Named consumer**: public-sector platform census (which municipalities run
  CKAN/PxWeb/OData) extends api-discovery to catalog scale; plus liveness
  monitoring as a free LLM-less byproduct.

## Component D: resumable storage-backed map primitive

C at 500k items is a scale the map node has never seen; `max_items` +
CAP-120 chaining is a workaround, not a primitive. D makes it one.

**Keystone (rev 6)**: D is the only component whose value is intrinsic to
the framework — it survives even if C's full run is never funded (the
primitive pays for itself at 10k-item scale) and B never unparks.

- **Contract sketch**: a map variant (or map option set) with
  - **item-level durability**: each completed item's result persists to
    storage (SQLite; same family as the checkpointer) the moment it finishes —
    a crash at item 312,401 loses one item, not the run;
  - **resume-by-skip**: re-running the graph skips items whose results exist
    (keyed by stable item id), extending `skip_if_exists` semantics from
    node-level to item-level;
  - **chunked execution**: bounded batches with configurable concurrency, so
    memory and rate limits hold at 500k;
  - **progress observability**: counts/failures queryable mid-run (FR-723
    route-log style JSONL or the OTel spans from FR-759).
- **Boundary decision for the FR**: extend the existing map node vs a new
  `durable_map` type — judged against LangGraph checkpointer granularity
  (superstep-level, not item-level at fan-out) so the primitive is built where
  LangGraph actually stops helping.
- **Witness**: kill -9 mid-run at scale N, re-run, prove completed items are
  not re-executed and the final catalog is identical to an uninterrupted run.
- **C is the acceptance demo**: the pilot batch runs on D.

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
- **Form**: shell tool manifest wrapping `lynx -dump`; modes `-nolist`
  (reading text) and `-listonly` (numbered link inventory).
- **Boundary rules** (no silent fallbacks): fail fast if binary missing;
  normalize encoding; cap dump size; per-fetch timeout; Finnish-encoding
  witness fixture (ä/ö, legacy ISO-8859-1 site).
- **JS policy**: empty/thin dump is **a signal, not a failure** — returned
  tagged (`render: empty|thin|full`), classified downstream as "JS-required".
- **JS tier (disposition: wrap, don't build)**: rendering JS pages to text is
  an occupied product category (Jina Reader, Firecrawl, Crawl4AI ~40k stars,
  browser-use). If C's pilot shows the "JS-required" fraction matters, the
  escalation tier is a second tool manifest wrapping **Crawl4AI** (pip,
  Playwright-based, LLM-friendly markdown) — same wrap-don't-reimplement
  verdict as mitmproxy2swagger in B. Building a renderer is out of scope for
  yamlgraph permanently: by the three-layer doctrine a renderer is Layer 3
  side-effect plumbing, not orchestration.
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

## Parked: B — `har-to-spec` (needs more info)

HAR→OpenAPI synthesis is deferred until the research below concludes; no FR
yet. B is the best native graph-shape fit in this plan (parallel LLM map +
deterministic reduce + witness), but it cannot yet complete the value
sentence — *for whom, against what pain, versus which alternative* — until
the baseline research answers what the LLM honestly adds over the converters.

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
and merging near-duplicate schemas.

### Potential map-reduce on HAR

Hybrid design — deterministic converter as scaffold, LLM map-reduce as the
curation pass:

```
har file
  │ scrub boundary (deterministic Python: cookies/auth/tokens out,
  │                 Pydantic entry records)
  ▼
baseline convert (wrap converter; emits draft spec + x-path-templates)
  │ group entries by (host, method, path-skeleton)
  ▼
map over endpoint groups (LLM per group, parallel):
  - promote/reject candidate path (replaces the human curation pass)
  - infer template segments incl. slugs; name parameters semantically
  - infer request/response schema from body samples; detect enums
  - one-line operation description
  ▼
reduce (deterministic): merge fragments into OpenAPI 3.1 doc,
  dedup shared component schemas (LLM-assisted only on near-duplicates)
  ▼
witness: round-trip through parse_openapi (FR-783) — our own parser
  must accept what we emit; plus schemathesis-style example validation
  as a stretch goal
```

- The map stage is D's consumer number two: a large HAR (thousands of
  entries, hundreds of endpoint groups) wants item-durable, resumable fan-out.
- Fallback posture: if the baseline converter already covers a given HAR
  fully, the LLM stage must degrade to a no-op-with-evidence, not invent
  changes (plausible_wrong_answer guard).

### Remaining research questions

1. Concrete first HAR: which real system's traffic do we convert first
   (public API fixture vs an actual undocumented internal API)?
2. Baseline run: execute *both* converters on that HAR — measure what each
   already delivers; the delta defines the LLM's honest scope.
3. Capture path: manual DevTools export vs agent-captured via Chrome DevTools
   MCP network tools.
4. Which converter to wrap: python-native m2s (repo fit, needs the LLM to
   replace its human pass) vs har-to-openapi (better heuristics + 3.1 output,
   but drags in node).

When answered, B lands as `examples/api-discovery/steps/har-to-spec/`.

## Sequencing

| FR | Scope | Depends on | Size |
|----|-------|------------|------|
| D | resumable storage-backed map primitive + kill-and-resume witness | — | M |
| A | fetch_page delta evidence → extend or new tool (fork resolved by judge) + smoke demo | — (parallel to D) | S (XS if fetch_page patch) |
| C | fi-catalog pilot on D + A: pre-filter, classify, catalog artifact, cost number | D, A | M |
| C2 | full-run decision gated on C's pilot cost/accuracy numbers | C | — |
| B | parked — research questions above; map stage would also consume D | (D) | — |

Each component enters as a `.chaplain/inbox/` proposal and follows
Plan → Judge → Enforce. All graph authoring goes through the
`scripts/author.sh` route per graph-authoring doctrine.

## Open Questions

1. **D's home**: map node option set vs new node type — where does LangGraph's
   checkpointer actually stop helping at fan-out scale?
2. **A's dependency fork**: lynx vs html2text/trafilatura, evidence-based —
   preceded by the fetch_page extend-vs-new decision.
3. **CC WET freshness**: how stale is Common Crawl for the .fi long tail, and
   what refresh fraction does that imply for the live-fetch tier?
4. **Catalog artifact home**: SQLite under `outputs/` for the pilot; a full
   production catalog likely deserves its own repo/dataset boundary.
5. **JS-required fraction**: C's pilot measures it; the number decides whether
   the Crawl4AI wrap tier is built at all.
