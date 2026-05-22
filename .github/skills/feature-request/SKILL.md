---
name: feature-request
description: "Create and manage YAMLGraph feature requests. Use when: writing a feature request, planning a feature, following the plan-judge-enforce workflow, submitting a proposal to the chaplain inbox, understanding the FR lifecycle, or writing acceptance criteria."
argument-hint: "'new', 'template', or FR-XXX number"
---

# Feature Request Workflow

Create, judge, and enforce feature requests. Sources: `feature-requests/TEMPLATE.md`, the Scripture (copilot-instructions.md).

## The Sermon: Plan → Judge → Enforce

1. **Research** — Let agents explore; distill into constraints. Cheapest code is unwritten code.
2. **Plan** — Write FR in `feature-requests/FR-XXX-name.md`. Define objectives, constraints, acceptance criteria.
3. **Judge** — Critically examine the FR. Resolve contradictions, eliminate ambiguity. If clear and minimal, freeze scope.
4. **Enforce** — Write failing test first. Make smallest sufficient change. Update FR with decisions.
5. **Purge** — Remove invented interfaces, speculative flags. If not required and not tested, delete.
6. **Submit** — Bump. Commit. Push. Release. Tag.
7. **Distill** — Add diary entry to `docs/diary/`. Name the trap or insight. Plant a Seed.

## FR Template

```markdown
# Feature Request: [Title]

**Priority:** LOW | MEDIUM | HIGH
**Type:** Feature | Bug | Enhancement
**Status:** Proposed
**Effort:** X days
**Requested:** YYYY-MM-DD

## Summary
Brief description.

## Value Statement
Who benefits and how (one sentence).

## Problem
What problem does this solve?

## Proposed Solution
How should it work? Include code examples.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Tests added
- [ ] Documentation updated

## Alternatives Considered
What other approaches were considered?

## Related
- Links to issues, PRs, files
```

## Status Lifecycle

`Proposed` → `Judged` → `In Progress` → `Completed` (or `Rejected`)

## Submitting to Chaplain

### Local Submission

Write to `.chaplain/inbox/`:

```bash
cat > .chaplain/inbox/refactor-state-builder.md << 'EOF'
Problem: State builder has grown to 450 lines.
Task: Split into state_builder.py and state_reducer.py.
EOF
```

### Remote Submission

Open a GitHub Issue with the `chaplain` label. The runtime imports it automatically.

## Conventions

- **Naming:** `FR-XXX-kebab-case-name.md` in `feature-requests/`
- **Commits:** `feat(scope): FR-XXX summary` (Conventional Commits)
- **Changelog:** Create fragment in `changelog/unreleased/` for feat/fix PRs
- **Diary:** Required for feat/fix PRs with FR reference
- **TDD:** RED commit (failing test, SKIP=pytest) then GREEN commit (fix) — separately
- **Multi-line commits:** Write to `tmp/msg.txt`, use `git commit -F tmp/msg.txt`

## Acceptance Criteria Patterns

Good criteria are:
- **Testable** — can be verified by a test or command
- **Specific** — no ambiguous language ("should work well")
- **Scoped** — tied to the FR, not aspirational

```markdown
- [ ] `yamlgraph graph lint` detects missing edges (E301)
- [ ] Unit test covers empty graph case
- [ ] Changelog fragment in `changelog/unreleased/`
```

## Requirement Traceability

Every test must link to a requirement:

```python
@pytest.mark.req("REQ-YG-XXX")
def test_feature():
    ...
```

When adding a new capability: add requirement to `ARCHITECTURE.md`, extend `scripts/req_coverage.py`, tag tests.

```bash
python scripts/req_coverage.py --strict    # Verify coverage
```

## Related Files

| File | Purpose |
|------|---------|
| `feature-requests/TEMPLATE.md` | FR template |
| `feature-requests/FR-*.md` | All feature requests |
| `ARCHITECTURE.md` | Requirements registry |
| `capabilities/CAP-*.yaml` | Capability specs |
| `scripts/req_coverage.py` | Requirement coverage checker |
| `.chaplain/inbox/` | Chaplain proposal inbox |
