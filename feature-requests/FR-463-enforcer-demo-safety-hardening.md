# Feature Request: Enforcer Demo Safety Hardening

**Priority:** HIGH
**Type:** Bug
**Status:** Enforced
**Effort:** 1 day
**Requested:** 2026-05-29

## Summary

The enforcer demo has structural problems: `write_file` accepts arbitrary filesystem paths, `git_commit` is an orthogonal concern, critical tools are missing (`edit_file`, `git_log`), and useful tools (`lint`, `git_diff`) are absent. The judge demo proves that structured output (schema) is the delivery mechanism — tools are for research and side effects, not for reporting results.

## Value Statement

Demo users get safe-by-default tool boundaries, clean separation of concerns, and a complete tool surface for real implementation work: the enforcer reads, writes, edits, searches history, lints, tests, and self-reviews — the caller decides whether to commit.

## Problem

Code review + tool analysis (2026-05-29) identified:

1. **`write_file` allows arbitrary path writes** — `Path(path)` with no validation means the agent can write to `/etc/`, `~/.ssh/`, or overwrite `.env`.

2. **`git_commit` violates separation of concerns** — The judge has no write tools; it reads the codebase and returns a `JudgeVerdict` via structured output. The enforcer should follow the same pattern: write code, run tests, return `ImplementationResult`. Whether to commit is an *orchestration* decision — the caller inspects the result and commits if satisfied. The self-referential execution disaster (diary-2026-05-29) happened precisely because the agent had commit authority it shouldn't have had.

3. **`edit_file` missing — CRITICAL gap** — `write_file` overwrites entire files. To edit a 400-line module, the agent must read it, hold it in context, and rewrite entirely — causing truncation, dropped imports, and corrupted indentation. A surgical `replace_in_file(path, old_text, new_text)` tool is needed.

4. **`git_log` missing** — Present in planner and judge but absent from enforcer. The enforcer can't search history for prior attempts, related implementations, or commit patterns.

5. **`lint` missing** — The enforcer writes Python but can't verify `ruff` compliance. Pre-commit will reject the code later. Catching violations during the write→test loop saves iteration cycles.

6. **`git_diff` missing** — After writing files, the agent can't see what it changed. No self-review capability.

7. **Inconsistent trailing edge** — `- from: enforcer` without explicit `to: END`.

**Deferred:** `read_file` (`cat {file}`) and other shell tools have path traversal risk. Framework-level concern requiring changes to the shell tool executor. Out of scope.

## Proposed Solution

### 1. Remove `git_commit` tool

Committing is an orchestration decision. Remove `git_commit` and the `commit_hash` field from `ImplementationResult`.

### 2. Add `edit_file` Python tool

Surgical file editing — same pattern as IDE's `replace_string_in_file`:

```python
def edit_file(path: str, old_text: str, new_text: str) -> str:
    project_root = Path.cwd().resolve()
    p = Path(path).resolve()
    if not p.is_relative_to(project_root):
        return f"Error: path {path} is outside project root"
    content = p.read_text()
    if old_text not in content:
        return f"Error: old_text not found in {path}"
    if content.count(old_text) > 1:
        return f"Error: old_text appears {content.count(old_text)} times — must be unique"
    content = content.replace(old_text, new_text, 1)
    p.write_text(content)
    return f"Replaced {len(old_text)} chars with {len(new_text)} chars in {path}"
```

### 3. Add `git_log` shell tool

Copy from planner/judge for trilogy consistency:

```yaml
git_log:
  type: shell
  command: git log --oneline --all --grep={pattern}
  description: "Search git history for commits mentioning a pattern."
  parse: text
```

### 4. Add `lint` shell tool

```yaml
lint:
  type: shell
  command: ruff check {file} 2>&1
  description: "Run ruff linter on a Python file to check for style and correctness issues."
  parse: text
```

### 5. Add `git_diff` shell tool

```yaml
git_diff:
  type: shell
  command: git diff {path}
  description: "Show unstaged changes for a file or all files (pass '.' for all)."
  parse: text
```

### 6. Path-restricted `write_file`

Validate that the resolved path stays within the project root. Apply same restriction to `edit_file` and planner's `write_file`.

### 7. Explicit `to: END` edge (cosmetic piggyback)

### 8. Update prompt

Remove commit step. Add edit, lint, diff, and history steps. The prompt should instruct: read → explore history → implement (write + edit) → lint → test → self-review (diff) → report.

### 9. Update `demo.sh`

Show post-run commit command.

### 10. Add `run_command` honeypot tool (no-op with logging)

A Python tool that logs the requested command but does not execute it. When the 9 task-shaped tools don't cover the agent's needs, it reaches for `run_command` — revealing gaps in the tool surface.

```python
def run_command(command: str) -> str:
    logger.info("run_command requested: %s", command)
    return (
        "run_command is not available. Use the specific tools provided: "
        "read_file, search, list_dir, git_log, git_diff, lint, "
        "run_tests, write_file, edit_file."
    )
```

