# Chapter 02: Pre-commit Gates

> *"What survives the fire may merge."*

Every commit in YAMLGraph must pass through a gauntlet of automated checks before it is accepted into the repository. These are not optional guidelines — they are enforced gates. If any hook fails, the commit is rejected. This chapter walks through each gate, explains the scripts that power them, and shows what happens when you run `git commit`.

---

## Why Pre-commit Hooks?

A bug caught at commit time costs minutes. The same bug caught in production costs hours, reputation, and sometimes data. YAMLGraph's pre-commit hooks encode the project's quality doctrine as executable checks: linting, formatting, testing, coverage traceability, dead code detection, duplication analysis, complexity gates, and commit message enforcement.

The hooks run automatically via [pre-commit](https://pre-commit.com/), configured in `.pre-commit-config.yaml` with `fail_fast: true` — the first failure stops the pipeline. This keeps the feedback loop tight: fix the nearest problem first.

Installation requires two commands:

```bash
pre-commit install                      # pre-commit stage hooks
pre-commit install --hook-type commit-msg  # commit-msg stage hooks
```

---

## Hook Configuration

As defined in `.pre-commit-config.yaml`, YAMLGraph configures **27 hooks** across three stages: `pre-commit`, `commit-msg`, and `post-commit` (with absolution running in two stages). The `fail_fast: true` setting ensures the pipeline short-circuits on the first failure.

### Pre-commit Stage Hooks

These hooks run before the commit is created. Every one must pass.

| # | Hook ID | Name | Source | Purpose |
|---|---------|------|--------|---------|
| 1 | `ruff` | Ruff linter | `astral-sh/ruff-pre-commit` | Lint Python with auto-fix (`--fix --exit-non-zero-on-fix`) |
| 2 | `ruff-format` | Ruff formatter | `astral-sh/ruff-pre-commit` | Enforce consistent code formatting |
| 3 | `trailing-whitespace` | Trailing whitespace | `pre-commit/pre-commit-hooks` | Strip trailing whitespace from all files |
| 4 | `end-of-file-fixer` | End-of-file fixer | `pre-commit/pre-commit-hooks` | Ensure files end with a newline |
| 5 | `check-yaml` | Check YAML | `pre-commit/pre-commit-hooks` | Validate YAML syntax |
| 6 | `check-added-large-files` | Check large files | `pre-commit/pre-commit-hooks` | Block accidentally committed large files |
| 7 | `check-merge-conflict` | Check merge conflict | `pre-commit/pre-commit-hooks` | Detect unresolved merge conflict markers |
| 8 | `check-ast` | Check AST | `pre-commit/pre-commit-hooks` | Validate Python files parse correctly |
| 9 | `check-toml` | Check TOML | `pre-commit/pre-commit-hooks` | Validate TOML syntax (`pyproject.toml`) |
| 10 | `debug-statements` | Debug statements | `pre-commit/pre-commit-hooks` | Block `breakpoint()`, `pdb.set_trace()` |
| 11 | `detect-private-key` | Detect private key | `pre-commit/pre-commit-hooks` | Prevent committing secrets |
| 12 | `diary-rotate` | Diary rotation | Local | Rotate `docs/diary.md` on day change; import scheduled entries |
| 13 | `req-coverage-strict` | Requirement coverage | Local | Verify all REQ-YG-XXX requirements have tests (`--strict`) |
| 14 | `noqa-confession` | noqa audit | Local | Verify all `# noqa` suppressions are documented (`--strict`) |
| 15 | `inline-llm-check` | Inline LLM check | Local | Detect scripts that bypass YAMLGraph's three-layer architecture |
| 16 | `radon-complexity` | Radon CC gate | Local | Block functions with cyclomatic complexity ≥ 21 (grade D) |
| 17 | `file-size-gate` | File size gate | Local | Error on files > 450 lines; warn > 400 lines |
| 18 | `forbid-terms` | Forbid terms | Local | Block `TODO`, `FIXME`, `backward compatibility` in source |
| 19 | `jscpd-dup` | jscpd duplicate check | Local | Detect code duplication (threshold 10%, min 10 lines/80 tokens) |
| 20 | `vulture-dead-code` | Vulture dead code | Local | Detect unused code with ≥ 80% confidence |
| 21 | `hedging-check` | Hedging check | Local | Detect silent-fallback patterns that mask bugs |
| 22 | `pytest` | pytest (unit) | Local | Run unit tests (`tests/unit/`) with short traceback |

### Commit-msg Stage Hooks

These hooks validate the commit message after you write it.

| # | Hook ID | Name | Purpose |
|---|---------|------|---------|
| 23 | `conventional-pre-commit` | Conventional commits | Enforce conventional commit format (`feat`, `fix`, `chore`, `docs`, etc.) |
| 24 | `feat-requires-fr` | FR reference check | Require `FR-XXX` reference in all `feat:` commits |
| 25 | `changelog-required` | CHANGELOG required | Require `CHANGELOG.md` changes in `feat:` and `fix:` commits |

### Dual-stage Hook

| # | Hook ID | Name | Stages | Purpose |
|---|---------|------|--------|---------|
| 26 | `absolution` | Absolution | `pre-commit`, `commit-msg` | Final summary; grants absolution with Distill reminder |

### Post-commit Stage Hook

| # | Hook ID | Name | Purpose |
|---|---------|------|---------|
| 27 | `inquisitor-background` | Inquisitor | Async background audit after commit completes |

---

## Key Scripts

Four custom Python scripts form the backbone of YAMLGraph's quality gates. Each enforces a specific doctrine from the project's Scripture.

### absolution.py — The Final Blessing

**Purpose:** The last hook to run in both `pre-commit` and `commit-msg` stages. If execution reaches this script, all prior gates have passed.

**When it runs:** Stages `pre-commit` and `commit-msg`, configured with `verbose: true` so its output always displays.

**Key logic:** The script is deliberately minimal — it prints a success message and a reminder to practice the Distill step from the Sermon of the Chaplain.

As defined in `scripts/absolution.py`:

```python
def main() -> int:
    """Grant absolution with Distill reminder."""
    print()
    print("✓ Absolution granted")
    print()
    print(
        "**Distill.** After completing a task list, add a metacognitive entry to docs/diary.md."
    )
    print("Name the cognitive trap or insight. Extract a heuristic.")
    print("Plant a seed — a forward-looking question to grow new ideas.")
    print("If the heuristic proves recurring, graduate it to the Scripture.")
    print()
    return 0
```

**Example output:**

```
✓ Absolution granted

**Distill.** After completing a task list, add a metacognitive entry to docs/diary.md.
Name the cognitive trap or insight. Extract a heuristic.
Plant a seed — a forward-looking question to grow new ideas.
If the heuristic proves recurring, graduate it to the Scripture.
```

The absolution pattern serves a dual purpose: it confirms that the full gauntlet passed, and it nudges the developer to reflect — turning every commit into a potential learning moment.

---

### req_coverage.py — Requirement Traceability

**Purpose:** Verify that every requirement defined in `ARCHITECTURE.md` has at least one test tagged with `@pytest.mark.req("REQ-YG-XXX")`. This is the enforcement arm of ADR-001 (Requirement Traceability).

**When it runs:** Pre-commit stage with `--strict` flag (exit code 1 on gaps).

**Key logic:** As defined in `scripts/req_coverage.py`, the script:

1. **Defines the canonical requirement set** — `ALL_REQS` lists every valid `REQ-YG-XXX` identifier, grouped by capability (CAP-01 through CAP-32).

2. **Scans test files via AST parsing** — walks `tests/unit/` and `tests/integration/`, parsing each `test_*.py` file's abstract syntax tree to find `@pytest.mark.req(...)` decorators. This is more reliable than regex — it handles multi-argument decorators, class-level markers inherited by methods, and nested class structures.

3. **Compares against the canon** — any requirement in `ALL_REQS` not found in any test decorator is reported as uncovered.

4. **Reports per-capability coverage** — groups results by capability for a high-level view:

```
CAPABILITY COVERAGE
----------------------------------------------------------------------
  ✅ CAP-01 Config Loading & Validation: 4/4 reqs, 12 tests
  ✅ CAP-02 Graph Compilation: 4/4 reqs, 8 tests
  ⚠️  CAP-14 Graph-Level Streaming: 2/3 reqs, 5 tests
  ❌ CAP-25 Tavily Domain RAG Demo: 0/1 reqs, 0 tests
```

**Advanced modes:**

- `--detail` — lists every test function mapped to each requirement
- `--implementation` — traces the full chain: requirement → source files → tests, using `.coverage` SQLite database with AST-based import analysis as fallback
- `--strict` — exits with code 1 if any requirement lacks test coverage (the mode used by the pre-commit hook)

**Example output (strict mode, failure):**

```
======================================================================
REQUIREMENT TRACEABILITY REPORT
======================================================================

Requirements: 85/87 covered
Tagged tests: 312 unique, 489 test-req pairs

UNCOVERED REQUIREMENTS (2)
----------------------------------------------------------------------
  ❌ REQ-YG-076
  ❌ REQ-YG-091
```

When adding a new capability to YAMLGraph, the workflow is:

1. Add requirements to `ARCHITECTURE.md`
2. Extend `_ALL_FRAMEWORK_REQS` range and `CAPABILITIES` dict in `req_coverage.py`
3. Write tests tagged with the new requirement IDs
4. The pre-commit hook verifies the chain is complete

---

### noqa_coverage.py — The Confession Gate

**Purpose:** Every `# noqa` suppression in the codebase must be documented in `docs/confessions.md` with a structured confession entry. Undocumented suppressions are rejected.

**When it runs:** Pre-commit stage with `--strict` flag.

**Key logic:** As defined in `scripts/noqa_coverage.py`, the script performs a two-sided audit:

1. **Scan the codebase** — walks `yamlgraph/`, `tests/`, `examples/`, and `scripts/` for all `# noqa` comments, extracting the file path, line number, and error code(s). Handles both specific suppressions (`# noqa: E402`) and blanket suppressions (`# noqa`).

2. **Parse confessions.md** — reads the confession registry, extracting structured entries that follow this format:

   ```markdown
   ### CONF-001
   - **File**: [path/file.py](../path/file.py#L145)
   - **Code**: S603
   - **Sin**: Subprocess call without shell=True validation
   - **Penance**: Input is controlled; only git commands with known arguments
   ```

3. **Cross-reference** — every noqa in the codebase must have a matching confession entry (matched by file path, line number, and error code). Unmatched suppressions are flagged.

**Example output (strict mode, failure):**

```
============================================================
noqa Confession Coverage Report
============================================================

Total noqa in codebase:     14
Documented confessions:     12
Undocumented:               2

------------------------------------------------------------
❌ Undocumented noqa (add to docs/confessions.md):
------------------------------------------------------------
  yamlgraph/tools/shell.py:45 (S603)
  scripts/diary_rotate.py:98 (S603)

Each noqa requires a confession entry with:
  - CONF-XXX identifier
  - File path with line number
  - Error code being suppressed
  - Sin (what the code does)
  - Penance (why it's acceptable)

FAIL -- undocumented noqa detected
See docs/confessions.md for how to confess your sins and beg forgiveness.
```

The confession pattern transforms lint suppressions from hidden technical debt into documented, reviewed decisions. Every suppression has a rationale, and that rationale is version-controlled alongside the code.

---

### diary_rotate.py — Diary Lifecycle Management

**Purpose:** Automatically rotate `docs/diary.md` when the calendar day changes, archiving the previous diary and creating a fresh one. Also imports scheduled entries from external automation pipelines.

**When it runs:** Pre-commit stage, `always_run: true`. Runs on every commit regardless of which files changed.

**Key logic:** As defined in `scripts/diary_rotate.py`, the script:

1. **Detects day change** — parses `## YYYY-MM-DD:` headers in `docs/diary.md` to find the most recent entry date. If it is before today, rotation is triggered.

2. **Archives the old diary** — moves `docs/diary.md` to `docs/diary-YYYY-MM-DD.md` (with `-N` suffix if the filename already exists). Creates a fresh diary with a `Previous:` link to the archive.

3. **Imports scheduled entries** — checks `~/scheduled-yamlgraphs/outputs/` for pending diary entries (from automated World Digest and Git Report pipelines). Converts their format and appends them to the diary.

4. **Stages files** — runs `git add` on both the archive and new diary so the rotation is included in the current commit.

**Example output (rotation triggered):**

```
📥 Imported diary_entry_20260225.md → docs/diary.md
📓 Rotating diary: docs/diary.md → docs/diary-2026-02-25.md
📓 Created fresh docs/diary.md (Previous: diary-2026-02-25.md)
```

**Dry-run mode:** `python scripts/diary_rotate.py --check` exits with code 0 if no rotation is needed, code 1 if it is — useful for CI checks without side effects.

---

## The Commit Flow

When you run `git commit` in a YAMLGraph repository, the following sequence executes:

### Stage 1: Pre-commit (before commit is created)

```
git commit
  │
  ├─  1. ruff                    Lint Python, auto-fix
  ├─  2. ruff-format             Format Python
  ├─  3. trailing-whitespace     Strip trailing whitespace
  ├─  4. end-of-file-fixer       Ensure final newline
  ├─  5. check-yaml              Validate YAML
  ├─  6. check-added-large-files Block large files
  ├─  7. check-merge-conflict    Detect conflict markers
  ├─  8. check-ast               Validate Python AST
  ├─  9. check-toml              Validate TOML
  ├─ 10. debug-statements        Block debugger calls
  ├─ 11. detect-private-key      Block secrets
  ├─ 12. diary-rotate            Rotate diary on day change
  ├─ 13. req-coverage-strict     All REQ-YG-XXX covered by tests
  ├─ 14. noqa-confession         All noqa suppressions documented
  ├─ 15. inline-llm-check        No bypass of three-layer architecture
  ├─ 16. radon-complexity         No grade-D functions (CC ≥ 21)
  ├─ 17. file-size-gate           No files > 450 lines
  ├─ 18. forbid-terms             No TODO/FIXME/backward compatibility
  ├─ 19. jscpd-dup                No excessive duplication
  ├─ 20. vulture-dead-code        No dead code
  ├─ 21. hedging-check            No silent fallback patterns
  ├─ 22. pytest                   Unit tests pass
  ├─ 26. absolution               ✓ Absolution granted
  │
  ▼ (if any hook fails → commit rejected, fail_fast stops pipeline)
```

### Stage 2: Commit-msg (after message is written)

```
  ├─ 23. conventional-pre-commit  Message follows conventional format
  ├─ 24. feat-requires-fr         feat: commits cite FR-XXX
  ├─ 25. changelog-required       feat:/fix: commits include CHANGELOG.md
  ├─ 26. absolution               ✓ Absolution granted (again)
  │
  ▼ (if any hook fails → commit rejected)
```

### Stage 3: Post-commit (after commit is created)

```
  └─ 27. inquisitor-background    Async audit (non-blocking)
```

The entire pipeline — from ruff through absolution — typically completes in 20–40 seconds. The unit test step (`pytest tests/unit/ -q`) is the slowest gate, targeted at ~20 seconds. Integration tests (which require API keys) run separately and are not part of the commit gate.

### What Failure Looks Like

Because `fail_fast: true` is set, a failure at any point stops the pipeline immediately:

```
$ git commit -m "feat: FR-042 add new node type"
ruff.....................................................Passed
ruff-format..............................................Passed
trailing-whitespace......................................Passed
...
file size gate (>450 error, >400 warn)..................Failed
- hook id: file-size-gate
- exit code: 1

ERROR yamlgraph/node_factory/llm_node.py -- 467 lines (max 450)

FAIL -- code files exceeding 450 lines detected
```

The developer must fix the issue — in this case, splitting the oversized module — before the commit can proceed. There are no overrides, no `--no-verify` escapes. As the Scripture states: *"[--no-verify flag will result in immediate termination; automatically enforced by CI.]"*

---

## Summary

YAMLGraph's pre-commit gates encode the project's quality doctrine as executable checks. They enforce:

- **Code quality** — linting, formatting, complexity, file size, dead code, duplication
- **Architectural integrity** — no inline LLM orchestration, no silent fallbacks
- **Traceability** — every requirement tested, every suppression documented
- **Process discipline** — conventional commits, feature request references, changelog updates
- **Reflection** — diary rotation and the Distill reminder in every absolution

These gates are not bureaucracy — they are the immune system of the codebase. What survives the fire may merge.
