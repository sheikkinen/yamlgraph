# Feature Request: Dependency Rationale Deep Audit

**Priority:** LOW
**Type:** Enhancement
**FR:** FR-245
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-04-19

## Summary

Extend `scripts/dependency_rationale.py` with orphan detection and module-path validation so the audit catches stale entries and broken `modules` references, not just missing entries.

## Value Statement

Maintainers get accurate dependency-to-code traceability by catching orphaned registry entries and invalid module paths, preventing the rationale registry from silently drifting out of sync with the codebase.

## Problem

FR-219 established the dependency rationale audit, but it only checks one direction: "is every pyproject.toml dependency documented?" Two failure modes go undetected:

1. **Orphaned entries** — A dependency is removed from `pyproject.toml` but its rationale entry remains. The registry reports 43 documented entries but nobody knows if all 43 are still relevant.

2. **Stale module paths** — The `modules` field lists files/directories that no longer exist. Today `ddgs` references `yamlgraph/tools/web_search.py` which was moved to `examples/shared/websearch.py` — a live example of silent drift.

Both undermine the registry's value as a source of truth for "which code uses this dependency."

## Proposed Solution

### 1. Add `find_orphaned()` function

```python
def find_orphaned(
    deps: dict[str, list[str]],
    registry: dict[str, dict],
) -> list[str]:
    """Find registry entries not present in any pyproject.toml group."""
    all_dep_names = set()
    for pkgs in deps.values():
        all_dep_names.update(pkgs)
    return sorted(set(registry.keys()) - all_dep_names)
```

### 2. Add `find_stale_modules()` function

```python
def find_stale_modules(
    registry: dict[str, dict],
    root: Path,
) -> list[tuple[str, str]]:
    """Find registry entries with modules paths that don't exist on disk.

    Skips non-filesystem references (e.g., 'pyproject.toml [tool.ruff]').
    Returns list of (package_name, invalid_path) tuples.
    """
```

### 3. Integrate into `main()` reporting

- Orphans reported under `⚠ Orphaned rationale entries (dep removed from pyproject.toml):`
- Stale modules reported under `⚠ Stale module paths (file/dir not found):`
- `--strict` mode exits 1 on orphans or stale modules (in addition to undocumented deps)

### 4. CLI flags

No new flags needed. Orphan and stale-module checks run unconditionally. `--strict` already gates on problems.

## Acceptance Criteria

- [ ] `find_orphaned()` detects entries in registry not in any pyproject.toml group
- [ ] `find_stale_modules()` detects `modules` paths that don't exist on disk
- [ ] Non-filesystem module references (containing `[`) are skipped
- [ ] `--strict` exits 1 when orphaned entries or stale modules exist
- [ ] Report output shows orphans and stale modules in separate sections
- [ ] Fix the existing stale entry: `ddgs.modules` → `["examples/shared/websearch.py", "examples/demos/fi_domain_crawl/nodes/seed_discovery.py"]`
- [ ] Unit tests cover `find_orphaned()` and `find_stale_modules()`
- [ ] Tests tagged with `@pytest.mark.req("REQ-YG-218")` (extends existing dependency-rationale requirement)

## Alternatives Considered

1. **Separate script** — A new `dependency_rationale_deep.py` script. Rejected: the checks are natural extensions of the existing audit, adding a second script fragments the workflow.
2. **Import scanning with AST** — Actually verify imports match the `modules` field by parsing Python ASTs. Too complex for the value; module-path existence is a sufficient proxy. Could be a future FR if drift proves persistent.
3. **CI workflow gate** — Add a GitHub Actions check alongside the pre-commit hook. Out of scope for this FR; the pre-commit hook already blocks commits that touch `pyproject.toml` or the registry.

## Related

- `feature-requests/FR-219-dependency-rationale-audit.md` — Parent FR (implemented)
- `scripts/dependency_rationale.py` — Script to extend
- `docs/dependency-rationale.yaml` — Registry with the stale `ddgs` entry
- `scripts/noqa_coverage.py` — Sibling audit pattern
