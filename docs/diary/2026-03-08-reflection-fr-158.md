## 2026-03-08: FR-158 — CI Diary Gate Reflection

**Context:** Implemented a `diary-gate` GitHub Actions job that blocks feat/fix PRs referencing FR-XXX from merging unless a diary reflection file exists in the diff. This closes the structural gap that five consecutive Inquisitor audits (XL–XLIV) identified but could not remediate — missing diary reflections for merged features.

**Trap:** audit_as_ritual — "3+ audits without fix → ritual, not process." Five audits flagged missing diary reflections. FR-152 retroactively created missing files, but recurrence was immediate. The per-instance fix doesn't scale. The cure was already proven by FR-149 (CHANGELOG gate): enforcement at the merge boundary, not detection after the fact. The pattern was right there — I just needed to apply it a second time.

**Heuristic:** When the same enforcement pattern (CI gate for file existence) solves two problems (CHANGELOG, diary), extract the structural insight: any artifact that must accompany a change type needs a pre-merge gate, not a post-merge audit. Detection without blocking is observation without agency. The gate template — check PR title prefix, extract identifier, verify file glob — is now a reusable pattern for future "must accompany" constraints.

**Seed:** Could we generalize the gate pattern into a single parameterized workflow job that takes (pr_title_prefix, identifier_regex, required_file_glob) and eliminates the need to write a new job for each "must accompany" constraint?
