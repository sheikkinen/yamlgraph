# Watcher2 Sanity-Check Reflection: FR-327 LLM-as-gate Pattern Reference

**Date:** 2026-05-05
**FR:** FR-327 reference doc for LLM-as-gate pattern
**Reviewer:** watcher2 (post-validate sanity check)
**Routing:** PASS

## Trap

`audit_as_ritual` — The risk was rubber-stamping a docs-only change
without verifying the acceptance tests actually interrogate the document
content. Tests that only assert file existence would pass trivially with
an empty file. This review confirmed that the 8 tests mechanically scan
for required tokens (router contract, schema shape, semantic vs
deterministic framing, composition guidance) — not just file presence.

## What Happened

FR-327 was a documentation-discoverability fix. The enforce commit
delivered:
- `reference/patterns/llm-as-gate.md` — complete with router YAML
  snippet, prompt schema, semantic-vs-deterministic guidance, and
  composition (chaining, fallback, retry).
- `reference/README.md` updated with link.
- `tests/unit/test_fr327_llm_as_gate_pattern_docs.py` — 8 tests, one
  per AC, all passing in 0.11 s.
- Changelog fragment, diary entry, and FR status all committed together
  in one clean squash-ready commit.

No runtime code was touched. Diff was 313 insertions, 0 deletions —
proportional to a docs+tests-only FR.

## Root Cause

No defect found. The existing diary entry
(`2026-05-05-reflection-fr-327-llm-as-gate-pattern.md`) was authored
during the enforce phase and already captures the `framework_costume`
trap and the `spec_kill` cure. Watcher2 review found nothing to add to
root-cause analysis.

## What Worked

- Token-level acceptance tests as gating contract prevented the doc from
  being a hollow stub that satisfies file-existence alone.
- The `spec_kill` heuristic held: the cheapest bug was killed in the FR
  itself (no new primitive added).
- Diary and changelog were co-committed with the feature — not deferred.
- `@pytest.mark.req("REQ-YG-271")` links tests to the requirement
  registry, satisfying traceability doctrine.

## Minor Observation

The changelog fragment (`changelog/unreleased/fr-327-llm-as-gate-pattern.md`)
omits the optional `req:` front-matter field. Per `CLAUDE.md` the field
is optional (`omit if none`), so `changelog-req-gate` should pass. If
CI surfaces a failure here, add `req: REQ-YG-271`. Flagged, non-blocking.

## Seed

Should the `docs/diary/` naming convention for watcher2 sanity-check
entries be enforced by a pre-commit or CI gate (e.g., require
`-watcher2-sanity-check-state.md` suffix when the diary author is
`watcher2`) to prevent diary entries from being silently misclassified
as enforce-phase reflections?
