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
  name (PEP 503-normalized) and verifying it is declared somewhere in
  `pyproject.toml`. A `PENDING_GAPS` table tracks imports already
  dispositioned to sibling FRs (FR-760's `langchain-core`, FR-762's
  `litellm`/`starlette`/`protobuf`) so the gate blocks only genuinely
  new undeclared core imports. Wired into `.pre-commit-config.yaml` as
  a blocking `--strict` hook. 11 unit tests exercise isolated fixture
  trees (undeclared/declared imports, nested/lazy imports, stdlib and
  first-party exclusion, alias resolution, underscore/hyphen
  normalization, optional-extra ownership, report-only roots, pending
  gaps). CAP-212 / REQ-YG-570 registered. (REQ-YG-570)
