# Judgement: FR-762 Example Dependency Taxonomy and Direct-Import Honesty

**Verdict:** APPROVED WITH REVISIONS — the dependency-taxonomy direction is sound, but authority activates only after the FR freezes the example classifications, removes the FR-761 scan-implementation overlap, and makes the "every example" rule mechanically checkable.

**Reviewed against:** `feature-requests/FR-762-example-dependency-taxonomy.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `docs/plan-research-dependency-negative-space.md`; `feature-requests/FR-759-otel-observability-boundary.md`; `feature-requests/FR-760-declare-langchain-core-dependency.md`; `feature-requests/FR-761-reproducible-dependency-governance.md`; `pyproject.toml`; `docs/dependency-rationale.yaml`; `examples/rag/README.md`; `examples/rag/index_docs.py`; `examples/dungeon_master/README.md`; `examples/dungeon_master/api/prompt_salience.py`; `examples/dungeon_master/api/plot/validate.py`; `examples/demos/chatterbox/README.md`; `examples/demos/chatterbox/tools.py`; `examples/demos/chatterbox/speak.py`; `examples/agent-sdk-planner/README.md`; `examples/agent-sdk-planner/plan.py`; `examples/openai_proxy/README.md`; `examples/openai_proxy/api/app.py`; `examples/shared/websearch.py`; `examples/demos/fi_domain_crawl/nodes/seed_discovery.py`; `yamlgraph/utils/llm_providers.py`; `yamlgraph/a2a/server.py`; `yamlgraph/cli/a2a_commands.py`; direct repository search for the imports named in the FR.

## What is sound

The problem is real and evidenced. FR-762 names the first user-facing failure as `pip install "yamlgraph[rag]"` followed by `examples/rag/index_docs.py` failing on imports such as `pyarrow` (`feature-requests/FR-762-example-dependency-taxonomy.md:8`), and the cited research records that examples have outgrown their extras and lack dependency tests (`docs/plan-research-dependency-negative-space.md:109-122`). The concrete import evidence matches the claim: `examples/rag/index_docs.py:232-234` imports `lancedb`, `pyarrow`, and `openai`, while the current `rag` extra declares only `lancedb` and `openai` (`pyproject.toml:85-88`).

The strategic classification is correct: this is a contrib/example dependency-governance fix, not a framework primitive. The research recommendation is specifically to "Create an example dependency taxonomy" and then fix direct-import honesty (`docs/plan-research-dependency-negative-space.md:198-199`), while sibling FR-760 owns the core `langchain-core` dependency (`feature-requests/FR-760-declare-langchain-core-dependency.md:30-37`) and sibling FR-761 owns the reusable direct-import scan (`feature-requests/FR-761-reproducible-dependency-governance.md:32-39`). FR-762 should therefore provide classifications and dependency fixes, not reinvent the scanner.

The FR honors existing repo patterns before extending them. Optional dependencies already live in `[project.optional-dependencies]` (`pyproject.toml:38-127`), every declared dependency must be recorded in `docs/dependency-rationale.yaml` (`docs/dependency-rationale.yaml:1-5`), and repo doctrine requires TDD plus requirement traceability for tests (`.github/copilot-instructions.md:171-174`, `.github/copilot-instructions.md:218-219`). The proposed dependency-rationale and changelog criteria align with those gates (`feature-requests/FR-762-example-dependency-taxonomy.md:61-62`).

The entropy-removal part is sound. `duckduckgo_search` is a legacy fallback beside declared `ddgs` in both shared web search and the `.fi` demo (`examples/shared/websearch.py:23-35`, `examples/demos/fi_domain_crawl/nodes/seed_discovery.py:16-22`), and Commandment 8 directs dead-code deletion over preserving false idols (`.github/copilot-instructions.md:220`).

**Prior art:** the only hit is FR-762's own body (self-match). Sibling FR-760 (core `langchain-core` declaration) and FR-761 (reusable direct-import scanner) are disjoint in scope and already cross-referenced above and in the Related section; FR-762 consumes FR-761's scanner rather than duplicating it (R-3 below).

## Required revisions

### R-1: Freeze the example classifications in the FR

Replace the open-ended "or mark externally provisioned -- decision at judgement" branches (`feature-requests/FR-762-example-dependency-taxonomy.md:46-47`) with this fixed classification table:

| Surface | Classification | Required dependency action |
|---|---|---|
| `yamlgraph/utils/llm_providers.py` Replicate provider | extra-backed | Add `litellm` explicitly to `replicate`; keep `langchain-litellm` (`yamlgraph/utils/llm_providers.py:294-295`, `pyproject.toml:69-71`). |
| `examples/rag/` | extra-backed by `rag` | Add `pyarrow` to `rag`; README already instructs `pip install yamlgraph[rag]` (`examples/rag/README.md:5-13`, `examples/rag/index_docs.py:232-234`). |
| `examples/dungeon_master/` | extra-backed by new `examples-dungeon-master` | Add `tiktoken`, `unified-planning`, and the server packages required to import/run the documented app entry points; the lazy optional imports still need a declared supported-install story (`examples/dungeon_master/api/prompt_salience.py:35-42`, `examples/dungeon_master/api/plot/validate.py:32-60`). |
| `examples/demos/chatterbox/` | extra-backed by existing `chatterbox` | Add direct `torch` and `torchaudio` declarations consistent with the README's platform constraints; do not hide them as transitive dependencies (`examples/demos/chatterbox/README.md:45-69`, `examples/demos/chatterbox/tools.py:25-27`, `examples/demos/chatterbox/speak.py:77-78`). |
| `examples/agent-sdk-planner/` | externally provisioned | Add the external marker to the taxonomy; do not add `claude-agent-sdk` to project extras because the README already presents it as a standalone spike prerequisite (`examples/agent-sdk-planner/README.md:1-18`, `examples/agent-sdk-planner/plan.py:170-182`). |
| `examples/openai_proxy/` | extra-backed by a named example extra | Add or update a named extra that owns FastAPI/Uvicorn/OpenAI-proxy imports and declares `starlette` explicitly because the code imports it directly (`examples/openai_proxy/README.md:30-38`, `examples/openai_proxy/api/app.py:60-64`). |
| `yamlgraph/a2a/` and A2A CLI/contrib surfaces | extra-backed by `a2a` | Add `starlette` and `protobuf` explicitly to `a2a` because the optional protocol code imports `starlette` and `google.protobuf` directly (`yamlgraph/a2a/server.py:321-325`, `yamlgraph/cli/a2a_commands.py:88-92`, `pyproject.toml:115-118`). |
| `duckduckgo_search` fallback paths | removed | Delete the fallback imports; do not declare `duckduckgo_search` (`examples/shared/websearch.py:23-35`, `examples/demos/fi_domain_crawl/nodes/seed_discovery.py:16-22`). |

This resolves the Scope, Consistency, and Single Responsibility criteria: one FR may own the taxonomy and row fixes, but it must not leave product/spend choices to the enforcer.

### R-2: Make "every example directory classified" mechanically checkable

Add a concrete classification artifact to the FR, preferably `examples/dependency-taxonomy.yaml`, with one row per example root and these fields: `path`, `status` (`extra-backed` or `externally-provisioned`), `extra` when extra-backed, `external_reason` when externally provisioned, and `entrypoints` for import tests. Define "example root" mechanically as any directory under `examples/` that contains a graph YAML, Python app/CLI entry point, or README usage command. Add a test that fails when such a root is omitted. README markers may mirror the taxonomy, but a prose-only README sweep is not mechanically checkable enough for the Measurability criterion.

### R-3: Remove the FR-761 implementation overlap

Revise the proposed solution and acceptance criteria so FR-762 depends on FR-761's scanner instead of implementing a second scan. FR-762 may change the scanner's data/configuration, add external-provisioning allowlist entries from the taxonomy, and flip the example rows from report-only to strict after the dependency fixes land. It must not add a separate direct-import scanner, lockfile, `pip-audit`, or dependency-governance framework; those belong to FR-761 (`feature-requests/FR-761-reproducible-dependency-governance.md:32-39`).

### R-4: Split static declaration checks from heavyweight install checks

Revise verification so the direct-import scanner is strict for every classified supported surface, while resolver/import jobs are required only for cheap supported extras. Keep the existing minimum import checks for `rag` and `replicate` (`feature-requests/FR-762-example-dependency-taxonomy.md:59`), add cheap checks for `a2a`, `examples-openai-proxy`, and `examples-dungeon-master` if their dependency weight is acceptable, and make `chatterbox` a static declaration/platform-marker check unless a human explicitly approves a heavyweight CI install. The Chatterbox README already documents a ~2GB/model and platform-constrained dependency profile (`examples/demos/chatterbox/README.md:45-64`), so a mandatory CI torch install would be a spend/platform decision, not a judgement-side default.

### R-5: Add requirement traceability to the acceptance criteria

Add an acceptance criterion requiring every new or changed test to carry `@pytest.mark.req(...)`, with either an existing requirement ID or a new capability/requirement entry if the taxonomy creates a new governed capability. Repo doctrine requires this for every test (`.github/copilot-instructions.md:171-174`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `reference/example-dependencies.md` or equivalent user-facing rule document defining extra-backed vs externally-provisioned examples |
| D-2 | `examples/dependency-taxonomy.yaml` machine-readable classification artifact |
| D-3 | `pyproject.toml` optional-dependency updates for only the classifications and direct-import rows listed in R-1 |
| D-4 | `docs/dependency-rationale.yaml` entries for every newly declared package |
| D-5 | Removal of `duckduckgo_search` fallback imports from the two cited fallback paths |
| D-6 | Tests for taxonomy completeness, direct-import declaration strictness/configuration, and cheap supported-extra import checks |
| D-7 | FR-761 scanner configuration/allowlist flip, only if FR-761's scanner exists in the branch being enforced |
| D-8 | Changelog fragment in `changelog/unreleased/` |

Not authorized: implementing a new dependency scanner independent of FR-761; adding a lockfile or `pip-audit` local gate; moving examples out of the repository; adding a YAMLGraph-native provider/model adapter; broad package-manager migration; CI jobs that install heavyweight Chatterbox/Torch stacks without explicit human approval; changing judge/review doctrine, hooks, or branch-protection infrastructure.

## Revised acceptance criteria

- [ ] AC-01: The FR documents the binary rule: every example root is either `extra-backed` or `externally-provisioned`; no third state exists.
- [ ] AC-02: `examples/dependency-taxonomy.yaml` lists every mechanically discovered example root and validates `status`, `extra`, `external_reason`, and `entrypoints` according to the rule.
- [ ] AC-03: The R-1 classification table is folded into the FR with no remaining "or judgement decision" branches.
- [ ] AC-04: `pyproject.toml` declares the direct packages required by the R-1 extra-backed surfaces: `litellm`, `pyarrow`, `tiktoken`, `unified-planning`, `torch`, `torchaudio`, `starlette`, and `protobuf`, with platform markers where required.
- [ ] AC-05: `examples/agent-sdk-planner/` is marked externally provisioned in the taxonomy and remains out of project extras.
- [ ] AC-06: `duckduckgo_search` fallback code is removed; `rg "duckduckgo_search" examples yamlgraph tests` finds no live import except historical text if explicitly allowed by the scanner.
- [ ] AC-07: `docs/dependency-rationale.yaml` has one entry per newly declared package and `python scripts/dependency_rationale.py --strict` passes.
- [ ] AC-08: FR-761's direct-import scan, if present, is strict for core and extra-backed example surfaces and uses the taxonomy as the only externally-provisioned allowlist.
- [ ] AC-09: Import-level dependency checks cover at least `rag` and `replicate`, plus every cheap newly supported extra; Chatterbox is verified statically unless a human approves heavyweight CI installation.
- [ ] AC-10: Every new or changed test has `@pytest.mark.req(...)`; add or reuse a valid requirement ID.
- [ ] AC-11: A changelog fragment exists in `changelog/unreleased/`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | If FR-761's scanner is not available in the enforcement branch, stop after dependency/taxonomy/doc fixes and leave strict-scan activation explicitly pending; do not invent a parallel scanner inside FR-762. | GATE |
| C-2 | Do not add `claude-agent-sdk` to any project extra under this FR; the authorized classification is externally provisioned. | GATE |
| C-3 | Do not add a CI job that installs Torch/Chatterbox heavyweight dependencies unless a human explicitly approves the spend/platform tradeoff. | GATE |
| C-4 | Do not add dependencies outside the R-1 table without returning to judgement; the FR's authority is direct-import honesty for the cited rows, not general dependency expansion. | GATE |
| C-5 | Do not modify judge/review doctrine, hooks, or branch-protection infrastructure. | GATE |

Authority granted: after R-1 through R-5 are folded into the FR, the enforcer may implement the example dependency taxonomy, the cited dependency declarations/removals, the taxonomy-backed scanner configuration, and the specified tests within the frozen surfaces above.
