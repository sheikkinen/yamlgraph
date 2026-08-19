# Feature Request: FR-827 gitclaw — Forkable Issue-to-Feature Cron Runner

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 3 days
**Requested:** 2026-08-20

**First consumer / first event:** a stranger's fork of
`sheikkinen/gitclaw`, the morning after they filed their first issue —
the pipeline planned, judged, enforced, reviewed, and pushed a working
yamlgraph feature, and the cron ran it. Second consumer: the Proclaim
narrative — "fork this repo and issues become running features" is the
strongest agent-first demonstration yet: the entire plan-judge-enforce
doctrine packaged as a forkable GitHub App-shaped repo, no App needed.

**Prior art:** FR-819 [Completed] and FR-826 [Enforced] are the
satellite mold (repo = runtime + state + publication record, cron +
commit-back, idempotency ledger) — inherited wholesale; the one-tree
test (diary 2026-08-19) passes: code, schedule, state, output, audit
all fit one tree. CAP-106 (GitHub-Issues remote inbox) is the nearest
precedent and must be distinguished: it *imports* labeled issues into
the LOCAL chaplain runtime on the operator's machine; gitclaw runs the
entire pipeline ON the Actions runner — no local runtime, which is
what makes it forkable. The chaplain FSM
(`.chaplain/scripts/start-system.sh`, watcher2) is the process
precedent for plan→judge→enforce orchestration; gitclaw is the
chaplain decoupled from the operator's machine. FR-081/FR-383/FR-105
[Completed] own the copilot node (CLI backend, session continuation);
gitclaw composes it, no core changes. `examples/demos/horoscope`
[exists] is the acceptance-feature precedent. The skills doctrine
contracts (`.github/skills/feature-request`, `judge-fr`, `review-pr`,
`graph-authoring`) are the instruction payload — vendored as a
snapshot, not referenced (forks must be self-contained).

## Summary

A public template repo `sheikkinen/gitclaw`, intended to be forked.
When a GitHub issue arrives, an Actions workflow runs a yamlgraph
graph whose copilot nodes orchestrate the doctrine: plan → judge →
enforce → review → push. The enforced artifact is itself a yamlgraph
feature (graph + prompts + optional tools) committed under
`features/<name>/`. A second workflow (daily cron) runs every
registered feature and commits outputs back. The repo ships with the
yamlgraph skills snapshot as the copilot nodes' contract, and with one
canned acceptance feature: **horoscope**. The README teaches fork +
PAT creation — the only two manual steps.

## Ideal Result

Fork gitclaw, create one fine-grained PAT, paste it as a secret, file
an issue: "daily horoscope for Aries in the style of a weather
report." Tomorrow morning the fork contains
`features/horoscope/graph.yaml` (planned, judged, enforced, reviewed
by the pipeline, with FR + judgement + review artifacts committed as
provenance) and `outputs/2026-08-21-horoscope.md` (the cron ran it).
The human touched: fork button, PAT page, one issue form.

## Value Statement

Anyone with a GitHub account and a Copilot subscription gets a
self-extending automation repo — the plan-judge-enforce doctrine as a
product, not a practice.

## Problem

The satellite mold (FR-819/FR-826) proved repo-as-organism, but every
satellite so far was hand-built by the operator's agent sessions. The
chaplain automates the doctrine but is welded to the operator's
machine (local FSM runtime, local worktrees). There is no artifact a
third party can adopt. The mold is a checklist; it should be a
template.

## Proposed Solution

### Repo layout

```
gitclaw/
├── README.md                  # fork + PAT instructions (see below)
├── gitclaw.yaml               # the orchestrator graph (issue → feature)
├── prompts/                   # plan/judge/enforce/review prompt templates
├── .github/
│   ├── skills/                # VENDORED yamlgraph skills snapshot:
│   │   ├── feature-request/   #   (feature-request, judge-fr, review-pr,
│   │   ├── judge-fr/          #    graph-authoring doctrine.md files)
│   │   ├── review-pr/         #   + SNAPSHOT.md recording source SHA
│   │   └── graph-authoring/
│   └── workflows/
│       ├── intake.yml         # on: issues (opened, label 'gitclaw')
│       └── cron.yml           # daily: run all features, commit outputs
├── features/
│   └── horoscope/             # canned acceptance feature (pre-shipped)
│       ├── graph.yaml
│       └── prompts/
├── outputs/                   # cron results, committed back
├── state/
│   └── issues.jsonl           # idempotency ledger: issue# → status
└── tools/                     # thin git/gh helpers for the push node
```

