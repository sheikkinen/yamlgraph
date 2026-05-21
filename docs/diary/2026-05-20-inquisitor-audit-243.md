## 2026-05-20: Inquisitor Audit — Watcher Direct-Push Bypass

**Context:** Audited the 5 most recent commits on `main` (f35a3254..a287352f, 2026-05-19 to 2026-05-20) against Scripture, Conventional Commits, diary-gate, changelog-gate, and ADR-001 requirement traceability.

**Findings:**

1. **✗ VIOLATION — `infrastructure_self_exempt`: watcher2 bypasses branch protection.** Four of five audited commits were pushed directly to `main` without a PR (19d8fbf2 FR-422, a06984e0 chore, a287352f FR-423, f35a3254 chore:wip). Only fbeb44c0 (FR-421, PR #423) went through the merge gate. Direct pushes skip diary-gate, changelog-req-gate, copilot-trailer-gate, and conflict-check. The automation that enforces doctrine exempts itself from doctrine — the exact trap the Scripture names.

2. **⚠ DRIFT — WIP commit on `main`.** `f35a3254` ("chore: investigation of chaplain failures, wip") is a work-in-progress commit on the protected branch. WIP belongs on feature branches; `main` should contain only completed, reviewed work.

3. **⚠ DRIFT — FR-423 missing diary reflection.** The `fix(watcher): FR-423` commit introduces a meaningful fix (plan-judge convergence stabilization) but contains no `docs/diary/` entry. The diary-gate would have blocked this through a PR — the direct push circumvented it.

4. **✓ COMPLIANT — Conventional Commits format.** All five commits follow the `type(scope): description` pattern. feat/fix commits reference FR-XXX IDs.

5. **✓ COMPLIANT — noqa confessions.** `noqa_coverage.py` reports 94 suppressions, 0 undocumented. No new noqa added in the audited range.

**Heuristic:** When an automated system pushes directly to a protected branch, every gate it bypasses is a gate that doesn't exist. Branch protection rules are only as strong as the weakest actor with push access. The watcher2 system must route through PRs or have an equivalent local gate that mirrors CI checks before pushing.

**Seed:** Should the watcher2 system be required to open PRs for its own fixes — applying the same merge ceremony it enforces on human contributors — or does the latency cost of PR review justify a "trusted actor" carve-out? If the latter, what compensating controls (post-push audit, auto-revert on gate failure) would preserve the spirit of branch protection?
