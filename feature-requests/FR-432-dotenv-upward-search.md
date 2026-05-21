# Feature Request: FR-432 Upward .env Search with Git Boundary

**Priority:** MEDIUM
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-05-21

**Judge Verdict:** APPROVE — `.git` boundary must use `.is_dir()` not `.exists()` (worktrees have `.git` as a file, not a directory).

## Summary

Fix `config.py` to search upward from CWD for `.env` instead of only checking the exact CWD, stopping at `.git` boundary to prevent cross-project leaks.

## Value Statement

Agents and shell scripts embedding `yamlgraph graph run` from subdirectories or worktrees get API keys loaded correctly, eliminating a class of silent task-skipping failures.

## Problem

`config.py` line 20: `load_dotenv(WORKING_DIR / ".env")` — loads `.env` only from `Path.cwd()`. When `yamlgraph` is invoked from a subdirectory, worktree, hook, or shell script whose CWD differs from the project root, `.env` is not found. The resulting error ("ANTHROPIC_API_KEY not set") is **plausible but wrong** — the key *is* configured, just not found because CWD is wrong.

**Failure chain:**
1. Shell script calls `yamlgraph graph run` from a non-root CWD
2. `config.py` runs `load_dotenv(CWD / ".env")` at import time → file not found → no-op
3. LLM provider raises "API key not set"
4. Agent interprets this as environment misconfiguration → skips task
5. The real cause (CWD ≠ project root) is never surfaced

Scripture traps: `plausible_wrong_answer` (error message is technically correct but misleading), `normalize_at_boundary` (`.env` loading is a system boundary and it's fragile).

**Affected callers:**
- Chaplain FSM actions (`wt_dir` changes CWD to worktree)
- Copilot hooks running `yamlgraph graph lint` then `yamlgraph graph run`
- CI scripts running from repo subdirectories
- Any `subprocess` invocation with explicit `cwd=`

## Proposed Solution

Replace the single-path `load_dotenv` with an upward search that stops at `.git` boundary:

```python
def _locate_env_file(start: Path) -> Path | None:
    """Walk up from *start* looking for .env, stopping at .git directory boundary.

    Uses .is_dir() for the .git check because git worktrees have .git as a
    *file* (containing ``gitdir: ...``), not a directory. The search must
    continue through worktree roots to find .env at the main repo root.
    """
    current = start.resolve()
    while True:
        candidate = current / ".env"
        if candidate.is_file():
            return candidate
        # Stop at .git *directory* boundary (not .git file in worktrees)
        if (current / ".git").is_dir():
            return None
        parent = current.parent
        if parent == current:
            return None  # filesystem root
        current = parent


# Working directory (where the user runs the CLI from)
WORKING_DIR = Path.cwd()

# Load environment variables — search upward from CWD to .git boundary
_dotenv_path = _locate_env_file(WORKING_DIR)
if _dotenv_path:
    load_dotenv(_dotenv_path)
```

### Precedence

1. `YAMLGRAPH_ENV` env var (explicit override, if set) — future enhancement, not in this FR
2. Upward search from CWD to `.git` boundary
3. No `.env` found → rely on exported environment variables (current fallback)

### What this does NOT change

- `WORKING_DIR` still equals `Path.cwd()` — all relative path resolution unchanged
- `PROMPTS_DIR`, `GRAPHS_DIR`, `OUTPUTS_DIR` still relative to CWD
- No new dependencies — `pathlib` and `dotenv` already imported
- `load_dotenv` is called once at import time — no runtime overhead change

## Acceptance Criteria

- [x] `.env` found when CWD is a subdirectory of the project root
- [x] `.env` found when CWD is a git worktree (`.git` is a file, not a dir — search continues to main repo root)
- [x] Search stops at `.git` *directory* boundary — never loads a parent project's `.env`
- [x] Search stops at filesystem root — no infinite loop
- [x] Explicit `.env` in CWD takes precedence over parent `.env` (first match wins)
- [x] Existing behavior unchanged when `.env` is in CWD
- [x] No `.env` found → no error, falls back to exported env vars (existing behavior)
- [x] Tests: `.env` in CWD, `.env` in parent, `.env` above `.git` boundary (not loaded), no `.env` anywhere

## Implementation Notes (2026-05-21)

- Added `_locate_env_file(start: Path) -> Path | None` to `yamlgraph/config.py`.
- Replaced single-path `load_dotenv(WORKING_DIR / ".env")` with upward search from CWD.
- Implemented `.git` boundary stop using `.is_dir()` so worktree `.git` files do not terminate search.
- Added `tests/unit/test_fr432_dotenv_upward_search.py` covering CWD, parent, precedence, git-dir boundary, worktree `.git` file continuation, and no-env behavior.

## Alternatives Considered

- **Hook-based detection**: A pre-command guard could warn when `yamlgraph graph run` is invoked from a CWD without `.env`. Rejected — treats symptom, not cause. Scripture: `downstream_fix`.
- **`YAMLGRAPH_ENV` env var only**: Requires all callers to set it explicitly. Too much friction for a problem that has a natural default (walk up to `.git`).
- **Always load from package root**: Wrong — package is installed in site-packages. The `.env` is a user file, not a package file.
- **`dotenv`'s `find_dotenv()`**: Built-in upward search exists but doesn't respect `.git` boundary. Could load wrong `.env` in nested repo structures. Scripture: `workspace_is_not_boundary`.

## Related

- [config.py](../yamlgraph/config.py#L20): Current `load_dotenv` call
- Scripture trap: `plausible_wrong_answer`, `normalize_at_boundary`, `workspace_is_not_boundary`
