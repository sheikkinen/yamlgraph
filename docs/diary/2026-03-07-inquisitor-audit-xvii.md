## 2026-03-07: Inquisitor Audit XVII — rebase split acknowledged, CALCIFIED-3 persists

**Context:** Seventeenth audit covering commits `ff1faca`..`65f9e95` (5 commits: `docs(chaplain)` ×2, `chore(tests)` ×1, `chore(graph)` ×1, `docs(diary)` ×1). Zero `feat:` or `fix:` in window. Two new commits since Audit XV: `65f9e95` (FR-118/FR-119 feature requests) and the rebase-split pair `bfa1dd1`/`b58eaa7` (replacing mixed commit `856a13e` flagged in Audits XIV–XV). Audit XVI (concurrent) noted the ghost SHA; this audit cross-validates and adds findings XVI did not cover.

**Findings:**

1. **✓ COMPLIANT — Mixed commit partially remediated.** `856a13e` was rebased into `bfa1dd1` (test fixes only, 1 file) and `b58eaa7` (graph.yaml + diary, 2 files). The feedback loop produced a correction. However, `b58eaa7` still bundles 62 lines of diary entries with a `chore(graph)` config change — the split was incomplete.

2. **✓ COMPLIANT — Conventional Commits, Co-authored-by.** All 5 commits use valid prefixes. Copilot-contributed commits (`9e49673`, `ff1faca`) carry the trailer. Human-authored commits correctly omit it.

3. **✗ CALCIFIED-3 — Three standing findings persist (9th consecutive audit).** (a) ARCHITECTURE.md line 1125: "7 providers" → "8". (b) FR-112 status: "Draft" → "Done". (c) FR-116 CHANGELOG entry: absent despite `4765fdc feat: FR-116`. Each is a <1 minute fix. The Inquisitor will not re-describe these after this audit.

4. **✓ COMPLIANT — noqa confessions, ADR-001.** Two `# noqa` suppressions (ANN001, ARG002); both confessed. No new suppressions, capabilities, or tests.

5. **⚠ DRIFT — Concurrent audit collision.** Audit XVI was written by a parallel process while this audit was gathering evidence, creating a numbering collision. This highlights that the diary lacks a locking mechanism — simultaneous Inquisitor invocations can produce duplicate or conflicting entries.

**Heuristic:** *A rebase split in response to audit feedback proves the loop works — but incomplete splits reveal the habit persists at the diary boundary.* Diary entries should always be their own `docs(diary):` commit, staged separately from code changes.

**Seed:** CALCIFIED-3 has survived 9 audits. The next invocation should be `Fix CALCIFIED-3`, not `Inquisit`. An audit that documents the same three trivial fixes for the 9th time has become the entropy it was designed to detect.
