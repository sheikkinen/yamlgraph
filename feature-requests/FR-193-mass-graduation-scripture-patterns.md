# Feature Request: Mass Graduation of Scripture Patterns

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-03-12

## Summary

Graduate 8 recurring patterns from diary analysis into the Scripture's Knowledge Graph: 5 process heuristics into the existing `process:` section, and 3 forward-looking seeds into a new `seeds:` section.

## Value Statement

All agents benefit from codified patterns that compress recurring diary insights into single-line signals, reducing re-discovery cost and making the Knowledge Graph a living index of organizational learning.

## Problem

The Philosopher's analysis of 220+ diary entries identified 9 patterns that meet the graduation threshold (3+ confirmed occurrences). One (`audit_as_ritual`) is already in Scripture. The remaining 8 are scattered across diary prose without formal Knowledge Graph representation.

Without graduation:
- Agents re-derive the same insights from scratch each session
- Seeds planted in diary entries are never harvested (the `audit_as_ritual` trap applied to seeds themselves)
- Process heuristics remain implicit rather than enforceable

### Evidence — Pattern Occurrence Counts

| Pattern | Occurrences | Category |
|---------|-------------|----------|
| `req_coverage_as_universal_gate` | 11 | seed |
| `detection_without_enforcement` | 8 | process |
| `changelog_ci_gate` | 7 | process |
| `inquisitor_auto_escalation` | 7 | seed |
| `verification_checkpoint_primitive` | 5 | seed |
| `automation_inherits_doctrine` | 4 | process |
| `enforcement_at_merge_boundary` | 4 | process |
| `mixed_commits_erode_auditability` | 4 | process |

Source: Philosopher diary analysis (`docs/diary/2026-03-12-philosopher.md`), cross-referencing 25+ inquisitor audit entries, 5+ reflection entries, and 5+ digest entries.

**Note on `changelog_ci_gate`:** This pattern is already implemented via FR-149 (`changelog-gate` CI job in `.github/workflows/commitlint.yml`). It is therefore a confirmed workflow pattern, not a forward-looking seed, and belongs in `process:` alongside other proven heuristics. This corrects the earlier draft which incorrectly placed it in `seeds:`.

## Proposed Solution

Two changes to the Knowledge Graph YAML block in `.github/copilot-instructions.md`:

### 1. Add 5 heuristics to existing `process:` section

```yaml
process:
  # ... existing entries ...
  automation_inherits_doctrine: "Scripts follow same rules as humans → no --no-verify bypass"
  changelog_ci_gate: "Require changelog fragments at CI, not documentation → FR-149 proved advisory docs insufficient"
  detection_without_enforcement: "Lint without gate = advisory → add CI block or remove claim"
  enforcement_at_merge_boundary: "PR merge is last gate → all enforcement must block there"
  mixed_commits_erode_auditability: "One concern per commit → clear blame, clear revert"
```

These are workflow patterns consistent with the existing `process:` entries (cf. `audit_gate`, `boring_enforcement`). `changelog_ci_gate` joins as a confirmed pattern since FR-149 already implements the CI enforcement it describes.

### 2. Add new `seeds:` section after `process:`

```yaml
seeds:
  # Forward-looking patterns awaiting implementation
  inquisitor_auto_escalation: "Auto-create FR when audit pattern hits threshold"
  req_coverage_as_universal_gate: "Block PR merge on coverage gaps, not just report"
  verification_checkpoint_primitive: "Checkpoint/resume for long enforce pipelines"
```

Seeds are distinct from heuristics: they are forward-looking questions that have recurred enough to be worth tracking but whose implementation has not yet been attempted. Seeds graduate to `process:` (or a new FR) when acted upon.

### Section placement

The `seeds:` section is placed after `process:` and before the closing ``` of the YAML block, preserving the progression: `the_one_law` → `boundaries` → `traps` → `cures` → `process` → `seeds`.

## Acceptance Criteria

- [x] 5 heuristic patterns added to `process:` section in `.github/copilot-instructions.md` with exact text from Proposed Solution
- [x] New `seeds:` section added after `process:` section with 3 seed patterns
- [x] Section comment `# Forward-looking patterns awaiting implementation` present on `seeds:`
- [x] All 8 pattern descriptions are one-liners following existing `key: "trigger → redirect"` convention
- [x] `changelog_ci_gate` placed in `process:` (not `seeds:`) with description referencing FR-149
- [x] No existing Knowledge Graph entries modified (this FR is additive only)
- [ ] Pre-commit hooks pass
- [x] Changelog fragment added to `changelog/unreleased/`
- [x] Diary reflection documents the graduation ceremony

## Alternatives Considered

1. **Individual FRs per pattern.** Rejected — the overhead of 8 separate FR/Judge/Enforce cycles for one-liner additions is disproportionate to the change. FR-189 through FR-191 demonstrated that individual graduation FRs work for entries requiring description refinement; for pure additions, batching is appropriate.

2. **Add seeds to `process:` without a separate section.** Rejected — seeds are aspirational (no implementation yet), while `process:` entries are confirmed workflow patterns. Conflating them would violate the Knowledge Graph's "confirmed recurrence → graduate" progression.

3. **Add seeds to diary only (no Knowledge Graph entry).** Rejected — this is exactly the `audit_as_ritual` trap: recording without formalizing. 11 occurrences of `req_coverage_as_universal_gate` across diary files proves that informal tracking does not lead to action.

4. **Wait for each seed to be implemented before graduating.** Rejected — seeds track recurring *questions*, not answers. Their value is in being visible to all agents as a shared index of open problems.

5. **Keep `changelog_ci_gate` in `seeds:`.** Rejected — it describes a capability already implemented by FR-149. Including it as "awaiting implementation" would be factually incorrect and misleading to agents. Moving it to `process:` correctly reflects its status as a confirmed workflow pattern.

## Related

- **Philosopher analysis:** `docs/diary/2026-03-12-philosopher.md`
- **Knowledge Graph location:** `.github/copilot-instructions.md`, lines 36–84
- **Recent graduation FRs:** FR-189, FR-190, FR-191 (individual trap refinements)
- **Graduation convention:** `process.graduation` in Knowledge Graph
- **`changelog_ci_gate` implementation:** FR-149, `.github/workflows/commitlint.yml` (`changelog-gate` job)
- **Relevant seeds (if implemented):**
  - `enforcement_at_merge_boundary` → relates to FR-150 (branch protection)
  - `req_coverage_as_universal_gate` → relates to ADR-001 (requirement traceability)

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted to implement.

**Reviewed:** 2026-03-12

**Assessment:**

1. **Scope** — Clear and minimal. Eight one-liner additions to a YAML block, plus one new section header. Exact text specified. Additive only.

2. **Contradictions** — None found. The `changelog_ci_gate` reclassification from seeds to process is well-justified (FR-149 confirms implementation). Section placement follows logical progression.

3. **Acceptance criteria** — All 9 criteria are binary and verifiable. No ambiguity.

4. **Feasibility** — Trivial. Text additions to a markdown file.

5. **Architectural alignment** — The `seeds:` section is a natural extension of the graduation pipeline (`traps → cures → process → seeds`). It completes the lifecycle: seeds track recurring questions before they become confirmed patterns.

6. **Single responsibility** — The FR batches two related concerns (process additions + new seeds section). The batching justification is sound: individual FR cycles for one-liner additions would be disproportionate overhead. Both share the same evidence base and review cycle.

**Observation (non-blocking):** Occurrence counts in the evidence table are from the Philosopher's semantic analysis and may not match exact-string grep counts. The patterns demonstrably recur across diary entries regardless of exact tally.
