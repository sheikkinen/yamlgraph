# Feature Request: Map Node Hardening — Scale-Correct Send Fan-out

**Priority:** HIGH
**Type:** Enhancement
**Status:** **SPLIT** (judged 2026-08-31; split record updated 2026-09-02) — no implementation authority; see child FRs below and `FR-936-map-node-hardening.judgement.md`
**Effort:** 2 days (across children)
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

## Split (2026-08-31; record updated 2026-09-02)

Judged **SPLIT**: this FR bundled four orthogonal map-node contracts —
Send payload projection, overflow disposition, timeout resource
lifecycle, and native retry — each with independent failure modes. The
audit findings below (§Problem) were found real and are inherited by the
children; the bundling was not. Each child must carry its own committed
research record (FR-890 gate), re-enter judgement independently, and
allocate its own CAP-11 requirement IDs. The bounded shared executor
proposed in §Proposed Solution 3 was **rejected** by the judgement (R-5):
it converts thread leakage into deterministic starvation.

| Child | Surface (fenced by the judgement) | Allocation | State (2026-09-02) |
|---|---|---|---|
| **D-1** | Map branch input projection: per-`Send` payload limited to statically derived keys ∪ explicit `pass_keys`; every execution-time state consumer enumerated per sub-node type (`variables`, `requires`, direct Jinja `state`, guards, verification, routing, `skip_if_exists`); Python/agent/subgraph sub-nodes classified dynamic → declared inputs or full-state pass-through with a lint warning (R-3, C-2) | **FR-955** `FR-955-map-branch-input-projection.md` | Authored and judged 2026-09-02: **APPROVED WITH REVISIONS**, R-1–R-7 folded 2026-09-02; research record `FR-955.research.md` promoted from the FR-890 route (six classes, subtractionist dissent preserved). Authority activates on human review |
| **D-2** | `max_items` overflow policy: typed `on_overflow: error \| truncate`, default `error`, validated at load, enforced before the first `Send` (R-4) | **FR-939** `FR-939-map-overflow-policy.md` | Judged APPROVED WITH REVISIONS 2026-08-31; R-1–R-4 folded; authority activates on human review of the judgement. **Not implemented** — `map_compiler.py` still warns and slices. FR-939 additionally found that `config.max_map_items` is parsed by `graph_loader.py` but never reaches `map_edge`, so the documented graph-level cap is inert today; that repair is inside FR-939's fence (its R-3) |
| **D-3** | Investigation FR: map branch timeout cancellation and resource lifecycle. Must prove the lifecycle from submission through timeout, cancellation/return, executor disposal and subsequent healthy-branch execution; accepted mechanism terminates work at the provider/client boundary or isolates it in a terminable execution unit; a thread-count bound alone does not satisfy (R-5, C-3) | **FR-956** `FR-956-map-branch-timeout-lifecycle-investigation.md` | Authored and judged 2026-09-02: **APPROVED WITH REVISIONS**, R-1–R-6 folded 2026-09-02 (judge accepted the in-body table under `TEMPLATE.md`; bounded-leak absolution path removed; dissent preserved); condemn-or-absolve witness shape (FR-706 precedent). Authority activates on human review |
| **D-4** | LangGraph `RetryPolicy` integration via `add_node(..., retry_policy=...)` with typed Pydantic config and a closed declarative `retry_on` allowlist; one retry owner; exceptions must reach LangGraph before `wrap_for_reducer` converts them to state updates; ordering against final `on_error` defined (R-6, C-4, C-5) | **FR-957** `FR-957-map-branch-native-retry-policy.md` | Authored and judged 2026-09-02: **APPROVED WITH REVISIONS**, R-1–R-6 folded 2026-09-02 (typed `NodeError` injection confirmed in LangGraph 1.2.11, side-table fallback deleted, defaults frozen); supersedes FR-031 within the map-branch fence. Authority activates on human review |

