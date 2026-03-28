## 2026-03-15: Inquisitor Audit — FR-202/FR-109 Post-Merge Compliance

**Context:** Audited the 5 most recent commits on `main`: `d118bc8` (fix: dict prompts), `8540b45` (feat: FR-202 image pipeline, #66), `74c078c` (docs: FR-202 FR), `06b93c4` (feat: FR-109 batch image prompts, #65), `a7ed7aa` (docs: FR-109 FR). Assessed against Conventional Commits, ADR-001, TDD, changelog, diary, and Co-authored-by requirements.

**Findings:**

1. ✗ **VIOLATION — Missing Co-authored-by trailer on 3 commits.** `d118bc8` (fix), `74c078c` (docs), and `a7ed7aa` (docs) lack the required `Co-authored-by: Copilot <...>` trailer. The squash-merged feat PRs (#65, #66) have it, but the standalone commits do not. The git commit trailer rule in `.github/copilot-instructions.md` applies to all Copilot-authored commits.

2. ✓ **COMPLIANT — ADR-001 req tag coverage (corrects audit-132).** Previous audit flagged FR-202 tests as having 82% untagged functions. This was a false positive: all 6 `@pytest.mark.req("REQ-YG-198")` decorators are at class level, and pytest propagates class marks to all methods. All 34 tests are covered. Same pattern in FR-109: 4 class-level marks cover all 21 tests.

3. ⚠ **DRIFT — `on_error: skip` in batch_image_prompts without verification.** `examples/batch_image_prompts/graph.yaml` uses `on_error: skip` on the `enrich` map node. Linter correctly fires W017 (silent fallback) and W022 (no verification question). The graph lints with warnings but no errors. Commandment 6 says "thou shalt not hedge with silent fallbacks" — an example shipping with a known W017 sets a precedent that weakens the rule.

4. ✓ **COMPLIANT — Conventional Commits and changelog.** All 5 commits follow `type(scope): description`. Both `feat` PRs reference FR numbers. Changelog fragments exist for both features and the fix (`FR-202-image-generation-pipeline.md`, `fr-109-batch-image-prompts.md`, `fix-image-pipeline-dict-prompts.md`).

5. ✓ **COMPLIANT — Diary reflections.** Both feature requests have diary entries: `2026-03-14-reflection-fr-109.md` and `2026-03-15-reflection-fr-202.md`. Both contain Context, Trap, Insight, Heuristic, and Seed sections.

**Heuristic:** Class-level `@pytest.mark.req` in pytest propagates to all methods — this is correct and sufficient for ADR-001 compliance. Auditors must verify propagation rules before flagging coverage gaps, or risk the `plausible_wrong_answer` trap in reverse: a plausible violation claim that is actually wrong erodes audit credibility.

**Seed:** Should the enforce pipeline add a post-commit hook that validates Co-authored-by trailers on all Copilot-session commits, not just squash merges? The 3-of-5 miss rate suggests the trailer is only reliably applied by the PR squash path, not by direct commits.
