# Feature Request: Re-integrate Inquisitor into Watcher2 FSM

**Priority:** HIGH
**Type:** Regression Fix
**Status:** Approved (scope-narrowed)
**Effort:** 0.5 day
**Requested:** 2026-05-18

## Summary

The Inquisitor audit loop was integrated into the old `watch.sh` (FR-261) but lost when the watcher was rebuilt as the FSM-based `start-system.sh` + `watcher-dispatcher.yaml` + `watcher-pipeline-v2.yaml`. The 27-day gap between audits (audit 233 on 2026-04-21 → audit 234 on 2026-05-18, run manually) proves the regression.

## Value Statement

Without periodic automated audits, doctrine drift accumulates silently. The Inquisitor is the only feedback loop that detects violations *after* code reaches `main`. Manual runs are unsustainable — the 27-day gap is the evidence.

## Problem

1. **FR-261 implemented against dead code**: The old `watch.sh` no longer exists. It was replaced by an FSM system (`start-system.sh` → `watcher-dispatcher.yaml` → `watcher-pipeline-v2.yaml`).
2. **No inquisitor state in the FSM**: The pipeline states are `setup → plan → capture_fr → judge → enforce_session → validate_fix → sanity_check → validate_gate → done → completed`. No audit step.
3. **Dispatcher has no post-cycle hook**: After `topic_done`, the dispatcher returns to `idle` immediately. No opportunity for periodic maintenance tasks.
4. **Result**: Inquisitor only runs when someone manually invokes `.chaplain/inquisitor.sh --force`.

## Proposed Solution

### Design: Action-internal time check + new event

The `statemachine-engine` has no `guard:` primitive. All decision logic lives inside actions. The integration point is the existing `syncing_inbox` action — after checking the inbox, it also checks time since last audit.

**New state:** `auditing`
**New events:** `audit_needed`, `audit_done`
**New context key:** `last_audit_ts` (epoch seconds, default 0)

#### Dispatcher YAML changes (`watcher-dispatcher.yaml`):

```yaml
states:
  - idle
  - syncing_inbox
  - processing_topic
  - auditing          # NEW
  - stopped

events:
  - "timeout(10)"
  - topic_found
  - no_topics
  - audit_needed      # NEW
  - audit_done        # NEW
  - topic_done
  - error
  - stop

context:
  inbox_dir: ".chaplain/inbox"
  last_audit_ts: 0    # NEW

transitions:
  # ... existing transitions unchanged ...

  # NEW: daily audit trigger
  - from: syncing_inbox
    to: auditing
    event: audit_needed

  # NEW: audit complete → idle
  - from: auditing
    to: idle
    event: audit_done

  # NEW: audit failure → idle (non-blocking)
  - from: auditing
    to: idle
    event: error
```

#### Action logic change (in syncing_inbox action):

After inbox check finds no topics, add:

```python
import time

AUDIT_INTERVAL = 86400  # 24 hours

last_audit = context.get("last_audit_ts", 0)
if time.time() - last_audit >= AUDIT_INTERVAL:
    return "audit_needed"
return "no_topics"
```

#### New action (`audit_action.py`):

```python
"""AuditAction — Run .chaplain/inquisitor.sh --propose, update last_audit_ts."""

import asyncio
import time
from statemachine_engine.actions.base import BaseAction

class AuditAction(BaseAction):
    async def execute(self, context: dict) -> str:
        proc = await asyncio.create_subprocess_shell(
            ".chaplain/inquisitor.sh --propose",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()

        # Log output
        log_path = f"logs/inquisitor-{int(time.time())}.log"
        with open(log_path, "w") as f:
            f.write(stdout.decode())

        # Update context timestamp
        context["last_audit_ts"] = int(time.time())

        if proc.returncode != 0:
            return "error"
        return "audit_done"
```

#### Key properties:

- **No new FSM primitives** — uses existing action → event return pattern
- **Decision logic in Python** — where it belongs in this engine
- **Cold start triggers immediately** — `last_audit_ts: 0` means first poll cycle fires audit (~10s after watcher starts)
- **Inquisitor's own gates still active** — commit-delta gate (FR-131) skips if nothing to audit
- **Non-blocking** — `error` event returns to `idle`, never halts the loop

## Recommendation

**Action-internal time check** as designed above. Single approach — no options to choose between. Decision logic in Python (where the engine expects it), state transitions in YAML (where they're observable). Once-daily cadence, cold-start-fires-immediately.

## Acceptance Criteria

- [ ] `auditing` state added to `watcher-dispatcher.yaml`
- [ ] `audit_needed` and `audit_done` events added
- [ ] `last_audit_ts` context key (default 0) added
- [ ] Syncing inbox action emits `audit_needed` when `time.time() - last_audit_ts >= 86400`
- [ ] `audit_action.py` runs `.chaplain/inquisitor.sh --propose` and updates `last_audit_ts`
- [ ] Audit failure emits `error` → returns to `idle` (non-blocking)
- [ ] Audit runs visible in FSM UI state transitions and logged to `logs/inquisitor-*.log`
- [ ] Inquisitor's own gates (worktree FR-142, commit-delta FR-131) remain active
- [ ] Manual invocation still works: `.chaplain/inquisitor.sh --force`
- [ ] FR-261 status updated to note supersession by this FR

## Related

- **FR-261**: Original inquisitor-into-watch-loop (implemented against now-dead `watch.sh`)
- **FR-076**: Inquisitor original implementation
- **FR-118**: `--propose` flag feeding inbox
- **FR-131**: Commit-delta gate (skips when no feat/fix since last audit)
- **FR-296**: Watcher2 FSM system (`start-system.sh`)
- **FR-305**: Pipeline v2 state collapse
- `.chaplain/config/watcher-dispatcher.yaml` — dispatcher FSM
- `.chaplain/config/watcher-pipeline-v2.yaml` — pipeline FSM
- `.chaplain/inquisitor.sh` — audit script (unchanged)

## Judgement

**Verdict:** APPROVE — Scope frozen, authority granted.

**Annotations:**

1. **No guards in statemachine-engine.** Confirmed by the engine author. All decision logic lives in action `execute()` methods that return event names. The design correctly places the time check inside the syncing_inbox action.

2. **Cold start fires immediately.** `last_audit_ts: 0` means first poll cycle triggers audit. Correct — the 27-day gap proves we want an immediate audit on startup.

3. **Inquisitor's commit-delta gate (FR-131) is the safety valve.** Even if the FSM triggers daily, the inquisitor itself skips when no feat/fix commits exist since last audit. No ritual audits.

4. **Single design, no option matrix.** Removed the A/B/C analysis — there's only one correct approach given the engine's capabilities. Clean.

5. **Change surface:** 3 files touched — `watcher-dispatcher.yaml` (state + events + transitions), syncing_inbox action (time check + new event return), new `audit_action.py`. Minimal.

**Judge:** Claude Opus 4.6, 2026-05-18
