# Feature Request: Graph Authoring Workflow Skill

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced round 2 (2026-07-29) — executable adapter route delivered per R-1..R-4
**Effort:** 1 day
**Requested:** 2026-07-28
**First consumer / first event:** A maintainer repeatedly creating new YAMLGraph
examples or demos from a natural-language task, at the moment they would otherwise
try the stale `examples/yamlgraph_gen` one-shot generator or manually re-derive the
authoring workflow from scattered examples, skills, linter output, and diary
lessons.

## Summary

Create a workflow-oriented graph-authoring skill that turns "make a new
YAMLGraph" from a single-shot generation attempt into a repeatable agent
procedure: inspect precedent, choose existing patterns, author graph/prompt files,
run local validation, repair failures, and report the verified artifact. The skill
uses the existing `author-graph` and `author-prompt` skills as low-level syntax
references, but adds the missing process contract for complete graph creation.

## Value Statement

Graph authors get a repeatable, locally verified workflow for creating graphs,
reducing failed one-shot generation and preserving an artifact-closed delegation
discipline for substantial work.

## Problem

YAMLGraph generation has succeeded many times in practice: the repository's
examples and demos are themselves evidence that agents can create useful graph
artifacts. The failed abstraction is not graph generation as a capability; it is
the one-shot `examples/yamlgraph_gen` model.

`examples/yamlgraph_gen/` attempts to synthesize a complete graph, prompts, tools,
validation, and report in one graph run. That collapses multiple abstraction
levels into one pipeline and has accumulated evidence of practical failure:

- It is a CREATE surface, not a safe RUN surface.
- It depends on LLM calls spanning pattern selection, graph assembly, prompt
  generation, tool generation, file writing, linting, and reporting.
- Local lint currently reports warnings that map directly to known failure modes:
  interrupt without checkpointer, clarify/classify cycle without loop limits,
  mixed simple/Jinja template syntax, and list-state `skip_if_exists` traps.
- Diary entries from 2026-07-27 document downstream fallout from local generator
  outputs under `examples/yamlgraph_gen/outputs/*`: gitignored generated graphs
  polluted example taxonomy discovery on dirty developer machines while clean
  review/CI worktrees missed the defect (`workspace_is_not_boundary`).

For one-off feature work, Chaplain already provides the correct Plan -> Judge ->
Enforce -> PR route. For repeated graph-authoring tasks, a skill is the missing
middle: lighter than a full FR for every demo draft, but stricter than "ask the
model to emit graph.yaml."

## Ideal Result

When a user asks for a new YAMLGraph example, one command executes the
authoring workflow the way `scripts/judge.sh` executes judgement: a thin
YAMLGraph adapter graph launches a copilot node that reads
`.github/skills/graph-authoring/doctrine.md`, researches committed precedent,
authors graph and prompt files, runs `yamlgraph graph lint` plus the narrowest
smoke command, repairs failures, and writes an artifact report. Graph creation
becomes a mechanized, evidence-producing execution route — not advice the
agent may or may not follow — while the doctrine stays the single
non-invocable source of workflow truth.

## Proposed Solution

Wrap graph authoring as a copilot-node-styled executable skill, mirroring the
`judge-fr` bundle shape (doctrine + thin adapter + operator wrapper):

```text
.github/skills/graph-authoring/
├── SKILL.md            # discovery wrapper (delivered round 1)
├── doctrine.md         # canonical workflow contract (delivered round 1)
└── adapters/
    ├── README.md       # execution instructions, load-bearing flags
    ├── graph.yaml      # copilot node, thin pointer to ../doctrine.md
    └── prompts/
        └── author.yaml # zero-duplication pointer prompt + re-entry guard
scripts/author.sh       # operator wrapper (mirrors scripts/judge.sh)
```

The adapter follows the `judge-fr` adapter contract exactly:

- **Thin pointer, zero duplication**: no doctrine in the adapter; the copilot
  node's prompt instructs the agent to read
  `.github/skills/graph-authoring/doctrine.md` and follow it.
