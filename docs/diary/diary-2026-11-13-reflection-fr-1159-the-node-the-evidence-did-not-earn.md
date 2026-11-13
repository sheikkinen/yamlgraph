# Reflection: FR-1158/FR-1159 — the node the evidence did not earn

**Date:** 2026-11-13
**FR:** FR-1158 (core `cached_map` node, rejected), FR-1159 (memo shipped as contrib)

## What happened

The request was a new `cached_map` node type, separate from `map`. The judge rejected it: two consumers and a
demo support a contrib helper, not a core primitive. The operator accepted the contrib classification. yamlgraph
has no node-type plugin hook, so "contrib node" collapsed into the smallest true thing: move the FR-1116 memo
tools from `examples/shared` (excluded from the wheel) into `yamlgraph/contrib`, unchanged, and prove it from an
installed wheel.

Two things broke along the way, and neither was in the code being moved. The wheel witness could not build with
`--no-build-isolation`, because the host Python has no setuptools; isolation lets pip fetch the declared backend.
The authoring adapter failed in six seconds with an empty output, because its pinned model was no longer served.
The adapter hid the CLI's stderr, so the cause took one direct `copilot -p` probe to surface.

The authoring agent also caught a brief error of mine: a Python node's dict return is merged into state, not
wrapped by `state_key`. The brief's flat `{"paths", "store"}` shape would have left `plan` unset.

## Heuristic

**When a feature request names a mechanism, check whether the evidence earns the mechanism or only the
capability.** "Cached map" was the capability; a node type was one possible mechanism, and the costliest. The
capability shipped with no compiler change.

Second: **an adapter that swallows its child's stderr turns every environmental failure into "contract
violated."** Probe the child directly before reading the adapter's verdict as a defect in the task.

**Seed:** Should `scripts/author.sh` and `scripts/judge.sh` preflight their pinned model with a one-token call, so
that a retired model id fails as "model unavailable" instead of as a missing report?
