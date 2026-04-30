# 2026-04-30 — Reflection: Watcher Standalone Scripts

## What happened

All 10 `.chaplain/lib/watcher/*.sh` scripts were broken for FSM execution. They defined functions but never called them, and used log functions that didn't exist. The FSM engine runs each script standalone via `bash script.sh`, but the scripts were written to be sourced by the old `watcher2.sh` monolith — which defined the log functions and called each function inline.

Fixed by: extracting shared `log_info`/`log_warn`/`log_error` into `common.sh`, adding CLI arg parsing to each script, and adding a function call at the bottom. One script (`wait_ci.sh`) needed a main guard pattern because an existing test (`test_fr279`) sources it.

## Cognitive process

The initial fix was mechanical — same pattern applied to all 10 scripts. But the session surfaced three distinct traps:

1. **`$0` vs `BASH_SOURCE[0]`**: First pass used `source "$(dirname "$0")/common.sh"`. This works when scripts run standalone but breaks when sourced from a temp directory (as the FR-279 test does). The fix: `BASH_SOURCE[0]` always resolves to the script's own location regardless of how it's invoked.

2. **Main guard asymmetry**: Only `wait_ci.sh` needs the `if [[ "${BASH_SOURCE[0]}" == "${0}" ]]` guard because only it has a test that sources it. The other 9 scripts get an unconditional function call. Applying the guard everywhere would be defensive coding without a test to justify it.

3. **FR-056 garbage commit**: A local-only commit from an automated chaplain run contained auto-generated RED tests and diary files for a feature that doesn't exist. It had to be dropped via interactive rebase before pushing. The trap: **infrastructure_self_exempt** — the chaplain automation created commits that didn't pass the same quality bar it enforces.

## Trap: boundary_mismatch

The root cause of all 10 broken scripts is a **boundary mismatch**: the scripts were designed for one execution model (sourced by monolith) but deployed into another (standalone by FSM engine). The functions were correct; the invocation contract was wrong. This is the `module_structure` boundary from the Knowledge Graph — import contracts must be declared, not assumed.

## Heuristic

**When migrating from monolith to modular execution, each extracted module must be self-sufficient at its boundary.** A function that depends on its caller for setup (log functions, argument parsing, invocation) is not a module — it's a fragment. The test: can you run `bash script.sh --help` and get a usage message? If not, it's not standalone.

## Seed

The 10 scripts now parse args individually with duplicated `while` loops. Could the `common.sh` shared library include a declarative arg parser — `parse_args "topic branch dir"` — that auto-generates `--topic`, `--branch`, `--dir` flags and validates required args? This would eliminate the boilerplate and enforce a consistent CLI contract across all watcher scripts.
