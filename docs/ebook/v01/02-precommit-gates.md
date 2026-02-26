# Chapter 02: Pre-commit Gates

> *"What is hidden in commit shall be revealed in production."*
> — Commandment VI, The Scripture

---

## Why Pre-commit Hooks?

Every codebase has a boundary between "work in progress" and "committed truth." Pre-commit hooks are the gate at that boundary — an automated tribunal that judges every commit before it enters the repository.

In YAMLGraph, these hooks enforce the project's doctrine at the moment it matters most: the point of no return. Rather than discovering a linting violation in CI minutes later, or a missing test requirement in code review days later, the developer gets immediate feedback at `git commit` time.

The design philosophy is **fail fast**: the configuration sets `fail_fast: true`, meaning the first hook failure aborts the entire commit. There is no partial pass. Either the commit meets every standard, or it is rejected entirely. This is not cruelty — it is mercy. A commit that passes all gates can be trusted by every downstream consumer: reviewers, CI, production.

Pre-commit hooks also serve as *living documentation*. New contributors don't need to memorize a style guide — the hooks enforce it. The rules are executable, not advisory.

---

## Hook Configuration

All hooks are defined in `.pre-commit-config.yaml` at the repository root. The configuration draws from three sources:

1. **External repos** — community-maintained hooks (Ruff, conventional commits, standard pre-commit checks)
2. **Local scripts** — project-specific Python scripts in `scripts/`
3. **Local inline** — bash one-liners for simple checks

Hooks run in three stages:
- **`pre-commit`** — triggered before the commit is created (code quality, tests, structural checks)
- **`commit-msg`** — triggered after the commit message is written (message format validation)
- **`post-commit`** — triggered after the commit completes (async auditing)

### Hook Summary

As defined in `.pre-commit-config.yaml`:

| Hook | Purpose | Stage |
|------|---------|-------|
| `ruff` | Lint Python code (with auto-fix) | pre-commit |
| `ruff-format` | Format Python code | pre-commit |
| `trailing-whitespace` | Remove trailing whitespace | pre-commit |
| `end-of-file-fixer` | Ensure files end with newline | pre-commit |
| `check-yaml` | Validate YAML syntax | pre-commit |
| `check-added-large-files` | Block oversized files | pre-commit |
| `check-merge-conflict` | Detect unresolved merge markers | pre-commit |
| `check-ast` | Validate Python AST parses | pre-commit |
| `check-toml` | Validate TOML syntax | pre-commit |
| `debug-statements` | Catch leftover `breakpoint()`/`pdb` | pre-commit |
| `detect-private-key` | Prevent accidental secret commits | pre-commit |
| `diary-rotate` | Rotate `docs/diary.md` on day change | pre-commit |
| `req-coverage-strict` | Verify all REQ-YG-XXX markers have tests | pre-commit |
| `noqa-confession` | Ensure all `# noqa` comments are documented | pre-commit |
| `inline-llm-check` | Detect inline LLM orchestration (use YAML) | pre-commit |
| `radon-complexity` | Block functions with cyclomatic complexity ≥ D (21+) | pre-commit |
| `file-size-gate` | Error at >450 lines, warn at >400 lines | pre-commit |
| `forbid-terms` | Block `TODO`, `FIXME`, `backward compatibility` | pre-commit |
| `jscpd-dup` | Detect code duplication (threshold 10%) | pre-commit |
| `vulture-dead-code` | Find dead/unused code (≥80% confidence) | pre-commit |
| `hedging-check` | Detect silent fallbacks and hedging patterns | pre-commit |
| `pytest` | Run unit tests (~20s) | pre-commit |
| `conventional-pre-commit` | Enforce Conventional Commits format | commit-msg |
| `feat-requires-fr` | Require `FR-XXX` reference in `feat:` commits | commit-msg |
| `changelog-required` | Require `CHANGELOG.md` changes in `feat:`/`fix:` commits | commit-msg |
| `absolution` | Final summary — grant absolution with Distill reminder | pre-commit, commit-msg |
| `inquisitor-background` | Async post-commit audit | post-commit |

