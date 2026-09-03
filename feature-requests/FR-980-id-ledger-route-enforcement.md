# Feature Request: Allocator Inventory and Mandatory Route Enforcement for CAP/REQ Reservation (Successor B to FR-970)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1.5 days
**Requested:** 2026-09-03
**First consumer / first event:** the next CAP/REQ allocation attempt on
any of the 3 development devices, or by chaplain automation, after this
lands — the first event is that attempt either returning a
FR-975-committed reservation or failing loudly before any `CAP-XXX`/
`REQ-YG-XXX` string is written, with no silent bypass path remaining.
**Research:** [FR-980.research.md](FR-980.research.md) (5 personas: os-infra-primitivist, data-process-planner, yamlgraph-native-planner, subtractionist, librarian)
**Prior art:** [FR-970](FR-970-load-bearing-atomic-id-allocation.md) / [FR-970.judgement](FR-970-load-bearing-atomic-id-allocation.judgement.md) — direct predecessor; SPLIT, this FR is exactly its Successor B (R-2), depending on Successor A's judged contract (D-2). [FR-975](FR-975-id-ledger-reservation-protocol.md) / [FR-975.judgement](FR-975-id-ledger-reservation-protocol.judgement.md) — Successor A; judged APPROVED WITH REVISIONS, **authority not yet activated** (pending human review, C-1 there). This FR's own authority is gated on that activation (see Constraints). [FR-180](FR-180-plan-phase-id-reservation.md) — its `.chaplain/id-registry.yaml`/`reserve_ids()` is the direct precedent for why an advisory mechanism decays: unwritten since 2026-04-19, proving "the mechanism exists" is not "the mechanism is used." [FR-701](FR-701-capability-registry-consistency-gate.md) — `validate_registry()` in `scripts/validate_capabilities.py`, the commit-boundary backstop this FR does not modify. [FR-767](FR-767-graph-authoring-sole-route.md) — the sole-route PreToolUse-guard pattern this FR's enforcement mechanism mirrors (arm a sentinel, deny unsentineled writes to governed paths), applied here to capability/FR-id writes instead of graph artifacts. Filename-noun matches from the research gate (FR-902, FR-596, FR-823, FR-824, FR-862) are coincidental on "ledger"/"route"/"enforcement" vocabulary in unrelated domains (session lifecycle, plot modelling, hosted runner, bulletin publishing, deviant-art scheduling) — no further disposition needed.

## Summary

Inventory every concrete surface that writes a new `CAP-XXX`/`REQ-YG-XXX`
identifier today, and make each surface either call FR-975's reservation
protocol and receive a committed id, or fail closed before writing — using
a PreToolUse-guard sentinel mechanism mirroring FR-767's proven
graph-authoring pattern, not a new coordination service. Judge, review,
and graph-authoring adapters keep their advisory, no-commit/no-push
contract unchanged; they consume already-reserved ids, never allocate.

## Value Statement

The collision class witnessed four times (FR-692/FR-700, FR-693/FR-700,
FR-081, and FR-180's own registry going unused) becomes structurally
unavailable rather than a documented convention nobody is forced to
follow — closing exactly the gap that made FR-180's reservation registry
decay to dead code four months after it shipped.

## Problem

**The real inventory** (verified by grep against the current tree, not
asserted):

| Surface | Current mechanism | Gap |
|---|---|---|
| Human/agent editing `capabilities/CAP-XXX-name.yaml` + FR markdown directly | No code path at all — a text edit | The sole actual allocation path today; nothing intercepts it |
| `scripts/id_registry.py::reserve_ids()` (FR-180) | Local in-memory counter + local file write | Exists, but nothing in the current authoring flow calls it — dead code for allocation purposes |
| Chaplain automation | Writes CAP/REQ ids autonomously when processing inbox items | Separate code path from human/agent editing; the FR-692/FR-700 incident was exactly a chaplain-vs-human race |
| `scripts/validate_id_registry.py` | CLI wrapper validating `.chaplain/id-registry.yaml`'s internal consistency (FR-180's model) | A **validator**, not an allocator — and a second, differently-scoped validator from FR-701's `validate_capabilities.py::validate_registry()` (which validates the live `capabilities/*.yaml` corpus). The near-identical names (`validate_id_registry.py` vs. `validate_registry()` inside `validate_capabilities.py`) are themselves a small, real drift worth noting but not in this FR's scope to fix. |

