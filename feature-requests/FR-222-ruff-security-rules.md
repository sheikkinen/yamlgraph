# Feature Request: Ruff Security Rules (flake8-bandit)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-04-12

## Summary

Enable the ruff `S` ruleset (flake8-bandit security checks) in `pyproject.toml` so that security-relevant code patterns are flagged at lint time.

## Value Statement

Framework maintainers get automated detection of insecure coding patterns (hardcoded passwords, unsafe subprocess calls, missing autoescape) at every commit, reducing the risk of security regressions.

## Problem

The `S` (flake8-bandit) ruleset is not enabled in ruff configuration. This means security-sensitive patterns like `shell=True`, binding to `0.0.0.0`, and unescaped Jinja2 templates are not flagged by the linter. While the current codebase handles these patterns safely (e.g., `shlex.quote()` for shell injection), new code could introduce insecure patterns without any lint warning.

## Proposed Solution

1. Add `"S"` to `[tool.ruff.lint] select` in `pyproject.toml`.
2. Triage existing violations — all 7 are legitimate patterns that require `# noqa` suppression with documented confessions.
3. Add a test verifying `ruff check --select S` passes clean on `yamlgraph/`.

### Existing Violations (all require noqa suppression)

| Rule | File | Rationale |
|------|------|-----------|
| S104 | `cli/__init__.py:207` | Intentional `0.0.0.0` default for A2A server CLI |
| S104 | `cli/a2a_commands.py:58` | Same — A2A server fallback host |
| S602 | `tools/shell.py:131` | `shell=True` required for pipes/redirects; variables sanitized via `shlex.quote()` |
| S603 | `node_factory/copilot_node.py:260` | `subprocess.run(cmd)` with internally-built cmd list |
| S607 | `utils/worktree_helpers.py:94` | `["git", ...]` partial path — git expected on PATH |
| S607 | `utils/worktree_helpers.py:105` | Same |
| S701 | `utils/template.py:47` | Jinja2 `Environment()` for YAML template parsing, not HTML rendering |

## Acceptance Criteria

- [x] `"S"` added to `[tool.ruff.lint] select` in `pyproject.toml`
- [x] `ruff check yamlgraph/ --select S` exits 0 (all violations suppressed or fixed)
- [x] Each `# noqa: SXXX` has a confession entry in `docs/confessions.md`
- [x] Test verifies ruff S rules pass clean
- [x] REQ-YG-220 added to `ARCHITECTURE.md`
- [x] CAP-86 capability file created
- [x] Changelog fragment created

## Alternatives Considered

- **Fix all violations instead of suppressing**: Not viable. `0.0.0.0` binding and `shell=True` are intentional design choices with appropriate safeguards.
- **Enable only specific S rules**: Would miss future security patterns. Better to enable all and suppress known-safe patterns.

## Related

- FR-187: CI dependency security scan (pip-audit)
- Commandment 6: "Expose every fault to ruff and CI"
- `.pre-commit-config.yaml`: ruff pre-commit hook
