# FR-180: Plan-Phase ID Reservation

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 1.5 days
**Requested:** 2026-03-10
**Judged:** 2026-03-10
**Approved:** 2026-03-10

## Judge's Amendments (2026-03-10)

1. **FIXED — Conflict resolution false guarantee:** Original Section 5 claimed `max()` guarantees no overlap. This is incorrect when two branches reserve from the same base — both get the same IDs. Amended to describe honest mechanics: max-wins for counters + validation detects duplicates + later-merged branch re-reserves.
2. **FIXED — Plan phase estimation underspecified:** Added clarification that the Planner agent infers counts from FR text, and that under-reservation is trivially recoverable via additional `reserve_ids()` calls.

## Summary

Move CAP-XX and REQ-YG-XXX ID assignment from the Enforcement phase to the Plan phase. A YAML registry file (`.chaplain/id-registry.yaml`) tracks the next available IDs and logs reservations per FR. The Planner reads the registry, reserves the IDs it needs, writes them into the FR markdown, and commits the updated registry. The Enforcer then consumes pre-assigned IDs instead of inventing them.

## Value Statement

All contributors benefit from deterministic, conflict-free ID assignment, since concurrent PRs no longer race to pick the same next ID.

## Prerequisites

- **FR-178** (Append-Only Capability Registry) should be implemented first or concurrently. FR-178 moves capability metadata into per-file YAML, making the "scan directory for max ID" approach viable. However, FR-180 is designed to work with **either** the current monolithic layout or the post-FR-178 registry — the id-registry.yaml is the single source of truth for next IDs regardless of storage format.

## Problem

CAP-XX and REQ-YG-XXX IDs are currently assigned during the Enforcement phase. This causes three concrete problems:

1. **ID collisions.** Two concurrent PRs independently read the same max ID from `ARCHITECTURE.md` or `req_coverage.py` and both assign the next number. One PR must be rebased and renumbered after the other merges.

2. **req_coverage.py merge conflicts.** The `_ALL_FRAMEWORK_REQS` list and `CAPABILITIES` dict are append-only in intent but edit-conflicting in practice. Every feat PR that adds a requirement touches the same trailing lines.

3. **No pre-implementation traceability.** An FR's acceptance criteria cannot reference specific REQ-YG-XXX IDs until enforcement, so the Plan and Judge phases operate with placeholders ("adds REQ-YG-TBD"). This makes Judgement less precise — the reviewer cannot verify that the requirement count matches the scope.

## Proposed Solution

### 1. ID Registry File

```yaml
# .chaplain/id-registry.yaml
next_cap: 65
next_req: 161
reserved:
  - fr: FR-180
    cap: []
    req: []
    note: "ID reservation mechanism itself — no new capabilities"
```

**Schema rules:**
- `next_cap` and `next_req` are monotonically increasing integers.
- `reserved` is an append-only list. Entries are never removed or edited.
- Each reservation records the FR that owns the IDs and the specific IDs reserved.

### 2. Implementation Module

The reservation logic lives in `yamlgraph/utils/id_registry.py` — a Python module callable from both Plan and Enforce graph contexts.

**Public API:**

```python
# yamlgraph/utils/id_registry.py

def load_registry(path: Path = REGISTRY_PATH) -> IdRegistry:
    """Load and validate the id-registry.yaml file."""

def reserve_ids(
    registry: IdRegistry,
    fr_id: str,
    cap_count: int = 0,
    req_count: int = 0,
    note: str = "",
) -> Reservation:
    """Reserve a contiguous range of CAP/REQ IDs for an FR.
    Increments next_cap/next_req and appends to reserved list.
    Returns the Reservation with concrete IDs."""

def save_registry(registry: IdRegistry, path: Path = REGISTRY_PATH) -> None:
    """Write the updated registry back to YAML."""

def validate_registry(registry: IdRegistry) -> list[str]:
    """Validate registry integrity. Returns list of error messages (empty = valid)."""
```

**Pydantic models:**

```python
class Reservation(BaseModel):
    fr: str                    # e.g. "FR-181"
    cap: list[int] = []        # e.g. [65]
    req: list[int] = []        # e.g. [161, 162, 163]
    note: str = ""

class IdRegistry(BaseModel):
    next_cap: int
    next_req: int
    reserved: list[Reservation] = []
```

### 3. Plan Phase: Reserve IDs

When the Planner creates or updates an FR:

1. Load `.chaplain/id-registry.yaml` via `load_registry()`.
2. Estimate the number of new capabilities and requirements from the FR scope. The Planner agent infers counts from the FR text (e.g., one new node type = one CAP + N REQs). If the estimate is wrong, under-reservation is recoverable — call `reserve_ids()` again for additional IDs during Enforcement (append-only design permits this trivially). Over-reservation wastes sequential numbers but has no functional cost.
3. Call `reserve_ids()` to claim a contiguous range:
   ```yaml
   - fr: FR-181
     cap: [65]
     req: [161, 162, 163]
     note: "Widget streaming node type"
   ```
4. `reserve_ids()` increments `next_cap` and `next_req` by the reserved count.
5. Write the reserved IDs into the FR's acceptance criteria (e.g., "Implements CAP-65 with REQ-YG-161, REQ-YG-162, REQ-YG-163").
6. Call `save_registry()` and commit the updated `id-registry.yaml` alongside the FR.

### 4. Enforcement Phase: Consume IDs

The Enforcer reads the FR markdown to find pre-assigned IDs. For legacy FRs created before FR-180 that lack reservations, the Enforcer calls `reserve_ids()` from the registry before proceeding — same reservation logic as the Planner.

