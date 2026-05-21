# Reflection: FR-438 Thoughtcrime Hook

## Trap: gate_checks_shape_not_substance
Instructions say "don't do X" but verification checks whether the instruction file exists, not whether the agent follows it. `copilot-instructions.md` is a shape gate: presence ≠ compliance. The agent's private reasoning (`reasoningText`) is the only place where non-compliance is observable, and no existing enforcement layer inspects it.

## Insight
The transcript JSONL is an overlooked enforcement boundary. PostToolUse and PreToolUse hooks inspect tool arguments and file contents — they operate at the *action* boundary. But reasoning anti-patterns live at the *instruction* boundary: the agent's internal chain-of-thought. The transcript JSONL is the only data source that crosses this boundary, turning unverifiable advisory text into auditable policy.

The two-hook concert pattern (PostToolUse arms, PreToolUse fires) is the key design insight — it converts an observation-only hook type (PostToolUse) into an enforcement mechanism by using the filesystem as a cross-hook communication channel. Session-scoped sentinel filenames provide natural isolation for parallel agents.

## Heuristic
When enforcement fails because the data lives in a different execution context than the gate, find the data source that crosses the boundary and add a hook there. Don't extend existing gates beyond their natural boundary.

**Seed:** Could the thoughtcrime registry evolve into a general-purpose "reasoning policy" language — where operators define not just forbidden phrases but required reasoning patterns (e.g., "before skipping a test, the agent must state which test and why"), creating a positive-obligation enforcement layer alongside the negative-prohibition one?
