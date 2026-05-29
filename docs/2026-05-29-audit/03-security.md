# Audit Report — Security & Dependencies

**Date**: 2026-05-29 | **Version**: 0.5.4

## Dependency Security Scanning

### Local
`pip-audit` is not installed in the local development environment. This is a **finding** — the tool should be available for local verification.

### CI
The `security` workflow (`.github/workflows/security.yml`) runs `pip-audit` on every PR. This is enforced as a required status check at the branch protection level... **however**, it is NOT currently listed in the branch protection required checks (see findings below).

## Static Security Measures

### Shell Injection Protection
- All user variables sanitized with `shlex.quote()` in `yamlgraph/tools/shell.py`
- No `eval()` usage in production code
- Command templates use YAML config (trusted); runtime variables are escaped

### Secrets Management
- API keys read from environment variables only
- `detect private key` pre-commit hook active
- No hardcoded secrets in codebase (pre-commit scans all files)

### Pre-commit Security Hooks
| Hook | Status |
|------|--------|
| detect private key | PASS |
| check python ast (syntax validity) | PASS |
| debug statements (python) | PASS |

## Branch Protection Findings

### Documented vs. Actual Required Status Checks

The `CLAUDE.md` documents these required status checks:
- `commitlint`
- `test`
- `conflict-check`
- `copilot-trailer-gate`
- `wip-gate`
- `changelog-gate`
- `changelog-req-gate`
- `demo-gate`
- `diary-gate`
- `security`

**Actually enforced** (per GitHub API):
- `commitlint`
- `test (3.11)`
- `test (3.12)`

### Gap Analysis

| Documented Check | Enforced | Risk |
|-----------------|----------|------|
| commitlint | YES | — |
| test | YES (split: 3.11 + 3.12) | — |
| conflict-check | NO | Low (pre-commit catches locally) |
| copilot-trailer-gate | NO | Medium (could be bypassed) |
| wip-gate | NO | Low (advisory) |
| changelog-gate | NO | Low (process, not security) |
| changelog-req-gate | NO | Low (process) |
| demo-gate | NO | Low (process) |
| diary-gate | NO | Low (process) |
| security | NO | **Medium** (CVE check not enforced at merge) |

## Recommendations

1. **Install pip-audit locally**: `pip install pip-audit` for local security verification
2. **Add missing status checks to branch protection**: At minimum, add `security` and `copilot-trailer-gate` as required checks
3. **Document the gap**: The CLAUDE.md lists checks that are not enforced — either enforce them or update documentation

## Verdict

**PARTIAL PASS** — Security controls exist but branch protection enforcement does not match documented requirements. The gap between documented and actual required status checks is the primary finding.
