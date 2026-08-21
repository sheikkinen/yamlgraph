# Feature Request: FR-847 Cron Schedules One YAMLGraph Task

**Priority:** HIGH
**Type:** Removal / responsibility correction
**Status:** Completed 2026-08-21 — enforced in GitClaw at `a01250622f0566b588099c6b72e8bd03ba0eb94c`
**Effort:** 0.5 day
**Requested:** 2026-08-20
**Depends on:** FR-845
**First consumer / first event:** A GitClaw template owner configures one graph
path and sees the scheduled workflow execute the same `yamlgraph graph run`
command they can run manually from the repository checkout.

**Amended:** 2026-08-21 — prune GitClaw's examples to the existing Oulu weather
haiku and use it as the sole scheduled-task witness.

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

Prune GitClaw's three example feature directories to one: retain the existing
`features/haiku/` Oulu weather haiku and delete the horoscope and software-craft
aphorism examples. One task, one example, and one scheduler command demonstrate
the boundary without carrying a catalogue.

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
output formatter, or output commit step. `features/haiku/` is the only retained
example; no horoscope or software-craft aphorism example remains.

## Proposed Solution

### 1. Exact scheduler contract

`.github/workflows/cron.yml` retains:

- `schedule` at `0 4 * * *` (human override during enforcement);
- `workflow_dispatch`;
- `permissions: contents: read`;
- `actions/checkout@v4` with `persist-credentials: false`;
- Python 3.12 setup; and
- `pip install yamlgraph`.

The workflow removes `permissions: contents: write`, git identity setup,
`git add`, `git commit`, `git push`, and generic output/failure publication.
The basic scheduler receives no generic repository write credential.

The direct execution step retains exactly the starter graph's existing
non-write provider mapping:

```yaml
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

It receives no `GH_TOKEN`, generic secret forwarding, new secret, or other
credential. The provider key enables the graph's LLM call; it grants no
repository publication authority.

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
derive current time itself or use prompt/tool configuration. The scheduler does
not invent a universal task schema or call a task-specific wrapper. The fact
that the previous haiku command required cron to pass `date` is the design error
this FR corrects: a scheduled task must be complete before a scheduler invokes
it.

### 2. Independent execution

README documents:

```bash
YAMLGRAPH_TASK=path/to/graph.yaml
yamlgraph graph run "$YAMLGRAPH_TASK" --full
```

That command must run from a normal checkout without GitHub event context. The
scheduled workflow invokes the same command. GitHub Actions is one trigger, not
the task runtime API.

The deterministic validation fixture and documented **starter task value** are
the existing tracked regular graph `features/haiku/graph.yaml`. README instructs
template owners to set the repository variable `YAMLGRAPH_TASK` to that value.
The workflow has no hidden fallback: an empty variable fails before execution.
The graph generates one 5-7-5 haiku about Oulu weather in a dry Finnish stoic
tone. Enforcement sets `YAMLGRAPH_TASK` to that path for both the local and
workflow-equivalent run.

The haiku graph is made self-sufficient through the canonical graph-authoring
route (`scripts/author.sh` and its verified authoring report):

1. top-level graph `variables` defines `city: "Oulu, Finland"` as the default;
2. callers may override it independently with `--var city="Rovaniemi, Finland"`;
3. a deterministic `type: tool` node invokes a named shell tool whose command
  is exactly `date +%Y-%m-%d` and stores stdout in `state.date`;
4. the LLM node receives `city` and the tool-produced `date` from graph state;
5. the prompt describes weather for that city/date and preserves the one-haiku,
  5-7-5, dry Finnish stoicism, no-commentary contract; and
6. the graph's no-argument execution path remains
  `yamlgraph graph run "$YAMLGRAPH_TASK" --full`.

No `type: python` node is added. If future domain behavior needs Python, it must
be a named tool implementation referenced by the graph, never scheduler or
inline orchestration. Current-date resolution is trivial shell tooling and does
not justify Python.

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
- README claims that cron runs and commits every accepted feature;
- all 6 tracked files under
  `features/daily-aphorism-about-software-craft/`; and
- all 3 tracked files under `features/horoscope/`.

Retain only the 6 tracked files under `features/haiku/`: its FR, judgement,
authoring report, review, graph, and prompt. Only `graph.yaml`,
`prompts/haiku.yaml`, and `authoring-report.md` may change, and only through the
canonical graph-authoring route. Do not rename or supplement the directory.
Pruning the other examples is deletion-only.

Do not preserve the old runner as fallback. FR-835/836 remain historical
evidence and candidate design input for a separately named advanced composition
runner only if a current consumer is identified in a later FR.

### 5. Exact change surface

Authorized in `sheikkinen/gitclaw`:

- `.github/workflows/cron.yml`;
- deletion of `tools/cron_run.py`;
- deletion/reduction of cron-specific tests;
- deletion of `features/daily-aphorism-about-software-craft/` and
  `features/horoscope/`;
- canonical authoring-route modification of `features/haiku/graph.yaml`,
  `features/haiku/prompts/haiku.yaml`, and its authoring report so the task owns
  current-date resolution and optional city configuration;
- README scheduled-task setup and responsibility documentation; and
- focused workflow contract tests using standard-library text/YAML-safe checks.

The focused workflow tests mechanically assert:

1. schedule is `0 4 * * *` and `workflow_dispatch` remains present;
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
- task graph creation outside the canonical graph-authoring route;
- modification of retained `features/haiku/FR.md`, `judgement.md`, or
  `review.md`;
- creation of replacement/example feature directories;
- scheduler-provided `date`/`city`, task wrapper scripts, inline Python, or a
  `type: python` node for date resolution;
- output formatting/publication code;
- generic secret forwarding, new secrets, permissions, dependencies, or
  schedules; or
- semantic expansion beyond optional city plus self-resolved current date.

## Acceptance Criteria

- [x] AC-01: RED proves the current cron path runs `python -m tools.cron_run`, discovers multiple feature graphs, interprets graph output state, supports composition scheduling/envelopes, writes rendered output/failure artifacts, and commits outputs instead of only scheduling one configured task
- [x] AC-02: `.github/workflows/cron.yml` uses the human-approved `0 4 * * *` schedule and retains `workflow_dispatch`
- [x] AC-03: The workflow defines `YAMLGRAPH_TASK: ${{ vars.YAMLGRAPH_TASK }}` and validates it before execution
- [x] AC-04: Empty, absolute, traversal, missing, untracked, directory, symlink, and non-`.yaml` task paths fail before `yamlgraph`; exactly one tracked regular relative `.yaml` path is accepted
- [x] AC-05: The workflow has `permissions: contents: read`, checkout uses `persist-credentials: false`, and no generic git identity, `git add`, `git commit`, `git push`, output commit, or generic failure-publication step remains
- [x] AC-06: The execution line is exactly `yamlgraph graph run "$YAMLGRAPH_TASK" --full`; there is no wrapper, `--json`, scheduler-provided `date`/`city`, `source_snapshots`, output parser, feature discovery, or state interpretation
- [x] AC-07: The execution step exposes only `ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}` for the starter graph; no `GH_TOKEN`, generic secret forwarding, new secret, or write-capable credential is introduced
- [x] AC-08: README documents setting the repository variable to starter value `YAMLGRAPH_TASK=features/haiku/graph.yaml`, with no workflow fallback, followed by `yamlgraph graph run "$YAMLGRAPH_TASK" --full`; the local execution command byte-for-byte matches the workflow command
- [x] AC-09: `features/haiku/graph.yaml` is authored through the canonical adapter, defaults `city` to `Oulu, Finland`, permits CLI city override, resolves `date` through a `type: tool` shell command exactly `date +%Y-%m-%d`, passes city/date state to the haiku prompt, contains no `type: python`, and runs independently with the exact no-argument scheduler command
- [x] AC-10: `features/haiku/` is the sole remaining example feature directory; all 6 tracked software-craft aphorism files and all 3 tracked horoscope files are deleted; no replacement example or graph/prompt change outside AC-09 is introduced
- [x] AC-11: `tools/cron_run.py`, its focused tests, multi-feature discovery, composition scheduling, output/failure rendering, attribution footer, state-output compatibility parsing, and output Git commit machinery are absent
- [x] AC-12: GitClaw generic executor/intake/control-bundle surfaces and YAMLGraph source are unchanged
- [x] AC-13: Production scheduled-execution code decreases from workflow plus Python runner to workflow-only implementation; final production line count, deleted cron-test count, and 9 deleted example files are recorded
- [x] AC-14: Focused workflow contract tests, the full remaining GitClaw suite, haiku graph lint, no-argument Oulu run, city-override run, workflow text/parse checks, authoring-report verification, and token/secret scans pass with commands or log paths recorded; unavailable provider credentials are recorded as blocked, not successful
- [x] AC-15: A human reviews the destructive workflow/runtime/test/example deletion diff, graph-authoring diff/report, and validation evidence before push

## Implementation Status — 2026-08-21

Implemented locally in `sheikkinen/gitclaw` with separate TDD commits:

- RED `f8af6f1`: 11 focused contract failures against the old scheduler/runtime;
- GREEN `6714fd0`: one-task workflow, self-sufficient haiku, README update,
  runner/test/example deletion, and obsolete-test purge;
- follow-up `a012506`: align README's documented run time with the human-
  approved 04:00 UTC schedule and add its contract assertion.

Validation evidence:

- `python -m pytest tests/test_cron_contract.py -q --no-header`: 11 passed;
- `python -m pytest tests/ -q`: 112 passed;
- `yamlgraph graph lint features/haiku/graph.yaml`: no issues;
- no-argument Oulu run: date tool completed, city was `Oulu, Finland`, and a
  non-empty weather haiku was produced;
- city-override run: date tool completed, city was `Rovaniemi, Finland`, and a
  non-empty weather haiku was produced;
- `python -m tools.control_bundle`: verified;
- token-shaped secret scan: zero findings;
- protected generic executor/intake/control-bundle implementation surfaces:
  unchanged.

Subtraction evidence:

- scheduled production: 50-line workflow + 439-line runner (489) to 49-line
  workflow only;
- focused cron tests: 563 lines / 26 test functions deleted;
- examples: 9 tracked files deleted; only `features/haiku/` remains;
- GREEN diff: 90 insertions, 1,619 deletions across 20 files.

**Human schedule override:** During enforcement, a concurrent edit changed the
schedule from `0 6 * * *` to `0 4 * * *`. The human explicitly selected “Keep
04:00 UTC.” This is the only deviation from the amended judgement; no new
schedule was added.

**Human review:** The operator reviewed the immutable three-commit range
`f8af6f1..a012506` (218 insertions, 1,617 deletions across 20 files) and selected
“Approve push.” GitClaw `main` was pushed and local/remote heads both resolve to
`a01250622f0566b588099c6b72e8bd03ba0eb94c`.

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-827 | Retain the schedule/dispatch idea; retire application-level runner and horoscope fixture |
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
| A-1 | The direct task still needs its non-write LLM provider credential | Preserve only the existing `ANTHROPIC_API_KEY` execution-step mapping; forbid write credentials and generic secret forwarding |
| A-2 | “Documented default” could imply a hidden workflow fallback | Define `features/haiku/graph.yaml` as the README starter value while empty `vars.YAMLGRAPH_TASK` remains a hard failure |

**Purge list:** `tools/cron_run.py`; its focused tests; scheduler-provided date;
task wrapper scripts; multi-feature discovery;
composition scheduling/envelopes; output/failure rendering; attribution footer;
state-output compatibility parsing; generic output Git publication; generic
write permission; persisted checkout credentials; wrapper/fallback variants.

**Scope frozen:** Yes. Deliverables are the simplified read-only cron workflow,
runner/test/example pruning, sole retained self-sufficient Oulu weather haiku
authored through the canonical adapter,
focused workflow contract tests, README responsibility documentation, and
recorded line-count/test/validation/human-review evidence. No YAMLGraph core,
intake/executor/control-bundle, new example, Python date node, Oulu semantic
beyond optional city/date ownership, secret, schedule, write-permission, or
generic publication change is authorized.

The existing `ANTHROPIC_API_KEY` provider mapping is explicitly retained for
the starter task and is not repository-write authority.

**Enforcement gates:** Do not re-run the judge during enforcement. Material
changes to the named graph and prompt must use the canonical graph-authoring
adapter and verified report. Human review of the destructive deletion and
graph-authoring diff plus validation evidence is mandatory before push.

**Amendment authority:** The 2026-08-21 example-pruning and self-sufficient
haiku addition was independently judged APPROVED WITH REVISIONS. A-1 and A-2
are folded above; enforcement authority is active within the amended scope.

### Questions for the human

None.
