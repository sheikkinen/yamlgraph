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
- **File**: [yamlgraph/executor_async.py](../yamlgraph/executor_async.py#L310)
- **Code**: ANN001 (missing type annotation for function argument)
- **Sin**: `state` parameter in `_get_interrupt_payload()` has no type annotation.
- **Penance**: The type is `langgraph.pregel.types.StateSnapshot` which is a private API. Importing it would couple us to LangGraph internals. The function only accesses `.tasks` and `.interrupts` attributes, which are stable across versions.

### CONF-004
- **File**: [yamlgraph/a2a_server.py](../yamlgraph/a2a_server.py#L43)
- **Code**: F401
- **Sin**: Re-imports from `a2a_message` appear unused in `a2a_server.py`.
- **Penance**: These are public re-exports for backward compatibility — tests and external consumers import from `yamlgraph.a2a_server`. The actual logic lives in `yamlgraph.a2a_message` after the module split to stay under 450 lines.

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
- **File**: [yamlgraph/node_factory/copilot_runtime.py](../yamlgraph/node_factory/copilot_runtime.py#L136)
- **Code**: S603
- **Sin**: `subprocess.run(cmd, ...)` in extracted copilot CLI runtime helper is flagged as untrusted input.
- **Penance**: Command is built as a list (no shell=True), with fixed executable/flags plus validated node configuration (`model`, `resume`, `continue_session`, `timeout`). No raw user input is interpolated into shell commands.

### CONF-009
- **File**: [yamlgraph/utils/template.py](../yamlgraph/utils/template.py#L48)
- **Code**: S701
- **Sin**: Jinja2 `Environment()` without `autoescape=True`.
- **Penance**: Used for YAML prompt template variable extraction, not HTML rendering. Autoescape would corrupt prompt text by escaping `<`, `>`, `&` characters. No web output is generated from this code path.

### CONF-010
- **File**: [yamlgraph/executor_base.py](../yamlgraph/executor_base.py#L128)
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
- **File**: [yamlgraph/node_factory/llm_nodes.py](../yamlgraph/node_factory/llm_nodes.py#L294)
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
- **File**: [tests/unit/test_req_coverage_ast.py](../tests/unit/test_req_coverage_ast.py#L17)
- **Code**: E402
- **Sin**: Import after `sys.path.insert` for scripts module.
- **Penance**: Test file needs to import from scripts/ which is not a package.

### CONF-020
- **File**: [tests/unit/test_fr027_execution_safety.py](../tests/unit/test_fr027_execution_safety.py#L804)
- **Code**: E731 (do not assign a lambda expression)
- **Sin**: Lambda assigned to variable for signal handler test.
- **Penance**: Lambda is cleaner than def for trivial no-op handler in test fixture. Accepted for test code.

### CONF-021
- **File**: [tests/unit/test_tavily_rag.py](../tests/unit/test_tavily_rag.py#L84)
- **Code**: F401
- **Sin**: Import `tavily_retrieve` after `sys.path.insert` appears unused (used via module reload).
- **Penance**: Import triggers module loading for test; removing it breaks the test.

### CONF-022
- **File**: [tests/unit/test_tavily_rag.py](../tests/unit/test_tavily_rag.py#L127)
- **Code**: F401
- **Sin**: Same as CONF-021 — import for domain-scoping test.
- **Penance**: Same as CONF-021.

### CONF-023
- **File**: [tests/unit/test_tavily_rag.py](../tests/unit/test_tavily_rag.py#L161)
- **Code**: F401
- **Sin**: Same as CONF-021 — import for no-domain fallback test.
- **Penance**: Same as CONF-021.

### CONF-024
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L20)
- **Code**: E402
- **Sin**: noqa pattern inside test fixture string — testing the noqa detector.
- **Penance**: Test fixture strings must contain realistic patterns to test detection.

### CONF-025
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L30)
- **Code**: F401
- **Sin**: Same as CONF-024 — noqa pattern inside test fixture string.
- **Penance**: Same as CONF-024.

### CONF-026
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L30)
- **Code**: F403
- **Sin**: Same as CONF-024 — noqa pattern inside test fixture string.
- **Penance**: Same as CONF-024.

### CONF-027
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L42)
- **Code**: ALL
- **Sin**: Same as CONF-024 — blanket noqa pattern inside test fixture string.
- **Penance**: Same as CONF-024.

### CONF-028
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L53)
- **Code**: E402
- **Sin**: Same as CONF-024 — noqa pattern inside test fixture string.
- **Penance**: Same as CONF-024.

### CONF-029
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L55)
- **Code**: F401
- **Sin**: Same as CONF-024 — noqa pattern inside test fixture string.
- **Penance**: Same as CONF-024.

### CONF-030
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L68)
- **Code**: E402
- **Sin**: Same as CONF-024 — noqa pattern inside test fixture string.
- **Penance**: Same as CONF-024.

### CONF-031
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L135)
- **Code**: E402
- **Sin**: Same as CONF-024 — noqa pattern inside confessions test fixture.
- **Penance**: Same as CONF-024.

### CONF-032
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L164)
- **Code**: E402
- **Sin**: Same as CONF-024 — noqa pattern inside documented entry test fixture.
- **Penance**: Same as CONF-024.

### CONF-033
- **File**: [tests/unit/test_noqa_coverage.py](../tests/unit/test_noqa_coverage.py#L188)
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
- **File**: [tests/unit/test_fr321_yamlgraph_async_subprocess_exec.py](../tests/unit/test_fr321_yamlgraph_async_subprocess_exec.py#L10)
- **Code**: E402
- **Sin**: Import `YamlgraphAsyncAction` after `pytest.importorskip("statemachine_engine")` guard.
- **Penance**: Same pattern as CONF-037. The `statemachine_engine` package is a local dependency not installed in CI; `importorskip` must execute before the action import to skip gracefully.

### CONF-048
- **File**: [yamlgraph/tools/agent.py](../yamlgraph/tools/agent.py#L166)
- **Code**: C901
- **Sin**: `create_agent_node` has high cyclomatic complexity due to tool registration loop, LLM config resolution, multi-turn message handling, agent iteration loop with tool calls, and structured output extraction.
- **Penance**: The function is a factory that builds a closure capturing configuration. The inner `node_fn` orchestrates the agent loop which is inherently sequential and branching. Splitting further would scatter the closure's captured variables across multiple functions with no clarity gain.

### CONF-049
- **File**: [yamlgraph/cli/__init__.py](../yamlgraph/cli/__init__.py#L329)
- **Code**: S104
- **Sin**: Binding A2A server to `0.0.0.0` (all interfaces) as default.
- **Penance**: A2A server is a development tool that must be network-accessible for agent-to-agent communication. The default matches standard server practice (FastAPI, uvicorn). Production deployments control binding via `--host` flag.

### CONF-050
- **File**: [tests/unit/test_fr651_654_worldgen_improvements.py](../tests/unit/test_fr651_654_worldgen_improvements.py#L26)
- **Code**: ANN202
- **Sin**: Missing return type annotation on `_load()` helper.
- **Penance**: Same pattern as CONF-037 et al. Returns dynamically-loaded module whose type is `types.ModuleType` but annotating gains nothing in test helper context.

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
- **File**: [tests/unit/test_fr637_novel_fandom_canon.py](../tests/unit/test_fr637_novel_fandom_canon.py#L33)
- **Code**: ANN202
- **Sin**: `_load()` helper returns `types.ModuleType` but annotated with `# noqa: ANN202`.
- **Penance**: Internal test helper; the return type varies dynamically depending on which module is loaded. Type annotation would be `types.ModuleType` which adds no value to callers that immediately destructure attributes.

### CONF-337
- **File**: [tests/unit/test_fr640_novel_fandom_enriched.py](../tests/unit/test_fr640_novel_fandom_enriched.py#L27)
- **Code**: ANN202
- **Sin**: `_load()` helper returns `types.ModuleType` but annotated with `# noqa: ANN202`.
- **Penance**: Same as CONF-336 — internal test helper, dynamically loaded module, type annotation adds no value.

### CONF-338
- **File**: [tests/unit/test_fr638_novel_fandom_pathfinder.py](../tests/unit/test_fr638_novel_fandom_pathfinder.py#L25)
- **Code**: ANN202
- **Sin**: `_load()` helper returns `types.ModuleType` but annotated with `# noqa: ANN202`.
- **Penance**: Same as CONF-336 — internal test helper, dynamically loaded module, type annotation adds no value.

### CONF-339
- **File**: [tests/unit/test_fr639_novel_fandom_close_loop.py](../tests/unit/test_fr639_novel_fandom_close_loop.py#L27)
- **Code**: ANN202
- **Sin**: `_load()` helper returns `types.ModuleType` but annotated with `# noqa: ANN202`.
- **Penance**: Same as CONF-336 — internal test helper, dynamically loaded module, type annotation adds no value.

### CONF-340
- **File**: [tests/unit/test_fr642_novel_fandom_wiki_core.py](../tests/unit/test_fr642_novel_fandom_wiki_core.py#L27)
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
- **File**: [tests/unit/test_fr296_watcher_fsm_startup_script.py](../tests/unit/test_fr296_watcher_fsm_startup_script.py#L116)
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
- **File**: [yamlgraph/a2a_message.py](../yamlgraph/a2a_message.py#L120)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-220
- **File**: [yamlgraph/a2a_message.py](../yamlgraph/a2a_message.py#L66)
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
- **File**: [yamlgraph/edge_compiler.py](../yamlgraph/edge_compiler.py#L229)
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
- **File**: [yamlgraph/linter/checks_semantic.py](../yamlgraph/linter/checks_semantic.py#L266)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-236
- **File**: [yamlgraph/linter/checks_semantic.py](../yamlgraph/linter/checks_semantic.py#L278)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-237
- **File**: [yamlgraph/linter/checks_semantic.py](../yamlgraph/linter/checks_semantic.py#L289)
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
- **File**: [yamlgraph/models/graph_schema.py](../yamlgraph/models/graph_schema.py#L73)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-241
- **File**: [yamlgraph/node_factory/copilot_node.py](../yamlgraph/node_factory/copilot_node.py#L83)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-242
- **File**: [yamlgraph/node_factory/llm_execution.py](../yamlgraph/node_factory/llm_execution.py#L134)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-243
- **File**: [yamlgraph/node_factory/llm_nodes.py](../yamlgraph/node_factory/llm_nodes.py#L125)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-244
- **File**: [yamlgraph/node_factory/llm_nodes.py](../yamlgraph/node_factory/llm_nodes.py#L126)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-245
- **File**: [yamlgraph/node_factory/llm_nodes.py](../yamlgraph/node_factory/llm_nodes.py#L159)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-246
- **File**: [yamlgraph/node_factory/llm_nodes.py](../yamlgraph/node_factory/llm_nodes.py#L57)
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
- **File**: [yamlgraph/utils/prompts.py](../yamlgraph/utils/prompts.py#L138)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-253
- **File**: [yamlgraph/utils/prompts.py](../yamlgraph/utils/prompts.py#L50)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-254
- **File**: [yamlgraph/utils/prompts.py](../yamlgraph/utils/prompts.py#L66)
- **Code**: FB001
- **Sin**: Contains lexical `fallback` token flagged by FR-418 fallback-token hygiene gate.
- **Penance**: Retained intentionally for domain semantics or existing contract wording; explicitly allowlisted and audited.

### CONF-304
- **File**: [yamlgraph/tools/agent.py](../yamlgraph/tools/agent.py#L42)
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
- **File**: [yamlgraph/tools/agent.py](../yamlgraph/tools/agent.py#L51)
- **Code**: FB001
- **Sin**: Comment uses `fallback` token describing a legitimate fallback trigger condition.
- **Penance**: Documents the structured-output mismatch recovery path. Renaming would obscure intent.

### CONF-351
- **File**: [yamlgraph/executor_base.py](../yamlgraph/executor_base.py#L335)
- **Code**: FB001
- **Sin**: Docstring of `_invoke_llm_once` contains `fallback` — describes the FR-464 structured-output fallback strategy.
- **Penance**: Documents the retry-then-parse pattern. Renaming would obscure intent.

### CONF-352
- **File**: [yamlgraph/utils/llm_providers.py](../yamlgraph/utils/llm_providers.py#L315)
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
- **File**: [yamlgraph/executor_base.py](../yamlgraph/executor_base.py#L130)
- **Code**: C901
- **Sin**: `_invoke_llm` function exceeds cyclomatic complexity threshold.
- **Penance**: Central LLM invocation dispatch handles multiple provider paths and structured output. Splitting would fragment the core execution flow without reducing actual complexity.

### CONF-365
- **File**: [yamlgraph/tools/agent.py](../yamlgraph/tools/agent.py#L94)
- **Code**: C901
- **Sin**: Agent tool handler exceeds cyclomatic complexity threshold.
- **Penance**: Agent node orchestration is inherently complex — tool dispatch, error handling, streaming. Splitting would obscure the sequential logic.

### CONF-373
- **File**: [tests/unit/test_fr713_persistent_bridge.py](../tests/unit/test_fr713_persistent_bridge.py#L288)
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
- **File**: [yamlgraph/utils/bridge.py](../yamlgraph/utils/bridge.py#L138)
- **Code**: BLE001
- **Sin**: `_deliver` catches `BaseException` around the awaited coroutine.
- **Penance**: Verdict transport — every outcome including CancelledError must cross the thread boundary to the caller's Future; swallowing nothing, relabeling nothing. Same contract as the FR-707 bridge it replaces.

### CONF-377
- **File**: [yamlgraph/utils/template.py](../yamlgraph/utils/template.py#L48)
- **Code**: B701
- **Sin**: Jinja2 `Environment()` constructed with `autoescape=False` (default).
- **Penance**: Templates render LLM prompt text, never HTML — autoescaping would corrupt prompts containing markup-like characters. XSS requires a browser sink; there is none.

### CONF-378
- **File**: [yamlgraph/cli/__init__.py](../yamlgraph/cli/__init__.py#L329)
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
