# Feature Request: Import-Linter Architectural Boundary Enforcement

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-04-08

## Summary

Add `import-linter` to the pre-commit and CI pipeline with explicit layer contracts that mechanically enforce the three-layer architecture (`cli → graph_loader/node_factory/executor → tools/models/utils`).

## Value Statement

All contributors get immediate, automated feedback when an import violates the declared architectural layers, preventing silent degradation of module boundaries under deadline pressure.

## Problem

The three-layer architecture (Presentation → Logic → Side Effects) is documented in ARCHITECTURE.md and CLAUDE.md but enforced by convention only. There is no mechanical contract preventing:

- `tools/` importing from `cli/` (side effects reaching into presentation)
- `models/` or `utils/` importing from `graph_loader` or `executor` (data layer depending on logic layer)
- A new module landing in the wrong layer under deadline pressure

The existing `scripts/lint_inline_llm.py` (REQ-YG-073) covers one symptom — inline LLM orchestration bypassing YAML graphs — but does not enforce the full dependency graph. The architecture can silently degrade across any module boundary.

This is a `detection_without_enforcement` violation: the architecture is claimed in documentation but not contracted in code. The Scripture already identifies this pattern: *"Lint without gate = advisory → add CI block or remove claim."*

The `architecture_as_diagram` trap (Knowledge Graph) names this directly: *"Three-layer documented but not contracted → violation possible under deadline pressure; enforce at module boundary with import-linter."*

## Proposed Solution

### 1. Add `import-linter` dependency

```toml
# pyproject.toml [project.optional-dependencies]
dev = [
    # ... existing ...
    "import-linter>=2.0",
]
```

### 2. Create `.importlinter` config

```ini
[importlinter]
root_package = yamlgraph

[importlinter:contract:three-layer]
name = Three-layer architecture (Presentation → Logic → Side Effects)
type = layers
layers =
    yamlgraph.cli
    yamlgraph.graph_loader | yamlgraph.node_factory | yamlgraph.executor | yamlgraph.linter | yamlgraph.edge_compiler | yamlgraph.node_compiler | yamlgraph.map_compiler | yamlgraph.routing | yamlgraph.graph_cache | yamlgraph.schema_loader | yamlgraph.data_loader | yamlgraph.discovery | yamlgraph.executor_async | yamlgraph.interactive_tool
    yamlgraph.tools | yamlgraph.models | yamlgraph.utils | yamlgraph.config | yamlgraph.constants | yamlgraph.storage | yamlgraph.schemas | yamlgraph.contrib | yamlgraph.executor_base | yamlgraph.error_handlers | yamlgraph.verification
```

This declares that:
- **Layer 1** (`cli`) may import from Layer 2 and Layer 3
- **Layer 2** (`graph_loader`, `node_factory`, `executor`, `linter`, `edge_compiler`, `node_compiler`, `map_compiler`, `routing`, `graph_cache`, `schema_loader`, `data_loader`, `discovery`, `executor_async`, `interactive_tool`) may import from Layer 3 only
- **Layer 3** (`tools`, `models`, `utils`, `config`, `constants`, `storage`, `schemas`, `contrib`, `executor_base`, `error_handlers`, `verification`) may not import from Layer 1 or Layer 2

**Note:** `executor_base`, `error_handlers`, and `verification` are placed in Layer 3 despite their names suggesting logic-layer affinity. Empirically, they only import from Layer 3 modules and are consumed by both Layer 2 and Layer 3 — making them shared utilities, not orchestration logic.

**Uncategorised modules** (`a2a_server`, `a2a_message`, `mcp_server`, `diary`, `toolsthon_tool`) are intentionally excluded from the layer contract. These are application-level entry points or experimental modules. Each should be assigned to a layer in a follow-up FR once their architectural role stabilises.

### 3. Add pre-commit hook

```yaml
# .pre-commit-config.yaml (local hook)
- repo: local
  hooks:
    - id: import-linter
      name: import-linter architectural boundaries
      entry: .venv/bin/lint-imports
      language: system
      pass_filenames: false
      always_run: true
      stages: [pre-commit]
```

### 4. Add CI check

Add `lint-imports` to `.github/workflows/workflow.yml` as a step in the lint job, or as a separate required status check, consistent with how `ruff` is run.

### 5. Document exceptions

If any current imports violate the contract (research found zero violations), document them as `importlinter:contract:*` `ignore_imports` entries with justification, following the same confession pattern as `noqa` in `docs/confessions.md`.

## Acceptance Criteria

- [ ] `import-linter>=2.0` added to `dev` dependencies in `pyproject.toml`
- [ ] `.importlinter` config file committed at repo root declaring three-layer contracts
- [ ] `lint-imports` passes on current codebase with zero violations
- [ ] `lint-imports` added to pre-commit as a local system hook
- [ ] `lint-imports` added to CI workflow as a required check
- [ ] All current violations (if any) resolved or explicitly documented as exceptions in `docs/confessions.md`
- [ ] REQ-YG-218 added to ARCHITECTURE.md: "Module imports must not violate declared layer contracts"
- [ ] Tests: `pytest` test that invokes `lint-imports` programmatically and asserts exit code 0
- [ ] Documentation updated in CLAUDE.md (Code Quality Standards section)

## Alternatives Considered

1. **Custom script (like `lint_inline_llm.py`)**: A bespoke Python script scanning AST for forbidden imports. Rejected because `import-linter` is a mature, well-maintained tool purpose-built for this exact problem. Writing our own would duplicate effort and miss edge cases (re-exports, conditional imports, `__init__` barrels).

2. **pylint import restrictions**: `pylint` has `allowed-modules` but it operates per-file, not as a layered contract. It cannot express "Layer A may import Layer B but not vice versa" without per-module configuration that drifts.

3. **Documentation only**: Continue relying on code review to catch violations. Rejected because the Scripture explicitly prohibits `detection_without_enforcement` — and the `architecture_as_diagram` trap names this exact failure mode.

## Judgement

**Verdict: APPROVED** — scope frozen, authority granted.

**Amendments applied during review:**

1. **Expanded layer coverage.** The original FR listed 8 of 30 top-level modules across 3 layers — 22 modules were unconstrained and could import from any layer without triggering a violation. This undermined the enforcement claim (the FR's own `detection_without_enforcement` citation applied to itself). All modules have now been assigned to layers, with 5 experimental/entry-point modules (`a2a_server`, `a2a_message`, `mcp_server`, `diary`, `toolsthon_tool`) documented as intentionally excluded pending architectural stabilisation.

2. **Corrected layer assignment for shared utilities.** `executor_base`, `error_handlers`, and `verification` were initially placed in Layer 2 (Logic), but empirical analysis shows they only import from Layer 3 modules and are consumed by both Layer 2 and Layer 3. They are shared utilities, not orchestration logic, and belong in Layer 3. The corrected assignment yields zero import violations against the current codebase.

**Validation:** AST-based import scan across all 30 modules confirms zero violations with the final layer assignment.

## Related

- `ARCHITECTURE.md` — Three-layer architecture diagram (lines 36–70)
- `CLAUDE.md` — Three-layer pattern description and anti-patterns
- `scripts/lint_inline_llm.py` — Existing partial enforcement (REQ-YG-073)
- `.pre-commit-config.yaml` — Hook infrastructure
- `.github/workflows/workflow.yml` — CI pipeline
- Knowledge Graph: `module_structure` boundary, `architecture_as_diagram` trap, `detection_without_enforcement` process pattern
