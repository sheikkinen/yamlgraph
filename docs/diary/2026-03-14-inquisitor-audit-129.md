## 2026-03-14: Inquisitor Audit — FR-109 Repeat Violations Unresolved

**Context:** Routine audit of the latest 5 commits spanning `feat/109-batch-image-prompt-generation` (3 commits) and `main` (2 commits, FR-201 horoscope). Triggered to verify whether audit #128's findings were addressed in the FR-109 GREEN commit.

**Findings:**

1. **✗ VIOLATION (ADR-001 — repeat):** `test_batch_image_prompts.py` still has 17/21 test functions without `@pytest.mark.req` tags. Audit #128 flagged this identical gap. The GREEN commit (531f33a) shipped production code, diary, and changelog — but did not remediate the traceability debt. A violation identified and then ignored is worse than one never found.

2. **✗ VIOLATION (ADR-001):** FR-109 has no capability file under `capabilities/` and no entry in `ARCHITECTURE.md`. FR-201 (horoscope demo, identical category — example graph) added `CAP-76` and updated `ARCHITECTURE.md`. The inconsistency signals drift: example graphs have no settled traceability contract.

3. **⚠ DRIFT (ADR-001):** The 4 tagged tests all reference `REQ-YG-003` ("linting"), yet most FR-109 tests validate graph structure, prompt schemas, and map-node configuration. The tag is technically present but semantically imprecise — it satisfies the letter, not the spirit.

4. **✓ COMPLIANT (Commandment 7):** RED (5b77fcd) and GREEN (531f33a) commits are cleanly separated. TDD discipline honored.

5. **✓ COMPLIANT (Commandment 10 / Sermon):** All 5 commits follow Conventional Commits. Changelog fragments and diary entries exist for both FR-109 and FR-201. Co-authored-by trailers present.

**Heuristic:** An audit finding that survives into the next commit is no longer a finding — it is accepted debt. If the GREEN commit does not remediate violations flagged in the RED phase, the audit loop is broken. **Fix audit violations before shipping GREEN, or explicitly defer with a tracked issue.**

**Seed:** Should the pre-commit hook block GREEN commits when a prior audit in the same branch has open `✗ VIOLATION` entries? This would close the gap between "finding" and "fixing" within a single feature branch lifecycle.
