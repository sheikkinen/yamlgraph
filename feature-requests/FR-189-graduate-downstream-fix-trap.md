# Feature Request: Graduate `downstream_fix` Trap Description

**Priority:** LOW
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-03-12

## Summary

Refine the `downstream_fix` trap description in the Scripture's Knowledge Graph based on evidence from 3 diary entries that confirm the pattern. The current description is misleading — it reads as a cure rather than a trap.

## Value Statement

All agents benefit from a clearer trap description that immediately communicates the cognitive hazard, reducing the chance of applying a downstream fix instead of a boundary-level correction.

## Problem

The `downstream_fix` trap in `.github/copilot-instructions.md` currently reads:

```yaml
downstream_fix: "Fix at callsite, not utility → avoid double-stripping"
```

This description is confusing for two reasons:

1. **It describes the cure, not the trap.** "Fix at callsite, not utility" sounds like advice (what to do), not a hazard (what goes wrong). Contrast with `quick_confidence: "When I feel certain → Judge instead"` which clearly names the trigger.

2. **It references a specific incident ("double-stripping") rather than the general pattern.** The 3 diary entries reveal a broader principle: the instinct to add guards where symptoms manifest rather than normalizing at the boundary where external data enters.

### Evidence — 3 Confirmed Occurrences

| Diary Entry | Domain | Downstream Fix (trap) | Boundary Fix (cure) |
|---|---|---|---|
| `2026-03-08-reflection-fr-150.md` | CI/Git | Adding more PR-level checks | Branch protection at the push boundary |
| `2026-03-09-reflection-fr-172.md` | Graph Config | Hardcoded `END` in router function | Config-level `loop_exits` field through compilation pipeline |
| `2026-03-08-reflection-fr-166.md` | Data Validation | Post-hoc `if min > max` guard in evaluator | Pydantic validation at regex parse boundary |

All three are instances of `the_one_law`: *"Normalize at the boundary where external data enters, not downstream where it manifests."*

## Proposed Solution

Update the `downstream_fix` entry in the `traps:` section of `.github/copilot-instructions.md`:

```yaml
# Before
downstream_fix: "Fix at callsite, not utility → avoid double-stripping"

# After
downstream_fix: "Guard added where symptom manifests → normalize at entry boundary instead"
```

This revised description:
- **Names the trigger**: "Guard added where symptom manifests" — describes what the agent catches itself doing
- **Points to the cure**: "normalize at entry boundary instead" — connects to `the_one_law`
- **Generalizes across domains**: applies to CI gates, config fields, and data validation alike

No other Scripture changes are needed. The complementary cure `callsite_fix: "Fix at the specific caller, not the shared utility"` remains correct and consistent.

## Acceptance Criteria

- [x] `downstream_fix` description in `.github/copilot-instructions.md` updated to: `"Guard added where symptom manifests → normalize at entry boundary instead"`
- [x] No other traps or cures descriptions changed
- [x] Pre-commit hooks pass (copilot-instructions content is validated)
- [x] Changelog fragment added to `changelog/unreleased/`

## Alternatives Considered

1. **Add a new trap instead of refining.** Rejected — the trap already exists; adding a second entry for the same pattern violates single-responsibility in the Knowledge Graph.

2. **Expand the description with examples.** Rejected — trap descriptions are one-liners by convention. The diary entries serve as the detailed evidence trail; the Scripture entry is a compressed signal.

3. **No change (leave as-is).** Rejected — the current description actively misleads by describing the cure rather than the hazard. The graduation threshold (3 occurrences) demands a clear, evidence-backed refinement.

## Related

- **Diary evidence:**
  - `docs/diary/2026-03-08-reflection-fr-150.md`
  - `docs/diary/2026-03-09-reflection-fr-172.md`
  - `docs/diary/2026-03-08-reflection-fr-166.md`
- **Scripture location:** `.github/copilot-instructions.md`, line 54
- **Complementary cure:** `callsite_fix` in `cures:` section
- **Underlying principle:** `the_one_law` in Knowledge Graph

---

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted.

**Reviewed:** 2026-03-12

### Assessment

1. **Scope: Clear and minimal.** Single one-liner change in `.github/copilot-instructions.md` line 54. No scope creep.

2. **No contradictions.** The proposed format (`trigger → redirect`) matches the existing convention (cf. `quick_confidence: "When I feel certain → Judge instead"`). The complementary `callsite_fix` cure remains consistent — the trap names what goes wrong; the cure names what to do.

3. **Acceptance criteria: Measurable.** Exact text specified, pre-commit validation, changelog fragment — all binary pass/fail.

4. **Feasible.** A single string edit. 0.5-day estimate accounts for ceremony (changelog, diary, pre-commit) — reasonable.

5. **Architecture-aligned.** Follows the Knowledge Graph graduation convention (3+ confirmed occurrences → refine Scripture). All 3 cited diary entries verified to exist and correctly reference the `downstream_fix` trap.

6. **Single responsibility.** One trap description, one file, one change.

### Scope Note

The ebook (`docs/ebook/v3/01-doctrine.md:193`) already uses improved language ("Patching the symptom where it manifests rather than the boundary where it enters") — this predates the FR and confirms the direction. Diary entries are historical records and must not be retroactively edited. The FR correctly limits scope to the Scripture source of truth.
