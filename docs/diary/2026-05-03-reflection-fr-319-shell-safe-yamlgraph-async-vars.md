# Reflection: FR-319 Shell-Safe YAMLGraph Async Vars

**Date:** 2026-05-03
**FR:** FR-319
**Issue:** gh-304

## Cognitive Process

The bug was clear: `asyncio.create_subprocess_shell()` passes variables through the shell, causing parentheses in precommit output (e.g., `pytest.mark.skip(reason="...")`) to be interpreted as shell syntax.

## Trap Encountered

**downstream_fix** — The symptom was in the precommit_check state but the root cause was in `yamlgraph_async_action.py` where variables were passed unsafely to shell commands.

## Insight

Normalize at the boundary where external data enters (the_one_law). The fix switches to `create_subprocess_exec()` or properly escapes variables before shell invocation.

## Seed

Could we lint for `create_subprocess_shell()` usage and flag any instance that interpolates variables without `shlex.quote()`?
