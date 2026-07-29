# Feature Request: Graph Authoring Workflow Skill

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged (APPROVED WITH REVISIONS — folded)
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

When a user asks an agent to create a YAMLGraph example, the agent follows a
single, repeatable graph-authoring workflow: it researches similar committed
graphs, selects the smallest existing pattern, authors graph and prompt files,
runs `yamlgraph graph lint` and an appropriate local smoke/demo command, fixes
failures, and returns only a verified artifact summary. New graph creation becomes
a delegated, evidence-producing workflow rather than a one-shot text generation
bet.

## Proposed Solution

Add a new workflow skill package, tentatively:

```text
.github/skills/graph-authoring/
├── SKILL.md
└── doctrine.md
```

The skill is distinct from the current low-level skills:

| Skill | Role |
|---|---|
| `author-graph` | Syntax reference for graph YAML fields, nodes, edges, state, tools, conditions. |
| `author-prompt` | Syntax reference for prompt YAML, schemas, Jinja2, and prompt contracts. |
| `graph-authoring` | End-to-end workflow for creating a complete graph artifact from a task. |

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

- [ ] AC-01: `.github/skills/graph-authoring/SKILL.md` exists with valid YAML
      frontmatter: `name: graph-authoring`, a non-empty `description` containing
      "Use when:", and a non-empty `argument-hint`.
- [ ] AC-02: `.github/skills/graph-authoring/doctrine.md` exists and defines the
      graph-authoring workflow contract: input closure, precedent search,
      artifact boundary/report, local validation, escalation rules, and
      anti-patterns.
- [ ] AC-03: `SKILL.md` explicitly composes with `author-graph` and
      `author-prompt` as syntax/reference skills and does not duplicate their
      graph-node or prompt-schema reference material beyond brief trigger
      guidance.
- [ ] AC-04: The skill or doctrine explicitly rejects the one-shot
      `examples/yamlgraph_gen` path as the default for repeated graph authoring
      and cites the `workspace_is_not_boundary` / FR-763 precedent.
- [ ] AC-05: The workflow requires `yamlgraph graph lint <graph.yaml>` and the
      narrowest meaningful smoke/demo command when credentials and dependencies
      permit; blocked validation must record the exact blocked command and
      reason, not claim success.
- [ ] AC-06: The workflow uses "artifact-closed delegation brief" language and
      explicitly states it is not FR judgement/review and must not invoke
      `judge-fr`, `review-pr`, their adapters, or any judgement/review graph.
- [ ] AC-07: `tests/unit/test_fr446_copilot_skills.py` includes
      `graph-authoring` under `@pytest.mark.req("REQ-YG-423")` and asserts
      frontmatter validity, non-empty substantive content, required doctrine
      headings, and composition references to `author-graph` and
      `author-prompt`.
- [ ] AC-08: `capabilities/CAP-158-copilot-skill-promotion.yaml` updates
      REQ-YG-423 to include `graph-authoring`, and `ARCHITECTURE.md` is
      regenerated so the CAP-158 text and module list match the capability file.
- [ ] AC-09: A changelog fragment exists in `changelog/unreleased/` with a valid
      requirement reference to REQ-YG-423.
- [ ] AC-10: The FR is updated with implementation status, decisions, and any
      deviations from this judgement after enforcement.
- [ ] AC-11: A diary reflection is added if the resulting PR type triggers the
      repo diary gate.
- [ ] AC-12: No changes are made to `examples/yamlgraph_gen/`, generated output
      directories, mobile/web trigger channels, judge/review doctrine or
      adapters, hooks, CI workflows, branch protection, or graph-generation
      runtime primitives under this FR.

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
