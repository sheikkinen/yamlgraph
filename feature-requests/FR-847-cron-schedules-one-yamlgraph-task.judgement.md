# Judgement: FR-847 Cron Schedules One YAMLGraph Task

**Original verdict (superseded 2026-08-21):** APPROVED WITH REVISIONS — the
subtraction was strategically correct, with R-1 through R-3 folded into the FR.

**Amended verdict:** APPROVED WITH REVISIONS — the responsibility correction,
Oulu weather haiku self-sufficiency, and example pruning are sound. Authority is
active after amended revisions A-1 and A-2 were folded into the FR.

**Reviewed against:** `feature-requests/FR-847-cron-schedules-one-yamlgraph-task.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-827-gitclaw-forkable-runner.md`; `feature-requests/FR-835-gitclaw-composition-boundary.md`; `feature-requests/FR-836-gitclaw-candidate-output-contract.md`; `feature-requests/FR-819-github-native-digest-poc-repo.md`; `feature-requests/FR-845-gitclaw-generic-skill-executor.md`; `feature-requests/FR-298-marketing-e2e-test-outcaller.md`; `/Users/sheikki/.copilot/skills/call-me-maybe/SKILL.md`; `../gitclaw/.github/workflows/cron.yml`; `../gitclaw/tools/cron_run.py`.

**Prior art:** FR-827 schedule/dispatch is retained; FR-835 composition and
FR-836 output compatibility are retired from the basic template; FR-819 remains
the application-owned output precedent; call-me-maybe is the direct one-graph
side-effect precedent; FR-845 deliberately deferred cron to this separate FR.

## Amended Judgement — 2026-08-21

The amended scope exposes the design error in the previous approach: cron
injected `date`, so the supposed task was not independently runnable. The
scheduler must invoke a complete task. The retained haiku graph therefore owns
current-date resolution through deterministic shell tooling, while an optional
`city` variable defaults to `Oulu, Finland`. No scheduler wrapper or Python date
node is justified for `date +%Y-%m-%d`.

The target tree grounds the pruning scope: retain the six tracked files under
`features/haiku/`; delete the six software-craft aphorism files and three
horoscope files. Material haiku graph/prompt changes must use the canonical
graph-authoring adapter and verified authoring report.

### Amended required revisions

| # | Finding | Folded resolution |
|---|---|---|
| A-1 | The direct haiku task still requires a provider credential | Preserve exactly the existing non-write `ANTHROPIC_API_KEY` execution-step mapping; forbid `GH_TOKEN`, write credentials, generic secret forwarding, and new secrets |
| A-2 | “Documented default” could imply a hidden workflow fallback | Call `features/haiku/graph.yaml` the README starter task value; require owners to set `vars.YAMLGRAPH_TASK`; keep empty configuration as a pre-execution failure |

### Amended frozen scope

- Simplify `.github/workflows/cron.yml` to one validated direct
	`yamlgraph graph run "$YAMLGRAPH_TASK" --full` invocation with read-only
	repository permission and only the explicit provider environment.
- Delete `tools/cron_run.py`, focused runner tests, composition/output parsing,
	generic publication machinery, horoscope, and software-craft aphorism.
- Retain only `features/haiku/`; only its graph, prompt, and authoring report may
	change, through the canonical graph-authoring route.
- Make the graph default `city` to `Oulu, Finland`, allow CLI city override,
	resolve `date` with a `type: tool` command exactly `date +%Y-%m-%d`, and pass
	city/date state to the haiku prompt. No `type: python` date node.
- Update README and focused contract tests. Record line/test/example deletion,
	graph lint/run, city override, authoring proof, secret scan, and human review.

Not authorized: YAMLGraph core; generic executor/intake/control bundle; new
examples, secrets, dependencies, schedules, write permission, output
publication, scheduler-provided task variables, wrapper scripts, retained haiku
FR/judgement/review mutation, or semantic expansion beyond optional city and
self-resolved current date.

### Amended enforcement gates