That's **27 hooks** guarding the commit boundary. Let's examine the key scripts that power the custom checks.

---

## Key Scripts

### absolution.py — The Final Blessing

**Purpose:** The last hook to run. If execution reaches `absolution.py`, every previous hook has passed. It prints a confirmation message and a reminder to practice the Distill step from the Scripture.

**When it runs:** At both `pre-commit` and `commit-msg` stages — the final checkpoint in each.

**Key logic:** Remarkably simple. As defined in `scripts/absolution.py`:

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

The script always returns `0` (success). Its only purpose is the message. But that message matters — it reinforces the reflective practice that drives continuous improvement. Every successful commit is also a prompt to learn.

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

**Purpose:** Enforces ADR-001 — every requirement in `ARCHITECTURE.md` must have at least one test tagged with `@pytest.mark.req("REQ-YG-XXX")`. This creates a traceable link from business requirement to test to implementation.

**When it runs:** Pre-commit stage with `--strict` flag, failing the commit if any requirement lacks test coverage.

**Key logic:** As defined in `scripts/req_coverage.py`:

1. **Define the universe.** The script maintains `ALL_REQS` — a list of every known requirement ID (currently REQ-YG-001 through REQ-YG-092, with some intentionally dropped). Requirements are grouped into capabilities (CAP-01 through CAP-32).

2. **Parse test files.** Using Python's `ast` module, it walks every test file in `tests/unit/` and `tests/integration/`, extracting `@pytest.mark.req(...)` decorators. It builds a mapping of requirement ID → list of test functions.

3. **Report coverage.** It prints a per-capability summary showing how many requirements are covered, and lists any uncovered requirements.

4. **Strict mode.** With `--strict`, any uncovered requirement causes exit code 1, blocking the commit.

The script also supports two additional modes:
- `--detail` — shows which specific test functions cover each requirement
- `--implementation` — traces the full chain: requirement → source file → test, using `.coverage` database and AST-based import analysis as fallback

**Example output:**

```
======================================================================
REQUIREMENT TRACEABILITY REPORT
======================================================================

Requirements: 85/87 covered
Tagged tests: 312 unique, 428 test-req pairs

CAPABILITY COVERAGE
----------------------------------------------------------------------
  ✅ CAP-01 Config Loading & Validation: 4/4 reqs, 18 tests
  ✅ CAP-02 Graph Compilation: 4/4 reqs, 12 tests
  ⚠️  CAP-03 Node Execution: 3/4 reqs, 8 tests
  ...

UNCOVERED REQUIREMENTS (2)
----------------------------------------------------------------------
  ❌ REQ-YG-042
  ❌ REQ-YG-076
```

---

### noqa_coverage.py — The Confession Booth

**Purpose:** Every `# noqa` suppression in the codebase must be documented in `docs/confessions.md` with a `CONF-XXX` identifier, explaining what rule is being suppressed (the sin) and why it's acceptable (the penance). This prevents `# noqa` from becoming a silent escape hatch.

**When it runs:** Pre-commit stage with `--strict` flag.

**Key logic:** As defined in `scripts/noqa_coverage.py`:

1. **Scan the codebase.** Walks all `.py` files in `yamlgraph/`, `tests/`, `examples/`, and `scripts/`, using regex to find every `# noqa` comment and extract the suppressed error codes.

2. **Parse confessions.** Reads `docs/confessions.md`, matching `### CONF-XXX` headers with their associated `**File**:` and `**Code**:` fields. Each confession records the exact file, line number, and error code.

3. **Cross-reference.** Compares the two sets. Any `# noqa` in the codebase without a matching confession entry is flagged as undocumented.

4. **Strict mode.** With `--strict`, undocumented suppressions fail the commit.

**Example output:**

```
============================================================
noqa Confession Coverage Report
============================================================

Total noqa in codebase:     12
Documented confessions:     12
Undocumented:               0

✓ All noqa suppressions are documented
```

When undocumented suppressions exist:

