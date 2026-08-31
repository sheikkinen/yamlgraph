# Feature Request: Map Node Hardening — Scale-Correct Send Fan-out

**Priority:** HIGH
**Type:** Enhancement
**Status:** SPLIT — see `FR-936-map-node-hardening.judgement.md` (2026-08-31).
No implementation authority. Replaced by four independently researched FRs:
(D-1) map branch input projection / `pass_keys`, (D-2) `max_items` overflow
policy with typed `on_overflow` — allocated as FR-939
(`FR-939-map-overflow-policy.md`), (D-3) investigation FR for timeout
cancellation and resource lifecycle (the bounded shared pool proposed below
was rejected — it converts leakage into deterministic starvation), (D-4)
LangGraph `RetryPolicy` integration and exception ownership. Replacement FR
numbers to be allocated when authored.
**Effort:** 2 days
**Requested:** 2026-08-31
**First consumer / first event:** the fi-catalog pilot (D, per
`docs/plan-web-toolkit.md`) — the first map run whose `over` list exceeds
`max_items`, which today silently truncates and reports success. Nearer-term:
any existing map graph running with the SQLite checkpointer pays the
full-state-payload tax on every pending write today.
**Research:** in-body dispositioned audit below (FR-889 style), verified
against current LangGraph docs and `yamlgraph/compile/map_compiler.py` on
2026-08-31; recorded in `docs/plan-web-toolkit.md` rev 8 ("Existing map node
audit" + "LangGraph-native coverage").

## Summary

The map node uses the canonical LangGraph Send+reducer pattern but deviates
from it in two scale-hostile ways (full-state Send payloads, silent
truncation at `max_items`) and misses native affordances (RetryPolicy;
per-branch timeout implemented as an abandoned thread). Harden the existing
node to the native pattern. Prerequisite for the resumable-map primitive (D
in `docs/plan-web-toolkit.md`); no new node type, no durability features —
those are D's scope.

## Value Statement

Every existing map graph gets smaller checkpoints and honest failure
semantics; the web-toolkit pipeline (550k-item fan-out) becomes buildable on
the map node instead of around it.

## Problem

Audit findings in `yamlgraph/compile/map_compiler.py` (2026-08-31):

1. **Full-state copy per Send** (`map_edge`):
   `Send(sub_node_name, {**state, item_var: item, "_map_index": i})` clones
   the entire parent state into every branch. The LangGraph docs' pattern
   sends a minimal per-item payload (`Send("generate_joke", {"subject": s})`).
   Consequences: memory × fan-out; every checkpointer pending-write carries
   the whole state; at 500k items the run is memory- and IO-bound on state
   copies. Root cause: sub-node prompts may reference arbitrary
   `{state.key}` variables, so the compiler passes everything instead of
   computing what is referenced — assumed, not declared (`module_structure`
   boundary lesson).

2. **Silent truncation at `max_items`** (`map_edge`, FR-027):
   `logger.warning` + `items[:max_items]`. A 550k-item run "succeeds" with
   the default cap's worth of items — textbook `plausible_wrong_answer`, and
   a Commandment 6 violation (silent fallback substituting a subset for the
   whole). The warning is invisible in non-interactive runs (cron, CI,
   chaplain pipelines).

3. **Per-branch timeout leaks the thread** (`_execute_node_fn`, FR-069):
   one-shot `ThreadPoolExecutor` + `shutdown(wait=False, cancel_futures=True)`
   abandons the still-running thread on timeout — it keeps holding its LLM
   connection and GIL slices. At large fan-outs with a realistic timeout-rate,
   zombie threads accumulate for the life of the process.

4. **No `RetryPolicy` surfaced**: LangGraph supports
   `add_node(..., retry=RetryPolicy(...))` natively; map sub-nodes get only
   the hand-rolled `on_error` path. Transient LLM failures inside a fan-out
   (rate limits, 529s) are exactly RetryPolicy's case.

Non-problem (explicitly out of scope → D): `CachePolicy`/Store-backed
resume-by-skip, chunked scheduling, `durability` mode exposure. This FR makes
the map node *correct*; D makes it *durable*.

## Ideal Result

A map run over N items either processes all N or raises before the first LLM
call; each Send payload carries only the keys the sub-node declares/uses;
a timed-out branch does not leak execution resources unaccounted; transient
per-branch failures retry via the native policy. The kill-and-resume witness
that D will add can then stand on writes small enough to checkpoint at scale.

## Proposed Solution

All changes inside `yamlgraph/compile/map_compiler.py` + config schema; no
new node type.

### 1. Declared-inputs Send payload

At compile time, compute the key set the sub-node actually needs:
`item_var`, `_map_index`, and every `{state.X}` / Jinja `state.X` reference
in the sub-node's `variables` and its prompt template. Fan out with only
that subset. An explicit `pass_keys: [..]` config overrides/extends when
the sub-node reads state dynamically (agent/subgraph sub-nodes may need it).

```yaml
nodes:
  classify:
    type: map
    over: "{state.domains}"
    as: domain
    pass_keys: [locale]   # optional; default = computed reference set
    node: {...}
```

Subgraph/agent sub-node types with uncomputable references default to
full-state pass-through **with a lint warning**, preserving correctness
while making the tax visible.

### 2. Raise on overflow, truncate only by explicit config

`len(items) > max_items` → raise `ValueError` naming the node, count, and
cap. Truncation only via explicit `on_overflow: truncate` (config is truth;
silent behavior is banned):

```yaml
    max_items: 1000
    on_overflow: error   # default; 'truncate' opt-in, logged at WARNING
```

### 3. Timeout without thread abandonment

Replace the per-call one-shot pool with a per-map-node bounded shared
executor; on timeout, record the leaked branch in the run's `errors` with
node/index so the leak is observable, and reuse pool slots so leaks are
bounded by pool size, not fan-out. (True cancellation of a blocking LLM call
belongs at the client boundary — per-request timeouts in llm_factory — noted
as related work, not scoped here.)

### 4. Surface native RetryPolicy

`retry:` map-node config mapped to LangGraph `RetryPolicy` on the sub-node
(`max_attempts`, `backoff_factor`, retryable exception filter). Coexists
with `on_error`; `retry` runs first, `on_error` disposes the final failure.

## Acceptance Criteria

- [ ] RED: failing test — Send payload for an llm sub-node contains only
      declared/referenced keys (witness: payload size independent of an
      unrelated 1 MB state key)
- [ ] RED: failing test — map over `max_items + 1` items raises with node
      name and counts; `on_overflow: truncate` restores slicing and logs
- [ ] RED: failing test — timed-out branch produces the existing timeout
      error result AND the executor is bounded (no unbounded thread growth
      across k timeouts, k > pool size)
- [ ] `retry:` config compiles to `RetryPolicy` on the sub-node; test with a
      flaky mock passing on attempt 2
- [ ] Existing map tests green; `examples` map demos re-run
      (`demo-output.log` where a demo graph is touched)
- [ ] `@pytest.mark.req` tags against CAP-11 REQs (extend CAP-11 with new
      REQ IDs for overflow semantics and payload minimality)
- [ ] `reference/graph-yaml.md` map section documents `pass_keys`,
      `on_overflow`, `retry`
- [ ] Changelog fragment (`fix`/`feat` per final typing)

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| New `durable_map` node type carrying all fixes | Rejected — hardening is orthogonal to durability; a new type duplicates CAP-11 surface (see plan rev 8, Open Question 1 answered) |
| Keep truncation default, raise opt-in | Rejected — silent subset-for-whole is the Commandment 6 case; default must be loud |
| Process-based branch isolation for killable timeouts | Rejected here — heavyweight; real cure is client-level request timeouts (llm_factory), separate FR if needed |
| Do nothing until D | Rejected — D's checkpoint-size and witness semantics stand on these fixes; and current users pay the payload tax today |

## Related

- `docs/plan-web-toolkit.md` rev 8 — audit + LangGraph-native coverage table
- `yamlgraph/compile/map_compiler.py` — all four findings
- CAP-11 (Subgraph & Map), FR-027 (max_items origin), FR-069 (timeout
  origin), FR-052 (flatten_output), FR-467 (router→map Send fan-out)
- LangGraph docs: Graph API (`Send`, node caching, retry), Persistence
  (pending writes, durability modes)
