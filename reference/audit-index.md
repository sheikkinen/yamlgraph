# Audit Index

> Evidence map for the YAMLGraph development lifecycle.
> Last updated: 2026-05-07

## Governance

| Artifact | Path | Purpose |
|----------|------|---------|
| Architecture | [ARCHITECTURE.md](../ARCHITECTURE.md) | Capabilities registry, requirements (REQ-YG-XXX), design philosophy |
| Scripture | [.github/copilot-instructions.md](../.github/copilot-instructions.md) | Doctrine: commandments, traps, cures, process rules |
| ADRs | [docs/adr/](../docs/adr/) | Architecture decision records (ADR-001: req traceability, ADR-002: LangSmith traces) |
| Feature Requests | [feature-requests/](../feature-requests/) | 343 FRs — proposal → judgement → implementation lifecycle |
| Break Glass | [reference/break-glass.md](break-glass.md) | Emergency bypass procedure with audit trail |
| Release Checklist | [reference/release-checklist.md](release-checklist.md) | Bump → commit → push → tag flow |

## Quality Gates

### CI Workflows (`.github/workflows/`)

| Workflow | File | Checks |
|----------|------|--------|
| Commit Lint | `commitlint.yml` | PR title, conflict markers, changelog gate, diary gate, demo gate |
| Tests | `workflow.yml` | pytest (80% coverage), ruff |
| Security | `security.yml` | pip-audit CVE scan |
| Daily Digest | `daily-digest.yml` | Automated digest generation |

### Pre-commit Hooks (28 hooks)

| Category | Hooks |
|----------|-------|
| Style | ruff, ruff-format, trailing-whitespace, end-of-file-fixer |
| Safety | check-ast, check-yaml, check-toml, debug-statements, detect-private-key, check-merge-conflict |
| Architecture | import-linter (layer boundaries), file-size-gate (>450 lines), radon-complexity (grade D block) |
| Duplication | jscpd-dup, vulture-dead-code |
| Traceability | req-coverage-strict, changelog-required, changelog-req-cross-check, demo-proof-check |
| Discipline | noqa-confession, dependency-rationale, inline-llm-check, hedging-check, forbid-terms |
| Provenance | conventional-pre-commit, feat-requires-fr, block-ai-coauthor |
| Tests | pytest (parallel, skip slow) |

## Traceability

| What | Where | Enforcement |
|------|-------|-------------|
| Requirement → Test | `@pytest.mark.req("REQ-YG-XXX")` on every test | `scripts/req_coverage.py --strict` + pre-commit |
| Capability → Requirements | [capabilities/](../capabilities/) (126 CAP files) | `scripts/validate_capabilities.py` + pre-commit |
| Suppression → Justification | [docs/confessions.md](../docs/confessions.md) (719 lines) | `scripts/noqa_coverage.py --strict` + pre-commit |
| Dependency → Rationale | [docs/dependency-rationale.yaml](../docs/dependency-rationale.yaml) | `dependency-rationale` pre-commit hook |
| Change → Changelog | [changelog/](../changelog/) (111 versions + unreleased fragments) | `changelog-required` hook + `changelog-gate` CI |
| Feature → FR reference | `feat:` commits must cite `FR-XXX` | `feat-requires-fr` hook + `commitlint` CI |

## Continuous Reflection

| Artifact | Path | Volume |
|----------|------|--------|
| Diary | [docs/diary/](../docs/diary/) | 607 entries (2025-04-23 → present) |
| Inquisitor audits | `docs/diary/inquisitor-audit-*` | 200+ commit audits against Scripture |
| Philosopher entries | `docs/diary/philosopher-*` | Pattern graduation proposals |
| Git reports | `docs/diary/git-report-*` | Daily activity summaries |

## Automation

| Component | Path | Role |
|-----------|------|------|
| Chaplain (archived) | [docs/archive/chaplain.md](../docs/archive/chaplain.md) | Retired FSM runtime (FR-1010–FR-1013): archive tag, replacement table, design note |
| Philosopher | `graphs/philosopher/graph.yaml` | Diary pattern scanning, graduation proposals (dormant) |

## Verification Commands

```bash
# Requirement coverage
python scripts/req_coverage.py --strict --detail

# noqa suppression coverage
python scripts/noqa_coverage.py --strict

# Capability registry validation
python scripts/validate_capabilities.py capabilities/

# Import boundary enforcement
lint-imports

# Dead code detection
vulture yamlgraph/ vulture_whitelist.py

# Cyclomatic complexity
radon cc yamlgraph/ -a -nc

# Dependency audit
pip-audit

# Full pre-commit suite
pre-commit run --all-files
```
