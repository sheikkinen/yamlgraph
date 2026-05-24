## 2026-05-23: Inquisitor Audit — FR-446 Skills & Housekeeping Commits

**Context:** Audit of 5 most recent commits on `main` (e764eeba..0977bfed) covering FR-446 skill promotion, LangSmith playbook addition, and documentation housekeeping.

**Findings:**

1. ✓ COMPLIANT — `feat(skills): FR-446 promote reference docs to Copilot skills` (ed84bc56): Conventional Commit format correct, changelog fragment present (`changelog/unreleased/FR-446-copilot-skill-promotion.md`), traces to REQ-YG-162, diary reflection written (2026-05-22-reflection-fr-446-skills-knowledge-compression.md). No new framework tests required — skills are static SKILL.md files, not code under `yamlgraph/`.

2. ✓ COMPLIANT — `docs(diary): FR-446 skills as curated knowledge compression` (79909b07): Diary entry committed separately from implementation. Good commit hygiene — separates reflection from code change.

3. ⚠ DRIFT — `chore: docs` commits (e764eeba, 46cd2cea): Both use the bare message `chore: docs` which technically satisfies Conventional Commits but is informationally empty. The first adds git-reports and world-digests; the second adds a LangSmith skill and a 259-line `scripts/langsmith_traces.py`. A utility script added under a `chore: docs` subject obscures the true scope.

4. ⚠ DRIFT — `scripts/langsmith_traces.py` (added in 46cd2cea): A 259-line operational script with no corresponding tests. As a `scripts/` utility (not under `yamlgraph/`) it's exempt from REQ-YG markers, but Commandment 7 (TDD) still applies to non-trivial logic. The script has argument parsing, API calls, and formatting — enough to warrant at least a smoke test.

5. ✓ COMPLIANT — No new `noqa` suppressions found in any of the 5 commits' changed files.

**Heuristic:** `chore: docs` is the commit equivalent of naming a variable `data` — technically valid but informationally bankrupt. When a commit bundles documentation *and* new scripts, the scope has outgrown `docs`. Split or use a more descriptive subject (`chore(scripts): add langsmith trace query tool`).

**Seed:** Should pre-commit enforce a minimum subject length or reject bare `chore: docs` when the diff touches non-documentation files (e.g., `scripts/*.py`)? A heuristic gate: if `--stat` includes `.py` files outside `docs/`, require a scope beyond `docs`.
