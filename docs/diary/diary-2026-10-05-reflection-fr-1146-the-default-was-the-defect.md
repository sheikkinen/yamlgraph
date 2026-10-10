# Reflection: FR-1146 — the default was the defect

**Date:** 2026-10-05
**FR:** FR-1146 (omit temperature for Anthropic models that reject it)

## What happened

`claude-sonnet-5-5` returned `400 temperature is deprecated for this model`
on the hello demo. The first instinct was "remove temperature from the
graph". The demo did set `temperature: 0.7`, but the factory replaces
`None` with `0.7` anyway. The client library already omitted `None`
from the wire. YAMLGraph's own "some providers reject None" default was
what reintroduced the value the provider now refuses. So a graph-level
fix could not have worked.

Probing every listed model (13) turned "Sonnet 5.5 is different" into
a clean split: 8 reject, 5 accept. A capability flag
(`thinking.enabled.supported`) matched the split 13/13. That was
tempting, but no documentation links the flag to sampling, so the guard
keys on an allowlist of probed ids instead. The judge then struck the
legacy ids I had added from memory (`claude-3`, 4.0, 4.1). Each of those
entries would have preserved a parameter with no evidence behind it,
which is the same claim-without-probe shape the allowlist exists to
prevent.

## Traps

- **Direction of the list.** FR-455 used a *denylist* of rejecting
  models. For a vendor whose newest models drop the parameter, a
  denylist reproduces this incident on every release. The safe direction
  is the closed, older set.
- **Shared editable install.** The worktree recreate re-pointed the
  shared `.venv` at the worktree; by enforce time it pointed back at
  main again (cause not traced: another session or a hook).
  `pytest` used the worktree (rootdir), but `python -c "import yamlgraph"`
  used main. I caught this only because the AC-09 probe failed with an
  `ImportError`. A probe that had imported an *existing* name would have
  silently measured main's code. Pin `PYTHONPATH` before any live witness.
- **Unactivated venv again.** `test_ramp_installer` failed on bare
  `python3`. Repo memory already recorded this exact case; the stash
  counterfactual confirmed it in one command.

## Heuristic

When a provider starts refusing a parameter, look for where *we* invent
that parameter first. The fix boundary is our default, not the
caller's config.

**Seed:** extended thinking on the same 8 models now fails for a parallel
reason (`thinking.type.enabled` → `adaptive` + `effort`). Is there one
"Anthropic generation" boundary object that should own both sampling and
thinking shape, rather than two prefix tuples drifting apart?
