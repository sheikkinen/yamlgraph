# Chapter 24: Three Bugs, One Chain

*On the fragility of parameter passing across an integration boundary — and why bugs in series can hide for much longer than bugs in parallel.*

---

## I. The Observation

After fixing the annotation bug (Chapter 23) and the event routing bug (FR-420), a third failure appeared at the `validate_fix` state. The pipeline had progressed further than ever before — plan ran, judge approved, enforce ran, sanity check passed — and then died at the last validation step with:

```
invalid action config: 1 validation error for ActionConfig
vars.validate_gate_output
  Input should be a valid string [type=string_type, input_value={'attempt': 1, ...}]
```

`validate_gate_output` is a dict in the FSM context. The action block templates it as `"{validate_gate_output}"`. When the template is a single-expression substitution, statemachine_engine passes through the raw context object — the dict is not stringified. `ActionConfig.variables: dict[str, str]` rejected it.

Three bugs. One path. All silent.

---

## II. The Topology of the Failure

The path a single variable takes from a pipeline YAML action block to a running graph:

```
watcher-pipeline-v2.yaml
  → statemachine_engine (context resolution / template substitution)
    → YamlgraphAsyncAction.execute()
      → ActionConfig.model_validate()
        → run_and_dispatch()
```

Three failure points in this path were discovered sequentially across this session:

| # | Boundary | Failure | Visible when |
|---|---|---|---|
| 1 | Config parsing | `extra="forbid"` rejected `description:` annotation | Always — first action |
| 2 | Graph output parsing | `extract_event` first-line only, missed preamble | Only after #1 fixed |
| 3 | Variable coercion | `dict[str, str]` rejected raw dict from engine | Only after #1 and #2 fixed |

This is the structure of **bugs in series**: the first failure aborts the chain. The pipeline never reaches the second or third failure point. Each fix reveals the next bug. The true count of failures in the system was not knowable from the first observation.

---

## III. The Underlying Fragility

The parameter-passing chain is an integration boundary with no typed contract.

On one side: statemachine_engine, which resolves `{key}` templates in YAML config using the FSM context dict. Its behavior on single-expression templates (`"{key}"` with nothing else in the string) is to pass through the raw context value — not stringify it. This is undocumented and untested.

On the other side: `ActionConfig`, a Pydantic model with `extra="forbid"` and typed fields. It expects strings in `variables`. It rejects unknown keys.

Between them: no contract. No integration test. No shared schema. What arrives at `model_validate()` depends on what statemachine_engine decided to do with each value — and that behavior is opaque.

The two execution paths in `action.py` make this worse. `_execute_cli()` (legacy, builds CLI args) stringified everything explicitly: `str(value)` before template substitution, then `str(ctx_val)` again when interpolating. The new `YamlgraphAsyncAction.execute()` path called `model_validate()` directly on the engine-resolved dict, trusting the engine to have done the right thing. It had not.

The same key passed through two paths with different behavior. No test caught the difference.

---

## IV. The Fixes

All three fixes normalize at the boundary — not downstream at the symptom site:

**Fix 1** (`_STRIP_BEFORE_VALIDATE`): Strip author-annotation keys before validation. The boundary is `model_validate()`. Fix there, not in the action block authors' behavior.

**Fix 2** (`extract_event` splitlines): Scan all lines, not just the first. The boundary is the raw LLM/copilot output entering the routing logic. Normalize there.

**Fix 3** (`_coerce_variable_values` validator): JSON-serialize non-string values in `variables`. The boundary is `model_validate()`. The engine's template behavior is the upstream we cannot control; coerce at entry.

Each fix is one method, in the right file, at the right boundary. None required changes to the pipeline YAML or the upstream engine.

---

## V. The Cognitive Trap

The trap in this session was **continuation_bias** compounded by **recent_changes_blindness**.

When the pipeline was failing at judge, the natural question was "what is wrong with judge routing?" — not "what else changed recently that touches the whole pipeline?" The recent change was FR-419. FR-419 touched `execute()`. `execute()` runs for every action in every state. The first diagnostic step should have been `git log --since=<last-working-run>` to enumerate what changed — not to read the judge event logic.

Instead, the investigation went: judge logs → extract_event → FR-420 fix → still failing → description field → FR-419 gap → still failing at validate_fix → dict coercion. Each step was correct but the sequence was bottom-up through symptoms rather than top-down from the change that introduced them.

The **changelog_first_diagnostic** heuristic exists for exactly this. It was not applied here.

---

## VI. What This Means for the System

The parameter-passing chain is not inherently unfixable — it is unfixed. What it needs is:

1. **A typed contract at the boundary**: either an integration test that exercises the full YAML → engine → ActionConfig → graph path, or a schema that the engine validates against before calling `execute()`.

2. **One execution path, not two**: `_execute_cli()` and `run_and_dispatch()` implement the same contract differently. The coercion in `_execute_cli()` should be in `ActionConfig`, not in the CLI-building code. The consolidation FR has not been written.

3. **Visibility on failure**: `event=error` from a validation failure looks identical in the state machine to `event=error` from a correctly-routed failure. The log line exists but is not surfaced differently. A distinction between "error from routing" and "error from internal exception" would cut investigation time significantly.

Until those three things exist, the chain will accumulate more breaks as new context variables are added to the pipeline. Each one that happens to be a dict, or a non-string primitive, will fail silently at `validate_fix` or wherever it is first used.

---

**Seed:** If `ActionConfig._coerce_variable_values` is the right place to normalize, should the coercion be lossless? JSON round-trip preserves dict structure. But what does the receiving graph do with a JSON string it expected to be a dict? The real fix may be that complex context objects should never travel as `--var` strings at all — they belong in a checkpoint or a shared state file. Is there a cleaner data-passing contract between the FSM and the graph?
