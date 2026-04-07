## 2026-04-07: Inquisitor Audit — Recent 5 Commits (f35af64..980d76a)

**Context:** Routine audit of the 5 most recent commits on `main`, covering FR-208 A2A server delivery, fsm-router fix, two FR planning docs, and a chore commit bundling batch scripts and diary entries.

**Findings:**

1. ✓ **COMPLIANT** — `feat(a2a): FR-208` exemplary doctrine adherence. Conventional Commit with FR ref, CAP-81 capability file with REQ-YG-206–213, all tests carry `@pytest.mark.req` tags, changelog fragment present, diary reflections written (`2026-03-29-reflection-fr-208-a2a-server.md`, `fr-209-a2a-streaming.md`), Co-authored-by trailer included. This is the gold standard.

2. ⚠ **DRIFT** — `chore: image pipeline batch scripts` (f35af64) bundles 12 diary entries spanning 9 days, a ChatGPT roadmap doc, and 2 batch scripts in a single commit. Violates "One concern per commit → clear blame, clear revert" (process: `mixed_commits_erode_auditability`). Should be at minimum two commits: diary catchup + batch scripts.

3. ⚠ **DRIFT** — `fix(fsm-router): map new_query payload` (f3a6709) has a changelog fragment (✓) but no condemning test. Commandment 7: "No bug shall be fixed unless first condemned by a failing test." The change is YAML-config-only in `examples/`, reducing severity, but the doctrine carves no exceptions.

4. ✓ **COMPLIANT** — Both `docs(FR):` commits (3f334ad, d398e81) follow Conventional Commits, are documentation-only, and correctly require no tests/changelog/diary.

5. ✓ **COMPLIANT** — No new `# noqa` suppressions found in the audited range.

**Heuristic:** Batch commits that accumulate during automated or scripted workflows (diary catchup, batch scripts) still deserve separation. The `chore` type does not exempt a commit from the single-concern rule — `git rebase -i` before push costs seconds, but a tangled revert costs hours.

**Seed:** Could the Chaplain daemon auto-commit diary entries individually as they're generated, rather than accumulating them for a manual bulk commit?
