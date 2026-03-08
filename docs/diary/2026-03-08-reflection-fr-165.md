## 2026-03-08: FR-165 — No-Silent-Fallback Lint Rule (W017)

**Context:** Added lint rule W017 that flags `on_error: skip` nodes in YAML graphs as silent fallback patterns. This enforces Commandment 6 ("Thou shalt bear witness of thy errors") at the linting stage, catching error-swallowing patterns before they reach production. The rule emits a warning with a suggestion to use `on_error: fallback` with an explicit fallback node instead.

**Trap:** plausible_wrong_answer — The `on_error: skip` directive is syntactically valid and the pipeline runs successfully, but the result silently omits failed node outputs. The pipeline produces a *plausible* answer that looks correct but is incomplete. This is the Scripture trap incarnate: "Silent fallback harder to catch than crash." The fix is not to ban error handling, but to demand *visible* error handling — a fallback node that explicitly handles the failure case rather than pretending it didn't happen.

**Heuristic:** When a framework provides a convenience shortcut that hides failure (skip, ignore, default-to-empty), add a lint rule that flags it. The shortcut is useful for prototyping but dangerous in production. The lint rule acts as the boundary between "I know this fails sometimes" (explicit fallback) and "I forgot this can fail" (silent skip). Enforcement at lint time is cheaper than debugging missing data in production traces.

**Seed:** Could W017 be extended to detect other silent-failure patterns beyond `on_error: skip` — for example, nodes with empty `fallback_value` fields, or router edges that silently default to a no-op path? A broader "silent failure detector" could surface an entire class of plausible-wrong-answer traps.
