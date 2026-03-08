## 2026-03-08: FR-144 — Pre-commit Cleanup Reflection

**Context:** Ran full pre-commit suite on the FR-144 branch. Only two hooks failed: `ruff` (SIM108 ternary) and `ruff-format` (auto-reformat). Both were in the same file — a test helper that used an if/else block where a ternary sufficed.

**Trap:** *quick_confidence* — The if/else felt more readable with comments explaining quoting nuances. But ruff's SIM108 rule exists precisely because simple conditional assignments are clearer as ternaries. The comments were defending complexity that didn't need to exist.

**Heuristic:** When a linter flags a pattern and you want to suppress it, ask: "Am I defending the code or defending my comfort?" If the ternary is genuinely less clear, add a `# noqa` with a confession. If it's just habit, accept the transform.

**Seed:** Could pre-commit hooks auto-apply safe fixes (like SIM108 ternaries) without human intervention, turning the hook from a gate into a formatter? What's the boundary between "safe auto-fix" and "needs human judgment"?
