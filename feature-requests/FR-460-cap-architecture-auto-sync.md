# Feature Request: FR-460 Auto-Regenerate ARCHITECTURE.md on CAP Changes

**Priority:** LOW
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-05-25

## Summary

Add a pre-commit hook that auto-runs `aggregate_capabilities.py` when `capabilities/*.yaml` files change, keeping ARCHITECTURE.md in sync.

## Value Statement

Developers get automatic ARCHITECTURE.md regeneration on capability changes, eliminating silent drift between the capability registry and architecture documentation.

## Problem

When a `capabilities/*.yaml` file is added or modified, ARCHITECTURE.md is not regenerated automatically. The pre-commit pipeline validates CAP schema (`validate-capabilities`) and checks requirement coverage (`req_coverage --strict`), but does not regenerate the derived content in ARCHITECTURE.md.

This causes silent drift:

1. Developer adds CAP-159 and commits
2. Schema validation passes, req coverage passes
3. ARCHITECTURE.md still contains stale generated content
4. Tests that assert on ARCHITECTURE.md content (`test_ac09_capability_registry_contains_cap149_req359`) break later when someone manually runs `aggregate_capabilities.py`

**Incident:** During FR-452 enforcement, manual `aggregate_capabilities.py` execution exposed two pre-existing issues:
- `CAP-` prefix format regression in `aggregate_capabilities.py` (the script had been modified but ARCHITECTURE.md was never regenerated)
- Stale REQ-YG-063 wording in CAP-18 (description updated but ARCHITECTURE.md still had old text)

Both had been silently drifting. The `detection_without_enforcement` pattern from Scripture applies: validation without regeneration is advisory, not a gate.

## Proposed Solution

Add a pre-commit hook mirroring the `changelog-release-sync` pattern:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: cap-architecture-sync
      name: capability architecture sync
      entry: .venv/bin/python scripts/aggregate_capabilities.py
      language: system
      pass_filenames: false
      files: (^capabilities/.*\.yaml$|^scripts/aggregate_capabilities\.py$)
      stages: [pre-commit]
```

The hook:
1. Triggers when any `capabilities/*.yaml` or the aggregate script itself changes
2. Runs `aggregate_capabilities.py` which regenerates the section between `<!-- BEGIN GENERATED CAPABILITIES -->` and `<!-- END GENERATED CAPABILITIES -->` markers
3. If ARCHITECTURE.md changes, the developer sees the diff and stages it

**No auto-staging needed** — pre-commit will detect the unstaged change and fail, prompting the developer to `git add ARCHITECTURE.md`. This is the same behavior as `ruff format` auto-fixes.

## Acceptance Criteria

- [ ] Pre-commit hook `cap-architecture-sync` triggers on `capabilities/*.yaml` changes
- [ ] Hook runs `aggregate_capabilities.py` and updates ARCHITECTURE.md
- [ ] Adding a new CAP file and committing regenerates ARCHITECTURE.md automatically
- [ ] Modifying a CAP description and committing updates the generated section
- [ ] Hook does not run when non-CAP files change (performance)
- [ ] Tests pass with regenerated content

## Alternatives Considered

- **`.github/hooks` (Copilot PreToolUse/PostToolUse)** — Wrong layer. CAP regeneration is a deterministic transform, not an agent tool call guard. `.github/hooks` are for real-time Copilot Chat interception.
- **CI-only check** — Catches drift at PR time but doesn't fix it. Developer still has to manually regenerate. Pre-commit is earlier and auto-fixes.
- **Make ARCHITECTURE.md fully generated** — Too aggressive. Only the capabilities section is generated; the rest is hand-authored.

## Related

- FR-452 — Exposed the silent drift during enforcement
- `changelog-release-sync` hook — Same pattern (derived file regeneration on source change)
- `aggregate_capabilities.py` — The regeneration script
- Scripture: `detection_without_enforcement` — "Lint without gate = advisory"
