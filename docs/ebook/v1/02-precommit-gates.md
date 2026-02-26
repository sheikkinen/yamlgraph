# Chapter 02: Pre-commit Gates

> *"What survives the fire may merge."* — The Scripture

Every commit in YAMLGraph passes through a gauntlet of automated checks before it can enter the repository. This is not optional. The `.pre-commit-config.yaml` defines **27 hooks** across three stages — a layered defense system that catches style violations, dead code, missing documentation, uncovered requirements, and broken tests before they reach the main branch. This chapter dissects every gate, explains the custom scripts that enforce YAMLGraph's unique doctrine, and walks through the complete commit flow from keystroke to absolution.

---

## 2.1 Why Pre-commit Hooks?

Pre-commit hooks are the first line of defense in the development pipeline. They run *before* a commit is recorded, which means problems are caught at the earliest possible moment — on the developer's machine, seconds after the code is written, not minutes later in CI.

YAMLGraph takes this further than most projects. The hook configuration enforces not just code style, but **doctrinal compliance**: every `noqa` suppression must be confessed, every requirement must be traced to a test, every `feat` commit must reference a feature request. The hooks embody the Tenth Commandment: *"Every failure shalt refine the law."*

The configuration begins with a critical setting, as defined in `.pre-commit-config.yaml`:

```yaml
fail_fast: true
```

This means the first hook failure stops the entire pipeline. There is no point running 20 more checks if the linter already failed. Fix the first problem, try again. This keeps the feedback loop tight.

---

## 2.2 Hook Configuration

The hooks are organized into three stages, each running at a different point in the Git workflow. Below is the complete inventory as defined in `.pre-commit-config.yaml`:

### Pre-commit Stage (runs before commit is created)

| # | Hook ID | Purpose | Source |
|---|---------|---------|--------|
| 1 | `ruff` | Lint Python code (with `--fix --exit-non-zero-on-fix`) | astral-sh/ruff-pre-commit v0.8.6 |
| 2 | `ruff-format` | Format Python code | astral-sh/ruff-pre-commit v0.8.6 |
| 3 | `trailing-whitespace` | Strip trailing whitespace | pre-commit-hooks v5.0.0 |
| 4 | `end-of-file-fixer` | Ensure files end with newline | pre-commit-hooks v5.0.0 |
| 5 | `check-yaml` | Validate YAML syntax | pre-commit-hooks v5.0.0 |
| 6 | `check-added-large-files` | Block accidentally committed large files | pre-commit-hooks v5.0.0 |
| 7 | `check-merge-conflict` | Detect unresolved merge conflict markers | pre-commit-hooks v5.0.0 |
| 8 | `check-ast` | Validate Python files parse correctly | pre-commit-hooks v5.0.0 |
| 9 | `check-toml` | Validate TOML syntax | pre-commit-hooks v5.0.0 |
| 10 | `debug-statements` | Catch leftover `breakpoint()` / `pdb` calls | pre-commit-hooks v5.0.0 |
| 11 | `detect-private-key` | Prevent private keys from being committed | pre-commit-hooks v5.0.0 |
| 12 | `diary-rotate` | Rotate `docs/diary.md` on day change | local: `scripts/diary_rotate.py` |
| 13 | `req-coverage-strict` | Verify all requirements have test coverage | local: `scripts/req_coverage.py --strict` |
| 14 | `noqa-confession` | Verify all `noqa` suppressions are confessed | local: `scripts/noqa_coverage.py --strict` |
| 15 | `inline-llm-check` | Block inline LLM orchestration in Python | local: `scripts/lint_inline_llm.py` |
| 16 | `radon-complexity` | Block functions with cyclomatic complexity ≥ 21 (grade D) | local: `radon cc` |
| 17 | `file-size-gate` | Error on files > 450 lines, warn > 400 | local: `bash` one-liner |
| 18 | `forbid-terms` | Block `TODO`, `FIXME`, `backward compatibility` | local: `bash` grep |
| 19 | `jscpd-dup` | Detect code duplication (threshold 10%) | local: `npx jscpd` |
| 20 | `vulture-dead-code` | Find unused code (min confidence 80%) | local: `vulture` |
| 21 | `hedging-check` | Block silent fallbacks and hedging patterns | local: `scripts/hedging_check.py --strict` |
| 22 | `pytest` | Run unit tests (~20s) | local: `pytest tests/unit/` |

