# Confessions — noqa Registry

Every `# noqa` suppression in this codebase must be documented here.
Run `python scripts/noqa_coverage.py` to verify all suppressions are confessed.

## Format

Each confession must include:
- **CONF-XXX**: Unique identifier
- **File**: Path with line number (as markdown link)
- **Code**: Ruff/flake8 error code being suppressed
- **Sin**: Brief explanation of what the code does
- **Penance**: Why this is acceptable (or what would fix it)

---

## Scripts

### CONF-200
- **File**: [scripts/noqa_coverage.py](../scripts/noqa_coverage.py#L44)
- **Code**: E402
- **Sin**: Example pattern in regex documentation comment.
- **Penance**: This script documents noqa patterns; the examples are not real suppressions but show what the regex matches.

### CONF-201
- **File**: [scripts/noqa_coverage.py](../scripts/noqa_coverage.py#L45)
- **Code**: E402
- **Sin**: Example pattern in regex documentation comment.
- **Penance**: Same as CONF-200.

### CONF-202
- **File**: [scripts/noqa_coverage.py](../scripts/noqa_coverage.py#L46)
- **Code**: E402
- **Sin**: Example pattern in regex documentation comment.
- **Penance**: Same as CONF-200.

### CONF-203
- **File**: [scripts/noqa_coverage.py](../scripts/noqa_coverage.py#L46)
- **Code**: F401
- **Sin**: Example pattern in regex documentation comment (multi-code example).
- **Penance**: Same as CONF-200.

### CONF-204
- **File**: [scripts/noqa_coverage.py](../scripts/noqa_coverage.py#L47)
- **Code**: ALL
- **Sin**: Example pattern showing blanket noqa in documentation comment.
- **Penance**: Same as CONF-200.

### CONF-205
- **File**: [scripts/diary_rotate.py](../scripts/diary_rotate.py#L98)
- **Code**: S603
- **Sin**: `subprocess.run(["git", "add", ...])` flagged as untrusted input.
- **Penance**: Command and args are hardcoded; only file paths from `Path` objects are passed. No user input reaches the shell.

### CONF-206
- **File**: [scripts/diary_rotate.py](../scripts/diary_rotate.py#L36)
- **Code**: S603
- **Sin**: `git_add()` helper uses `subprocess.run(["git", "add", ...])` — S603 flags subprocess call with non-constant arguments.
- **Penance**: Arguments are `Path` objects from the diary folder; command is hardcoded `["git", "add"]`. No shell expansion, no user input.

### CONF-207
- **File**: [scripts/migrate_capabilities.py](../scripts/migrate_capabilities.py#L345)
- **Code**: E402
- **Sin**: Module-level import `from req_coverage import CAPABILITIES` appears after `sys.path.insert()` manipulation.
- **Penance**: The import must occur after sys.path is modified to find `req_coverage.py` in the scripts directory. This is standard Python pattern for runtime path manipulation.

---

## Framework Code

Framework suppressions require elevated scrutiny. These live in `yamlgraph/`.

### CONF-001
- **File**: [yamlgraph/linter/checks.py](../yamlgraph/linter/checks.py#L108)
- **Code**: C901 (function too complex)
- **Sin**: `check_state_declarations` has high cyclomatic complexity due to multiple validation passes over graph nodes, prompts, and tools.
- **Penance**: Decomposing would scatter cohesive validation logic across helper functions without meaningful abstraction gain. The function is linear and readable despite branching.

### CONF-002
- **File**: [yamlgraph/utils/token_tracker.py](../yamlgraph/utils/token_tracker.py#L55)
- **Code**: ARG002 (unused method argument)
- **Sin**: `kwargs` parameter unused in callback handler.
- **Penance**: Required by LangChain callback interface (`BaseCallbackHandler.on_llm_end`). Cannot remove without breaking signature compatibility.

### ~~CONF-005~~ (RESOLVED by FR-223)
- **Resolved**: `create_node_function` decomposed into `resolve_llm_node_config()`, `_apply_verification()`, `_resolve_route()`, `_handle_error()`. C901 now passes without suppression.

### ~~CONF-006~~ (RESOLVED by FR-223)
- **Resolved**: `node_fn` now an orchestrator calling extracted phases. C901 now passes without suppression.

### CONF-007
- **File**: [yamlgraph/tools/agent.py](../yamlgraph/tools/agent.py#L88)
- **Code**: C901 (cognitive complexity 19 > 15)
- **Sin**: `create_agent_node` assembles agent with tool binding, prompt loading, and LLM configuration in one function.
- **Penance**: Agent node factory has inherent setup complexity. Decomposition deferred to a future FR.

### CONF-008
- **File**: [yamlgraph/linter/checks.py](../yamlgraph/linter/checks.py#L108)
- **Code**: C901 (cognitive complexity 16 > 15)
- **Sin**: `check_state_declarations` traverses graph YAML, resolves prompt references, and extracts template variables.
- **Penance**: Barely above threshold (16 vs 15). Will be addressed when linter checks are decomposed.

### CONF-003
- **File**: [yamlgraph/streaming_events.py](../yamlgraph/streaming_events.py#L56)
- **Code**: ANN001 (missing type annotation for function argument)
- **Sin**: `state` parameter in `_get_interrupt_payload()` has no type annotation.
- **Penance**: The type is `langgraph.pregel.types.StateSnapshot` which is a private API. Importing it would couple us to LangGraph internals. The function only accesses `.tasks` and `.interrupts` attributes, which are stable across versions.

### CONF-004
- **File**: [yamlgraph/a2a/server.py](../yamlgraph/a2a/server.py#L43)
- **Code**: F401
- **Sin**: Re-imports from `a2a_message` appear unused in `a2a_server.py`.
- **Penance**: These are public re-exports for backward compatibility — tests and external consumers import from `yamlgraph.a2a.server`. The actual logic lives in `yamlgraph.a2a.message` after the module split to stay under 450 lines.

### CONF-005
- **File**: [yamlgraph/cli/__init__.py](../yamlgraph/cli/__init__.py#L317)
- **Code**: S104
- **Sin**: A2A server CLI default host is `0.0.0.0` (binds to all interfaces).
- **Penance**: Intentional for server CLI commands. Users override via `--host`. Binding to all interfaces is the standard default for development servers.

### CONF-006
- **File**: [yamlgraph/cli/a2a_commands.py](../yamlgraph/cli/a2a_commands.py#L58)
- **Code**: S104
- **Sin**: Fallback host `0.0.0.0` when `--host` arg is not present.
- **Penance**: Same as CONF-005 — intentional default for A2A server command.

### CONF-007
- **File**: [yamlgraph/tools/shell.py](../yamlgraph/tools/shell.py#L129)
- **Code**: S602
- **Sin**: `subprocess.run(..., shell=True)` for shell command execution.
- **Penance**: `shell=True` is required for command templates with pipes/redirects. All user variables are sanitized via `shlex.quote()` in `sanitize_variables()` before substitution. The command template itself comes from trusted YAML configuration, not user input.

### CONF-008
- **File**: [yamlgraph/node_factory/copilot_node.py](../yamlgraph/node_factory/copilot_node.py#L371)
- **Code**: S603
- **Sin**: `subprocess.run(cmd, ...)` flagged as untrusted input.
- **Penance**: The `cmd` list is built entirely from hardcoded strings (`"gh"`, `"copilot"`, `"suggest"`) plus internal config flags and validated graph metadata (model name, timeout). No user input reaches the command arguments.

### CONF-303
- **File**: [yamlgraph/node_factory/copilot_runtime.py](../yamlgraph/node_factory/copilot_runtime.py#L167)
- **Code**: S603
- **Sin**: `subprocess.run(cmd, ...)` in extracted copilot CLI runtime helper is flagged as untrusted input.
- **Penance**: Command is built as a list (no shell=True), with fixed executable/flags plus validated node configuration (`model`, `resume`, `continue_session`, `timeout`). No raw user input is interpolated into shell commands.

### CONF-009
- **File**: [yamlgraph/utils/template.py](../yamlgraph/utils/template.py#L48)
- **Code**: S701
- **Sin**: Jinja2 `Environment()` without `autoescape=True`.
- **Penance**: Used for YAML prompt template variable extraction, not HTML rendering. Autoescape would corrupt prompt text by escaping `<`, `>`, `&` characters. No web output is generated from this code path.

### CONF-010
- **File**: [yamlgraph/executor_base.py](../yamlgraph/executor_base.py#L175)
- **Code**: C901 (function too complex)
- **Sin**: `prepare_messages` has high cyclomatic complexity (14 > 15 after refactoring, but still flagged) due to branching logic for different system field types (scalar vs. list vs. system_segments) and provider-specific message formatting.
- **Penance**: Working functionality for FR-276 prompt caching. Complexity reduced from D (24) to C (14) through helper function extraction. The function orchestrates message preparation across multiple input formats and providers, making some complexity unavoidable.

### CONF-035
- **File**: [yamlgraph/utils/worktree_helpers.py](../yamlgraph/utils/worktree_helpers.py#L97)
- **Code**: S607
- **Sin**: `["git", "diff", "--name-only"]` uses partial executable path.
- **Penance**: `git` is expected on PATH in all development environments. Using absolute path would break portability across OS/distro.

### CONF-036
- **File**: [yamlgraph/utils/worktree_helpers.py](../yamlgraph/utils/worktree_helpers.py#L108)
- **Code**: S607
- **Sin**: `["git", "diff", "--cached", "--name-only"]` uses partial executable path.
- **Penance**: Same as CONF-035.

### CONF-037
- **File**: [yamlgraph/utils/worktree_helpers.py](../yamlgraph/utils/worktree_helpers.py#L96)
- **Code**: S603
- **Sin**: `subprocess.run()` called with list argument flagged as untrusted input.
- **Penance**: Command list is hardcoded `["git", "diff", "--name-only"]` — no user input reaches arguments. Used to detect unstaged changes before worktree operations.

### CONF-038
- **File**: [yamlgraph/utils/worktree_helpers.py](../yamlgraph/utils/worktree_helpers.py#L107)
- **Code**: S603
- **Sin**: `subprocess.run()` called with list argument flagged as untrusted input.
- **Penance**: Same as CONF-037 — hardcoded `["git", "diff", "--cached", "--name-only"]` for staged change detection.

### CONF-039
- **File**: [yamlgraph/node_factory/llm_nodes.py](../yamlgraph/node_factory/llm_nodes.py#L301)
- **Code**: C901 (cognitive complexity > 15)
- **Sin**: Nested `node_fn` still orchestrates loop guards, requirements checks, execution, verification, routing, and error dispatch in one closure.
- **Penance**: FR-223 already extracted core helpers (`_apply_verification`, `_resolve_route`, `_handle_error`), and FR-632 extracted `_normalize_result`, but closure structure keeps orchestration complexity above threshold. Suppressed while follow-up decomposition lands.

### CONF-040
- **File**: [yamlgraph/utils/timing_tracker.py](../yamlgraph/utils/timing_tracker.py#L50)
- **Code**: ARG002 (unused method argument)
- **Sin**: `serialized` parameter unused in `on_llm_start` callback.
- **Penance**: Required by LangChain callback interface (`BaseCallbackHandler.on_llm_start`). Cannot remove without breaking signature compatibility.

### CONF-041
- **File**: [yamlgraph/utils/timing_tracker.py](../yamlgraph/utils/timing_tracker.py#L51)
- **Code**: ARG002 (unused method argument)
- **Sin**: `prompts` parameter unused in `on_llm_start` callback.
- **Penance**: Same as CONF-040 — required by LangChain callback interface.

### CONF-042
- **File**: [yamlgraph/utils/timing_tracker.py](../yamlgraph/utils/timing_tracker.py#L52)
- **Code**: ARG002 (unused method argument)
- **Sin**: `kwargs` parameter unused in `on_llm_start` callback.
- **Penance**: Same as CONF-040 — required by LangChain callback interface.

### CONF-043
- **File**: [yamlgraph/utils/timing_tracker.py](../yamlgraph/utils/timing_tracker.py#L57)
- **Code**: ARG002 (unused method argument)
- **Sin**: `kwargs` parameter unused in `on_llm_end` callback.
- **Penance**: Same as CONF-002 — required by LangChain callback interface (`BaseCallbackHandler.on_llm_end`).

### CONF-044
- **File**: [yamlgraph/linter/checks.py](../yamlgraph/linter/checks.py#L108)
- **Code**: C901 (too complex)
- **Sin**: `check_state_declarations` function exceeds cyclomatic complexity threshold.
- **Penance**: The function must cross-reference prompt variables, tool inputs, and state declarations across the graph. Splitting would scatter related validation logic across multiple functions with no clarity gain. The complexity is inherent to the validation domain.

### CONF-045
- **File**: [yamlgraph/utils/worktree_helpers.py](../yamlgraph/utils/worktree_helpers.py#L249)
- **Code**: S603
- **Sin**: `subprocess.run()` called with list argument flagged as untrusted input.
- **Penance**: Command is `[sys.executable, "-c", f"import {package}"]` where `package` is a caller-provided string. Used only internally by worktree cleanup to probe import health. No user-facing input reaches this path.

### CONF-046
- **File**: [yamlgraph/utils/worktree_helpers.py](../yamlgraph/utils/worktree_helpers.py#L250)
- **Code**: S607
- **Sin**: `sys.executable` is used as the executable path rather than an absolute path.
- **Penance**: `sys.executable` is the canonical way to reference the running interpreter, ensuring venv isolation. It is already an absolute path at runtime.

---

## Test Code

Test suppressions are acceptable when they enable testing patterns that conflict with lint rules.

### CONF-010
- **File**: [tests/unit/test_legacy_cli_removed.py](../tests/unit/test_legacy_cli_removed.py#L19)
- **Code**: F401 (imported but unused)
- **Sin**: Import inside `pytest.raises(ImportError)` block appears unused.
- **Penance**: The import IS the test — we're asserting it raises ImportError. F401 cannot understand this pattern.

### CONF-011
- **File**: [tests/unit/test_legacy_cli_removed.py](../tests/unit/test_legacy_cli_removed.py#L25)
- **Code**: F401
- **Sin**: Same as CONF-010 — import inside `pytest.raises(ImportError)`.
- **Penance**: Intentional import failure test.

### CONF-012
- **File**: [tests/unit/test_legacy_cli_removed.py](../tests/unit/test_legacy_cli_removed.py#L42)
- **Code**: F401
- **Sin**: Same as CONF-010 — import inside `pytest.raises(ImportError)`.
- **Penance**: Intentional import failure test.

### CONF-013
- **File**: [tests/unit/test_legacy_cli_removed.py](../tests/unit/test_legacy_cli_removed.py#L52)
- **Code**: F401
- **Sin**: Same as CONF-010 — import inside `pytest.raises(ImportError)`.
- **Penance**: Intentional import failure test.

### CONF-014
- **File**: [tests/unit/test_mcp_server.py](../tests/unit/test_mcp_server.py#L14)
- **Code**: E402 (module level import not at top of file)
- **Sin**: Import after `pytest.importorskip("mcp")`.
- **Penance**: Skip marker must execute before imports to skip when mcp not installed.

### CONF-015
- **File**: [tests/unit/test_book_translator_quality.py](../tests/unit/test_book_translator_quality.py#L12)
- **Code**: E402
- **Sin**: Import after `sys.path.insert` for example module.
- **Penance**: Example tests must modify sys.path to import local modules. Standard pattern for testing standalone examples.

### CONF-016
- **File**: [tests/unit/test_book_translator_assembler.py](../tests/unit/test_book_translator_assembler.py#L12)
- **Code**: E402
- **Sin**: Import after `sys.path.insert` for example module.
- **Penance**: Same as CONF-015.

### CONF-017
- **File**: [tests/unit/test_book_translator_glossary.py](../tests/unit/test_book_translator_glossary.py#L12)
- **Code**: E402
- **Sin**: Import after `sys.path.insert` for example module.
- **Penance**: Same as CONF-015.

### CONF-018
- **File**: [tests/unit/test_book_translator_splitter.py](../tests/unit/test_book_translator_splitter.py#L12)
- **Code**: E402
- **Sin**: Import after `sys.path.insert` for example module.
- **Penance**: Same as CONF-015.

### CONF-019
- **File**: [tests/unit/test_req_coverage_ast.py](../tests/unit/test_req_coverage_ast.py#L20)
- **Code**: E402
- **Sin**: Import after `sys.path.insert` for scripts module.
- **Penance**: Test file needs to import from scripts/ which is not a package.

### CONF-020
- **File**: [tests/unit/test_fr027_execution_safety.py](../tests/unit/test_fr027_execution_safety.py#L805)
- **Code**: E731 (do not assign a lambda expression)
- **Sin**: Lambda assigned to variable for signal handler test.
- **Penance**: Lambda is cleaner than def for trivial no-op handler in test fixture. Accepted for test code.

### CONF-021
- **File**: [tests/unit/test_tavily_rag.py](../tests/unit/test_tavily_rag.py#L86)
- **Code**: F401
- **Sin**: Import `tavily_retrieve` after `sys.path.insert` appears unused (used via module reload).
- **Penance**: Import triggers module loading for test; removing it breaks the test.

### CONF-022
- **File**: [tests/unit/test_tavily_rag.py](../tests/unit/test_tavily_rag.py#L129)
- **Code**: F401
- **Sin**: Same as CONF-021 — import for domain-scoping test.
- **Penance**: Same as CONF-021.

### CONF-023
- **File**: [tests/unit/test_tavily_rag.py](../tests/unit/test_tavily_rag.py#L163)
- **Code**: F401
- **Sin**: Same as CONF-021 — import for no-domain fallback test.
- **Penance**: Same as CONF-021.

### CONF-024
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L22)
- **Code**: E402
- **Sin**: noqa pattern inside test fixture string — testing the noqa detector.
- **Penance**: Test fixture strings must contain realistic patterns to test detection.

### CONF-025
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L32)
- **Code**: F401
- **Sin**: Same as CONF-024 — noqa pattern inside test fixture string.
- **Penance**: Same as CONF-024.

### CONF-026
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L32)
- **Code**: F403
- **Sin**: Same as CONF-024 — noqa pattern inside test fixture string.
- **Penance**: Same as CONF-024.

### CONF-027
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L44)
- **Code**: ALL
- **Sin**: Same as CONF-024 — blanket noqa pattern inside test fixture string.
- **Penance**: Same as CONF-024.

### CONF-028
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L55)
- **Code**: E402
- **Sin**: Same as CONF-024 — noqa pattern inside test fixture string.
- **Penance**: Same as CONF-024.

### CONF-029
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L57)
- **Code**: F401
- **Sin**: Same as CONF-024 — noqa pattern inside test fixture string.
- **Penance**: Same as CONF-024.

### CONF-030
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L70)
- **Code**: E402
- **Sin**: Same as CONF-024 — noqa pattern inside test fixture string.
- **Penance**: Same as CONF-024.

### CONF-031
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L137)
- **Code**: E402
- **Sin**: Same as CONF-024 — noqa pattern inside confessions test fixture.
- **Penance**: Same as CONF-024.

### CONF-032
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L166)
- **Code**: E402
- **Sin**: Same as CONF-024 — noqa pattern inside documented entry test fixture.
- **Penance**: Same as CONF-024.

### CONF-033
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L190)
- **Code**: E402
- **Sin**: Same as CONF-024 — noqa pattern inside documented entry test fixture.
- **Penance**: Same as CONF-024.

### CONF-034
- **File**: [tests/unit/test_discovery.py](../tests/unit/test_discovery.py#L36)
- **Code**: F841
- **Sin**: `mcp` variable assigned but never used after `importorskip`.
- **Penance**: `pytest.importorskip("mcp")` is used as an import guard — the test must be skipped if `mcp` is not installed. The returned module is intentionally unused; the call's side effect (skip or proceed) is the purpose.

### CONF-035
- **File**: [tests/unit/test_a2a_commands.py](../tests/unit/test_a2a_commands.py#L130)
- **Code**: S104
- **Sin**: Hardcoded bind-all address `0.0.0.0` in test fixture `argparse.Namespace`.
- **Penance**: Test data simulating CLI arguments for the A2A serve command. Not a real network binding — the server is fully mocked. Required to verify the argument-passing path.

### CONF-036
- **File**: [tests/unit/test_a2a_message.py](../tests/unit/test_a2a_message.py#L489)
- **Code**: S104
- **Sin**: Hardcoded bind-all address `0.0.0.0` in `build_agent_card` test call.
- **Penance**: Test data verifying Agent Card URL construction. No actual network socket is opened — the function only builds a data structure. Required to test the host-to-URL mapping.

### CONF-037
- **File**: [tests/unit/test_mcp_typed_tools.py](../tests/unit/test_mcp_typed_tools.py#L21)
- **Code**: E402
- **Sin**: Import `mcp.types` after `pytest.importorskip("mcp")` guard.
- **Penance**: Same pattern as CONF-034. The `mcp` package is an optional dependency; `importorskip` must execute before any `mcp` imports to skip the test file gracefully when the package is not installed.

### CONF-047
- **File**: [tests/unit/test_fr321_yamlgraph_async_subprocess_exec.py](../tests/unit/test_fr321_yamlgraph_async_subprocess_exec.py#L12)
- **Code**: E402
- **Sin**: Import `YamlgraphAsyncAction` after `pytest.importorskip("statemachine_engine")` guard.
- **Penance**: Same pattern as CONF-037. The `statemachine_engine` package is a local dependency not installed in CI; `importorskip` must execute before the action import to skip gracefully.

### CONF-048
- **File**: [yamlgraph/tools/agent.py](../yamlgraph/tools/agent.py#L142)
- **Code**: C901
- **Sin**: `create_agent_node` has high cyclomatic complexity due to tool registration loop, LLM config resolution, multi-turn message handling, agent iteration loop with tool calls, and structured output extraction.
- **Penance**: The function is a factory that builds a closure capturing configuration. The inner `node_fn` orchestrates the agent loop which is inherently sequential and branching. Splitting further would scatter the closure's captured variables across multiple functions with no clarity gain.

### CONF-049
- **File**: [yamlgraph/cli/__init__.py](../yamlgraph/cli/__init__.py#L366)
- **Code**: S104
- **Sin**: Binding A2A server to `0.0.0.0` (all interfaces) as default.
- **Penance**: A2A server is a development tool that must be network-accessible for agent-to-agent communication. The default matches standard server practice (FastAPI, uvicorn). Production deployments control binding via `--host` flag.

### CONF-050
- **File**: [tests/unit/test_fr651_654_worldgen_improvements.py](../tests/unit/test_fr651_654_worldgen_improvements.py#L26)
- **Code**: ANN202
- **Sin**: Missing return type annotation on `_load()` helper.
- **Penance**: Same pattern as CONF-037 et al. Returns dynamically-loaded module whose type is `types.ModuleType` but annotating gains nothing in test helper context.

### CONF-051
- **File**: [tests/integration/conftest.py](../tests/integration/conftest.py#L42)
- **Code**: F401
- **Sin**: `import yamlgraph.config` with no name used from it.
- **Penance**: The import is executed for its module-level side effect — dotenv upward-search loading of `.env` — so the readiness probe checks credential presence AFTER the same boundary the tests themselves cross (FR-801 judgement R-2). Binding a name would be a lie about usage.

### CONF-052
- **File**: [tests/integration/test_fr801_readiness_preflight.py](../tests/integration/test_fr801_readiness_preflight.py#L32)
- **Code**: F401
- **Sin**: `import yamlgraph.config` with no name used from it.
- **Penance**: Same side-effect idiom as CONF-051, in the witness: dotenv must already be loaded before `monkeypatch.delenv` so the absent-key path is proven absent *after* dotenv, matching the conftest probe's boundary semantics.

### CONF-301
- **File**: [tests/unit/test_fr346_fsm_bridge_shared_module_red.py](../tests/unit/test_fr346_fsm_bridge_shared_module_red.py#L19)
- **Code**: PLC0415
- **Sin**: Import from `yamlgraph.utils.fsm` inside the test function.
- **Penance**: The test is explicitly validating package-level importability as an acceptance criterion. Keeping the import inside the test body ensures evaluation happens at assertion time and avoids module-import side effects during test collection.

### CONF-302
- **File**: [yamlgraph/utils/fsm/event_sender.py](../yamlgraph/utils/fsm/event_sender.py#L13)
- **Code**: S108
- **Sin**: Hardcoded `/tmp/statemachine-control` path.
- **Penance**: This is the statemachine-engine's AF_UNIX socket convention — not a temp file vulnerability. The engine binds to `/tmp/statemachine-control-{name}.sock` and all clients must match.

---

## Example Code

Example runner scripts frequently need sys.path manipulation to import yamlgraph.
These are E402 suppressions and are acceptable as "glue code" patterns.

### CONF-100
- **File**: [examples/beautify/run.py](../examples/beautify/run.py#L17)
- **Code**: E402
- **Sin**: Import after `sys.path.insert`.
- **Penance**: Runner script pattern — must set up path before imports.

### CONF-101
- **File**: [examples/daily_digest/run_digest.py](../examples/daily_digest/run_digest.py#L22)
- **Code**: E402
- **Sin**: Import after path/env setup.
- **Penance**: Runner script pattern.

### CONF-102
- **File**: [examples/daily_digest/api/app.py](../examples/daily_digest/api/app.py#L19)
- **Code**: E402
- **Sin**: FastAPI imports after sys.path setup.
- **Penance**: Runner script pattern (web server entry point).

### CONF-103
- **File**: [examples/daily_digest/api/app.py](../examples/daily_digest/api/app.py#L27)
- **Code**: E402
- **Sin**: Security imports after sys.path setup.
- **Penance**: Same as CONF-102.

### CONF-104
- **File**: [examples/daily_digest/api/app.py](../examples/daily_digest/api/app.py#L28)
- **Code**: E402
- **Sin**: Pydantic import after sys.path setup.
- **Penance**: Same as CONF-102.

### CONF-105
- **File**: [examples/daily_digest/api/app.py](../examples/daily_digest/api/app.py#L29)
- **Code**: E402
- **Sin**: slowapi import after sys.path setup.
- **Penance**: Same as CONF-102.

### CONF-106
- **File**: [examples/daily_digest/api/app.py](../examples/daily_digest/api/app.py#L30)
- **Code**: E402
- **Sin**: slowapi errors import after sys.path setup.
- **Penance**: Same as CONF-102.

### CONF-107
- **File**: [examples/daily_digest/api/app.py](../examples/daily_digest/api/app.py#L31)
- **Code**: E402
- **Sin**: slowapi util import after sys.path setup.
- **Penance**: Same as CONF-102.

### CONF-108
- **File**: [examples/daily_digest/api/app.py](../examples/daily_digest/api/app.py#L33)
- **Code**: E402
- **Sin**: yamlgraph import after sys.path setup.
- **Penance**: Same as CONF-102.

### CONF-110
- **File**: [examples/demos/interview/demo_async_executor.py](../examples/demos/interview/demo_async_executor.py#L32)
- **Code**: E402
- **Sin**: langgraph import after sys.path setup.
- **Penance**: Demo script pattern.

### CONF-111
- **File**: [examples/demos/interview/demo_async_executor.py](../examples/demos/interview/demo_async_executor.py#L33)
- **Code**: E402
- **Sin**: Command import after sys.path setup.
- **Penance**: Demo script pattern.

### CONF-112
- **File**: [examples/demos/interview/demo_async_executor.py](../examples/demos/interview/demo_async_executor.py#L35)
- **Code**: E402
- **Sin**: yamlgraph import after sys.path setup.
- **Penance**: Demo script pattern.

### CONF-113
- **File**: [examples/demos/interview/run_interview_demo.py](../examples/demos/interview/run_interview_demo.py#L22)
- **Code**: E402
- **Sin**: Command import after sys.path setup.
- **Penance**: Demo script pattern.

### CONF-114
- **File**: [examples/demos/interview/run_interview_demo.py](../examples/demos/interview/run_interview_demo.py#L24)
- **Code**: E402
- **Sin**: yamlgraph import after sys.path setup.
- **Penance**: Demo script pattern.

### CONF-115
- **File**: [examples/demos/interview/demo_interview_e2e.py](../examples/demos/interview/demo_interview_e2e.py#L26)
- **Code**: E402
- **Sin**: Command import after sys.path setup.
- **Penance**: Demo script pattern.

### CONF-116
- **File**: [examples/demos/interview/demo_interview_e2e.py](../examples/demos/interview/demo_interview_e2e.py#L28)
- **Code**: E402
- **Sin**: yamlgraph import after sys.path setup.
- **Penance**: Demo script pattern.

### CONF-117
- **File**: [examples/demos/interrupt/test_subgraph_interrupt.py](../examples/demos/interrupt/test_subgraph_interrupt.py#L41)
- **Code**: E402
- **Sin**: Command import after sys.path setup.
- **Penance**: Demo script pattern.

### CONF-118
- **File**: [examples/demos/interrupt/test_subgraph_interrupt.py](../examples/demos/interrupt/test_subgraph_interrupt.py#L43)
- **Code**: E402
- **Sin**: yamlgraph import after sys.path setup.
- **Penance**: Demo script pattern.

### CONF-120
- **File**: [examples/yamlgraph_gen/run_generator.py](../examples/yamlgraph_gen/run_generator.py#L25)
- **Code**: E402
- **Sin**: yamlgraph import after sys.path setup.
- **Penance**: Runner script pattern.

### CONF-121
- **File**: [examples/yamlgraph_gen/run_generator.py](../examples/yamlgraph_gen/run_generator.py#L26)
- **Code**: E402
- **Sin**: linter import after sys.path setup.
- **Penance**: Runner script pattern.

### CONF-122
- **File**: [examples/demos/tavily_rag/nodes/tavily_retrieve.py](../examples/demos/tavily_rag/nodes/tavily_retrieve.py#L50)
- **Code**: F811
- **Sin**: Redefinition of `TavilySearchResults` in except branch (imports real or creates stub).
- **Penance**: Graceful degradation pattern — function raises clear error if package missing rather than crashing on import.

### CONF-124
- **File**: [examples/demos/session-test/run_demo.py](../examples/demos/session-test/run_demo.py#L24)
- **Code**: E402
- **Sin**: Import `Command` from langgraph after `load_dotenv()` call.
- **Penance**: Environment must be loaded before yamlgraph imports that read API keys. Standard pattern matching interview demo and other HITL examples.

### CONF-125
- **File**: [examples/demos/session-test/run_demo.py](../examples/demos/session-test/run_demo.py#L26)
- **Code**: E402
- **Sin**: Import yamlgraph modules after `load_dotenv()` call.
- **Penance**: Same as CONF-124 — env vars must be set before yamlgraph imports initialize LLM clients.

### CONF-126
- **File**: [vulture_whitelist.py](../vulture_whitelist.py#L4)
- **Code**: F401
- **Sin**: Import `worktree_helpers` functions without using them in Python.
- **Penance**: Vulture's standard false-positive suppression mechanism. These functions are invoked via `python3 -c` in `scripts/enforce_worktree.sh`, invisible to static analysis. The import makes them visible to Vulture.

### CONF-127
- **File**: [tests/unit/test_llm_factory.py](../tests/unit/test_llm_factory.py#L275)
- **Code**: ARG001 (unused function argument)
- **Sin**: `capture_env(**kwargs)` side-effect helper ignores kwargs; it only captures `os.environ` state.
- **Penance**: The `**kwargs` signature is required to match `ChatGoogleGenerativeAI`'s constructor call signature. The argument is intentionally unused.

### CONF-128
- **File**: [tests/unit/test_llm_factory.py](../tests/unit/test_llm_factory.py#L346)
- **Code**: ARG001
- **Sin**: Same as CONF-127 — `capture_env(**kwargs)` ignores kwargs to capture env snapshot.
- **Penance**: Same as CONF-127.

### CONF-129
- **File**: [tests/unit/test_llm_factory.py](../tests/unit/test_llm_factory.py#L371)
- **Code**: SLF001 (private member accessed)
- **Sin**: Test accesses `llm_mod._VERTEX_CONSTRUCT_LOCK` to verify it exists and is a `threading.Lock`.
- **Penance**: The lock is a module-level private attribute deliberately tested as part of FR-227 acceptance criteria. Test access to private implementation details is an accepted pattern here.

### CONF-130
- **File**: [tests/unit/test_llm_factory.py](../tests/unit/test_llm_factory.py#L389)
- **Code**: SLF001
- **Sin**: Test invokes `llm_mod._masked_env(key)` to verify the context manager's remove-and-restore behavior.
- **Penance**: `_masked_env` is a private implementation helper mandated by FR-227; direct testing of its contract is required.

### CONF-131
- **File**: [tests/unit/test_llm_factory.py](../tests/unit/test_llm_factory.py#L409)
- **Code**: SLF001
- **Sin**: Same as CONF-130 — invokes `llm_mod._masked_env` inside `pytest.raises` to verify restore-on-exception.
- **Penance**: Same as CONF-130.

### CONF-132
- **File**: [tests/unit/test_llm_factory.py](../tests/unit/test_llm_factory.py#L425)
- **Code**: ARG001
- **Sin**: Same as CONF-127 — `capture_env(**kwargs)` ignores kwargs to capture env snapshot.
- **Penance**: Same as CONF-127.

### CONF-133
- **File**: [tests/unit/test_llm_factory.py](../tests/unit/test_llm_factory.py#L278)
- **Code**: ARG001
- **Sin**: Same as CONF-127 — `capture_env(**kwargs)` ignores kwargs to capture env snapshot.
- **Penance**: Same as CONF-127.

### CONF-134
- **File**: [tests/unit/test_llm_factory.py](../tests/unit/test_llm_factory.py#L349)
- **Code**: ARG001
- **Sin**: Same as CONF-127 — `capture_env(**kwargs)` ignores kwargs to capture env snapshot.
- **Penance**: Same as CONF-127.

### CONF-135
- **File**: [tests/unit/test_llm_factory.py](../tests/unit/test_llm_factory.py#L374)
- **Code**: SLF001
- **Sin**: Accesses `llm_mod._VERTEX_CONSTRUCT_LOCK` directly in test.
- **Penance**: Test validates the module-level lock exists and is the correct type. No public API to verify this.

### CONF-136
- **File**: [tests/unit/test_llm_factory.py](../tests/unit/test_llm_factory.py#L392)
- **Code**: SLF001
- **Sin**: Calls `llm_mod._masked_env()` directly in test.
- **Penance**: Tests the private context manager in isolation. No public API wrapping it.

### CONF-137
- **File**: [tests/unit/test_llm_factory.py](../tests/unit/test_llm_factory.py#L412)
- **Code**: SLF001
- **Sin**: Same as CONF-136 — calls `llm_mod._masked_env()` inside `pytest.raises`.
- **Penance**: Same as CONF-136.

### CONF-138
- **File**: [tests/unit/test_llm_factory.py](../tests/unit/test_llm_factory.py#L428)
- **Code**: ARG001
- **Sin**: Same as CONF-127 — `capture_env(**kwargs)` ignores kwargs to capture env snapshot.
- **Penance**: Same as CONF-127.

### CONF-139
- **File**: [tests/unit/test_llm_factory.py](../tests/unit/test_llm_factory.py#L460)
- **Code**: ARG001
- **Sin**: `capture_env(**kwargs)` ignores kwargs to capture env snapshot for FR-229 test.
- **Penance**: Same as CONF-127 — `ChatGoogleGenerativeAI` is constructed with kwargs; the test only needs to inspect `os.environ`, not the constructor arguments.

### CONF-140
- **File**: [tests/unit/test_llm_factory.py](../tests/unit/test_llm_factory.py#L514)
- **Code**: ARG001
- **Sin**: Same as CONF-139 — `capture_env(**kwargs)` in ADC mode test ignores kwargs.
- **Penance**: Same as CONF-139.

### CONF-141
- **File**: [examples/demos/diary_index/tools.py](../examples/demos/diary_index/tools.py#L19)
- **Code**: ARG001
- **Sin**: `list_diary_files(state)` ignores the `state` parameter — the function needs no input state.
- **Penance**: YAMLGraph python-node signature requires a `state: dict` parameter. The function scans the filesystem directly, so `state` is unused but mandatory for the node contract.

### CONF-142
- **File**: [tests/unit/test_fr293_pytest_xdist.py](../tests/unit/test_fr293_pytest_xdist.py#L15)
- **Code**: F401
- **Sin**: `import xdist` appears unused — the module is imported but not referenced.
- **Penance**: The import IS the test — we're asserting that xdist is importable (installed). F401 cannot understand this pattern.

### CONF-144
- **File**: [examples/plot_modeller/run.py](../examples/plot_modeller/run.py#L37)
- **Code**: E402
- **Sin**: `from nodes.tools import load_glosses, load_glosses_with_kinds, load_synopsis` appears after `sys.path` manipulation.
- **Penance**: The import must follow the `sys.path.insert` that makes the `nodes` package discoverable. This is the standard pattern for standalone example runners that aren't installed packages.

### CONF-145
- **File**: [examples/novel_fandom/nodes/persist_pages.py](../examples/novel_fandom/nodes/persist_pages.py#L170)
- **Code**: BLE001
- **Sin**: Broad `except Exception` in validation fallback.
- **Penance**: FR-649 design decision: persist work product even when Pydantic validation fails. The broad catch is intentional — any validation error (type mismatch, missing field, extra field) should trigger the warning-and-persist fallback, not crash the pipeline. The exception is logged with full context.

### CONF-146
- **File**: [examples/demos/self-portrait/extract.py](../examples/demos/self-portrait/extract.py#L84)
- **Code**: S608
- **Sin**: `PRAGMA table_info({table})` interpolates a table name into SQL.
- **Penance**: FR-782. `table` is never user input — every call site passes a literal from the module's own `REQUIRED_TABLES` / fixed table names (`ne_records`, `tp_records`, `loc_records`, `significant_contacts`, `sources`). SQLite forbids parameter binding for identifiers, so PRAGMA introspection (the schema-drift assertion this example depends on) has no parameterized form. The connection is read-only URI mode, so even a hypothetical injection could not write.

### CONF-147
- **File**: [examples/demos/self-portrait/extract.py](../examples/demos/self-portrait/extract.py#L107)
- **Code**: S608
- **Sin**: Entity query concatenates an optional-column fragment (`language` or `NULL AS language`) into the SELECT list.
- **Penance**: FR-782. The fragment comes from `_optional()`, which chooses between two module-literal strings based on whether the column exists — no external value reaches the SQL. The row limit is bound as a parameter. Read-only connection. This is the assert-and-adapt boundary that lets missing optional columns degrade to `None` instead of failing the run.

### CONF-148
- **File**: [examples/demos/self-portrait/extract.py](../examples/demos/self-portrait/extract.py#L152)
- **Code**: S608
- **Sin**: Location query interpolates the optional `clp_country` fragment.
- **Penance**: FR-782. Same mechanism and same guarantees as CONF-147 — literal fragment chosen by `_optional()`, read-only connection, no user input.

### CONF-149
- **File**: [examples/demos/self-portrait/extract.py](../examples/demos/self-portrait/extract.py#L170)
- **Code**: S608
- **Sin**: Significant-contacts query interpolates three optional-column fragments.
- **Penance**: FR-782. Same mechanism and same guarantees as CONF-147 — `significant_contacts` varies most across macOS versions, so all three columns are optional-by-construction.

### CONF-150
- **File**: [examples/demos/self-portrait/extract.py](../examples/demos/self-portrait/extract.py#L193)
- **Code**: S608
- **Sin**: Provenance query interpolates the optional `record_count` fragment into both the SELECT list and the ORDER BY.
- **Penance**: FR-782. Same mechanism and same guarantees as CONF-147.

### CONF-151
- **File**: [examples/demos/self-portrait/wikidata.py](../examples/demos/self-portrait/wikidata.py#L62)
- **Code**: S310
- **Sin**: `urllib.request.Request(url)` flagged for possible non-HTTP(S) scheme.
- **Penance**: FR-782. `url` is built from the module constant `WIKIDATA_API` (`https://www.wikidata.org/w/api.php`) plus `urlencode`d Q-IDs; the scheme is fixed and no caller supplies a URL. Stdlib `urllib` is used deliberately — the judgement (C-4/C-7) forbids adding an undeclared HTTP dependency for this example.

### CONF-152
- **File**: [examples/demos/self-portrait/wikidata.py](../examples/demos/self-portrait/wikidata.py#L65)
- **Code**: S310
- **Sin**: `urllib.request.urlopen(request)` flagged for possible non-HTTP(S) scheme.
- **Penance**: FR-782. Opens the `Request` built two lines above from the fixed HTTPS constant (CONF-151); a timeout is set and failures degrade to bare Q-IDs rather than propagating.

### CONF-306
- **File**: [examples/plot_modeller/spike_salience_gate.py](../examples/plot_modeller/spike_salience_gate.py#L39)
- **Code**: E402
- **Sin**: `from nodes.tools import _strip_code_fences, load_glosses_with_kinds` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-144 — the import must follow the `sys.path.insert` that makes the `nodes` package discoverable for this standalone FR-585 spike harness.

### CONF-307
- **File**: [examples/plot_modeller/spike_salience_gate.py](../examples/plot_modeller/spike_salience_gate.py#L41)
- **Code**: E402
- **Sin**: `from yamlgraph.executor import execute_prompt` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-306 — grouped with the `nodes` import below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-308
- **File**: [examples/plot_modeller/spike_snapshot_diff.py](../examples/plot_modeller/spike_snapshot_diff.py#L44)
- **Code**: E402
- **Sin**: `from nodes.tools import _strip_code_fences, diff_snapshots, load_glosses_with_kinds` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-306 — the import must follow the `sys.path.insert` that makes the `nodes` package discoverable for this standalone FR-587 snapshot-diff spike harness.

### CONF-309
- **File**: [examples/plot_modeller/spike_snapshot_diff.py](../examples/plot_modeller/spike_snapshot_diff.py#L49)
- **Code**: E402
- **Sin**: `from spike_salience_gate import _load_gt_agents, _type_triple` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-308 — reuses the sibling FR-585 spike's GT loader and triple typer below the required `sys.path.insert`.

### CONF-310
- **File**: [examples/plot_modeller/spike_snapshot_diff.py](../examples/plot_modeller/spike_snapshot_diff.py#L51)
- **Code**: E402
- **Sin**: `from yamlgraph.executor import execute_prompt` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-308 — grouped with the local imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-311
- **File**: [examples/plot_modeller/spike_vocab_encode.py](../examples/plot_modeller/spike_vocab_encode.py#L25)
- **Code**: E402
- **Sin**: `import yaml` appears after `sys.path.insert`.
- **Penance**: Same as CONF-308 — the import must follow the `sys.path.insert` that makes the `nodes`/repo packages discoverable for this standalone FR-591/592 vocab-encode spike harness.

### CONF-312
- **File**: [examples/plot_modeller/spike_vocab_encode.py](../examples/plot_modeller/spike_vocab_encode.py#L26)
- **Code**: E402
- **Sin**: `from evaluate import _load_gt_pre_eff, score_l5` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-311 — reuses the example's evaluation helpers below the required `sys.path.insert`.

### CONF-313
- **File**: [examples/plot_modeller/spike_vocab_encode.py](../examples/plot_modeller/spike_vocab_encode.py#L27)
- **Code**: E402
- **Sin**: `from nodes.tools import _parse_beats, combine_perspectives, load_glosses_with_kinds` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-311 — grouped with the local `nodes` imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-314
- **File**: [examples/plot_modeller/spike_vocab_encode.py](../examples/plot_modeller/spike_vocab_encode.py#L33)
- **Code**: E402
- **Sin**: `from yamlgraph.executor import execute_prompt` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-311 — grouped with the local imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-315
- **File**: [examples/plot_modeller/spike_affect.py](../examples/plot_modeller/spike_affect.py#L56)
- **Code**: E402
- **Sin**: `from evaluate import _load_gt_affects, main_l7` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-308 — the import must follow the `sys.path.insert` that makes the example's `evaluate` module discoverable for this standalone FR-596 affect-throughline spike harness.

### CONF-316
- **File**: [examples/plot_modeller/spike_affect.py](../examples/plot_modeller/spike_affect.py#L57)
- **Code**: E402
- **Sin**: `from nodes.tools import _strip_code_fences, affect_balance, combine_affects, load_glosses_with_kinds` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-315 — grouped with the local `nodes` imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-317
- **File**: [examples/plot_modeller/spike_affect.py](../examples/plot_modeller/spike_affect.py#L64)
- **Code**: E402
- **Sin**: `from yamlgraph.executor import execute_prompt` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-315 — grouped with the local imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-318
- **File**: [examples/plot_modeller/spike_affect_per_kind.py](../examples/plot_modeller/spike_affect_per_kind.py#L54)
- **Code**: E402
- **Sin**: `import evaluate as ev` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-315 — the import must follow the `sys.path.insert` that makes the example's `evaluate` module discoverable for this standalone FR-604 per-kind affect-detection spike harness.

### CONF-319
- **File**: [examples/plot_modeller/spike_affect_per_kind.py](../examples/plot_modeller/spike_affect_per_kind.py#L55)
- **Code**: E402
- **Sin**: `from nodes.tools import _strip_code_fences, combine_affects, load_glosses_with_kinds` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-318 — grouped with the local `nodes` imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-320
- **File**: [examples/plot_modeller/spike_affect_per_kind.py](../examples/plot_modeller/spike_affect_per_kind.py#L61)
- **Code**: E402
- **Sin**: `from yamlgraph.executor import execute_prompt` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-318 — grouped with the local imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-321
- **File**: [examples/plot_modeller/spike_affect_twopass.py](../examples/plot_modeller/spike_affect_twopass.py#L46)
- **Code**: E402
- **Sin**: `import evaluate as ev` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-318 — the import must follow the `sys.path.insert` that makes the example's `evaluate` module discoverable for this standalone FR-605 two-pass affect-localization spike harness.

### CONF-322
- **File**: [examples/plot_modeller/spike_affect_twopass.py](../examples/plot_modeller/spike_affect_twopass.py#L47)
- **Code**: E402
- **Sin**: `from nodes.tools import _strip_code_fences, load_glosses_with_kinds` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-321 — grouped with the local `nodes` imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-323
- **File**: [examples/plot_modeller/spike_affect_twopass.py](../examples/plot_modeller/spike_affect_twopass.py#L48)
- **Code**: E402
- **Sin**: `from spike_affect_per_kind import (...)` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-321 — grouped with the local imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-324
- **File**: [examples/plot_modeller/spike_affect_twopass.py](../examples/plot_modeller/spike_affect_twopass.py#L56)
- **Code**: E402
- **Sin**: `from yamlgraph.executor import execute_prompt` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-321 — grouped with the local imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-325
- **File**: [examples/plot_modeller/spike_affect_goal.py](../examples/plot_modeller/spike_affect_goal.py#L50)
- **Code**: E402
- **Sin**: `import evaluate as ev` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-321 — the import must follow the `sys.path.insert` that makes the example's `evaluate` module discoverable for this standalone FR-607 goal-anchored affect-referent spike harness.

### CONF-326
- **File**: [examples/plot_modeller/spike_affect_goal.py](../examples/plot_modeller/spike_affect_goal.py#L51)
- **Code**: E402
- **Sin**: `from nodes.tools import _strip_code_fences, load_glosses_with_kinds` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-325 — grouped with the local `nodes` imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-327
- **File**: [examples/plot_modeller/spike_affect_goal.py](../examples/plot_modeller/spike_affect_goal.py#L52)
- **Code**: E402
- **Sin**: `from spike_affect_per_kind import (...)` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-325 — grouped with the local imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-328
- **File**: [examples/plot_modeller/spike_affect_goal.py](../examples/plot_modeller/spike_affect_goal.py#L58)
- **Code**: E402
- **Sin**: `from spike_affect_twopass import _pass1_set, _skeleton` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-325 — grouped with the local imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-329
- **File**: [examples/plot_modeller/spike_affect_goal.py](../examples/plot_modeller/spike_affect_goal.py#L60)
- **Code**: E402
- **Sin**: `from yamlgraph.executor import execute_prompt` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-325 — grouped with the local imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-330
- **File**: [examples/plot_modeller/spike_affect_graph.py](../examples/plot_modeller/spike_affect_graph.py#L50)
- **Code**: E402
- **Sin**: `import evaluate as ev` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-325 — the import must follow the `sys.path.insert` that makes the example's `evaluate` module discoverable for this standalone FR-609 goal-graph affect-referent spike harness.

### CONF-331
- **File**: [examples/plot_modeller/spike_affect_graph.py](../examples/plot_modeller/spike_affect_graph.py#L51)
- **Code**: E402
- **Sin**: `from nodes.tools import _strip_code_fences, load_glosses_with_kinds` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-330 — grouped with the local `nodes` imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-332
- **File**: [examples/plot_modeller/spike_affect_graph.py](../examples/plot_modeller/spike_affect_graph.py#L52)
- **Code**: E402
- **Sin**: `from spike_affect_goal import (...)` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-330 — grouped with the local imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-333
- **File**: [examples/plot_modeller/spike_affect_graph.py](../examples/plot_modeller/spike_affect_graph.py#L57)
- **Code**: E402
- **Sin**: `from spike_affect_per_kind import (...)` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-330 — grouped with the local imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-334
- **File**: [examples/plot_modeller/spike_affect_graph.py](../examples/plot_modeller/spike_affect_graph.py#L63)
- **Code**: E402
- **Sin**: `from spike_affect_twopass import _pass1_set, _skeleton` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-330 — grouped with the local imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-335
- **File**: [examples/plot_modeller/spike_affect_graph.py](../examples/plot_modeller/spike_affect_graph.py#L65)
- **Code**: E402
- **Sin**: `from yamlgraph.executor import execute_prompt` appears after `sys.path` manipulation.
- **Penance**: Same as CONF-330 — grouped with the local imports below the `sys.path.insert` required by the standalone example runner pattern.

### CONF-336
- **File**: [tests/unit/test_fr637_novel_fandom_canon.py](../tests/unit/test_fr637_novel_fandom_canon.py#L35)
- **Code**: ANN202
- **Sin**: `_load()` helper returns `types.ModuleType` but annotated with `# noqa: ANN202`.
- **Penance**: Internal test helper; the return type varies dynamically depending on which module is loaded. Type annotation would be `types.ModuleType` which adds no value to callers that immediately destructure attributes.

### CONF-337
- **File**: [tests/unit/test_fr640_novel_fandom_enriched.py](../tests/unit/test_fr640_novel_fandom_enriched.py#L29)
- **Code**: ANN202
- **Sin**: `_load()` helper returns `types.ModuleType` but annotated with `# noqa: ANN202`.
- **Penance**: Same as CONF-336 — internal test helper, dynamically loaded module, type annotation adds no value.

### CONF-338
- **File**: [tests/unit/test_fr638_novel_fandom_pathfinder.py](../tests/unit/test_fr638_novel_fandom_pathfinder.py#L27)
- **Code**: ANN202
- **Sin**: `_load()` helper returns `types.ModuleType` but annotated with `# noqa: ANN202`.
- **Penance**: Same as CONF-336 — internal test helper, dynamically loaded module, type annotation adds no value.

### CONF-339
- **File**: [tests/unit/test_fr639_novel_fandom_close_loop.py](../tests/unit/test_fr639_novel_fandom_close_loop.py#L29)
- **Code**: ANN202
- **Sin**: `_load()` helper returns `types.ModuleType` but annotated with `# noqa: ANN202`.
- **Penance**: Same as CONF-336 — internal test helper, dynamically loaded module, type annotation adds no value.

### CONF-340
- **File**: [tests/unit/test_fr642_novel_fandom_wiki_core.py](../tests/unit/test_fr642_novel_fandom_wiki_core.py#L29)
- **Code**: ANN202
- **Sin**: `_load()` helper returns `types.ModuleType` but annotated with `# noqa: ANN202`.
- **Penance**: Same as CONF-336 — internal test helper, dynamically loaded module, type annotation adds no value.

### CONF-341
- **File**: [tests/unit/test_fr643v2_novel_fandom_worldgen.py](../tests/unit/test_fr643v2_novel_fandom_worldgen.py#L32)
- **Code**: ANN202
- **Sin**: `_load()` helper returns `types.ModuleType` but annotated with `# noqa: ANN202`.
- **Penance**: Same as CONF-336 — internal test helper, dynamically loaded module, type annotation adds no value.

### CONF-342
- **File**: [examples/novel_fandom/nodes/persist_pages.py](../examples/novel_fandom/nodes/persist_pages.py#L56)
- **Code**: BLE001
- **Sin**: Bare `except Exception` catches all exceptions during Pydantic validation.
- **Penance**: Intentional — unknown page types or malformed data from LLM output should be skipped, not crash the pipeline. The warning is logged.

### CONF-343
- **File**: [tests/unit/test_fr647_event_propagation.py](../tests/unit/test_fr647_event_propagation.py#L27)
- **Code**: ANN202
- **Sin**: `_load` helper has no return type annotation.
- **Penance**: Internal test helper that dynamically loads modules — return type is `ModuleType` but annotation adds no value. Same pattern as CONF-336.

### CONF-344
- **File**: [tests/unit/test_fr648_obsidian_wiki.py](../tests/unit/test_fr648_obsidian_wiki.py#L30)
- **Code**: ANN202
- **Sin**: `_load` helper has no return type annotation.
- **Penance**: Same as CONF-343 — internal test helper, dynamically loaded module.

### CONF-345
- **File**: [tests/unit/test_fr649_persist_normalize.py](../tests/unit/test_fr649_persist_normalize.py#L26)
- **Code**: ANN202
- **Sin**: `_load` helper has no return type annotation.
- **Penance**: Same as CONF-343 — internal test helper, dynamically loaded module.

### CONF-346
- **File**: [examples/novel_fandom/nodes/persist_pages.py](../examples/novel_fandom/nodes/persist_pages.py#L162)
- **Code**: BLE001
- **Sin**: Bare `except Exception` in validation fallback.
- **Penance**: FR-649 fallback: any Pydantic validation error must trigger persist-with-warning. Catching broad Exception is intentional — unknown model errors should not silently drop pages.

### CONF-347
- **File**: [tests/unit/test_fr650_canon_type_subfolders.py](../tests/unit/test_fr650_canon_type_subfolders.py#L26)
- **Code**: ANN202
- **Sin**: `_load` helper has no return type annotation.
- **Penance**: Same as CONF-343 — internal test helper, dynamically loaded module.

### CONF-348
- **File**: [tests/unit/test_fr657_agentic_event_deepening.py](../tests/unit/test_fr657_agentic_event_deepening.py#L28)
- **Code**: ANN202
- **Sin**: `_load` helper has no return type annotation.
- **Penance**: Same as CONF-343 — internal test helper, dynamically loaded module.

### CONF-143
- **File**: [tests/unit/test_fr296_watcher_fsm_startup_script.py](../tests/unit/test_fr296_watcher_fsm_startup_script.py#L118)
- **Code**: S603
- **Sin**: `subprocess.run()` called with list argument flagged as untrusted input.
- **Penance**: Command list is hardcoded `["bash", "-n", str(SCRIPT_PATH)]` — no user input. `SCRIPT_PATH` is a constant derived from `__file__`. Used to validate shell script syntax in tests.

### CONF-210
- **File**: [yamlgraph/node_factory/copilot_node.py](../yamlgraph/node_factory/copilot_node.py#L371)
- **Code**: S603
- **Sin**: `subprocess.run()` called without `check=True`, suppressing the `S603` subprocess call warning.
- **Penance**: The `cmd` list is built entirely from hardcoded strings (`"gh"`, `"copilot"`, `"suggest"`) plus internal config flags and validated graph metadata (model name, timeout). No user input reaches the command arguments. Return code is checked manually to distinguish timeout, CLI unavailability, and success.

### CONF-209
- **File**: [vulture_whitelist.py](../vulture_whitelist.py)
- **Code**: F401
- **Sin**: `check_python_node_variables` is imported and referenced in `vulture_whitelist.py` to suppress dead-code detection.
- **Penance**: The function is an API stub retained for stability after FR-252 made W020 obsolete. It is called from tests and exported from `checks_contracts`. Removing it would break any callers that imported the function directly.

### CONF-208
- **File**: [scripts/validate_id_registry.py](../scripts/validate_id_registry.py#L28)
- **Code**: E402
- **Sin**: Import from `yamlgraph.utils.id_registry` after `sys.path.insert()`.
- **Penance**: The `sys.path` modification is required before the import so `yamlgraph` is resolvable when running the script standalone. Standard pattern for repo scripts.

### CONF-211
- **File**: [tests/unit/test_fr355_mcp_schema_validation_gate_red.py](../tests/unit/test_fr355_mcp_schema_validation_gate_red.py#L12)
- **Code**: E402
- **Sin**: Import `mcp.types` after `pytest.importorskip("mcp")` guard.
- **Penance**: `mcp` is an optional dependency; the skip guard must execute before importing `mcp.types` so the test file is skipped cleanly when MCP extras are not installed.

### CONF-212
- **File**: [scripts/extract_copilot_events_lib.py](../scripts/extract_copilot_events_lib.py#L100)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-213
- **File**: [scripts/extract_copilot_events_lib.py](../scripts/extract_copilot_events_lib.py#L104)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-214
- **File**: [scripts/extract_copilot_events_lib.py](../scripts/extract_copilot_events_lib.py#L31)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-215
- **File**: [scripts/extract_copilot_events_lib.py](../scripts/extract_copilot_events_lib.py#L33)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-216
- **File**: [scripts/req_coverage.py](../scripts/req_coverage.py#L403)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-217
- **File**: [scripts/req_coverage.py](../scripts/req_coverage.py#L408)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-218
- **File**: [scripts/req_coverage.py](../scripts/req_coverage.py#L450)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-219
- **File**: [yamlgraph/a2a/message.py](../yamlgraph/a2a/message.py#L120)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-220
- **File**: [yamlgraph/a2a/message.py](../yamlgraph/a2a/message.py#L66)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-221
- **File**: [yamlgraph/constants.py](../yamlgraph/constants.py#L48)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-222
- **File**: [yamlgraph/diary/importer.py](../yamlgraph/diary/importer.py#L234)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-223
- **File**: [yamlgraph/compile/edge_compiler.py](../yamlgraph/compile/edge_compiler.py#L229)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-224
- **File**: [yamlgraph/error_handlers.py](../yamlgraph/error_handlers.py#L1)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-225
- **File**: [yamlgraph/error_handlers.py](../yamlgraph/error_handlers.py#L139)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-226
- **File**: [yamlgraph/error_handlers.py](../yamlgraph/error_handlers.py#L142)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-227
- **File**: [yamlgraph/error_handlers.py](../yamlgraph/error_handlers.py#L144)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-228
- **File**: [yamlgraph/error_handlers.py](../yamlgraph/error_handlers.py#L154)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-229
- **File**: [yamlgraph/error_handlers.py](../yamlgraph/error_handlers.py#L155)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-230
- **File**: [yamlgraph/error_handlers.py](../yamlgraph/error_handlers.py#L157)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-231
- **File**: [yamlgraph/error_handlers.py](../yamlgraph/error_handlers.py#L161)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-232
- **File**: [yamlgraph/linter/checks_contracts.py](../yamlgraph/linter/checks_contracts.py#L216)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-233
- **File**: [yamlgraph/linter/checks_contracts.py](../yamlgraph/linter/checks_contracts.py#L217)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-234
- **File**: [yamlgraph/linter/checks_semantic.py](../yamlgraph/linter/checks_semantic.py#L14)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-235
- **File**: [yamlgraph/linter/checks_semantic.py](../yamlgraph/linter/checks_semantic.py#L232)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-236
- **File**: [yamlgraph/linter/checks_semantic.py](../yamlgraph/linter/checks_semantic.py#L244)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-237
- **File**: [yamlgraph/linter/checks_semantic.py](../yamlgraph/linter/checks_semantic.py#L255)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-238
- **File**: [yamlgraph/linter/graph_linter.py](../yamlgraph/linter/graph_linter.py#L128)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-239
- **File**: [yamlgraph/linter/graph_linter.py](../yamlgraph/linter/graph_linter.py#L129)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-240
- **File**: [yamlgraph/models/node_schema.py](../yamlgraph/models/node_schema.py#L75)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-241
- **File**: [yamlgraph/node_factory/copilot_node.py](../yamlgraph/node_factory/copilot_node.py#L83)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-242
- **File**: [yamlgraph/node_factory/llm_execution.py](../yamlgraph/node_factory/llm_execution.py#L159)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-243
- **File**: [yamlgraph/node_factory/llm_nodes.py](../yamlgraph/node_factory/llm_nodes.py#L130)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-244
- **File**: [yamlgraph/node_factory/llm_nodes.py](../yamlgraph/node_factory/llm_nodes.py#L131)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-245
- **File**: [yamlgraph/node_factory/llm_nodes.py](../yamlgraph/node_factory/llm_nodes.py#L166)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-246
- **File**: [yamlgraph/node_factory/llm_nodes.py](../yamlgraph/node_factory/llm_nodes.py#L60)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-247
- **File**: [yamlgraph/node_factory/router_race_node.py](../yamlgraph/node_factory/router_race_node.py#L38)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-248
- **File**: [yamlgraph/storage/serializers.py](../yamlgraph/storage/serializers.py#L64)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-249
- **File**: [yamlgraph/utils/conditions.py](../yamlgraph/utils/conditions.py#L123)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-250
- **File**: [yamlgraph/utils/fsm/action.py](../yamlgraph/utils/fsm/action.py#L29)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-251
- **File**: [yamlgraph/utils/prompts.py](../yamlgraph/utils/prompts.py#L1)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-252
- **File**: [yamlgraph/utils/prompts.py](../yamlgraph/utils/prompts.py#L159)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-253
- **File**: [yamlgraph/utils/prompts.py](../yamlgraph/utils/prompts.py#L71)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-254
- **File**: [yamlgraph/utils/prompts.py](../yamlgraph/utils/prompts.py#L87)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-304
- **File**: [yamlgraph/tools/agent.py](../yamlgraph/tools/agent.py#L68)
- **Code**: FB001
- **Sin**: Docstring of `_try_structured_output` contains `fallback` — describes the try-parse-first, fallback-to-LLM strategy (FR-448).
- **Penance**: The word describes the actual algorithmic pattern. Renaming would obscure intent.

### CONF-305
- **File**: [yamlgraph/tools/agent.py](../yamlgraph/tools/agent.py#L151)
- **Code**: FB001
- **Sin**: Comment `# Fallback: structured output re-invoke (expensive)` uses `fallback` token.
- **Penance**: Same as CONF-304 — documents the two-phase structured output strategy.

### CONF-349
- **File**: [yamlgraph/utils/llm_factory_async.py](../yamlgraph/utils/llm_factory_async.py#L80)
- **Code**: FB001
- **Sin**: Docstring of `invoke_async` contains `fallback` — describes the FR-464 structured-output JSON fallback strategy.
- **Penance**: The word describes the actual retry-then-parse pattern from FR-676. Renaming would obscure intent.

### CONF-255
- **File**: [yamlgraph/utils/fsm/ui_log.py](../yamlgraph/utils/fsm/ui_log.py#L50)
- **Code**: S603
- **Sin**: `subprocess.run(cmd, ...)` is flagged as potentially executing untrusted input.
- **Penance**: Command is a fixed argv list for `statemachine_engine.database.cli send-event`; inputs are structured message fields serialized into JSON and passed as an argument (no shell expansion, `shell=True` is not used).

### CONF-256
- **File**: [scripts/node_type_coverage.py](../scripts/node_type_coverage.py#L63)
- **Code**: S112
- **Sin**: `try-except-continue` silently skips YAML files that fail to parse.
- **Penance**: Script scans all `*.yaml` under demos/ — some may be prompt templates or malformed. Skipping unparseable files is the correct behavior for a coverage scanner; logging would add noise without value.

---

## Process Exceptions

Process-level suppression of rules that are normally forbidden by Scripture.
These are not `# noqa` suppressions — they are documented deviations from process rules.

### CONF-300
- **File**: `.chaplain/config/integration-pipeline.yaml`
- **Code**: --no-verify (Scripture: "no --no-verify flag")
- **Sin**: Intermediate stub commits in FR-301 integration test use `git commit --no-verify` to skip pre-commit hooks on docs-only echo statements.
- **Penance**: These commits exist only inside a worktree branch that will be squash-merged. The `finalizing` state runs `pre-commit run --all-files` on the complete worktree before push. The final squash-merged commit on main passes all CI gates. No unverified code reaches main.

### CONF-301
- **File**: [examples/novel_fandom/nodes/persist_genesis.py](../examples/novel_fandom/nodes/persist_genesis.py#L17)
- **Code**: ANN202
- **Sin**: `_load_persist_impl` helper returns dynamically loaded function, type is not expressible without Protocol.
- **Penance**: Internal loader used only within persist_genesis; return type is `Callable` but annotating it adds no value over reading the one callsite.

### CONF-302
- **File**: [tests/unit/test_fr655_genesis.py](../tests/unit/test_fr655_genesis.py#L27)
- **Code**: ANN202
- **Sin**: `_load` test helper returns dynamically loaded module, same pattern as all other novel_fandom test files.
- **Penance**: Consistent with CONF-247..256 pattern across test_fr637..654 files. Test-only utility.

### CONF-350
- **File**: [yamlgraph/tools/agent.py](../yamlgraph/tools/agent.py#L77)
- **Code**: FB001
- **Sin**: Comment uses `fallback` token describing a legitimate fallback trigger condition.
- **Penance**: Documents the structured-output mismatch recovery path. Renaming would obscure intent.

### CONF-351
- **File**: [yamlgraph/executor_base.py](../yamlgraph/executor_base.py#L384)
- **Code**: FB001
- **Sin**: Docstring of `_invoke_llm_once` contains `fallback` — describes the FR-464 structured-output fallback strategy.
- **Penance**: Documents the retry-then-parse pattern. Renaming would obscure intent.

### CONF-352
- **File**: [yamlgraph/utils/llm_providers.py](../yamlgraph/utils/llm_providers.py#L342)
- **Code**: FB001
- **Sin**: Docstring contains `fallback` — explicitly states there is NO silent fallback at this boundary.
- **Penance**: The word is used to negate a fallback pattern, not to implement one.

### CONF-366
- **File**: [tests/unit/test_fr689_genesis_consistency.py](../tests/unit/test_fr689_genesis_consistency.py#L36)
- **Code**: ANN202
- **Sin**: `_load_yaml` test helper omits return type annotation.
- **Penance**: Internal test utility returning `dict`. Consistent with CONF-247..365 pattern.

### CONF-367
- **File**: [tests/unit/test_fr689_genesis_consistency.py](../tests/unit/test_fr689_genesis_consistency.py#L68)
- **Code**: ANN202
- **Sin**: `_node_names` test helper omits return type annotation.
- **Penance**: Internal test utility returning `list[str]`. Test-only.

### CONF-368
- **File**: [tests/unit/test_fr689_genesis_consistency.py](../tests/unit/test_fr689_genesis_consistency.py#L212)
- **Code**: ANN202
- **Sin**: `_canon_fixture` pytest fixture omits return type annotation.
- **Penance**: Pytest fixture returning `Path`. Consistent with test fixture patterns.

### CONF-369
- **File**: [tests/unit/test_fr689_genesis_consistency.py](../tests/unit/test_fr689_genesis_consistency.py#L305)
- **Code**: ANN202
- **Sin**: `_canon_with_files` pytest fixture omits return type annotation.
- **Penance**: Pytest fixture returning `Path`. Consistent with test fixture patterns.

### CONF-370
- **File**: [tests/unit/test_fr689_genesis_consistency.py](../tests/unit/test_fr689_genesis_consistency.py#L417)
- **Code**: ANN202
- **Sin**: `_canon_fixture` pytest fixture omits return type annotation.
- **Penance**: Pytest fixture returning `Path`. Consistent with test fixture patterns.

### CONF-371
- **File**: [yamlgraph/node_factory/race_node.py](../yamlgraph/node_factory/race_node.py#L198)
- **Code**: BLE001
- **Sin**: `except BaseException` in the race bridge's verdict transport catches everything, including KeyboardInterrupt/SystemExit.
- **Penance**: FR-707 verdict handoff — the coroutine's outcome (result OR any exception) must cross the thread boundary via the Future; swallowing nothing, relabeling nothing. Anything not captured here would vanish in the daemon thread and the caller would hit the bridge budget as an anonymous RuntimeError, recreating the NC-361 forensic hole this fix exists to close. Same pattern as the previous `_run` transport it replaces.

### CONF-372
- **File**: [yamlgraph/node_factory/router_race_node.py](../yamlgraph/node_factory/router_race_node.py#L41)
- **Code**: FB001
- **Sin**: Docstring contains the lexical token `fallback`.
- **Penance**: It documents the judged `on_error: fallback` contract (route via `default_route`, record the error in state) — an explicit, tested error mode, not a silent fallback. The docstring moved onto the flagged line during the FR-707 call-site edit (and again in FR-713); the semantics predate it.

### CONF-355
- **File**: [examples/novel_fandom/nodes/creation_tools.py](../examples/novel_fandom/nodes/creation_tools.py#L71)
- **Code**: BLE001
- **Sin**: Bare `except Exception` in entity builder dispatch catches all errors.
- **Penance**: Builder functions may raise arbitrary errors from Pydantic validation; catching broadly and returning structured error message is the correct pattern for a graph-tool node that must not crash the parent agent.

### CONF-356
- **File**: [examples/novel_fandom/nodes/persist_genesis.py](../examples/novel_fandom/nodes/persist_genesis.py#L23)
- **Code**: E402
- **Sin**: Module-level import not at top of file.
- **Penance**: Import after `sys.path` manipulation to locate sibling module. Standard pattern for example code with relative imports.

### CONF-357
- **File**: [examples/novel_fandom/nodes/persist_genesis.py](../examples/novel_fandom/nodes/persist_genesis.py#L28)
- **Code**: ANN202
- **Sin**: Function omits return type annotation.
- **Penance**: Example code helper function. Not part of the core framework.

### CONF-358
- **File**: [tests/unit/test_fr664_665_667_dedup_trilogy.py](../tests/unit/test_fr664_665_667_dedup_trilogy.py#L26)
- **Code**: ANN202
- **Sin**: `_load` test helper omits return type annotation.
- **Penance**: Consistent with CONF-247..354 pattern. Test-only utility.

### CONF-359
- **File**: [tests/unit/test_fr683_ref_integrity_graph_tool.py](../tests/unit/test_fr683_ref_integrity_graph_tool.py#L24)
- **Code**: ANN202
- **Sin**: `_load` test helper omits return type annotation.
- **Penance**: Consistent with CONF-247..354 pattern. Test-only utility.

### CONF-360
- **File**: [tests/unit/test_fr684_semantic_dedup_graph_tool.py](../tests/unit/test_fr684_semantic_dedup_graph_tool.py#L24)
- **Code**: ANN202
- **Sin**: `_load` test helper omits return type annotation.
- **Penance**: Consistent with CONF-247..354 pattern. Test-only utility.

### CONF-361
- **File**: [tests/unit/test_fr686_agent_first_rewrite.py](../tests/unit/test_fr686_agent_first_rewrite.py#L32)
- **Code**: ANN202
- **Sin**: `_load_yaml` test helper omits return type annotation.
- **Penance**: Consistent with CONF-247..354 pattern. Test-only utility.

### CONF-362
- **File**: [tests/unit/test_fr686_agent_first_rewrite.py](../tests/unit/test_fr686_agent_first_rewrite.py#L258)
- **Code**: ANN202
- **Sin**: `_canon_fixture` pytest fixture omits return type annotation.
- **Penance**: Pytest fixture returning `Path`. Consistent with test fixture patterns.

### CONF-363
- **File**: [tests/unit/test_fr686_agent_first_rewrite.py](../tests/unit/test_fr686_agent_first_rewrite.py#L398)
- **Code**: ANN202
- **Sin**: `_canon_fixture` pytest fixture omits return type annotation.
- **Penance**: Pytest fixture returning `Path`. Consistent with test fixture patterns.

### CONF-364
- **File**: [yamlgraph/executor_base.py](../yamlgraph/executor_base.py#L172)
- **Code**: C901
- **Sin**: `_invoke_llm` function exceeds cyclomatic complexity threshold.
- **Penance**: Central LLM invocation dispatch handles multiple provider paths and structured output. Splitting would fragment the core execution flow without reducing actual complexity.

### CONF-365
- **File**: [yamlgraph/tools/agent.py](../yamlgraph/tools/agent.py#L94)
- **Code**: C901
- **Sin**: Agent tool handler exceeds cyclomatic complexity threshold.
- **Penance**: Agent node orchestration is inherently complex — tool dispatch, error handling, streaming. Splitting would obscure the sequential logic.

### CONF-373
- **File**: [tests/unit/test_fr713_persistent_bridge.py](../tests/unit/test_fr713_persistent_bridge.py#L317)
- **Code**: SLF001
- **Sin**: AC-11 witness stops `bridge._loop` directly to simulate loop-thread death.
- **Penance**: Loop death is an internal fatality by definition — no public API should exist to kill the bridge; the witness must reach through the seam it guards.

### CONF-374
- **File**: [yamlgraph/utils/bridge.py](../yamlgraph/utils/bridge.py#L79)
- **Code**: SLF001
- **Sin**: `_reset_after_fork` rebinds `llm_factory._cache_lock` directly.
- **Penance**: Fork hygiene cannot go through `clear_cache()` — the forked lock may be held by a thread that no longer exists in the child; acquiring it would deadlock. Rebinding a fresh lock is the only safe move.

### CONF-376
- **File**: [yamlgraph/utils/bridge.py](../yamlgraph/utils/bridge.py#L80)
- **Code**: SLF001
- **Sin**: `_reset_after_fork` rebinds `llm_factory._llm_cache` directly.
- **Penance**: Companion to CONF-374 — cached clients bind sessions to the parent's loop; the child must drop them without touching the possibly-poisoned lock.

### CONF-375
- **File**: [yamlgraph/utils/bridge.py](../yamlgraph/utils/bridge.py#L141)
- **Code**: BLE001
- **Sin**: `_deliver` catches `BaseException` around the awaited coroutine.
- **Penance**: Verdict transport — every outcome including CancelledError must cross the thread boundary to the caller's Future; swallowing nothing, relabeling nothing. Same contract as the FR-707 bridge it replaces.

### CONF-377
- **File**: [yamlgraph/utils/template.py](../yamlgraph/utils/template.py#L48)
- **Code**: B701
- **Sin**: Jinja2 `Environment()` constructed with `autoescape=False` (default).
- **Penance**: Templates render LLM prompt text, never HTML — autoescaping would corrupt prompts containing markup-like characters. XSS requires a browser sink; there is none.

### CONF-378
- **File**: [yamlgraph/cli/__init__.py](../yamlgraph/cli/__init__.py#L366)
- **Code**: B104
- **Sin**: a2a serve CLI defaults `--host` to `0.0.0.0`.
- **Penance**: Development server for local/container use; binding all interfaces is the documented default (containers need it). Deployment behind a proxy is the operator's boundary, flagged in help text.

### CONF-379
- **File**: [yamlgraph/cli/a2a_commands.py](../yamlgraph/cli/a2a_commands.py#L58)
- **Code**: B104
- **Sin**: a2a serve fallback host is `0.0.0.0` when args carry no host.
- **Penance**: Companion to CONF-378 — same default, same context, single serve path.

### CONF-380
- **File**: [yamlgraph/tools/shell.py](../yamlgraph/tools/shell.py#L131)
- **Code**: B602
- **Sin**: `subprocess` invoked with `shell=True` for YAML-declared command templates.
- **Penance**: Command templates come from trusted graph YAML only; all runtime variables pass through `shlex.quote()` before substitution (module's documented security contract). Pre-existing nosec, confessed retroactively by FR-714 Judgement F1.

### CONF-381
- **File**: [yamlgraph/utils/fsm/event_sender.py](../yamlgraph/utils/fsm/event_sender.py#L13)
- **Code**: B108
- **Sin**: FSM control socket prefix hardcoded under `/tmp` (bandit twin of CONF-302's S108).
- **Penance**: AF_UNIX datagram sockets need a well-known rendezvous path shared across processes; the statemachine-engine contract pins this prefix. Same rationale as CONF-302.

### CONF-382
- **File**: [tests/unit/test_fr716_module_splits.py](../tests/unit/test_fr716_module_splits.py#L45)
- **Code**: F401
- **Sin**: FR-716 re-export witness imports public names without using them.
- **Penance**: The import IS the assertion — the test proves `yamlgraph.models` re-exports survive the bisection; usage would test something else.

### CONF-383
- **File**: [tests/unit/test_fr716_module_splits.py](../tests/unit/test_fr716_module_splits.py#L51)
- **Code**: F401
- **Sin**: Companion to CONF-382 — direct `node_schema` import unused.
- **Penance**: Same witness pattern: importability of the new module path is the property under test.

### CONF-384
- **File**: [tests/unit/test_fr719_conditions_smt.py](../tests/unit/test_fr719_conditions_smt.py#L24)
- **Code**: E402
- **Sin**: Module-level import after `pytest.importorskip("z3")`.
- **Penance**: The skip guard MUST precede the import of the module under test — importing `conditions_smt` without z3 present would defeat the AC-05 optional-dependency contract the file witnesses.

### CONF-385
- **File**: [tests/unit/test_fr719_conditions_smt.py](../tests/unit/test_fr719_conditions_smt.py#L27)
- **Code**: E402
- **Sin**: Companion to CONF-384 — `evaluate_condition` imported after the skip guard.
- **Penance**: Same ordering constraint; the faithfulness witness needs the runtime evaluator only when z3 is present.


### CONF-386
- **File**: [examples/icpc-2-rfe/nodes/build_catalog.py](../examples/icpc-2-rfe/nodes/build_catalog.py#L77)
- **Code**: S314
- **Sin**: `xml.etree.ElementTree.fromstring` on the ICPC-2e ClaML file instead of defusedxml.
- **Penance**: The input is trusted by construction: `build_catalog` refuses any zip whose sha256 differs from the pinned digest of the official ICPC-2e-v7.0 release (FR-722 A1), so only one byte-exact known file is ever parsed; the unit-test path parses a committed 3-row excerpt. Adding a defusedxml dependency for an example builder would violate the no-new-deps posture for examples.

### CONF-387
- **File**: [examples/cwe-classifier/nodes/build_catalog.py](../examples/cwe-classifier/nodes/build_catalog.py#L66)
- **Code**: S314
- **Sin**: `xml.etree.ElementTree.fromstring` on cwec_v4.20.xml instead of defusedxml.
- **Penance**: Same trust construction as CONF-386: `build_catalog` refuses any zip whose sha256 differs from the pinned digest of the versioned MITRE cwec_v4.20.xml.zip release (FR-733), so only one byte-exact known file is ever parsed; the unit-test path parses a committed hand-reduced excerpt. Examples take no new dependencies.

### CONF-388
- **File**: [.github/hooks/scripts/checks/prior_art_gate.py](../.github/hooks/scripts/checks/prior_art_gate.py#L36)
- **Code**: S603
- **Sin**: `subprocess.run([GIT, "diff", "--cached", ...])` flagged as untrusted input.
- **Penance**: Command and args are hardcoded constants; GIT resolved via `shutil.which`. No user input reaches the call.

### CONF-389
- **File**: [.github/hooks/scripts/checks/prior_art_gate.py](../.github/hooks/scripts/checks/prior_art_gate.py#L47)
- **Code**: S603
- **Sin**: `subprocess.run([GIT, "show", f":0:{path}"])` — path interpolated into an argument.
- **Penance**: `path` comes from pre-commit's staged-filename list (list-form argv, no shell); worst case is a git error for a nonexistent blob, handled by returncode check.

### CONF-390
- **File**: [scripts/vscode/now.py](../scripts/vscode/now.py#L36)
- **Code**: S603
- **Sin**: `subprocess.run([GIT, "-C", repo, *args])` — non-constant arguments.
- **Penance**: GIT resolved via `shutil.which`; subcommands are hardcoded read-only queries (branch/diff/log); repo paths come from workspace.json enumeration, list-form argv, no shell.

### CONF-391
- **File**: [scripts/vscode/now.py](../scripts/vscode/now.py#L198)
- **Code**: B007
- **Sin**: loop variable `model` reused after the loop — B007 flags the unused loop body.
- **Penance**: deliberate last-match idiom (want the final modelId in the tail window); a `pass` body with the value read after the loop is the cheapest form.

### CONF-392
- **File**: [scripts/vscode/tests/test_tap.py](../scripts/vscode/tests/test_tap.py#L28)
- **Code**: E402
- **Sin**: `import tap` after a `sys.path.insert` — module-level import not at top.
- **Penance**: the spike suite lives outside the package; the path bootstrap must precede the import. Same idiom as any script-adjacent test without an installable package.

### CONF-393
- **File**: [scripts/tests/test_fr_board.py](../scripts/tests/test_fr_board.py#L30)
- **Code**: E402
- **Sin**: `import fr_board` after a `sys.path.insert` — module-level import not at top.
- **Penance**: script-adjacent test outside the installable package; path bootstrap must precede the import (CONF-392 idiom).

### CONF-398
- **File**: [tests/unit/test_fr717_seams.py](../tests/unit/test_fr717_seams.py#L40)
- **Code**: F401
- **Sin**: Re-export witness imports `load_and_compile` without using it.
- **Penance**: The import IS the assertion — the test proves top-level re-exports survived the package moves (same pattern as CONF-382).

### CONF-394
- **File**: [scripts/vscode/tests/test_todos.py](../scripts/vscode/tests/test_todos.py#L23)
- **Code**: E402
- **Sin**: `import todos` after a `sys.path.insert` — module-level import not at top.
- **Penance**: script-adjacent test outside the installable package; path bootstrap must precede the import (CONF-392/393 idiom).

### CONF-395
- **File**: [scripts/vscode/todos.py](../scripts/vscode/todos.py#L108)
- **Code**: S324
- **Sin**: `hashlib.sha1` for the orphan drop key.
- **Penance**: content addressing of todo titles for dedupe, zero security role; sha1's 8-hex prefix is stable, short, and printable — collision resistance is irrelevant at n≈30 titles.

### CONF-396
- **File**: [scripts/vscode/tests/test_brief.py](../scripts/vscode/tests/test_brief.py#L22)
- **Code**: E402
- **Sin**: `import now` after a `sys.path.insert` — module-level import not at top.
- **Penance**: script-adjacent test outside the installable package; path bootstrap must precede the import (CONF-392/393/394 idiom).

### CONF-397
- **File**: [.github/hooks/scripts/checks/triage_gate.py](../.github/hooks/scripts/checks/triage_gate.py#L40)
- **Code**: S603
- **Sin**: `subprocess.run([GIT, "show", ...])` flagged as untrusted input.
- **Penance**: Command and args are hardcoded constants; GIT resolved via `shutil.which`; path comes from pre-commit's staged-file list. No user input reaches the call (CONF-388 idiom).

### CONF-399
- **File**: [scripts/direct_import_scan.py](../scripts/direct_import_scan.py#L68)
- **Code**: E402
- **Sin**: `from dependency_rationale import parse_pyproject_dependencies` after a `sys.path.insert` — module-level import not at top.
- **Penance**: script-adjacent module reusing a sibling script's parser; path bootstrap must precede the import (CONF-392/393/394/396 idiom).

### CONF-400
- **File**: [scripts/example_taxonomy_scan.py](../scripts/example_taxonomy_scan.py#L63)
- **Code**: E402
- **Sin**: `from dependency_rationale import parse_pyproject_dependencies` after a `sys.path.insert` — module-level import not at top.
- **Penance**: script-adjacent module reusing a sibling script's parser; path bootstrap must precede the import (CONF-392/393/394/396/399 idiom).

### CONF-401
- **File**: [scripts/example_taxonomy_scan.py](../scripts/example_taxonomy_scan.py#L64)
- **Code**: E402
- **Sin**: `from direct_import_scan import (...)` after a `sys.path.insert` — module-level import not at top.
- **Penance**: reuses FR-761's scanner internals (import extraction, distribution resolution, normalization) rather than reimplementing them; same path-bootstrap idiom as CONF-400.

### CONF-402
- **File**: [tests/unit/test_example_taxonomy_scan.py](../tests/unit/test_example_taxonomy_scan.py#L11)
- **Code**: E402
- **Sin**: `from example_taxonomy_scan import (...)` after a `sys.path.insert` — module-level import not at top.
- **Penance**: test imports the script module directly (not via the `scripts` package) to exercise it with isolated `tmp_path` fixtures; same path-bootstrap idiom as CONF-400/401.

### CONF-403
- **File**: [tests/unit/test_example_taxonomy_scan.py](../tests/unit/test_example_taxonomy_scan.py#L12)
- **Code**: E402
- **Sin**: `import example_taxonomy_scan` (the module itself, not just its names) after a `sys.path.insert` — module-level import not at top.
- **Penance**: needed alongside the `from ... import (...)` on the next line so `monkeypatch.setitem(example_taxonomy_scan.README_CLI_SUBCOMMAND_MODULES, ...)` can mutate the module's dict in place (PR #464 review, round 2); same path-bootstrap idiom as CONF-400/401/402.


---

## Adding New Confessions

When you add a `# noqa` to the codebase:

1. Find the next available CONF-XXX ID in the appropriate section
2. Add the full entry with File, Code, Sin, and Penance
3. Run `python scripts/noqa_coverage.py --strict` to verify

The ID ranges are:
- **CONF-001 to CONF-009**: Framework code (requires elevated scrutiny)
- **CONF-010 to CONF-099**: Test code
- **CONF-100 to CONF-199**: Example code
- **CONF-200 to CONF-299**: Scripts

### CONF-404
- **File**: [tests/unit/test_weekly_recap.py](../tests/unit/test_weekly_recap.py#L20)
- **Code**: E402
- **Sin**: `import weekly_recap` after a `sys.path.insert` — module-level import not at top.
- **Penance**: test imports the script module directly to monkeypatch `run_recap_graph` and exercise the render/no-op contract LLM-free; same path-bootstrap idiom as CONF-400/401/402/403.

### CONF-405
- **File**: [scripts/weekly_recap.py](../scripts/weekly_recap.py#L44)
- **Code**: S603
- **Sin**: `subprocess.run([GIT, "-C", repo_path, ...])` flagged as untrusted input.
- **Penance**: Command and args are hardcoded constants; GIT resolved via `shutil.which`; repo_path comes from the operator's CLI flag or the workflow's own checkout. No user input reaches the call (CONF-388/397 idiom).

### CONF-406
- **File**: [scripts/spikes/da_publish_spike.py](../scripts/spikes/da_publish_spike.py#L22)
- **Code**: S105
- **Sin**: `TOKEN_URL = "https://www.deviantart.com/oauth2/token"` flagged as hardcoded password.
- **Penance**: False positive — the string is the public OAuth token endpoint URL; the variable name merely contains "token". No secret is stored.

### CONF-407
- **File**: [scripts/spikes/da_publish_spike.py](../scripts/spikes/da_publish_spike.py#L81)
- **Code**: N802
- **Sin**: `do_GET` method name is not snake_case.
- **Penance**: `http.server.BaseHTTPRequestHandler` dispatches on this exact name; the stdlib contract dictates the casing.

### CONF-408
- **File**: [tests/unit/test_fr851_req_audit_red.py](../tests/unit/test_fr851_req_audit_red.py#L22)
- **Code**: E402
- **Sin**: Import after `sys.path.insert` for scripts module.
- **Penance**: Test imports from scripts/ which is not a package (CONF-019 idiom).

### CONF-409
- **File**: [tests/unit/test_fr851_req_audit_red.py](../tests/unit/test_fr851_req_audit_red.py#L32)
- **Code**: E402
- **Sin**: Import after `sys.path.insert` for scripts module.
- **Penance**: Test imports from scripts/ which is not a package (CONF-019 idiom).

### CONF-410
- **File**: [scripts/req_audit_questions.py](../scripts/req_audit_questions.py#L33)
- **Code**: E402
- **Sin**: Import after `sys.path.insert` for sibling scripts module.
- **Penance**: scripts/ is not a package; req_audit_questions reuses req_coverage loaders per FR-851 (CONF-019 idiom).

### CONF-411
- **File**: [tests/unit/test_fr850_coverage_contexts_red.py](../tests/unit/test_fr850_coverage_contexts_red.py#L23)
- **Code**: E402
- **Sin**: Import after `sys.path.insert` for scripts module.
- **Penance**: Test imports the FR-850 shared loader from scripts/ flat path (CONF-019 idiom).

### CONF-412
- **File**: [scripts/req_coverage.py](../scripts/req_coverage.py#L34)
- **Code**: E402
- **Sin**: Import after `sys.path.insert` for sibling scripts module.
- **Penance**: scripts/ is not a package; req_coverage consumes the shared coverage_contexts boundary per FR-850 (CONF-019 idiom).

### CONF-413
- **File**: [scripts/req_audit_questions.py](../scripts/req_audit_questions.py#L28)
- **Code**: E402
- **Sin**: Import after `sys.path.insert` for sibling scripts module.
- **Penance**: scripts/ is not a package; req_audit_questions consumes the shared coverage_contexts boundary per FR-850 (CONF-019 idiom).

### CONF-414
- **File**: [tests/unit/test_ramp_installer.py](../tests/unit/test_ramp_installer.py#L24)
- **Code**: E402
- **Sin**: Import after `sys.path.insert` for scripts module.
- **Penance**: Test imports the FR-865 ramp installer from the scripts/ flat path (CONF-019 idiom).

### CONF-415
- **File**: [scripts/vscode/tests/test_session_shapes.py](../scripts/vscode/tests/test_session_shapes.py#L22)
- **Code**: E402
- **Sin**: `import session_shapes` after a `sys.path.insert` — module-level import not at top.
- **Penance**: script-adjacent test outside the installable package; path bootstrap must precede the import (CONF-392/393/394 idiom).

### CONF-416
- **File**: [scripts/vscode/session_shapes.py](../scripts/vscode/session_shapes.py#L176)
- **Code**: S311
- **Sin**: `random.Random(seed)` flagged as non-cryptographic PRNG.
- **Penance**: sampling is deliberately deterministic (seeded, AC-02 reproducible stratum), not security-sensitive.

### CONF-417
- **File**: [scripts/vscode/session_shapes.py](../scripts/vscode/session_shapes.py#L333)
- **Code**: PLC0415
- **Sin**: `from ledger import load_prices` inside `main()` — import not at top.
- **Penance**: sibling-spike reuse needs a sys.path bootstrap first and must not break library import of the module under test; CLI-only dependency stays in the CLI path.

### CONF-418
- **File**: [scripts/vscode/fr884_skeletons.py](../scripts/vscode/fr884_skeletons.py#L17)
- **Code**: E402
- **Sin**: `from session_shapes import ...` after a `sys.path.insert` — module-level import not at top.
- **Penance**: sibling-spike reuse; the path bootstrap must precede the import (same idiom as CONF-392).

### CONF-419
- **File**: [scripts/vscode/now.py](../scripts/vscode/now.py#L82)
- **Code**: S603
- **Sin**: `subprocess.run` with dynamic args in `orphan_worktree_lines`.
- **Penance**: read-only git plumbing on fixture-verified paths; same idiom as CONF-390.

### CONF-420
- **File**: [scripts/vscode/now.py](../scripts/vscode/now.py#L90)
- **Code**: S607
- **Sin**: `gh` invoked by partial path.
- **Penance**: gh is PATH-resolved by design (user-installed CLI); availability is pre-checked and unknown is reported as pr=?, never assumed.

### CONF-421
- **File**: [scripts/vscode/tests/test_worktree_board.py](../scripts/vscode/tests/test_worktree_board.py#L18)
- **Code**: E402
- **Sin**: `import now` after `sys.path.insert` — module-level import not at top.
- **Penance**: sibling-spike reuse; the path bootstrap must precede the import (CONF-392 idiom).

### CONF-422
- **File**: [examples/demos/corpus_census/adapters/corpus_adapters.py](../examples/demos/corpus_census/adapters/corpus_adapters.py#L62)
- **Code**: S603
- **Sin**: `subprocess.run` invoking git for the FR-892 git-timeline census adapter.
- **Penance**: Fixed argv list (`git -C <repo> ...`), no shell, 30s timeout, check=True; repo path comes from the operator's --var input, never from LLM output.

### CONF-423
- **File**: [examples/demos/corpus_census/adapters/corpus_adapters.py](../examples/demos/corpus_census/adapters/corpus_adapters.py#L63)
- **Code**: S607
- **Sin**: `git` invoked by partial path in the FR-892 census adapter.
- **Penance**: git is PATH-resolved by design (developer tooling); same pattern as CONF-421.

### CONF-424
- **File**: [scripts/vscode/timesheet.py](../scripts/vscode/timesheet.py#L94)
- **Code**: S608
- **Sin**: `session_id IN (...)` placeholder fragment interpolated into the SQL string.
- **Penance**: The interpolated fragment is only a fixed count of `?` characters generated from `len(session_ids)` — never a value. All actual values (`session_ids`) are bound as query parameters. Read-only connection (`mode=ro`) to the local chronicle DB.

### CONF-425
- **File**: [examples/demos/pattern_model_census/tools/git_tools.py](../examples/demos/pattern_model_census/tools/git_tools.py#L20)
- **Code**: S603
- **Sin**: `subprocess.run` invoking git for the FR-896 pattern/model census discover/extract adapters.
- **Penance**: Fixed argv list (`git -C <repo> ...`), no shell, 30s timeout, check=True; repo path comes from the operator's `--var source=...` input, never from LLM output — same pattern as CONF-422.

### CONF-426
- **File**: [examples/demos/pattern_model_census/tools/git_tools.py](../examples/demos/pattern_model_census/tools/git_tools.py#L21)
- **Code**: S607
- **Sin**: `git` invoked by partial path in the FR-896 census adapter.
- **Penance**: git is PATH-resolved by design (developer tooling); same pattern as CONF-423.

### CONF-427
- **File**: [tests/unit/test_vscode_ledger.py](../tests/unit/test_vscode_ledger.py#L26)
- **Code**: E402
- **Sin**: `import ledger` after a `sys.path.insert` — module-level import not at top.
- **Penance**: script-adjacent test for the scripts/vscode spike suite; the path bootstrap must precede the import (CONF-415 idiom).

### CONF-428
- **File**: [scripts/vscode/tests/test_session_ledger.py](../scripts/vscode/tests/test_session_ledger.py#L30)
- **Code**: E402
- **Sin**: `import session_ledger` after a `sys.path.insert` — module-level import not at top.
- **Penance**: script-adjacent test outside the installable package; path bootstrap must precede the import (CONF-392/393/394/396 idiom).

### CONF-429
- **File**: [scripts/vscode/session_ledger.py](../scripts/vscode/session_ledger.py#L40)
- **Code**: E402
- **Sin**: `from ledger import ...` after a `sys.path.insert` — module-level import not at top.
- **Penance**: script-adjacent module reusing the sibling ledger's price machinery (judged "reuse, don't fork"); path bootstrap must precede the import (CONF-392/393/394/396 idiom).

### CONF-430
- **File**: [examples/demos/corpus_census/adapters/corpus_adapters.py](../examples/demos/corpus_census/adapters/corpus_adapters.py#L102)
- **Code**: S603
- **Sin**: `subprocess.run` invoking gh for the FR-899 org repo census adapters.
- **Penance**: Fixed argv list (`gh repo list`/`gh api`), no shell, 60s timeout, check=True; org and item refs come from operator --var input and the gh API listing, never from LLM output.

### CONF-431
- **File**: [examples/demos/corpus_census/adapters/corpus_adapters.py](../examples/demos/corpus_census/adapters/corpus_adapters.py#L103)
- **Code**: S607
- **Sin**: `gh` invoked by partial path in the FR-899 census adapters.
- **Penance**: gh is PATH-resolved by design (developer tooling); same pattern as CONF-423/426.

### CONF-432
- **File**: [scripts/tests/test_fr858_board_retirement.py](../scripts/tests/test_fr858_board_retirement.py#L27)
- **Code**: S603
- **Sin**: `subprocess.run(["git", "ls-files", ...])` without shell escaping analysis.
- **Penance**: fixed argument list, no user input; `git` is PATH-resolved by design in developer tooling (CONF-423/426/431 pattern). The test must ask git the tracking question — no library answer exists.

### CONF-433
- **File**: [scripts/tests/test_fr858_board_retirement.py](../scripts/tests/test_fr858_board_retirement.py#L45)
- **Code**: S603
- **Sin**: `subprocess.run([sys.executable, "scripts/fr_board.py"])` in the stdout/no-write witness.
- **Penance**: FR-858 AC-04/AC-07 witness the *CLI contract* (stdout only, writes nothing); invoking the module in-process would not exercise the surface under test. `sys.executable` and a literal script path, no user input.

### CONF-434
- **File**: [scripts/tests/test_fr858_board_retirement.py](../scripts/tests/test_fr858_board_retirement.py#L59)
- **Code**: S603
- **Sin**: `subprocess.run([sys.executable, "scripts/fr_board.py", *flag])` proving retired flags are rejected.
- **Penance**: same CLI-contract rationale as CONF-433; `flag` iterates a literal tuple defined in the test, never external input.

### CONF-435
- **File**: [scripts/vscode/now.py](../scripts/vscode/now.py#L416)
- **Code**: PLC0415
- **Sin**: `import fr_board` inside `live_plan_state()` rather than at module top.
- **Penance**: FR-858 — `now.py` is a standalone script; `fr_board` lives in a sibling directory reachable only after a per-repo `sys.path` insert, and the repo under inspection is a runtime argument. A top-level import would bind one repo at import time and break the multi-repo scan.

### CONF-436
- **File**: [scripts/vscode/now.py](../scripts/vscode/now.py#L421)
- **Code**: BLE001
- **Sin**: bare `except Exception` around the live plan-state computation.
- **Penance**: FR-858 C-5 requires that a live-computation failure be *surfaced*, never silently downgraded to stale committed state. The handler names the exception type and message in the output line; a narrower except would let an unanticipated parser error crash a situational-awareness tool whose whole job is to keep reporting.

### CONF-437
- **File**: [tests/unit/test_fr909_a2a_retirement.py](../tests/unit/test_fr909_a2a_retirement.py#L62)
- **Code**: S603
- **Sin**: `subprocess.run(["git", "ls-files", relative_path])` in the FR-909 tracked-absence witness.
- **Penance**: FR-924 — FR-909 AC-01 asks whether git tracks the path; only git can answer. Fixed argument list, `relative_path` iterates a literal module-level list, `git` is PATH-resolved by design in developer tooling (CONF-432 pattern).

### CONF-438
- **File**: [tests/unit/test_fr910_mcp_retirement.py](../tests/unit/test_fr910_mcp_retirement.py#L59)
- **Code**: S603
- **Sin**: `subprocess.run(["git", "ls-files", relative_path])` in the FR-910 tracked-absence witness.
- **Penance**: FR-924 — added alongside (never replacing) FR-910 AC-01's filesystem checks, which C-2 preserves. Same fixed-argument rationale as CONF-437.

### CONF-439
- **File**: [tests/unit/test_fr915_mastra_demo_retirement.py](../tests/unit/test_fr915_mastra_demo_retirement.py#L22)
- **Code**: S603
- **Sin**: `subprocess.run(["git", "ls-files", "examples/demos/mastra-integration/*"])` in the FR-915 witness.
- **Penance**: FR-924 — literal pathspec, no interpolation; same rationale as CONF-437.

### CONF-440
- **File**: [scripts/vscode/session_join.py](../scripts/vscode/session_join.py#L28)
- **Code**: S603
- **Sin**: `subprocess.run` on the git executable to read checkpoint trailers.
- **Penance**: FR-902 — read-only `git log` plumbing with a fixed argument vector; the executable is resolved via `shutil.which("git")` and the only variables are a validated repo path and a `session/<uuid>` ref derived from a UUID-shaped session id. Same idiom as CONF-390.

### CONF-441
- **File**: [.github/hooks/scripts/checks/main_write.py](../.github/hooks/scripts/checks/main_write.py#L57)
- **Code**: S603
- **Sin**: `subprocess.run([GIT, "-C", probe, "rev-parse", …])` — non-constant probe path in the FR-889 main-write classifier.
- **Penance**: read-only `git rev-parse` plumbing with a fixed subcommand vector; GIT resolved via `shutil.which`; the probe path is derived from the hook payload solely to CLASSIFY the write (worktree vs main), list-form argv, no shell. Same idiom as CONF-390/CONF-440; extracted verbatim from the previously unlinted guard heredoc.

### CONF-442
- **File**: [tests/unit/test_fr912_skill_export_retirement.py](../tests/unit/test_fr912_skill_export_retirement.py#L96)
- **Code**: S603
- **Sin**: `subprocess.run(["git", "ls-files", relative_path])` in the FR-912 tracked-absence witness.
- **Penance**: FR-912 — literal pathspec from a module-level constant, no interpolation; same rationale as CONF-437/CONF-438.

### CONF-443
- **File**: [examples/demos/corpus_census/tools.py](../examples/demos/corpus_census/tools.py#L50)
- **Code**: E402
- **Sin**: `import ledger_failures` after a `sys.path.insert` — module-level import not at top.
- **Penance**: FR-943 — demo-local taxonomy module outside the installable package; the REPO_ROOT path bootstrap must precede the import (CONF-427/430 idiom).

### CONF-444
- **File**: [tests/unit/test_lan_recon.py](../tests/unit/test_lan_recon.py#L144)
- **Code**: S104
- **Sin**: `"0.0.0.0"` appears in a `@pytest.mark.parametrize` list.
- **Penance**: FR-945 — the string is a probe TARGET under test, not a bind address; the test asserts that `recon.probe("0.0.0.0", computer_name=...)` raises `UnsafeTargetError` because unspecified addresses are refused. The recon skill never binds a socket.

### CONF-445
- **File**: [.github/skills/lan-delegate/models.py](../.github/skills/lan-delegate/models.py#L64)
- **Code**: S105
- **Sin**: `TOKEN_LEAK_DETECTED = "TOKEN_LEAK_DETECTED"` — ruff flags the string literal as a possible hardcoded password.
- **Penance**: FR-948 — the string is the *name* of a `DelegationPolicyStatus` enum value emitted when a literal `GH_TOKEN` byte match is detected in an artifact; it is a public policy identifier that must equal its symbolic name for wire-format stability. No credential material.

### CONF-446
- **File**: [.github/skills/lan-delegate/delegate.py](../.github/skills/lan-delegate/delegate.py#L114)
- **Code**: S603, S607
- **Sin**: `subprocess.run(["git", "-C", str(workdir), "status", "--porcelain"])` and the sibling `rev-parse HEAD` invocation in FR-948's local-tree-freeze check.
- **Penance**: FR-948 — literal list-form argv, no shell, no user interpolation. `workdir` is a `pathlib.Path` derived from `os.cwd()` (never a caller-supplied argument), and `git` is the standard system-wide tool the FR-945 recon precondition confirms is on PATH; same idiom as CONF-441/442.

### CONF-447
- **File**: [tests/unit/test_lan_delegate_wire.py](../tests/unit/test_lan_delegate_wire.py#L558)
- **Code**: S105
- **Sin**: `assert ps.parameters["Token"] == "gho_test_token_1234"` — ruff flags the string literal as a possible hardcoded password.
- **Penance**: FR-948 — the string is a test fixture proving the WinRM `Token` parameter carries the byte value delegate.py received from the mocked environment. It is a synthetic identifier that starts with the `gho_` prefix so the redaction-test path exercises the actual byte pattern; no real credential material.

### CONF-448
- **File**: [tests/unit/test_lan_delegate_wire.py](../tests/unit/test_lan_delegate_wire.py#L211)
- **Code**: E402
- **Sin**: `import lan_delegate_pkg.errors as errors` after top-level executable code (the `_load("delegate")` call earlier in the file).
- **Penance**: FR-948 — the `.github/skills/lan-delegate/` directory has a dashed package name that cannot be imported statically. The dynamic `_load()` helper materializes it under `lan_delegate_pkg` in `sys.modules`; the E402-flagged import must run AFTER that materialization to see the same class instances delegate.py raises/instantiates. Static import order is impossible here; the wire tests would otherwise trip pydantic's two-module-instances validation error.

### CONF-449
- **File**: [tests/unit/test_lan_delegate_wire.py](../tests/unit/test_lan_delegate_wire.py#L212)
- **Code**: E402
- **Sin**: `import lan_delegate_pkg.models as models` — same delayed-import pattern as CONF-448.
- **Penance**: FR-948 — identical rationale; `LanDelegationRequest` and `LanDelegationResult` referenced in the tests must be the same class instances the delegate module uses, which requires the dynamic package materialization to run first.

### CONF-450
- **File**: [.github/skills/issue-delegate/models.py](../.github/skills/issue-delegate/models.py#L64)
- **Code**: S105
- **Sin**: `TOKEN_LEAK_DETECTED = "TOKEN_LEAK_DETECTED"` — ruff flags the enum value as a possible hardcoded password.
- **Penance**: FR-949 — the string is a closed-enum status literal naming the leak-detection outcome, mirroring CAP-257's identical member (CONF pattern from FR-948); no credential material.

### CONF-451
- **File**: [.github/skills/issue-delegate/worker.py](../.github/skills/issue-delegate/worker.py#L67)
- **Code**: S506
- **Sin**: `yaml.load(blocks[0], Loader=_StrictLoader)` — ruff cannot see that `_StrictLoader` is safe.
- **Penance**: FR-949 — `_StrictLoader` subclasses `yaml.SafeLoader` solely to refuse duplicate mapping keys (AC-04); `yaml.safe_load` cannot express duplicate-key refusal, and the loader adds no constructors beyond the safe set.

### CONF-452
- **File**: [yamlgraph/node_factory/copilot_runtime_claude.py](../yamlgraph/node_factory/copilot_runtime_claude.py#L114)
- **Code**: S603
- **Sin**: `subprocess.run(argv, ...)` in the version/auth probe runner with a non-constant argument list.
- **Penance**: FR-959 — argv is always a Python list (no shell), the executable and flag names are literals, and every variable element comes from `ClaudeCliFlags` (strict Pydantic, extra keys forbidden) or from the rendered prompt as one list element (REQ-YG-087 discipline, byte-for-byte argv tests in `tests/unit/test_fr959_claude_backend.py`). The child environment is the stripped copy built by `_build_claude_env`, never a caller-supplied mapping.

### CONF-453
- **File**: [yamlgraph/node_factory/copilot_runtime_claude.py](../yamlgraph/node_factory/copilot_runtime_claude.py#L266)
- **Code**: S603
- **Sin**: `subprocess.run(cmd, ...)` for the `claude -p` agent call with a non-constant argument list.
- **Penance**: FR-959 — same argv discipline as CONF-452: list form, literal executable/flags, prompt passed as one list element, stripped `_build_claude_env` environment.

### CONF-454
- **File**: [yamlgraph/node_factory/copilot_runtime_claude.py](../yamlgraph/node_factory/copilot_runtime_claude.py#L69)
- **Code**: N815
- **Sin**: `loggedIn: bool` — camelCase field in `_ClaudeAuthStatus`.
- **Penance**: FR-959 — the field mirrors the vendor's `claude auth status` JSON key verbatim; renaming would require alias plumbing for a private parse-only model.

### CONF-455
- **File**: [yamlgraph/node_factory/copilot_runtime_claude.py](../yamlgraph/node_factory/copilot_runtime_claude.py#L70)
- **Code**: N815
- **Sin**: `authMethod: str` — camelCase field in `_ClaudeAuthStatus`.
- **Penance**: FR-959 — same vendor-JSON mirroring rationale as CONF-454.

### CONF-456
- **File**: [yamlgraph/node_factory/copilot_runtime_claude.py](../yamlgraph/node_factory/copilot_runtime_claude.py#L71)
- **Code**: N815
- **Sin**: `apiProvider: str` — camelCase field in `_ClaudeAuthStatus`.
- **Penance**: FR-959 — same vendor-JSON mirroring rationale as CONF-454.

### CONF-457
- **File**: [examples/demos/cap_journey_census/tools.py](../examples/demos/cap_journey_census/tools.py#L28)
- **Code**: E402
- **Sin**: `from examples.demos.cap_journey_census.extract import …` after a `sys.path.insert` — module-level import not at top.
- **Penance**: CAP journey census (docs/2026-09-05-research-plan-cap-journey-census.md) — demo-local split to stay under the 450-line gate; the REPO_ROOT path bootstrap must precede the import (CONF-443 idiom).

### CONF-458
- **File**: [examples/demos/cap_journey_census/tools.py](../examples/demos/cap_journey_census/tools.py#L32)
- **Code**: E402
- **Sin**: `from examples.demos.cap_journey_census.render import _markdown` after a `sys.path.insert` — module-level import not at top.
- **Penance**: Same split as CONF-457 (rendering moved to render.py for the size gate); same bootstrap ordering.

### CONF-459
- **File**: [docs/spikes/outsider-llm-2026-09-05/tools.py](../docs/spikes/outsider-llm-2026-09-05/tools.py#L51)
- **Code**: S603
- **Sin**: `subprocess.run([gh, "pr", "view", pr, "-R", repo, …])` — external `pr`/`repo` reach a subprocess.
- **Penance**: Spike record (research plan §13). argv list, no shell; `gh` resolved via `shutil.which`; `pr` must match `^\d{1,7}$` and `repo` `^owner/name$` before the call (`_pr_and_repo`). `docs/spikes/**` has no per-file ignore, unlike `examples/**`/`scripts/**` — confessed rather than widening the ignore list.

### CONF-460
- **File**: [docs/spikes/outsider-llm-2026-09-05/tools.py](../docs/spikes/outsider-llm-2026-09-05/tools.py#L144)
- **Code**: S603
- **Sin**: `subprocess.run([gh, "pr", "comment", pr, "-R", repo, "--body-file", …])` — same arguments reach a subprocess.
- **Penance**: Same validation as CONF-459; only runs when `--post` is given.

### CONF-461
- **File**: [tests/unit/test_fr1014_authoring_proof_dir_graphs.py](../tests/unit/test_fr1014_authoring_proof_dir_graphs.py#L67)
- **Code**: S102
- **Sin**: `exec()` of the `def governed_path` text extracted from `.github/hooks/scripts/pre-command-guard.sh`'s Python heredoc.
- **Penance**: FR-1014 witness: the predicate lives inside a bash heredoc and cannot be imported; executing the repository's own hook source (read from the tree, not from input) is the only way to assert it row-for-row against `check_authoring_proof.GOVERNED` on hosts that cannot exec the bash hook. Namespace is limited to `re`.
