# Reflection — FR-1087, FR-1088: the gate that knows one log per directory

**Date:** 2026-09-26
**FRs:** FR-1087 (safety-guards demo repair), FR-1088 (innovation_matrix pipeline repair)

## What happened

Two demo repairs shipped on one branch. FR-1087 was a one-token edge fix
(`to: [revise, expand]` → `to: revise`), and its README now names the W803
warning. FR-1088 declared `domain`, bounded the grid in the schema, took
cell IDs from the real list lengths, and gave `synthesize` every
dispatched pair. It then made its one authorized live run: 25 of 25 cells,
exit 0, and every top idea cites its cell ID.

Both FRs were well judged, and enforcement was boring apart from one
point. The demo-proof gate (local hook and CI step) requires
`demo-output.log` in the diff whenever a demo directory changes. The
`innovation_matrix` directory holds two graphs. The frozen scope put
the proof in `demo-output-pipeline.log` and forbade touching `graph.yaml`
or paying for a second run. The FR and the gate each made sense alone, and
together they could not both be satisfied.

## The trap

`gate_checks_shape_not_substance` in reverse: the gate checks *which file*
changed, not *which graph* the proof witnesses. The FR author, the judge
and I all knew about the two graphs. None of us asked what the gate would
demand of this directory. My first reflex was the loophole
(`SKIP=demo-proof-check`). Instead the conflict went to the operator as a
question. The operator approved the SKIP, and it is disclosed in the
commit, the FR and the PR. A skip that is disclosed and has an owner is a
decision. A silent skip is a bypass.

A second false positive turned up in the same place. The log validator's
`Node .+ failed` pattern is greedy and ran across one long line of LLM
prose ("node" … "failed ground deliveries"). A successful run would have
been rejected for its own content. It also found that the `*.log` ignore
rule silently drops every proof log that is not named `demo-output.log`.
The commit's file stat caught this before the push.

## Heuristic

When a judged scope names a proof artifact by filename, check it against
every gate that inspects that directory **before** approving the scope.
The judge reads the FR, and the gate reads the path. Neither reads the
other.

**Seed:** Should the demo-proof gate map each proof log to the graph it
witnesses (for example `demo-output-<graph-stem>.log`), and require a log
only for the graphs whose files changed, instead of one log per directory?
