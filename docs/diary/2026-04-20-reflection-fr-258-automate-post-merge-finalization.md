## 2026-04-20: FR-258 — Implementation Reflection

**Context:** Implemented automated post-merge finalization in watch.sh, extracting shared library from finalize_merge.sh.

**Trap:** `downstream_fix` — The original inline duplication between finalize_merge.sh and watch.sh was the classic symptom of not normalizing at the boundary. The shared library extraction (.chaplain/lib/finalize_lib.sh) normalizes the four finalization functions at one source, preventing drift between manual and automated paths.

**Heuristic:** When two scripts need the same text transforms, extract to a sourceable library immediately. The "just copy it" impulse creates a second maintenance point that ages silently — the 94.7% failure rate of manual finalization proves that detection-without-enforcement degrades to audit-as-ritual faster than any human notices.

**Seed:** Can the shared library pattern be extended to other .chaplain/ scripts that share logic (e.g., worktree setup, git operations)? Should `.chaplain/lib/` become a systematic factoring point for all daemon shell utilities?