### Commit-msg Stage (runs after message is written)

| # | Hook ID | Purpose | Source |
|---|---------|---------|--------|
| 23 | `conventional-pre-commit` | Enforce Conventional Commits format | compilerla/conventional-pre-commit v4.3.0 |
| 24 | `feat-requires-fr` | `feat:` commits must reference `FR-XXX` | local: `bash` pattern match |
| 25 | `changelog-required` | `feat:`/`fix:` commits must include `CHANGELOG.md` | local: `bash` + `git diff --cached` |

### Both Pre-commit and Commit-msg Stages

| # | Hook ID | Purpose | Source |
|---|---------|---------|--------|
| 26 | `absolution` | Final summary — grants absolution with Distill reminder | local: `scripts/absolution.py` |

### Post-commit Stage (runs after commit is recorded)

| # | Hook ID | Purpose | Source |
|---|---------|---------|--------|
| 27 | `inquisitor-background` | Async audit (runs in background via `nohup`) | local: `.chaplain/inquisitor.sh` |

---

## 2.3 The Standard Guards (Hooks 1–11)

The first eleven hooks come from well-known open-source repositories and handle universal code hygiene. Two deserve special attention.

**Ruff** (hooks 1–2) handles both linting and formatting. The linter runs with `--fix --exit-non-zero-on-fix`, meaning it will auto-fix what it can — but if any fix was needed, the hook still fails. This forces you to review and re-stage the auto-fixed code rather than blindly committing corrections you haven't seen.

**detect-private-key** (hook 11) is a security gate. It scans staged files for patterns that match private key formats (RSA, DSA, EC, PGP). In a project that routinely handles API keys for multiple LLM providers, this hook prevents catastrophic credential leaks.

---

## 2.4 The Entropy Killers (Hooks 16–20)

Five hooks work together to enforce the Eighth Commandment: *"Thou shalt kill all entropy and false idols."*

### Radon Complexity Gate

```bash
radon cc yamlgraph/ -n D -s
```

This runs cyclomatic complexity analysis on all Python files in `yamlgraph/`. The `-n D` flag filters to only show functions with grade D or worse (complexity ≥ 21). If any function reaches that threshold, the commit is blocked. The message is direct:

```
FAIL -- functions with cyclomatic complexity >= 21 (grade D) detected
```

### File Size Gate

The file size gate scans every `.py` file in `yamlgraph/`:
- **> 450 lines**: `ERROR` — commit blocked
- **> 400 lines**: `WARN` — commit allowed, but the warning is a signal to refactor

This enforces the project's module size standard: target < 400 lines, hard max 450.

### Forbid Terms

A grep-based scan blocks three patterns:
- `TODO` — unfinished work must not be committed; use issues or feature requests
- `FIXME` — same rationale
- `backward compatibility` — a key indicator that a refactoring is needed instead of a compatibility shim

### jscpd Duplicate Check

```bash
npx jscpd yamlgraph --threshold 10 --min-lines 10 --min-tokens 80 --format python --gitignore --reporters console
```

Detects code duplication using jscpd with a 10% threshold. Duplicated blocks of at least 10 lines or 80 tokens are flagged. The Scripture is clear: *"burn duplicates with jscpd."*

### Vulture Dead Code

```bash
vulture yamlgraph --min-confidence 80
```

Vulture performs static analysis to find unused functions, variables, imports, and classes. The 80% confidence threshold reduces false positives while still catching genuine dead code.

---

## 2.5 Key Scripts

### `scripts/absolution.py` — The Final Blessing

**Purpose**: The last hook to run. If all other hooks passed, this script grants absolution — a confirmation that the commit has survived the gauntlet.

**When it runs**: Both `pre-commit` and `commit-msg` stages (the only hook that runs in both).

**Key logic**: The script is deliberately simple. As defined in `scripts/absolution.py`:

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

