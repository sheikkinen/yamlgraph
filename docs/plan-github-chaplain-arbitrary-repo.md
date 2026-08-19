# Plan: GitHub Process Channel — Plan+Judge for Arbitrary Repos

**Date:** 2026-08-18
**Origin:** `docs/research-agent-channels-2026-08-18.md` §1 — the process
channel needs the pipeline to produce and judge an FR for a repo that is
not yamlgraph. Prior art: FR-243 (issue intake), watcher2 (PR flows),
`scripts/judge.sh` + judge graph (`.github/skills/judge-fr/adapters/`),
`scripts/author.sh`, `examples/demos/judge`.

## Ideal Result (stated first, per `ideal_result_backwards`)

A maintainer of any repo adds one workflow file and one label. When anyone
— human or agent — opens an issue labeled `chaplain`, the repo receives:
a PR containing a doctrine-shaped FR, a rendered judgement on that FR, and
an issue comment with the verdict. If GRANTED, the issue is handoff-ready
for any coding agent (GitHub Copilot coding agent, Claude, human) with
frozen scope attached. The maintainer merges or closes; the pipeline never
pushes to a protected branch.

## The scoping decision that makes this tractable

**Enforce does not ship.** Running codegen in a foreign repo is the hard,
dangerous, already-solved-by-others part — GitHub's own coding agents take
issues and produce PRs. What they lack is exactly what plan+judge
produces: a judged, frozen, doctrine-shaped scope. Position the product as
the **front half**: chaplain plans and judges; the target repo's coding
agent of choice enforces; our review contract can follow later as the
back half. This turns the biggest competitor (Copilot coding agent) into
the fulfillment layer.

## Reality check: the current process is agent sessions, not LLM calls

Corrected 2026-08-18 after checking the skills. The actual routes today:

- **Plan** — interactive: an operator chat session following the
  `feature-request` skill. The chaplain's headless equivalent
  (`.chaplain/graphs/watcher-plan/step-plan-unified.yaml`, FR-305) is a
  single `type: copilot, backend: cli` node — a full Copilot CLI agent
  session (`allow_all_tools`, model-pinned `gpt-5.3-codex`) that drafts
  the FR, researches, writes acceptance tests, and runs verify-red in a
  worktree.
- **Judge** — `scripts/judge.sh <fr-path>`: OS lock + lineage sentinel,
  then the adapter graph (`.github/skills/judge-fr/adapters/graph.yaml`)
  — again one `copilot`/`cli` node spawning an agent session
  (`gpt-5.5`, all tools, artifact contract on `tmp/draft-judgement.md`).
  Chaplain variant `step-judge-v2` enforces model independence from plan
  (fresh session, different model — anchoring-bias defense to preserve).

So the *chaplain's* execution substrate is the Copilot CLI agent runtime.
But the portable middle tier already exists (second correction, same
day, after checking examples):

- **`examples/demos/planner` (FR-452)** — standalone FR planner,
  `type: agent` with task-shaped tools (read_file, search, list_dir,
  git_log, write_file). Its README states the design intent verbatim:
  "Mirrors the Chaplain's `step-plan-unified.yaml` but uses `type: agent`
  with shell tools instead of `type: copilot`, making it portable — runs
  in CI, scripts, and cron without the VS Code runtime."
- **`examples/demos/judge` (FR-450)** — standalone judge, `type: agent`
  with read_file/search/list_dir/git_log/run_tests, structured
  `JudgeVerdict` output, 8 Scripture criteria.
- **`examples/demos/judge/eval.sh` (FR-453)** — multi-model judge
  evaluation harness with archived results (haiku, sonnet, opus…) — the
  judge-regression-fixture proposal partially exists here already.

These need only a provider API key: no Copilot entitlement, no VS Code,
no agent-runtime secret. The porting problem is therefore NOT
"re-derive as pure-LLM graphs" — it is generalizing FR-450/452 beyond
yamlgraph's repo layout.

## Architecture: composite action over the FR-450/452 graphs

