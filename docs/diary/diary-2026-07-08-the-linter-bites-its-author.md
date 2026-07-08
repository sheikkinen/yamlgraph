# The Linter Bites Its Author (FR-700)

**Date:** 2026-07-08
**Context:** FR-700 timeframe recap demo — Plan → Judge → Enforce in one sitting.

## What happened

The Judgement froze a 4-field output schema (`workstreams`, `orphans`,
`hotspots`, `conventions_detected`). During Enforce, `yamlgraph graph lint`
raised W026 — the prompt-monolith linter graduated from FR-586 — against the
very schema the Judge had just approved: 4 top-level fields, possible fused
judgement.

The linter was right. `conventions_detected` is mechanically derivable
(`fr_changes`/`fragments` non-empty) — bookkeeping wearing a judgement's
costume. The Jinja2 template already told the model "no convention detected";
asking the model to echo that back as a bool was asking a stateless worker to
re-derive what code already knew. Removed from the schema, deviation recorded
in the FR.

## The trap

A special case of `infrastructure_self_exempt` with a twist: the exemption was
not deliberate. The Judge checked the schema against the FR's own constraints
(one judgement, serialization out of scope) and passed it — but did not run
the mechanical gate that encodes the same doctrine. Human-shaped judgement
approved what machine-shaped judgement rejected minutes later. The gate
exists precisely because Judgement under momentum miscounts abstraction
levels.

## The second observation (read_raw_output_first, applied)

Ran the demo for real and read the raw recap end-to-end before accepting the
exit code. Concrete detail a generated dump would not contain: every one of 21
workstreams ends with the identical string `layers: code/graph/prompt/other` —
the model reproduced the format example from the field description instead of
computing per-layer counts. The judgement (grouping, orphan flagging) is
grounded and correct; the decoration is filler. Not chased with prompt levers:
the layer counts are mechanically derivable from `--numstat` and belong in
code if anyone ever needs them (`l5-prompt-lever-discrimination-kill` applies).
Recorded in the FR as a known limitation.

## Heuristic

Run the mechanical gates *during* Judgement, not only during Enforce — `graph
lint` on the sketched YAML is free and would have caught F-W026 before scope
freeze. The Judge who does not run the linter is reviewing with one eye.

**Seed:** Should the Judge step of the chaplain pipeline compile-and-lint the
FR's sketched graph/prompt YAML blocks (extract fenced yaml, lint in a temp
dir) so that frozen scope can never contradict a gate that already exists?
