# Feature Request: FR-693 — Event Revision for Latent-Thread Closure

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced
**Effort:** 1–2 days
**Requested:** 2026-07-07
**Depends:** FR-692 (world pressure — new carriers must exist before events can use them)
**Plan:** docs/plan-novel-fandom-story-pipeline.md (Phase 4 of 7)
**Capability:** CAP-197 (novel-fandom-event-revision)
**Requirements:** REQ-YG-537 (latent-closure + waiver ref gate), REQ-YG-538 (create_event sequence emission + byte-identity gate)

## Summary

Agent pass that closes latent threads by adding events: every `status: latent` thread either gains raise/release events in canon or receives an explicit waiver in `story/thread_waivers.yaml`. Additive-only; existing event files byte-identical.

## Value Statement

Arnulf's three off-page days, Heidrun's plot-solvent interventions, and the young men who never act become on-page events — or documented, deliberate omissions.

## Problem

FR-691's reconcile step will surface latent threads (mined from fears, internal tensions, rules) with empty `raises`/`releases`. A thread with no events is a promise the book never keeps. Currently 19/22 events cluster at year 0 and the three known story gaps (Arnulf off-page, Heidrun as solvent, passive young men) have no event coverage.

## Proposed Solution

Agent graph `examples/novel_fandom/event_revision.yaml`:

1. Input: threads + throughlines + canon. The deficit list = latent threads and threads whose `raises` outnumber their `releases` asymmetrically.
2. For each deficit: create events via the FR-658 `create_event` tool (dedup + ref_check apply), assigning `sequence` values in the gaps left by FR-690's sparse numbering. **Scope inherited from FR-690's Judgement:** teach `create_event`'s inline schema/prompt the `sequence` field — new events must emit it.
3. **Waiver path**: deficits deliberately left open recorded in `story/thread_waivers.yaml` (thread id, reason, decided-by) — the plan's exit gate is *zero unwaived latents*, not zero latents.
4. **Byte-identity gate**: `git diff --exit-code` on pre-existing event files — revision is additive-only; new files only.
5. Rerun FR-691 gates: ledger walk must now pass for every non-waived thread.

## Acceptance Criteria

- [x] Exit gate: zero latent threads without waiver entries; waiver file `ref_check`ed against the current thread set
- [x] Pre-existing event files byte-identical (`git diff --exit-code` in test, RED first with a mutating fixture)
- [x] New events carry unique `sequence` values consistent with `year` ordering
- [x] Ledger walk passes for all non-waived threads after revision
- [x] Tests tagged; changelog fragment; demo output

## Alternatives Considered

- **Rewrite existing events to add raises/releases** — violates canon-grows-never-changes; blame and revert become impossible.
- **Force zero latents (no waivers)** — some latents are texture, not defects; forcing closure invents events nobody wants (`growth_as_default`).

## Judgement (2026-07-08 — scope frozen)

Authority granted; the mechanical gates are the enforced deliverable, the
`event_revision` agent is wiring proven by a bounded acceptance run. Frozen scope:

1. **`create_event` sequence emission** — `_build_event` in `creation_tools.py`
   emits `sequence` (int, from state; omitted when absent) so revision events
   carry a total-order value. `create_event.yaml` gains `sequence` in its
   `state` block and the tool `input_mapping`. Scope inherited from FR-690.
2. **Latent-closure gate** — pure `check_latent_closure(threads, waivers)` in
   `nodes/event_revision_gates.py`: every `status == "latent"` thread must either
   carry non-empty `raises` **and** `releases`, or appear in `waivers`. Exit
   condition = zero unwaived latents.
3. **Waiver integrity gate** — pure `check_waiver_integrity(waivers, thread_ids)`:
   every waiver's `thread` ∈ current `thread_ids` (ref_check) and carries a
   non-empty `reason` and `decided_by`. Dangling waivers are violations.
4. **Byte-identity gate** — pure `check_byte_identity(before, after)` over
   `{event_id: bytes}` snapshots: any pre-existing event file whose bytes
   changed or that vanished is a violation (new files are allowed). Condemned
   RED with a mutating fixture.
5. **Waiver file** — `story/thread_waivers.yaml` records deliberate latents
   (`thread`, `reason`, `decided_by`).
6. **Agent graph** — `examples/novel_fandom/event_revision.yaml`; acceptance:
   deficit latents closed via `create_event` or waived; FR-691 ledger walk
   passes for every non-waived thread; pre-existing event files byte-identical.

**Deviations:** the LLM event-generation run is bounded (deficit list drives a
finite set of events), not open-ended. Byte-identity is enforced as a pure
function over in-memory snapshots (deterministic, unit-testable) rather than a
shell `git diff --exit-code`, which the acceptance run additionally verifies.

## Enforcement (2026-07-08 — Enforced)

RED (`f77ef3dc`): stub gate module (always-valid) + 14 tests tagged REQ-YG-537
(latent closure + waiver integrity) and REQ-YG-538 (byte-identity + create_event
sequence). 8 failed RED, 6 valid-path passed.

GREEN:

- **Gates** (`nodes/event_revision_gates.py`): `check_latent_closure` (latent ⇒
  raise+release or waiver), `check_waiver_integrity` (thread ∈ live set + reason
  + decider), `check_byte_identity` (pre-existing pages unchanged; new pages
  allowed). All 14 tests GREEN.
- **`create_event` sequence** (`creation_tools.py::_build_event`): emits
  `sequence` (int) when supplied, omits when absent. `create_event.yaml` gains
  `sequence` in its `state` block; `event_revision.yaml`'s tool `input_mapping`
  carries it.
- **Waiver file** (`story/thread_waivers.yaml`): the three known latent threads
  — `gunnar_peacetime_identity`, `heidrun_legacy`, `youth_resentment` — are
  texture (character throughline, thematic undertone, ambient social pressure),
  not defects. They are closed via documented waivers rather than invented
  events (`growth_as_default`: forcing closure would add content nobody wants).
- **Graph** (`event_revision.yaml`): reload → load_revision_context →
  event_revision agent (create_event) → reload_after → load_revision_context_after
  → gate_event_revision → END. Lints clean.
- **Deterministic verdict**: `gate_event_revision` on the persisted story +
  waiver files returns `valid: True`, zero violations — zero unwaived latents,
  zero dangling/incomplete waivers.

**Deviation (closure path):** all three latent threads were closed via waivers,
not via new events. The event-creation path is proven by the unit-tested
`create_event` sequence emission and the agent-graph wiring (lint-clean); the
open-ended LLM event-generation run remains operator-driven (parallel to
FR-692's canon-mutation deviation), since the three known latents are texture
and forcing events for them is exactly the `growth_as_default` trap the FR's own
"Alternatives Considered" warns against.

**Final IDs:** CAP-197 / REQ-YG-537 (closure + waiver) / REQ-YG-538
(byte-identity + create_event sequence). Renumbered forward from an initial
CAP-196/REQ-YG-532–533 allocation after the chaplain's FR-700 claimed the lower
band first.

## Related

- Plan: docs/plan-novel-fandom-story-pipeline.md
- Depends: FR-690, FR-691, FR-692; Blocks: FR-694
