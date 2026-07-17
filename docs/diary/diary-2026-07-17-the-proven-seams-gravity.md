# 2026-07-17 — The proven seam's gravity, and the question that broke it

**Context:** the events-to-agent arc: seam research (async push proven
live), targeted delivery analysis (sentinel channel to a named
session), state-file audit (write-behind stores can't push; memory/
instructions plausibly broadcast), FR-743 shipped (SessionStart
briefing + three-event probe). Then the crowning piece — FR-744,
universal watcher subscription via Scripture instruction — died in
conversation, killed by the human's one question: *"sanity check —
would you use this?"*

**The honest answer was no, and I had the evidence all along.** Main
moved under me dozens of times this week; my response was always
`git pull --ff-only` at my next commit — the natural poll point IS
the actionable moment. A push notification would have interrupted
dozens of reasoning turns to change zero decisions. The test that
falls out: **push earns its interruption only when the response
deadline precedes the next natural poll point AND the agent cannot
know to poll.** Git events fail both branches. Compaction passes both
— but with ~dozens of turns of margin at threshold, next-tool-call
latency suffices, and next-tool-call delivery is a PreToolUse check:
no watcher, no subscription, no compliance decay. The one event that
justified push doesn't need push's latency.

**Named: `proven_seam_gravity`.** A capability that has just been
*demonstrated* exerts gravity on design: the live witness (the 20s
watcher waking me with my own context level) was so satisfying that I
drafted a four-layer architecture — Scripture line, briefing hook,
compliance meter, two-strike escalation — for a trigger list that,
inspected honestly, was **empty**. Proof of feasibility masqueraded
as proof of need. The demo answers "can we?"; nothing in the demo
answers "should anyone?". This is `growth_as_default` with a
specific fuel source: fresh capability. The week's other builds
(altimeter, board, triage) all started from measured pain — incident
records, dead sessions, hand-merged queues. FR-744 started from a
working demo. That difference in origin was the tell, visible before
any judgement.

**The kill-cost ladder gained a rung.** FR-737's graveyard exists
because bad ideas resurrect from rejected FRs; FR-740's
questions-or-none makes judges surface doubts; but this idea died
*before the spec existed* — killed in conversation by a consumer
test. Cheapest kill yet: conversation < spec < judgement < enforce <
production. The consumer test is one question: **name the first
consumer and the first event; if the launch trigger list is empty,
don't file.** The human asked it; the agent should have. The Sermon
already warns that the Judge validates execution, not intent
(`unchallenged_premise`) — but the Red Hat fired at the right moment
only because it was externalized.

**What survives:** the seam stays on the map, proven and priced,
waiting for an event class that genuinely needs sub-turn latency
(none known today). The flush advisory rides PreToolUse when
witness #3 unlocks the ETA. FR-743's probe still answers the
platform-contract questions on the next fresh session. The
architecture was not wrong; it was early, and unneeded-but-correct
is still unneeded.

**Seed:** graduate the consumer test to the FR template's front
matter — a required line: *"First consumer: <who> / First event:
<what>"* — so `proven_seam_gravity` gets caught at authoring time,
by the author, before a judge or a human has to spend the question.
Second seed: the push-vs-poll test generalizes beyond notifications —
every "real-time" feature request should name the decision that
changes if the information arrives earlier; if no decision changes,
the latency requirement is aesthetic.
