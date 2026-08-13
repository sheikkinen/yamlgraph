# Research: LangGraph 1.2.x Feature Gap Analysis

**Date:** 2026-08-13
**Grounding:** repo pins `langgraph>=1.2.0`; installed 1.2.9; latest release
1.2.11 (2026-08-11). Claims below verified against the yamlgraph source
(grep for wiring), the LangGraph release feed, and current LangChain docs —
not against memory.

## Question

Is YAMLGraph missing features that current LangGraph (1.2.x, post-1.0 API)
provides? If so, which gaps are worth YAML surface area, and what would the
examples and value look like?

## Finding in one line

YAMLGraph is not behind on orchestration *semantics* — every gap found is a
LangGraph primitive that yamlgraph does not yet **expose in YAML**, not
missing machinery. The framework's compile pipeline (`add_node` kwargs,
`compile()` kwargs, invoke kwargs) already has the attachment points.

## Already covered — no gap

| LangGraph feature | YAMLGraph surface |
|---|---|
| `CachePolicy` node caching | `cache:` config → `compile/node_compiler.py::resolve_cache_policy` |
| Dynamic `interrupt()` / `Command(resume=)` | `type: interrupt` nodes (`node_factory/control_nodes.py`) + CLI resume loop + A2A INPUT_REQUIRED |
| `Send()` fan-out | `type: map` with fan-out cap (FR-027) |
| Subgraphs | `type: subgraph` |
| Token streaming (`stream_mode="messages"`) | `run_graph_streaming` / `streaming_events.py` |
| Retry semantics | `on_error: retry` (own loop — see gap 3 for the caveat) |
| Checkpointers: memory, SQLite, Redis | `config.checkpointer` |

Deliberate non-gap: the **Functional API** (`@entrypoint` / `@task`) is the
imperative alternative to yamlgraph's declarative premise. Adopting it would
be framework_costume in reverse. Watch, never adopt.

## Gaps, ranked by value to this repo

### 1. `BaseStore` long-term memory (cross-thread store)

**What:** LangGraph's `Store` is a namespaced key-value store shared across
threads, passed at `compile(store=...)`, with optional semantic search
(embeddings) on `put`/`search`. Checkpointers are thread-scoped; the store is
the sanctioned cross-thread persistence layer.

**Gap:** yamlgraph has zero wiring (`grep BaseStore|InMemoryStore|store=`
finds only A2A `task_store`). Every example needing cross-run memory
hand-rolls files: NPC memory, FR-782's portrait-diff reads its own previous
JSON output, diary_digest greps the filesystem.

**Potential YAML surface:**

```yaml
config:
  store: sqlite          # memory | sqlite (path defaults beside checkpointer)

nodes:
  recall:
    type: store_get      # or store_search with query:
    namespace: "npc/{npc_id}/memories"
    state_key: memories
  remember:
    type: store_put
    namespace: "npc/{npc_id}/memories"
    value: "{summary}"
```

**Example candidates:** `examples/demos/memory_store/` — a two-run demo where
run 2 (new thread_id) recalls what run 1 stored; NPC example upgraded from
file-based memory; FR-782 diff mode reading prior portraits from the store
instead of scanning the output dir.

**Value added:** the single biggest genuinely missing capability. Unlocks
"agent that remembers the user across sessions" natively — the exact shape
FR-782 and the operator-calibration pattern approximate by hand. First
consumer is concrete and already exists in the repo.

### 2. Durability modes (`durability="sync"|"async"|"exit"`)

**What:** per-invoke knob controlling when checkpoints commit. The 1.2.x
line invested heavily here: delta channels, `Overwrite` JSON-roundtrip fixes,
exit-mode task_id fixes (1.2.7–1.2.9) — this is where upstream is spending
its engineering budget.

**Gap:** yamlgraph never passes `durability`; every checkpointed graph pays
synchronous checkpoint cost per superstep. Long pipelines (chaplain enforce,
ebook chapters, book translator) checkpoint dozens of times when `"exit"`
or `"async"` would do.

