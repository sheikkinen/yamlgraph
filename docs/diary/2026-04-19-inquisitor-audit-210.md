## 2026-04-19: Inquisitor Audit — FR-250/FR-251/FR-252 Doctrine Compliance

**Context:** Audited the 5 most recent commits on `feat/fr-251-harden-remote-inbox` (d5ee4c2f..e6535653) covering FR-250 (A2A protocol gaps), FR-251 (remote inbox hardening), and FR-252 (planning doc). Checked Conventional Commits, changelog fragments, ADR-001 traceability, TDD separation, diary entries, and noqa confessions.

**Findings:**

1. ✓ COMPLIANT — **Conventional Commits**: All 5 commits follow the format. `feat` commits cite FR-XXX. RED/GREEN separation honored for FR-251 (`test(chaplain)` → `feat(chaplain)`).

2. ✓ COMPLIANT — **ADR-001 Requirement Traceability**: FR-251 added CAP-109/REQ-YG-256 to ARCHITECTURE.md; all 8 tests in `test_harden_remote_inbox.py` carry `@pytest.mark.req("REQ-YG-256")`. FR-250 tests (12 total across `test_a2a_server.py` and `test_a2a_message.py`) carry req markers for existing REQ-YG-210/211/213.

3. ⚠ DRIFT — **FR-250 changelog fragment missing `req:` front matter**: The fragment `FR-250-a2a-server-complete-gaps.md` mentions REQ-YG-210, 211, 213 in the body but omits the `req:` YAML key. The `changelog-req-gate` silently skips fragments without `req:`, so CI won't catch this. By design, multi-REQ fragments are deferred to the LLM graph — but the fragment needs a `req:` field to even enter that path. Traceability chain is broken at the changelog level.

4. ✓ COMPLIANT — **Diary entries**: Both FR-250 and FR-251 have reflection entries with Cognitive Trap, Heuristic, and Seed sections. FR-247 also has a reflection present.

5. ✓ COMPLIANT — **No new noqa suppressions**: No `# noqa` additions in the audited diff.

**Heuristic:** **Multi-REQ fragments need at least one `req:` anchor**: When a changelog fragment implements multiple registered requirements, omitting the `req:` field entirely causes the `changelog-req-gate` to skip validation. The fragment should cite the primary REQ (or a comma-separated list) so the gate can route it to mechanical or LLM validation. Silent skip ≠ compliant — it means unchecked.

**Seed:** Could `check_changelog_req.py` be extended to warn (or fail in strict mode) when a `feat` changelog fragment has no `req:` field at all? Currently, missing `req:` is treated as "not applicable" — but for `type: feat` fragments, a requirement reference should arguably be mandatory. This would close the gap where multi-REQ features escape validation by omission.
