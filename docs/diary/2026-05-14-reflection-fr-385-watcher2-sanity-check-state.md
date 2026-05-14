# Watcher2 Sanity Check: FR-385 CI Copilot Trailer Gate

**Date:** 2026-05-14
**FR:** FR-385
**Branch:** feat/watcher2-gh-388
**Reviewer:** watcher2 (post-validate)

## Trap

**detection-without-enforcement** — The local `block-ai-coauthor` pre-commit hook (CAP-82 / REQ-YG-215) gave a false sense of coverage. Local hooks are bypassed by server-side merges. The FR correctly identified the merge boundary as the only reliable enforcement point and added a CI gate rather than strengthening the local hook.

## What Happened

FR-385 adds a standalone `copilot-trailer-gate` job to `.github/workflows/commitlint.yml`. The job runs deterministic shell grep over `BASE_SHA..HEAD_SHA` commit messages and PR body text, failing on either `Co-authored-by: Copilot` form (short and full email). Traceability entries CAP-148 and REQ-YG-358 were added. Eight behavioral tests exercise real git repos and real bash execution, covering all 7 acceptance criteria. All 8 tests pass.

One notable diff item: a single line was removed from `.github/copilot-instructions.md` — the advisory instruction "Do not add `Co-authored-by` trailers to commits or PR bodies — CI rejects them." The removal is defensible (the actual enforcement now lives in CI, not in advisory instructions to AI agents), and aligns with the doctrine principle of enforcement over advisory.

## Root Cause

The governance gap (GitHub issue #388) existed because local pre-commit hooks are not run during server-side squash merges. Without a CI job at PR merge, the policy was advisory rather than mandatory.

## What Worked

- Established CI gate pattern (`conflict-check`, `changelog-gate`, `diary-gate`) provided an exact shape to follow — copy the job structure, substitute the concern.
- TDD: 8 RED tests written before the CI job, then all turned GREEN with the implementation.
- Behavioral tests using real git repos and real bash execution provide high signal: they test the actual gate script, not mocks.
- Scope discipline: the FR explicitly named out-of-scope items (other AI trailer variants, local hook refactor), preventing creep during implementation.

## Seed

**Seed:** The `copilot-trailer-gate` currently encodes two specific trailer strings directly in workflow YAML. As the vendor-trailer policy grows (other AI tools, future Copilot variants), each new blocked pattern requires a workflow edit. Could a policy file (e.g., `.github/blocked-trailers.txt`) be introduced so the CI gate reads patterns from config rather than hardcoding them — making policy changes a one-line config edit rather than a workflow change?
