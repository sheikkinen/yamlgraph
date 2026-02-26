# Chapter 02: Pre-commit Gates

> *"What survives the fire may merge."* — The Scripture

Every commit in YAMLGraph passes through a gauntlet of automated checks before it reaches the repository. This chapter maps the complete pre-commit pipeline: what each hook enforces, the custom scripts that power the quality gates, and the precise sequence that runs when you type `git commit`.

---

## Why Pre-commit Hooks?

A codebase degrades one commit at a time. A linting violation here, an undocumented suppression there, a test left untagged — individually harmless, collectively fatal. Pre-commit hooks are the gate that prevents bad commits from entering the codebase. They enforce the doctrine *before* code reaches CI, catching violations at the cheapest possible moment: on the developer's machine, before the commit is even created.

YAMLGraph's hook configuration is aggressive by design. The very first line of `.pre-commit-config.yaml` sets the tone:

```yaml
fail_fast: true
```

If any hook fails, the entire commit is rejected. There is no "fix it later." This single setting transforms pre-commit from an advisory tool into an enforcement mechanism.

---

## Hook Configuration

As defined in `.pre-commit-config.yaml`, the pipeline contains **27 hooks** spanning three stages: `pre-commit`, `commit-msg`, and `post-commit`. Each hook runs in sequence; `fail_fast: true` halts execution on the first failure.

### Pre-commit Stage Hooks

| Hook | Source | Purpose |
|------|--------|---------|
| `ruff` | `astral-sh/ruff-pre-commit` v0.8.6 | Lint Python code with auto-fix (`--fix --exit-non-zero-on-fix`) |
| `ruff-format` | `astral-sh/ruff-pre-commit` v0.8.6 | Format Python code to consistent style |
| `trailing-whitespace` | `pre-commit/pre-commit-hooks` v5.0.0 | Strip trailing whitespace from all files |
| `end-of-file-fixer` | `pre-commit/pre-commit-hooks` v5.0.0 | Ensure files end with a newline |
| `check-yaml` | `pre-commit/pre-commit-hooks` v5.0.0 | Validate YAML syntax |
| `check-added-large-files` | `pre-commit/pre-commit-hooks` v5.0.0 | Block accidentally committed large files |
| `check-merge-conflict` | `pre-commit/pre-commit-hooks` v5.0.0 | Detect unresolved merge conflict markers |
| `check-ast` | `pre-commit/pre-commit-hooks` v5.0.0 | Verify Python files parse without syntax errors |
| `check-toml` | `pre-commit/pre-commit-hooks` v5.0.0 | Validate TOML file syntax |
| `debug-statements` | `pre-commit/pre-commit-hooks` v5.0.0 | Catch leftover `breakpoint()` and `pdb` calls |
| `detect-private-key` | `pre-commit/pre-commit-hooks` v5.0.0 | Prevent accidental secret commits |
| `diary-rotate` | Local: `scripts/diary_rotate.py` | Rotate `docs/diary.md` when the day changes |
| `req-coverage-strict` | Local: `scripts/req_coverage.py --strict` | Verify all requirements have tagged tests |
| `noqa-confession` | Local: `scripts/noqa_coverage.py --strict` | Ensure every `# noqa` has a confession entry |
| `inline-llm-check` | Local: `scripts/lint_inline_llm.py` | Detect LLM calls that bypass graph execution |
| `radon-complexity` | Local: `radon cc` | Block functions with cyclomatic complexity ≥ 21 (grade D) |
| `file-size-gate` | Local: `bash` | Error on files > 450 lines, warn on > 400 |
| `forbid-terms` | Local: `bash` | Reject `TODO`, `FIXME`, and `backward compatibility` |
| `jscpd-dup` | Local: `npx jscpd` | Detect code duplication (threshold 10%, min 10 lines) |
| `vulture-dead-code` | Local: `vulture` | Find unreachable/unused code (min confidence 80%) |
| `hedging-check` | Local: `scripts/hedging_check.py --strict` | Detect silent fallback patterns (Commandment 6) |
| `pytest` | Local: `pytest tests/unit/ -q` | Run unit tests (~20s); integration tests run separately |

### Commit-msg Stage Hooks

| Hook | Source | Purpose |
|------|--------|---------|
| `conventional-pre-commit` | `compilerla/conventional-pre-commit` v4.3.0 | Enforce Conventional Commits format (`feat`, `fix`, `chore`, etc.) |
| `feat-requires-fr` | Local: `bash` | Require `FR-XXX` reference in `feat:` commits |
| `changelog-required` | Local: `bash` | Require `CHANGELOG.md` changes in `feat:` and `fix:` commits |

