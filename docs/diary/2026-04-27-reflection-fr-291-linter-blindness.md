---

## 2026-04-27: FR-291 — Linter Blindness at the Custom Action Boundary

**Context:** Enforcing FR-291 (Phase 1 action wiring) — replacing 32 log stubs across dispatcher and pipeline FSM configs with real action types (bash_context, yamlgraph_async, git_commit, precommit). TDD cycle: 33 RED tests, all 50 GREEN after implementation. The tricky part wasn't the action code — it was the tooling gap.

**Trap:** **downstream_fix** — The FSM linter (`statemachine-lint`) hardcodes known action types in an allowlist. Custom actions loaded via `--actions-dir` at runtime are invisible to the linter, which reports E008 ("Unknown action type") for every custom action usage. The validator (`statemachine-validate`) had a similar gap: it flagged `sync_done` as an orphan event when two sequential actions in the same state emitted different events. The temptation was to patch the linter to accept custom types, but the real fix was simpler: scope lint tests to exclude E008/E012 (custom types and runtime context keys) while keeping structural checks (E001–E007) enforced.

**Heuristic:** **When tooling doesn't know your extension point, scope the gate — don't weaken the tool.** The linter is correct that `bash_context` isn't a builtin. The validator is correct that `sync_done` has no transition. Rather than teaching every tool about every extension, run the tool on the subset it understands and separately test what it can't see (the custom action module existence, class hierarchy, and behavior tests handle that layer).

**Evidence chain:**
- ActionLoader discovers `*_action.py` by naming convention and builds class names via `capitalize()` per word — `yamlgraph_async` becomes `YamlgraphAsyncAction`, not `YamlGraphAsyncAction`. This naming mismatch was caught by the ActionRegistration test, not by the linter.
- Combining `inbox_sync.sh` (bash) and topic-find (bash_context) into two sequential actions in one state caused the validator to flag `sync_done` as orphaned. Merging them into a single bash_context action resolved the structural issue and simplified the config.
- The pre-commit `ruff` gate caught S603/S607 (subprocess with partial path) on trusted commands (`pre-commit`, `git`). The noqa must go on the line with the literal array, not the `subprocess.run` line — ruff reports the error on the argument, not the function call.

**Seed:** The linter's E008 gap reveals a broader pattern: FSM configs with custom actions need a "plugin manifest" that declares available action types to static analysis tools. Could the `--actions-dir` directory include an `__actions__.yaml` registry that both the runtime loader and the linter consume? This would close the static/runtime gap without weakening either gate.
