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
- **File**: [scripts/diary_rotate.py](../scripts/diary_rotate.py#L95)
- **Code**: S603
- **Sin**: `subprocess.run(["git", "add", ...])` flagged as untrusted input.
- **Penance**: Command and args are hardcoded; only file paths from `Path` objects are passed. No user input reaches the shell.

---

## Framework Code

Framework suppressions require elevated scrutiny. These live in `yamlgraph/`.

### CONF-002
- **File**: [yamlgraph/utils/token_tracker.py](../yamlgraph/utils/token_tracker.py#L51)
- **Code**: ARG002 (unused method argument)
- **Sin**: `kwargs` parameter unused in callback handler.
- **Penance**: Required by LangChain callback interface (`BaseCallbackHandler.on_llm_end`). Cannot remove without breaking signature compatibility.

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
