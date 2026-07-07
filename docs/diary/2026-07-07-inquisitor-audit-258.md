## 2026-07-07: Inquisitor Audit — Chaplain Path-Doubling Fix Merges Without a Condemning Test

**Context:** New commit landed since audit-257 (`1ed5b8b6 fix(chaplain): graph-root-relative tool paths in enforce-session and philosopher graphs`), closing a live production defect: FR-445's path-confinement plus FR-658's `graph_root` plumbing caused `tools.py` paths declared repo-root-relative to be doubled (`.../watcher-enforce/.chaplain/graphs/watcher-enforce/tools.py`), killing every Chaplain enforce session at launch. Audited this commit against the Scripture, in particular Commandment 7 (TDD) and the changelog/diary gates.

---

## Findings

1. **✓ COMPLIANT — Conventional Commits + changelog fragment.** Title `fix(chaplain): graph-root-relative tool paths in enforce-session and philosopher graphs` is well-formed; `changelog/unreleased/fix-chaplain-graph-tool-paths.md` correctly documents the FR-445/FR-658 interaction and the doubled-path symptom.

2. **✗ VIOLATION — No condemning test for a bug that "killed every enforce session at launch" (Commandment 7).** The diff touches three graph configs and adds a new `write_diary` proxy function in `.chaplain/graphs/philosopher/tools.py` (loading `.chaplain/lib/diary.py` via `importlib.util.spec_from_file_location` at an absolute path). Neither the path-doubling regression nor the new proxy function is covered by `tests/unit/test_philosopher.py` or any other test — grep across `tests/` found zero references to `write_diary` or the graph-root-relative path fix. This is a fix without a witness test: a hypothesis, not a proof, per the Agents' prayer ("No bug shall be fixed unless first condemned by a failing test").

3. **⚠ DRIFT — No diary reflection accompanies the fix itself.** The commit doesn't carry an `FR-XXX` reference in its title, so the CI `diary-gate` doesn't require one, but the Sermon's Distill step still calls for a reflection after any corrective task, especially one closing a "kills every session" defect. None was added in this commit.

4. **⚠ DRIFT (recurring, not new) — Direct-to-main push, no PR.** `gh pr list` shows the last merged PR is #457 (2026-07-04); commits since then, including this fix, landed without a PR. This is the same branch-protection bypass pattern flagged in audit-256/257 and remains unremediated — no `reference/break-glass.md` entry cites this batch.

5. **✓ COMPLIANT — No noqa suppressions introduced;** `docs/confessions.md` obligations unaffected by this change.

---

## Heuristic

**A fix commit that repairs a "kills every session" defect is exactly the case the Scripture means by "condemn before you cure."** The severity of the regression (total enforce-pipeline failure) makes the missing test more consequential, not less — yet urgency is precisely when the TDD discipline is most likely to be skipped. Any fix touching path-resolution logic across multiple YAML configs should ship with at least one test asserting the resolved absolute path, so a future FR-445/FR-658-style interaction is caught before it reaches "kills every session."

---

**Seed:** Could a lightweight pre-commit check flag `fix(...)` commits that modify `path:` fields in `.chaplain/graphs/**/*.yaml` (or any `type: python` tool declaration) without a corresponding new/changed test asserting the resolved path — turning "test-optional emergency fix" into "test required before merge, even for infra self-repairs"?
