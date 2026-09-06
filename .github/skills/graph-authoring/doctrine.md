# Graph Authoring Doctrine

Canonical workflow contract for creating a complete YAMLGraph artifact
(graph YAML + prompt YAML + optional tools + validation evidence) from a
task. Governed by FR-765; registered under CAP-158 / REQ-YG-423. This
doctrine is local to authoring — it does not modify or weaken the
canonical Judge/Review execution routes.

## Trigger boundary

This doctrine binds on the **artifact class, not the task phrasing**:
any work that creates or materially modifies a `graph.yaml` or
`prompts/*.yaml` is graph authoring, whether the request says "create",
"mv", "copy", or "adapt". Copying a committed graph into a new
directory materializes a new artifact and enters this doctrine at the
precedent-search step (the copy IS the precedent); lint + smoke +
honest validation record remain mandatory.

## Input closure

Inputs are closed: the task request, committed repository artifacts, and
files the user explicitly provides. When executed via the adapter route,
the task request is a **task brief** — a markdown file passed as
`task_path` — and any target directory or desired artifact name must be
stated inside that brief, never inferred from hidden chat narrative.
FR-bound task briefs live committed under
`feature-requests/authoring-briefs/` (`fr-XXX-<slug>-brief.md`;
standalone briefs `<slug>-brief.md`), and the governing FR cites that
committed path — the brief is the artifact's input-closure record and
must survive tmp/ cleanup (FR-852). Do
not treat chat narrative,
uncommitted local state, or ignored generated outputs as authoring
input. In particular, never rely on `examples/yamlgraph_gen/outputs/*`
or any other gitignored generated tree — ignored generator outputs
polluting discovery is the `workspace_is_not_boundary` failure recorded
by FR-763.

## Precedent search

Before authoring anything, search committed precedent in this order:

1. `examples/demos/` — smallest runnable patterns (start here).
2. `examples/` — full applications with tools and tests.
3. `graphs/` — process/pipeline graph shapes (`graphs/enforcement/`,
   `graphs/fr_triage/`, `graphs/world_distill/`, `graphs/philosopher/`).
4. `reference/graph-yaml.md`, `reference/prompt-yaml.md`, and
   `reference/expressions.md` — syntax only.

Choose the smallest existing pattern and adapt it. Copying a working
committed graph beats inventing a new shape; a new abstraction requires
naming why every existing pattern fails.

## Artifact boundary and report

Name the artifact boundary before writing files: target directory,
`graph.yaml`, `prompts/*.yaml`, optional `nodes/`/tool files, README or
demo output, and tests. If the task is feature work on the framework
itself — not a new example/demo/pipeline — file an FR instead
(see Escalation).

The artifact report returned to the requester must contain:

- Files created/modified (paths).
- Pattern precedent used (which committed graph was adapted).
- Exact validation commands run and their outcomes.
- Failures found and how each was repaired.
- Any blocked validation: the exact blocked command and the reason
  (missing credential, missing extra, absent service).

When executed via the adapter route, the report is written to
`tmp/draft-authoring-report.md` as a parseable artifact with the
required headings `Artifacts`, `Precedent`, `Validation`, `Repairs`,
and `Blocked validation`; the `Artifacts` section lists at least one
repo-relative authored path. The wrapper verifies this report and the
listed paths by existence — never by exit code.

## Validation

Local validation is mandatory, command-backed, and honest:

- Run `yamlgraph graph lint <graph.yaml>` — required for every authored
  or modified graph. Fix warnings that map to known failure modes:
  interrupt without checkpointer, cycles without loop limits, mixed
  simple/Jinja template syntax, list-state `skip_if_exists` traps.
- Run the narrowest meaningful smoke command (`yamlgraph graph run …`
  with minimal vars, or the example's demo script) when credentials and
  dependencies permit.
- If validation is blocked, record the exact blocked command and reason
  in the artifact report. A blocked validation is a blocked validation —
  never claim success, and never substitute a weaker check silently.

## Sole route (adapter execution, artifact-closed)

ALL graph authoring — there is no materiality threshold — runs through
an **artifact-closed adapter execution**: closed inputs (task + named
committed artifacts), explicit expected artifacts, no hidden chat
narrative, and a returned artifact report per the contract above. The
sole executable route is the adapter: `scripts/author.sh <task-brief.md>`
(see `adapters/README.md`). The requesting session writes the brief and
runs the adapter; it never authors the artifact itself. The route is
enforced mechanically (FR-767): unsentineled writes to governed graph
artifact paths are denied by the PreToolUse guard. If the route fails,
fix the adapter and rerun — route failure is never a license to author
manually. Re-entry guard (narrowed): an agent launched BY
the adapter is the authoring execution itself — it must not invoke the
`graph-authoring` skill, `scripts/author.sh`, the adapter graph, or any
command relaunching the route; running `yamlgraph graph lint` and
narrow smoke commands against the graphs it authors remains required.

This is workflow execution, not FR judgement or PR review. The brief
and the authoring execution **must not invoke** `judge-fr`, `review-pr`, their
adapters, or any judgement/review graph, and must not use verdict
vocabulary (approved, rejected, condemned, verdict) in the report.

## Escalation

Submit a proposal (`proposals/`, see the feature-request skill) instead of authoring
directly when:

- The task changes framework code, hooks, CI, or doctrine — anything
  beyond a self-contained graph artifact.
- The graph needs a new node type, provider, or runtime primitive.
- Acceptance requires judged scope (multi-file feature work with
  constraints worth freezing).

Graph artifact authoring — examples, demos, pipelines — goes through
the adapter route above; one-off feature work goes Plan → Judge →
Enforce through the operator rite (`reference/command-book.md`).

## Anti-patterns

- **Single-shot generation**: emitting graph + prompts + tools + report
  from one synthesis call (the rejected `examples/yamlgraph_gen` model).
- **Generated outputs under tracked example trees**: writing generator
  results where discovery/taxonomy scans can mistake them for committed
  examples (FR-763, `workspace_is_not_boundary`).
- **Unvalidated graph.yaml**: delivering a graph without a lint run and
  a smoke attempt (or an honestly recorded blocked command).
- **Broad fallback**: wrapping generation or validation in catch-all
  handlers that convert failure into success-shaped output.
- **Remote/mobile create-and-run collapse**: auto-running uncommitted or
  generated graphs from remote requests.
- **Syntax duplication**: restating `reference/graph-yaml.md` /
  `reference/prompt-yaml.md` reference material here instead of
  consulting those docs.
