# Problem Brief: CAP/REQ ID Allocation Race Across Distributed Devices

**Prior art:** filename-noun hits (`session-accountability-record.md`, `fr-950-windows-bridge-import-brief.md`, `fr956-map-timeout-lifecycle-brief.md`, `fr-888-problem-brief.md`, `fr-929-local-diary-existence-brief.md`) are single-word coincidences ("atomic"/"race"/"push" used in unrelated contexts: session accountability, Windows bridge imports, map-branch timeout lifecycle, main-write locking, diary existence) — none address CAP/REQ id allocation. The real prior art is FR-180 and FR-701, both dispositioned in the FR body below.

## Problem statement

`CAP-XXX` and `REQ-YG-XXX` identifiers are allocated by reading the current
maximum ID from committed files (`capabilities/*.yaml`, `ARCHITECTURE.md`)
and assigning the next integer. Development happens across 3 devices plus
autonomous chaplain automation, all committing to the same git remote
without guaranteed simultaneous connectivity. Two allocators that read the
"next free id" before either has pushed will independently pick the same
number; whichever pushes second must be manually rebased and renumbered
after the fact. A prior attempt to fix this (FR-180, 2026-03-10) built a
reservation registry (`.chaplain/id-registry.yaml` + a `reserve_ids()` API)
but the registry has been stale since 2026-04-19 (`next_cap: 94`,
`next_req: 246`, while the live corpus is past CAP-170/REQ-YG-580) and the
Python module it depended on, `yamlgraph/utils/id_registry.py`, does not
exist in the current tree. A follow-up FR (FR-701, 2026-07-09) explicitly
considered rebuilding an "id-reservation service / allocation lock" and
rejected it, choosing a commit-boundary consistency gate instead
(`validate_registry()` catching duplicates at `req-coverage-strict`) on the
stated grounds that a coordination service is unneeded infrastructure for
a near-zero-cost event.

## Classification

judgement/analysis/generation

## Constraints

- No new server, daemon, or externally-hosted service may be introduced;
  the repo's tooling philosophy is git-native and each of the 3 devices
  must be able to work fully offline except at the moment of push/pull.
- Must not regress or duplicate FR-701's `validate_registry()` commit-
  boundary gate (`scripts/req_coverage.py`), which is implemented and
  relied upon as a backstop.
- Must not reintroduce a registry file or API that can silently go stale
  the way FR-180's `.chaplain/id-registry.yaml` did (last write
  2026-04-19) — any reservation mechanism must be load-bearing (its use
  cannot be optional/bypassable by any allocator, human or automated).
- Chaplain automation and manual human sessions on any of the 3 devices
  must be able to allocate IDs through the same mechanism; a fix that
  only covers one allocator class does not close the gap FR-701 named
  ("no reservation and no uniqueness validation at any boundary").

## Witnessed incidents

- FR-692 / FR-693 (2026-07-xx): chaplain automation independently
  allocated `CAP-195`/`REQ-YG-531` that a concurrent human-authored FR-700
  also claimed; the registry silently merged two capabilities under one
  id and no gate failed at the time (root incident cited by FR-701).
- FR-731 (2026-07-14): self-documents as "recurrence #3 of the allocation
  race" — FR-730 was claimed by two independently-authored FRs
  (`icpc2-chapter-inflation` landed on origin one commit before), forcing
  a rename at judgement time.
- FR-081 (2026-02-xx): "REQ ID collision (084-086 taken)" required manual
  reallocation to REQ-YG-087/088/089 before that FR could proceed.
- Operator-recorded pattern (agent session memory, `collision_by_increment`):
  one session hit four separate FR-number collisions (955/958/961/962)
  in sequence before landing, each requiring re-enumeration of main plus
  all open PRs to find a safe number.
- FR-180's own registry file (`.chaplain/id-registry.yaml`), the prior
  attempted fix, has been dead (unwritten) since 2026-04-19 — direct
  evidence that a voluntary/advisory reservation mechanism does not
  survive contact with multiple allocators over time.
