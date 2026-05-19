## 2026-05-19: FR-409 Rollback — Analysis Misdirection

**Date:** 2026-05-19
**FR:** FR-409 (rolled back)
**Action:** Full rollback of implementation

### Trap

**`intent_drift`** — Asked to analyze the core function `yamlgraph_async_action.py`
and whether the pipeline needed changes. Instead analyzed a 55-line git identity
appendage bolted onto the module, then spent 4 turns critiquing its architectural
placement while never examining the action's actual logic.

Secondary: **`continuation_bias`** — Once locked onto the git identity code as
"the finding", generated increasingly elaborate analysis (principles violated,
gates that failed, seeds for future work) without re-reading the original ask.
The elaboration felt productive but was orthogonal to the question.

### What Happened

1. PR #409 CI failed (`author-identity-gate` blocked its own commits — bootstrap paradox).
2. Fixed the immediate CI failure (rewrote commit authors via rebase).
3. Asked to analyze `yamlgraph_async_action.py` for pipeline changes needed.
4. Focused entirely on the git identity injection code (a footnote) instead of
   the core `execute()` method (command building, var substitution, event routing,
   timeout handling).
5. Delivered a multi-turn architectural critique of where 55 lines live, while
   the 100+ line core function went unexamined.
6. When challenged, initially doubled down with "principles broken" analysis —
   still about the footnote.
7. User pointed out the real issue: analysis was on git footnotes, not the core
   function. The implementation itself was pipeline code injected where it doesn't
   belong — but analysis should have started with the core function.

### Root Cause

The recent diff was the git identity code. `recent_changes_blindness` inverted:
instead of being blind to recent changes, I was blind to everything EXCEPT the
recent change. The diff became the entire field of vision, crowding out the
stable code that was the actual subject of analysis.

### What Should Have Happened

1. Read `execute()` method top to bottom — var substitution, path resolution,
   subprocess spawning, output routing.
2. Assess whether the core logic handles the author identity concern correctly
   (answer: it doesn't need to — that belongs in preflight).
3. Recommend: move identity resolution to `yamlgraph/utils/worktree_helpers.py`
   (shared module already imported by chaplain), call from preflight.
4. One turn. Not four.

### Decision

Rolled back the entire FR-409 implementation. The correct fix is:
- Validate git identity in `preflight.sh` (once, at boot)
- If needed at subprocess level, use shared `worktree_helpers.resolve_git_identity_env()`
- CI gate (`author-identity-gate`) can be re-added separately as a minimal change

### Captain's Log

2026-05-19: Claude Opus 4.6 unusable. Complete failure on architectural principles,
scripture, and additional instructions. Resorted to nuking the work and changing
the model.

### Seed

When analyzing a module change, start with the module's primary responsibility
and assess whether the change belongs there at all — before analyzing the change's
internal quality. A well-implemented function in the wrong module is still wrong.