### Multi-stage Hook

| Hook | Source | Stage | Purpose |
|------|--------|-------|---------|
| `absolution` | Local: `scripts/absolution.py` | `pre-commit`, `commit-msg` | Final gate — prints success message and Distill reminder |

### Post-commit Stage Hook

| Hook | Source | Purpose |
|------|--------|---------|
| `inquisitor-background` | Local: `.chaplain/inquisitor.sh` | Async audit launched after successful commit |

---

## Key Scripts

### absolution.py — The Final Gate

**File:** `scripts/absolution.py`
**Stage:** `pre-commit` and `commit-msg`
**Purpose:** Grant absolution when all hooks pass.

This is the last hook in the chain. If execution reaches `absolution.py`, it means every prior hook — linters, tests, coverage, complexity, duplication — has passed. The script prints a success message and a reminder to follow the Distill phase of the development doctrine:

```python
def main() -> int:
    """Grant absolution with Distill reminder."""
    print()
    print("✓ Absolution granted")
    print()
    print("**Distill.** After completing a task list, ...")
    print("Name the cognitive trap or insight. Extract a heuristic.")
    print("Plant a seed — a forward-looking question to grow new ideas.")
    ...
    return 0
```

The hook always returns `0` (success). Its purpose is not to gate — it is to *witness*. By running at both `pre-commit` and `commit-msg` stages, it confirms that the full pipeline has completed.

**Example output:**

```
✓ Absolution granted

**Distill.** After completing a task list, add a metacognitive entry to docs/diary.md.
Name the cognitive trap or insight. Extract a heuristic.
Plant a seed — a forward-looking question to grow new ideas.
If the heuristic proves recurring, graduate it to the Scripture.
```

---

### req_coverage.py — Requirement Traceability

**File:** `scripts/req_coverage.py`
**Stage:** `pre-commit` (via `--strict` flag)
**Purpose:** Ensure every requirement in `ARCHITECTURE.md` has at least one tagged test.

YAMLGraph enforces full traceability from requirements to tests using `@pytest.mark.req("REQ-YG-XXX")` markers. This script is the enforcement mechanism.

#### How It Works

1. **Defines all known requirements** — A master list (`ALL_REQS`) enumerates every `REQ-YG-XXX` identifier in the framework, grouped by capability (CAP-01 through CAP-32).

2. **Scans test files via AST parsing** — Walks `tests/unit/` and `tests/integration/`, parsing each `test_*.py` file to extract `@pytest.mark.req(...)` decorators. Both function-level and class-level markers are collected, with class-qualified keys (`stem::ClassName::method`) to avoid collisions.

3. **Reports coverage** — Prints a capability-by-capability summary showing how many requirements are covered and how many tests exist per capability.

4. **Fails on gaps** — With `--strict`, exits with code 1 if any requirement lacks a tagged test.

#### Modes

| Flag | Behavior |
|------|----------|
| *(none)* | Summary report: covered/total counts |
| `--detail` | Per-requirement test list |
| `--implementation` | Full traceability: requirement → source file → test (uses `.coverage` DB + AST fallback) |
| `--strict` | Exit 1 if any requirement is uncovered (used in pre-commit) |

#### Example Output

```
======================================================================
REQUIREMENT TRACEABILITY REPORT
======================================================================

Requirements: 82/82 covered
Tagged tests: 247 unique, 312 test-req pairs

CAPABILITY COVERAGE
----------------------------------------------------------------------
  ✅ CAP-01 Config Loading & Validation: 4/4 reqs, 18 tests
  ✅ CAP-02 Graph Compilation: 4/4 reqs, 12 tests
  ✅ CAP-03 Node Execution: 4/4 reqs, 15 tests
  ...
```

When a requirement is uncovered:

```
UNCOVERED REQUIREMENTS (1)
----------------------------------------------------------------------
  ❌ REQ-YG-092

FAIL -- strict mode: uncovered requirements detected
```

---

### noqa_coverage.py — The Confession Enforcer

**File:** `scripts/noqa_coverage.py`
**Stage:** `pre-commit` (via `--strict` flag)
**Purpose:** Verify that every `# noqa` suppression in the codebase is documented in `docs/confessions.md`.

