## 2026-03-07: Inquisitor Audit XV — mixed commit recidivism, standing findings calcified

**Context:** Fifteenth audit covering commits `6c737d9`..`856a13e` (5 commits: `chore(tests)` ×1, `docs(chaplain)` ×2, `docs(diary)` ×1, `chore(enforce)` ×1). Zero `feat:` or `fix:` commits in window. Audit XIII ruled the Inquisitor should recuse until a qualifying commit lands or a standing finding is resolved — neither condition was met. Despite this, the user explicitly invoked the audit; the Inquisitor complies and records.

**Findings:**

1. **✗ VIOLATION — Mixed commit recidivism.** `856a13e` message says "resolve ruff E741 and SIM105 in watch enforce tests" but the diff also adds 62 lines to `docs/diary.md` (Audits XI–XIV) and restructures `examples/copilot/graph.yaml` (provider/model → defaults block). Three unrelated changes in one commit; message describes only one. This is the exact pattern flagged in Audit XIV — unfixed, repeated.

2. **✓ COMPLIANT — Conventional Commits.** All 5 commits use valid prefixes. Co-authored-by trailers present on Copilot-contributed commits (3 of 5). Human-authored commits (`856a13e`, `6c737d9`) lack trailers correctly.

3. **⚠ DRIFT — Three standing findings persist (8th+ consecutive audit).** ARCHITECTURE.md line 1125: "7 providers" (should be 8). FR-112 status: "Draft" (should be "Done"). FR-116 CHANGELOG entry: absent. These have been documented since Audit VIII. The Inquisitor has spent more time documenting them than it would take to fix all three.

4. **✓ COMPLIANT — ADR-001, noqa confessions.** Modified test file has `@pytest.mark.req("REQ-YG-116")` tags. No new `# noqa` suppressions added. All existing suppressions confessed (CONF-002 through CONF-125).

5. **✓ COMPLIANT — Diary entries.** FR-115 judgement reflection committed in `ff1faca`. Sermon's Distill step honored.

**Heuristic:** *A violation flagged twice and repeated a third time is not drift — it is habit.* Mixed commits have now been flagged in Audits XIV and XV with no corrective action. The root cause is not ignorance but workflow: multiple changes accumulate in the working tree and get swept into a single commit. The cure is `git add -p` (stage hunks selectively) or a pre-commit hook that warns when a commit touches both `docs/diary.md` and non-docs files under a non-`docs:` prefix.

**Seed:** Should the Inquisitor stop documenting standing findings after the 3rd consecutive audit and instead emit a single "CALCIFIED-N" reference? Repeating the same three findings for 8 audits is itself entropy — the audit log has become the noise it was designed to detect.
