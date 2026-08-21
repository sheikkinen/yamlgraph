# Feature Request: FR-847 Cron Schedules One YAMLGraph Task

**Priority:** HIGH
**Type:** Removal / responsibility correction
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-08-20
**Depends on:** FR-845
**First consumer / first event:** A GitClaw template owner configures one graph
path and sees the scheduled workflow execute the same `yamlgraph graph run`
command they can run manually from the repository checkout.

**Prior art:** FR-827 introduced a small daily runner, but FR-835 expanded it
into a multi-feature composition DAG and process supervisor; FR-836 added output
compatibility parsing. Those mechanisms served the abandoned Oulu composition
arc and are not required by the basic template. FR-819 proves GitHub schedule
and manual dispatch, but its application owns digest state/output. The
call-me-maybe skill is the clearest responsibility precedent: it invokes
`yamlgraph graph run graphs/outcaller.yaml ...`; the outcaller graph owns the
phone call and structured response. FR-845 retained cron unchanged only to keep
its semantic-executor replacement single-purpose; FR-847 is the separately
judged subtraction.

## Summary

Reduce GitClaw scheduled execution to one responsibility:

> Cron schedules one YAMLGraph task.

Delete `tools/cron_run.py`, its multi-feature composition/process tests, output
attribution/commit machinery, and automatic feature discovery. Configure one
graph path and invoke it directly from `.github/workflows/cron.yml` with
`yamlgraph graph run`.

The YAMLGraph task is independently runnable using the exact same command. The
task—not cron—owns its outputs and effects: phone calls, emails, files,
database/state changes, structured results, or other domain behavior.

## Value Statement

GitClaw demonstrates scheduling without becoming a second YAMLGraph runtime:
one workflow line starts one graph, while task behavior remains testable and
runnable outside GitHub Actions.

## Problem

The current “cron implementation” is not cron:

- `.github/workflows/cron.yml`: 50 lines;
- `tools/cron_run.py`: 439 lines;
- focused cron tests: 563 lines;
- total: 1,052 lines.

`cron_run.py` currently contains:

1. strict composition-manifest parsing and filesystem safety;
2. legacy/candidate state-output coercion;
3. bounded subprocess and descendant-process supervision;
4. graph discovery, DAG validation, cycle detection, topological scheduling,
   result caching, and source envelopes;
5. Markdown/failure file rendering and attribution; and
6. continue-past-failure accounting.

These are runtime, composition, compatibility, and publication concerns. A cron
scheduler needs one line: start the configured task at the configured time.

The abstraction also reverses ownership. GitClaw parses arbitrary graph state
to decide what the task “output” was, then writes and commits a Markdown file.
That makes every graph conform to a GitClaw-specific wrapper. YAMLGraph tasks
already know their intended output and side effect. Outcaller makes a phone
call; a digest writes/publishes a digest; an exporter writes an artifact. Cron
should not reinterpret any of them.

## Ideal Result

GitClaw has one scheduled workflow with a schedule trigger and manual dispatch.
It installs YAMLGraph and runs one configured graph using one direct command.
The README shows the identical local command. Running locally or from cron
produces the same task-owned effects and artifacts. GitClaw contains no Python
cron runner, graph discovery, composition scheduler, state-output parser,
output formatter, or output commit step.

## Proposed Solution

### 1. Exact scheduler contract

`.github/workflows/cron.yml` retains:

- `schedule` at `0 6 * * *`;
- `workflow_dispatch`;
- `permissions: contents: read`;
- `actions/checkout@v4` with `persist-credentials: false`;
- Python 3.12 setup; and
- `pip install yamlgraph`.

The workflow removes `permissions: contents: write`, git identity setup,
`git add`, `git commit`, `git push`, and generic output/failure publication.
The basic scheduler receives no generic repository write credential.

It defines one repository-configurable task path:

```yaml
env:
  YAMLGRAPH_TASK: ${{ vars.YAMLGRAPH_TASK }}
```

The workflow fails before execution if `YAMLGRAPH_TASK` is empty, absolute,
contains traversal, is not a tracked regular `.yaml` file, or is a symlink.
Validation is a short shell precondition, not a new Python scheduler.

The execution step is exactly:

```bash
yamlgraph graph run "$YAMLGRAPH_TASK" --full
```

No generic `date` variable is injected. Task inputs belong to the task: it may
derive current time itself, use prompt/tool configuration, or be wrapped by a
task-specific script if its domain genuinely requires arguments. The scheduler
does not invent a universal task schema.

### 2. Independent execution

README documents:

```bash
YAMLGRAPH_TASK=path/to/graph.yaml
yamlgraph graph run "$YAMLGRAPH_TASK" --full
```

