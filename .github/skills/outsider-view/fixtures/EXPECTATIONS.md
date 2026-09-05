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

## R-1 positive fixture (judge FR-995 R-1) — written BEFORE the run, 2026-09-05
D. inputs/pr-591-v3.md — the final glossed #591 body as merged (v2 body + five glosses).
   Derived rule (unchanged): YES iff §3 items <= 2 AND §1 contains none of: "does not say", "something called", "not stated", "cannot tell" (case-insensitive).
   Expectation: derived YES. If NO, the threshold is NOT loosened; the body is glossed further and re-run, each attempt recorded.
   Attempt 1 (v3): derived NO — 4 items ("FR-990" what is an FR; "yamlgraph" the project name; the ten user-type ids in the run command; "mercury-2"), 0 hedges. Restatement complete and correct. Threshold kept.
   Attempt 2: inputs/pr-591-v4.md = v3 + four glosses (project name and what it does; FR defined; ids → "the ten user types, definitions in journeys.yaml"; mercury-2 vendor). Expectation before run: derived YES.
   Attempt 2 (v4): derived NO — 3 items (the ten ids "what precise criteria"; "FR-990 AC-7"; "plan §12"), 0 hedges, model §2 YES. Threshold kept.
   Attempt 3: inputs/pr-591-v5.md = v4 with the raw id list replaced by a pointer to journeys.yaml, AC-7 spelled out, "plan §12" explained. Expectation before run: derived YES. If NO again, stop: record that <=2 was not reached in three glossing passes and hand the threshold question to the FR as evidence, not as a tweak.
   Attempt 3 (v5): 2 items ("the ten user-type names"; "catalog" in the AC wording) — count passes; §1 contains "the text does not say who has final responsibility for acting on its recommendations" — hedge hit → derived NO. Model §2 YES.
   STOP per the rule above. Three glossing passes did not produce a derived YES under the unchanged rule. Evidence for the FR: (a) the hedge clause carried the last verdict and pointed at a genuine omission (who decides on retirements); (b) the count clause was met only after the raw id list was removed from the body. Candidate fourth gloss for implementation time (expectation to be written first): state who acts on the recommendations.

## Attempt 4 — implementation time (FR-995 AC-08), written BEFORE the run, 2026-09-05
positive.md = pr-591-v5.md + one sentence stating who decides on recommendations (the hedge from attempt 3) and where the ten user types are defined (the residual item from attempts 2–3).
Rule unchanged: YES iff §3 <= 2 items and no hedge marker in §1.
Expectation: derived YES. If NO: record, do not loosen, and the selftest stays red until a positive is evidenced.
   Attempt 4 result: derived NO — 5 items, 0 hedges: "catalog", "retire rows", "the business plan", "novel_fandom", "fi_domain_crawl". A DIFFERENT set from attempts 1–3: the reader's item set moves between runs; glossing chases a moving target. Rule kept. Selftest stays red on the positive until a positive is evidenced (FR-995 AC-07/AC-08 open).
   Selftest run 06:25–06:26Z (production wrapper): pr-591 NO (8 items) · plain-591 NO (5) · pr-591-v2 NO (8) · positive **YES (0 items, §3 "nothing")** → PASS NO/NO/NO/YES.
   FINDING: the SAME positive.md derived NO with 5 items at 06:24Z and YES with 0 items at 06:26Z. The reader is not stable run-to-run at the borderline. The positive fixture exists (R-1 satisfied by an actual output) but the selftest will flicker on it. Any future gate must measure repeat-run variance, not single runs. Rule unchanged.
