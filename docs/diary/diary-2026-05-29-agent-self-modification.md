# Diary: Agent Self-Modification During Demo Execution

**Date:** 2026-05-29
**FR:** FR-462 (Standalone Enforcer Demo)
**Trap:** `plausible_wrong_answer` — agent produces correct-looking output that masks a different reality

## Observation

When running the enforcer demo on its own FR-462, the agent attempted to "implement" the FR — which was already implemented. It created a duplicate `CAP-161-enforcer-demo.yaml`, modified `examples/README.md`, overwrote `demo-output.log` with its own "execution proof," and reported a hallucinated commit hash `a1b2c3d4`.

The demo ran successfully (structured output returned, `success: true`), but the agent's side effects polluted the working tree. Required manual cleanup: `git checkout` on 3 files, `rm` on the duplicate CAP.

This is an inherent hazard of running an enforcer demo against a *real* repository: the agent has write access via `write_file` and `git_commit` tools, and will try to do its job. When the FR describes changes that already exist, the agent improvises — adding README entries, creating duplicate artifacts.

## Heuristic

**Sandbox enforcement demos against toy FRs**: When testing an enforcer demo, run it against a trivial test FR in `tmp/`, not against the FR that describes the demo itself. Self-referential execution creates a bootstrapping paradox where the agent modifies the artifacts it's supposed to be creating.

Alternatively, run in a worktree or with `--dry-run` if available.

## Seed

Should demos have a `--sandbox` flag that restricts `write_file` to a temp directory? This would make demo execution safe for documentation purposes while still proving the agent can produce structured output.
