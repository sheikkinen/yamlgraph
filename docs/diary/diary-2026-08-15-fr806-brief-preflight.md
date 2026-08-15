# Diary — 2026-08-15 — FR-806: the brief is code, so lint it like code

**Context:** Enforcing FR-806 (author.sh brief pre-flight), second of
the judged trio 810 → 806 → 809.

## What happened

The manual dry-run heuristic ("check the brief's premises before
burning a run") had fired successfully three times as operator
diligence and failed once as operator memory — the FR-789 run-1 death.
`two_strike_split` graduated it to code: a stdlib-only Python helper
that scans the brief for asserted-input paths, statically resolves
validation-command executables, and counts live smokes against the
900s ceiling. author.sh calls it before the lock, before the sentinel,
before any tokens.

## The design tension

The interesting decision was **fail-open vs fail-closed per check
class**. The route's report gate fails closed (a missing artifact kills
the run); the pre-flight inverts this for ambiguity: a path on a line
with neither input nor output markers is *not* checked, and a command
headed by `$(...)` is skipped, never evaluated. The asymmetry is
justified by cost direction — a false pre-flight failure kills a
legitimate 15-minute run to save nothing, while a false pass merely
returns us to the status quo (the run dies expensively, as it always
did). Advisory-vs-blocking is not a property of the gate; it's a
property of which error is cheaper.

## Trap encountered

`spec_from_file_location` + dataclass + Python 3.14: string annotations
on a dataclass fail to resolve unless the module is registered in
`sys.modules` before `exec_module`. Sixty-six test files in this repo
use the same loading pattern; most predate 3.14 or avoid dataclasses.
One line (`sys.modules[name] = module`) fixed it — but the error
surfaced as a `@dataclass` decorator failure three frames deep, not as
an import error, which cost one diagnostic cycle.

## Heuristic

When a gate guards *spend* rather than *correctness*, tune each check
to fail toward the cheaper error: block only on mechanically certain
violations, warn on heuristics, skip on ambiguity. The report gate and
the pre-flight gate share a script but not an error economy.

**Seed:** The pre-flight knows the brief's validation plan (commands,
smoke counts). The report gate later learns what validation *actually
ran*. Nobody compares the two — a brief promising three smokes whose
report shows zero validations passes both gates. Should the report
gate cross-check the pre-flight's extracted plan?