No allocator surface today is required to call anything before a
`CAP-XXX`/`REQ-YG-XXX` string is written. FR-975 (once its own authority
activates) gives every allocator a correct protocol to call; nothing yet
makes calling it mandatory.

## Ideal Result

Every one of the four surfaces above either returns a FR-975-committed
reservation before any CAP/REQ string is written, or is mechanically
denied from writing one at all — with no discipline-dependent step, no
advisory convention, and no code path that can silently skip the
protocol the way FR-180's registry was silently skipped for five months.
The judge, review, and graph-authoring adapters are untouched: they
already never allocate, and this FR keeps it that way explicitly rather
than assuming it. The minimal path to this: one PreToolUse guard (mirroring
FR-767's existing, working sentinel pattern) scoped to `capabilities/*.yaml`
and `feature-requests/FR-*.md` writes, plus wiring `reserve_ids()`-shaped
calls to FR-975's protocol at the two surfaces that have real code
(`scripts/id_registry.py` callers, chaplain automation) — no new service,
no new coordination layer beyond FR-975's already-judged ledger.

## Proposed Solution

### 1. Direct file-edit surface: PreToolUse sentinel guard

Mirror FR-767's graph-authoring guard exactly in shape: a governed-path
list (`capabilities/*.yaml`, and new-file creation matching
`feature-requests/FR-[0-9]+-*.md`) is denied for direct write unless a
per-run sentinel is armed. The sentinel is armed only by a thin CLI
wrapper (`scripts/allocate_ids.sh`, new, mirroring `scripts/author.sh`'s
shape) that calls FR-975's protocol, receives a committed reservation, and
arms the sentinel with exactly the reserved ids — a subsequent write of
those specific ids to those specific paths is permitted; any other
`CAP-XXX`/`REQ-YG-XXX` string is still denied. This reuses FR-767's
already-reviewed and working guard infrastructure pattern rather than
inventing a new one.

### 2. `scripts/id_registry.py` callers: retire in favor of FR-975

`reserve_ids()`/`save_registry()` are not modified (FR-975's own R-1
already defines the correct schema separately), but any caller that
still invokes FR-180's local-only path is migrated to call
`scripts/allocate_ids.sh`/FR-975's protocol instead. `scripts/id_registry.py`
itself, `.chaplain/id-registry.yaml`, and `scripts/validate_id_registry.py`
are marked retired (FR-465/466 CAP-retirement precedent), citing this FR,
once no caller remains — not deleted in the same commit that removes the
last caller, to preserve a clean bisectable history.

### 3. Chaplain automation

The chaplain's inbox-processing allocation code path is updated to call
`scripts/allocate_ids.sh`/FR-975's protocol exactly like a human/agent
allocator, using the same idempotency-key contract FR-975 defines (the
chaplain's own run/task id is a natural `request_id`).

### 4. Judge/review/graph-authoring adapters: explicitly untouched

No adapter under `.github/skills/*/adapters/` is modified. Each already
consumes ids reserved during Plan/Enforce; this FR states that contract
explicitly as a gate (see Acceptance Criteria) rather than leaving it
implicit, closing the exact ambiguity FR-970's judgement flagged as a
structural risk in the original combined proposal.

### 5. Human review requirement

The PreToolUse guard addition is enforcement infrastructure. Per FR-970's
C-6/C-8 and the Scripture's `instruction_boundary_uncrossed`, it is
isolated in its own commit and requires explicit human approval before
merge — this FR's own authority for that specific commit is conditioned
on that approval, exactly like the graph-authoring guard's own history.

## Alternatives Considered

(from FR-980.research.md; all five personas' verdicts preserved)

- **Pre-commit hook intercepting capability-file/ARCHITECTURE.md writes**
  (os-infra-primitivist, `pursue`) — a real alternative to the PreToolUse
  sentinel; not adopted as the primary mechanism because a pre-commit
  hook fires only at commit time (a human can still write and view an
  uncommitted collision locally, and multi-file staged commits complicate
  attributing which write needs which reservation), whereas a PreToolUse
  guard denies the write itself, matching FR-767's already-proven pattern
  exactly. Not excluded as a secondary backstop if the sentinel proves
  insufficient in practice.
- **Corpus-census discover-extract-map-reduce pattern with FR-892 tool
  slots** (yamlgraph-native-planner, `pursue`) — considered for the
  *inventory* step (this FR's own table above is exactly that inventory,
  done directly rather than through a census graph); a full census graph
  was judged unnecessary machinery for a four-row, manually-verifiable
  table, consistent with the "smaller alternative complements, never
  replaces, the census" principle only when the corpus is actually large.
- **LedgerDB-style git-native optimistic-concurrency document store**
  (librarian, `pursue`) — an external precedent for the same pattern
  FR-975 already implements; not adopted as a distinct alternative
  because FR-975 already is this pattern for this repo's specific need,
  and adopting a third-party library would violate FR-970's "no new
  externally-hosted or heavyweight dependency" position.
- **Delete the judge/review advisory-only constraint, let them allocate
  from a pre-reserved pool** (subtractionist, `dissent`) — explicitly
  rejected: this directly contradicts FR-970's binding judgement (R-2/C-2)
  and would reintroduce exactly the allocation-by-side-effect risk that
  caused FR-970 to be judged SPLIT in the first place. The "pre-reserved
  pool" framing is preserved conceptually but implemented correctly:
  reservations happen during Plan/Enforce (this FR's §1-3), and judge/
  review only ever *read* an already-committed id, never allocate one.

## Acceptance Criteria

- [ ] AC-01: A fixture test proves a direct write of a new `CAP-XXX` id
      to `capabilities/` without an armed sentinel is denied
- [ ] AC-02: `scripts/allocate_ids.sh <fr-id> --cap N --req M` arms the
      sentinel with exactly the ids FR-975's protocol returned; a
      subsequent write of those exact ids to the expected paths succeeds
- [ ] AC-03: A fixture test proves writing a *different* CAP/REQ id than
      the one the sentinel armed is still denied (the guard checks the
      specific ids, not merely "a sentinel exists")
- [ ] AC-04: Chaplain automation's allocation code path is updated to
      call the same protocol; a test simulates two concurrent chaplain-
      and human-driven allocations and asserts no collision
- [ ] AC-05: A test asserts the judge, review, and graph-authoring
      adapters make zero calls into any allocation function during their
      execution — consuming only ids already present in their input FR
- [ ] AC-06: `scripts/id_registry.py`, `.chaplain/id-registry.yaml`, and
      `scripts/validate_id_registry.py` are marked `status: retired`
      (or file-level equivalent) citing this FR, once no caller remains
- [ ] AC-07: `scripts/validate_capabilities.py::validate_registry()` and
      its tests are unchanged and green
- [ ] AC-08: The PreToolUse guard change lands in its own isolated
      commit, explicitly flagged for human review before merge
- [ ] Changelog fragment in `changelog/unreleased/`
- [ ] Diary entry in `docs/diary/`

## Related

- FR-970, FR-970.judgement — predecessor and governing SPLIT verdict this
  FR discharges (R-2 there)
- FR-975, FR-975.judgement — Successor A, the protocol this FR makes
  mandatory; this FR's authority is gated on FR-975's activation
- FR-180 — the advisory-registry failure mode this FR exists to close;
  its module and registry file retire once superseded (AC-06)
- FR-701 — `validate_registry()` backstop, unmodified
- FR-767 — the PreToolUse sole-route guard pattern this FR reuses
- Scripture: `detection_without_enforcement`, `instruction_boundary_uncrossed`,
  `constraint_over_code`
