# Feature Request: Example Dependency Taxonomy and Direct-Import Honesty

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged
**Effort:** 2 days
**Requested:** 2026-07-26
**First consumer / first event:** A user running `pip install "yamlgraph[rag]"` and then `examples/rag/index_docs.py`, at the moment `pyarrow` (or `tiktoken`, `torch`, `unified_planning`, `claude_agent_sdk`) raises ImportError because the example outgrew its extra.

## Summary

Examples have grown into real applications (RAG indexing, Dungeon Master, Chatterbox audio, OpenAI proxy, A2A, agent-SDK planner) whose dependencies are only partially encoded in extras. Define a taxonomy — each example is either *runnable from a declared extra* or *explicitly marked externally provisioned* — and fix each direct-import discrepancy accordingly.

## Value Statement

Users and agents can tell from `pyproject.toml` alone whether an example is supported and what installs it, so example failures stop masquerading as framework failures.

## Problem

From `docs/plan-research-dependency-negative-space.md` (direct-import table, finding 4, recommendations 4–5):

| Import | Where | Status |
|---|---|---|
| `litellm` | `yamlgraph/utils/llm_providers.py` (Replicate) | transitive via `langchain-litellm` |
| `pyarrow` | `examples/rag/index_docs.py` | transitive via `lancedb` |
| `tiktoken` | `examples/dungeon_master/api/prompt_salience.py` | undeclared |
| `unified_planning` | Dungeon Master plot modules + tests | undeclared |
| `torch`, `torchaudio` | Chatterbox demo tools | undeclared |
| `claude_agent_sdk` | `examples/agent-sdk-planner/plan.py` | undeclared |
| `starlette` | A2A / OpenAI proxy servers | transitive via `fastapi` / `a2a-sdk` |
| `google.protobuf` | A2A code + tests | transitive via `a2a-sdk` |
| `duckduckgo_search` | legacy fallback beside `ddgs` | remove fallback, don't declare |

There is no rule stating whether examples must run from declared extras, and no test that installs an extra and imports its example entry points.

## Ideal Result

Every example directory has a declared dependency story: either an installable extra whose import surface is verified by a dependency test, or an "externally provisioned" marker in its README. The direct-import scan (FR-761) runs strict — zero undeclared direct imports anywhere in the repo.

## Proposed Solution

1. **Write the rule** (in `reference/example-dependencies.md`): an example is either extra-backed or externally-provisioned; no third state.
2. **Frozen classification table (R-1, no remaining judgement branches):**

   | Surface | Classification | Required dependency action |
   |---|---|---|
   | `yamlgraph/utils/llm_providers.py` Replicate provider | extra-backed | Add `litellm` explicitly to `replicate`; keep `langchain-litellm` |
   | `examples/rag/` | extra-backed by `rag` | Add `pyarrow` to `rag` |
   | `examples/dungeon_master/` | extra-backed by new `examples-dungeon-master` | Add `tiktoken`, `unified-planning`, and the server packages required to import/run the documented app entry points |
   | `examples/demos/chatterbox/` | extra-backed by existing `chatterbox` | Add direct `torch` and `torchaudio` declarations consistent with the README's platform constraints (platform markers where required) |
   | `examples/agent-sdk-planner/` | externally provisioned | Taxonomy marker only; do **not** add `claude-agent-sdk` to project extras |
   | `examples/openai_proxy/` | extra-backed by a named example extra | Extra owns FastAPI/Uvicorn/proxy imports and declares `starlette` explicitly (direct import) |
   | `yamlgraph/a2a/` + A2A CLI surfaces | extra-backed by `a2a` | Add `starlette` and `protobuf` explicitly to `a2a` (direct imports) |
   | `duckduckgo_search` fallback paths | removed | Delete fallback imports in `examples/shared/websearch.py` and `examples/demos/fi_domain_crawl/nodes/seed_discovery.py`; do not declare the package |

