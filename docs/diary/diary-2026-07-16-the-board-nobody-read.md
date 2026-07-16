# 2026-07-16 — The board nobody read: integration is a rung, not a hook

**Context:** "reflect fr-board — how is it integrated to the real
workflow." The audit took one grep and was damning:
`grep -rln "docs/fr-board"` across the repo returned **exactly one
file: the generator**. Hours after FR-740 completed, the board had
write-side integration (a pre-commit hook that *blocks* commits) and
zero read-side integration (nothing and nobody routed to it at
decision time). The motivating question — "what's next?" — would
still have been answered by hand-merging FR files, the precise trap
the FR was filed to kill.

**The pattern has a name and I still walked into it.** This is
emission≠reception at workflow scale, documented *this morning* in
the reception-hierarchy diary, enforced *this week* in FR-737/738.
The board emitted; no rung delivered. A pre-commit hook is not
delivery — it is negative integration (stops the bad) with no
positive counterpart (surfaces the good). The write path got a gate;
the read path got hope. `now.py` — the session-start briefing that
IS the delivery rung for live state — didn't mention plan state at
all.

**Worse: an unrecorded deviation surfaced.** The FR proposed four
input streams; the enforcement shipped two. `git log` motion and
lane facts were neither implemented nor purged — silently absent,
`intent_drift` in its purest form, caught by a reflection prompt
rather than by any process. The FR is the source of truth for the
change, and the truth had a hole in it for six hours.

**Fixes, same day:** the FR now records the deviation with an
explicit disposition (deferred until a consumer exists — the AC-06
read proved status truth is the board's value; motion/lanes without
a consumer would be `growth_as_default`). `now.py` prints
`plan state: docs/fr-board.md (N active rows)` — one line, rung 2.
The session-introspection skill routes "what's next?" to the board
before hand-derivation, which closes the loop for agents who load
the skill.

**Distilled:** `a_view_without_a_reader_is_a_write_only_database` —
when shipping any generated view, the enforce checklist must include
the reception question explicitly: *name the rung, name the reader,
name the moment*. Who reads this, on which channel, at what point in
the workflow? If the answer is "whoever opens the file," the view is
not integrated; it is archived at birth. The FR-740 judgement pinned
active-set scoping, gate schemas, drift lint — every property of the
artifact — and never asked the one question that determines whether
the artifact matters. Judgements judge the *thing*; they must also
judge the *seam where the thing meets the workflow*.

**Seed:** the board's remaining unserved consumer is the human's
morning question. now.py serves agents mid-session; the skill serves
agents at start; nothing serves the human who asks "what's next?"
without an agent. Candidate: `fr_board.py --gated` printing only
gated rows with their pre-drafted questions — the eight-decisions-
in-one-sitting artifact from the unasked-question diary, on demand,
three seconds. If the human uses it twice, wire it; if not, the
gates.yaml questions were the value and the view was already enough.
