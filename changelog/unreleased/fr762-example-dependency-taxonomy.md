---
type: feat
scope: governance
req: REQ-YG-571
---
- **FR-762 Example Dependency Taxonomy**: every `examples/` root is now
  mechanically classified as `extra-backed` (every third-party import
  resolves to a distribution declared in `pyproject.toml`; owning
  extra(s) recorded) or `externally-provisioned` (an undeclared import
  is cited by name, never silently added). `scripts/example_taxonomy_scan.py`
  discovers 112 roots (top-level `examples/*`, with `examples/demos/*`
  flattened one level) and writes the generated allowlist
  `examples/dependency-taxonomy.yaml`; `--check` mode fails CI when the
  committed file drifts from a fresh discovery run. `pyproject.toml`
  gained direct declarations for `litellm` (replicate), `pyarrow` (rag),
  `starlette`+`protobuf` (a2a), `torch`+`torchaudio` (chatterbox,
  platform-marked), plus two new extras (`examples-dungeon-master`,
  `openai-proxy`) — closing the frozen negative-space table from
  `docs/plan-research-dependency-negative-space.md`. The `duckduckgo_search`
  fallback was removed (`ddgs` only). FR-761's `direct_import_scan.py`
  gained a `taxonomy_path` parameter (AC-08): `extra-backed` example
  roots are now scanned at core-failure strictness; `externally-provisioned`
  roots (currently only `examples/agent-sdk-planner`, citing
  `claude_agent_sdk` — deliberately excluded from project extras) stay
  excused. CI's test install gained the new lightweight extras
  (`rag`, `replicate`, `openai-proxy`, `examples-dungeon-master`); a new
  import-level smoke test suite verifies each actually imports.
  `torch`/`torchaudio` remain statically verified only (no heavyweight
  CI install without explicit human approval). CAP-213 / REQ-YG-571
  registered; 17 new unit tests (13 taxonomy generator, 4 taxonomy-aware
  scanner) plus 12 import-level smoke tests. (REQ-YG-571)