### 5. Conflict Resolution

If `id-registry.yaml` has a merge conflict (concurrent plans on different branches):

- **Counters:** Take the maximum of both values. Max-wins ensures the counter is correct going forward, but does **not** retroactively prevent duplicate reservations made from the same base. If branch A and B both read `next_cap=65` and each reserve CAP-65, the counter merges to `max(66, 66) = 66` yet both branches hold the same ID.
- **Reserved list:** Concatenate both lists (append-only, no edits). Duplicate FR entries indicate a re-plan; keep the latest.
- **Duplicate detection:** After merge, `validate_id_registry.py` detects overlapping IDs across reservations (rule 3). The later-merged branch must re-reserve its IDs from the updated counter (`reserve_ids()` again) and update its FR references. This is still a major improvement over the status quo — the conflict is localized to one file, detected immediately at validation, and resolution requires only the later-merged branch to renumber.
- **Git merge driver (optional, future):** A custom merge driver (`git config merge.id-registry.driver`) could automate max-wins resolution and flag duplicate IDs. Not required for v1 — manual resolution is trivial.

### 6. Validation

`scripts/validate_id_registry.py` validates:

1. `next_cap` ≥ max(all reserved cap IDs) + 1.
2. `next_req` ≥ max(all reserved req IDs) + 1.
3. No two reservations claim the same ID.
4. Every CAP/REQ reserved **after FR-180** has a corresponding reservation entry. Pre-existing IDs (CAP-01 through CAP-64, REQ-YG-001 through REQ-YG-160) are exempt — they predate the registry and backfilling them provides no correctness guarantee.

```bash
python scripts/validate_id_registry.py
```

A pre-commit hook runs this script on changes to `.chaplain/id-registry.yaml`.

## Acceptance Criteria

- [ ] `.chaplain/id-registry.yaml` exists with `next_cap`, `next_req`, and `reserved` fields, seeded at `next_cap: 65`, `next_req: 161`
- [ ] `yamlgraph/utils/id_registry.py` implements `load_registry`, `reserve_ids`, `save_registry`, `validate_registry` with Pydantic models
- [ ] `scripts/validate_id_registry.py` validates registry integrity (monotonic counters, no duplicate IDs, post-FR-180 reservations only)
- [ ] Plan phase reads registry and reserves IDs before writing FR
- [ ] Reserved IDs appear in FR acceptance criteria with concrete CAP-XX / REQ-YG-XXX values
- [ ] Enforcement phase reads pre-assigned IDs from the FR; for legacy FRs without reservations, the Enforcer reserves IDs from the registry before proceeding (same logic as Planner)
- [ ] Conflict resolution documented: max-wins for counters, concatenate for reservations
- [ ] Pre-commit hook runs `validate_id_registry.py` on changes to `.chaplain/id-registry.yaml`
- [ ] Tests: unit tests for `id_registry.py` (reserve, validate, conflict scenarios)
- [ ] Documentation: updated `CLAUDE.md` with ID reservation workflow reference

## Alternatives Considered

### A. Scan-based ID discovery (no registry)

Derive next ID by scanning `capabilities/` files or `ARCHITECTURE.md` at enforcement time. This is what FR-178 implicitly proposes (`ls capabilities/CAP-*.yaml | sort -t- -k2 -n | tail -1`).

**Rejected because:** Two concurrent branches scanning the same directory state will compute the same next ID. The race condition is the core problem this FR solves.

### B. GitHub Issue-based ID tracking

Use GitHub issue numbers or labels as the ID source of truth.

**Rejected because:** Adds external dependency, breaks offline workflows, and conflates issue tracking with capability registration.

### C. UUID-based IDs instead of sequential

Replace CAP-XX / REQ-YG-XXX with UUIDs to eliminate collisions entirely.

**Rejected because:** Sequential IDs provide chronological ordering and human readability. The existing codebase has 160+ sequential REQ-YG-XXX references. Migration cost is prohibitive and the readability loss is permanent.

## Cascade Changes

| Artifact | Change |
|----------|--------|
| `.chaplain/id-registry.yaml` | **New file** — seed with `next_cap: 65`, `next_req: 161`, empty `reserved` list |
| `yamlgraph/utils/id_registry.py` | **New file** — `load_registry`, `reserve_ids`, `save_registry`, `validate_registry` + Pydantic models |
| `scripts/validate_id_registry.py` | **New file** — CLI validation wrapper calling `id_registry.validate_registry()` |
| `.pre-commit-config.yaml` | Add hook for id-registry validation on `.chaplain/id-registry.yaml` changes |
| `CLAUDE.md` | Document ID reservation workflow |
| `.chaplain/watch.sh` | Update Plan phase to call `id_registry.reserve_ids()` via shell tool or graph node |
| `feature-requests/TEMPLATE.md` | Add "Reserved IDs" section |
| `tests/unit/test_id_registry.py` | **New file** — unit tests for reservation, validation, conflict logic |

## Related

- **FR-178** (Append-Only Capability Registry) — changes where IDs are stored; FR-180 changes when they are assigned. Complementary.
- **FR-177** (Remove Capability Counts) — removes the count sentence that drifts; FR-180 ensures ID assignment is deterministic.
- **FR-179** (Append-Only Changelog) — another append-only pattern; same design philosophy of eliminating edit conflicts.
- `scripts/req_coverage.py` — current ID validation; will be updated by FR-178 but still relevant until then.
- `ARCHITECTURE.md` — current source of truth for CAP/REQ definitions.
