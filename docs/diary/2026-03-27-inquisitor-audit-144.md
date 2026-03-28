---

## 2026-03-27: Inquisitor Audit — The Inquisitor Inquisited

**Context:** Audited the 5 most recent commits (e4a7d27..16e4973): two `docs(FR)` (FR-203, FR-204), three `chore(examples)` (image pipeline timestamps, parallelization, EXIF enrichment). Critically, this audit also re-examined the evidence behind the escalating req-tag violation flagged in audits #139–143, using the project's authoritative tooling rather than grep approximations.

**Findings:**

1. ✗ VIOLATION (META — SELF-CORRECTION) — **Audits #139–143 escalated a false violation for five consecutive cycles.** The claim: "28/34 tests in `test_image_pipeline.py` lack `@pytest.mark.req` tags." The truth: all 34 test functions reside inside 6 classes, each decorated with `@pytest.mark.req("REQ-YG-198")`. Pytest inherits class-level markers to all methods. `req_coverage.py --detail` confirms: `REQ-YG-198 (34 tests)` — full coverage, zero gap. Prior audits used `grep -c '@pytest.mark.req'` (6) vs `grep -c 'def test_'` (34) and concluded 28 were untagged — a surface pattern that ignores pytest's marker inheritance. This is the `plausible_wrong_answer` trap applied to the audit process itself. Five cycles of escalation, calls for CI gates, enforcement ultimatums, and auto-FR proposals — all to remediate a non-existent defect. The `infrastructure_self_exempt` trap also applies: the Inquisitor did not apply to its own findings the verification rigour it demands of code.

2. ✓ COMPLIANT — All 5 commits follow Conventional Commits (`docs(FR):`, `chore(examples):`). No `feat`/`fix`; changelog/diary gates correctly not triggered.

3. ✓ COMPLIANT — `noqa_coverage.py`: 55/55 documented. `req_coverage.py`: 132/132 covered. No regressions.

4. ⚠ DRIFT — Five `chore(examples)` commits across multiple audit windows form a design arc with no diary reflection. CI-exempt (`chore` type), but Sermon Distill applies to meaningful engineering decisions regardless of commit type.

5. ✓ COMPLIANT — FR-203/FR-204 well-structured. Commandment 1 honoured.

**Heuristic:** Before escalating any finding, verify it with the authoritative tool — not a grep approximation. `req_coverage.py --detail` is the single source of truth for ADR-001 compliance; it resolves class-level markers, parametrize decorators, and all pytest inheritance mechanisms. A grep count is a hint, not evidence. **Procedure change: the Inquisitor must run `req_coverage.py --detail` as Step 1 of any req-tag audit check, and cross-reference its output before classifying findings.** An Inquisitor that does not verify its own evidence becomes the ritual it warns against — and five false escalations prove the cost of that failure is not zero.

**Seed:** What other Inquisitor checks use grep approximations where authoritative scripts exist? A meta-audit of audit procedures — comparing each check against available tooling — could prevent future false cascades. The pattern generalises: any automated judgement that bypasses the purpose-built verification tool is a `plausible_wrong_answer` waiting to compound.
