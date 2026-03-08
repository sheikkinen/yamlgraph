# Feature Request: FR-150 and FR-154 Missing Diary Reflections

**ID:** FR-161
**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 0.25 days
**Requested:** 2026-03-08

## Summary

Create missing diary reflection files for FR-150 (branch protection on `main`) and FR-154 (architecture capability count guard). Both features were merged without the Sermon's Distill obligation — FR-150 has been cited as ✗ VIOLATION across **5 consecutive audits** (XL → XLI → XLII → XLIII → XLIV), FR-154 across **3 consecutive audits** (XLII → XLIII → XLIV).

## Value Statement

The project closes two long-standing audit violations and restores doctrine compliance, preventing the `audit_as_ritual` trap from normalizing unenforced gaps.

## Problem

The Sermon of the Chaplain requires a metacognitive diary entry after completing every task list (the **Distill** step). Two merged features lack reflections:

| Feature | Title | Merged | Reflection | Audit History |
|---------|-------|--------|------------|---------------|
| FR-150 | Branch Protection for Main | ✓ | ✗ Missing | XL → XLI → XLII → XLIII → XLIV (5 consecutive ✗) |
| FR-154 | Architecture Capability Count Guard | ✓ | ✗ Missing | XLII → XLIII → XLIV (3 consecutive ✗) |

FR-152 remediated the identical class of violation for FR-137 and FR-145. The pattern has recurred — this is the same `audit_as_ritual` anti-pattern where detection without remediation becomes ritual.

**Root cause:** Despite FR-144's pre-commit gate preventing new unfilled stubs, these two reflections were never created at all. The gate catches bad content but cannot enforce creation of missing files.

## Proposed Solution

Create two diary reflection files following the established naming convention and content structure (see `docs/diary/2026-03-08-reflection-fr-149.md` as exemplar).

### File 1: `docs/diary/2026-03-08-reflection-fr-150.md`

**Content guidance:**
- **Feature context:** Added GitHub branch protection rules to `main` — requiring PRs, squash-merge only, and passing status checks (`commitlint`, `test`). Documented emergency bypass procedure in `reference/break-glass.md`.
- **Cognitive trap:** `downstream_fix` — Prior enforcement (FR-127 commitlint, FR-149 changelog gate) operated inside the PR path but did nothing to prevent direct pushes. The fix was moving the enforcement boundary upstream to the repository settings level, where GitHub's branch protection API creates a true pre-merge gate that cannot be bypassed by local workflow.
- **Heuristic:** When enforcement gates are bypassed by an alternative path (direct push vs PR), the fix is to gate the path itself (branch protection), not add more checks inside the existing path.
- **Seed:** Could branch protection rules be declaratively managed in a YAML config file (like `.github/branch-protection.yaml`) and enforced by CI, closing the gap between documented rules and actual GitHub API settings?

### File 2: `docs/diary/2026-03-08-reflection-fr-154.md`

**Content guidance:**
- **Feature context:** Added a guard test in `test_architecture_capability_count.py` to prevent capability/requirement count drift in ARCHITECTURE.md. The prose claimed "19 capabilities covering 68 requirements" while the actual table had 46 capabilities and 109 requirements.
- **Cognitive trap:** `audit_as_ritual` — The count was accurate when first written (CAP-19) but 27 capabilities were added without updating the prose. Manual discipline failed silently; the fix was structural enforcement via a guard test that reads the document and asserts counts match.
- **Heuristic:** When a document makes quantitative claims about the codebase, guard those claims with a test. Manual discipline decays; structural enforcement closes drift permanently. This mirrors the pattern FR-121 established for provider counts.
- **Seed:** Should the guard test auto-update the prose counts on failure (fix-on-detect) rather than merely failing, or does the manual correction step serve as a valuable review checkpoint?

## Acceptance Criteria

- [ ] `docs/diary/2026-03-08-reflection-fr-150.md` exists with genuine metacognitive content (not placeholder stubs)
- [ ] `docs/diary/2026-03-08-reflection-fr-154.md` exists with genuine metacognitive content (not placeholder stubs)
- [ ] Each reflection identifies at least one cognitive trap from the Knowledge Graph (`downstream_fix`, `audit_as_ritual`, or equivalent)
- [ ] Each reflection contains a forward-looking **Seed** question
- [ ] Both files follow the naming convention `YYYY-MM-DD-reflection-fr-NNN.md`
- [ ] Both files pass the `diary-reflection-check` pre-commit hook (no unfilled placeholders)
- [ ] Next inquisitor audit clears both violations (no ✗ VIOLATION for FR-150/FR-154 reflections)

## Alternatives Considered

1. **Wait for a creation-enforcement gate** — Rejected. FR-144's pre-commit hook validates content quality but cannot enforce file creation. A future FR could add a CI check that cross-references merged `feat` commits against existing reflections, but the 5-audit backlog demands immediate remediation.
2. **Combine into a single reflection file** — Rejected. Each FR addresses a distinct domain (repository settings vs document accuracy). Separate files maintain the 1:1 FR-to-reflection mapping established by convention.
3. **Auto-generate reflections from audit findings** — Rejected. The Sermon requires genuine metacognition. The content guidance above informs human authoring; the reflection must name a real trap and extract a real heuristic.

## Related

- **Audits XL–XLIV:** Escalation path for FR-150 violation; Audits XLII–XLIV for FR-154
- **FR-150:** `feature-requests/FR-150-branch-protection-main.md` — Branch protection (merged, missing reflection)
- **FR-154:** `feature-requests/FR-154-architecture-capability-count-guard.md` — Capability count guard (merged, missing reflection)
- **FR-152:** `feature-requests/FR-152-missing-diary-reflections.md` — Precedent: identical class of violation remediated for FR-137/FR-145
- **FR-144:** `feature-requests/FR-144-enforce-diary-reflection-content.md` — Pre-commit hook preventing unfilled stubs
- **FR-149 reflection:** `docs/diary/2026-03-08-reflection-fr-149.md` — Exemplar for content structure
- **Knowledge Graph traps:** `downstream_fix`, `audit_as_ritual`
