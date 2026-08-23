# Authoring brief: FR-862 deviant-daily dispatch inputs

**Prior art:** the governing FR-862 dispositions the FR-level prior art
(FR-826 parent, FR-822 API contracts, FR-819 Actions pattern). No prior
authoring brief targets `deviant-daily/graph.yaml`; the FR-826 brief
created it, this one modifies it.

Governing FR: `feature-requests/FR-862-deviant-daily-on-demand-publish.md`
(judged APPROVED WITH REVISIONS 2026-08-23; C-3 requires this route for
the graph change).

## Target

Modify the existing graph in the sibling repo
`/Users/sheikki/Documents/src/deviant-daily/graph.yaml`. That repo is a
separate git repository — author in place, do not copy it into this
workspace, do not commit anything there.

Artifact to modify: `/Users/sheikki/Documents/src/deviant-daily/graph.yaml`
No prompt artifacts change.

## Task

The graph currently accepts one variable, `date`. Three more dispatch
variables must reach the tool nodes so a manual workflow run can pin a
model, run without publishing, and force an extra post.

Add to the `state:` block:

- `model: str`
- `dry_run: str`
- `force: str`

Wire them into the existing `tool_call` node args, keeping every current
arg intact:

- `draw` gains `force: "{state.force}"` and `dry_run: "{state.dry_run}"`
- `generate` gains `model: "{state.model}"`
- `gate` gains `slot: "{state.drawn.result.slot}"` and `dry_run: "{state.dry_run}"`
- `publish` gains `slot: "{state.drawn.result.slot}"` and `dry_run: "{state.dry_run}"`

Do not change the node types, the tool names, the `state_key` values,
the `on_error` settings, or any edge or condition. The existing
`drawn.result.done` and `gate.result.publish` routing stays exactly as
it is.

The corresponding Python step functions in that repo already accept
these arguments with defaults (`tools/steps.py`), and their unit tests
pass. Unset variables resolve to the empty string, which those
functions normalize to the scheduled-path default — so a run that
passes only `date` must behave exactly as it does today.

## Validation

Run from this workspace:

```bash
yamlgraph graph lint /Users/sheikki/Documents/src/deviant-daily/graph.yaml
```

The graph calls Replicate, an Anthropic vision model, and the
DeviantArt API through its tools, so a live full-pipeline smoke would
publish to a public gallery. Do not run the graph. Record the lint
result and note the smoke as deliberately withheld; the FR carries the
live dry-run dispatch as its own witness (AC-17).