- **Re-entry guard (narrowed, R-1)**: the launched agent IS the authoring
  execution — it must author directly and must not invoke the `graph-authoring`
  skill, `scripts/author.sh`, `.github/skills/graph-authoring/adapters/graph.yaml`,
  or any command that launches that adapter route again. Ordinary
  `yamlgraph graph lint <target graph>` and narrow smoke commands against the
  authored target graphs remain required — the guard bans only recursion into
  the route, never validation (judge-fr NC-414 recursion guard, adapted).
- **Copilot node** with `backend: cli`, `allow_all_paths`/`allow_all_tools`
  (load-bearing for non-interactive file writes — NC-414 precedent), model
  pinned, generous timeout (authoring includes lint/smoke loops).
- **Operator input contract (R-2)**: `scripts/author.sh <task-brief.md>` is the
  sole operator command; the wrapper validates the task brief exists; the
  adapter graph state includes `task_path: str`; the pointer prompt instructs
  the launched agent to read that task brief plus committed repo artifacts and
  explicit user-provided files only. Target directories and desired artifact
  names live inside the task brief, never in hidden chat narrative.
- **Artifact-report contract (R-2)**: `tmp/draft-authoring-report.md` is a
  parseable artifact, not prose: it must contain the headings `Artifacts`,
  `Precedent`, `Validation`, `Repairs`, and `Blocked validation`, and list at
  least one repo-relative authored/modified path under `Artifacts`.
  `scripts/author.sh` fails unless the report is non-empty and at least one
  listed artifact path exists; the adapter graph's exit code is never
  sufficient proof of success.
- **Advisory output**: authored files land in the working tree uncommitted;
  the human reviews and commits. The graph must never auto-commit, open PRs,
  poll inboxes, manage worktrees, run CI, or merge.

The skill remains distinct from the current low-level skills:

| Skill | Role |
|---|---|
| `author-graph` | Syntax reference for graph YAML fields, nodes, edges, state, tools, conditions. |
| `author-prompt` | Syntax reference for prompt YAML, schemas, Jinja2, and prompt contracts. |
| `graph-authoring` | Executable end-to-end workflow for creating a complete graph artifact from a task. |

### Workflow contract

`graph-authoring/SKILL.md` should instruct the agent to:

1. **Research precedent first** — search committed `examples/`, `examples/demos/`,
   and `.chaplain/graphs/` for the closest existing graph shape before authoring.
2. **Name the artifact boundary** — identify the graph directory, prompt files,
   optional tool files, README/demo output, tests, and whether the task belongs in
   Chaplain instead.
3. **Choose the smallest pattern** — prefer copying and adapting an existing
   graph/prompt pattern over inventing a new abstraction.
4. **Delegate when substantial** — for non-trivial graph creation, use an
   artifact-closed delegation brief: closed inputs, explicit artifacts, no hidden
   chat narrative, and a returned report with commands run and failures fixed.
   This is not FR judgement or PR review; it must not invoke `judge-fr`,
   `review-pr`, their adapters, or any judgement/review graph.
5. **Author with existing skills** — consult `author-graph` for graph YAML syntax
   and `author-prompt` for prompt/schema syntax instead of duplicating their
   reference material.
6. **Validate locally** — run `yamlgraph graph lint <graph.yaml>` and the narrowest
   meaningful smoke command. If the graph uses LLM calls and credentials are not
   available, record the exact blocked command rather than claiming success.
7. **Fail loudly** — do not substitute broad catches, skipped map branches, or
   success-shaped fallbacks for failed graph generation.

### Doctrine file

`graph-authoring/doctrine.md` should hold the stable workflow rules, analogous to
`judge-fr/doctrine.md`, so the `SKILL.md` wrapper stays short and discoverable.
The doctrine is local to authoring; it must not modify or weaken the canonical
Judge/Review execution routes.

Suggested doctrine sections:

- Input closure: task request + committed repo artifacts + explicit user-provided
  files only.
- Precedent search order.
- Artifact report contract.
- Validation command requirements.
- Escalation rules: when to submit a Chaplain proposal instead of editing directly.
- Anti-patterns: single-shot generator, generated outputs under tracked example
  trees, unvalidated graph.yaml, broad fallback, remote/mobile create-and-run
  collapse.

This FR unconditionally extends CAP-158 / REQ-YG-423 with the
`graph-authoring` skill. Enforcement must update
`capabilities/CAP-158-copilot-skill-promotion.yaml`, regenerate the CAP-158
section of `ARCHITECTURE.md`, and extend the skill promotion tests in the same
change.