**Non-overlap contract:** D-1 owns `Send` payload contents; D-2 owns the
item-count check and its disposition; D-3 owns `_execute_node_fn` and
executor lifecycle; D-4 owns sub-node registration and exception
ordering. No child may touch another's surface (judgement C-6); durable
or resumable map behaviour, chunked scheduling, concurrency control,
`CachePolicy`, Store-backed results, checkpoint format and progress
logging remain outside all four (component D, `docs/plan-web-toolkit.md`).

**Ordering note:** the first census-scale consumer
(`docs/plan-web-toolkit.md` component D; ranked use cases in
`docs/2026-09-02-brainstorm-business-use-cases.md` §5.2) needs D-2 before
any paid run (coverage arithmetic depends on never dropping scope) and
D-1 before checkpointing at scale (every branch currently checkpoints a
copy of the whole parent state). D-3 and D-4 are correctness and
operability, not blockers for a first run.

**Completion contract (rejudged 2026-09-02):** FR-936 is complete as a
split record only when all four rows above name committed child FRs,
each with its own FR-890 research record. The authoritative criteria
are AC-01–AC-12 and gates C-1–C-8 of the 2026-09-02 rejudgement appended
to `FR-936-map-node-hardening.judgement.md`. The §Acceptance Criteria
list further down is the *historical* bundled proposal and grants no
authority (rejudgement R-6, AC-10). Rejudgement R-1 is satisfied as of
2026-09-02: D-1, D-3 and D-4 are authored as FR-955, FR-956 and FR-957.
Open work: each child re-enters judgement independently (R-2 substance
check applies to each research record).

### Adjacent findings parked (not FR-936 deliverables)

**Research-route precedent checker misses legacy FR filenames.**
`examples/demos/research-route/nodes/research_tools.py:391-395`
(`_check_committed_ids`) resolves `FR-NNN` mentions with the glob
`FR-{number}[-.]*` and raises `precedent names nonexistent FR-NNN`
otherwise. FRs filed before the `FR-` prefix convention live as
`NNN-slug.md` (`069-map-node-timeout.md`, `030-map-concurrency-control.md`,
`027-…`, `031-…`, `052-…`). On 2026-09-02 the FR-956 and FR-957 research
runs completed all five personas and then failed in the reducer on
exactly these two IDs; the persona output was not persisted. Same
class as FR-701's finding for CAP→FR references. Route: one-line glob
widening (`{number}-*` alongside `FR-{number}[-.]*`) with a RED witness,
its own small FR; until then, briefs that must cite legacy-numbered
prior art use the in-body alternatives table `TEMPLATE.md` sanctions.

**Research-route promotion verifier hashes different bytes than the
launcher on Windows.** `scripts/research.sh` hashes the raw bytes of
`tmp/draft-alternatives.md`, which the reducer writes in Python text
mode — CRLF on Windows (20 CR bytes in the FR-955 artifact).
`scripts/research_preflight.py:303-333` (`verify_promotion`) hashes
`record_text[start:]` after `read_text()` newline normalization, so a
byte-identical promotion reports `mismatched` (FR-955: logged
`3997450c…`, verifier `c557bd45…`). Not CI-gated; unit-tested only
with LF fixtures (`tests/unit/test_fr896_precedent_traceability.py:391`).
FR-951 class (undeclared text boundary). Route: hash normalized bytes on
both sides, or write the artifact with `newline="\n"`; one small FR.

**Pattern 12 documentation drift** (below).

#### Pattern 12 shorthand

`reference/patterns.md` Pattern 12 ("Quality Gate for Map Output",
~line 1113 onward) documents map nodes with `source:` / `prompt:` /
`state_key:` keys. `yamlgraph/schemas/graph-v1.json` and
`yamlgraph/compile/map_compiler.py` accept only `over` / `as` / `node` /
`collect`; the snippet does not load. No FR covers this drift (FR-894
edits `patterns.md` only for cross-links from Patterns 8 and 10). Route:
fold into FR-939's reference update (D-7 of its judgement) if the human
reviewer widens that deliverable, otherwise a one-line docs FR. Recorded
here so the finding has a home; it grants no authority.

---

The original proposal follows, unmodified, as the record of what was
bundled and why.

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
