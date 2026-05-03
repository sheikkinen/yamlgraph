# Diary: FR-317 Retire Obsolete Watcher2 Components

**Date:** 2026-05-03
**FR:** FR-317
**Scope:** chaplain infrastructure cleanup

## What Happened

Issue #300 requested cleanup of obsolete watcher components after the FSM migration. The automated enforce step correctly identified removals (watcher2.sh, graphs/copilot/, graphs/enforce/, test-entry.md) and prompt migrations (judge.yaml from copilot/prompts to watcher-plan/prompts). However, it over-migrated — moving 9 dead prompts to new locations and writing tests to validate the moves.

## The Trap: Migration as Preservation

The enforce step conflated "migrate" with "preserve." When removing old directories, it moved every prompt file to the new location instead of asking "is this prompt referenced by any graph?" Only `judge.yaml` was actually needed (by `step-judge-v2.yaml`). The other 9 prompts were dead code being relocated rather than deleted.

The second trap: the enforce step then wrote tests asserting these dead prompts existed at the new path, creating self-reinforcing dead code — the test validates the file exists, the file exists because it was migrated, but no runtime code uses it.

## The Cure

Manual finalization removed the dead migrated prompts and their assertions. The `write-acceptance-tests.yaml` and `research.yaml` prompts were restored because existing tests (from earlier FRs, not this enforce run) reference them as plan-phase artifacts.

## Key Insight

**Dead code migration is not cleanup — it's relocation.** The boundary check should be: "does any graph YAML reference this prompt file?" not "should this prompt exist in the new directory structure?"

## Seed

Could the validate-session graph run a "dead prompt scan" — checking that every `.yaml` file in a `prompts/` dir is referenced by at least one graph node's `prompt:` key?
