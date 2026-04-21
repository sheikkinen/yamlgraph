## 2026-04-21: Inquisitor Audit — Mixed Commits and Changelog Fragment Format

**Context:** Audited the 5 most recent commits (20e9eb9c..a7a609c8) covering a watcher timeout config change, two FR planning docs, accumulated diary reflections, and an a2a test-skip fix. Checked against Conventional Commits, CHANGELOG fragments (FR-179), ADR-001 req traceability, diary (Sermon: Distill), and noqa Confessions.

**Findings:**

1. ✗ **VIOLATION — Mixed commit concerns** (`a7a609c8` `chore: watcher timeout`): Bundles a timeout config change (`.chaplain/graphs/copilot/graph.yaml`), 4 inquisitor audit diary entries, a chaplain diary entry, a git report, and FR-259 planning doc — 9 files across 4 unrelated concerns in one commit. The Knowledge Graph explicitly states `mixed_commits_erode_auditability: "One concern per commit → clear blame, clear revert"`. A revert of the timeout change would also revert diary entries; a revert of FR-259 would lose the audits.

2. ⚠ **DRIFT — Changelog fragment missing YAML front matter** (`fix-a2a-sdk-optional-skip.md` and `fix-a2a-sdk-optional-tests.md`): FR-179 convention requires `---\ntype: fix\nscope: a2a\n---` front matter for `scripts/aggregate_changelog.py` to classify entries correctly. Both fix fragments use raw markdown headers instead. Compare with `FR-257-chaplain-research-step.md` which has proper front matter. The `changelog-req-gate` CI check may not validate these fragments correctly.

3. ✓ **COMPLIANT — Conventional Commits**: All 5 commits follow the format (`chore:`, `docs(FR):`, `docs(diary):`, `fix(a2a):`). Types and scopes are appropriate.

4. ✓ **COMPLIANT — noqa Confessions**: `noqa_coverage.py` reports 0 undocumented suppressions across 86 total `noqa` markers. All 100 confessions current.

5. ✓ **COMPLIANT — ADR-001 and diary quality**: `fix(a2a)` tests retain `@pytest.mark.req` tags (REQ-YG-250 through REQ-YG-252). Diary entries in `7dc44faa` are rich — philosopher reflections name traps (`quick_confidence`), plant seeds, and cite commit SHAs as evidence. FR-253 reflection identifies a novel heuristic (`framework_ceremony_ratio`).

**Heuristic:** *Batch commits that mix operational changes with documentation create false coupling.* The watcher timeout is a 2-line config tweak; bundling it with diary entries and an FR doc means neither can be reverted independently. The `chore:` type masks the scope mismatch — `chore` implies one concern, not four. Separate by concern: config changes in one commit, diary landings in another, FR docs in a third.

**Seed:** Could a pre-commit hook detect mixed-concern commits by checking whether modified files span more than N unrelated directory trees (e.g., `.chaplain/graphs/` + `docs/diary/` + `feature-requests/`) and warn before commit?
