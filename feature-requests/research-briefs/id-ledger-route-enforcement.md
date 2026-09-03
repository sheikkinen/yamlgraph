# Problem Brief: Allocator Inventory and Mandatory Route Enforcement for CAP/REQ Reservation

**Prior art:** FR-970 and its judgement (direct predecessor, SPLIT; this
brief is exactly its R-2 successor scope). FR-975 and its judgement
(Successor A, the reservation protocol this brief makes mandatory;
authority not yet activated, pending human review). FR-180
(`.chaplain/id-registry.yaml`/`reserve_ids()`, the advisory-mechanism
failure precedent). FR-701 (`validate_registry()` backstop, unmodified).
FR-767 (graph-authoring PreToolUse sole-route guard, the enforcement
pattern this brief reuses).

## Problem statement

FR-970 (2026-09-03, judged SPLIT) identified that CAP/REQ id collisions
recur (FR-692/FR-700, FR-693/FR-700, FR-081) because no allocator is
*required* to go through any preventive reservation mechanism — allocation
is advisory, and an advisory mechanism decays to unused (FR-180's own
`.chaplain/id-registry.yaml` registry has been stale since 2026-04-19,
proof that "the mechanism exists" is not the same as "the mechanism is
used"). FR-970's judgement required this concern be split from the
reservation-primitive itself (Successor A) into a separate FR: an
inventory of every actual CAP/REQ allocator (feature-request planning,
enforcement, chaplain automation, direct human/operator allocation on any
of 3 development devices) and a mandatory route — or a mechanical denial
— at every bypassable surface, so that an allocator either returns a
committed reservation from the (now separately judged) protocol or fails
before writing a CAP/REQ identifier at all. FR-975 (Successor A, judged
APPROVED WITH REVISIONS 2026-09-03, authority pending human review)
defines that protocol: `scripts/id_ledger.py`, a `refs/heads/id-ledger`
git-ref compare-and-swap boundary, with typed non-silent failures. This
brief's scope is exclusively the adoption/enforcement side: which
surfaces write CAP/REQ ids today, and how each is made to call FR-975's
protocol or refuse to write, without touching FR-975's protocol internals
or any judge/review adapter's advisory contract.

## Classification

judgement/analysis/generation

## Constraints

- Depends on FR-975's judged contract (its Pydantic reservation model,
  typed `LedgerError` hierarchy, and `allocate()`/equivalent call surface)
  as an external, unmodified dependency; this brief may not redesign or
  re-litigate FR-975's protocol internals (its own scope, already judged).
  If FR-975's authority has not yet activated (pending human review) when
  this brief's FR is written, this FR's own authority is gated on that
  activation — it must say so explicitly, not assume it.
- Must preserve the judge, review, and graph-authoring adapters'
  advisory-only, no-commit/no-push contract exactly as FR-970's judgement
  requires (R-2/C-2 there): none of them may call an allocation function
  that itself commits/pushes. If an adapter needs a reserved id, it must
  consume an id already reserved during Plan or Enforce, never allocate
  by side effect during Judge or Review.
- Must name every concrete executable surface that writes a `CAP-XXX` or
  `REQ-YG-XXX` string into a capability file, `ARCHITECTURE.md`, or a test
  marker today, not a generic description — the inventory is itself a
  literal grep-verifiable artifact, checked into the FR or a linked
  document, not asserted in prose.
- Must not modify `validate_registry()` (`scripts/validate_capabilities.py`)
  — it remains the independent commit-boundary backstop (FR-970 C-7,
  carried forward).
- Must not modify FR-975's `scripts/id_ledger.py` internals, schema, or
  the `refs/heads/id-ledger` ref's write path — this brief only adds
  *callers* of that already-defined interface, or denial checks at
  surfaces that currently bypass it.
- Any proposed hook, adapter, or CI change that becomes enforcement
  infrastructure requires explicit human review before merge, mirroring
  FR-970's C-6/C-8 and the graph-authoring sole-route precedent (FR-767)
  — this brief must name that review requirement, not assume tacit
  approval.
- Must work correctly with 3 independent development devices plus
  chaplain automation, none guaranteed online simultaneously — the same
  operating constraint as FR-975.

## Witnessed incidents

- FR-692 / FR-700 (per FR-701): concurrent allocation of `CAP-195` and
  `REQ-YG-531` merged silently under one id; no gate fired at allocation
  time because no allocator was required to reserve before writing.
- FR-693 / FR-700 (per FR-701 and FR-970's judgement correction): a
  separate renumbering incident with the same root cause — no mandatory
  route.
- FR-081: a manual REQ ID reallocation (084-086 already taken) — same
  root cause, an earlier incident predating FR-180's registry attempt.
- FR-180's `.chaplain/id-registry.yaml`: `next_cap: 94`/`next_req: 246`,
  unwritten since 2026-04-19, while the live corpus is past CAP-170/
  REQ-YG-580 — the registry existed and was never made a mandatory route,
  so it was simply not called and went stale. This is the direct
  precedent for why "build a protocol" (FR-975) is necessary but not
  sufficient — this brief exists because that exact failure mode must not
  repeat with the new ledger protocol.
- FR-970's own judgement (2026-09-03): explicitly required this inventory
  and mandatory-route FR as Successor B (R-2), separate from the
  reservation primitive, and named the constraint that judge/review
  adapters must remain advisory (carried into this brief's constraints).
