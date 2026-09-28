---
name: feature-request
description: "Create and manage YAMLGraph feature requests. Use when: writing a feature request, planning a feature, following the plan-judge-enforce workflow, submitting a proposal to proposals/, understanding the FR lifecycle, or writing acceptance criteria."
argument-hint: "'new', 'template', or FR-XXX number"
---

# Feature Request Workflow

Create, judge, and enforce feature requests. Sources: `feature-requests/TEMPLATE.md`, the Scripture (copilot-instructions.md).

## The Sermon: Plan → Judge → Enforce

1. **Research** — Run `scripts/research.sh <problem-brief.md>` (FR-890 sole route): a closed problem brief fans out to five orthogonal personas; the accepted `tmp/draft-alternatives.md` is promoted to `feature-requests/FR-XXX.research.md`. Cheapest code is unwritten code.
2. **Plan** — Write FR in `feature-requests/FR-XXX-name.md`. Define objectives, constraints, acceptance criteria, first consumer, the `**Research:**` reference, and the `## Planned Operations` block (see [Planned Operations](#planned-operations-fr-1129)).
3. **Judge** — Critically examine the FR. Resolve contradictions, eliminate ambiguity. If clear and minimal, freeze scope. An FR without a committed research reference receives no authority (FR-890, prospective).
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
**Requested:** YYYY-MM-DD
**First consumer / first event:** who uses this first, at what moment
**Research:** [FR-XXX.research.md](FR-XXX.research.md)

## Summary
Brief description.

## Value Statement
Who benefits and how (one sentence).

## Problem
What problem does this solve?

## Ideal Result
The end state; the solution is the minimal path back from it.

## Planned Operations
One fenced YAML block: probes, branches, delegations, waits, commands.

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

## Planned Operations (FR-1129)

State the work, not its duration. `**Effort:**` was removed: across 92
FRs its estimate correlated 0.09 with commit activity
(`feature-requests/FR-1129-evidence.md`). Write one fenced YAML block
with exactly these keys, each a non-empty list of strings:

| Key | Content |
|---|---|
| `probes` | command or read, and what its answer decides |
| `branches` | condition → consequence |
| `delegations` | route, run count, item count (subagent, sibling session, census, sole-route adapter) |
| `waits` | named wait states — never timed |
| `commands` | audit-visible command strings a reader can grep later |

Rules:

- **No numeric duration** — no number followed by a millisecond-through-year
  unit or its abbreviation. Counts ("10 raw issues", "1 run") and named
  waits ("CI", "human merge decision") are the substance.
- **Reference the standard pipeline, don't retype it** — list the
  research/judge/review runs only as delegations with counts; spend the
  lines on what is specific to this FR.
- **Write it before the judge run** — the judge reads it; writing it
  first is what surfaces blockers (a governed prompt, an API cap, a
  census cost estimate due first).

Sample (I1 — LangGraph issues census):

<!-- fr1129-planned-operations-sample:begin -->
```yaml
probes:
  - "grep corpus_census adapters for a gh-issues adapter — absent means RED/GREEN adapter work"
  - "gh api search total_count vs the search cap of 1,000 results — over the cap means list endpoint or date slices"
  - "read 10 raw issues end-to-end before drafting pain categories"
  - "census cost: item count x per-item tokens x cheap-map price, before any smaller alternative"
branches:
  - "10-item smoke rows misclassified → back to plan, revise categories"
  - "rate limit on discover → paged, cached discover keyed on updated_at"
  - "brief prompt or schema is a governed prompts/*.yaml → author.sh route, never manual"
delegations:
  - "research.sh: 1 run"
  - "judge.sh: 1 run, 2 if revisions are disputed"
  - "author.sh: 1 run for the brief prompt and schema"
  - "census: smoke on 10 items, then full population with map cache"
  - "outsider.sh and review.sh: 1 run each"
waits:
  - "judge"
  - "CI"
  - "full census run"
  - "human merge decision"
commands:
  - scripts/research.sh
  - scripts/judge.sh
  - scripts/author.sh
  - yamlgraph graph lint
  - yamlgraph graph run examples/demos/corpus_census/graph.yaml
  - scripts/outsider.sh
  - scripts/review.sh
```
<!-- fr1129-planned-operations-sample:end -->

### Completion reconciliation

At completion, the implementation status carries this table, filled by
hand from witnesses:

```markdown
| Planned operation | Outcome (ran / did not run / changed) | Witness |
|---|---|---|

**Unplanned operations:** None
```

A witness is an audit-log match (`.github/hooks/logs/audit.jsonl`), a
commit SHA, a CI run, or a named human decision; a row without one is not
reconciled. List every operation that ran without being planned, or write
`None`. Automated reconciliation is not part of this contract.

## Research Evidence (FR-890)

Every FR created after FR-890 activation must carry a `**Research:**`
header pointing at a COMMITTED record — normally
`feature-requests/FR-XXX.research.md`, the promoted output of the
research sole route:

```bash
scripts/research.sh feature-requests/research-briefs/my-problem.md
# accepted → promote:
cp tmp/draft-alternatives.md feature-requests/FR-XXX.research.md
```

Lifecycle (R-6): the FR author promotes the artifact at FR filing or
amendment time, adding a header with brief filename, run date, and
personas executed. An equivalent committed record (an in-body
dispositioned alternatives table) may be referenced instead. Dangling
or absent references are gate failures — the Judge grants no authority.
The problem brief itself must be closed input: problem statement,
classification enum, constraints, witnessed incidents — no
solution-shaped sections (the preflight rejects them, exit 64).

## Status Lifecycle

`Proposed` → `Judged` → `In Progress` → `Completed` (or `Rejected`)

## Submitting a proposal (spark)

Sparks live in `proposals/` at the repository root. The directory is
git-ignored (root-anchored `/proposals/`) and may not exist on a fresh
checkout, so create it with the write:

```bash
mkdir -p proposals && cat > proposals/refactor-state-builder.md << 'EOF'
Problem: State builder has grown to 450 lines.
Task: Split into state_builder.py and state_reducer.py.
EOF
```

Proposal contents are never committed; the operator triages them into
feature requests. The former chaplain inbox directory no longer exists
(FR-1011) — a write to the old path fails with `ENOENT`, on purpose.

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
| `proposals/` | Proposal (spark) inbox — untracked, root-ignored |
