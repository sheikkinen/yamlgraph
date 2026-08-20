# Feature Request: FR-827 gitclaw — Forkable Issue-to-Feature Cron Runner

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged 2026-08-20 APPROVED WITH REVISIONS
(`FR-827-gitclaw-forkable-runner.judgement.md`) — R-1..R-6 folded
2026-08-20 — READY FOR ENFORCEMENT (C-1 satisfied)
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

Fork gitclaw, create one fine-grained PAT, paste it as a secret. The
pre-shipped horoscope feature proves the cron lane on day one:
`outputs/<date>-horoscope.md` lands without touching anything. Then
file an issue — e.g. "daily haiku about the weather in Oulu" — and the
pipeline plans, judges, enforces, reviews, and pushes
`features/haiku/` with FR + judgement + review + authoring-report
artifacts as provenance; next morning its output joins the cron
commit. The human touched: fork button, PAT page, one issue form.
*(R-3 fold: horoscope is PRE-SHIPPED and proves cron; a separate
canned issue proves issue-to-feature generation.)*

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
│   └── horoscope/             # PRE-SHIPPED cron fixture (R-3: proves the
│       ├── graph.yaml         #  cron lane; issue-to-feature generation is
│       └── prompts/           #  proven by a separate canned issue)
├── scripts/
│   └── author.sh              # gitclaw-local executable authoring route
│                              #  (R-2: writes authoring-report.md; lint +
│                              #   smoke evidence per generated feature)
├── outputs/                   # cron results, committed back
├── state/
│   └── issues.jsonl           # intake ledger (frozen state machine, R-5)
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
                # authors features/<name>/graph.yaml + prompts VIA THE
                # GITCLAW-LOCAL EXECUTABLE ROUTE scripts/author.sh
                # (R-2 fold: vendored adapter writing
                # authoring-report.md; lint + smoke evidence committed
                # under the feature's provenance dir — doctrine prose
                # alone is not a route)
  review:       # copilot/cli — FRESH session; reviews diff against FR
                # + judgement per review-pr skill; verdict routes:
                # REJECTED → one remediation lap back to enforce, then
                # hard fail with review.md posted to the issue
  contain:      # tool_call — DIFF CONTAINMENT GATE (R-4 fold): fail
                # closed unless every changed path is in the run's
                # allowlist (features/<name>/**, provenance artifacts,
                # feature registry, state/issues.jsonl). Refuses
                # .github/workflows/**, .github/skills/**, dependency
                # manifests, secret config, any out-of-feature path.
  push:         # tool_call — git add with EXPLICIT path arguments
                # (never broad add), commit
                # "feat(gitclaw): #<issue> <name>", push; register
                # feature in cron manifest; comment on issue with
                # commit SHA + file links; close issue
```

Conditional edges mirror deviant-daily: every stage's failure commits
a ledger transition before exiting non-zero, so reruns resume.

### Frozen state machines (R-5 fold)

**Intake ledger** (`state/issues.jsonl`, one JSONL line per
transition, committed BEFORE the next external side effect — the
FR-826 shape):

```
seen → planned → judged_approved | judged_rejected
judged_approved → enforced → reviewed_approved | reviewed_rejected
reviewed_rejected → enforced (exactly one remediation lap)
              → reviewed_rejected_final (fail closed, review.md posted)
