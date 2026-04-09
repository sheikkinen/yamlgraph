# Feature Request: Dependency Rationale Audit

**Priority:** MEDIUM
**Type:** Enhancement
**FR:** FR-219
**Status:** Approved
**Effort:** 1.5 days
**Requested:** 2026-04-09

## Summary

Create `docs/dependency-rationale.md` recording why each package in `pyproject.toml` exists, which modules use it, and whether it is still needed. Add a pre-commit hook that requires this document to be updated whenever `pyproject.toml` changes.

## Value Statement

Maintainers and security reviewers can verify that every dependency has documented justification, making unprompted agent-added packages and rationale drift detectable at the commit boundary.

## Problem

`pyproject.toml` declares 11 core dependencies and 16 optional dependency groups (50+ total packages). No document records:

- **What capability** each dependency provides
- **Which module(s)** import it
- **Whether it is still actively used** (vs. accumulated over time)
- **What the removal cost** would be
- **Whether a lighter alternative** was considered

This is a supply chain hygiene gap. The 2026-04-08 threat model identified unprompted dependency additions as a high-risk agent attack vector — indistinguishable from legitimate additions without a baseline rationale document. Without this document, a proposed "unprompted dependency gate" cannot enforce the right invariant: a new dependency requires documented rationale, and a dependency lacking rationale is a candidate for removal.

`pip-audit` in CI (FR-187) catches known CVEs but cannot detect:
- Abandoned packages (no maintainer, no CVE yet)
- Ownership-changed packages with no advisory
- Rationale drift (dependency added for FR-X, FR-X removed, dependency remains)
- Scope creep (dependency added for one feature, now imported everywhere)
- Duplicate coverage (e.g., `openai` SDK alongside `langchain-openai`)

CVE scanning and rationale auditing are complementary, not substitutes.

## Proposed Solution

### Phase 1: Rationale Document

Create `docs/dependency-rationale.md` with a table per dependency group. Each entry answers seven questions:

1. **What does it do?** One sentence.
2. **Which files import it?** Grep-verifiable list.
3. **Core or optional?** Whether it belongs in `[project.dependencies]` or `[project.optional-dependencies]`.
4. **When was it added and why?** FR reference if available.
5. **Is it still needed?** Has any refactor made it redundant?
6. **What would removal require?** Impact assessment.
7. **Who maintains it?** Active maintenance status and last release date.

#### Table format per group

```markdown
## Core Dependencies (`[project.dependencies]`)

| Package | Version Pin | Purpose | Used In | Alternatives Considered | Removal Cost | Last Reviewed |
|---------|-------------|---------|---------|------------------------|--------------|---------------|
| langgraph | >=0.2.0 | Core pipeline orchestration — StateGraph, compiled graphs | graph_loader.py, node_factory/ | LangChain LCEL (no checkpointing), raw asyncio (no state mgmt) | High — core framework | 2026-04-09 |
```

### Phase 2: Enforcement Hook

Add a pre-commit hook: when `pyproject.toml` is in staged files, require that `docs/dependency-rationale.md` is also in staged files, unconditionally.

This ensures any dependency change is documented at the boundary where external packages enter.

```yaml
# .pre-commit-config.yaml addition
- repo: local
  hooks:
    - id: dep-rationale-check
      name: dependency rationale check
      entry: bash -c 'if git diff --cached --name-only | grep -q "^pyproject.toml$"; then if ! git diff --cached --name-only | grep -q "^docs/dependency-rationale.md$"; then echo "ERROR: pyproject.toml modified without updating docs/dependency-rationale.md"; exit 1; fi; fi'
      language: system
      pass_filenames: false
      always_run: true
      stages: [pre-commit]
```

**Why unconditional (not OR with changelog fragment):** A changelog fragment documents a user-facing change; it does not document supply chain rationale. The existing `changelog-required` hook already enforces changelog fragments for `feat`/`fix` commits independently. These are orthogonal gates; combining them with OR weakens both. See Judgement below.

### Audit Findings

The audit is expected to surface at least one actionable finding. Candidates visible from current `pyproject.toml`:

