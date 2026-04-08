# Feature Request: Dependency Rationale Audit

**Priority:** MEDIUM
**Type:** Enhancement
**FR:** FR-219
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-04-09

## Summary

Audit script that verifies every `pyproject.toml` dependency (core and optional) has a documented rationale in `docs/dependency-rationale.yaml`.

## Value Statement

Maintainers get immediate CI feedback when undocumented dependencies are added, preventing "why do we need this?" questions during reviews and reducing supply-chain risk from unexplained transitive pulls.

## Problem

YAMLGraph's `pyproject.toml` lists 11 core dependencies and 14 optional dependency groups with no documented rationale for why each package is needed or which modules consume it. When evaluating security advisories, upgrade decisions, or dependency pruning, developers must reverse-engineer the "why" from imports scattered across the codebase.

The noqa confession pattern (`docs/confessions.md` + `scripts/noqa_coverage.py`) has proven this "registry + audit" approach effective. Applying the same pattern to dependencies closes a documentation gap flagged by the infrastructure-self-exempt trap.

## Proposed Solution

### 1. Rationale Registry — `docs/dependency-rationale.yaml`

```yaml
# Dependency Rationale Registry
# Every pyproject.toml dependency must have an entry here.
# Run: python scripts/dependency_rationale.py --strict

dependencies:
  langchain-anthropic:
    rationale: "Anthropic LLM provider integration for Claude models"
    modules: ["yamlgraph/utils/llm_factory.py"]
    added: "0.1.0"

  pydantic:
    rationale: "Structured LLM output validation (Commandment 5)"
    modules: ["yamlgraph/models/"]
    added: "0.1.0"
```

### 2. Audit Script — `scripts/dependency_rationale.py`

```bash
python scripts/dependency_rationale.py           # summary report
python scripts/dependency_rationale.py --detail  # show all entries
python scripts/dependency_rationale.py --strict  # exit 1 on gaps
```

Follows `noqa_coverage.py` pattern:
- Parse `pyproject.toml` for all dependency names (strip version specifiers)
- Load `docs/dependency-rationale.yaml` entries
- Report undocumented packages
- `--strict` mode exits 1 when gaps exist

### 3. Pre-commit Hook

```yaml
- id: dependency-rationale
  name: dependency-rationale --strict
  entry: .venv/bin/python scripts/dependency_rationale.py --strict
  language: system
  pass_filenames: false
  files: (pyproject\.toml|docs/dependency-rationale\.yaml)
  stages: [pre-commit]
```

## Acceptance Criteria

- [x] `scripts/dependency_rationale.py` parses `pyproject.toml` `[project.dependencies]` and `[project.optional-dependencies]`
- [x] `docs/dependency-rationale.yaml` documents every current dependency with rationale, modules, and added version
- [x] `--strict` mode exits 1 when undocumented dependencies exist
- [x] `--detail` mode shows all rationale entries
- [x] Pre-commit hook registered in `.pre-commit-config.yaml`
- [x] Unit tests cover parse, compare, and main functions
- [x] REQ-YG-218 added to ARCHITECTURE.md

## Alternatives Considered

1. **Inline comments in pyproject.toml** — TOML supports comments but they're not machine-parseable. Can't enforce or validate.
2. **Markdown table** — Harder to parse programmatically than YAML. Doesn't match the Pydantic-first philosophy.
3. **pip-licenses output** — Shows license info but not rationale (why we chose it).

## Related

- `scripts/noqa_coverage.py` — Confession registry pattern this follows
- `docs/confessions.md` — Existing registry-audit pattern
- FR-187 — CI dependency security scan (complementary: security + rationale)
- `pyproject.toml` — Source of truth for dependencies
