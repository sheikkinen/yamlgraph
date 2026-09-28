# Feature Request: FR-1129 Planning skill — state the operations, not the effort

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Requested:** 2026-09-28
**First consumer / first event:** the sibling session that files the
LangGraph-issues census FR (I1, 2026-09-28) writes its `## Planned
Operations` section with this skill before its judge run; the operator
later compares that section with what the session actually did.
**Research:** [FR-1129.research.md](FR-1129.research.md)
**Prior art:** [FR-746](FR-746-ideal-result-slot.md) — added the
Ideal Result section; this FR adds the operations the path back consists
of. FR-853 (`is_this_a_graph` moment) — a question the skill asks at
planning time, unchanged. FR-965 (`map_reduce_the_corpus`) — the census
cost line becomes a planned operation, unchanged doctrine. FR-1022 (judge
round sentinel) — precedent for a countable record; this FR records plans,
does not count rounds. FR-452 (`examples/demos/planner`) — a generic
planning graph demo, not an FR planning artifact. FR-096 (FR template demo
plan) — template content, different field. Research row "fr-planner
graph": phantom, no such graph exists (see research record header).
No REJECTED FR found for FR planning or effort fields
(`ls feature-requests | grep -iE 'plan|operation|effort|estimat'`).

## Summary

Add a `planning` skill that tells FR authors to write a `## Planned
Operations` section — probes, branch points, delegations, waits, and the
audit-visible commands the work will run — and remove the `**Effort:** X
days` field from the FR template, which measurement shows carries no
information.

## Value Statement

The operator and reviewers can see, before work starts, what a session
will actually do (which sole routes, which subagents, which census over
how many items), and can compare it with the audit record afterwards.

## Problem

`feature-requests/TEMPLATE.md` line 6 forces `**Effort:** X days` on every
FR. Measured 2026-09-28 over 92 FRs numbered 900+: median estimate 4.0 h,
median active time 1.29 h, ratio median 0.24, 21 % within 2x, Pearson
correlation 0.09; 40 of 92 estimates are exactly "0.5 day". Wall-clock
span (median 7.4 h) is dominated by waits no estimate names. Nothing in
`scripts/`, `yamlgraph/`, `.github/hooks/` or `tests/` parses the field.

Meanwhile the operations the work consists of are already recorded after
the fact (`.github/hooks/logs/audit.jsonl`: `scripts/judge.sh` 109,
`scripts/research.sh` 63, `scripts/author.sh` 45, `scripts/review.sh` 35,
`runSubagent` 61 occurrences) but never stated in advance. In a dry run
(I1 census), writing the operations list first surfaced three blockers
before any code: the brief prompt is governed (`author.sh`), the GitHub
search API cap is below the population, and the census cost estimate is
due first.

## Ideal Result

Every new FR states, before judgement, the concrete operations its
enforcement will run and where it may branch or wait; the standard
pipeline is referenced, not retyped; no duration number appears; and at
completion the FR's implementation status says which planned operations
happened, which did not, and which unplanned ones did.

## Proposed Solution

1. **New skill** `.github/skills/planning/SKILL.md` (front matter `name`,
   `description`, `argument-hint`, like the other 16 skills). Content:
   - When: after Ideal Result, before Proposed Solution is frozen; again
     before handing a task to a sibling session or subagent.
   - The section contract (below), the rule "no durations; counts and
     named waits only", and the post-completion reconciliation paragraph.
   - One worked sample: the I1 LangGraph-issues census plan.
   - Scope sentence: `feature-request` owns the FR lifecycle; `planning`
     owns only the `## Planned Operations` section.
2. **Template change** in `feature-requests/TEMPLATE.md` **and** its
   byte-exact mirror `ramp/assets/tier2/feature-requests/TEMPLATE.md`
   (`ramp/manifest.yaml` `mirror_exact`, FR-865): delete the `**Effort:**`
   line; add a `## Planned Operations` section after `## Ideal Result`
   with a one-line pointer to the skill. The inline template copy in
   `.github/skills/feature-request/SKILL.md` gets the same change
   (`partial_remediation`).
