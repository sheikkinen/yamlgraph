## 2026-03-07: Chaplain — FR-127 Conventional Commits Enforcement Amended

FR-127 proposed GitHub Actions validation for Conventional Commits on PR titles to close the gap where server-side merges bypass local hooks. The plan was sound—scoped, clear acceptance criteria—but the judge identified three critical gaps: AC #6's conditional `FR-XXX` enforcement can't be handled by the action alone and requires custom scripting; revert handling was flagged in the problem but left unaddressed in the solution; and merge strategy assumptions weren't documented. The verdict was AMEND, moving FR-127 back to inbox. These gaps reveal a common pattern: solutions that appear complete often miss edge cases and conditional logic that require explicit design decisions rather than tool assumptions.

**Seed:** How can we build a checklist or pattern library that surfaces conditional enforcement logic and edge-case handling *during* the planning phase, rather than discovering them in review?
