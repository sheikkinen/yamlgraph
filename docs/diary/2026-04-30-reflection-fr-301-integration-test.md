# 2026-04-30 — Reflection: FR-301 No-LLM Integration Test

## What happened

Created isolated FSM configs (`integration-dispatcher.yaml`, `integration-pipeline.yaml`) that run the full watcher pipeline end-to-end with bash stubs replacing all 4 LLM steps. 28 acceptance tests, a wrapper script, and a CONF-300 confession for `--no-verify`.

## Cognitive process

The FR was well-specified after judgement added 5 amendments (A1–A5). Enforcement was mostly mechanical — translate the FR spec into YAML configs and test code. Three corrections during enforcement:

1. **Missing `subprocess` import** — copied the test pattern from FR-291 but forgot the import since the lint tests were at the bottom of the file. Caught immediately by running tests.

2. **Lint `--select` filter** — `statemachine-lint` reports E008 (unknown action type) for custom types like `bash_context` and E012 for context keys injected at runtime. Production tests already handle this with `--select E001,...,E007`. Applied the same pattern.

3. **Changelog req cross-wiring** — used `req: REQ-YG-162` in the changelog fragment, but FR-301 has no capability file mapping it to that REQ. The `test_no_req_collision_across_unrelated_frs` guard caught this. Fixed by removing the req field.

## Trap: req_inheritance_assumption

The tests use `@pytest.mark.req("REQ-YG-162")` because it's the same capability area (watcher FSM). But the changelog fragment's `req:` field has a different contract — it must map through a capability file. Same identifier, different validation boundary. This is `false_duplicate` from the Knowledge Graph: syntactic similarity does not imply semantic equivalence.

## Heuristic

**Test markers and changelog fragments validate through different pipelines.** `@pytest.mark.req` is checked by `req_coverage.py` against `ARCHITECTURE.md`. Changelog `req:` is checked by `changelog-req-gate` against capability YAML files. Don't assume one grants permission for the other.

## Seed

Should the changelog-req-gate and req_coverage.py share a single source of truth for FR→REQ mappings, or is the current dual-validation intentional (catching drift between architecture docs and capability registry)?
