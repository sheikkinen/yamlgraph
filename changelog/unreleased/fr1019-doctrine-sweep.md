---
type: removal
scope: doctrine
---
- **FR-1019 Doctrine and reference sweep after Chaplain removal** (Phase 3 of FR-1010): the Scripture section `## Sermon of the Chaplain` is now `## Sermon` and the canonical-sources clause no longer names a "chaplain pipeline" (two lines; Sermon steps and Knowledge Graph unchanged). `docs/development-process.md` describes the operator-driven rite (`scripts/author.sh` → `scripts/judge.sh` → worktree → `scripts/outsider.sh`/`scripts/review.sh` → human merge) instead of the FSM daemon; the one-pager, audit index, graph reference, command book, FSM-as-conductor pattern, examples README and the graph-authoring/judge-fr skill doctrines point at `proposals/`, `graphs/` and `docs/archive/` instead of `.chaplain/`. `docs/context/chaplain-system.md` moved unchanged to `docs/archive/chaplain-system.md` and is linked from `docs/archive/chaplain.md`. The judge-fr doctrine ramp mirror stays byte-identical (REQ-YG-613); no new test, requirement or census.
