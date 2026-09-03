# Problem Brief: Isolated Git Remote-Ref Compare-and-Swap for CAP/REQ Reservation

**Prior art:** FR-970 and its judgement (direct predecessor, SPLIT; this
brief is exactly its R-1 successor scope). FR-180 (`scripts/id_registry.py`
Pydantic model, reused unchanged). FR-701 (`validate_registry()` backstop,
unmodified). FR-823 (filename-noun coincidence only, on "ledger"/
"reservation" — a prepaid-billing-ledger concept for a rejected hosted
runner, unrelated to CAP/REQ allocation). FR-754 (flags a hardcoded path
to a nonexistent `yamlgraph/utils/id_registry.py`; the real module is at
`scripts/id_registry.py`, process tooling, not shipped package code — that
FR's concern does not apply here).

## Problem statement

`CAP-XXX`/`REQ-YG-XXX` identifiers are allocated today by reading the
current maximum from committed files and assigning the next integer.
Development happens across 3 devices plus autonomous chaplain automation,
none guaranteed to be online simultaneously. Two allocators reading before
either has pushed pick the same number.

FR-180 (2026-03-10) built a candidate fix, `scripts/id_registry.py`
(confirmed present and functional in the current tree): a Pydantic
`IdRegistry` model with `reserve_ids()` (increments `next_cap`/`next_req`
in memory, appends a `Reservation`) and `save_registry()` (writes the YAML
back to a local path). Neither function performs any git operation —
`reserve_ids`/`save_registry` are a pure local read-modify-write with no
fetch, no compare-and-swap against a remote, and no push. Two allocators
calling `reserve_ids()` from stale local clones still collide identically
to the file-scan approach it was meant to replace; the registry additionally
went stale in practice (`.chaplain/id-registry.yaml`: `next_cap: 94`,
`next_req: 246`, last write 2026-04-19, while the live corpus is past
CAP-170/REQ-YG-580) because nothing forces any allocator to call it.

FR-701 (2026-07-09) diagnosed the same race from the collision side (the
FR-692/FR-700 CAP-195 and REQ-YG-531 double-allocation, with FR-693/FR-700
a separate renumbering incident) and shipped `validate_registry()` in
`scripts/validate_capabilities.py` as a commit-boundary duplicate-detection
gate — a backstop, not a preventive allocation mechanism. It explicitly
declined to build a new reservation/lock service on the grounds that a
commit-boundary gate was cheaper for a "near-zero-cost" event; the FR-970
judgement (2026-09-03) found that cost assessment unsupported by the
recorded incident count and required a real preventive mechanism, scoped
narrowly to the allocation primitive itself (this brief), separate from any
question of which callers must use it (a separate, later brief).

FR-970 (2026-09-03) proposed a preventive mechanism but was judged SPLIT:
it conflated the reservation primitive with allocator-adoption enforcement,
proposed integrating allocation into the judge/review adapters (which must
stay advisory and must never commit or push — a boundary this brief must
not cross), and described "commit and push only that file" without
accounting for git's actual serialization unit (a ref, not an individual
file) or naming a dedicated ledger ref, isolated commit construction,
idempotent-recovery semantics, or a real (non-mocked) concurrency witness.

## Classification

judgement/analysis/generation

## Constraints

- No new server, daemon, or externally-hosted coordination service. The
  only always-available coordination primitive is the existing git remote
  (already required for every allocator to reach in order to file/push an
  FR at all).
- Must operate correctly with 3 independent development devices, none
  guaranteed to be online simultaneously; a device may allocate only when
  it can reach the remote, which is already true of filing an FR today.
- Must not read from, write to, or push the calling allocator's own
  working branch, worktree, or index — allocation must be isolated commit
  construction against its own dedicated ref, per the FR-970 judgement's
  R-1 and C-3 (shared-index/one_session_one_repo risk otherwise).
- Must not touch, modify, weaken, or replace `validate_registry()`
  (`scripts/validate_capabilities.py`) — it remains an independent
  commit-boundary backstop (FR-970 judgement C-7).
- Must not modify, wire into, or add commit/push side effects to any
  judge, review, or graph-authoring adapter (`.github/skills/*/adapters/`)
  — those must remain advisory-only (FR-970 judgement R-2/C-2). This brief
  is the reservation primitive alone; which callers must use it is a
  separate, later scope (FR-970 judgement D-2/R-2).
- Must define typed, non-silent failure outcomes for: offline/unreachable
  remote, authentication failure, remote-policy (branch protection)
  rejection, malformed ledger, non-fast-forward retry exhaustion, and
  ambiguous push result (network drops after the server may have already
  accepted the push). No silent fallback to unprotected local allocation
  on any of these (FR-970 judgement C-4).
- The concurrency proof must exercise a real local bare git remote with at
  least two concurrent allocators starting from the same ledger tip; a
  mocked/stubbed remote cannot substitute (FR-970 judgement C-5, AC-03).

## Witnessed incidents

- FR-692 / FR-700 (per FR-701, 2026-07-09): concurrent allocation of
  `CAP-195` and `REQ-YG-531`; the then-current registry silently merged
  two capabilities under one id and no gate fired at the time.
- FR-693 / FR-700 (per FR-701 and the FR-970 judgement's correction): a
  separate renumbering incident where FR-693's initially claimed band was
  reassigned after FR-700 claimed it first.
- FR-731 (2026-07-14): self-documented as "recurrence #3 of the allocation
  race" for FR numbers specifically (out of this brief's CAP/REQ scope,
  per FR-970 judgement R-4 — cited here only to corroborate that the
  underlying race class recurs across more than one ID namespace).
- FR-081 (2026-02-xx): a REQ ID collision (084-086 already taken) required
  manual reallocation to REQ-YG-087/088/089.
- The FR-180 registry itself, `.chaplain/id-registry.yaml`: no write since
  2026-04-19 despite the live corpus advancing past CAP-170/REQ-YG-580 —
  direct evidence that a purely local, non-git-synchronized reservation
  mechanism does not survive contact with multiple allocators over time,
  independent of whether anyone calls it.
- FR-970 (2026-09-03): judged SPLIT, citing exactly the feasibility gap
  this brief exists to close — no named canonical ref, no isolated commit
  construction, no real concurrency witness, no typed failure table for
  the enumerated remote/retry failure modes.
