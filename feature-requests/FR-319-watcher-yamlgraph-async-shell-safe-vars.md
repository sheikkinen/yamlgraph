# Feature Request: FR-319 watcher yamlgraph_async shell-safe vars

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-03

## Summary

Normalize `yamlgraph_async_action.py` CLI variable encoding so every `--var key=value` payload is shell-safe when executed through `asyncio.create_subprocess_shell()`.

## Value Statement

Watcher2 operators get stable validate/precommit remediation loops even when pre-commit output includes quotes, parentheses, backticks, or `$` expansions.

## Problem

`YamlgraphAsyncAction` currently builds shell command segments as:

```python
cmd_parts.extend(["--var", f'{key}="{resolved}"'])
```

This only wraps values in double quotes before joining and passing to `create_subprocess_shell()`. When `resolved` contains nested double quotes or shell metacharacters, tokenization and shell evaluation change the intended value.

Observed impact (GitHub issue #304): `precommit_output` containing:

```python
pytestmark = pytest.mark.skip(reason="FR-316 obsolete")
```

is split/mangled in the spawned shell command, which can trigger repeated `validate -> precommit_check -> fix_needed` loops.

## Objectives

1. Make `--var` payload construction shell-safe for all context-substituted values.
2. Preserve current watcher pipeline behavior and event routing.
3. Add explicit RED acceptance tests that fail until shell-safe quoting is implemented.

## Constraints

1. Scope is limited to `.chaplain/actions/yamlgraph_async_action.py` and targeted unit tests.
2. No FSM topology changes in `.chaplain/config/watcher-pipeline-v2.yaml`.
3. No prompt/schema changes in watcher plan/enforce/validate graphs.
4. Keep `create_subprocess_shell()` call pattern intact in this FR; fix argument safety at the var boundary.

## Research Findings

1. **Injection boundary exists today.**
   `.chaplain/actions/yamlgraph_async_action.py` executes shell text via `asyncio.create_subprocess_shell(command, ...)` and currently interpolates values with manual `"{resolved}"` quoting.

2. **Unsafe content is expected by design.**
   `.chaplain/actions/precommit_action.py` writes raw hook output into `context["precommit_output"]`, and `.chaplain/config/watcher-pipeline-v2.yaml` forwards it into validate via:
   - `precommit_output: "{precommit_output}"`

3. **Validate prompt renders raw pre-commit output.**
   `.chaplain/graphs/watcher-enforce/prompts/validate-session.yaml` includes the full `precommit_output` block in the LLM context, so quotes and punctuation are common.

4. **Repo prior art uses `shlex.quote()` for shell boundaries.**
   `yamlgraph/tools/shell.py` normalizes untrusted variable values with `shlex.quote()` before shell execution (`shell=True` path), matching the same boundary type as this action.

5. **Gap:** no acceptance tests currently lock this quoting contract for `YamlgraphAsyncAction`.

## Proposed Solution

In `.chaplain/actions/yamlgraph_async_action.py`:

1. Import `shlex`.
2. Keep existing placeholder substitution (`{ctx_key}` replacement) unchanged.
3. Replace manual double-quote wrapping with shell-safe quoting:
   - Build each var as `f"{key}={shlex.quote(resolved)}"`.
   - Keep argument structure `["--var", "<key>=<quoted-value>"]`.
4. Keep command assembly (`" ".join(cmd_parts)`) and subprocess execution path unchanged.

This isolates the fix to one boundary and avoids broader pipeline refactors.

## Acceptance Criteria

- [x] **AC-01:** `YamlgraphAsyncAction` encodes each `--var` argument as `key=<shell-quoted value>` rather than `key="<raw value>"`.
- [x] **AC-02:** A value containing inner double quotes (e.g., `pytest.mark.skip(reason="FR-316 obsolete")`) survives as one shell token for `--var precommit_output=...`.
- [x] **AC-03:** Values containing shell metacharacters (`$`, backticks, `;`, `&&`, parentheses) are quoted so they are passed literally, not interpreted by shell parsing.
- [x] **AC-04:** Context placeholder substitution still occurs before quoting.
- [x] **AC-05:** Existing success/error/event_map routing behavior in `YamlgraphAsyncAction.execute()` remains unchanged.
- [x] **AC-06:** RED acceptance tests are added in `tests/unit/test_fr319_watcher_yamlgraph_async_shell_safe_vars.py`.

## Failing Acceptance Tests (RED)

Create `tests/unit/test_fr319_watcher_yamlgraph_async_shell_safe_vars.py` with:

1. `test_ac01_precommit_output_with_inner_quotes_is_single_var_token`
2. `test_ac02_shell_metacharacters_use_shlex_quote_contract`
3. `test_ac04_context_placeholders_resolve_before_quoting`

RED command:

```bash
pytest tests/unit/test_fr319_watcher_yamlgraph_async_shell_safe_vars.py -q --no-cov
```

Expected RED before implementation:

- AC-01 fails because current `"{resolved}"` wrapping produces shell token splitting.
- AC-02 fails because command text does not use `shlex.quote()` output contract.
- AC-04 fails because resulting parsed `--var` token does not preserve full substituted content as a single value.

## Alternatives Considered

1. **Switch to `create_subprocess_exec()` with arg list**
   Rejected in this FR: larger refactor touching command construction and execution semantics; not minimal for issue #304.

2. **Manual escaping with string replace (`\"`, `\$`, etc.)**
   Rejected: brittle and incomplete versus standard shell quoting.

3. **Pass `precommit_output` via temporary file instead of `--var`**
   Rejected: adds new IO contract and prompt wiring complexity beyond this bug scope.

## Related

- GitHub issue #304: <https://github.com/sheikkinen/yamlgraph/issues/304>
- `.chaplain/actions/yamlgraph_async_action.py`
- `.chaplain/actions/precommit_action.py`
- `.chaplain/config/watcher-pipeline-v2.yaml`
- `.chaplain/graphs/watcher-enforce/prompts/validate-session.yaml`
- `yamlgraph/tools/shell.py`
- Topic source requested: `.chaplain/processing/gh-304.md` (not present in this worktree)
- Canonical source used: GitHub issue #304
