
---

## 2026-03-09: Reflection — FR-168 Cross-Graph Session Continuity

**Trap:** Linter false positive as hidden coupling. The W-COPILOT-SESSION lint rule checked for `.session_id` in the resume expression, assuming the pattern is always `{state.result.session_id}`. The cross-graph handoff uses `{state.plan_session_id}` where the variable IS the session ID. The check `".session_id" not in resume_val` excluded the valid pattern `plan_session_id` because it lacks a dot prefix. Fix: broaden to `"session_id" not in resume_val`.

**Heuristic:** When introducing a new valid pattern that an existing lint rule doesn't anticipate, update the lint rule in the same commit. Lint rules encode assumptions — new patterns must update those assumptions, not work around them.

**Seed:** Could the linter infer variable types from state declarations (e.g., `plan_session_id: str` in YAML state) to distinguish "this IS a session ID" from "this is a CopilotResult with a session_id attribute"? Type-aware linting would catch more classes of resume expression errors.
