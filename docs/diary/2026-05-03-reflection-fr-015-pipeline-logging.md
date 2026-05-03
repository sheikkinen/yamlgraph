# Reflection: FR-FSM-015 pipeline logging

**Date:** 2026-05-03
**FR:** FR-FSM-015

**Trap**
partial_remediation

**What Happened**
The dispatcher command already had most of the logging pipeline, but the contract was only implicit. Without explicit acceptance tests, the behavior could regress silently in later refactors.

**Root Cause**
I initially relied on existing implementation shape instead of codifying the behavior at the same boundary where the logs are created (dispatcher `processing_topic` command).

**What Worked**
I added direct acceptance tests against the dispatcher command contract (log filename pattern, `--debug`, retention command, and dispatcher log path invariant) and tightened the command with explicit `logs/` creation plus emitted pipeline log path.

**Seed**
Should watcher FSM configs expose a shared shell helper for log setup/rotation so dispatcher and validation scripts cannot drift on retention and naming rules?