That command must run from a normal checkout without GitHub event context. The
scheduled workflow invokes the same command. GitHub Actions is one trigger, not
the task runtime API.

The deterministic validation fixture is the existing tracked regular graph
`features/horoscope/graph.yaml`. Enforcement sets `YAMLGRAPH_TASK` to that path
for both the local and workflow-equivalent run. If that file is absent,
untracked, symlinked, or no longer a regular YAML graph at enforcement time,
stop for replanning; this FR does not authorize creating or modifying a graph
or prompt artifact.

### 3. Task-owned output

The scheduled task owns all observable behavior and output contracts.

Examples:

- **Call Me Maybe / outcaller:** the command runs `graphs/outcaller.yaml`; the
  graph places the call and returns structured answers. Cron would merely decide
  when to place it.
- **Digest task:** the graph/tools fetch, deduplicate, format, and write/publish
  the digest. Cron does not parse graph state into Markdown.
- **File/export task:** the graph/tool writes the declared target artifact. Cron
  does not add attribution or infer filenames.

If a task needs committed output, Git commit/push is part of that task's
explicit side-effect contract or a separately composed Git publication action.
It is not silently built into every scheduled task.

If YAMLGraph reports task failure incorrectly (for example, process exit zero
while state contains a pipeline error), that is a YAMLGraph CLI/runtime defect
and must be fixed in YAMLGraph. GitClaw must not maintain a parallel state
interpreter to compensate.

### 4. Mandatory deletion

Delete in the same reviewed change:

- `tools/cron_run.py`;
- `tests/test_cron_run.py`;
- `tests/test_cron_run_process.py`;
- cron-specific extraction/composition/output tests in other modules;
- workflow output commit and failure-surfacing steps;
- generic repository write permission and persisted checkout credentials;
- multi-feature discovery and `composition.json` scheduling support from the
  basic GitClaw template; and
- README claims that cron runs and commits every accepted feature.

Do not preserve the old runner as fallback. FR-835/836 remain historical
evidence and candidate design input for a separately named advanced composition
runner only if a current consumer is identified in a later FR.

### 5. Exact change surface

Authorized in `sheikkinen/gitclaw`:

- `.github/workflows/cron.yml`;
- deletion of `tools/cron_run.py`;
- deletion/reduction of cron-specific tests;
- README scheduled-task setup and responsibility documentation; and
- focused workflow contract tests using standard-library text/YAML-safe checks.

The focused workflow tests mechanically assert:

1. schedule remains `0 6 * * *` and `workflow_dispatch` remains present;
2. task-path validation occurs before every `yamlgraph` invocation;
3. empty, absolute, traversal, missing, untracked, directory, symlink, and
  non-`.yaml` paths fail before execution;
4. exactly one tracked regular relative `.yaml` path is accepted;
5. the only execution command is
  `yamlgraph graph run "$YAMLGRAPH_TASK" --full`;
6. `python -m tools.cron_run`, `--json`, `--var date=`, `source_snapshots`,
  output-state parsing, feature-glob scheduling, `git add`, `git commit`, and
  `git push` are absent; and
7. the README local command is byte-for-byte the workflow execution command
  after assigning `YAMLGRAPH_TASK`.

Not authorized:

- generic issue executor, command parser, publisher, control bundle, skills,
  hooks, request/reference handling, or intake workflow;
- YAMLGraph core changes;
- task graph creation or modification;
- output formatting/publication code;
- new secrets, permissions, dependencies, or schedules; or
- Oulu feature work.

## Acceptance Criteria

