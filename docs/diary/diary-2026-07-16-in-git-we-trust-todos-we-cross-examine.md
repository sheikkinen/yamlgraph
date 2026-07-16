# 2026-07-16 — In git we trust; todos we cross-examine

**Context:** reflection on `now.py` × the todo store, prompted by the
human: "now should include the next steps agents are/were planning …
and in git we trust." The two halves of that sentence turn out to be
a complete epistemology for the situation board.

**The tense triad.** The board's sources sort by tense and by
epistemic status, and the two axes align perfectly:
- **git** — past — *fact*. Commits are witnessed, hashed, pushed.
- **tap** — present — *fact*. OTel events are emitted by the runtime,
  not curated by anyone.
- **todos** — future — *claim*. Written by the agent about itself,
  updated only when the agent remembers that updating is a task.

`now.py` had the past and the present; the todo store is the only
source that speaks in future tense — and the future is exactly where
interleave prediction lives. Git can only report the collision
afterwards; two sessions' next-steps naming the same file is a
*forecast*. The missing column was intent.

**But the claim column is measurably rotten, and in one direction.**
Today's forensics: my own session's todos read "not-started" for work
pushed hours earlier; NC-365's orphan reads "not-started" beside the
delivered FR and its judgement in git. The asymmetry has a mechanism —
updating a todo is optional effort *after* the reward (the work being
done), so claims decay toward **done-but-claimed-undone**, almost
never the reverse. Testimony lags forensics; it does not fabricate.
That makes the cross-examination cheap and safe: where a claim names
an artifact, git overrules the todo, mechanically, every time —
`STALE CLAIM`, next witness.

**Distilled:** `render_claims_as_claims` — a situation board may mix
facts and testimony only if the seam is visible. The failure mode is
not including unreliable data; it is *laundering* it — printing an
intent in the same visual register as a git fact, so the reader's
trust transfers across the seam. now.py's future column ships with a
`claims:` prefix and a mechanical overrule rule, or it doesn't ship.
(This is the third appearance of one shape today: the board separates
generated-from-tracked, the ledger separates estimate-from-exact with
a stamped seam, and now the briefing separates fact-from-claim. The
general law is older than all three: **label the epistemic grade of
every column, because the reader inherits your confusion.**)

**The pleasing recursion:** the todo store's unreliability was proven
*by* the introspection suite (todos.py cross-checked against git and
the filesystem), and the cure is to wire that same cross-check into
the delivery rung. The instrument that caught the lie becomes the
notary for the testimony. Bound as FR-741 A1 — live intent rows,
testimony-marked, git-overruled.

**Seed:** collision forecasting — two live sessions whose claimed
next-steps intersect on files or FR lanes is the interleave tripwire
*before* the staging collision, the predictive upgrade to
`one_session_one_repo`'s reactive flag. Purged from FR-741 scope,
recorded here: it needs claim-quality data first, and claim quality
improves only after the briefing makes stale claims embarrassing —
the instrument must create the incentive before it can rely on it.
