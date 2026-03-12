# Feature Request: CI Dependency Security Scan

**Priority:** MEDIUM
**Type:** Enhancement
**FR:** FR-187
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-12

## Summary

Add a `pip-audit` CI job in a dedicated `security.yml` workflow to scan Python dependencies for known vulnerabilities on every PR and release tag push.

## Value Statement

All contributors get automated early warning when a dependency introduces a known CVE, preventing vulnerable packages from reaching production.

## Problem

The project has **no dependency vulnerability scanning**. The CI pipeline runs tests, linting, and coverage — but never checks whether installed packages have known security advisories. A compromised or vulnerable transitive dependency (e.g., in langchain, pydantic, or jinja2) would pass CI undetected.

Existing security controls (REQ-YG-055–062) cover **runtime execution bounds** (loop limits, timeouts, shell injection prevention) but not **supply-chain risk** at the dependency level.

## Proposed Solution

Create a new `.github/workflows/security.yml` workflow with a single `security` job that runs `pip-audit`. The workflow triggers on both `pull_request` and version tag pushes.

### Why a new workflow

The release pipeline (`workflow.yml`) triggers only on version tags. Adding a `pull_request` trigger there would cause `build`, `publish`, and `create-release` to fire on every PR — unacceptable without extensive `if:` guards.

Placing the job in `commitlint.yml` is possible but mixes concerns: that workflow validates PR metadata (title format, changelog fragments, diary reflections), not code or dependency quality.

A dedicated `security.yml` is the cleanest option:
- Triggers on both `pull_request` and `push: tags: v*.*.*`
- Single responsibility: dependency vulnerability scanning
- No pollution of existing workflows
- Produces a single `security` status check name for branch protection

### Gating semantics

- **On PRs:** The `security` job gates via branch protection (required status check). This is the primary enforcement boundary.
- **On tag pushes:** The `security` job runs in parallel with the release pipeline as defense-in-depth. It cannot use `needs` to gate `build` in `workflow.yml` because GitHub Actions `needs` cannot cross workflow boundaries. However, tag pushes only occur after a PR was merged to `main`, which already required `security` to pass. Tag-time scanning catches vulnerabilities disclosed between PR merge and release.

### Workflow file

```yaml
# .github/workflows/security.yml
name: Dependency Security Scan

on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    tags:
      - 'v*.*.*'

permissions:
  contents: read

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]" pip-audit

      - name: Run pip-audit
        run: pip-audit --strict --desc
```

### Why pip-audit over alternatives

| Criterion | pip-audit | safety |
|-----------|-----------|--------|
| Maintained by | PyPA (Python Packaging Authority) | SafetyCLI (commercial) |
| Data source | OSV + PyPI advisory DB | SafetyCLI proprietary DB |
| License | Apache-2.0 | MIT (free tier limited) |
| Auth required | No | Yes (API key for full DB since v3) |
| CI friction | Zero config | Requires `SAFETY_API_KEY` secret |

`pip-audit` is the PyPA-endorsed tool, uses the open OSV database, requires no API keys, and integrates cleanly into existing CI without secrets management.

### Branch protection update

Add `security` to the required status checks list for `main` (alongside `commitlint`, `test`, `conflict-check`, `changelog-gate`, `diary-gate`).

### Documentation updates

Update the branch protection table and required status checks section in `CLAUDE.md`:

- Add `security` row to the "Required status checks" table
- Add `security` entry to the detailed status checks list with description: validates installed dependencies have no known vulnerabilities (CVEs) via `pip-audit`

## Acceptance Criteria

- [ ] `.github/workflows/security.yml` exists with a `security` job running `pip-audit --strict --desc`
- [ ] The workflow triggers on `pull_request` (opened, synchronize, reopened) and `push: tags: v*.*.*`
- [ ] `security` is added to required status checks in branch protection for `main`
- [ ] Documentation updated: add `security` job to the branch protection table in `CLAUDE.md` and the required status checks list
- [ ] A known-vulnerable dependency (simulated via pinned version) causes the job to fail (manual verification on PR)

## Alternatives Considered

1. **safety**: Requires API key for full vulnerability DB since v3. Adds secret management overhead. Commercial model may change terms.
2. **Dependabot**: GitHub-native, but operates on a schedule (not per-PR) and creates PRs rather than blocking merges. Complementary but not a gate.
3. **Snyk / Trivy**: Full-featured but heavyweight for a Python-only project. Better suited for container/multi-ecosystem scanning.
4. **Pre-commit hook**: Running pip-audit locally is slow (~10s) and requires network access. CI-only is the right boundary — developers get feedback on PR, not on every commit.
5. **Add to `commitlint.yml`**: Mixes dependency scanning with PR metadata validation. Different concern, different failure modes, different fix actions.
6. **Add to `workflow.yml` with `pull_request` trigger**: Would require `if:` guards on `build`, `publish`, and `create-release` to prevent release steps on PRs. Fragile and violates single responsibility.

## Related

- `.github/workflows/workflow.yml` — release pipeline (test → build → publish → release)
- `.github/workflows/commitlint.yml` — PR gate checks (commitlint, conflict-check, changelog-gate, diary-gate)
- `ARCHITECTURE.md` REQ-YG-055–062 — existing execution safety guards
- `CLAUDE.md` branch protection table — documents required status checks