It always returns `0` (success). Its role is not to gate — it's to remind. Every successful commit prints the Distill reminder from the Sermon of the Chaplain, reinforcing the practice of metacognitive reflection.

**Example output**:

```
✓ Absolution granted

**Distill.** After completing a task list, add a metacognitive entry to docs/diary.md.
Name the cognitive trap or insight. Extract a heuristic.
Plant a seed — a forward-looking question to grow new ideas.
If the heuristic proves recurring, graduate it to the Scripture.
```

---

### `scripts/req_coverage.py` — Requirement Traceability

**Purpose**: Ensures every requirement defined in `ARCHITECTURE.md` has at least one test tagged with `@pytest.mark.req("REQ-YG-XXX")`. This is the enforcement mechanism for ADR-001 (Requirement Traceability).

**When it runs**: Pre-commit stage with `--strict` flag (exit code 1 on gaps).

**Key logic**: As defined in `scripts/req_coverage.py`, the script:

1. **Defines the canonical requirement list** — `ALL_REQS` enumerates every `REQ-YG-XXX` ID that must be covered, grouped by capability (CAP-01 through CAP-32).

2. **Scans test files using AST parsing** — The `extract_req_markers()` function parses Python test files and extracts `@pytest.mark.req(...)` decorator arguments. It handles both function-level and class-level markers, producing class-qualified keys (`stem::Class::method`) to avoid collisions.

3. **Reports coverage by capability** — Each capability group shows its coverage status with emoji indicators:
   - ✅ All requirements covered
   - ⚠️  Partially covered
   - ❌ No coverage

4. **Optional modes**:
   - `--detail`: Shows per-requirement test mapping
   - `--implementation`: Traces requirements through to source files using `.coverage` SQLite database and AST import analysis as fallback
   - `--strict`: Exits with code 1 if any requirement is uncovered

**Example output** (summary mode):

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

**Example output** (strict failure):

```
UNCOVERED REQUIREMENTS (1)
----------------------------------------------------------------------
  ❌ REQ-YG-092
```

The requirement-to-capability mapping in this script is the single source of truth for what YAMLGraph must do and whether tests prove it works. When adding a new capability, the script itself must be updated — add the requirement IDs to `ALL_REQS` and `CAPABILITIES`, then tag tests with the new IDs.

---

### `scripts/noqa_coverage.py` — The noqa Confessional

