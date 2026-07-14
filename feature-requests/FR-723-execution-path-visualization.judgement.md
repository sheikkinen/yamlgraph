# Judgement: FR-723 Execution Path Visualization (2026-07-14)

**Verdict: APPROVED WITH REVISIONS.** This is the right kind of framework
FR: a design proven project-locally (NC-372/373, enforced 2026-07-14),
ported to the boundary with *the prototype's own failure log as the
justification* — and the Raw Output Read contains a genuine surprising
detail (the loop-exit hole) that a generated dump could not produce. The
graduation criterion ("second project asks" — NC-372's purge list) is
satisfied by the FR's consumer list. Three revisions.

## Verified by the Judge

- **routing.py is the seam claimed:** 103 lines, `make_router_fn` +
  `make_expr_router_fn` + `evaluate_condition`. The loop-exit branch
  (L76–80) returns `END`/target with **no log line of any kind** — the
  "sixth seam, invisible by construction" claim is source-true; condition
  matches get only a `logger.debug`.
- **The condemning evidence is real:** ninchat NC-373 enforce log shows
  `99edb4e` "the fifth seam was missing" — per-project emission missed a
  seam on day one exactly as the Problem section says. `emit_route` calls
  live in flex_navigator.py (L140, L277, …) ready for the shim-and-delete
  migration.
- **CAP-06/CAP-10 exist** for AC-06's REQ placement. LangSmith rejection
  consistent with NC-373's ruling and FR-713/NC-367 evidence.

## R-1 (`thread_id` is not reachable from the proposed seam — resolve, don't hand-wave)

The proposed line carries `"thread_id":<from config>`, but both router fns
receive **`state` only** — no `RunnableConfig` in their signatures, and
`evaluate_condition` likewise. The thread id lives in
`config["configurable"]["thread_id"]`, which routing.py never sees. Ruling:
pick the mechanism at judgement, not mid-enforce — options in preference
order: (a) a **contextvar** set by the executor/run entrypoints around
graph invocation (zero signature churn, works for both router fns and any
future seam); (b) LangGraph's config-injected conditional-edge signature
(`(state, config)`) — verify version support before choosing. Absent
either, the field is emitted as `null` — never fabricated. AC-01 gains the
assertion: route lines carry the same thread_id the run was invoked with.

## R-2 (map fan-out target must emit a name, not a `Send` repr)

`expr_router_fn` can return `map_edge_fn(state)` — `Send` objects — as the
routing outcome. The hook's `"target"` field for that branch must emit the
**map-node name + fan-out count** (`{"target":"process_items","fan_out":4}`),
not `repr(Send)` (unbounded, state-leaking — violates the FR's own
privacy-by-construction rule, since `Send` payloads carry state content).
Add to AC-01's fixture matrix: a map fan-out decision emits name+count and
no state content (the privacy assertion made testable).

## R-3 (migration NC is part of this FR's definition of done)

The migration note says ninchat's five `emit_route` calls "MUST be deleted"
— but that work lives in another repo and will not happen by gravity.
Ruling: AC-06 extends — the ninchat migration NC is **filed (not enforced)**
before FR-723 merges, and the framework grammar records one compatibility
fact for it: ninchat's parser keys on `call_sid` in a `📋 FACTS:` prefixed
line; the framework emits `event:route` JSON on the `yamlgraph.route`
logger with `thread_id`. The NC owns the mapping (ninchat sets
thread_id=call_sid at invocation — it already does — so the shim is a
prefix/field rename, small by design). Without the filed NC, the shim
lingers and the no-shims commandment is violated by omission.

## Advisories (no AC changes)

- `make_router_fn` (the simple state-value router, L21–44) also decides —
  the FR's "both router fns" covers it; ensure the fixture matrix includes
  one simple-router decision so the hook isn't accidentally expr-only.
- Export view (piece 2) should mark the loop-exit edge explicitly
  (`loop_exit → recap` as a rendered edge) — the hole this FR closes
  deserves to be visible on the authored map, not only in route lines.
- Logger namespace `yamlgraph.route` — document that downstream projects
  attach handlers/filters there; that IS the public API surface of piece 1.

## Blast-radius ruling

The hook touches the hottest path in the framework (every conditional edge
of every graph) — the zero-overhead-when-off guard (AC-01's mock assert)
is the load-bearing criterion; keep it first in enforce. Export/overlay
are CLI-side, read-only. Migration blast lands in ninchat_voice via its
own NC (R-3). New REQs under CAP-06/CAP-10 per AC-06; changelog fragment
and demo gate already in the ACs.

## Ruling

APPROVED upon folding R-1 (thread_id mechanism chosen: contextvar
preferred, null never fabricated), R-2 (map fan-out emits name+count,
privacy assertion testable), R-3 (ninchat migration NC filed before
merge; grammar compatibility fact recorded). Advisories at enforcer's
discretion. The boundary argument — two seams the prototype missed, both
impossible to miss at routing.py — is the strongest single justification
in the FR; it stands as written.