### Explicit non-goals

- Do not revive `examples/yamlgraph_gen` as the primary path.
- Do not add a mobile/web trigger surface in this FR.
- Do not alter `judge-fr` or `review-pr` doctrine.
- Do not implement a new graph-generation framework primitive.
- Do not auto-run uncommitted/generated graphs from remote requests.

## Acceptance Criteria

Round 1 (delivered 2026-07-29, commits 30fc5a4a + 6d2259fc):

- [x] AC-01: `.github/skills/graph-authoring/SKILL.md` exists with valid YAML
      frontmatter: `name: graph-authoring`, a non-empty `description` containing
      "Use when:", and a non-empty `argument-hint`.
- [x] AC-02: `.github/skills/graph-authoring/doctrine.md` exists and defines the
      graph-authoring workflow contract: input closure, precedent search,
      artifact boundary/report, local validation, escalation rules, and
      anti-patterns.
- [x] AC-03: `SKILL.md` explicitly composes with `author-graph` and
      `author-prompt` as syntax/reference skills and does not duplicate their
      graph-node or prompt-schema reference material beyond brief trigger
      guidance.
- [x] AC-04: The skill or doctrine explicitly rejects the one-shot
      `examples/yamlgraph_gen` path as the default for repeated graph authoring
      and cites the `workspace_is_not_boundary` / FR-763 precedent.
- [x] AC-05: The workflow requires `yamlgraph graph lint <graph.yaml>` and the
      narrowest meaningful smoke/demo command when credentials and dependencies
      permit; blocked validation must record the exact blocked command and
      reason, not claim success.
- [x] AC-06: The workflow uses "artifact-closed delegation brief" language and
      explicitly states it is not FR judgement/review and must not invoke
      `judge-fr`, `review-pr`, their adapters, or any judgement/review graph.
- [x] AC-07: `tests/unit/test_fr446_copilot_skills.py` includes
      `graph-authoring` under `@pytest.mark.req("REQ-YG-423")` and asserts
      frontmatter validity, non-empty substantive content, required doctrine
      headings, and composition references to `author-graph` and
      `author-prompt`.
- [x] AC-08: `capabilities/CAP-158-copilot-skill-promotion.yaml` updates
      REQ-YG-423 to include `graph-authoring`, and `ARCHITECTURE.md` is
      regenerated so the CAP-158 text and module list match the capability file.
- [x] AC-09: A changelog fragment exists in `changelog/unreleased/` with a valid
      requirement reference to REQ-YG-423.
- [x] AC-10: The FR is updated with implementation status, decisions, and any
      deviations from this judgement after enforcement.
- [x] AC-11: A diary reflection is added if the resulting PR type triggers the
      repo diary gate.
- [x] AC-12: No changes are made to `examples/yamlgraph_gen/`, generated output
      directories, mobile/web trigger channels, judge/review doctrine or
      adapters, hooks, CI workflows, branch protection, or graph-generation
      runtime primitives under this FR.

Round 2 (executable adapter route — judged 2026-07-29, R-1..R-4 folded):

- [x] AC-13: `.github/skills/graph-authoring/adapters/graph.yaml` exists,
      passes `yamlgraph graph lint`, and defines exactly one `type: copilot`
      node with `backend: cli`, `allow_all_paths: true`,
      `allow_all_tools: true`, a pinned model, a prompt named `author`, a
      `state_key`, and a timeout sized for lint/smoke repair loops. The graph
      state includes `task_path: str` passed to the prompt; no hidden chat
      narrative is required to execute the route.
- [x] AC-14: `adapters/prompts/author.yaml` is a thin pointer prompt: it
      instructs the agent to read `../doctrine.md` and the task brief at
      `task_path`, follow the doctrine, and write
      `tmp/draft-authoring-report.md`; it duplicates no doctrine content and
      contains the narrowed re-entry guard (R-1): must not invoke the
      `graph-authoring` skill, `scripts/author.sh`, the adapter graph, or any
      command relaunching the route — while `yamlgraph graph lint` and narrow
      smoke commands against authored target graphs remain required.