Option A — composite GitHub Action (`chaplain-action`), pip-installs
yamlgraph, runs the planner and judge agent graphs. Chosen. Option B —
hosted GitHub App: rejected for now (infra, key custody, hides the
dogfooding); it is the metered/monetization form, revisit on install
count.

Tiering, corrected:

**Tier 1 — portable agent graphs (the marketplace product).** The
FR-450/452 graphs, generalized. `type: agent` + bounded tools runs on
any provider the LLM factory supports with function calling. Unlike a
pure-LLM downgrade, this tier keeps evidence probing: the judge still
reads cited files, greps for prior art, checks git history, runs
acceptance tests. The tool set is an allowlist by construction — a
*better* security posture against untrusted issue text than the home
pipeline's `allow_all_tools`.

**Tier 2 — Copilot CLI sessions (home fidelity, opt-in).** The existing
copilot-node graphs for repos that provision an agent-runtime secret.
Deferred — not needed for the barebones or MVP.

Preserve FR-305's plan/judge model-independence rule (different models,
fresh sessions) in the action's two jobs.

## What must be decoupled (the real work)

| Coupling today | Portable form |
|---|---|
| Judge doctrine at `.github/skills/judge-fr/doctrine.md` | Bundle default doctrine + rubric inside the action; target repo may override via `.chaplain/doctrine.md` |
| FR template at `feature-requests/TEMPLATE.md` | Bundle default template; override via `.chaplain/TEMPLATE.md` |
| Repo context (plan graph assumes yamlgraph layout) | Context-pack step: README + file tree + languages + top-level configs, capped at N tokens; no repo-specific assumptions |
| Judge/author scripts assume repo-local paths | Parameterize graph vars: `--var doctrine_path=... --var repo_context=...` |
| FR-450/452 graphs assume yamlgraph layout (Scripture criteria, feature-requests/, pytest in run_tests tool) | Generalize: doctrine/template as vars; run_tests command configurable or omitted for unknown test runners; judge criteria degrade gracefully when repo has no ARCHITECTURE.md / REQ registry |
| Provider keys (`ANTHROPIC_API_KEY`) | BYO provider key as default. ~~GitHub Models zero-secret path~~ — **GitHub Models was retired 2026-07-30** (playground, inference API, BYOK all gone). Minimum-secret alternative: Copilot CLI in the runner authenticated via `COPILOT_GITHUB_TOKEN` = user-owned fine-grained PAT with the "Copilot Requests" permission (officially documented headless auth); bills the adopter's Copilot premium requests and reuses yamlgraph's existing `type: copilot, backend: cli` node — no new provider code |
| `judge.sh` operational guards (OS lock, lineage sentinel, artifact contract) | Lock → workflow concurrency group; sentinel → env var as today; artifact contract unchanged — verify by artifact, never exit code |

The Copilot-PAT route matters strategically: no zero-secret path exists
anymore, but any adopter with a Copilot plan already has credits and
the PAT permission is purpose-built — one secret, no new billing
relationship, no provider code. Precedent that GitHub sanctions LLM
work on Actions runners billed to Copilot: the Copilot coding agent
itself runs there on premium requests.

## Pipeline state machine (labels as FSM)

```
issue + label chaplain
  → chaplain:planning   (action claims issue, idempotency guard)
  → chaplain:planned    (FR PR opened, linked in comment)
  → chaplain:judged     (judgement committed to PR + verdict comment)
  → chaplain:granted | chaplain:rejected
```

One issue = one FR = one PR. Re-labeling a processed issue is a no-op
unless the FR PR was closed. Judge runs in a **separate job** from plan —
input closure by construction (job receives only FR file + doctrine, never
the issue thread or plan-job logs; the never-judge-in-author's-session
rule mapped to CI).

## Security (this is untrusted input by definition)

- Issue body is a prompt-injection surface feeding an LLM with repo write
  paths. Mitigations: PR-only writes (never direct push), `permissions:`
  minimal (`contents: write` scoped to a branch, `issues: write`),
  fork issues honored but PRs always require maintainer
  merge.
