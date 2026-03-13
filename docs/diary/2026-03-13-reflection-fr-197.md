# Diary: FR-197 Philosopher Distill Node

**Date:** 2026-03-13
**FR:** FR-197
**Theme:** Boundary-aware JSON parsing

## Reflection

Implementing the distill node revealed a subtle parser boundary issue: `extract_json()` uses an array-first search order (`[` before `{`), which silently extracts inner arrays from objects containing `"files": [...]`. For the analyze node (which outputs arrays), this order is correct. For distill (which outputs objects), it would return the nested `files` array — a plausible wrong answer that passes type checks but is semantically wrong.

**Trap:** `plausible_wrong_answer` — The `extract_json` utility would have returned valid JSON (the files array), and `Proposal.model_validate()` would have failed with a confusing Pydantic error pointing at the wrong location. Without the RED phase catching this immediately, the bug would have been attributed to the Pydantic model or the LLM output format.

**Heuristic:** When reusing a parser across contexts, verify its assumptions hold in the new context. `extract_json` assumed array-first because it was built for the analyze node. The distill node's object-first requirement was invisible until TDD exposed it.

The fix was surgical: `unwrap_distill` does its own `{}`-first extraction instead of calling `extract_json`. This follows the callsite_fix cure — fix at the specific caller, not the shared utility.

**Seed:** Should `extract_json` accept an optional `prefer` parameter (`"object"` vs `"array"`) to make the search order explicit? Or is it cleaner to keep callers responsible for their own parsing boundary?
