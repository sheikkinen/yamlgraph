---
type: feat
scope: governance
req: REQ-YG-570
---
- **FR-761 Reproducible Dependency Governance**: added
  `constraints/dev-py312.txt` (pip-freeze snapshot of the CI dev
  environment, byte-for-byte reproduction verified), declared
  `pip-audit>=2.7.0` as an explicit `dev` extra dependency (CI now
  installs it via `.[dev]` instead of an ad hoc pip install), and added
  `scripts/direct_import_scan.py` — an AST-based scanner that walks
  `yamlgraph/` (core, strict) plus `examples/`, `scripts/`, `tests/`
  (report-only), resolving every third-party import to a distribution
  name (PEP 503-normalized) and verifying it is declared under the
  correct owner: module-level (unconditional) imports in `yamlgraph/`
  require core `[project.dependencies]` unless the file matches a
  known optional feature surface (`PATH_PREFIX_OWNERS` — e.g.
  `storage/simple_redis.py` → `redis-simple`, `contrib/a2a_client.py`
  and `a2a/` → `a2a`, `export/mcp.py` → `mcp`, `utils/fsm/` → `fsm`),
  in which case that surface's owning extra also
  counts; nested/lazy imports (multi-provider-factory pattern) may be
  satisfied by any declared group. Top-level `try/except` imports
  execute at import time and are treated as module-level surface
  (PR #463 review P1). Dotted namespace imports resolve to their actual
  distribution before ownership checks (`langgraph.checkpoint.redis` →
  `langgraph-checkpoint-redis`, `google.protobuf` → `protobuf`;
  PR #463 review round-2 P1), and first-party modules exposed via
  explicit `sys.path.insert` local roots in tests/examples are excluded
  from report-only findings (round-2 P2). Report-only findings under
  `examples/`, `scripts/`, `tests/` exclude first-party local sibling
  modules/packages. A `PENDING_GAPS` table, keyed by
  (path-prefix, import-name) so dispositions are surface-scoped and
  never global by distribution name (PR #463 review P2), tracks imports already
  dispositioned to sibling FRs (FR-760's `langchain-core`, FR-762's
  `litellm`/`starlette`/`protobuf`) so the gate blocks only genuinely
  new undeclared core imports. Wired into `.pre-commit-config.yaml` as
  a blocking `--strict` hook. 17 unit tests exercise isolated fixture
  trees (undeclared/declared imports, nested/lazy imports, stdlib and
  first-party exclusion, alias resolution, underscore/hyphen
  normalization, owner-specific vs unrelated-extra ownership, local
  sibling module/package exclusion, report-only roots, pending gaps).
  CAP-212 / REQ-YG-570 registered. (REQ-YG-570)
- **Round 2 fix**: `constraints/dev-py312.txt` regenerated to cover the
  actual CI-tested extras (`.[dev,digest,websearch,a2a,fsm,verify]`),
  not just `.[dev,fsm,verify]` — the artifact previously omitted
  `feedparser`, `resend`, `beautifulsoup4`, `slowapi`, `ddgs`,
  `a2a-sdk`, and `grpcio`. Reproduction re-verified byte-for-byte
  against the corrected command.
