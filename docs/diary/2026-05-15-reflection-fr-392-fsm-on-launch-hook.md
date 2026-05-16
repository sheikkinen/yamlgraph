# Reflection: FR-392 FSM on_launch Lifecycle Hook

**Date:** 2026-05-15
**FR:** FR-392 — add `on_launch` hook to `YamlgraphAsyncAction`
**Reviewer:** watcher2 validate pass

## Trap

`working_system_inertia` — The existing lifecycle hook surface (`pre_snapshot`,
`pre_dispatch`, `on_success`, `on_error`) worked. That very fact made it easy to
overlook the gap at the exact boundary where snapshot resolution completes but the
background task has not yet been scheduled. The hook was absent not from neglect but
because the system worked without it.

## What Happened

Adding `on_launch` required only four lines to `action.py`: the method definition (a
typed no-op) and the call site between `snapshot_params()` and `asyncio.create_task()`.
The position contract — snapshot resolves, hook fires, task launches — is now enforced
by AC-02's position assertions directly against source text. Tests confirm the hook is
not called when `snapshot_params()` raises `ValueError`, preserving fail-closed
semantics.

The AST-based `test_ac02` check (position in source) is a structural guard that
survives refactors that preserve line ordering but not one that reorders the three
operations. This is a deliberate choice: the constraint is about sequencing, and source
position is the cheapest proxy that doesn't require runtime instrumentation.

## Heuristic

When a lifecycle hook chain has *n* defined boundaries, check whether every meaningful
state transition inside the method has a corresponding hook. Missing hooks force
subclasses to override the entire method, which creates drift risk.

## Seed

**Seed:** Could an introspective test walk the call graph of `execute()` automatically
and emit a list of "hookable" transition points — positions where the internal state
changes materially — so that hook coverage becomes measurable rather than discovered
ad-hoc?
