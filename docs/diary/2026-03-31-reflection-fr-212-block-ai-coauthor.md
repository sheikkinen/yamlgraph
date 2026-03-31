# 2026-03-31: FR-212 — Block AI Co-Author Trailers

**Context:** Implemented a `commit-msg` pre-commit hook (`block_ai_coauthor.py`) that
detects AI agent `Co-authored-by:` trailers and blocks the commit with a penance liturgy.
Followed strict TDD (RED → GREEN): 12 failing tests written first, then minimal script +
config change to make them pass.

**Trap:** `infrastructure_self_exempt` — the instruction scaffold (GitHub Copilot CLI) injects
the very trailer this hook now blocks. This creates a reflexive enforcement loop: the tool
that helps write the hook also adds the thing the hook forbids. The cure is clarity of
ownership: the committer edits the message before signing; the hook enforces that contract
at the boundary.

**Heuristic:** `enforcement_at_merge_boundary` — a local `commit-msg` hook is the earliest
enforceable gate. By the time a trailer reaches CI, it is already in branch history. The
`--no-verify` bypass is already forbidden by doctrine; therefore the hook cannot be silently
skipped. Normalize at the boundary.

**Seed:** Could the hook auto-strip known AI trailers (with a `--fix` flag) rather than
always blocking? Would silent correction undermine the penance ritual and author-ownership
principle, or is it pragmatic when working solo?
