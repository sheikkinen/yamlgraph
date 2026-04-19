## 2026-04-19: Inquisitor Audit — FR-032 Cache Policy & Recent Commits

**Context:** Audited the 5 most recent commits on `feat/069-map-node-timeout` and `main`, covering FR-032 (node-level cache policy), FR-069 merge integration, and two FR documentation commits (FR-239, FR-240).

**Findings:**

1. ✓ **COMPLIANT** — FR-032 commit (`268d0aeb`) follows Conventional Commits with FR reference, includes changelog fragment, diary entry, demo-output.log, ARCHITECTURE.md requirement (REQ-YG-239), and Co-authored-by trailer. Full ceremony observed.

2. ⚠ **DRIFT** — Changelog fragment `fr-032-node-level-caching.md` references `(REQ-YG-032)` in its text body, but the actual ARCHITECTURE.md requirement for cache policy is `REQ-YG-239`. The `req:` front-matter field also says `REQ-YG-032` (CLI entry point). Tests correctly use `REQ-YG-239`. The changelog fragment is the only place where the wrong REQ is cited.

3. ✓ **COMPLIANT** — Tests in `test_node_cache_policy.py` all carry `@pytest.mark.req("REQ-YG-239")`, correctly linking to the ARCHITECTURE.md requirement. 16 test functions, all tagged.

4. ✓ **COMPLIANT** — docs(FR) commits (`97359252`, `1b96f96a`) correctly use Conventional Commits for documentation-only changes. No changelog or diary required for `docs` type.

5. ✓ **COMPLIANT** — No undocumented `# noqa` suppressions found in files changed by FR-032 (`node_compiler.py`, `graph_schema.py`).

**Heuristic:** When a feature request number (FR-NNN) differs from its requirement ID (REQ-YG-NNN), verify the changelog fragment references the requirement ID, not the FR number. The FR is a planning artifact; the REQ is the traceability anchor.

**Seed:** Should `scripts/req_coverage.py` cross-check changelog fragment `req:` fields against ARCHITECTURE.md to catch REQ ID mismatches before merge?
