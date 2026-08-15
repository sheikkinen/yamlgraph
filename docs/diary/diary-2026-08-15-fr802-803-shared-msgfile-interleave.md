# Diary: Market-Research Follow-ups — the Shared msg.txt Interleave

**Date:** 2026-08-15
**Context:** FR-802 (node-type census) + FR-803 (Pipecat Flows re-assessment) created and judged via the sole adapter route; both APPROVED WITH REVISIONS, revisions folded, committed as 73f441a8→c5d94f17.

## Commit provenance note (permanent record)

Commit **c5d94f17** contains the FR-802/FR-803 artifacts but carries the FR-798 message. Cause: this session wrote `tmp/msg.txt`, a parallel session overwrote it before `git commit -F` ran. An amend (73f441a8, correct message) was prepared but branch protection declined the force-push; local was reset to origin to preserve sync. The intended message is preserved in `logs/commit-fr802-803.log`'s staging record and in this entry's Context line.

## Traps encountered

1. **`one_session_one_repo`, new vector: the shared scratch file.** The Scripture's ritual covers the index, working tree, and environment — but `tmp/msg.txt` is a fourth shared channel. The Scripture's own convention ("always write to ./tmp/msg.txt") *manufactures* the collision: two sessions obeying the same doctrine line clobber each other deterministically. Cure applied going forward: session-unique message files (`tmp/msg-<topic>.txt`). Heuristic: any doctrine that names a *fixed* scratch path is a latent interleave vector; conventions must be parameterized by session.
2. **Edit-clobber during gate remediation.** Adding the `**Prior art:**` line via string replacement consumed the `**First consumer:**` label because the replacement anchored on too little context. Caught by re-reading the file immediately after the edit (`three_reads` in miniature). Heuristic: after any header-block edit, re-read the header block — labels are load-bearing for gates.
3. **The prior-art gate worked as designed.** It fired on lexical noise (FR-708/709/713/777 matching "type/census") and forced explicit dispositions. Cost: one commit cycle. Value: the FR now carries its own noise-vs-substance separation. `boring_enforcement` — the gate's fire was boring, meaning the judgement was good.

## Insight

The judge adapter twice returned APPROVED WITH REVISIONS with revisions that were *mechanically checkable* upgrades of my prose criteria ("attempted" → PASS/PARTIAL/FAIL mapping table; "grep type:" → structural discovery + raw evidence). The pattern: an author writes intentions; the judge converts them into audit surfaces. That conversion is exactly the `two_strike_split` lesson applied prophylactically — the abstraction level belongs in checkable structure, not in wording.

**Seed:** the fixed-path convention (`tmp/msg.txt`) failed under session parallelism. Which other Scripture conventions name fixed paths (`tmp/draft-judgement.md`, `tmp/draft-authoring-report.md`) — and does the judge/authoring adapter's OS lock actually cover the window between draft-write and artifact-copy, or is that the next interleave vector waiting for its incident?