- Tier 1 agents have a **bounded, task-shaped tool allowlist**
  (read/search/list/git_log; write_file constrained to the FR path;
  run_tests omitted or command-pinned by the maintainer, never derived
  from issue text). Injection can steer the agent but cannot expand its
  toolbox. Tier 2 (`allow_all_tools`) is deferred; if ever shipped:
  ephemeral runner, no secrets beyond the agent key, explicit opt-in.
- The FR PR diff is only markdown under `feature-requests/` — enforce this
  in the action (path allowlist) so a hijacked plan step cannot write code.
  Defense in depth over the tool constraints: the agent may be steered,
  but only markdown leaves the runner.
- Verdict comment renders LLM output — sanitize @-mentions and links.

## Phases

### Barebones (prove it on a sibling — named first consumer)

`action/` directory in this repo (not yet a marketplace listing):

- `action/action.yml` — composite action: inputs `issue_number`,
  `provider`; steps: checkout, `pip install yamlgraph`, context-pack
  script, run planner graph, run judge graph, open PR, comment verdict.
- `action/graphs/planner.yaml` + `action/graphs/judge.yaml` — copies of
  `examples/demos/planner/graph.yaml` (FR-452) and
  `examples/demos/judge/graph.yaml` (FR-450) with yamlgraph-isms lifted
  to `--var` (doctrine_path, template_path, fr_dir, test_command). The
  demos stay untouched; the action carries its own generalized copies
  until convergence is proven, then dedupe.
- `action/doctrine/` — extracted default judge rubric + FR template.
- `.github/workflows/chaplain.yml` in **ninchat_voice or
  statemachine-engine** — the acceptance test: one real issue → FR PR +
  verdict on a repo that is not yamlgraph.

Exit criterion: a sibling-repo issue produces a judged FR PR with zero
yamlgraph-repo assumptions leaking (grep the FR for yamlgraph-isms).

### MVP (adoptable by strangers)

- Copilot-PAT auth option: document `COPILOT_GITHUB_TOKEN` (fine-grained
  PAT, "Copilot Requests" permission) + Copilot CLI install step as the
  minimum-secret path alongside BYO provider keys. (`github_models`
  provider is dead — service retired 2026-07-30.)
- Label FSM + idempotency + concurrency guard.
- Override points (`.chaplain/doctrine.md`, `.chaplain/TEMPLATE.md`).
- Path-allowlist and permissions hardening as above.
- README for the action written as ad copy (agents and maintainers both
  read it); publish to Actions Marketplace. Harvest: install count +
  issues-processed counter → `data/harvest/ledger.jsonl`.

### Later (explicitly deferred)

- Review-as-action (back half; needs the enforce PR to exist first).
- Hosted GitHub App with metering (the monetization form).
- Copilot-coding-agent auto-assignment on GRANTED (one `gh` call, but
  only after the handoff format is proven manually).

## Open questions (for the FR's judge, not for this doc)

1. Is Copilot-premium-request quality/quota sufficient for judge-grade
   reasoning under a Copilot Pro plan, or is BYO provider key the honest
   default with Copilot-PAT as the low-friction option?
2. Judgement quality on repos with no doctrine: is the bundled default
   rubric meaningful for a repo with zero Scripture, or does the judge
   need a "doctrine-free" mode that judges only internal consistency?
3. One-repo-one-run concurrency: is the FR-243 single-consumer assumption
   safe under GitHub's at-least-once workflow delivery?
4. How much verdict quality does the agent-graph judge (FR-450) lose
   versus the Copilot-session judge? The eval harness already exists
   (`examples/demos/judge/eval.sh`, FR-453, multi-model results
   archived) — extend it with the copilot-route as one more label and
   run the 20-FR fixture. This is the judge-regression-fixture proposal
   (`.chaplain/inbox/judge-regression-fixture.md`) acquiring its second
   consumer and a head start.
5. Can Copilot CLI run headless in Actions at all under current
   licensing (Copilot-entitled PAT)? Only blocks Tier 2, which is
   deferred.

## Next step

This plan is chaplain-inbox-shaped. Submit as proposal
(`.chaplain/inbox/github-chaplain-arbitrary-repo.md`) referencing this
doc — the pipeline should plan and judge its own externalization.