### The orchestrator graph (`gitclaw.yaml`)

Five stages; copilot nodes carry the doctrine, tool_call nodes carry
the side effects:

```yaml
nodes:
  intake:       # tool_call — ledger check (issue already processed → done),
                # write drawn transition (FR-826 idempotency shape)
  plan:         # copilot/cli — writes features/<name>/FR.md per the
                # feature-request skill; session A
  judge:        # copilot/cli — FRESH session (input closure: doctrine
                # forbids judging in the author's session); renders
                # judgement.md; verdict routes: REJECTED → close issue
                # with rationale, END
  enforce:      # copilot/cli — resumes session A (FR-105); TDD:
                # authors features/<name>/graph.yaml + prompts per the
                # graph-authoring skill; runs `yamlgraph graph lint`
                # + smoke as its own gate
  review:       # copilot/cli — FRESH session; reviews diff against FR
                # + judgement per review-pr skill; verdict routes:
                # REJECTED → one remediation lap back to enforce, then
                # hard fail with review.md posted to the issue
  push:         # tool_call — git add features/<name> outputs state,
                # commit "feat(gitclaw): #<issue> <name>", push;
                # register feature in cron manifest; comment on issue
                # with commit SHA + file links; close issue
```

Conditional edges mirror deviant-daily: every stage's failure commits
a ledger transition before exiting non-zero, so reruns resume.

### Trigger and trust boundary

`intake.yml` fires on `issues: [opened, labeled]` but the job runs
ONLY when `github.event.issue.author_association` is `OWNER` or the
issue carries the `gitclaw` label applied by the owner. Issue bodies
are untrusted input crossing the instruction boundary — on a public
fork, anyone can file an issue, and the body flows into copilot
prompts. Restricting to owner-authored/owner-labeled issues is the
minimum viable injection defense; the README states this explicitly.
Concurrency group serializes intake runs (single-writer ledger, the
FR-826 shape).

### Cron runner

`cron.yml` (daily) reads the feature manifest (`features/*/graph.yaml`
glob or an explicit registry file), runs each with
`yamlgraph graph run`, commits `outputs/<date>-<name>.md`. A feature
that fails gets a structured failure record in outputs, not a dead
workflow — one broken feature must not starve the rest.

### Copilot CLI on the runner (the load-bearing risk)

The copilot nodes use `backend: cli`, which requires the `copilot`
CLI on the Actions runner (`npm install -g @github/copilot`) and
authentication tied to a Copilot-subscribed account (the PAT owner).
**This must be spiked FIRST** (AC-01): if CLI auth on a headless
runner proves impossible, fallback is `backend: api` with
`ANTHROPIC_API_KEY` as an alternative secret — the graph is written so
the backend is the only change. The README documents both paths.

### Secrets (README PAT instructions)

| Secret | Purpose | Scope |
|--------|---------|-------|
| `GH_PAT` | push, issue comment/close, cron commit-back | fine-grained, this repo only: contents RW, issues RW |
| Copilot auth | copilot CLI on runner | PAT owner's Copilot subscription (or `ANTHROPIC_API_KEY` on the api fallback) |

README walks through: fork → Settings→Secrets → PAT creation
screenshots-level steps (fine-grained, single-repo, minimal scopes) →
file the canned horoscope issue → watch Actions → see the commit.

### Skills vendoring

`.github/skills/` is a snapshot copied from yamlgraph at a recorded
SHA (`SNAPSHOT.md`), pruned to the four contracts the pipeline
consumes. No submodule, no fetch-at-runtime — forks must work with
zero references back to the mothership. Drift is accepted and
re-snapshotted deliberately.

## Acceptance Criteria

- [ ] AC-01: SPIKE FIRST — copilot CLI authenticates and answers one
      prompt on a plain `ubuntu-latest` runner using only repo
      secrets; findings recorded in this FR before any other work
      (if impossible: `backend: api` fallback recorded and used)
