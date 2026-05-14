# Reflection: FR-385 CI gate to block Copilot co-author trailers

**Date:** 2026-05-14
**FR:** FR-385
**Branch:** feat/watcher2-gh-388

## Cognitive Process

The task was to add a deterministic CI gate that blocks Copilot `Co-authored-by` trailers from reaching the merge boundary via PR commits or PR body text. The local `block-ai-coauthor` pre-commit hook (CAP-82 / REQ-YG-215) already existed but local hooks alone cannot enforce at merge boundary.

The implementation followed the repo's established CI gate pattern: a standalone job in `.github/workflows/commitlint.yml` using deterministic shell grep, with unit tests covering both workflow structure and shell behavior. Existing gates (`conflict-check`, `changelog-gate`, `diary-gate`) provided clear precedent — copy the shape, substitute the concern.

Traceability entries (CAP-148, REQ-YG-358) were added to maintain the capability registry and requirement coverage chain.

## Traps Encountered

**Detection-without-enforcement trap (graduated pattern).** The local pre-commit hook was already present but local hooks can be bypassed or are simply not run on server-side merges. Recognising that "detection exists locally" is not the same as "enforcement exists at the merge boundary" was the key insight that motivated the CI gate. A guard that only fires locally is advisory, not mandatory.

**Scope creep temptation.** The problem statement could easily expand to "block all AI trailer variants" or "replace/refactor the local script." Both were explicitly rejected to keep the change minimal and reviewable. Naming the out-of-scope items in the FR provided a forcing function to resist those expansions during implementation.

## Heuristic

> **Local guard ≠ merge-boundary enforcement.** When a policy exists only as a local pre-commit hook, treat it as advisory until a corresponding CI gate blocks the same condition at PR merge. The merge boundary is the last deterministic enforcement point — add a CI job, not just a local script.

## Seed

**Seed:** The `copilot-trailer-gate` currently scans for two specific string forms of the Copilot trailer. Could a generalised "vendor trailer policy" gate be defined declaratively (e.g., a YAML list of blocked trailer patterns in `.github/`) so new vendor-trailer rules can be added without modifying workflow YAML? This would decouple the policy definition from the enforcement mechanism and make future expansions a one-line config change rather than a workflow edit.