- [x] AC-15: `scripts/author.sh <task-brief.md>` exists, is executable,
      validates the task brief exists, launches the adapter graph with
      `task_path`, and verifies success by artifact existence, never exit
      code: `tmp/draft-authoring-report.md` must be non-empty, contain the
      `Artifacts`/`Precedent`/`Validation`/`Repairs`/`Blocked validation`
      headings, and list at least one repo-relative artifact path that exists.
- [x] AC-16: `adapters/README.md` documents the sole invocation command
      `scripts/author.sh <task-brief.md>`, the load-bearing CLI flags, the
      artifact-existence verification rule, and the prohibition on
      auto-commit, PR creation, merge, inbox polling, CI, and
      worktree-management actions.
- [x] AC-17: `SKILL.md` and `doctrine.md` name the adapter as the execution
      route for delegated authoring, including the task-brief input closure
      and report contract (keeping doctrine non-invocable and
      zero-duplicated).
- [x] AC-18: Skill promotion tests (still `@pytest.mark.req("REQ-YG-423")`)
      assert adapter substance, not presence (R-4): graph shape/flags/model/
      timeout, prompt pointer with narrowed guard and no doctrine-heading
      duplication, executable wrapper documenting the task-brief command with
      artifact-report checks, README command/flag/prohibition content, and
      CAP-158 module synchronization.
- [x] AC-19: `capabilities/CAP-158-copilot-skill-promotion.yaml` updates
      REQ-YG-423 to name the executable graph-authoring adapter route and its
      key modules (SKILL.md, doctrine.md, adapters/README.md,
      adapters/graph.yaml, adapters/prompts/author.yaml, scripts/author.sh),
      and `ARCHITECTURE.md` is regenerated to match (R-3).

## Alternatives Considered

- **Revive `examples/yamlgraph_gen` as the recommended generator:** rejected. Its
  shape is the failure: graph authoring is a multi-step workflow with validation
  and correction loops, not a single synthesis call.
- **Use Chaplain for every graph-authoring request:** correct for feature work,
  but too heavy for repeated local drafting of examples and demos. The skill
  should help decide when to escalate to Chaplain.
- **Expand `author-graph` into the workflow skill:** rejected. FR-446 explicitly
  split `author-graph` and `author-prompt` because graph and prompt authoring
  are distinct syntax concerns. End-to-end graph creation is a third concern:
  workflow orchestration.
- **Build a new YAMLGraph framework primitive for generation:** rejected. Existing
  evidence shows the problem is process discipline, not missing runtime
  capability.

## Related

- `examples/yamlgraph_gen/` — existing one-shot graph generator example, not the
  default path proposed here.
- `.github/skills/author-graph/SKILL.md` — low-level graph YAML authoring
  reference.
- `.github/skills/author-prompt/SKILL.md` — low-level prompt YAML authoring
  reference.
- `.github/skills/judge-fr/doctrine.md` — input-closure and artifact-contract
  precedent; not modified by this FR.
- FR-446 — Copilot skill promotion and split of `author-graph` /
  `author-prompt`.
- FR-763 and `docs/diary/diary-2026-07-27-taxonomy-git-tracked-boundary.md` —
  generator outputs and `workspace_is_not_boundary` precedent.

## Judgement (2026-07-28)

**Verdict:** APPROVED WITH REVISIONS — folded.

Full judgement:
[FR-765-graph-authoring-workflow-skill.judgement.md](FR-765-graph-authoring-workflow-skill.judgement.md)

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | CAP-158 extension was conditional, but CAP-158 / REQ-YG-423 is the governing skill-promotion registry. | Folded: this FR unconditionally extends CAP-158 / REQ-YG-423 with `graph-authoring`; AC-08 requires capability and `ARCHITECTURE.md` sync. |
| R-2 | Tests only checked file presence/non-empty content, a `gate_checks_shape_not_substance` risk. | Folded: AC-07 requires frontmatter parsing, substantive content checks, required doctrine headings, and composition references. |
| R-3 | "judge-fr-style delegation" blurred the hard judge/review execution boundary. | Folded: wording changed to "artifact-closed delegation brief"; AC-06 forbids invoking judge/review skills, adapters, or graphs. |

