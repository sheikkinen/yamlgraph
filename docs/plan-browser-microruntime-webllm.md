# Plan: Browser Micro-Runtime — WebLLM as the Engine Under Exported Graphs

**Date:** 2026-07-15
**Status:** CONDEMNED unless a named consumer appears — see Red Hat verdict
(2026-07-15, below); rung-1 findings banked, rungs 2–4 parked indefinitely
**Source:** `docs/2026-07-14-research-browser-llm-webgpu.md` (Path 4, Seeds 5-6),
integration-options analysis 2026-07-15 (option C)
**Lineage:** FR-731 (rung-1 spike: prompt compile, kill-criterion event, JSON
directive), FR-735/FR-736 (self-evidencing instrument + trace format)

## The inversion

Options A/B keep Python-yamlgraph as the runtime asking an LLM server for
completions. This plan removes the Python runtime entirely: graph YAML is
compiled **ahead of time** into a static artifact, and a small JS runtime in
the visitor's browser executes the graph, calling WebLLM in-tab for every
`llm`/`router` node. Zero server, zero key, weights in the browser cache —
the FR-731 demo's premise scaled from one prompt to one graph.

```mermaid
flowchart LR
  subgraph dev [dev machine, ahead of time]
    Y[graph.yaml + prompts/*.yaml] --> C1[compiler - build.py grown up]
    C1 --> A[static artifact: graph.json + prompt contracts]
  end
  subgraph browser [visitor's browser]
    A --> R[JS micro-runtime ~hundreds of lines]
    R -->|llm / router nodes| W[WebLLM engine, WebGPU]
    R -->|interrupt nodes| UI[DOM form]
    R -->|state| M[in-memory / OPFS]
  end
```

Different product than local inference (option B): **any visitor gets a
working yamlgraph pipeline with zero installation** — landing-page "try
it", icpc-style classification as a private in-browser tool (data never
leaves the machine), the questionnaire example as a standalone page.

## Why the runtime is small

Semantics are frozen in YAML and witnessed by ~4,900 tests; the JS runtime
re-implements only the execution loop for a **declared subset**:

| Portable naturally | Portable with work | Not portable |
|---|---|---|
| `llm`, `router` → WebLLM | `python` tools → JS callables | `tool`/shell (no sandbox) |
| `map` = `Promise.all`, `race` = `Promise.race` | checkpointing → OPFS/IndexedDB | `copilot`, `a2a` |
| `interrupt` — a browser form, *more* natural than CLI | `subgraph` | |
| condition expressions + loop limits (tiny grammar, no eval) | | |

`interrupt` is the sleeper: the reflexion loop (draft → critique → refine
until score ≥ 0.8) runs entirely in-tab, and human-in-loop is what pages
are *for*. First target subset: `llm` + `interrupt` + conditions — enough
for the reflexion demo, nothing more.

## Named hazards and their pre-built cures

1. **`framework_costume` in reverse** — claiming "yamlgraph runs in the
   browser" when a subset does. Cure = **Seed 5**: a `browser-safe` lint
   profile that mechanically verifies a graph uses only the portable
   subset. The claim is generated-or-gated, never hand-written (FR-729
   lesson, applied prospectively).
2. **Second-implementation drift** — a JS runtime silently diverges from
   Python semantics. Cure = **Seed 6**: FR-723's route log is a
   runtime-independent execution trace; run the same fixture graphs in
   both runtimes and `graph export --diff` their route.jsonl — **the
   empty diff is the conformance witness**. Adopt before the first line
   of JS exists. FR-736's trace format extends conformance one level
   down: message-level request/response pairs as cross-runtime
   regression fixtures.

## Laws already banked by the rung-1 spike (would have been runtime bugs)

- **Grammar runtimes need prompt-side JSON steering** — the compiler must
  append the JSON directive; template + schema alone floods whitespace
  deterministically (FR-731 kill-criterion event, upstream-confirmed).
- **Defaulted fields may be omitted** from grammar-enforced output (not
  in `required`) — the runtime must apply schema defaults client-side.
- **Bound max_tokens** — an unbounded degenerate run cost 87 s; bounded,
  ~10 s.
- Grammar overhead is measurable and small (`grammar_init_s` ≈ 0.38,
  per-token ≈ 0.000135 — FR-736 trace, apple metal-3).

## Ladder (strict order, each rung gates the next)

