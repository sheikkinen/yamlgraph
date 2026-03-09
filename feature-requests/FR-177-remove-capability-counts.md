# FR-177: Remove Hardcoded Capability/Requirement Counts from ARCHITECTURE.md

**Priority:** LOW
**Type:** Chore
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-09

## Summary

Remove the hardcoded capability and requirement count summary sentence from
ARCHITECTURE.md (line 273), retire CAP-52 and REQ-YG-150 which guard it, and
delete the now-unnecessary test file.

## Value Statement

All contributors benefit from fewer merge conflicts on feat PRs, since the
count summary line must be incremented by every PR that adds a capability,
forcing serial rebases on an otherwise conflict-free file.

## Problem

Line 273 of ARCHITECTURE.md contains:

```
YAMLGraph implements **61 capabilities** covering **125 requirements**. Each capability maps to specific modules.
```

This sentence causes two problems:

1. **Merge conflicts** — Every feat PR that adds a capability row must also
   increment this line's counts. When multiple feat PRs are in flight, the
   line becomes a serialization bottleneck requiring rebases. Recent git
   history shows ARCHITECTURE.md is modified by nearly every feat commit
   (10 of the last 10 commits touch it), making this a frequent friction
   point.

2. **Redundant information** — The capability table immediately below is the
   authoritative source of truth. The sentence is a manually-maintained cache
   of data that can be computed from the table. Anyone needing a count can
   count table rows or run `python scripts/req_coverage.py --detail`.

**Note:** The counts are currently accurate (61 capabilities, 125
requirements) — the guard test from FR-154 works correctly. The motivation
is merge-conflict reduction and redundancy elimination, not drift.

## Proposed Solution

Remove the count summary sentence and replace it with a counts-free
introduction. Retire all artifacts that exist solely to maintain or guard
the counts.

### Before (ARCHITECTURE.md line 273)

```markdown
YAMLGraph implements **61 capabilities** covering **125 requirements**. Each capability maps to specific modules.
```

### After

```markdown
Each capability below maps to specific modules and requirements.
```

### Cascade Changes

| Artifact | Action | Reason |
|----------|--------|--------|
| `ARCHITECTURE.md` L273 | Rewrite sentence without counts | Primary change |
| `ARCHITECTURE.md` L329 (CAP-52 row) | Delete row | Capability exists solely to guard the removed sentence |
| `ARCHITECTURE.md` L791 (REQ-YG-150 row) | Delete row | Requirement exists solely to guard the removed sentence |
| `tests/unit/test_architecture_capability_count.py` | Delete file | Test guards the removed sentence |
| `scripts/req_coverage.py` L50 (`[150]`) | Remove from `ALL_REQS` | REQ-YG-150 no longer exists |
| `scripts/req_coverage.py` L244 (`CAP-52`) | Remove from `CAPABILITIES` dict | CAP-52 no longer exists |
| `feature-requests/FR-154-architecture-capability-count-guard.md` | Update status to "Superseded by FR-177" | FR-154 introduced the guard; FR-177 removes it |

### Post-change invariants

- Capability table row count decreases by 1 (CAP-52 removed)
- Requirement count decreases by 1 (REQ-YG-150 removed)
- The summary sentence no longer contains any numbers, so no future PR
  needs to update it
- `python scripts/req_coverage.py` passes with updated counts
- `pytest tests/unit/ -q --no-cov` passes

## Acceptance Criteria

- [ ] ARCHITECTURE.md summary sentence (L273) no longer contains hardcoded counts
- [ ] CAP-52 row removed from capability table in ARCHITECTURE.md
- [ ] REQ-YG-150 row removed from requirements table in ARCHITECTURE.md
- [ ] `tests/unit/test_architecture_capability_count.py` deleted
- [ ] `REQ-YG-150` removed from `scripts/req_coverage.py` `ALL_REQS`
- [ ] `CAP-52` removed from `scripts/req_coverage.py` `CAPABILITIES` dict
- [ ] `python scripts/req_coverage.py` runs without error
- [ ] `pytest tests/unit/ -q --no-cov` passes
- [ ] FR-154 status updated to "Superseded by FR-177"

## Alternatives Considered

1. **Automate the count via pre-commit hook** — A hook could rewrite the
   sentence on every commit. Rejected: adds tooling complexity to maintain
   a line that provides no value beyond the table itself.

2. **Keep the sentence, remove the guard test** — Lets the counts drift
   silently, which is worse than the current state (accurate counts with
   merge friction). Rejected.

3. **Keep everything as-is** — The guard test works and counts are accurate.
   Accept the merge-conflict cost. Viable, but the cost compounds with
   every concurrent feat PR.

## Related

- `feature-requests/FR-154-architecture-capability-count-guard.md` — Introduced the guard; superseded by this FR
- `tests/unit/test_architecture_capability_count.py` — To be deleted
- `tests/unit/test_architecture_provider_count.py` — Unaffected (guards provider count in module table, separate concern)
- `scripts/req_coverage.py` — REQ-YG-150 and CAP-52 removal only


## Judgement

**Verdict: APPROVE**
**Judge date:** 2026-03-09

### Evaluation

1. **Scope: Clear and minimal.** Single concern - remove one redundant sentence and its guard artifacts. The cascade table enumerates every affected file with specific line numbers and actions. No feature creep.

2. **Contradictions/Ambiguities: None found.** The FR correctly notes the counts are accurate today and the motivation is merge-conflict reduction, not drift correction. No mixed signals.

3. **Acceptance criteria: Measurable.** Every criterion is a binary check (file deleted, line changed, script passes). Two automated gates (req_coverage.py, pytest) provide machine-verifiable confirmation.

4. **Implementation approach: Feasible.** Pure deletion and one-line rewrite. No new abstractions, no new dependencies, no behavioral changes to runtime code. 0.5-day effort estimate is realistic.

5. **Architecture alignment: Strong.** Follows Commandment 8 (entropy elimination) - removing a manually-maintained cache of computable data. The capability table remains the single source of truth.

6. **Single responsibility: Yes.** Every cascade change serves one goal: eliminate the count sentence and its guard chain. FR-154 status update is a bookkeeping consequence, not orthogonal scope.

### Minor note (non-blocking)

The FR references scripts/req_coverage.py L244 for CAP-52; actual line is L245. Trivial - the implementer should grep rather than rely on line numbers.

### Authority granted

Scope frozen. Implement per cascade table. No additions beyond listed artifacts.
