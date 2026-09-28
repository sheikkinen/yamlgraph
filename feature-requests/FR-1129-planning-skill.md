# Feature Request: FR-1129 Planned Operations — state the work, not the effort

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** In Progress (judged APPROVED WITH REVISIONS, R-1..R-5 folded)
**Requested:** 2026-09-28
**First consumer / first event:** the sibling session that files the
LangGraph-issues census FR (I1, 2026-09-28) writes its `## Planned
Operations` section from the `feature-request` skill before its judge
run; the operator later compares that section with what the session did.
**Research:** [FR-1129.research.md](FR-1129.research.md)
**Evidence:** [FR-1129-evidence.md](FR-1129-evidence.md)
**Judgement:** [FR-1129-planning-skill.judgement.md](FR-1129-planning-skill.judgement.md)
**Prior art:**
[FR-746](FR-746-ideal-result-slot.md) — added the Ideal Result section;
this FR adds the operations the path back consists of.
[FR-853](FR-853-agent-instrument-registry.md) — `is_this_a_graph` moment;
the plan names the graph, doctrine unchanged.
[FR-965](FR-965-graduate-map-reduce-corpus-cure.md) — census cost first;
becomes a planned operation, doctrine unchanged.
[FR-1022](FR-1022-judge-round-sentinel.md) — countable judge record; this
FR records plans, counts nothing mechanically.
[FR-452](FR-452-standalone-planner-demo.md) — generic planner graph demo,
not an FR planning artifact.
[FR-096](FR-096-fr-template-demo-plan.md) — template demo-plan content, a
different field.
Retrieval hits (research record): FR-578 (plot-modeller L7 affect
assignment), FR-514 (dm-v2 carry-forward floor) and FR-587 (plot-modeller
L5 snapshot-then-diff) are story-engine FRs sharing only the nouns
"operations"/"list" — dismissed, `false_duplicate`; FR-845 (gitclaw
generic skill executor) runs skills at graph runtime, does not shape FR
planning — dismissed; FR-291 (watcher FSM action wiring) wires runtime
actions, not planned work — dismissed. Research row "fr-planner graph":
phantom, no such graph exists. No REJECTED FR concerns FR planning or
effort fields (`ls feature-requests | grep -iE 'plan|operation|effort|estimat'`).

## Summary

Replace the FR template's `**Effort:** X days` field with a `## Planned
Operations` section (probes, branch points, delegations, waits,
audit-visible commands), and document how to write and later manually
reconcile it in the existing `feature-request` skill.

## Value Statement

The operator and reviewers can see, before work starts, what a session
will actually do, and compare it by hand with the recorded outcome at
completion.

## Problem

`feature-requests/TEMPLATE.md` forces `**Effort:** X days` on every FR;
nothing in `scripts/`, `yamlgraph/`, `.github/hooks/` or `tests/` parses
it (evidence §3). Committed measurement ([FR-1129-evidence.md](FR-1129-evidence.md) §1,
92 FRs numbered 900+): estimate vs. commit-activity correlation 0.09;
active/estimate ratio median 0.24; 40 of 92 estimates are exactly
"0.5 day". Wall-clock span is dominated by waits no estimate names.

The operations the work consists of are recorded after the fact in the
local hook audit log (evidence §2) but never stated in advance. In a dry
run (I1 census), writing the operations list first surfaced three
blockers before any code: the brief prompt is governed (`author.sh`), the
GitHub search API cap is below the population, and the census cost
estimate is due first.

## Ideal Result

Every new FR states, before judgement, the concrete operations its
enforcement will run and where it may branch or wait; the standard
pipeline is referenced, not retyped; no duration number appears; and at
completion the FR carries an operator-readable table of which planned
operations ran, did not run, or changed — each with a witness — plus any
unplanned operations.

## Proposed Solution

1. **Template** `feature-requests/TEMPLATE.md` and its byte-exact mirror
   `ramp/assets/tier2/feature-requests/TEMPLATE.md` (`ramp/manifest.yaml`
   `mirror_exact`): delete the `**Effort:**` line; add `## Planned
   Operations` directly after `## Ideal Result`, pointing to the
   `feature-request` skill.
2. **Skill** `.github/skills/feature-request/SKILL.md` (no new skill,
   R-1): Plan step gains the operations contract; the inline template
   loses `**Effort:**` and gains the section; a new section documents
   the five-key contract, the no-duration rule, the marked I1 sample, and
   the completion reconciliation schema.