**Purpose**: Every `# noqa` suppression in the codebase must be documented in `docs/confessions.md` with a `CONF-XXX` identifier, the error code, the sin (what it does), and the penance (why it's acceptable). This script enforces that doctrine.

**When it runs**: Pre-commit stage with `--strict` flag.

**Key logic**: As defined in `scripts/noqa_coverage.py`, the script performs two passes:

1. **Scan the codebase** — `scan_codebase()` walks through `yamlgraph/`, `tests/`, `examples/`, and `scripts/` directories, finding every `# noqa` comment. It parses both specific codes (`# noqa: E402`) and blanket suppressions (`# noqa`).

2. **Parse confessions** — `parse_confessions()` reads `docs/confessions.md`, extracting structured data from entries formatted as:
   ```markdown
   ### CONF-001
   - **File**: [path/file.py](../path/file.py#L145)
   - **Code**: E402
   ```

3. **Cross-reference** — Any `noqa` comment not matched to a confession entry is flagged as undocumented. In `--strict` mode, this blocks the commit.

**Example output** (all documented):

```
============================================================
noqa Confession Coverage Report
============================================================

Total noqa in codebase:     12
Documented confessions:     12
Undocumented:               0

✓ All noqa suppressions are documented
```

**Example output** (strict failure):

```
------------------------------------------------------------
❌ Undocumented noqa (add to docs/confessions.md):
------------------------------------------------------------
  yamlgraph/executor.py:42 (E402)

Each noqa requires a confession entry with:
  - CONF-XXX identifier
  - File path with line number
  - Error code being suppressed
  - Sin (what the code does)
  - Penance (why it's acceptable)

FAIL -- undocumented noqa detected
See docs/confessions.md for how to confess your sins and beg forgiveness.
```

The confessional system ensures that lint suppressions are never silent. Every exception to the rules is visible, justified, and reviewable.

---

### `scripts/diary_rotate.py` — Diary Rotation

**Purpose**: Automatically rotates the development diary (`docs/diary.md`) when the day changes, preserving historical entries in dated archive files.

**When it runs**: Pre-commit stage, `always_run: true`. Runs on every commit attempt regardless of which files changed.

**Key logic**: As defined in `scripts/diary_rotate.py`, the rotation follows a specific sequence:

1. **Check the latest entry date** — `latest_entry_date()` scans `docs/diary.md` for `## YYYY-MM-DD:` headers and extracts the most recent date.

2. **Compare with today** — If the latest entry date is before today, rotation is triggered.

3. **Import scheduled entries** — Before rotating, `import_scheduled_entries()` checks `~/scheduled-yamlgraphs/outputs/` for pending diary entries (e.g., World Digest entries generated by scheduled pipelines) and `import_git_reports()` checks for git activity reports.

4. **Archive the old diary** — The current `docs/diary.md` is moved to `docs/diary-YYYY-MM-DD.md`. If that filename already exists, a numeric suffix is appended (`diary-2026-02-25-1.md`).

5. **Create a fresh diary** — A new `docs/diary.md` is written with a header and a `Previous:` link to the archived file:
   ```markdown
   # Development Diary

   Metacognitive reflections on development process.

   Previous: [diary-2026-02-25.md](diary-2026-02-25.md) — 4 entries from 2026-02-25.

   ---
   ```

6. **Stage files** — Both the archive and the fresh diary are staged with `git add`, so the rotation is included in the current commit.

**Example output** (rotation triggered):

```
📓 Rotating diary: docs/diary.md → docs/diary-2026-02-25.md
📓 Created fresh docs/diary.md (Previous: diary-2026-02-25.md)
```

**Example output** (with scheduled import):

```
📥 Imported diary_entry_20260225.md → docs/diary.md
📓 Rotating diary: docs/diary.md → docs/diary-2026-02-25.md
📓 Created fresh docs/diary.md (Previous: diary-2026-02-25.md)
```

The diary rotation ensures the development diary stays manageable while preserving the full history. Combined with the Distill reminder from absolution, it creates a continuous practice of reflection — the diary grows daily, rotates automatically, and the developer is reminded to contribute on every commit.

---

## 2.6 The Commit-msg Guards (Hooks 23–25)

Three hooks validate the commit message itself, running after the developer writes it.

### Conventional Commits

The `conventional-pre-commit` hook enforces the [Conventional Commits](https://www.conventionalcommits.org/) specification. Only these prefixes are allowed:

```
feat, fix, chore, docs, refactor, test, ci, perf, style, build
```

A commit message like `"updated some stuff"` is rejected. It must be `"fix(streaming): correct chunk boundary handling"` or similar.

### Feature Request Enforcement

The `feat-requires-fr` hook adds a YAMLGraph-specific rule: any commit starting with `feat:` or `feat(...):` must contain an `FR-XXX` reference. This ties every new feature to its planning document in `feature-requests/`.

```bash
# ❌ Rejected
feat(streaming): add subgraphs parameter

# ✅ Accepted
feat(streaming): FR-030 add subgraphs parameter
```

### Changelog Enforcement

The `changelog-required` hook ensures that `feat:` and `fix:` commits include changes to `CHANGELOG.md`. This is checked by examining the staged files (`git diff --cached --name-only`). If `CHANGELOG.md` is not in the staged set, the commit is blocked:

```
ERROR: feat:/fix: commits must include CHANGELOG.md changes
Add your entry under the current [Unreleased] or version heading.
```

---

## 2.7 The Post-commit Inquisitor (Hook 27)

After the commit is recorded, one final hook fires asynchronously:

```yaml
- id: inquisitor-background
  name: inquisitor (async audit)
  entry: bash -c 'nohup .chaplain/inquisitor.sh > .chaplain/inquisitor.log 2>&1 &'
  language: system
  pass_filenames: false
  always_run: true
  stages: [post-commit]
```

The inquisitor runs in the background via `nohup`, writing its output to `.chaplain/inquisitor.log`. It does not block the developer — by the time it runs, the commit is already recorded. Its findings surface later as recommendations, not gates.

---

## 2.8 The Complete Commit Flow

Here is what happens when you run `git commit` in a YAMLGraph repository:

```
git commit -m "feat(nodes): FR-042 add copilot node type"
│
├─ STAGE 1: pre-commit
│  │
│  ├─ [1]  ruff              → Lint Python, auto-fix, fail if fixes needed
│  ├─ [2]  ruff-format       → Format Python code
│  ├─ [3]  trailing-whitespace → Strip trailing spaces
│  ├─ [4]  end-of-file-fixer → Ensure trailing newline
│  ├─ [5]  check-yaml        → Validate YAML syntax
│  ├─ [6]  check-added-large-files → Block large files
│  ├─ [7]  check-merge-conflict → Detect conflict markers
│  ├─ [8]  check-ast         → Validate Python parses
│  ├─ [9]  check-toml        → Validate TOML syntax
│  ├─ [10] debug-statements  → Catch breakpoint()/pdb
│  ├─ [11] detect-private-key → Block leaked secrets
│  ├─ [12] diary-rotate      → Archive old diary, create fresh one
│  ├─ [13] req-coverage      → Verify all REQ-YG-XXX have tests
│  ├─ [14] noqa-confession   → Verify all noqa are confessed
│  ├─ [15] inline-llm-check  → Block inline LLM orchestration
│  ├─ [16] radon-complexity   → Block complexity grade D+
│  ├─ [17] file-size-gate    → Error >450 lines, warn >400
│  ├─ [18] forbid-terms      → Block TODO/FIXME/backward compat
│  ├─ [19] jscpd-dup         → Block >10% code duplication
│  ├─ [20] vulture-dead-code → Block unused code
│  ├─ [21] hedging-check     → Block silent fallbacks
│  ├─ [22] pytest            → Run unit tests
│  └─ [26] absolution        → "✓ Absolution granted" + Distill reminder
│
├─ STAGE 2: commit-msg
│  │
│  ├─ [23] conventional-pre-commit → Enforce conventional commit format
│  ├─ [24] feat-requires-fr  → feat: must reference FR-XXX
│  ├─ [25] changelog-required → feat:/fix: must include CHANGELOG.md
│  └─ [26] absolution        → (runs again for commit-msg stage)
│
├─ ✅ COMMIT RECORDED
│
└─ STAGE 3: post-commit
   │
   └─ [27] inquisitor        → Background async audit (non-blocking)
```

If any hook in stages 1 or 2 fails, `fail_fast: true` aborts the entire pipeline immediately. The developer sees the error, fixes it, and tries again. Only when all gates pass does the commit enter the repository.

---

## 2.9 Installing the Hooks

The hooks are installed with two commands:

```bash
pre-commit install
pre-commit install --hook-type commit-msg
```

The first installs hooks for the `pre-commit` and `post-commit` stages. The second adds the `commit-msg` stage hooks. Both are required — the `CLAUDE.md` development guide lists them explicitly under Environment Setup.

To run all hooks manually (without committing):

```bash
pre-commit run --all-files
```

---

## 2.10 The Philosophy

The pre-commit configuration embodies a clear philosophy: **catch problems at the boundary where they enter, not downstream where they manifest**. This is the One Law from the Knowledge Graph:

> *Normalize at the boundary where external data enters, not downstream where it manifests.*

Every commit is a boundary. The hooks ensure that what crosses that boundary is linted, formatted, tested, traced, confessed, and documented. The cost of running 27 hooks on every commit is measured in seconds. The cost of a bad commit reaching production is measured in hours or days.

The hooks are also self-reinforcing. When a new cognitive trap is discovered (say, silent fallbacks masking errors), a new hook is added (`hedging-check`). When a pattern recurs in diary entries, it graduates to the Scripture, and a hook enforces it. The system evolves, and each evolution makes the next commit safer than the last.

*What survives the fire may merge.*
