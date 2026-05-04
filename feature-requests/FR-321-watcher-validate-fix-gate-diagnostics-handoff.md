# Feature Request: FR-321 replace yamlgraph_async shell execution with exec argv

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-04

## Summary

Replace `.chaplain/actions/yamlgraph_async_action.py` subprocess invocation from `asyncio.create_subprocess_shell(" ".join(cmd_parts))` to `asyncio.create_subprocess_exec(*argv)` so watcher2 no longer routes user-derived values through a shell interpreter.

## Value Statement

Watcher2 operators get deterministic and safer command execution for validate/enforce sessions, especially when `--var` values contain shell metacharacters.

## Problem

Issue #321 identifies that FR-319 reduced risk with `shlex.quote()` but retained the shell boundary:

1. `YamlgraphAsyncAction` still executes via `create_subprocess_shell(command, ...)`.
2. Command text is still assembled by joining tokens into one string.
3. `precommit_output` and other context values can include shell-significant characters by design.

This is a boundary mismatch: structured argv is available (`cmd_parts`) but shell parsing is still introduced downstream.

## Research Findings

1. **Problem not fully solved today.**
   `.chaplain/actions/yamlgraph_async_action.py` now quotes var payloads (`shlex.quote`) but still calls `create_subprocess_shell(command, ...)`.

2. **Issue payload contains untrusted shell-like text.**
   `.chaplain/actions/precommit_action.py` stores raw hook output in `context["precommit_output"]`, and watcher pipeline forwards that value into yamlgraph vars.

3. **Prior FR explicitly deferred this exact refactor.**
   `feature-requests/FR-319-watcher-yamlgraph-async-shell-safe-vars.md` rejected switching to `create_subprocess_exec()` as out-of-scope for FR-319.

4. **In-repo prior art already uses exec argv for git actions.**
   `.chaplain/actions/git_commit_action.py` uses `asyncio.create_subprocess_exec(...)` across all git subprocesses, proving the pattern is established.

5. **Current behavior is coupled to one action boundary.**
   The shell-vs-exec choice for this defect is localized to `YamlgraphAsyncAction`; watcher FSM topology and graph contracts do not require changes.

## Objectives

1. Remove shell interpretation from `YamlgraphAsyncAction` execution path.
2. Preserve existing action behavior: cwd handling, timeout handling, stdout/stderr logging, return-code routing, and event_map matching.
3. Keep scope minimal: one action module plus focused unit tests.

## Constraints

1. Only touch `.chaplain/actions/yamlgraph_async_action.py` and directly-coupled tests.
2. Do not change watcher pipeline FSM transitions or event names.
3. Do not change graph prompt content, plan/judge/enforce logic, or validate gate rules.
4. No broad fallback/silent behavior changes; error routing must remain explicit.

## Proposed Solution

### In scope

1. Build argv directly:
   - Keep current `cmd_parts` construction pattern.
   - Encode each `--var` as a literal argv token (`key=value`) without shell quoting.
2. Execute with `asyncio.create_subprocess_exec(*cmd_parts, cwd=..., stdout=PIPE, stderr=PIPE)`.
3. Keep timeout/wait logic and event_map routing unchanged.
4. Keep logging concise and safe (string preview of argv for observability).
5. Add unit tests that lock this contract.

### Out of scope

1. Refactoring other chaplain actions that still intentionally use shell strings.
2. Redesigning placeholder substitution semantics.
3. Any watcher2 orchestration, branch, or PR-automation changes.

## Acceptance Criteria

- [x] **AC-01:** `YamlgraphAsyncAction` uses `asyncio.create_subprocess_exec` instead of `create_subprocess_shell`.
- [x] **AC-02:** `YamlgraphAsyncAction` passes command and `--var` values as argv tokens (no shell command string join).
- [x] **AC-03:** `shlex.quote()` is not used in `YamlgraphAsyncAction` var encoding.
- [x] **AC-04:** Existing `success`/`error`/`event_map` routing behavior remains unchanged for equivalent subprocess outputs.
- [x] **AC-05:** Existing `cwd` resolution and timeout handling behavior remains unchanged.
- [x] **AC-06:** Focused RED acceptance tests exist for AC-01..AC-05.

## Failing Acceptance Tests (RED)

Create:

- `tests/unit/test_fr321_yamlgraph_async_subprocess_exec.py`

Test cases:

1. `test_ac01_uses_create_subprocess_exec_not_shell`
2. `test_ac02_passes_var_payload_as_literal_argv_token`
3. `test_ac03_yamlgraph_async_action_has_no_shlex_quote_dependency`
4. `test_ac04_event_map_routing_unchanged_with_exec_subprocess`
5. `test_ac05_timeout_and_error_routing_unchanged`

RED command:

```bash
pytest tests/unit/test_fr321_yamlgraph_async_subprocess_exec.py -q --no-cov
```

Additional RED evidence commands (expected to fail before implementation):

```bash
rg -n "create_subprocess_exec\(" .chaplain/actions/yamlgraph_async_action.py
rg -n "create_subprocess_shell\(" .chaplain/actions/yamlgraph_async_action.py
```

## Alternatives Considered

1. **Keep FR-319 shlex quoting only**
   Rejected: shell parsing remains in the execution path; this does not eliminate the boundary mismatch.

2. **Manual escaping strategy in shell command text**
   Rejected: brittle, hard to reason about, and still shell-dependent.

3. **Pass large var payloads via temp files**
   Rejected: adds new IO contracts and graph prompt plumbing beyond this defect scope.

## Related

- GitHub issue #321: <https://github.com/sheikkinen/yamlgraph/issues/321>
- `.chaplain/actions/yamlgraph_async_action.py`
- `.chaplain/actions/precommit_action.py`
- `.chaplain/actions/git_commit_action.py`
- `.chaplain/config/watcher-pipeline-v2.yaml`
- `feature-requests/FR-319-watcher-yamlgraph-async-shell-safe-vars.md`
- Topic source requested: `.chaplain/processing/gh-321.md` (not present in this worktree)
- Canonical source used for drafting: GitHub issue #321
