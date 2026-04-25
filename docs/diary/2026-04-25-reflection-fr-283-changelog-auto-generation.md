# 2026-04-25 Reflection: FR-283 Changelog Auto-Generation

**Context:** Implementing automatic changelog fragment generation in watcher2 pipeline to eliminate the #1 cause of manual intervention (100% of recent PRs required manual changelog fixes).

**Trap:** **plausible_wrong_answer** - Initially reached for complex shell command composition without first confirming it would pass YAMLGraph's variable linter. The shell approach seemed obviously correct but triggered E001 validation errors during demo creation, leading to a Python-based demo that actually proved the concept more clearly.

**Heuristic:** When implementing infrastructure automation, prototype the integration point first. YAMLGraph's linting rules exist for good reasons - respect the boundaries between shell environment variables and graph state variables. Test the demonstration early to catch validation constraints before they block delivery.

**Seed:** Could watcher2's defense-in-depth pattern (shell + prompt + finalize + CI) be generalized into a reusable automation framework? What other manual intervention points in the pipeline could benefit from this layered approach?