---
type: feat
scope: governance
req: REQ-YG-571
---
- **FR-762 Example Dependency Taxonomy**: every `examples/` root is now
  mechanically classified as `extra-backed` (every third-party import
  resolves to a distribution declared in `pyproject.toml`; owning
  extra(s) recorded, preferring a single full-coverage extra over a
  partial-owner combination) or `externally-provisioned` (an undeclared
  import is cited by name, never silently added).
  `scripts/example_taxonomy_scan.py` recursively discovers every
  independently-runnable root under `examples/` (135 roots — any directory
  at any nesting depth whose `README.md` documents a fenced usage command,
  not just top-level directories; graph YAML detection parses structurally,
  requiring a top-level `nodes` mapping, so prompt files containing the
  substring `nodes:` never create roots — PR #464 review P1), and writes the generated allowlist
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
  registered; 19 taxonomy generator tests plus 12 import-level smoke tests,
  covering the recursive nested-root discovery, README usage-command
  detection, full-coverage extra preference, and ancestor-aware local-module
  resolution added per PR #464 review. Round 2 fix: `_root_imports()` now
  also follows YAML tool-module (`module: yamlgraph...`) references and
  README-documented `yamlgraph <subcommand>` CLI invocations out to the
  yamlgraph/ files implementing them, so `a2a_call`/`a2a_server` correctly
  resolve to `extra: [a2a]`/`extra: [a2a, booking]` instead of `null`; 7 new
  regression tests added. CAP-213/REQ-YG-571 spec text realigned to the
  implemented discovery rule (recursive any-depth walk, structural
  top-level `nodes` mapping, README fenced usage command — PR #464
  review round 2); classifier stdlib/local checks now key on the
  top-level segment of dotted import names after merging FR-761's
  namespace-preserving extraction (npc gains `redis` extra). (REQ-YG-571)
