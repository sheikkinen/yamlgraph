# Canary expectations — written 2026-09-05 BEFORE any run

A. inputs/pr-591.md  (the PR as it stands: a pasted `fix(...)` commit body under a `feat` title)
   - §2 answer: NO
   - §3: >= 5 items; must include at least: "enum-leak demotion" or "junk-drawer cap" (undefined term),
     "FR-990" (unexplained identifier), "plan section 8" (assumed prior context),
     "30/30" or "canaries" (claim without pointer)
   - §4: must name "what was found" as missing
   - §1: restatement should NOT be able to say what the census found or who benefits

B. inputs/plain-591.md  (the operator-approved plain account as if it were the PR body)
   - §2 answer: YES (or NO only for a stated reason about evidence/test pointers, not vocabulary)
   - §3: <= 2 items; none of type `undefined term`
   - §1: restatement names: a list of 242 capabilities, four questions (user type / still used / keep-remove / worth),
     and at least one finding (two removal candidates, or half serve only developers)

If A and B are not clearly separated on §2 and §3 count, the outsider is not an outsider.
Model for both: gpt-5.6-sol (operator decision: PR-level content read by the judge-class model).
Second pass, if time: claude-haiku-4-5 via backend api — to see whether a cheap reader separates them too.

## Revision 2 (after §12.6) — written BEFORE the v2 runs
Prompt v2: §3 = comprehension only, max 8, no ordinary English; §4 = merge-needs checklist, max 10, skip what the text states.
C. inputs/pr-591-v2.md (the rewritten PR body: plain account + pointers + stated gaps)
   - §1 names: 242 capabilities, the four questions, two removal candidates or "half serve developers", and that tests are absent
   - §2: YES
   - §3: <= 3 items; acceptable ones: "FR-990", "CAP-184"/"CAP-78" style ids, "worktree"/"chaplain" if present. Not acceptable: any ordinary phrase.
   - §4: <= 5 bullets; must NOT list tests, runs, cost, locality, or where-to-look (all stated)
Re-run A and B under v2 for comparison: A §3 should still be >= 5 (cap 8), B §3 <= 3.

## v2 scoring (2026-09-05T05:25Z)
C  §1 correct incl. two removal candidates + unreliable classification; §2 YES ✓; §3 5 (expected ≤3 — all five genuinely project-specific, accepted; glossed in PR body v3); §4 7 (expected ≤5; none of the forbidden items) — PASS with looser counts.
A  §3 8 (cap) all real jargon ✓; §1 still hedged ✓; §2 **YES — false**: the generous v2 YES-rule let "30/30" + a wildcard path count as "found" and "where to look". §2 cannot be trusted from the model; derive it in code: YES iff §3 ≤ 2 AND §1 has no hedge markers ("does not say", "something called", "not stated").
B  §2 NO for the right reason (no pointers, no tests) ✓; §3 6 — all self-referential phrases in the approved plain text ("the business plan", "the fast, cheap one we had agreed to try", "template I copied", "rulebook"): the outsider is right, the approved account assumes team context. §4 10 legit pointer needs.
Separation now on §1 hedging and §3 content, with counts A 8 / B 6 / C 5 under a cap of 8. Count alone still weak; content is not.