3. **Machine-readable taxonomy (R-2):** commit `examples/dependency-taxonomy.yaml` with one row per example root: `path`, `status` (`extra-backed`\|`externally-provisioned`), `extra` (when extra-backed), `external_reason` (when external), `entrypoints` (for import tests). "Example root" is defined mechanically: any directory under `examples/` containing a graph YAML, a Python app/CLI entry point, or a README usage command. A test fails when such a root is omitted.
4. **Scanner reuse (R-3):** depend on FR-761's scanner — do not implement a second scan. FR-762 may change scanner data/configuration, feed the taxonomy as the sole externally-provisioned allowlist, and flip example rows from report-only to strict after the dependency fixes land. No separate scanner, lockfile, `pip-audit`, or governance framework here.
5. **Verification split (R-4):** the direct-import scanner is strict for every classified supported surface. Resolver/import jobs run only for cheap supported extras: keep import checks for `rag` and `replicate`; add cheap checks for `a2a`, the openai-proxy extra, and `examples-dungeon-master` if dependency weight is acceptable. `chatterbox` is verified statically (declaration/platform-marker check) — no heavyweight torch CI install without explicit human approval.

## Acceptance Criteria (revised per judgement)

- [x] AC-01: The FR documents the binary rule: every example root is either `extra-backed` or `externally-provisioned`; no third state exists
- [x] AC-02: `examples/dependency-taxonomy.yaml` lists every mechanically discovered example root and validates `status`, `extra`, `external_reason`, and `entrypoints` according to the rule
- [x] AC-03: The R-1 classification table is folded into the FR with no remaining "or judgement decision" branches
- [x] AC-04: `pyproject.toml` declares the direct packages required by the extra-backed surfaces: `litellm`, `pyarrow`, `tiktoken`, `unified-planning`, `torch`, `torchaudio`, `starlette`, and `protobuf`, with platform markers where required
- [x] AC-05: `examples/agent-sdk-planner/` is marked externally provisioned in the taxonomy and remains out of project extras
- [x] AC-06: `duckduckgo_search` fallback code is removed; `rg "duckduckgo_search" examples yamlgraph tests` finds no live import
- [x] AC-07: `docs/dependency-rationale.yaml` has one entry per newly declared package and `python scripts/dependency_rationale.py --strict` passes
- [x] AC-08: FR-761's direct-import scan, if present, is strict for core and extra-backed example surfaces and uses the taxonomy as the only externally-provisioned allowlist
- [x] AC-09: Import-level dependency checks cover at least `rag` and `replicate`, plus every cheap newly supported extra; Chatterbox is verified statically unless a human approves heavyweight CI installation
- [x] AC-10: Every new or changed test has `@pytest.mark.req(...)` with a valid (existing or new) requirement ID
- [x] AC-11: A changelog fragment exists in `changelog/unreleased/`

## Alternatives Considered

- **Declare everything in extras regardless of size:** rejected for `torch`/`claude_agent_sdk`-class deps — multi-GB or experimental installs should not look first-party supported by default.
- **Move heavyweight examples out of the repo:** larger governance question; taxonomy first, relocation later if warranted.
- **Do nothing until users report ImportErrors:** rejected — that is the current failure mode the research documented.

## Related

- `docs/plan-research-dependency-negative-space.md` — direct-import table, finding 4, recommendations 4–5
- FR-761 direct-import scan (this FR provides the fixes that let it go strict)
- Sibling FRs from the same research: FR-759, FR-760, FR-761

## Judgement (2026-07-26)

**Verdict:** APPROVED WITH REVISIONS — revisions R-1..R-5 folded above; authority active.

Full judgement: [FR-762-example-dependency-taxonomy.judgement.md](FR-762-example-dependency-taxonomy.judgement.md)

**Conditions (GATE):** C-1 if FR-761's scanner is absent in the enforcement branch, stop after dependency/taxonomy/doc fixes and leave strict-scan activation explicitly pending — no parallel scanner; C-2 never add `claude-agent-sdk` to a project extra; C-3 no CI job installing Torch/Chatterbox heavyweight deps without explicit human approval; C-4 no dependencies outside the frozen table without returning to judgement; C-5 no changes to judge/review doctrine, hooks, or branch protection.

**Scope frozen:** D-1 `reference/example-dependencies.md` rule doc; D-2 `examples/dependency-taxonomy.yaml`; D-3 `pyproject.toml` updates for the frozen table only; D-4 rationale entries; D-5 duckduckgo_search fallback removal; D-6 taxonomy/scanner/import tests; D-7 FR-761 scanner config flip (only if the scanner exists); D-8 changelog fragment.