3. **Witness test** asserting: the template (both copies) carries no
   `**Effort:**` line and carries a `## Planned Operations` heading; the
   skill file exists with the three front-matter keys; the skill's sample
   block is parseable YAML with the keys `probes`, `branches`,
   `delegations`, `waits`, `commands`, and contains no duration token
   (`\b\d+(\.\d+)?\s*(min|h|hours?|days?|weeks?)\b`).

Section contract:

```yaml
# ## Planned Operations — standard pipeline is implicit:
#   research.sh → FR → judge.sh → RED/GREEN → review.sh → merge → diary
probes:        # command or read, and what the answer decides
  - "gh api repos/langchain-ai/langgraph --jq .open_issues_count  # decides discover strategy"
branches:      # condition → consequence
  - "10 raw samples do not fit the category draft → back to plan"
delegations:   # route, count, item count
  - "census: corpus_census, 1 run, ~7.5k items, cheap tier"
  - "author.sh: 1 run (brief prompt + schema)"
waits:         # named, never timed
  - "judge rounds (1–2)"
  - "CI"
  - "human merge decision"
commands:      # audit-visible strings a reconciler can grep later
  - scripts/judge.sh
  - scripts/author.sh
  - scripts/review.sh
```

Existing FRs are not rewritten; their `Effort:` lines stay as history.

## Planned Operations

```yaml
probes:
  - "grep the repo for code parsing Effort:  # done: none"
  - "ramp/manifest.yaml mirror_exact for TEMPLATE.md  # done: yes, mirror required"
branches:
  - "judge demands a deterministic reconciler in scope → split to a follow-up FR, not this PR"
delegations:
  - "research.sh: 1 run (done, azure override)"
  - "judge.sh: 1–2 runs"
  - "outsider.sh + review.sh: 1 run each"
waits:
  - "judge"
  - "CI"
  - "human merge decision"
commands:
  - scripts/research.sh
  - scripts/judge.sh
  - scripts/outsider.sh
  - scripts/review.sh
```

## Acceptance Criteria

- [ ] AC-1: `.github/skills/planning/SKILL.md` exists with `name: planning`,
      `description`, `argument-hint`, the section contract, the no-duration
      rule, the reconciliation paragraph, and the I1 worked sample.
- [ ] AC-2: `feature-requests/TEMPLATE.md` and
      `ramp/assets/tier2/feature-requests/TEMPLATE.md` are byte-identical,
      have no `**Effort:**` line, and have a `## Planned Operations` section
      directly after `## Ideal Result`.
- [ ] AC-3: `.github/skills/feature-request/SKILL.md` inline template has
      no `**Effort:**` line and names the planning skill.
- [ ] AC-4: witness test (RED committed before GREEN) covers AC-1..AC-3,
      including the YAML-parse and no-duration-token checks on the sample;
      tagged with a new REQ ID; `python scripts/req_coverage.py --strict`
      passes.
- [ ] AC-5: changelog fragment in `changelog/unreleased/`; diary entry.
- [ ] AC-6: this FR's own implementation status reconciles its
      `## Planned Operations` against what ran.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Keep `Effort:`, add operations alongside | Refused: keeps a field measured at r=0.09 and asks authors for both |
| Deterministic reconciler script over `audit.jsonl` in this FR | Deferred to a follow-up FR: one concern per PR; needs session↔FR mapping design; first consumer is I1's completion |
| FR-planning graph (research row, yamlgraph_native) | Refused: the precedent it cites does not exist; the section is short prose/YAML an author writes, no LLM stage needed |
| External audit-planning checklist (research row, librarian) | Adopted in spirit: plan states scope and steps, evidence reconciles afterwards; no external tool |
| Remove `effort-risk` column from research artifacts | Out of scope: it rates risk, is part of the research contract (FR-890), and is not a duration field |

## Related

- `feature-requests/research-briefs/planning-operations-list.md`
- `feature-requests/TEMPLATE.md`, `ramp/manifest.yaml`
- `.github/skills/feature-request/SKILL.md`
- `docs-planning/plan-test-mutator.md` (a plan already listing stages and owners)