The log output becomes telemetry: review `demo-output.log` after runs to discover which commands the agent wanted. Recurring patterns graduate to new task-shaped tools.

### Final tool surface (10 tools)

| Tool | Type | Purpose |
|------|------|---------|
| `read_file` | shell | Read project files |
| `search` | shell | Search codebase with ripgrep |
| `list_dir` | shell | List directory contents |
| `git_log` | shell | Search git history |
| `git_diff` | shell | View unstaged changes |
| `lint` | shell | Run ruff on Python files |
| `run_tests` | shell | Run pytest on test files |
| `write_file` | python | Write files (path-restricted) |
| `edit_file` | python | Surgical text replacement (path-restricted) |
| `run_command` | python | **Honeypot** — logs requested command, returns error directing agent to specific tools |

10 tools total: 7 shell + 3 python (write, edit, honeypot).

## Design Note: Task-Shaped Tools vs. `run_command`

The 7 shell tools are constrained wrappers around single commands (`cat`, `rg`, `ls`, `git log`, `git diff`, `ruff check`, `pytest`). A single `run_command(command)` tool could replace all seven — the agent constructs the full shell command, gaining unlimited flexibility.

The tradeoff:

| | Task-shaped (7 shell tools) | `run_command` (1 tool) |
|--|:--:|:--:|
| Shell injection | `shlex.quote()` on every param | Agent constructs raw commands — no protection |
| Capability surface | Only predefined commands | Anything: `curl`, `rm -rf`, `pip install` |
| Auditability | Structured tool calls with named params | Opaque command strings |
| Anticipation | Must predict every command needed | Agent adapts freely |

The IDE agent (Copilot) has `run_in_terminal` — that's why it can do anything. But it operates under human supervision. The enforcer runs unattended.

**Decision:** Keep task-shaped tools for safety and auditability. Add `run_command` as a **no-op honeypot** that logs what the agent *wanted* to run without executing it. The log becomes telemetry for discovering missing tools — recurring `run_command` patterns graduate to new task-shaped tools. This preserves the security boundary while capturing the flexibility signal.

## Judgement Notes

- Shell injection is already handled by `shlex.quote()` — no new work needed.
- `read_file` path traversal deferred: framework-level shell tool concern.
- `git_commit` removed entirely — separation of concerns trumps convenience.
- The judge proves the pattern: tools for research, schema for delivery.
- `edit_file` is the highest-value addition — agents consistently corrupt files when forced to rewrite entirely.
- `git_log` restores trilogy symmetry (was in planner/judge but missing from enforcer).
- `lint` and `git_diff` enable a write→lint→test→review inner loop.
- `to: END` is cosmetic but trivial; accepted as piggyback.

## Acceptance Criteria

- [ ] `git_commit` tool removed from enforcer graph
- [ ] `commit_hash` field removed from `ImplementationResult` schema
- [ ] `edit_file` Python tool added with path restriction and unique-match validation
- [ ] `git_log` shell tool added (same as planner/judge)
- [ ] `lint` shell tool added (`ruff check {file}`)
- [ ] `git_diff` shell tool added (`git diff {path}`)
- [ ] Enforcer `write_file` rejects paths outside `Path.cwd()` (returns error, does not raise)
- [ ] Enforcer `edit_file` rejects paths outside `Path.cwd()`
- [ ] Planner `write_file` gets same path restriction
- [ ] Prompt updated: no commit step, adds lint/diff/history steps
- [ ] `demo.sh` updated: shows post-run commit command
- [ ] Enforcer graph edge updated to explicit `to: END`
- [ ] `run_command` Python honeypot tool added (logs command, returns error)
- [ ] Enforcer tool list: 10 tools (7 shell + 3 python)
- [ ] New unit tests: path traversal rejection, edit_file unique-match, run_command no-op, tool count = 10
- [ ] Existing planner tests still pass
- [ ] Both graphs pass `yamlgraph graph lint`

## Alternatives Considered

- **Keep `git_commit` but fix `git add -A` → `git add .`**: Treats the symptom. The root cause is that committing doesn't belong in the agent.
- **Allowlist of directories**: Too restrictive for `write_file`.
- **Chroot/sandbox**: Overkill for a demo.
- **Skip `edit_file`, use only `write_file`**: Agents consistently truncate large files when forced to rewrite entirely. Surgical editing is the single highest-value tool addition.
- **Skip `lint`**: Agent would iterate more (write → commit fail → read error → fix). Catching ruff violations in-loop saves cycles.

## Related

- FR-462: Standalone Enforcer Demo (parent FR)
- FR-452: Standalone Planner Demo (same `write_file` pattern)
- FR-450: Standalone Judge Demo (proves tools-for-research, schema-for-delivery pattern)
- `docs/diary/diary-2026-05-29-agent-self-modification.md`: Self-referential execution hazard
- `docs/diary/diary-2026-05-29-tool-surface-trust-boundary.md`: Tools as trust boundaries
