# Feature Request: FR-068 Chaplain Watch Loop

**Priority:** LOW
**Type:** Enhancement
**Status:** Done
**Effort:** 0.5 day
**Requested:** 2026-02-21

## Summary

File watcher that runs Plan → Judge → Amend loop automatically when topics appear in `.chaplain/inbox/`.

## Problem

Manual invocation of "Plan... → Judge... → Amend..." requires human to type each prompt. Batch FR creation is tedious.

## Proposed Solution

```
.chaplain/
├── inbox/       # Drop topic files here
├── drafts/      # Intermediate state
└── watch.sh     # The loop
```

**watch.sh core:**
```bash
while true; do
    topic_file=$(find .chaplain/inbox -name "*.md" | head -1)
    [[ -z "$topic_file" ]] && { sleep 5; continue; }

    topic=$(cat "$topic_file")
    slug=$(basename "$topic_file" .md)

    # Plan
    copilot -p "Plan a solution for: $topic. Document as FR."

    # Judge loop (max 3 cycles)
    for i in 1 2 3; do
        verdict=$(copilot -p "Judge FR in .chaplain/drafts/$slug.md")
        [[ "$verdict" == *APPROVE* ]] && break
        [[ "$verdict" == *AMEND* ]] && copilot -p "Amend FR $slug.md"
    done

    # Move approved FR to feature-requests/
    mv .chaplain/drafts/$slug.md feature-requests/
    rm "$topic_file"
done
```

**Usage:**
```bash
# Terminal 1
.chaplain/watch.sh

# Terminal 2
echo "Map node timeout" > .chaplain/inbox/map-timeout.md
```

## Acceptance Criteria

- [x] `watch.sh` processes inbox files in order
- [x] Plan creates draft FR with next number
- [x] Judge outputs APPROVE/AMEND/REJECT
- [x] Amend loop runs max 3 times
- [x] Approved FRs moved to `feature-requests/`
- [x] Rejected FRs marked `.rejected.md`

## Alternatives Considered

1. **Manual prompts only** — Current state. Works but tedious for batch.
2. **Full agent orchestration** — Tried in chaplain.sh. Too complex.

## Related

- `scripts/chaplain.sh` — Existing implementation (more complex)
- `docs-planning/plan-four-agent-chaplaincy.md` — Protocol definition