```
------------------------------------------------------------
❌ Undocumented noqa (add to docs/confessions.md):
------------------------------------------------------------
  yamlgraph/utils/helpers.py:42 (E402)

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

**Purpose:** Manages the lifecycle of `docs/diary.md`, the metacognitive development diary. When a new day begins, the old diary is archived and a fresh one is created, keeping the active diary focused on current work.

**When it runs:** Pre-commit stage, always — even if no diary changes are staged.

**Key logic:** As defined in `scripts/diary_rotate.py`:

1. **Detect day change.** Parses `## YYYY-MM-DD:` headers in the current `docs/diary.md` to find the most recent entry date. If that date is before today, rotation is triggered.

2. **Import external entries.** Before rotating, the script checks `~/scheduled-yamlgraphs/outputs/` for pending diary entries (World Digest and Git Report files generated by scheduled YAMLGraph pipelines). These are converted to diary format and appended.

3. **Archive.** Moves the current `docs/diary.md` to `docs/diary-YYYY-MM-DD.md` (with a `-N` suffix if the archive name already exists).

4. **Create fresh diary.** Writes a new `docs/diary.md` with a header and a `Previous:` link to the archived file.

5. **Stage files.** Runs `git add` on both the archive and the new diary, so the rotation is included in the current commit.

The script also supports `--check` for dry-run mode (exit 0 = no rotation needed, exit 1 = rotation would occur).

**Example output:**

```
📓 Rotating diary: docs/diary.md → docs/diary-2026-02-24.md
📓 Created fresh docs/diary.md (Previous: diary-2026-02-24.md)
📥 Imported diary_entry_20260224.md → docs/diary.md
```

---

## The Commit Flow

When you run `git commit` in the YAMLGraph repository, here is the full sequence of events:

### Phase 1: Pre-commit Stage

The moment you press Enter on `git commit`, the pre-commit framework intercepts and runs hooks in order. Because `fail_fast: true` is set, the first failure stops everything.

```
1. Ruff linter          → Fix and check Python code style
2. Ruff formatter        → Enforce consistent formatting
3. Standard checks       → Whitespace, YAML, TOML, AST, large files,
                           merge conflicts, debug statements, private keys
4. Diary rotation        → Archive old diary if day changed
5. Requirement coverage  → Every REQ-YG-XXX must have tagged tests
6. noqa confessions      → Every # noqa must be documented
7. Inline LLM check      → No hardcoded LLM calls in Python
8. Radon complexity      → No functions with grade D or worse
9. File size gate        → No files over 450 lines
10. Forbidden terms       → No TODO, FIXME, backward compatibility
11. jscpd duplication     → No duplicate code blocks >10%
12. Vulture dead code     → No unused code (≥80% confidence)
13. Hedging check         → No silent fallbacks
14. pytest unit tests     → All unit tests must pass
15. Absolution            → ✓ All gates passed — commit may proceed
```

### Phase 2: Commit Message Stage

After the pre-commit hooks pass and you write your commit message, the commit-msg hooks validate it:

```
16. Conventional Commits  → Message must follow format: type(scope): description
17. feat requires FR      → feat: commits must reference FR-XXX
18. CHANGELOG required    → feat:/fix: commits must update CHANGELOG.md
19. Absolution            → ✓ Message validated — commit is recorded
```

### Phase 3: Post-commit

After the commit is recorded, the async inquisitor runs in the background:

```
20. Inquisitor            → Background audit (non-blocking)
```

### What This Means in Practice

A typical commit attempt takes **20–40 seconds** — dominated by the pytest run (~20s) and jscpd duplication check. The developer gets immediate feedback:

- **If everything passes:** The commit goes through, and you see "✓ Absolution granted" with the Distill reminder.
- **If anything fails:** The commit is rejected with a clear error message pointing to exactly what needs fixing. No partial commits. No "I'll fix it in the next commit."

This is the gate. It is always on. There is no `--no-verify` — that flag results in immediate termination, automatically enforced by CI.

---

*What survives the fire may merge.*