1. Do not re-run the judge during enforcement.
2. Use the canonical authoring adapter for the haiku graph/prompt change.
3. Keep cron repository access read-only and provider environment explicit.
4. Stop for replanning if the exact direct command cannot run the task; do not
	 restore scheduler-owned inputs or a wrapper.
5. Human review of deletion, graph-authoring diff/report, and validation
	 evidence is mandatory before push.

## What is sound

The core responsibility correction is valid. FR-847 names one narrow scheduler contract, "Cron schedules one YAMLGraph task," and explicitly moves task effects back to the task. The current cited implementation is materially larger than that responsibility: the workflow runs `python -m tools.cron_run`, grants content write permission, configures git identity, and commits generated outputs, while `cron_run.py` handles output extraction, process supervision, composition manifests, envelopes, and output files.

The prior-art disposition is sufficient for the direction. FR-835 and FR-836 intentionally built composition/output runtime machinery for a now-abandoned advanced composition arc, while FR-845 explicitly preserved cron unchanged so the executor replacement stayed single-purpose. This FR is the correct separate subtraction.

Strategic classification: **contrib/example template responsibility correction**, not a YAMLGraph framework primitive. Existing YAMLGraph CLI execution is the right abstraction: the call-me-maybe precedent invokes one graph directly and lets the graph own the side effect and structured response.

## Required revisions

### R-1: Remove generic scheduler write authority

Fold into the Proposed Solution, Exact Change Surface, and Acceptance Criteria that the basic cron workflow must not retain generic repository write credentials. The workflow must remove `permissions: contents: write`, the git identity step, `git add`, `git commit`, `git push`, and the generic output/failure publication path currently present in the cited workflow. The replacement must set `permissions: contents: read` and configure `actions/checkout@v4` with `persist-credentials: false`.

This is required because FR-847 says task-owned output and committed output belong to the explicit task contract, not silently to every scheduled task, but the current FR only names deletion of commit/failure steps and does not freeze removal of the inherited write credential. A scheduler that no longer publishes generic outputs must not keep a generic publisher token.

### R-2: Name the deterministic fixture graph

Fold an exact existing tracked fixture path into the FR for AC-06. Use the existing GitClaw fixture graph, expected to be `features/horoscope/graph.yaml` from FR-827's pre-shipped cron fixture contract. The enforcement tests must set `YAMLGRAPH_TASK` to that path for the local and workflow-equivalent run.

If the canonical GitClaw repository no longer contains that tracked regular YAML file at enforcement time, enforcement must stop for replanning rather than creating or editing a graph under this FR. FR-847 currently requires a deterministic fixture graph run while also forbidding task graph creation or modification; the fixture must therefore be named up front.

### R-3: Make the workflow contract tests exact

Replace broad validation prose with exact contract tests. The focused workflow tests must assert all of the following mechanically:

1. the workflow keeps `schedule` at `0 6 * * *` and `workflow_dispatch`;
2. the validation step occurs before any `yamlgraph` invocation;
3. empty, absolute, traversal, missing, untracked, directory, symlink, and non-`.yaml` task paths fail before execution;
4. one tracked regular relative `.yaml` path is accepted;
5. the only execution command is `yamlgraph graph run "$YAMLGRAPH_TASK" --full`;
6. there is no `python -m tools.cron_run`, `--json`, `--var date=`, `source_snapshots`, output-state parsing, feature glob scheduling, `git add`, `git commit`, or `git push`; and
7. the README local command is byte-for-byte the workflow execution command after assigning `YAMLGRAPH_TASK`.

The FR already points toward these checks, but AC-11's "workflow parse" and "secret scan" language is too broad for an enforcer to know what evidence satisfies the gate. Fold the exact assertions above so failing tests can be written directly.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `../gitclaw/.github/workflows/cron.yml` simplified to one validated direct YAMLGraph task invocation |
| D-2 | Delete `../gitclaw/tools/cron_run.py` |
| D-3 | Delete or reduce cron-specific tests, including `../gitclaw/tests/test_cron_run.py` and `../gitclaw/tests/test_cron_run_process.py`, replacing only with focused workflow contract tests |
| D-4 | `../gitclaw/README.md` scheduled-task setup and task-owned-output documentation |
| D-5 | Enforcement evidence recording line-count reduction, deleted test count, commands/logs, and human review |