Silencing a linter warning is a deliberate act. YAMLGraph requires each suppression to be *confessed* — documented with a unique identifier, the error code, what the code does (the *sin*), and why the suppression is acceptable (the *penance*).

#### How It Works

1. **Scans the codebase** — Walks `yamlgraph/`, `tests/`, `examples/`, and `scripts/` for all `# noqa` comments, parsing both specific codes (`# noqa: E402`) and blanket suppressions (`# noqa`).

2. **Parses confessions.md** — Reads `docs/confessions.md` looking for structured entries matching each `CONF-XXX` identifier to a file path, line number, and error code.

3. **Cross-references** — Compares found `noqa` comments against documented confessions. Any undocumented suppression is flagged.

4. **Fails on gaps** — With `--strict`, exits with code 1 if undocumented suppressions exist.

#### Confession Format

Each entry in `docs/confessions.md` follows this structure:

```markdown
### CONF-001
- **File**: [yamlgraph/tools/shell.py](../yamlgraph/tools/shell.py#L98)
- **Code**: S603
- **Sin**: subprocess call without shell=True validation
- **Penance**: All user inputs are sanitized with shlex.quote() at the boundary
```

#### Example Output

When all confessions are documented:

```
============================================================
noqa Confession Coverage Report
============================================================

Total noqa in codebase:     12
Documented confessions:     12
Undocumented:               0

✓ All noqa suppressions are documented
```

When a suppression is missing its confession:

```
------------------------------------------------------------
❌ Undocumented noqa (add to docs/confessions.md):
------------------------------------------------------------
  yamlgraph/executor.py:45 (E402)

Each noqa requires a confession entry with:
  - CONF-XXX identifier
  - File path with line number
  - Error code being suppressed
  - Sin (what the code does)
  - Penance (why it's acceptable)

FAIL -- undocumented noqa detected
```

---

### diary_rotate.py — Diary Rotation

**File:** `scripts/diary_rotate.py`
**Stage:** `pre-commit`
**Purpose:** Automatically rotate the development diary when the day changes, and import scheduled entries.

The development diary (`docs/diary.md`) accumulates metacognitive entries — reflections on traps, insights, and heuristics. When a new day arrives, the diary must be archived so it doesn't grow unbounded.

#### How It Works

1. **Checks the latest entry date** — Parses `## YYYY-MM-DD:` headers in `docs/diary.md` to find the most recent entry date.

2. **Compares to today** — If the latest entry date is before today, rotation is triggered.

3. **Archives the old diary** — Moves `docs/diary.md` to `docs/diary-YYYY-MM-DD.md` (with `-N` suffix if the archive already exists).

4. **Creates a fresh diary** — Writes a new `docs/diary.md` with a header and a `Previous:` link to the archived file.

5. **Imports scheduled entries** — Checks `~/scheduled-yamlgraphs/outputs/` for pending diary entries and git reports generated by automated pipelines, converting and appending them to the diary.

6. **Stages files** — Runs `git add` on both the archived and new diary files, so the rotation is included in the current commit.

#### Modes

| Flag | Behavior |
|------|----------|
| *(none)* | Rotate if needed, import scheduled entries |
| `--check` | Dry run — exit 0 if no rotation needed, exit 1 if rotation would occur |

#### Example Output

```
📓 Rotating diary: docs/diary.md → docs/diary-2026-02-25.md
📓 Created fresh docs/diary.md (Previous: diary-2026-02-25.md)
📥 Imported diary_entry_20260226.md → docs/diary.md
```

---

## Other Noteworthy Hooks

### inline-llm-check (lint_inline_llm.py)

Detects Python scripts with a `main()` function that import LLM execution functions (`execute_prompt`, `ChatAnthropic`, `create_llm`, etc.) *without* also importing graph loader functions (`load_graph_config`, `compile_graph`). This is the code smell of bypassing YAMLGraph's three-layer architecture — the LLM orchestration should live in a YAML graph, not inline in a script.

### hedging-check (hedging_check.py)

Graduated from a diary insight (2026-02-17), this hook detects silent fallback patterns — code like `if not results: results = all_data` that masks bugs by substituting broader datasets when a filter returns nothing. Enforces Commandment 6: *"Thou shalt not hedge with silent fallbacks; when a filter yields nothing, raise — never substitute everything."*

### radon-complexity

Runs `radon cc yamlgraph/ -n D -s` to compute cyclomatic complexity. Any function scoring grade D or higher (complexity ≥ 21) fails the commit. This enforces maintainability by requiring complex functions to be decomposed.

