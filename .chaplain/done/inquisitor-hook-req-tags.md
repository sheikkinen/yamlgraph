# Fix: Hook tests missing @pytest.mark.req traceability

## Violation
Inquisitor audits 244 and 245 (consecutive, 2026-05-20 and 2026-05-21) both flag that test files
in `.github/hooks/tests/` lack `@pytest.mark.req` tags. ADR-001 states "every test function must
have `@pytest.mark.req`" but the scope boundary between core capability tests and infrastructure
hook tests is undefined. Six test files exist with zero req markers:

- `test_fr_checks.py`
- `test_markdown_checks.py`
- `test_pre_command_guard.py`
- `test_python_checks.py`
- `test_session_timeline.py`
- `test_yaml_checks.py`

Both audits recommend defining explicit traceability tiers or extending ADR-001 to cover
infrastructure tests.

## Suggested Fix
**Structural gap → FR required.**

1. Amend `ARCHITECTURE.md` to define ADR-001 scope tiers:
   - **Tier 1 (core):** `tests/unit/`, `tests/integration/` — full `@pytest.mark.req("REQ-YG-XXX")` required.
   - **Tier 2 (infrastructure):** `.github/hooks/tests/` — `@pytest.mark.req("REQ-INF-XXX")` with a separate `REQ-INF-*` registry, or explicit exemption with documented rationale.
   - **Tier 3 (demo/proof):** `examples/`, `feature-requests/*/` — no req tags required.

2. If Tier 2 gets req tags: add `REQ-INF-001` through `REQ-INF-N` entries to `ARCHITECTURE.md` covering hook capabilities (FR validation, YAML checks, markdown checks, Python checks, pre-command guard, session timeline).

3. If Tier 2 is exempted: document the exemption in ADR-001 with rationale ("hook tests validate shell scripts, not Python capabilities; they run outside pytest collection").

4. Update `scripts/req_coverage.py` to either scan `.github/hooks/tests/` or explicitly exclude it.