3. **Witness test** `tests/unit/test_fr1129_planned_operations.py`
   (REQ-YG-716, CAP-293).

Operations contract — a single fenced YAML block with exactly these keys,
each a non-empty list of strings:

| Key | Content |
|---|---|
| `probes` | command or read, and what its answer decides |
| `branches` | condition → consequence |
| `delegations` | route, run count, item count (subagent, sibling session, census, sole-route adapter) |
| `waits` | named wait states, never timed |
| `commands` | audit-visible command strings a reader can grep later |

No numeric duration: a number followed by a millisecond-through-year unit
or common abbreviation (`ms`, `s`, `sec`, `min`, `h`, `hr`, `d`, `wk`,
`mo`, `yr` …) is forbidden, case-insensitive. Counts and named waits are
allowed.

Completion reconciliation (manual, R-2) — in the FR's implementation
status:

```markdown
| Planned operation | Outcome (ran / did not run / changed) | Witness |
|---|---|---|

**Unplanned operations:** None
```

A witness is an audit-log match, a commit SHA, a CI run, or a named human
decision; a row without one is not reconciled. Reconciliation cutoff:
plan and table end at enforcement completion; push CI, outsider, review
and merge happen after the head that would record them and are recorded
by the PR, never planned in the FR. FR-1129 delivers this
manual record only — an automated audit-log reconciler is not authorized
and must re-enter the pipeline as its own FR after session-to-FR mapping
is designed.

Existing FRs keep their historical `Effort:` lines.

## Planned Operations

```yaml
probes:
  - "grep scripts, yamlgraph, hooks, tests for code parsing Effort: — decides whether removal needs a code change (done: none)"
  - "ramp/manifest.yaml mirror_exact for TEMPLATE.md — decides whether the ramp copy changes too (done: yes)"
  - "origin/main + remote branches for highest CAP and REQ ids — decides allocation (done: CAP-293, REQ-YG-716 free)"
branches:
  - "judge demands an automated reconciler → separate FR, not this PR (judged: deferred)"
  - "ID collision at push → renumber per repo memory rule"
delegations:
  - "research.sh: 1 run (done, azure override; anthropic 401)"
  - "judge.sh: 1 run (done), second only if folding is disputed"
waits:
  - "judge"
commands:
  - scripts/research.sh
  - scripts/judge.sh
```

## Acceptance Criteria

- [ ] AC-01: `feature-requests/TEMPLATE.md` has no `**Effort:**` line and has `## Planned Operations` directly after `## Ideal Result`, with one line directing authors to the `feature-request` skill.
- [ ] AC-02: `ramp/assets/tier2/feature-requests/TEMPLATE.md` is byte-identical to `feature-requests/TEMPLATE.md`; the existing ramp mirror-exact test passes.
- [ ] AC-03: `.github/skills/feature-request/SKILL.md` updates its Plan step and inline template, defines the five-key contract, forbids numeric durations while allowing counts and named waits, contains the uniquely marked I1 sample, and defines the completion table plus `Unplanned operations` contract.
- [ ] AC-04: No `.github/skills/planning/` skill exists.
- [ ] AC-05: The I1 sample extracts as exactly one YAML document with exactly `probes`, `branches`, `delegations`, `waits`, `commands`; every value is a non-empty list of strings; no numeric duration with a millisecond-through-year unit or common abbreviation appears, case-insensitively.
- [ ] AC-06: `tests/unit/test_fr1129_planned_operations.py` witnesses AC-01..AC-05 and the reconciliation schema, every test marked `REQ-YG-716`, committed RED before GREEN.
- [ ] AC-07: `capabilities/CAP-293-fr-planned-operations.yaml` declares REQ-YG-716; `ARCHITECTURE.md` regenerated; `python scripts/req_coverage.py --strict` and capability validation pass.
- [ ] AC-08: Every retrieval hit in the research record has a disposition above.
- [ ] AC-09: Every quantitative claim in Problem is reproducible from [FR-1129-evidence.md](FR-1129-evidence.md).
- [ ] AC-10: Changelog fragment exists; diary entry with `**Seed:**`.
- [ ] AC-11: Implementation status reconciles every planned operation with outcome and witness, and lists unplanned operations or `None`.
- [ ] AC-12: Historical FR `Effort:` lines, the research `effort-risk` column, and every not-authorized surface in the judgement have no diff.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Standalone `planning` skill (original proposal) | Refused at judgement (R-1): `feature-request` already owns "planning a feature"; a second skill for one FR section duplicates routing |
| Keep `Effort:`, add operations alongside | Refused: keeps a field measured at r=0.09 and asks for both |
| Automated reconciler over `audit.jsonl` | Deferred to a follow-up FR (R-2): needs session↔FR mapping design; first consumer is I1's completion |
| FR-planning graph (research row, yamlgraph_native) | Refused: cited precedent does not exist; no LLM stage needed for a short authored section |
| External audit-planning checklist (research row, librarian) | Adopted in spirit: plan states steps, evidence reconciles afterwards |
| Remove research `effort-risk` column | Out of scope: a risk rating inside the FR-890 contract, not a duration field |