- [ ] AC-02: Repo `sheikkinen/gitclaw` public, marked as template;
      layout as specified; skills snapshot present with SNAPSHOT.md
      recording the yamlgraph source SHA
- [ ] AC-03: `gitclaw.yaml` passes `yamlgraph graph lint`; judge and
      review nodes are fresh sessions (no `resume`), enforce resumes
      plan's session — verified by graph inspection test
- [ ] AC-04: Intake is idempotent: replayed issue event exits via
      ledger without a second pipeline run (unit test + witnessed
      rerun)
- [ ] AC-05: Trust boundary enforced: non-owner issue without the
      `gitclaw` label does not start the pipeline (workflow condition
      witnessed by a run that skips)
- [ ] AC-06: Horoscope acceptance walkthrough green end-to-end on the
      canonical repo: canned issue filed → pipeline commits
      `features/horoscope/` with FR + judgement + review artifacts →
      issue commented and closed with commit SHA (run ID recorded)
- [ ] AC-07: Cron run executes the horoscope feature and commits
      `outputs/<date>-horoscope.md` (run ID recorded)
- [ ] AC-08: A REJECTED judgement closes the issue with rationale and
      commits the ledger transition — witnessed with a deliberately
      unjudgeable issue
- [ ] AC-09: Failure of one feature in cron does not block others
      (test with a poisoned feature fixture)
- [ ] AC-10: README contains complete fork + PAT instructions; a
      fresh-eyes read-through finds no undocumented manual step
      (operator or second session verifies)
- [ ] AC-11: No secret value in any commit, log, output, or issue
      comment (grep + run-log inspection, FR-826 AC-06 pattern)
- [ ] AC-12: FR-827 updated with run IDs, repo URL, snapshot SHA,
      scope deviations; diary entry lands

## Constraints

- New sibling repo (`~/Documents/src/gitclaw`); yamlgraph core
  unchanged — gitclaw composes existing node types only. Any core
  gap discovered → separate FR, not an inline patch (FR-826 C-8
  shape).
- Judge and review copilot nodes MUST NOT resume the author session
  (doctrine input closure). The linter cannot enforce this across a
  satellite; AC-03's inspection test does.
- Issue body is untrusted input (instruction boundary); it reaches
  prompts only inside a fenced "user request" block, and the trust
  gate (AC-05) precedes any LLM call.
- Enforced features are yamlgraph-only artifacts (graph + prompts +
  optional thin tools); the pipeline must reject requests requiring
  new secrets or external side effects beyond commit-back — the
  judge prompt carries this as a standing constraint.
- Actions cron is best-effort (satellite-mold diary); README states
  the cadence honestly.
- Skills snapshot is pruned to the four consumed contracts; no
  chaplain FSM, no hooks — hooks are local enforcement, wrong layer
  for a fork (operator correction 2026-08-20: skills, not hooks).

## Alternatives Considered

- **GitHub App / Probot**: real product surface, but hosting, auth
  churn, and a server — fails the one-tree test that makes this
  forkable.
- **Reuse CAP-106 remote inbox**: requires the operator's local
  runtime; not forkable by construction.
- **Copilot Workspace / Coding Agent assignment**: assigns issues to
  GitHub's own agent — no doctrine (no judge, no review closure), no
  yamlgraph artifact, no cron composition. gitclaw's value IS the
  doctrine.
- **Vendoring yamlgraph itself**: pip install from PyPI suffices; the
  skills are the only artifacts not shipped in the wheel.

## Questions for the human

1. Repo name confirmed `gitclaw`? (assumed yes from the brief)
2. Horoscope output channel: committed `outputs/*.md` only, or also
   posted as an issue comment / GitHub Pages? (planned: commit only —
   cheapest witness; extensions are follow-up FRs)

## Related

- FR-819, FR-826 (satellite mold), CAP-106 (remote inbox,
  distinguished), FR-081/FR-383/FR-105 (copilot node),
  `examples/demos/horoscope`, diary 2026-08-19 (one-tree test),
  `.github/skills/{feature-request,judge-fr,review-pr,graph-authoring}`
