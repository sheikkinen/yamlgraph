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
- **File**: [scripts/migrate_capabilities.py](../scripts/migrate_capabilities.py#L349)
- **Code**: E402
- **Sin**: Module-level import `from req_coverage import CAPABILITIES` appears after `sys.path.insert()` manipulation.
- **Penance**: The import must occur after sys.path is modified to find `req_coverage.py` in the scripts directory. This is standard Python pattern for runtime path manipulation.

---

## Framework Code

Framework suppressions require elevated scrutiny. These live in `yamlgraph/`.

### CONF-002
- **File**: [yamlgraph/utils/token_tracker.py](../yamlgraph/utils/token_tracker.py#L51)
- **Code**: ARG002 (unused method argument)
- **Sin**: `kwargs` parameter unused in callback handler.
- **Penance**: Required by LangChain callback interface (`BaseCallbackHandler.on_llm_end`). Cannot remove without breaking signature compatibility.

### CONF-003
- **File**: [yamlgraph/executor_async.py](../yamlgraph/executor_async.py#L310)
- **Code**: ANN001 (missing type annotation for function argument)
- **Sin**: `state` parameter in `_get_interrupt_payload()` has no type annotation.
- **Penance**: The type is `langgraph.pregel.types.StateSnapshot` which is a private API. Importing it would couple us to LangGraph internals. The function only accesses `.tasks` and `.interrupts` attributes, which are stable across versions.

### CONF-004
- **File**: [yamlgraph/a2a_server.py](../yamlgraph/a2a_server.py#L44)
- **Code**: F401
- **Sin**: Re-imports from `a2a_message` appear unused in `a2a_server.py`.
- **Penance**: These are public re-exports for backward compatibility — tests and external consumers import from `yamlgraph.a2a_server`. The actual logic lives in `yamlgraph.a2a_message` after the module split to stay under 450 lines.

### CONF-005
- **File**: [yamlgraph/cli/__init__.py](../yamlgraph/cli/__init__.py#L207)
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
- **File**: [yamlgraph/node_factory/copilot_node.py](../yamlgraph/node_factory/copilot_node.py#L260)
- **Code**: S603
- **Sin**: `subprocess.run(cmd, ...)` flagged as untrusted input.
- **Penance**: The `cmd` list is built entirely from hardcoded strings (`"gh"`, `"copilot"`, `"suggest"`) plus internal config flags. No user input reaches the command arguments.

### CONF-009
- **File**: [yamlgraph/utils/template.py](../yamlgraph/utils/template.py#L47)
- **Code**: S701
- **Sin**: Jinja2 `Environment()` without `autoescape=True`.
- **Penance**: Used for YAML prompt template variable extraction, not HTML rendering. Autoescape would corrupt prompt text by escaping `<`, `>`, `&` characters. No web output is generated from this code path.

### CONF-035
- **File**: [yamlgraph/utils/worktree_helpers.py](../yamlgraph/utils/worktree_helpers.py#L94)
- **Code**: S607
- **Sin**: `["git", "diff", "--name-only"]` uses partial executable path.
- **Penance**: `git` is expected on PATH in all development environments. Using absolute path would break portability across OS/distro.

### CONF-036
- **File**: [yamlgraph/utils/worktree_helpers.py](../yamlgraph/utils/worktree_helpers.py#L105)
- **Code**: S607
- **Sin**: `["git", "diff", "--cached", "--name-only"]` uses partial executable path.
- **Penance**: Same as CONF-035.

### CONF-037
- **File**: [yamlgraph/utils/worktree_helpers.py](../yamlgraph/utils/worktree_helpers.py#L93)
- **Code**: S603
- **Sin**: `subprocess.run()` called with list argument flagged as untrusted input.
- **Penance**: Command list is hardcoded `["git", "diff", "--name-only"]` — no user input reaches arguments. Used to detect unstaged changes before worktree operations.

### CONF-038
- **File**: [yamlgraph/utils/worktree_helpers.py](../yamlgraph/utils/worktree_helpers.py#L104)
- **Code**: S603
- **Sin**: `subprocess.run()` called with list argument flagged as untrusted input.
- **Penance**: Same as CONF-037 — hardcoded `["git", "diff", "--cached", "--name-only"]` for staged change detection.

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

### CONF-123
- **File**: [projects/incaller/nodes/twilio_inbound.py](../projects/incaller/nodes/twilio_inbound.py#L38)
- **Code**: E402
- **Sin**: Import from outcaller after logger/env setup at module level.
- **Penance**: REQ-YG-086 requires reusing outcaller nodes. Import must follow env setup that loads incaller's `.env` to avoid polluting outcaller's env vars. Standard pattern matching CONF-015+ (example imports after path setup).

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

### CONF-208
- **File**: [scripts/validate_id_registry.py](../scripts/validate_id_registry.py#L28)
- **Code**: E402
- **Sin**: Import from `yamlgraph.utils.id_registry` after `sys.path.insert()`.
- **Penance**: The `sys.path` modification is required before the import so `yamlgraph` is resolvable when running the script standalone. Standard pattern for repo scripts.

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