### file-size-gate

A bash one-liner that scans all `.py` files in `yamlgraph/`. Files exceeding 450 lines produce an error and block the commit. Files between 400 and 450 lines produce a warning but pass. The target is ≤ 400 lines per module.

### forbid-terms

Rejects any Python file containing `TODO`, `FIXME`, or `backward compatibility`. The first two enforce that work items belong in issue trackers, not source comments. The third catches compatibility shims that should be refactored.

---

## The Commit Flow

When you run `git commit`, here is the precise sequence of events:

### Phase 1: Pre-commit Stage

```
git commit
  │
  ├─ 1. ruff                    Lint check (auto-fixes applied)
  ├─ 2. ruff-format             Code formatting
  ├─ 3. trailing-whitespace     Whitespace cleanup
  ├─ 4. end-of-file-fixer       Newline at EOF
  ├─ 5. check-yaml              YAML syntax validation
  ├─ 6. check-added-large-files Large file detection
  ├─ 7. check-merge-conflict    Merge conflict markers
  ├─ 8. check-ast               Python syntax validation
  ├─ 9. check-toml              TOML syntax validation
  ├─ 10. debug-statements       Leftover debugger calls
  ├─ 11. detect-private-key     Secret detection
  ├─ 12. diary-rotate           Diary rotation (if day changed)
  ├─ 13. req-coverage-strict    Requirement traceability
  ├─ 14. noqa-confession        noqa suppression audit
  ├─ 15. inline-llm-check       Three-layer architecture enforcement
  ├─ 16. radon-complexity       Cyclomatic complexity gate
  ├─ 17. file-size-gate         Module size limits
  ├─ 18. forbid-terms           TODO/FIXME/compat drift
  ├─ 19. jscpd-dup              Code duplication detection
  ├─ 20. vulture-dead-code      Dead code detection
  ├─ 21. hedging-check          Silent fallback detection
  ├─ 22. pytest (unit)          Unit test suite (~20s)
  └─ 23. absolution             ✓ Absolution granted
```

If any hook from steps 1–22 fails, `fail_fast: true` halts the pipeline immediately. The commit is rejected. No partial passes.

### Phase 2: Commit-msg Stage

After the pre-commit hooks pass and the commit message is written:

```
  ├─ 24. conventional-pre-commit   Conventional Commits format check
  ├─ 25. feat-requires-fr          FR-XXX required for feat: commits
  ├─ 26. changelog-required        CHANGELOG.md required for feat:/fix:
  └─ 27. absolution                ✓ Absolution granted (again)
```

The commit message must follow Conventional Commits format. Feature commits must reference a feature request (`FR-XXX`). Both feature and fix commits must include changes to `CHANGELOG.md`. Absolution runs again to confirm the message-stage gates passed.

### Phase 3: Post-commit Stage

After the commit succeeds:

```
  └─ 28. inquisitor-background     Async audit (nohup, non-blocking)
```

The inquisitor runs asynchronously via `nohup`, performing deeper audit tasks that don't need to block the commit.

### The Complete Picture

```
Developer runs: git commit -m "feat(streaming): FR-045 add token callbacks"
                    │
                    ▼
            ┌───────────────┐
            │  Pre-commit   │  22 hooks check code quality
            │  Stage        │  Tests run, coverage verified
            └───────┬───────┘
                    │ All pass?
                    ▼
            ┌───────────────┐
            │  Commit-msg   │  Format, FR-XXX, CHANGELOG enforced
            │  Stage        │
            └───────┬───────┘
                    │ All pass?
                    ▼
            ┌───────────────┐
            │  Commit       │  ✓ Absolution granted
            │  Created      │
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │  Post-commit  │  Inquisitor audit (async)
            │  Stage        │
            └───────────────┘
```

The `--no-verify` flag to bypass these hooks is explicitly forbidden by the project doctrine:

> *"[--no-verify flag will result in immediate termination; automatically enforced by CI.]"*

Even if a developer were to skip local hooks, CI runs the same checks. There is no escape.

---

## Summary

The pre-commit pipeline is the first line of defense — and the most important one. It enforces code style, validates syntax, runs tests, checks complexity, hunts dead code and duplication, traces requirements to tests, audits linter suppressions, rotates the diary, and validates commit messages. Twenty-eight hooks, three stages, zero tolerance.

The philosophy is simple: catch everything early, catch it cheaply, and never let entropy through the gate. What survives the fire may merge.

---