**Purge list:** Do not revive `examples/yamlgraph_gen`; do not add mobile/web
trigger channels; do not modify judge/review doctrine or adapters; do not add a
new graph-generation runtime primitive.

**Scope frozen:**

| Deliverable | Surface |
|---|---|
| D-1 | `.github/skills/graph-authoring/SKILL.md` |
| D-2 | `.github/skills/graph-authoring/doctrine.md` |
| D-3 | `tests/unit/test_fr446_copilot_skills.py` |
| D-4 | `capabilities/CAP-158-copilot-skill-promotion.yaml` |
| D-5 | `ARCHITECTURE.md` regenerated CAP-158 text only |
| D-6 | This FR implementation status/decisions |
| D-7 | `changelog/unreleased/` fragment |
| D-8 | `docs/diary/` reflection if submitted as a feat/fix PR |

**Conditions (GATE):** C-1 no runtime primitive, generator framework,
mobile/web trigger, or remote create-and-run path; C-2 no judge/review doctrine,
adapter, or route changes; C-3 keep CAP-158, `ARCHITECTURE.md`, and tests
synchronized; C-4 tests check substance; C-5 validation claims are
command-backed or explicitly blocked; C-6 do not rely on ignored
`examples/yamlgraph_gen/outputs/*`; C-7 graph-authoring delegation must not use
verdict vocabulary or judge/review routes.

### Questions for the human (as options, or 'none')

None.

## Implementation Status (Round 1 enforced 2026-07-29; amended same day)

**Amendment (2026-07-29, human correction):** Round 1 delivered the skill as
pattern documentation only (SKILL.md + doctrine.md + tests + CAP-158). The
operator's intent was an *executable* copilot-node-styled skill like
`judge-fr`: a thin YAMLGraph adapter graph whose copilot node executes the
doctrine, launched by an operator wrapper, verified by artifact existence.
Round 1 artifacts stand (the doctrine is the canonical contract the adapter
points to); the missing execution surface is specified in the amended
Proposed Solution and AC-13..AC-18, pending re-judgement. AC-12's "no new
runtime primitives" is unaffected — the adapter reuses the existing copilot
node type exactly as judge-fr's adapter does.

Round 1 delivery (commits 30fc5a4a RED, 6d2259fc GREEN):

- **D-1** `.github/skills/graph-authoring/SKILL.md`: discovery wrapper with
  frontmatter (`name`, `description` with "Use when:" triggers,
  `argument-hint`), composition contract naming `author-graph`/`author-prompt`
  as syntax references (AC-01/03), explicit rejection of the one-shot
  `yamlgraph_gen` model citing `workspace_is_not_boundary`/FR-763 (AC-04),
  and the quick lint+smoke validation loop with blocked-command honesty.
- **D-2** `.github/skills/graph-authoring/doctrine.md`: full workflow
  contract — Input closure, Precedent search (demos → examples →
  `.chaplain/graphs/` → syntax skills), Artifact boundary and report,
  Validation (`yamlgraph graph lint` mandatory, blocked commands recorded
  verbatim), artifact-closed delegation brief with judge/review invocation
  ban and verdict-vocabulary ban (AC-06/C-7), Escalation to Chaplain, and
  Anti-patterns (AC-02/05).
