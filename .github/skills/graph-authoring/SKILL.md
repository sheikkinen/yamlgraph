---
name: graph-authoring
description: "End-to-end workflow for creating a complete YAMLGraph artifact from a natural-language task — the ONLY way to author graphs. Use when: asked to create a new graph, example, or demo; turning a task description into graph + prompt files; ANY task that results in a new or materially modified graph.yaml or prompts/*.yaml, however phrased (mv, copy, adapt, tweak); drafting a pipeline that needs local validation before delivery. Not a syntax reference — composes reference/graph-yaml.md and reference/prompt-yaml.md."
argument-hint: "task description, or target directory like examples/demos/<name>/"
---

# Graph Authoring Workflow (discovery wrapper)

The canonical workflow contract lives in the adjacent `doctrine.md` —
that file is the single source of graph-authoring doctrine. This wrapper
tells you where things are and how the skill composes.

**This skill is the only way.** The trigger is the artifact class, not
the task phrasing: if the work creates or materially modifies a
`graph.yaml` or `prompts/*.yaml` artifact — even when the request is
worded as "mv", "copy", or "adapt" — it is graph authoring and follows
`doctrine.md`. A copy of a working demo into a new directory is a new
artifact, not a file move (witnessed 2026-07-29: "mv hello-runpod"
materialized a new demo whose provider silently defaulted wrong until
lint caught W016 — exactly the failure the doctrine's validation loop
exists to catch).

## Sole route (executable)

```bash
scripts/author.sh <task-brief.md>
```

**(SOLE ROUTE)** — ALL graph authoring runs through this adapter (see
`adapters/README.md` for flags and the artifact-proof rule). There is
no separate "direct" or "delegated" tier and no materiality
discriminator: if the artifact class is governed, the route is the
adapter. The adapter graph launches a copilot node that reads
`doctrine.md`, authors the files, validates them, and writes
`tmp/draft-authoring-report.md`. Output is advisory and uncommitted.
Verify by the report artifact, never exit code.

The route is mechanically enforced (FR-767): `author.sh` arms a per-run
sentinel token, and the PreToolUse guard (`pre-command-guard.sh`) denies
any unsentineled write to governed paths — `examples/**/graph.yaml`,
`examples/**/prompts/*.yaml`, `graphs/*.yaml`, `graphs/<name>/*.yaml`, `graphs/<name>/prompts/*.yaml`
— across file tools and terminal write shapes, failing closed on
ambiguity. If the adapter route fails, **fix the adapter and rerun** —
the failure of the enforcement route is a defect in the route, never a
license to author manually.

Session separation (judge parity): the requesting session writes the
task brief and runs the adapter; it does not author the artifact itself.
FR-bound briefs are written under `feature-requests/authoring-briefs/`
(`fr-XXX-<slug>-brief.md`) and cited by the governing FR — the brief is
the committed input-closure record (FR-852).
Exception (re-entry guard): an agent already launched BY this adapter is
the authoring execution — it authors directly per `doctrine.md` (research
precedent → name the artifact boundary → choose the smallest pattern →
author → validate locally → repair → report), honors the input closure
(task brief + committed repo artifacts + explicit user-provided files
only), and must not relaunch the route.

## Brief pre-flight (FR-806)

`author.sh` mechanically dry-runs the brief before the backend spawns
(no LLM, no execution of brief text). Write briefs so the checks can
see your premises:

- **Checked premise forms:** a line naming a workspace-relative path
  (`dir/file.ext`) alongside an input assertion — "existing", "fixture",
  "prerequisite", "serves", "against", "input", "located at" — must
  point at an existing file, or the run exits 64 quoting the line.
  Lines with output language ("create", "write", "generate", "output",
  "new") are treated as deliverables and never fail pre-flight.
- **Command resolution:** every command line in a fenced block under a
  Validation heading must have a statically resolvable executable
  (PATH lookup; `VAR=x` prefixes stripped; `python -m ...` resolves the
  interpreter; `./script` must exist in the workdir). Substitution-
  headed commands are skipped, never evaluated.
- **Budget warning trigger:** 2+ live full-pipeline
  `yamlgraph graph run …/graph.yaml` smokes — or 3+ narrower graph-run
  smokes — in the validation plan warn against the backend's 900s
  ceiling (the FR-791 timeout class). Advisory only: split validation
  into a resumed brief when it fires.
- **`--no-preflight` boundary:** skips only the pre-flight block.
  Sentinel arming, the report gate, and every other route exit
  semantic remain mandatory (`automation_inherits_doctrine`).

## Forbidden routes

- **Direct main-session authoring** — writing governed graph artifacts
  from the requesting session, however small the edit.
- **Ad-hoc subagent briefs** — delegating authoring to a subagent
  outside the adapter wrapper.
- **Copy/move/adapt framing** — "mv", "cp", "adapt", "tweak" of a
  governed artifact is authoring of a new artifact, not a file
  operation (witnessed 2026-07-29: "mv hello-runpod" materialized a
  demo whose provider silently defaulted wrong until lint caught W016).
- **One-shot generation** — the rejected `examples/yamlgraph_gen`
  single-synthesis model (FR-763).

## Composition — do not duplicate syntax references

- `reference/graph-yaml.md` — graph YAML syntax: nodes, edges, routing,
  state keys, tools, loop limits, error handling. Consult it; do not
  restate it here. (`reference/expressions.md` for conditions.)
- `reference/prompt-yaml.md` — prompt YAML syntax: templates, inline
  schemas, Jinja2, system segments, and the prompt contract (one prompt
  = one subagent brief). Consult it; do not restate it here.
- `graph-authoring` (this skill) — the process contract around both:
  what to do first, what artifact to produce, how to prove it works.

## What this skill is NOT

- **Not the one-shot generator.** The stale `examples/yamlgraph_gen`
  one-shot generation model is rejected as the default path for repeated
  graph authoring: it collapses pattern selection, assembly, prompt
  generation, validation, and reporting into a single synthesis bet, and
  its ignored `outputs/*` directories caused the
  `workspace_is_not_boundary` phantom-root incident (FR-763).
- **Not FR judgement or PR review.** Substantial work is delegated via
  an artifact-closed delegation brief (see doctrine), which must not
  invoke `judge-fr`, `review-pr`, their adapters, or any judgement/review
  graph, and must not use verdict vocabulary.

## Quick validation loop

```bash
yamlgraph graph lint path/to/graph.yaml
yamlgraph graph run path/to/graph.yaml --var key=value --full   # narrowest smoke
```

If credentials or dependencies block the smoke run, record the exact
blocked command and the reason — never claim success for an unexecuted
validation.
