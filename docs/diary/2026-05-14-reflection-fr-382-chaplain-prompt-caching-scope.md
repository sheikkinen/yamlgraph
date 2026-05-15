# Reflection: FR-382 Chaplain Prompt Caching Scope

## Cognitive Traps and Insights

**Trap: working_system_inertia — "It works" blocks seeing it clearly.**
The rough topic asked for blanket conversion of all Chaplain prompt files to
`system_segments`. Research revealed that most Chaplain prompts are consumed by
`type: copilot` nodes, which read `system` and `user` fields only — they silently
ignore `system_segments`. A broad conversion would have removed system instructions
from every Copilot-backed node while appearing to succeed (no crash, just missing
context). The system would still "work" — just with degraded prompts.

**Trap: plausible_wrong_answer — output passes shape check but is semantically wrong.**
Converting all prompt files to `system_segments` passes YAML schema validation.
The linter would not flag it. The unit tests would not fail unless tests explicitly
assert the `copilot` boundary. This is a classic plausible-wrong-answer: structurally
valid YAML, semantically broken runtime behavior.

**Insight: normalize at the boundary where external data enters.**
The correct boundary was the node type: `type: llm` nodes go through `executor_base.py`
which understands `system_segments`; `type: copilot` nodes go through `copilot_node.py`
which does not. The safe conversion scope is exactly the set of prompts consumed by
`type: llm` nodes — determined by graph inventory, not by prompt file structure.

## What Worked Well

- Inverting the scope question from "which files can I convert?" to "which node types
  support `system_segments`?" immediately narrowed the blast radius to a single prompt.
- Writing AC tests that assert the copilot boundary *before* implementation made the
  scope machine-checkable and prevented regression.
- Single-responsibility: YAML-only change with no Python runtime modifications kept
  the diff minimal and the risk low.

## Heuristic Reinforced

`gate_checks_shape_not_substance`: YAML schema validation confirms structure but not
runtime semantics. Tests that assert behavioral boundaries (which node type consumes
which field) are the only guard against structurally-valid but semantically-broken
changes.

Seed: Could the graph linter be extended to emit a warning when a prompt file uses
`system_segments` but is referenced only by `type: copilot` nodes — catching the
caching-boundary mismatch before it reaches a human reviewer?
