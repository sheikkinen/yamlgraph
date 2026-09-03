# Feature Request: Load-Bearing Atomic ID Allocation for CAP/REQ (successor to FR-180)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-09-03
**First consumer / first event:** every allocator (3 development devices +
chaplain automation) that needs a new `CAP-XXX` or `REQ-YG-XXX` id — the
first event is the next FR filed after this one lands, which must succeed
without a manual renumber.
**Research:** [FR-970.research.md](FR-970.research.md) (5 personas: os-infra-primitivist, data-process-planner, yamlgraph-native-planner, subtractionist, librarian)
**Prior art:** FR-180 (Plan-Phase ID Reservation, Approved 2026-03-10) — direct predecessor, superseded; its registry (`.chaplain/id-registry.yaml`) is dead since 2026-04-19, cited as evidence in Problem below. FR-701 (Capability Registry Consistency Gate, Proposed) — diagnosed the same race, explicitly rejected an "id-reservation service / allocation lock"; this FR's mechanism is deliberately not that (git-native push atomicity inside a mandatory node, not a new lock service) and keeps FR-701's gate as backstop, not a replacement. The research brief's filename-noun hits (session-accountability-record.md, fr-950/fr956/fr-888/fr-929) are single-word coincidences on "atomic"/"race"/"push" in unrelated domains — dispositioned as no-overlap.

## Summary

Replace the dead FR-180 reservation registry with a **git-native, load-bearing**
allocation mechanism: ID allocation happens inside the mandatory graph
compilation step every FR-authoring/enforcement route already runs through,
and the actual serialization primitive is git's own atomic remote push
(fast-forward-or-reject), not a new lock service. FR-701's
`validate_registry()` commit-boundary gate stays as the backstop.

## Value Statement

Every allocator on any of the 3 development devices, and the chaplain
automation, gets a collision-free `CAP-XXX`/`REQ-YG-XXX` id without a new
server, a daemon, or an always-online dependency — closing the gap FR-701
explicitly left open ("no reservation and no uniqueness validation at any
boundary") without reintroducing the coordination infrastructure FR-701
correctly rejected building as a separate service.

## Problem

`CAP-XXX`/`REQ-YG-XXX` ids are allocated by reading the current max from
committed files. Two allocators reading before either has pushed pick the
same number. Witnessed repeatedly: FR-081 (REQ collision), FR-692/693
(CAP-195/REQ-YG-531 silently double-claimed, no gate fired), FR-731
("recurrence #3 of the allocation race"), and a recorded agent-session
pattern of four FR-number collisions in one sitting.

FR-180 (2026-03-10) already built the "typical database" answer — a
reservation registry (`.chaplain/id-registry.yaml`) with a `reserve_ids()`
API. It is dead: `next_cap: 94` / `next_req: 246`, last write 2026-04-19,
while the live corpus is past CAP-170/REQ-YG-580; the Python module
(`yamlgraph/utils/id_registry.py`) no longer exists on disk. FR-701
(2026-07-09) diagnosed the same class of failure and explicitly considered
rebuilding an "id-reservation service / allocation lock," rejecting it as
unneeded coordination infrastructure for a "near-zero-cost" event — a cost
assessment the incident record (3+ named collisions since) does not
support. FR-701 shipped a commit-boundary consistency gate instead, which
catches collisions but does not prevent the renumbering tax.

**Root cause, per the research's convergent finding (2 personas
independently agreed):** allocation is advisory. Nothing forces every
allocator through one mechanism, and any registry that is optional decays
to unused, exactly as FR-180's did.

## Proposed Solution

