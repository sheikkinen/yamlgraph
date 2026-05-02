---
type: feat
scope: fsm
---
- **FR-305 Watcher Pipeline FSM Simplification**: Collapse 20+ state pipeline into 6 operational states (plan, commit_plan, judge, enforce, validate, done) with enforce⇄validate retry loop and session continuations.