- **D-3** `tests/unit/test_fr446_copilot_skills.py`: RED commit 30fc5a4a —
  `graph-authoring` added to `TIER_1_SKILLS`; presence checks upgraded to
  substance (R-2): parametrized frontmatter parsing (name match, "Use
  when:" triggers, argument-hint) for all seven skills, plus a
  graph-authoring class asserting doctrine headings, composition
  references, generator rejection with FR-763 citation, lint requirement,
  and delegation-not-judgement language. 26 tests pass under
  `@pytest.mark.req("REQ-YG-423")` (AC-07).
- **D-4/D-5** `capabilities/CAP-158-copilot-skill-promotion.yaml` extended
  to seven skills; `ARCHITECTURE.md` CAP-158 section regenerated via
  `aggregate_capabilities.py` (AC-08/C-3).
- **D-7** `changelog/unreleased/fr765-graph-authoring-workflow-skill.md`
  (`type: feat`, `req: REQ-YG-423`) (AC-09).
- **D-8** diary reflection committed with enforcement (AC-11).

Deviations: none. One friction note: the FR-756 process-boundary gate
pattern-matches the literal `examples/` in test docstrings — reworded the
AC-04 docstring rather than marking a filesystem-only test as `process`.

Round 2 delivery (executable adapter route; judgement 2026-07-29 APPROVED
WITH REVISIONS, R-1..R-4 folded before enforcement):

- **D-4** `.github/skills/graph-authoring/adapters/graph.yaml`: single
  copilot node, `backend: cli`, `model: gpt-5.5` pinned, both load-bearing
  NC-414 flags, `task_path: str` state passed as a prompt variable,
  `timeout: 900` for lint/smoke repair loops. `yamlgraph graph lint` clean
  (AC-13).
- **D-5** `adapters/prompts/author.yaml`: thin pointer — read doctrine +
  task brief, write `tmp/draft-authoring-report.md` with the five required
  headings; narrowed re-entry guard (R-1/C-1): bans only relaunching the
  route, explicitly requires `yamlgraph graph lint` + narrow smoke against
  authored graphs; zero doctrine-heading duplication (AC-14).
- **D-6** `scripts/author.sh`: mirrors `scripts/judge.sh` — usage/missing
  brief exits 64/66, `AUTHOR_EXECUTION` lineage sentinel exit 70, atomic
  lock exits 73/75, executor resolution exit 69, artifact contract exit 65
  verifying the report is non-empty with all five headings and at least one
  listed repo-relative artifact path existing (R-2/C-5); exit code never
  proof. Smoke-verified: rc 64/66/0/70 with a stubbed `YAMLGRAPH_BIN`
  (AC-15).
- **D-3** `adapters/README.md`: sole command, task-brief input closure,
  load-bearing flags, artifact-existence rule, auto-commit/PR/merge/inbox/
  CI/worktree prohibitions, judge/review-route ban (AC-16).
- **D-1/D-2** `SKILL.md` gained the "Executable route for delegated
  authoring" section; `doctrine.md` gained the task-brief input closure,
  the parseable report contract, and the narrowed re-entry guard in the
  Delegation section (AC-17).
- **D-7** `tests/unit/test_fr446_copilot_skills.py`:
  `TestGraphAuthoringAdapter` — 10 substance tests (graph shape/flags/
  model/timeout, `task_path` closure, in-process `lint_graph` clean run,
  pointer + narrowed guard, no doctrine-heading duplication, wrapper
  executable with artifact-contract and sentinel content, README
  command/flags/prohibitions, SKILL/doctrine route naming, CAP-158 module
  sync). 36/36 pass (AC-18).
- **D-8/D-9** CAP-158 modules extended with the six adapter-route surfaces;
  REQ-YG-423 description names the executable route; `ARCHITECTURE.md`
  regenerated (AC-19).

Round-2 deviations: none from the frozen scope. Friction notes: (1) the
FR-756 process-boundary gate pattern-matches literal boundary strings in
test module source — adapter test paths are constructed from `Path()`
parts because the tests are pure committed-file reads (no subprocess),
following the round-1 rewording precedent; behavioral wrapper execution
tests (à la FR-758's stubbed `YAMLGRAPH_BIN` suite) were smoke-verified in
the terminal instead, staying within the frozen D-7 test surface. (2) The
round-1 changelog fragment was updated in place to cover the executable
route rather than adding a second fragment (D-11's "one fragment").

Post-enforcement addendum (2026-07-29, operator-directed sole-path sync):
after the route shipped and its first end-to-end smoke passed
(`tmp/task-brief-commit-lint.md` → `examples/demos/commit_lint/`, three
self-repairs, artifact contract verified), the operator directed a
sole-path consistency pass across doctrine surfaces adjacent to but
outside the frozen D-list: `.github/copilot-instructions.md` quickstart
now names the delegated-authoring sole route + re-entry exception
(mirroring the judge/review Sermon declarations); `graph-authoring/SKILL.md`
upgraded "runs through the adapter" to explicit SOLE-route language;
`author-graph` and `author-prompt` SKILL.md descriptions and bodies gained
scope-boundary pointers up to `graph-authoring`, closing the discovery
overlap where "create a new graph" triggers matched the syntax skills
first. No doctrine content was duplicated; all pointers reference the
canonical files.