1. **Rung 1 — CLOSE FIRST:** FR-731 10-run tally verdict on the amended
   artifact + merged FR-735/736 format witness. The instrument is frozen
   until this runs.
2. **Rung 2 — Seed 5:** `browser-safe` lint profile (mechanical subset
   verification). Small FR; reuses linter architecture; the
   `linter-llm-free` import contract is the portability certificate
   precedent.
3. **Rung 3 — Seed 6:** conformance harness — fixture graphs + route-log
   diff runner, Python side only (defines the bar the JS runtime must
   clear before it exists).
4. **Rung 4 — the runtime:** smallest subset (`llm` + `interrupt` +
   conditions), reflexion demo as the acceptance fixture, conformance
   diff empty, browser-safe lint green on the fixture.

**Stop rule:** Path 4 waits for a **second consumer** beyond the
landing-page demo. If nobody asks for rung 2, the ladder correctly ends —
`growth_as_default` names the alternative. No FR for rungs 2–4 is filed
until the rung-1 verdict is written into FR-731.

## Explicitly out of scope

- WebLLM as a `create_llm()` provider (impossible: browser-only, no
  Python binding; see option A analysis).
- MLC-LLM serve via the lmstudio provider (option B — a separate
  30-minute verification spike if local inference is wanted; different
  product, different plan).
- Model picker, streaming UI, service workers, telemetry — the demo
  purge lists carry forward.

## Red Hat verdict (2026-07-15) — largely a red herring

Challenged same-day ("multiple gotchas — jinja2, state management. is
this a red herring?"). The challenge survives scrutiny; recorded so the
ladder is not an attractive nuisance:

1. **Jinja2 is the prompt system, not a corner case.** The
   schema-driven-extraction pattern — the flagship — iterates
   `schema.fields` in Jinja2. The portable-template subset excludes
   exactly the graphs worth porting. "Reject at compile" filters out
   the demand, not the risk.
2. **State merge semantics are the incident-dense boundary** (reducers,
   messages append, map fan-out merge, on_error, resume). By
   `incident_density_ranking`, a second runtime re-buys every recorded
   incident in a language with no test suite behind it. "~Hundreds of
   lines" was the optimistic estimate of exactly the code that is never
   small.
3. **The portable subset is `framework_costume` by construction**: what
   ports easily (`llm` + `interrupt` + conditions) is a ~50-line vanilla
   JS loop — the framework minus its reasons to exist (tools,
   checkpointing, observability, enforcement).
4. **Engine ceiling**: browser ≈ 1B q4. This week's evidence: directive
   needed to avoid whitespace flood, defaulted fields omitted. The
   "private in-browser classifier" story assumes quality that icpc
   needed caps + judges + harnesses to get from far larger models.
5. **Cost signal**: one prompt, in-browser, correctly instrumented =
   three FRs + a kill-criterion event. A graph multiplies that by every
   node type.

**What survives:** rung-1 compile-path laws (transfer to any grammar
runtime, incl. MLC serve). Seeds 5–6 park with rung 4.

**Path 2 (Pyodide) killed same day, second pass:** paste-YAML-get-
lint-and-diagram is FR-070 (`yamlgraph serve` web playground,
REJECTED 2026-02-21) wearing a WASM costume — the graduated doctrine
("No UI, ever; text is the interface; visual tools create a human
dependency that YAML eliminates") objected to the visual *authoring
surface*, not the runtime, so moving it into Pyodide changes nothing.

**The one visual survivor — realtime forensic overlay:** FR-070's own
rejection table sanctioned visual *observability* (LangSmith trace
URLs were the preferred alternative); only authoring UI is banned.
Doctrine-compliant shape: `yamlgraph graph watch` — tail a live
route.jsonl (producer already exists: `YAMLGRAPH_ROUTE_LOG=<path>`),
re-render `render_overlay` per decision, atomic-write the `.mmd`; any
auto-refreshing mermaid preview renders it. No server, no JS, no UI
framework — the file is the interface. Named consumer: ninchat_voice
(NC-376 renders route artifacts at teardown; realtime is its upgrade,
and loop starvation of the NC-386 class becomes visible while it
happens — `streaming_xray`).

**Reopen condition (rung 4):** a *named* consumer with a graph that (a) fits the
portable subset as-is, (b) tolerates 1B-class output quality, and
(c) cannot be served by the single-prompt page. All three,
or it stays dead.
