## 2026-03-14: Inquisitor Audit — Chaplain Direct-Push & Capability Drift

**Context:** Routine audit of the 5 most recent commits on `main`, covering FR-201 (horoscope demo), FR-196 (portable chaplain), and supporting docs/chore commits. Checked Conventional Commits, changelog fragments, requirement traceability (ADR-001), test `@pytest.mark.req` tags, diary entries, noqa confessions, and branch protection compliance.

**Findings:**

1. ✗ VIOLATION — **Chaplain bypasses PR gate.** Commits `d6850b7`, `50c13fb`, `a7ed7aa` (author "Test") are pushed directly to `main` without a PR (no `(#XX)` squash-merge suffix). Branch protection requires pull requests; the Scripture states `automation_inherits_doctrine: "Scripts follow same rules as humans → no --no-verify bypass."` No break-glass documentation found for these bypasses.

2. ⚠ DRIFT — **CAP-76 description stale after d6850b7.** The capability file says "Pure YAML, zero Python" but `d6850b7` added `tools.py` to the horoscope demo. The claim no longer matches reality.

3. ⚠ DRIFT — **d6850b7 missing Co-authored-by trailer.** The two PR-merged feat commits (`9ff1d16`, `15e24a1`) include the Copilot trailer; the three direct-push commits do not.

4. ✓ COMPLIANT — **FR-201 main commit (9ff1d16)** is exemplary: Conventional Commits, changelog fragment, CAP-76 capability file, REQ-YG-197 in ARCHITECTURE.md, all tests tagged `@pytest.mark.req("REQ-YG-197")`, dedicated diary reflection, Co-authored-by trailer.

5. ✓ COMPLIANT — **FR-196 (15e24a1)** passes full checklist: changelog, capability, requirement, diary, trailer.

**Heuristic:**
> **Automation must walk through the same gates it guards.** When the Chaplain enforce pipeline pushes directly to `main`, it undermines the branch protection rules it helped establish. The fix is not to weaken enforcement but to make the automation open PRs — the same path humans take.

**Seed:** Should the Chaplain enforce pipeline be refactored to create PRs instead of direct-pushing, and should a CI job detect direct pushes to `main` by non-human authors?