- [ ] AC-01: RED proves the current cron path runs `python -m tools.cron_run`, discovers multiple feature graphs, interprets graph output state, supports composition scheduling/envelopes, writes rendered output/failure artifacts, and commits outputs instead of only scheduling one configured task
- [ ] AC-02: `.github/workflows/cron.yml` retains the `0 6 * * *` schedule and `workflow_dispatch`
- [ ] AC-03: The workflow defines `YAMLGRAPH_TASK: ${{ vars.YAMLGRAPH_TASK }}` and validates it before execution
- [ ] AC-04: Empty, absolute, traversal, missing, untracked, directory, symlink, and non-`.yaml` task paths fail before `yamlgraph`; exactly one tracked regular relative `.yaml` path is accepted
- [ ] AC-05: The workflow has `permissions: contents: read`, checkout uses `persist-credentials: false`, and no generic git identity, `git add`, `git commit`, `git push`, output commit, or generic failure-publication step remains
- [ ] AC-06: The execution line is exactly `yamlgraph graph run "$YAMLGRAPH_TASK" --full`; there is no wrapper Python, `--json`, universal `date` variable, `source_snapshots`, output parser, feature discovery, or state interpretation
- [ ] AC-07: README documents `YAMLGRAPH_TASK=<path>` followed by `yamlgraph graph run "$YAMLGRAPH_TASK" --full`, byte-for-byte matching the workflow execution command after variable assignment
- [ ] AC-08: Existing tracked `features/horoscope/graph.yaml` runs independently with the documented local command and through workflow-equivalent shell setup; no graph or prompt artifact is created or modified
- [ ] AC-09: `tools/cron_run.py`, its focused tests, multi-feature discovery, composition scheduling, output/failure rendering, attribution footer, state-output compatibility parsing, and output Git commit machinery are absent
- [ ] AC-10: GitClaw generic executor/intake/control-bundle surfaces and YAMLGraph source are unchanged
- [ ] AC-11: Production scheduled-execution code decreases from workflow plus Python runner to workflow-only implementation; final production line count and deleted test count are recorded
- [ ] AC-12: Focused workflow contract tests, the full remaining GitClaw suite, the deterministic fixture run, workflow text/parse checks, and token/secret scans pass with commands or log paths recorded
- [ ] AC-13: A human reviews the destructive workflow/runtime/test deletion diff and validation evidence before push

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-827 | Retain the schedule/dispatch idea; retire application-level runner |
| FR-835 | Historical advanced composition implementation; no current basic-template consumer, removed here |
| FR-836 | Preserve the lesson that tasks need explicit output contracts; YAMLGraph task owns that contract, not cron |
| FR-819 | Reuse GitHub schedule/manual trigger precedent; distinguish application-owned digest output from scheduler responsibility |
| Call-me-maybe skill | Direct precedent: one command starts outcaller graph; graph owns side effect/result |
| FR-845 | Cron was deliberately untouched during executor replacement; FR-847 is the separate responsibility correction |

## Alternatives Considered

- **Split `cron_run.py` into smaller modules:** rejected; improves file size but
  retains the wrong ownership.
- **Keep bounded process supervisor only:** rejected from basic scheduler;
  YAMLGraph CLI owns process/task failure semantics.
- **Keep composition as optional flag in the same workflow:** rejected; basic
  cron would still carry advanced runtime complexity.
- **Commit stdout generically:** rejected; stdout is not every task's domain
  output, as outcaller demonstrates.
- **Inject date universally:** rejected; task inputs are graph-specific.
- **Keep old runner as fallback:** rejected; two scheduler/runtime contracts
  recreate drift.

## Related

- `feature-requests/FR-827-gitclaw-forkable-runner.md`
- `feature-requests/FR-835-gitclaw-composition-boundary.md`
- `feature-requests/FR-836-gitclaw-candidate-output-contract.md`
- `feature-requests/FR-819-github-native-digest-poc-repo.md`
- `feature-requests/FR-845-gitclaw-generic-skill-executor.md`
- `feature-requests/FR-298-marketing-e2e-test-outcaller.md`
- `/Users/sheikki/.copilot/skills/call-me-maybe/SKILL.md`
- `../gitclaw/.github/workflows/cron.yml`
- `../gitclaw/tools/cron_run.py`

## Judgement

**Verdict:** APPROVED WITH REVISIONS — authority activates after R-1 through
R-3 are folded. All revisions are folded in this document.

| # | Finding | Resolution (binding) |
|---|---|---|
| R-1 | Generic scheduler publication was removed but inherited repository write authority was not explicitly forbidden | Require `contents: read`, non-persisted checkout credentials, and removal of all generic git publication steps |
| R-2 | The deterministic fixture was not named while graph changes are forbidden | Fix validation to existing tracked `features/horoscope/graph.yaml`; stop for replanning if unavailable |
| R-3 | Workflow test evidence was underspecified | Freeze the seven exact mechanical assertions in Exact Change Surface and revised ACs |

**Purge list:** `tools/cron_run.py`; its focused tests; multi-feature discovery;
composition scheduling/envelopes; output/failure rendering; attribution footer;
state-output compatibility parsing; generic output Git publication; generic
write permission; persisted checkout credentials; wrapper/fallback variants.

**Scope frozen:** Yes. Deliverables are the simplified read-only cron workflow,
runner/test deletion, focused workflow contract tests, README responsibility
documentation, and recorded line-count/test/validation/human-review evidence.
No graph/prompt, YAMLGraph core, intake/executor/control-bundle, Oulu, secret,
schedule, write-permission, or generic publication change is authorized.

**Enforcement gates:** Do not re-run the judge during enforcement. If the named
fixture needs creation or modification, stop for separately judged graph
authoring. Human review of the destructive deletion diff and validation evidence
is mandatory before push.

### Questions for the human

None.
