# Feature Request: FR-068 Chaplain Watch Loop

**Priority:** LOW
**Type:** Enhancement
**Status:** Draft
**Effort:** 0.5 day
**Requested:** 2026-02-21

## Summary

File watcher that runs Plan → Judge → Amend loop automatically when topics appear in `.chaplain/inbox/`.

## Problem

Manual invocation of "Plan... → Judge... → Amend..." requires human to type each prompt. Batch FR creation is tedious.

## Proposed Solution

```
.chaplain/
├── inbox/       # Drop topic files here (or FR with issues returns here)
├── drafts/      # FR being judged
└── watch.sh     # Two prompts, file-driven loop
```

### watch.sh

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "👀 Watching .chaplain/inbox/"

while true; do
    topic_file=$(find .chaplain/inbox -name "*.md" -type f | head -1)
    [[ -z "$topic_file" ]] && { sleep 5; continue; }

    echo "📋 Processing: $topic_file"

    # Plan
    copilot --allow-all-paths -p "**Plan.** Read $topic_file. Write the feature request in .chaplain/drafts/. Define objectives, constraints, acceptance criteria, and implementation approach. The feature request is the plan. Follow feature-requests/TEMPLATE.md. Delete $topic_file when complete."

    # Judge
    copilot --allow-all-paths -p "**Judge.** Examine the FR in .chaplain/drafts/. Critically examine the feature request; resolve contradictions; eliminate ambiguity; refine constraints and acceptance criteria until the path is explicit and minimal. If clear, minimal, and internally consistent: freeze scope, grant authority, move to feature-requests/. If not: write issues into the file and move back to .chaplain/inbox/."
done
```

### Flow

```
inbox/topic.md
    ↓ Plan
drafts/XXX-slug.md
    ↓ Judge
    ├── APPROVE → feature-requests/XXX-slug.md (done)
    └── NEEDS WORK → inbox/XXX-slug.md (re-enters loop)
```

**Key insight:** Judge returning file to inbox re-triggers Plan, which now sees an FR with issues and fixes them. Loop continues until Judge approves.

**Usage:**
```bash
# Terminal 1
.chaplain/watch.sh

# Terminal 2
echo "Map node timeout" > .chaplain/inbox/map-timeout.md
```

## Acceptance Criteria

- [ ] `watch.sh` only watches and calls copilot (no file ops in shell)
- [ ] `prompts/plan.md` creates draft with next FR number
- [ ] `prompts/judge.md` moves/renames files and outputs DONE
- [ ] `prompts/amend.md` fixes issues in draft
- [ ] Loop exits when judge outputs DONE
- [ ] Max 3 amend cycles

## Alternatives Considered

1. **Manual prompts only** — Current state. Works but tedious for batch.
2. **Full agent orchestration** — Tried in chaplain.sh. Too complex.

## Related

- `scripts/chaplain.sh` — Existing implementation (more complex)
- `docs-planning/plan-four-agent-chaplaincy.md` — Protocol definition