## Implementation Status (enforced 2026-07-26)

All 11 acceptance criteria satisfied. Condition C-1 does not apply: this
branch was based on `feat/fr-761-dependency-governance`, so FR-761's scanner
was present at enforcement time, and full strict-scan activation (D-7,
AC-08) was completed rather than deferred.

**Key deviation — mechanical taxonomy generation, not hand authoring.**
The FR's literal "example root" definition, applied without further scoping,
yields 112 roots (every top-level `examples/*` directory, with
`examples/demos/*` flattened one level). Hand-classifying 112 rows was
infeasible within reasonable effort, and any manual table would drift the
moment a new example was added. `scripts/example_taxonomy_scan.py` was
written instead: it reuses FR-761's scanner internals (import extraction,
distribution resolution, PEP 503 normalization) to mechanically classify
every discovered root, and writes `examples/dependency-taxonomy.yaml` as a
generated artifact. `--check` mode fails when the committed file drifts
from a fresh discovery run, so a new/removed root is caught mechanically —
satisfying R-2's "test fails when a root is omitted" requirement without
hand maintenance.

**Root-discovery scope decisions** (documented per R-2's mechanical
definition, applied literally would also count loose top-level files):
- `examples/demos/` is flattened one level (each demo subdirectory is its
  own root) rather than treated as a single root — this matches "one row
  per independently-runnable unit."
- `examples/shared/` is excluded — it is a support library imported by many
  other roots, not itself independently runnable.
- Loose top-level files directly under `examples/` (not inside a directory)
  are not discovered as roots under this directory-based definition; none
  currently carry third-party imports that would need taxonomy tracking.

**Local-module false-positive fix.** The first taxonomy run flagged 12
false positives — `tools`, `utils`, `api`, `actions`, `canon_tools`,
`chatterbox` (module, not the `chatterbox-tts` distribution), `tavily`
(module, not `tavily-python`), and others — all either genuinely local
per-example modules imported via the common `sys.path.insert(...); import
X` fixture idiom, or real third-party packages missing an alias in
`direct_import_scan.py`'s `IMPORT_TO_DIST` table (`tavily`→`tavily-python`,
`chatterbox`→`chatterbox-tts`, added). Local-module detection (matching a
`.py` stem or subdirectory name anywhere under the same root) was added to
both `example_taxonomy_scan.py` and `direct_import_scan.py`'s `scan()` (the
latter needed it too once AC-08 promoted extra-backed example roots to
strict). Final result: 111 extra-backed, 1 externally-provisioned
(`examples/agent-sdk-planner`, citing `claude_agent_sdk` — satisfies AC-05).

**AC-08 implementation.** `direct_import_scan.py`'s `scan()` gained an
optional `taxonomy_path` parameter: report-only files under an
`extra-backed` taxonomy root are now held to core-failure standard
(blocking `--strict` unless in `PENDING_GAPS`); files under an
`externally-provisioned` root, or under no taxonomy row at all (e.g.
`examples/shared/`, `scripts/`, `tests/`), keep the pre-FR-762 report-only
behavior. `main()` auto-detects `examples/dependency-taxonomy.yaml` when
present. `PENDING_GAPS`'s `litellm`/`starlette`/`protobuf` entries (owned by
this FR) were removed now that they are genuinely declared; `langchain_core`
(FR-760, separately in flight) remains.

**AC-09 implementation.** CI's `.[dev,digest,websearch,a2a,fsm,verify]`
install line gained `,rag,replicate,openai-proxy,examples-dungeon-master` —
all lightweight, pure-Python-wheel packages. `tests/unit/test_example_extra_imports.py`
does a real `importlib.import_module()` for every package declared by each
of those extras. `torch`/`torchaudio` (chatterbox) are declared in
`pyproject.toml` for direct-import honesty but deliberately NOT installed in
CI per C-3; the corresponding test documents this as a standing decision
rather than asserting an import.

**New capability/requirement:** `capabilities/CAP-213-example-dependency-taxonomy.yaml`
(REQ-YG-571) covers `scripts/example_taxonomy_scan.py`,
`tests/unit/test_example_taxonomy_scan.py`, the taxonomy-aware additions to
`direct_import_scan.py`, and `tests/unit/test_example_extra_imports.py`.