Two changes, combining the research's converging candidates
(yamlgraph-native-planner + data-process-planner, both `pursue`, both
independently landed on "make allocation load-bearing inside a path every
allocator already must take"):

### 1. `allocate_ids` — mandatory graph node, not an optional API call

A Python node (`yamlgraph/utils/id_allocation.py`) that:
- Scans the live corpus (`capabilities/*.yaml`, `ARCHITECTURE.md`) for the
  current max `CAP`/`REQ-YG` id — the existing, already-correct read path.
- Writes the allocated id(s) into graph state before any downstream
  FR/CAP-authoring node executes.
- Is wired into the FR-authoring and judge adapter graphs
  (`.github/skills/*/adapters/graph.yaml`) as a **required** node — not an
  optional pre-step a human can skip, mirroring FR-767's sole-route
  enforcement pattern for graph authoring.

### 2. Atomic reservation via git's own push, not a new lock service

At the moment `allocate_ids` computes a candidate id, it immediately:
1. Appends one line to a git-tracked append-only ledger
   (`.chaplain/id-ledger.log` — replacing the stale `id-registry.yaml`
   shape with a pure append log per the librarian persona's convergent
   event-sourcing candidate).
2. Commits and pushes **only that file** to origin.
3. If the push is rejected (non-fast-forward — another allocator won the
   race), fetches, replays the ledger to find the new max, recomputes,
   and retries. Bounded retries; terminates because exactly one push can
   land per parent commit.
4. If the push succeeds, the id is allocated, globally, with no lock
   service, no daemon, and no requirement that any other device be
   online at that moment — only that the allocator itself can reach
   origin, which is already required to file the FR at all.

FR-701's `validate_registry()` gate is unchanged and remains the
commit-boundary backstop (defense in depth, not a replacement).

## Alternatives Considered

(from FR-970.research.md, all five personas' verdicts preserved)

- **`.git/index.lock`-style local file-creation atomicity**
  (os-infra-primitivist, `pursue`) — viable but scoped to a single
  device's local git operations; doesn't by itself serialize across 3
  independent devices the way a remote push does. Superseded by the
  remote-push mechanism above, which generalizes the same "OS/VCS
  already provides atomicity" insight to the actual distributed case.
- **Commit-trailer declaration validated by a pre-commit hook**
  (data-process-planner, `pursue`) — a real alternative encoding; rejected
  in favor of a dedicated ledger file because a trailer is per-commit
  metadata, harder to replay/audit as a standalone sequence, and doesn't
  cleanly support the fetch-and-retry loop on rejection.
- **Delete the registry entirely, rely solely on FR-701's gate**
  (subtractionist, `dissent`) — explicitly rejected: the subtractionist's
  own citation of FR-692/693 is the proof this fails — the gate did not
  catch that collision before merge; detection-only is not sufficient
  when the renumbering cost is real and recurring.
- **Pure event-sourcing append-only log** (librarian, `pursue`) — adopted
  as the ledger *shape* (§Proposed Solution part 2), combined with the
  graph-native mandatory allocation node rather than left as a standalone
  log anyone may or may not consult.

## Acceptance Criteria

- [ ] `yamlgraph/utils/id_allocation.py` implements ledger-append +
      push + fetch-retry-on-rejection; unit test simulates a rejected
      push (mocked remote) and asserts recomputation + successful retry
- [ ] `allocate_ids` node wired into the FR-authoring and judge adapter
      graphs as a required (non-skippable) step
- [ ] `.chaplain/id-registry.yaml` and any dead `reserve_ids()` references
      removed or explicitly marked retired, citing this FR
- [ ] FR-701's `validate_registry()` gate untouched and still green
- [ ] Fixture test reproducing the FR-692/693 double-allocation scenario
      now fails fast at allocation time (not just at commit-boundary
      validation)
- [ ] Changelog fragment in `changelog/unreleased/`
- [ ] Diary entry in `docs/diary/`

## Related

- FR-180 (Plan-Phase ID Reservation) — prior attempt, superseded; its
  registry file is dead evidence cited above
- FR-701 (Capability Registry Consistency Gate) — the commit-boundary
  backstop this FR complements, not replaces
- FR-692, FR-693, FR-731, FR-081 — witnessed collision incidents
- FR-767 (graph-authoring sole-route enforcement) — the mandatory-node
  pattern this FR mirrors for id allocation
- Scripture: `detection_without_enforcement`, `collision_by_increment`,
  `constraint_over_code`
