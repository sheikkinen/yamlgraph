## 2026-05-19: Inquisitor Audit — WIP on main, noqa confession gap, calcified direct-push habit

**Context:** Audited the 5 most recent commits on `main` (8a731d71..27795d03, 2026-05-19) against the Scripture. Three prior audits today (235–237) already flagged direct pushes for FR-416 and FR-419. This audit checks whether the pattern has been corrected and examines the newest commit (27795d03).

**Findings:**

1. ✗ **VIOLATION — WIP commit on main (27795d03):** `chore: investigation of chaplain failures, wip` landed directly on `main` with mixed concerns: FR-420 production code + tests, two inquisitor audit diary entries, inbox cleanup, module-map update, and a new feature request. Commandment 8 forbids entropy; the Sermon demands mixed commits erode auditability ("one concern per commit → clear blame, clear revert"). A WIP commit is the antithesis of the Submit rite ("Let CI judge. What survives the fire may merge.").

2. ✗ **VIOLATION — noqa without confession (27795d03):** New `# noqa: S105 — ANSI colour label, not a credential` added in FR-420 test code without a corresponding CONF-XXX entry in `docs/confessions.md`. The noqa Confessions rule requires every suppression to be documented. The inline comment explains intent but does not satisfy the registry contract.

3. ✗ **VIOLATION — Direct push habit uncorrected:** Four of five audited commits lack the `(#NNN)` squash-merge suffix — they bypassed PR review entirely. Audits 235, 236, and 237 all flagged this. The pattern has not been corrected; it has accelerated. No break-glass entries document any of these bypasses.

4. ⚠ **DRIFT — FR-416 still has no diary entry:** Two FR-416 fix commits (8a731d71, 17da4033) modified production FSM code without a reflection. The Sermon's Distill step requires metacognitive reflection after completing a task. FR-416 involved non-trivial debugging (event key mismatch + legacy config forwarding) — exactly the kind of work that produces heuristics worth capturing.

5. ✓ **COMPLIANT — FR-418 remains exemplary (71c89093):** The only commit that went through a PR. Conventional Commits with `(#419)`. Changelog fragment with `req: REQ-YG-408`. Tests tagged `@pytest.mark.req("REQ-YG-408")`. Diary with `Seed:` marker. REQ added to ARCHITECTURE.md. This is the standard the others should match.

**Heuristic:** A WIP commit on `main` is a compound violation — it simultaneously breaks branch protection, mixed-commit auditability, and the Submit rite. When investigation work needs to be saved, commit to a feature branch. The branch exists to absorb mess; `main` exists to reject it.

**Seed:** Three consecutive audits have flagged direct pushes without effect. At what point does repeated audit without remediation become the `audit_as_ritual` trap — and should the Inquisitor have authority to block the next release until prior violations are resolved?
