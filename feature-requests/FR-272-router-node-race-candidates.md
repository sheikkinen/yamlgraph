# Feature Request: Router node with `candidates:` race support

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1–2 days
**Requested:** 2026-04-22
**Judged:** 2026-04-22
**Implemented:** 2026-04-22

## Summary

Extend the `router` node type to accept a `candidates: [...]` list (same shape
as `race`), racing them for the routing decision and cancelling losers. Routing
semantics (`route_field`, `routes`, `default_route`) remain unchanged. Builds on
FR-267, FR-270, and FR-271 which made `race` production-safe.

## Value Statement

Classification prompts on the critical path — where a caller is waiting in
silence — cease to stall on a single provider's tail latency. One provider's
regional hiccup or rate-limit blip no longer blocks the entire decision. No
new node type, no new abstraction for graph authors: the existing `router`
becomes race-capable by adding a config list.

## Problem

`router` nodes today invoke one provider. When that provider stalls, the
graph waits. Observed in production ninchat_voice call
`CA0ec7f9b5b306d2e2e9616698a4083de2` (2026-04-22): the navigator's
`classify` router took 12.7 s to decide between `medical_triage /
elderlycare / crisis`, blocking the caller in silence for the entire
window before a different bug compounded the outcome. (Unrelated to this
FR; see ninchat_voice NC-244 for the compound incident.)

The downstream workaround today is to rewrite the router as:

```
classify (race, parse_json, state_key: intent)
  → branch_on_intent (python function dispatching on state.intent)
  → [switch_to_triage | switch_to_interrai | crisis_response]
```

This works but:

1. **Duplicates router semantics.** The `route_field → routes` mapping is
   literally what `router` does. Every project that needs low-latency
   classification reimplements it.
2. **Adds a node per call site.** Navigator gains 1–2 nodes; medical_triage's
   `classify_recap` would also need the pattern. Two projects (ninchat_voice,
   customer-service-agent-platform) both face this.
3. **Loses the `router` declarative clarity.** Graph authors reading the YAML
   see `race + python + conditional edges` instead of one `router` block.
4. **Separate maintenance.** Future router features (`default_route`
   semantics, routing telemetry, etc.) don't apply to the local rewrite.

`extract_fields` (medical_triage) and similar structured-output races
already use `race` correctly. The gap is specifically for the
*race-then-route* pattern that `router` captures.

## Proposed Solution

Accept `candidates:` on `router` nodes with identical schema to `race`:

```yaml
classify:
  type: router
  prompt: classify
  parse_json: true
  route_field: intent
  timeout: 10.0
  candidates:
    - { provider: vertex,    model: gemini-2.5-flash }
    - { provider: anthropic, model: claude-haiku-4-5 }
  routes:
    medical_triage: switch_to_triage
    elderlycare:    switch_to_interrai
    crisis:         crisis_response
  default_route: switch_to_triage
```

### Semantics

- **With `candidates:` present:** execute as a race (per FR-271 async
  cancellable semantics). First non-error, parse-valid result wins. Losers
  are cancelled. Extract `route_field` from winner's output, look up in
  `routes`, route accordingly. Fall back to `default_route` if the value is
  missing or unmapped.
- **Without `candidates:` (legacy):** unchanged single-provider behaviour.
- **Mutual exclusion:** `provider:` + `candidates:` together is a config
  error, raised at compile time. Same rule as `race`.
