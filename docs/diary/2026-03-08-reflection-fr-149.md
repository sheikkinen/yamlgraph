## 2026-03-08: FR-149 — CI CHANGELOG Gate Reflection

**Context:** Implemented a GitHub Actions job (`changelog-gate`) that blocks feat/fix PRs from merging without CHANGELOG.md changes, closing a structural enforcement gap.

**Trap:** audit_as_ritual — Two prior mechanisms (FR-077 local hook, FR-125 post-merge script) existed but neither created a pre-merge gate. The audit kept flagging the same gap (Audits XXXIV, XXXV) without a blocking fix. The cure was obvious once framed as a boundary problem: enforcement must happen at the merge boundary (CI), not downstream (local hooks or manual scripts).

**Heuristic:** When an audit repeatedly flags the same category of violation, the fix is a gate at the boundary, not a better post-hoc process. Local hooks are bypassed by server-side operations; manual scripts are forgotten. Only CI-level checks create true pre-merge gates.

**Seed:** Could we auto-generate the `changelog-gate` condition from the Conventional Commits type list, so adding a new type that requires CHANGELOG updates only needs a config change?
