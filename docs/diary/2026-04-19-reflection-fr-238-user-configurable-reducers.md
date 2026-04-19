# Diary: FR-238 User-Configurable Reducers in YAML State

**Date:** 2026-04-19
**FR:** FR-238

## Cognitive Process

The state section's existing `type: str` syntax needed extending to `{type: str, reducer: append}` without breaking the simple string form. The boundary here is `parse_state_config()` — where YAML state entries enter the framework. Both syntaxes must resolve to the same TypedDict shape but with different LangGraph reducer annotations.

## Trap Avoided: Downstream Fix

Adding reducer logic at the TypedDict generation layer (downstream) rather than normalizing at `parse_state_config()` (the boundary) would have created a second path through the codebase. The fix was kept at the entry point.

## Insight

**Dict-syntax extension must be additive.** Introducing `{type, reducer}` dict syntax alongside `type: str` shorthand means the parser must handle both forms transparently. A `REDUCER_MAP` lookup with a warning for unknown keys is the right boundary guard — fail loudly on typos, not silently.

## Heuristic

When extending a YAML config field to accept multiple syntaxes (string vs dict), normalize at the parse boundary to a canonical internal form, never at the consumer.

## Seed

Should reducers be extensible via plugin — allowing users to register custom Python functions as reducer names in the YAML state section, beyond the built-in `add`, `append`, `extend`?