Not authorized: generic issue executor, command parser, publisher, control bundle, skills, hooks, request/reference handling, intake workflow, YAMLGraph core, task graph creation or modification, prompt creation or modification, output formatting/publication code, new secrets, new schedules, new write permissions, Oulu feature work, composition-runner fallback, state-output compatibility parser, or preservation of `tools/cron_run.py` under another name.

## Revised acceptance criteria

- [ ] AC-01: RED proves the current cron path runs `python -m tools.cron_run`, discovers multiple feature graphs, interprets graph output state, supports composition scheduling/envelopes, writes rendered output/failure artifacts, and commits outputs instead of only scheduling one configured task.
- [ ] AC-02: `.github/workflows/cron.yml` retains the `0 6 * * *` schedule and `workflow_dispatch`.
- [ ] AC-03: The workflow defines `YAMLGRAPH_TASK: ${{ vars.YAMLGRAPH_TASK }}` and validates it before execution.
- [ ] AC-04: Empty, absolute, traversal, missing, untracked, directory, symlink, and non-`.yaml` task paths fail before `yamlgraph`; exactly one tracked regular relative `.yaml` path is accepted.
- [ ] AC-05: The workflow has `permissions: contents: read`, checkout uses `persist-credentials: false`, and no generic git identity, `git add`, `git commit`, `git push`, output commit, or generic failure-publication step remains.
- [ ] AC-06: The execution line is exactly `yamlgraph graph run "$YAMLGRAPH_TASK" --full`; there is no wrapper Python, `--json`, universal `date` variable, `source_snapshots`, output parser, feature discovery, or state interpretation.
- [ ] AC-07: README documents `YAMLGRAPH_TASK=<path>` followed by `yamlgraph graph run "$YAMLGRAPH_TASK" --full`, byte-for-byte matching the workflow execution command after variable assignment.
- [ ] AC-08: The FR names the existing tracked deterministic fixture graph used for validation; that fixture runs independently with the documented local command and through workflow-equivalent shell setup; no graph or prompt artifact is created or modified.
- [ ] AC-09: `tools/cron_run.py`, its focused tests, multi-feature discovery, composition scheduling, output/failure rendering, attribution footer, state-output compatibility parsing, and output Git commit machinery are absent.
- [ ] AC-10: GitClaw generic executor/intake/control-bundle surfaces and YAMLGraph source are unchanged.
- [ ] AC-11: Production scheduled-execution code decreases from workflow plus Python runner to workflow-only implementation; final production line count and deleted test count are recorded.
- [ ] AC-12: Focused workflow contract tests, the full remaining GitClaw suite, the deterministic fixture run, workflow text/parse checks, and token/secret scans pass with commands or log paths recorded.
- [ ] AC-13: A human reviews the destructive workflow/runtime/test deletion diff and validation evidence before push.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-3 must be folded into FR-847 before implementation authority activates. | GATE |
| C-2 | Do not invoke or re-run the judge during enforcement. | GATE |
| C-3 | Do not create or materially modify any `graph.yaml` or `prompts/*.yaml` artifact under this FR; if that becomes necessary, stop for a separately judged graph-authoring scope. | GATE |
| C-4 | Do not retain generic repository write credentials in the basic cron scheduler. Any commit/push behavior must be task-specific and outside this FR. | GATE |
| C-5 | Do not modify YAMLGraph core, GitClaw intake/executor/control-bundle surfaces, Oulu features, secrets, schedules, or generic publication code. | GATE |
| C-6 | Human review of the destructive deletion diff and validation evidence is mandatory before push. | GATE |

Authority granted: after R-1 through R-3 are folded, the enforcer may simplify GitClaw cron to validate one configured tracked YAML graph and run exactly `yamlgraph graph run "$YAMLGRAPH_TASK" --full`, while deleting the old cron runner and generic publication machinery.