**Potential YAML surface:**

```yaml
defaults:
  durability: async      # sync (default) | async | exit
```

plus `--durability` CLI override. Pure passthrough to `invoke/stream`.

**Example candidate:** benchmark demo — same 10-node graph with SQLite
checkpointer timed under the three modes; the delta is the demo output.

**Value added:** latency for free on every long checkpointed run; smallest
diff of all four gaps (one config key, one kwarg).

### 3. Node-level `RetryPolicy`

**What:** `add_node(retry_policy=RetryPolicy(...))` — exponential backoff,
jitter, `retry_on` exception classes, retries *before* the checkpoint
commits.

**Gap:** yamlgraph's `on_error: retry` is a fixed-count loop inside the node
wrapper — no backoff, no exception taxonomy, and the failed attempt's state
handling lives at the wrong layer (downstream_fix pattern: we guard where
the symptom manifests instead of using the boundary primitive).

**Potential YAML surface:** extend the existing key rather than adding one —

```yaml
nodes:
  flaky_provider:
    on_error: retry
    retry:
      max_attempts: 4
      backoff_factor: 2.0
      retry_on: [ratelimit, timeout]   # mapped to exception classes
```

compiled onto `retry_policy=` instead of the hand-rolled loop.

**Example candidate:** RunPod serverless node (documented tens-of-seconds
cold starts in CLAUDE.md) — the retry contract this provider already needs.

**Value added:** correctness (retry-before-checkpoint) + deleting our own
retry loop (Commandment 8: feed the duplicate to the framework that owns it).

### 4. Deferred nodes (`defer=True`)

**What:** node waits for **all** in-bound branches before executing — the
proper join for diamond/fan-in shapes.

**Gap:** map nodes reduce implicitly, but an arbitrary diamond (e.g. race +
gather, parallel fan-out edges converging on an aggregator) can fire the
join early with partial state.

**Potential YAML surface:** one boolean on the node:

```yaml
nodes:
  aggregate:
    type: python
    defer: true
```

**Example candidate:** `fan_out_demo` extended with a deferred aggregator;
lint rule warning when a node has >1 in-edge and no `defer`.

**Value added:** closes a correctness hole in graphs users can already
express; near-zero implementation cost.

## Watch list (not FR-worthy yet)

- **`trace_policy` on `add_node`** (1.2.10→1.2.11: added, reverted,
  re-added — API still churning). Per-node LangSmith trace control; fits
  Commandment 9. Revisit when it survives two releases unchanged.
- **Runtime context API** (`context_schema` / `Runtime[T]`, the 0.6+
  successor to `config["configurable"]`). yamlgraph still uses the old
  idiom; it works and is not yet removed. Migration is a refactor FR when
  deprecation lands, not a feature.
- **Multi-`stream_mode`** (`["updates", "messages"]` in one stream) and the
  1.2.10 typed v3 `stream_events` + native projections. CLI streams
  messages-only today; useful when a consumer (A2A, openai_proxy) needs
  progress + tokens simultaneously.
- **Checkpoint TTL / `omit_expired`** (checkpoint 4.2.0, opt-in). Relevant
  to unbounded SQLite/Redis checkpoint growth in scheduled installs
  (~/scheduled-yamlgraphs agents run weekly forever).
- **Postgres checkpointer extra** — yamlgraph ships memory/sqlite/redis;
  add `[postgres]` extra only when a deployment asks (would_you_use_this:
  no named consumer today).

## Recommendation

Value ordering: **store (1) > durability (2) > retry_policy (3) > defer (4)**.
Store and durability are independent FR-sized units with named first
consumers already in the repo; retry and defer could travel together as a
"node-policy passthrough" FR. All four respect C-shaped scope: YAML schema +
compile passthrough + example + tests, no new machinery.

**Seed:** when upstream concentrates releases on one subsystem (three
consecutive patch releases touching durability/delta channels), that is the
vendor telling us where production pain lives — should the quarterly
dependency review read release feeds as a demand signal, not just a CVE
source?
