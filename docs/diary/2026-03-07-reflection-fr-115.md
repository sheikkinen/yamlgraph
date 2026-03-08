## 2026-03-07: Judgement — FR-115 approved, tmp/msg.txt trap surfaced

**Context:** Judged FR-115 (inquisitor auto-propose). The FR was well-scoped and evidence-backed — 7 consecutive audits documenting the same two violations, costing ~1,700 words to document problems that each require <1 minute to fix. Approved with three non-blocking implementation notes (filename determinism, edge case handling, smoke test procedure).

**Trap — stale tmp/msg.txt:** The heredoc `cat > tmp/msg.txt << 'EOF'` failed silently when chained with `git add && ... && git commit -F`, leaving a previous commit message (`fix(FR-106):`) in the file. The `changelog-required` hook caught it — the stale message triggered the feat/fix CHANGELOG gate. The trap: `tmp/msg.txt` is a shared mutable resource; any prior script can leave residue.

**Heuristic:** *Verify file content after writing, before consuming.* A `cat tmp/msg.txt` between write and `git commit -F` would have caught the stale content immediately. Shared scratch files need explicit overwrite confirmation, not assumed success.

**Seed:** Should `tmp/msg.txt` be replaced by a timestamped or process-scoped file (`tmp/msg-$$.txt`) to prevent cross-invocation contamination? Or should the commit helper be a function that writes-and-commits atomically?