- **`timeout:`:** race-level budget, same semantics as `race`. If exceeded
  with no valid winner, routing falls back to `default_route` and records
  an error (via the node's existing `on_error:` policy).
- **`parse_json:`:** a candidate producing malformed JSON is treated as a
  failed candidate and disqualified; others continue. Same as `race`.
- **Winner disqualification:** if a winner's `route_field` is missing,
  attempt the next completed candidate. If all candidates are disqualified,
  treat as timeout → `default_route`.

### Implementation sketch

In `yamlgraph/node_factory/llm_nodes.py`:

1. Extend `LLMNodeConfig` to accept optional `candidates:` on router nodes
   (same validator path `race` already uses).
2. In the node factory for `NodeType.ROUTER`, branch on
   `cfg.candidates is not None`:
   - If set: delegate to the existing race execution path (refactored out of
     `race_node.py` into a shared `_race_core()` helper if not already).
   - Otherwise: existing single-provider execution.
3. Routing resolution (`_resolve_router_routing`) is unchanged — it operates
   on the winner's structured output just like it does today on the single
   provider's output.
4. Tests: new `tests/unit/test_router_race.py` mirroring
   `test_race_node.py` with routing assertions.

### Shared refactor opportunity

`race` and `router` would both call `_race_core(candidates, prompt,
parse_json, timeout) -> winner_output`. `llm` node (if we ever want
`candidates:` there too — not proposed here) could follow. Graduating
`candidates:` to a first-class mixin is out of scope for this FR; prove the
pattern in `router` first.

## Alternatives Considered

- **Add a new `race_router` node type.** Rejected: introduces a second
  routing concept for graph authors to learn, duplicates routing
  resolution logic, and breaks the "one node per concept" line.
- **Expose `race` with a `routes:` block.** Rejected: puts routing logic
  on a node whose identity is "race". Harder to read, easier to misuse
  (routing on a race that isn't meant to drive control flow).
- **Keep the downstream rewrite as the permanent answer.** Rejected: this
  is the third or fourth project facing this pattern. Local copies drift.

## Acceptance Criteria

1. ✅ **Router with `candidates:` races and routes.** A router node configured
   with two candidates and `parse_json: true` produces correct routing
   behaviour when either candidate is first-to-complete. Tested with
   controlled async mock providers.
2. ✅ **Losers are cancelled.** When a winner emerges, pending candidates
   receive `asyncio.Task.cancel()` before the router returns (inherits
   FR-271 semantics). Verified by instrumented candidates.
3. ✅ **Malformed-JSON candidate: not fatal.** Per Judgement amendment: winner
   disqualification dropped. A winner with no matching `route_field` falls
   to `default_route` — same as single-provider router. No exception raised.
4. ✅ **Timeout falls back to `default_route`.** When all candidates exceed
   `timeout`, routing uses `default_route` and records an error. No exception
   propagated unless `on_error: fail` (which raises `AllCandidatesFailedError`).
5. ✅ **Mutually exclusive config rejected.** `provider:` + `candidates:` on
   the same router raises at graph compile time. `on_error: skip` also rejected.
6. ✅ **No regression in single-provider routers.** Existing router tests pass
   unchanged.
7. ✅ **Telemetry parity with `race`.** `_race_winner: {provider, model}` set
   in state; compiler skips `_maybe_wrap_timeout` for router-with-candidates.

## Out of Scope

- Adding `candidates:` to `llm` or `copilot` nodes. Follow-up if the pattern
  proves itself in `router`.
- Routing based on arbitrary quorum / consensus across candidates.
  First-valid-wins only.
- Streaming outputs from a race-capable router. Race node doesn't support
  streaming; this FR inherits that limitation.
- Per-candidate prompts or variables. All candidates share the same
  rendered prompt, same as `race`.

## References

- FR-267 race node timeout double-wrap (#155, merged)
- FR-270 pool shutdown non-blocking (#168, merged)
- FR-271 async race node cancellable (#171, merged in v0.4.71)
- ninchat_voice NC-247 (local race-then-route rewrite filed as tactical
  fix; expected to revert to this FR's native form once shipped)
- [yamlgraph/node_factory/llm_nodes.py](yamlgraph/node_factory/llm_nodes.py)
  `_resolve_route` — routing resolution already separated from
  LLM invocation, making this extension tractable.

---

## Judgement

**Verdict: Approved with amendments.**

### Assessment

The FR is well-structured, addresses a real production-observed problem
(12.7 s classify stall), and proposes a minimal extension of an existing
concept rather than a new abstraction. The scope is tight. The acceptance
criteria are mostly precise and testable. The chain of prior FRs
(267 → 270 → 271) that made race production-safe is solid foundation.

### Amendments required before implementation

#### 1. Drop winner disqualification — use `default_route` instead

The FR proposes: "if a winner's `route_field` is missing, attempt the next
completed candidate." This is incompatible with the current `_race_async`
contract, which cancels all losers immediately on first success
(`loser.cancel()` at line 130 of `race_node.py`). Supporting
disqualification-then-retry would require either:

- Deferring cancellation until routing validates (adds latency, complexity)
- Adding a validation predicate to `_invoke_candidate_async` (couples race
  to routing semantics)

**Amendment:** If the winner's `route_field` value is missing from `routes`,
fall through to `default_route`. This matches existing single-provider
router behaviour (which already does this in `_resolve_route`) and keeps
the race contract unchanged. Update the "Winner disqualification" semantic
and acceptance criterion 3 accordingly.

#### 2. Clarify compile-path timeout handling

`NodeType.ROUTER` currently maps to `_compile_llm_node` in
`NODE_TYPE_HANDLERS` (`node_compiler.py`). The `_compile_llm_node` handler
wraps nodes with `_maybe_wrap_timeout`. But race nodes explicitly skip this
wrapper (FR-267) because the race manages its own deadline internally.

**Amendment:** When a router has `candidates:`, the compile path must skip
`_maybe_wrap_timeout` — the race deadline is authoritative. Document this
branching explicitly in the implementation sketch. Preferred approach:
branch inside `_compile_llm_node` based on `node_config.candidates`.

#### 3. Clarify `on_error` + timeout + router interaction

The FR says timeout falls back to `default_route` and records an error.
But `on_error: fail` should raise, not silently route. And `on_error: skip`
is semantically impossible on a router (a router MUST produce `_route`).

**Amendment:** Define the interaction matrix:

| `on_error`     | Timeout / all-fail behaviour                              |
|----------------|-----------------------------------------------------------|
| `fail` (default) | Raise `AllCandidatesFailedError` — no routing.          |
| `skip`         | Invalid on router nodes — reject at compile time.         |
| `fallback`     | Route via `default_route`, record error.                  |
| (unset)        | Route via `default_route`, record error.                  |

#### 4. Fix function name reference

The references section cites `_resolve_router_routing`. The actual function
is `_resolve_route` in `llm_nodes.py` (line ~241). Cosmetic but should not
mislead the implementer.

#### 5. `_race_winner` metadata on router results

The race node sets `_race_winner: {provider, model}` on its state output.
Router-with-candidates should do the same for telemetry and debugging
parity. Note this in the implementation sketch.

### Items confirmed correct

- **Mutual exclusion** (`provider:` + `candidates:` → compile error) — add
  to `NodeConfig.validate_node_requirements()` in `graph_schema.py`.
- **Routing resolution unchanged** — `_resolve_route(cfg, result)` operates
  on winner output the same way it does on single-provider output.
- **Refactor path** — extract `_race_async` + `_invoke_candidate_async` +
  `_run_coro_sync_safe` into a shared importable surface (or simply import
  from `race_node.py`). No new `_race_core()` wrapper needed — the existing
  functions are already well-factored.
- **Test plan** — new `test_router_race.py` mirroring race test patterns
  with routing assertions. Sound approach.
- **Effort estimate** — 1–2 days is realistic given the existing separation
  of concerns.

### Scope confirmed frozen

No `candidates:` on `llm` or `copilot` nodes. No streaming. No consensus.
No per-candidate prompts. First-valid-wins only.