- **`replicate` group** contains `langchain-litellm`, not `replicate` — naming mismatch
- **`openai` SDK** in `[rag]` alongside `langchain-openai` in core — potential duplicate
- **`langsmith`** in core deps — verify whether it is imported in production code or only used when tracing is enabled (could be optional)

Each finding must be documented in the rationale table with a recommendation (keep, move, remove, rename).

## Acceptance Criteria

- [ ] `docs/dependency-rationale.md` created covering all packages in `[project.dependencies]` (11 packages)
- [ ] `docs/dependency-rationale.md` covers all 16 optional dependency groups
- [ ] Each entry answers the 7 questions listed above (grep-verifiable import lists)
- [ ] At least one audit finding documented with recommendation (unused, misplaced, duplicated, or misnamed)
- [ ] Pre-commit hook `dep-rationale-check` added: `pyproject.toml` changes unconditionally require a `docs/dependency-rationale.md` update in the same commit
- [ ] Tests: unit test for hook logic (staged `pyproject.toml` without rationale update → fail; with update → pass)
- [ ] Documentation updated: `CLAUDE.md` mentions `docs/dependency-rationale.md` as canonical dependency reference

## Alternatives Considered

1. **Inline comments in `pyproject.toml`**: TOML supports `#` comments, but they are lost on tooling roundtrips (e.g., `pip-compile`, dependency update bots). A separate document is more durable and supports richer content (tables, links, alternatives).

2. **Automated import scanning only** (e.g., `pipreqs`): Detects unused imports but cannot capture rationale, alternatives considered, or removal cost. Complements the rationale document but doesn't replace it.

3. **Dependabot/Renovate configuration**: These tools manage version updates and security patches but do not audit rationale or detect scope creep. Orthogonal concern.

4. **Extend `changelog-required` hook to `chore` commits**: Would force changelog entries for non-user-visible `pyproject.toml` changes (e.g., version pin bumps). The `dep-rationale-check` hook is more targeted: it specifically requires documentation of *what changed and why* rather than a user-facing changelog entry.

5. **CI-only enforcement**: Running the check only in CI delays feedback to PR time. The pre-commit hook catches it locally at commit time, consistent with other boundary enforcement hooks in this project (`changelog-required`, `req-coverage-strict`).

6. **OR-logic (changelog OR rationale update)**: Originally proposed but rejected during Judgement. A changelog fragment documents a user-facing change, not supply chain rationale. An engineer could add a dependency, write a changelog entry, and pass the hook without ever updating the rationale doc — exactly the gap this FR closes. See Judgement.

## Judgement — APPROVED (2026-04-09)

**Verdict:** APPROVE. Scope is frozen.

**Assessment:**

1. **Scope:** Clear and minimal. Two phases (rationale document + enforcement hook) are tightly coupled — the hook enforces updates to the document. Neither is useful without the other. Single responsibility confirmed.

2. **Acceptance criteria:** All 7 criteria are measurable and verifiable. Package counts (11 core, 16 optional groups) match `pyproject.toml`. Hook test criterion is precise.

3. **Feasibility:** Hook follows the established `changelog-required` pattern (`.pre-commit-config.yaml` line 214). Implementation is straightforward. 1.5-day estimate is realistic for auditing 50+ packages.

4. **Architecture alignment:** Enforces at the commit boundary where external packages enter — consistent with The One Law ("normalize at the boundary where external data enters"). Complements FR-187 (`pip-audit` for CVEs) without overlap.

5. **AND-logic (not OR):** The hook requires `docs/dependency-rationale.md` to be staged whenever `pyproject.toml` is staged, unconditionally. This is correct — changelog fragments and rationale documentation serve different purposes. The existing `changelog-required` hook handles changelog enforcement independently. These are orthogonal gates that must not be weakened by OR-combination.

**Authority granted to implement.**

## Related

- FR-187: CI Dependency Security Scan (`pip-audit`) — complementary CVE scanning
- FR-218: Import-Linter Architectural Boundary Enforcement — related boundary enforcement pattern
- 2026-04-08 threat model: unprompted dependency injection as agent attack vector
- `.pre-commit-config.yaml` line 214–219: existing `changelog-required` hook pattern
- `.github/workflows/security.yml`: `pip-audit` CI gate
- `pyproject.toml`: 11 core deps, 16 optional groups
