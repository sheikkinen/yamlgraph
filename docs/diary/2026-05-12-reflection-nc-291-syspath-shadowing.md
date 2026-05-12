# Reflection: NC-291 sys.path Shadowing in Production

**Date:** 2026-05-12
**FR:** NC-290 → NC-291 — action import shadowing from sys.path pollution
**Reviewer:** human + agent collaborative troubleshooting

## Trap

`downstream_fix`: NC-290 diagnosed the symptom (`No module named 'actions.real'`)
and applied `__init__.py` files to convert namespace packages to proper packages.
Three deploy cycles were spent on this fix before discovering it was irrelevant —
the wrong `actions` package was being found first because `statemachine_engine/`
itself was on `sys.path[0]`.

`symptom_patch`: SSH reproductions always passed, creating false confidence. The
SSH environment doesn't exercise the `statemachine` CLI entry point, so the
contaminated `sys.path` never appeared. The debug-patched action_loader (logging
`sys.path` and `sys.modules`) should have been the first action, not the last.

`quick_confidence`: the initial diagnosis ("missing `__init__.py`") felt
plausible and was cheap to apply. This certainty delayed the deeper
investigation by three deploy-and-test cycles.

## What Happened

After deploying NC-280 (supervisor mode for concurrent calls) and commit
`b20bf0f` (voice_runtime as pip package), every incoming call failed immediately.
The FSM worker could not load the `yamlgraph_async` action.

Initial investigation focused on namespace packages and `__init__.py` presence.
Three deploys tested this hypothesis — all failed. Debug logging finally revealed
the true root cause: `engine.py` line 674 contained
`sys.path.insert(0, str(Path(__file__).parent.parent))` inside
`_emit_realtime_event()`. This added the `statemachine_engine/` package directory
to `sys.path[0]`. Since the event socket was always disconnected, this fallback
fired on every state transition, adding the package dir repeatedly. The internal
`statemachine_engine/actions/` directory then shadowed the application's
`/app/actions/`.

The fix: replace the `sys.path` manipulation with a proper absolute import
(`from statemachine_engine.database.models import get_realtime_event_model`).
Five other files in the FSM codebase had the same antipattern — all already used
proper `from statemachine_engine.xxx` imports immediately after the unnecessary
`sys.path.insert`, making the path manipulation dead code. Published as
statemachine-engine 1.0.90.

## What Worked

- Docker local reproduction confirmed the fix before deploying to Fly.io.
- The user's key observation — "3 entries in sys.path = 3 workers" — connected
  the sys.path contamination to NC-280's concurrent call architecture, directing
  the search to `engine.py` rather than `action_loader.py`.
- `grep sys.path.insert` across the FSM codebase found the culprit at line 674
  and five siblings — all fixed in one pass.

## What Failed

- **Recent-changes blindness**: the agent did not spontaneously inventory what
  changed between the last working deploy and the broken one. The user had to
  explicitly point out: "two changes yesterday: voice_runtime as a package and
  handling of multiple concurrent calls." This context was available in git log
  but was not consulted as a first diagnostic step.
- **SSH reproduction paradox**: four SSH-based import tests all passed, consuming
  time and building false confidence. The divergence between SSH `sys.path` and
  subprocess `sys.path` was the critical variable, but it was discovered last.
- **Smoke check gap**: the deploy smoke check (`fly ssh console -C "python3 -c
  'from actions.real...'"`) passes in SSH but doesn't exercise the worker
  subprocess path. A true smoke check must validate within the actual worker
  process context.

## Insight: Recent-Changes Analysis as First Diagnostic Step

When troubleshooting a regression in a deployed system, the first step should be:

```
git log --oneline --since="<last_known_good>" -- <affected_path>
```

Enumerate every change. For each, ask: "Could this change the import/load/path
environment?" This is cheaper than any reproduction and immediately narrows the
search space. In this case, it would have surfaced `_emit_realtime_event`'s
`sys.path.insert` as the only path-modifying code that runs per-state-transition
— a hot path that fires dozens of times per call.

**For LLM agents specifically**: the agent lacks implicit awareness of "what
changed recently." This must be an explicit, structured step in any
troubleshooting workflow: gather the diff, read it, reason about environmental
side effects. The cheapest bug is the one caught in the changelog.

## Seed

The `_emit_realtime_event` fallback fires on every state transition because the
event socket is never connected in supervisor mode. Should the supervisor spawn
a shared event relay process that all workers connect to — eliminating both the
fallback noise and the database write overhead? Or would that add coupling
between workers that the isolation model (NC-280) was designed to prevent?