## Deviations

- File slug stays `FR-1129-planning-skill.md` so the adjacent
  `.judgement.md` (FR-1022 round counting) keeps its pairing; the title
  carries the R-1 rename.
- The RED test's inline-template extractor split at the first `## `
  heading, which lies inside the fenced template; GREEN corrected it to
  extract the fenced `markdown` block. Mutation probe after the fix
  (Effort line + "2 days" injected into the skill) turned exactly the
  two targeted tests red.
- Review round 2 (post-judgement): the contract as judged required
  reconciling review and merge from committed witnesses, which cannot
  exist at the reviewed head. Added a reconciliation cutoff at
  enforcement completion; outsider, review, push CI and merge were removed
  from this FR's plan and from the skill sample, and CAP-293 now owns the
  witness test (judgement R-5(2)). Outsider, review and merge outcomes are
  on PR #739.

## Implementation Status

**Status:** Implemented — D-1..D-9 delivered; awaiting human merge
decision.

| Planned operation | Outcome (ran / did not run / changed) | Witness |
|---|---|---|
| probe: code parsing `Effort:` | ran — no reader found | `FR-1129-evidence.md` §3: scoped `git grep` command and verbatim output (a fixture's data line, an unrelated class name) |
| probe: ramp `mirror_exact` | ran — mirror required | `test_ramp_installer.py` passes on GREEN commit `03a0c354` |
| probe: free CAP/REQ ids | ran — CAP-293 / REQ-YG-716 | RED commit `a7f674e5` |
| branch: automated reconciler | ran — deferred by judgement R-2 | `FR-1129-planning-skill.judgement.md` |
| branch: ID collision at push | did not run — no collision | audit-log match: pre-push `git grep ... origin/main -- capabilities/` returned no CAP-293+/REQ-YG-716+; branch push of `03a0c354` |
| research.sh: 1 run | ran (azure override) | commit `300197ef` (`FR-1129.research.md`) |
| judge.sh: 1 run | ran — 1 run, no second | commit `ef28bbcd` (judgement) |
| waits: judge | ran | commit `ef28bbcd` |

**Unplanned operations:**
- prior-art gate (FR-738) refused judgement + evidence files; fixed with pointer `**Prior art:**` lines (commit `ef28bbcd`)
- `ruff format` rewrote the RED test; re-staged (commit `a7f674e5`)
- capability validation required `fr:` in CAP-293 (commit `a7f674e5`)
- PreToolUse guard refused pytest `| tail`; re-run via log file (audit log)
- witness-test extractor fix (see Deviations)
- `test_no_duplicate_fr_numbers` refused `FR-1129.evidence.md`; renamed to the accepted sibling slug `FR-1129-evidence.md` (GREEN commit `03a0c354`)
- PR body glossary edit after the outsider report (PR #739 edit history)
- review round 1 refused pending D-8 rows (commit `48252248` filled them); review round 2 refused the self-referential review/merge rows and CAP-293's missing test ownership — fixed by the reconciliation cutoff (RED `d9a61ba4`, GREEN `30eb37a2`)
- review round 3 refused CI/merge wait examples in the skill rules and an unsupported parser-probe witness — cutoff extended to push CI and wait examples (RED `ea76ecdd`, GREEN `424eba96`), probe recorded as evidence §3
- review round 4: deleting the skill's key table and no-duration rule left the suite green; added `test_skill_states_the_five_key_contract` and `test_skill_states_the_no_duration_rule`. No RED commit was possible, because the product text was already correct. The proof is the same deletion mutation: exactly those two tests fail (2 failed, 23 passed), and the suite is green on restore.

## Related

- `feature-requests/research-briefs/planning-operations-list.md`
- `feature-requests/TEMPLATE.md`, `ramp/manifest.yaml`
- `.github/skills/feature-request/SKILL.md`
- `docs-planning/plan-test-mutator.md`
