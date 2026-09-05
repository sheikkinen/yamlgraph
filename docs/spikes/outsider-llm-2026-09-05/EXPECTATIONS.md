# yamlgraph-outsider (llm node) — expectations written BEFORE any run, 2026-09-05
Model: anthropic claude-sonnet-4-5, temperature 0 (decision line in graph.yaml). Structured output via prompt schema; no markdown parsing.
Rule unchanged from FR-995: derived YES iff <= 2 unclear items and no hedge marker in the restatement.
Fixtures (same texts as the copilot spike):
  pr-591     expected NO  (>= 5 unclear)
  plain-591  expected NO  (restatement correct; pointer needs; some team-context phrases)
  pr-591-v2  expected NO
  positive   expected YES — and the real question: run it TWICE. If both runs agree, T=0 on the API is stable where the Copilot CLI flickered.
Then PR #592 live (post=false first). Compare item sets with the gpt-5.6-sol reports.
FINDING (run 1): claude-sonnet-4-5 returned the list[str] fields as a JSON-encoded STRING; yamlgraph's schema boundary did not coerce it (FR-059 class). Spike normalises in code (_lines); FR candidate for the framework boundary.

## Results (claude-sonnet-4-5, T=0, structured output) — 2026-09-05 08:03–08:07Z
positive run 1: NO, 7 unclear, 0 hedge — yamlgraph, capabilities/CAP-*.yaml, FR-990, journeys.yaml, mercury-2, scripts/author.sh, authoring-briefs
positive run 2: NO, 6 unclear, 0 hedge — same set minus authoring-briefs. 6/7 identical across runs.
pr-591:     NO, 8 unclear (all real shorthand: CAP, shape anchors, journey canaries, enum-leak demotion, wedges, extend_to, junk-drawer cap, Proposed Solution 1-5), hedge 1
plain-591:  NO, 8 unclear — includes "capabilities", "compliance evidence", "the process" (plain English; over-flagging), 10 needs
pr-591-v2:  NO, 7 unclear, hedge 1
PR #592 live: NO, 8 unclear — quotes the inline GLOSS itself ("the repository's independent plan-reviewer (a separate model run that reads only the plan…)") and asks what it is; "glossed", "nagger", "gpt-5.6-sol". 4 needs. Comment posted.

Findings:
1. STABILITY: sonnet at T=0 is far more stable than the Copilot CLI: same text 7→6 items with 6 shared, verdict NO both times (gpt-5.6-sol: 5→0, NO→YES). The API path gives a real temperature control.
2. CALIBRATION: sonnet over-flags — it lists every path and identifier even when the text explains it, and quotes explanations as unclear. Under the ≤2 rule no real PR body passes on sonnet. gpt-5.6-sol discriminates content better but flickers. Different failure modes, both real.
3. The two are complementary: stability from the API, discrimination from the judge-class model — or one model plus a CODE cap (FR-725 idiom): drop items whose quote is a file path, or is immediately followed in the body by a parenthetical gloss. Not a prompt reword; a reducer rule.
4. Structured output removed the markdown-parse failure class entirely (5/5 fixtures + live: zero rejects) but introduced the FR-059 type lie (list as JSON string) — normalised in code; framework FR candidate.
5. Standalone footprint: yamlgraph (pip) + gh + one API key. No Copilot. ~25 s per PR on sonnet.