reviewed_approved → pushed → closed
any stage → failed_recovery_required (side effect done, record lost)
```

Rerun action per state: terminal states (`closed`,
`judged_rejected`, `reviewed_rejected_final`) → idempotent exit;
non-terminal → resume at the next stage; `failed_recovery_required`
→ hard stop, human recovers. Replay of a processed issue event never
starts a second pipeline.

**Cron runner** (per-feature, in the run log + structured output
record): `running → succeeded | failed_recorded`; `failed_recorded`
writes a structured failure output and CONTINUES to the next feature
— one poisoned feature must not starve the rest.

### Trigger and trust boundary

`intake.yml` fires on `issues: [opened, labeled]` but the gate is a
**job-level `if:`** — `on: issues` workflows always run in the trusted
context with secrets (unlike fork PRs), so this condition is the ONLY
barrier between anonymous input and the LLM + PAT; it must evaluate
before any step executes:

- `opened`: `github.event.issue.author_association` ∈
  `OWNER|MEMBER|COLLABORATOR`. **Never `CONTRIBUTOR`** — that
  association is granted to anyone with one merged commit and, on
  forks, to upstream committers in shared history.
- `labeled`: `github.event.label.name == 'gitclaw'` AND
  `github.event.sender` is the trusted party (owner login or
  write-permission check). **Label presence alone is insufficient**:
  issue forms can auto-apply labels (`labels:` in template YAML), so
  an anon issue can arrive pre-labeled; the gate verifies WHO applied
  the label, not that it exists. Corollary: gitclaw must never ship
  an issue template that auto-applies `gitclaw`.

Issue bodies are untrusted input crossing the instruction boundary —
on a public fork, anyone can file an issue, and the body flows into
copilot prompts. Restricting to owner-authored/owner-labeled issues
is the minimum viable injection defense; the README states this
explicitly. Concurrency group serializes intake runs (single-writer
ledger, the FR-826 shape).

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
**This must be spiked FIRST** (AC-01). **R-1 fold:** if headless CLI
auth proves impossible, enforcement STOPS — there is no silent
`backend: api` fallback, because FR-383's API mode cannot author
files, run tools, or resume sessions; the agentic enforce stage is
architecturally CLI-only. A redesign (api-mode reasoning for
plan/judge/review plus a separate specified artifact-materialization
mechanism for enforce) would change the core architecture and must
re-enter judgement as a revised FR.

### Secrets (README PAT instructions)

| Secret | Purpose | Scope |
|--------|---------|-------|
| `GH_PAT` | push, issue comment/close, cron commit-back | fine-grained, this repo only: contents RW, issues RW |
| Copilot auth | copilot CLI on runner | PAT owner's Copilot subscription (or `ANTHROPIC_API_KEY` on the api fallback) |

README walks through: fork → enable workflows (if GitHub requires the
extra click on forks — R-6: documented, not hidden) →
Settings→Secrets → PAT creation (fine-grained, single-repo, minimal
scopes) → watch the first cron horoscope land → file the canned
haiku issue → watch Actions → see the commit.

### Skills vendoring

`.github/skills/` is a snapshot copied from yamlgraph at a recorded
SHA (`SNAPSHOT.md`), pruned to the four contracts the pipeline
consumes. No submodule, no fetch-at-runtime — forks must work with
zero references back to the mothership. Drift is accepted and
re-snapshotted deliberately.

## Implementation Status

**2026-08-20 — AC-01 spike GREEN (first attempt).** Repo
`sheikkinen/gitclaw` created (public); spike workflow
`spike-copilot-cli.yml` on plain `ubuntu-latest`, run ID
**32317560089**, conclusion `success`. Findings:

- Install: `npm install -g @github/copilot` via setup-node@v4
  (node 22) — clean.
- Auth: `COPILOT_GITHUB_TOKEN` env var (documented in
  `copilot help environment` as taking precedence over stored
  credentials) — secret `COPILOT_CLI_TOKEN` holds a gh OAuth token of
  the Copilot-subscribed owner, set via
  `gh auth token | gh secret set` (value never displayed or logged).
- Prompt round-trip: `copilot --silent -p ...` returned exactly
  `GITCLAW-SPIKE-OK`; log line
  `copilot output: GITCLAW-SPIKE-OK` at 00:30:51Z.
- Pre-spike local control: same auth path with clean `COPILOT_HOME`
  (no stored creds) green locally — token is the sole credential.
- C-3 gate: PASSED — no api fallback needed; CLI backend confirmed
  viable on runners. Auto-update is disabled by default in CI (CLI
  detects `CI` env) — pin-friendly.

## Acceptance Criteria

*(Replaced wholesale by the judgement's revised list — R-1..R-6 folds.)*

- [x] AC-01: A headless-runner Copilot CLI spike completes before
      other implementation work: workflow log records install, auth
      method, one successful prompt, and non-secret evidence. If CLI
      auth fails, enforcement stops unless a revised FR is judged.
- [ ] AC-02: Public `sheikkinen/gitclaw` exists outside this
      repository, is marked as a template, and is not committed here
      as a nested repo, submodule, vendored directory, archive, or
      generated artifact.
- [ ] AC-03: The skills snapshot exists with `SNAPSHOT.md` recording
      yamlgraph source SHA and the exact vendored contract files;
      graph-authoring is backed by an executable gitclaw-local
      route/report contract, not only prose.
- [ ] AC-04: `gitclaw.yaml` passes `yamlgraph graph lint`; graph
      inspection proves judge and review start fresh sessions and
      enforce resumes the plan session only when CLI backend is
      active.
- [ ] AC-05: Intake trust gate is a job-level `if` running before any
      step: non-owner issue without trusted-sender `gitclaw` label
      exits skipped, records no feature, and has a witnessed skipped
      Actions run. Gate rejects `CONTRIBUTOR` association and
      template-auto-applied labels (sender check on `labeled`
      events); no issue template auto-applies `gitclaw`.
- [ ] AC-06: Issue body is rendered only inside a fenced user-request
      block in copilot prompts; a prompt-injection fixture attempting
      to modify workflow/skills/secrets files is rejected by the diff
      containment gate before commit.
- [ ] AC-07: Intake ledger state machine is tested for replay after
      success and interruption before/after plan, judge, enforce,
      review, push, issue comment, and issue close; no replay starts
      a second independent pipeline for the same issue.
- [ ] AC-08: Rejected judgement path closes or comments on the issue
      with rationale, commits the rejection ledger transition, and
      registers no cron feature.
- [ ] AC-09: Rejected review path permits exactly one remediation lap
      back to enforce; the second rejected review fails closed with
      `review.md` posted or linked and no push of generated feature
      code.
- [ ] AC-10: Generated diff containment allowlist is enforced before
      push; push uses explicit path arguments and refuses
      `.github/workflows/**`, `.github/skills/**`, dependency
      manifests, secret configuration, and paths outside the current
      feature/provenance/state allowlist.
- [ ] AC-11: The horoscope fixture model is consistent: pre-shipped
      horoscope proves cron; a separate canned issue proves feature
      generation (Option A chosen, R-3).
- [ ] AC-12: The issue-to-feature witness on the canonical repo
      records issue URL, Actions run ID, generated feature path,
      FR/judgement/review artifacts, commit SHA, issue close/comment
      link, and no secrets in committed/logged output.
- [ ] AC-13: Cron workflow runs all registered features, commits
      `outputs/<date>-<name>.md` for successes, writes structured
      failure records for failures, and continues past a poisoned
      feature fixture.
- [ ] AC-14: Fork/template witness proves the documented adopter path
      with only documented manual steps and records fork/template
      repo URL, run IDs, generated commit SHA, closed issue link, and
      cron output; README is corrected if any extra manual step is
      required.
- [ ] AC-15: README contains complete fork/template, Actions
      enablement if required, PAT/secret scopes, issue-label trust
      model, Copilot CLI/auth spike limitations, API-fallback
      limitations, and cron best-effort cadence.
- [ ] AC-16: Secret scan and run-log inspection prove no secret value
      appears in commits, outputs, issue comments, ledgers, workflow
      logs, or uploaded artifacts.
- [ ] AC-17: FR-827 records implementation status with repo URL,
      fork/template witness, run IDs, snapshot SHA, authoring
      reports, scope deviations, and diary entry.

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

## Judgement gates (C-1..C-7, frozen 2026-08-20)

- C-1 authority active only now that R-1..R-6 are folded (this
  revision). C-2 never re-run the judge during enforcement. C-3 CLI
  auth failure = hard stop, no silent api swap. C-4 every generated
  graph/prompt needs lint + smoke evidence from the executable
  authoring route. C-5 diff containment gate before every push,
  fail closed. C-6 gitclaw never vendored into yamlgraph. C-7 core
  changes / new node types / broader permissions → separate judged
  FR.

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
