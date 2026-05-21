## 2026-05-20: Inquisitor Audit — FR-424/425/426 Compliance Sweep

**Context:** Audited the 5 most recent commits on `main` (fc94c8ca..a00ae619) covering FR-424 (session timeline), FR-425 (hook classification daemon + Phase B emit), and FR-426 (schema_loader tool type). Checked Conventional Commits, changelog fragments, requirement traceability, diary reflections, and noqa confessions.

**Findings:**

- ✓ **COMPLIANT — Conventional Commits**: All 5 commits follow `type(scope): FR-XXX description` format correctly. Types used: `feat`, `docs`.
- ✓ **COMPLIANT — FR-425/426 doctrine coverage**: Both FRs have changelog fragments with `req:` front-matter, `@pytest.mark.req` tagged tests (REQ-YG-411–418), and diary reflections. The C901 noqa on `create_agent_node` in `yamlgraph/tools/agent.py` is confessed in `docs/confessions.md`.
- ✗ **VIOLATION — FR-424 missing diary reflection**: `feat(hooks): FR-424 session timeline join script` has no corresponding diary entry in `docs/diary/`. The Sermon requires Distill after every task. The diary-gate CI check should catch this on `feat` PRs with FR references, yet this commit merged. Either the gate was bypassed or the diary was in a different PR that didn't land.
- ⚠ **DRIFT — FR-424 tests lack `@pytest.mark.req` tags**: `.github/hooks/tests/test_session_timeline.py` contains tests without requirement markers. These live outside `tests/unit/` and run via `python3` directly rather than pytest, placing them in a grey zone. ADR-001 states "every test function" — the boundary between hook infrastructure tests and core tests is uncontracted.
- ⚠ **DRIFT — FR-424 changelog fragment missing `req:` field**: `changelog/unreleased/fr-424-session-timeline-join.md` omits `req:` front-matter. The `changelog-req-gate` validates present references but does not enforce presence itself, so CI passes. This leaves the traceability chain broken for FR-424.

**Heuristic:** Infrastructure tests in `.github/hooks/tests/` exist outside the doctrine's enforcement perimeter — no pytest collection, no req tags, no coverage reporting. When a feature adds tests in an uncontracted location, the gates pass but traceability silently degrades. Either extend ADR-001 to cover hook tests explicitly, or create a separate traceability contract for infrastructure scripts.

**Seed:** Should the project define a formal "enforcement perimeter" map — a document listing which directories are subject to which gates — so that new directories don't silently escape doctrine coverage?
