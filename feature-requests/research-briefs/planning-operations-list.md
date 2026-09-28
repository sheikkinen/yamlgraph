# Problem brief: FR plans carry a fabricated effort number instead of the work that will actually run

**Prior art:** FR-746 (`ideal_result_backwards`; Ideal Result section in the
template); FR-739 (session guillotine: the agent knows what is ongoing and
when it ends); FR-742 (briefing carries diary debt to successors); FR-853
(`is_this_a_graph` moment: name the graph before reaching for
scripts/subagents); FR-965 (`map_reduce_the_corpus`: cost the census first);
FR-1022 (judge round sentinel: a countable record a wrapper can read);
FR-180 (plan-phase ID reservation); FR-096 (FR template demo plan);
`.github/skills/feature-request/SKILL.md` and `feature-requests/TEMPLATE.md`
(line 6: `**Effort:** X days`); `docs-planning/plan-test-mutator.md` (a
planning document that already lists its stages and their owners).

## Problem statement

Every FR template instance asks the author for `**Effort:** X days`. The
number is written before any probe runs and is never reconciled against
what happened. The FR says nothing about the operations the work will
actually consist of — research route runs, judge rounds, `author.sh`
invocations, subagent delegations, census runs, RED/GREEN commits, CI
waits, review, the human merge decision — although those operations are
countable, and the hook audit log already records most of them by command
text.

The consequence is twofold. First, the plan cannot be checked: a reviewer
or a successor session cannot compare "what the FR said would happen"
with "what the session did", so unplanned subagent fan-out, skipped probes,
or a manual route around a sole-route adapter are visible only by reading
the transcript. Second, discoveries that a step list would force early are
made mid-work instead: in a 2026-09-28 dry run, writing the step list for
a GitHub-issues census surfaced three blockers before any code — the brief
prompt is a governed `prompts/*.yaml` artifact (sole route `author.sh`),
the GitHub search API caps results below the target population, and the
census cost estimate belongs before any smaller alternative is offered.

The question: what planning artifact should an FR carry so that the
planned work is stated in advance, is checkable afterwards against the
audit record, and does not reintroduce fabricated duration numbers — and
what should the skill that guides authors say?

## Classification

judgement/analysis/generation

## Constraints

- No duration or effort estimates as a planning output: the measured
  estimate carries no information (see incidents). Counts of operations
  and named wait states are allowed; clock durations are not.
- Must honour existing sole routes: research via `scripts/research.sh`,
  judge via `scripts/judge.sh`, graph/prompt authoring via
  `scripts/author.sh`, review via `scripts/review.sh`. The planning
  artifact describes these runs; it never replaces or wraps them.
- Standard pipeline steps (research, judge, RED/GREEN, review, diary) are
  identical across FRs; an artifact that makes every author retype them is
  ritual (`audit_as_ritual`, `gate_checks_shape_not_substance`).
- The information-carrying part is FR-specific: probes, branch points,
  corpus sizes, delegations, expected waits. The artifact must make that
  part visible, not bury it.
- Must be reconcilable afterwards by a deterministic, LLM-free check
  (`linter-must-stay-llm-free` repo memory) against `.github/hooks/logs/audit.jsonl`
  and git history; a list that is never reconciled is a fabricated
  estimate in a different shape.
- Skills live in `.github/skills/<name>/SKILL.md` with YAML front matter
  (`name`, `description`, `argument-hint`); the repo already has 16
  skills, and `feature-request` owns FR authoring. Overlap must be
  resolved, not duplicated.
- One concern per PR (`mixed_commits_erode_auditability`); the audit
  reconciliation tool, if needed, may be a separate FR.
- Governed paths: main checkout is write-locked (FR-889); all edits in a
  worktree.

## Witnessed incidents

- 2026-09-28 measurement (script output kept at `tmp/fr_effort_vs_actual.txt`
  in the main checkout): 92 FRs numbered 900+ with a parseable
  `**Effort:**` value. Median estimate 4.0 h; median active time 1.29 h
  (sum of inter-commit gaps capped at 45 min, commits whose subject names
  the FR); median wall-clock span 7.4 h. Active/estimate ratio median
  0.24 (p10 0.05, p90 0.75); 21 % within 2x; Pearson correlation between
  estimate and active time 0.09. Estimates are quantised: 40 of 92 are
  exactly 0.5 day, 21 exactly 1 day.
- Examples from the same table: FR-980 estimated 24 h, active 0.94 h;
  FR-959 estimated 12 h, active 3.71 h across a 313.6 h span — the span is
  dominated by waits, which no estimate names.
- 895 FR files carry an `Effort:` line; the template field
  (`feature-requests/TEMPLATE.md` line 6) forces it on every author.
- `.github/hooks/logs/audit.jsonl` (main checkout, 2026-09-28): 65,192
  events over 143 sessions; command-text occurrences — `scripts/judge.sh`
  109, `scripts/research.sh` 63, `scripts/author.sh` 45,
  `scripts/review.sh` 35, `runSubagent` 61. The operations are already
  recorded; nothing states them in advance.
- 2026-09-28 dry run (GitHub-issues census of `langchain-ai/langgraph`,
  7,529 issues+PRs): writing the operations list before any work surfaced
  the `author.sh` route for the brief prompt, the search-API result cap,
  and the census cost estimate. About 60 % of the list was the standard
  pipeline, identical to any FR.
